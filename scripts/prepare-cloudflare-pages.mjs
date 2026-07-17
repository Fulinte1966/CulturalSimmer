import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const CLOUDFLARE_PAGES_FILE_LIMIT = 20_000;
export const CLOUDFLARE_PAGES_FILE_SIZE_LIMIT = 25 * 1024 * 1024;
export const SITE_BASE = "CulturalSimmer";

const redirects = `\
/ /CulturalSimmer/ 301
/CulturalSimmer /CulturalSimmer/ 301
`;

const headers = `\
/*
  X-Robots-Tag: noindex
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
`;

function listFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return listFiles(entryPath);
    return entry.isFile() ? [entryPath] : [];
  });
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

  const files = listFiles(destinationDirectory);
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
        .map((filePath) => path.relative(destinationDirectory, filePath))
        .join(", ")}`,
    );
  }

  return {
    destinationDirectory,
    fileCount: files.length,
    siteDirectory,
  };
}

const isMainModule = process.argv[1]
  ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
  : false;

if (isMainModule) {
  const sourceDirectory = path.resolve(process.argv[2] ?? "dist");
  const destinationDirectory = path.resolve(
    process.argv[3] ?? "cloudflare-dist",
  );
  const result = prepareCloudflarePages(
    sourceDirectory,
    destinationDirectory,
  );
  console.log(
    `Prepared ${result.fileCount} Cloudflare Pages file(s) in ${result.destinationDirectory}.`,
  );
}
