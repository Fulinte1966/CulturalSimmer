import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseHtml, serialize as serializeHtml } from "parse5";
import { parse as parseYaml } from "yaml";

export const CLOUDFLARE_PAGES_FILE_LIMIT = 20_000;
export const CLOUDFLARE_PAGES_FILE_SIZE_LIMIT = 25 * 1024 * 1024;
export const SITE_BASE = "CulturalSimmer";
export const MIRROR_DOWNLOAD_ATTRIBUTE = "data-cloudflare-download";

const redirects = `\
/ /CulturalSimmer/ 301
/CulturalSimmer /CulturalSimmer/ 301
`;

const headers = `\
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/CulturalSimmer/_astro/*
  Cache-Control: public, max-age=31536000, immutable

/CulturalSimmer/fonts/*
  Access-Control-Allow-Origin: *
  Cross-Origin-Resource-Policy: cross-origin
  Cache-Control: public, max-age=86400

/CulturalSimmer/covers/*
  Access-Control-Allow-Origin: *
  Cross-Origin-Resource-Policy: cross-origin
  Cache-Control: public, max-age=86400

/CulturalSimmer/downloads/*
  Cache-Control: public, max-age=31536000, immutable
  Content-Disposition: attachment
`;

function listFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return listFiles(entryPath);
    return entry.isFile() ? [entryPath] : [];
  });
}

function readBookFrontmatter(filePath) {
  const source = fs.readFileSync(filePath, "utf8");
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) {
    throw new Error(`Book file has no YAML front matter: ${filePath}`);
  }
  return parseYaml(match[1]);
}

function resolveRepositoryFile(repositoryDirectory, relativePath) {
  const repositoryRoot = path.resolve(repositoryDirectory);
  const resolvedPath = path.resolve(repositoryRoot, relativePath);
  const relative = path.relative(repositoryRoot, resolvedPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Repository path escapes the project root: ${relativePath}`);
  }
  return resolvedPath;
}

function normalizeSha256(manifest, manifestPath) {
  const sourceSha256 = manifest.sourceSha256;
  const assetDigest = manifest.githubAssetDigest?.replace(/^sha256:/, "");
  if (sourceSha256 && assetDigest && sourceSha256 !== assetDigest) {
    throw new Error(`Manifest SHA-256 values disagree: ${manifestPath}`);
  }

  const digest = sourceSha256 ?? assetDigest;
  if (!/^[a-f0-9]{64}$/i.test(digest ?? "")) {
    throw new Error(`Manifest has no valid SHA-256 digest: ${manifestPath}`);
  }
  return digest.toLowerCase();
}

export function loadLatestPdfReleases(repositoryDirectory) {
  const booksDirectory = path.join(
    path.resolve(repositoryDirectory),
    "src",
    "content",
    "books",
  );
  if (!fs.existsSync(booksDirectory)) {
    throw new Error(`Book content directory does not exist: ${booksDirectory}`);
  }

  return fs
    .readdirSync(booksDirectory, { withFileTypes: true })
    .filter(
      (entry) =>
        entry.isFile() &&
        entry.name.endsWith(".md") &&
        !entry.name.startsWith("_"),
    )
    .map((entry) => {
      const bookPath = path.join(booksDirectory, entry.name);
      const book = readBookFrontmatter(bookPath);
      if (!book?.id || !Array.isArray(book.editions) || book.editions.length === 0) {
        throw new Error(`Book has no edition records: ${bookPath}`);
      }

      const latestEdition = [...book.editions].sort(
        (left, right) => Number(right.edition) - Number(left.edition),
      )[0];
      if (!latestEdition.manifest) {
        throw new Error(
          `Latest edition has no manifest: ${book.id} v${latestEdition.edition}`,
        );
      }

      const manifestPath = resolveRepositoryFile(
        repositoryDirectory,
        latestEdition.manifest,
      );
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
      const pdfFilename = String(manifest.pdfFilename ?? "");
      if (!/^[A-Za-z0-9][A-Za-z0-9._-]*\.pdf$/.test(pdfFilename)) {
        throw new Error(`Manifest has an unsafe PDF filename: ${manifestPath}`);
      }
      if (
        manifest.bookId !== book.id ||
        Number(manifest.edition) !== Number(latestEdition.edition) ||
        manifest.releaseTag !== latestEdition.releaseTag
      ) {
        throw new Error(
          `Latest edition and manifest identity do not match: ${manifestPath}`,
        );
      }

      const downloadUrl = new URL(String(manifest.downloadUrl ?? ""));
      const expectedDownloadPath = `/releases/download/${manifest.releaseTag}/${pdfFilename}`;
      if (
        downloadUrl.protocol !== "https:" ||
        downloadUrl.hostname !== "github.com" ||
        !downloadUrl.pathname.endsWith(expectedDownloadPath)
      ) {
        throw new Error(
          `Manifest download URL is not a GitHub Release asset: ${manifestPath}`,
        );
      }

      const bytes = Number(manifest.bytes);
      if (!Number.isSafeInteger(bytes) || bytes <= 0) {
        throw new Error(`Manifest has no valid byte count: ${manifestPath}`);
      }

      return {
        bookId: book.id,
        edition: Number(latestEdition.edition),
        releaseTag: latestEdition.releaseTag,
        pdfFilename,
        downloadUrl: downloadUrl.href,
        bytes,
        sha256: normalizeSha256(manifest, manifestPath),
      };
    })
    .sort((left, right) => left.bookId.localeCompare(right.bookId));
}

export function validateCloudflarePagesOutput(directory) {
  const files = listFiles(directory);
  if (files.length > CLOUDFLARE_PAGES_FILE_LIMIT) {
    throw new Error(
      `Cloudflare Pages Free file limit exceeded: ${files.length} > ${CLOUDFLARE_PAGES_FILE_LIMIT}`,
    );
  }

  const oversizedFiles = files.filter(
    (filePath) =>
      fs.statSync(filePath).size > CLOUDFLARE_PAGES_FILE_SIZE_LIMIT,
  );
  if (oversizedFiles.length > 0) {
    throw new Error(
      `Cloudflare Pages 25 MiB file limit exceeded: ${oversizedFiles
        .map((filePath) => path.relative(directory, filePath))
        .join(", ")}`,
    );
  }

  return files.length;
}

export function prepareCloudflarePages(
  sourceDirectory,
  destinationDirectory,
) {
  if (!fs.existsSync(sourceDirectory)) {
    throw new Error(`Build directory does not exist: ${sourceDirectory}`);
  }

  fs.rmSync(destinationDirectory, { recursive: true, force: true });
  fs.mkdirSync(destinationDirectory, { recursive: true });

  const siteDirectory = path.join(destinationDirectory, SITE_BASE);
  fs.cpSync(sourceDirectory, siteDirectory, { recursive: true });
  fs.writeFileSync(path.join(destinationDirectory, "_redirects"), redirects);
  fs.writeFileSync(path.join(destinationDirectory, "_headers"), headers);

  return {
    destinationDirectory,
    fileCount: validateCloudflarePagesOutput(destinationDirectory),
    siteDirectory,
  };
}

export function downloadReleaseAsset(downloadUrl, destinationPath) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "curl",
      [
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--retry",
        "3",
        "--retry-all-errors",
        "--retry-delay",
        "2",
        "--connect-timeout",
        "15",
        "--max-time",
        "180",
        "--max-filesize",
        String(CLOUDFLARE_PAGES_FILE_SIZE_LIMIT),
        "--proto",
        "=https",
        "--output",
        destinationPath,
        downloadUrl,
      ],
      { stdio: ["ignore", "ignore", "pipe"] },
    );
    let stderr = "";
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk) => {
      stderr = `${stderr}${chunk}`.slice(-4_000);
    });
    child.on("error", (error) => {
      reject(
        new Error(`Unable to start curl for a GitHub Release asset: ${error.message}`),
      );
    });
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(
        new Error(
          `Unable to download a GitHub Release asset with curl (exit ${code}): ${stderr.trim()}`,
        ),
      );
    });
  });
}

async function sha256File(filePath) {
  const hash = createHash("sha256");
  for await (const chunk of fs.createReadStream(filePath)) {
    hash.update(chunk);
  }
  return hash.digest("hex");
}

export async function copyLatestPdfs(
  siteDirectory,
  releases,
  { downloadImpl = downloadReleaseAsset, localPdfDirectory } = {},
) {
  if (typeof downloadImpl !== "function") {
    throw new Error("A release asset downloader is required");
  }

  const downloadsDirectory = path.join(siteDirectory, "downloads");
  fs.mkdirSync(downloadsDirectory, { recursive: true });

  for (const release of releases) {
    if (release.bytes > CLOUDFLARE_PAGES_FILE_SIZE_LIMIT) {
      throw new Error(
        `Cloudflare Pages 25 MiB file limit exceeded: downloads/${release.pdfFilename}`,
      );
    }

    const targetPath = path.join(downloadsDirectory, release.pdfFilename);
    const temporaryPath = `${targetPath}.part`;

    try {
      const localCandidate = localPdfDirectory
        ? path.join(localPdfDirectory, release.pdfFilename)
        : undefined;
      if (localCandidate && fs.existsSync(localCandidate) && fs.statSync(localCandidate).isFile()) {
        fs.copyFileSync(localCandidate, temporaryPath);
      } else {
        await downloadImpl(release.downloadUrl, temporaryPath);
      }
      const bytes = fs.statSync(temporaryPath).size;
      if (bytes > CLOUDFLARE_PAGES_FILE_SIZE_LIMIT) {
        throw new Error(
          `Cloudflare Pages 25 MiB file limit exceeded while downloading ${release.pdfFilename}`,
        );
      }
      if (bytes !== release.bytes) {
        throw new Error(
          `PDF byte count mismatch for ${release.pdfFilename}: expected ${release.bytes}, received ${bytes}`,
        );
      }
      const sha256 = await sha256File(temporaryPath);
      if (sha256 !== release.sha256) {
        throw new Error(`PDF SHA-256 mismatch for ${release.pdfFilename}`);
      }
      fs.renameSync(temporaryPath, targetPath);
    } catch (error) {
      fs.rmSync(temporaryPath, { force: true });
      fs.rmSync(targetPath, { force: true });
      throw error;
    }
  }
}

function getAttribute(node, name) {
  return node.attrs?.find((attribute) => attribute.name === name);
}

function setAttribute(node, name, value) {
  const attribute = getAttribute(node, name);
  if (attribute) {
    attribute.value = value;
  } else {
    node.attrs ??= [];
    node.attrs.push({ name, value });
  }
}

function visitHtmlNodes(node, visitor) {
  visitor(node);
  for (const child of node.childNodes ?? []) {
    visitHtmlNodes(child, visitor);
  }
  if (node.content) {
    visitHtmlNodes(node.content, visitor);
  }
}

export function rewriteCloudflareDownloadLinks(siteDirectory, releases) {
  const releaseByFilename = new Map(
    releases.map((release) => [release.pdfFilename, release]),
  );
  const rewriteCounts = new Map(
    releases.map((release) => [release.pdfFilename, 0]),
  );

  for (const htmlPath of listFiles(siteDirectory).filter((filePath) =>
    filePath.endsWith(".html"),
  )) {
    const source = fs.readFileSync(htmlPath, "utf8");
    if (!source.includes(MIRROR_DOWNLOAD_ATTRIBUTE)) continue;

    const document = parseHtml(source);
    visitHtmlNodes(document, (node) => {
      if (node.tagName !== "a") return;
      const marker = getAttribute(node, MIRROR_DOWNLOAD_ATTRIBUTE);
      if (!marker) return;

      const release = releaseByFilename.get(marker.value);
      if (!release) {
        throw new Error(
          `Download link references a PDF that is not hosted: ${marker.value}`,
        );
      }

      setAttribute(
        node,
        "href",
        `/${SITE_BASE}/downloads/${encodeURIComponent(release.pdfFilename)}`,
      );
      setAttribute(node, "download", release.pdfFilename);
      node.attrs = node.attrs.filter(
        (attribute) => attribute.name !== MIRROR_DOWNLOAD_ATTRIBUTE,
      );
      rewriteCounts.set(
        release.pdfFilename,
        rewriteCounts.get(release.pdfFilename) + 1,
      );
    });
    fs.writeFileSync(htmlPath, serializeHtml(document));
  }

  const missingLinks = [...rewriteCounts.entries()]
    .filter(([, count]) => count === 0)
    .map(([filename]) => filename);
  if (missingLinks.length > 0) {
    throw new Error(
      `No Cloudflare download link found for: ${missingLinks.join(", ")}`,
    );
  }

  return [...rewriteCounts.values()].reduce(
    (total, count) => total + count,
    0,
  );
}

/**
 * @param {{
 *   sourceDirectory: string,
 *   destinationDirectory: string,
 *   repositoryDirectory: string,
 *   downloadImpl?: (downloadUrl: string, destinationPath: string) => Promise<void>,
 *   localPdfDirectory?: string,
 * }} options
 */
export async function prepareCloudflareSite({
  sourceDirectory,
  destinationDirectory,
  repositoryDirectory,
  downloadImpl = downloadReleaseAsset,
  localPdfDirectory,
}) {
  try {
    const result = prepareCloudflarePages(
      sourceDirectory,
      destinationDirectory,
    );
    const releases = loadLatestPdfReleases(repositoryDirectory);
    await copyLatestPdfs(result.siteDirectory, releases, {
      downloadImpl,
      localPdfDirectory,
    });
    const rewrittenLinkCount = rewriteCloudflareDownloadLinks(
      result.siteDirectory,
      releases,
    );

    return {
      ...result,
      fileCount: validateCloudflarePagesOutput(destinationDirectory),
      hostedPdfCount: releases.length,
      rewrittenLinkCount,
    };
  } catch (error) {
    fs.rmSync(destinationDirectory, { recursive: true, force: true });
    throw error;
  }
}

const isMainModule = process.argv[1]
  ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
  : false;

if (isMainModule) {
  const sourceDirectory = path.resolve(process.argv[2] ?? "dist");
  const destinationDirectory = path.resolve(
    process.argv[3] ?? "cloudflare-dist",
  );
  const repositoryDirectory = path.resolve(process.argv[4] ?? ".");
  const localPdfDirectory = process.env.CLOUDFLARE_CANDIDATE_PDF_DIR
    ? path.resolve(process.env.CLOUDFLARE_CANDIDATE_PDF_DIR)
    : undefined;
  const result = await prepareCloudflareSite({
    sourceDirectory,
    destinationDirectory,
    repositoryDirectory,
    localPdfDirectory,
  });
  console.log(
    `Prepared ${result.fileCount} Cloudflare Pages file(s), hosted ${result.hostedPdfCount} latest PDF(s), and rewrote ${result.rewrittenLinkCount} download link(s).`,
  );
}
