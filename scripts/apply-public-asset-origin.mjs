import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const publicAssetDirectories = ["assets", "covers", "fonts"];
const buildTextExtensions = new Set([
  ".css",
  ".html",
  ".js",
  ".json",
  ".mjs",
  ".svg",
  ".webmanifest",
  ".xml",
]);
const fontSourcePattern =
  /url\((?:"|')?(\/[^)'"\s]*\/fonts\/[^)'"\s]+)(?:"|')?\)\s*format\((?:"|')woff2(?:"|')\)/g;

export function normalizeAssetOrigin(value) {
  const candidate = value?.trim();
  if (!candidate) return undefined;

  const url = new URL(candidate);
  if (url.protocol !== "https:") {
    throw new Error("PUBLIC_ASSET_BASE_URL must use HTTPS");
  }
  if (
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    (url.pathname !== "/" && url.pathname !== "")
  ) {
    throw new Error("PUBLIC_ASSET_BASE_URL must be an HTTPS origin without a path");
  }

  return url.origin;
}

export function addFontFallbackSources(css, assetOrigin) {
  let replacements = 0;
  let existingSources = 0;
  const transformed = css.replace(fontSourcePattern, (source, localUrl) => {
    const remoteUrl = `${assetOrigin}${localUrl}`;
    if (css.includes(`url("${remoteUrl}")`)) {
      existingSources += 1;
      return source;
    }

    replacements += 1;
    return (
      `url("${remoteUrl}") format("woff2"),` +
      `url("${localUrl}") format("woff2")`
    );
  });

  return { css: transformed, replacements, existingSources };
}

function listFiles(directory, predicate = () => true) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return listFiles(entryPath, predicate);
    return entry.isFile() && predicate(entryPath) ? [entryPath] : [];
  });
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function buildPublicAssetVersions(publicDirectory) {
  const versions = new Map();

  for (const directoryName of publicAssetDirectories) {
    const directory = path.join(publicDirectory, directoryName);
    if (!fs.existsSync(directory)) continue;

    for (const filePath of listFiles(directory)) {
      const relativePath = path
        .relative(publicDirectory, filePath)
        .split(path.sep)
        .join("/");
      const version = createHash("sha256")
        .update(fs.readFileSync(filePath))
        .digest("hex")
        .slice(0, 12);
      versions.set(relativePath, version);
    }
  }

  return versions;
}

export function addPublicAssetVersions(source, versions, siteBase = "/CulturalSimmer/") {
  let replacements = 0;
  let transformed = source;
  const normalizedBase = siteBase.endsWith("/") ? siteBase : `${siteBase}/`;

  for (const [relativePath, version] of versions) {
    const assetUrl = `${normalizedBase}${relativePath}`;
    const pattern = new RegExp(
      `${escapeRegExp(assetUrl)}(?:\\?v=[A-Za-z0-9._~-]+)?`,
      "g",
    );
    transformed = transformed.replace(pattern, () => {
      replacements += 1;
      return `${assetUrl}?v=${version}`;
    });
  }

  return { source: transformed, replacements };
}

export function applyPublicAssetOrigin(
  directory,
  value,
  publicDirectory = path.resolve("public"),
) {
  const assetOrigin = normalizeAssetOrigin(value);
  if (!fs.existsSync(directory)) {
    throw new Error(`Build directory does not exist: ${directory}`);
  }
  if (!fs.existsSync(publicDirectory)) {
    throw new Error(`Public directory does not exist: ${publicDirectory}`);
  }

  const versions = buildPublicAssetVersions(publicDirectory);
  let versionedReferences = 0;
  let versionedFilesChanged = 0;
  for (const filePath of listFiles(
    directory,
    (candidate) => buildTextExtensions.has(path.extname(candidate)),
  )) {
    const source = fs.readFileSync(filePath, "utf8");
    const result = addPublicAssetVersions(source, versions);
    if (result.replacements === 0 || result.source === source) continue;

    fs.writeFileSync(filePath, result.source);
    versionedReferences += result.replacements;
    versionedFilesChanged += 1;
  }

  let replacements = 0;
  let existingSources = 0;
  let filesChanged = 0;
  if (assetOrigin) {
    for (const filePath of listFiles(
      directory,
      (candidate) => candidate.endsWith(".css"),
    )) {
      const source = fs.readFileSync(filePath, "utf8");
      const result = addFontFallbackSources(source, assetOrigin);
      existingSources += result.existingSources;
      if (result.replacements === 0) continue;

      fs.writeFileSync(filePath, result.css);
      replacements += result.replacements;
      filesChanged += 1;
    }

    if (replacements === 0 && existingSources === 0) {
      throw new Error("No local WOFF2 font sources were found in the build output");
    }
  }

  return {
    assetOrigin,
    replacements,
    existingSources,
    filesChanged,
    versionedReferences,
    versionedFilesChanged,
  };
}

const isMainModule = process.argv[1]
  ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
  : false;

if (isMainModule) {
  const directory = path.resolve(process.argv[2] ?? "dist");
  const result = applyPublicAssetOrigin(
    directory,
    process.env.PUBLIC_ASSET_BASE_URL,
  );
  console.log(
    `Versioned ${result.versionedReferences} public asset references in ${result.versionedFilesChanged} build file(s).`,
  );
  if (result.assetOrigin) {
    console.log(
      `Applied public asset origin to ${result.replacements} font sources in ${result.filesChanged} CSS file(s).`,
    );
  } else {
    console.log("PUBLIC_ASSET_BASE_URL is unset; using versioned same-origin assets.");
  }
}
