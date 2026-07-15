import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

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

function listCssFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return listCssFiles(entryPath);
    return entry.isFile() && entry.name.endsWith(".css") ? [entryPath] : [];
  });
}

export function applyPublicAssetOrigin(directory, value) {
  const assetOrigin = normalizeAssetOrigin(value);
  if (!assetOrigin) {
    return { assetOrigin: undefined, replacements: 0, filesChanged: 0 };
  }
  if (!fs.existsSync(directory)) {
    throw new Error(`Build directory does not exist: ${directory}`);
  }

  let replacements = 0;
  let existingSources = 0;
  let filesChanged = 0;
  for (const filePath of listCssFiles(directory)) {
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

  return { assetOrigin, replacements, existingSources, filesChanged };
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
  if (result.assetOrigin) {
    console.log(
      `Applied public asset origin to ${result.replacements} font sources in ${result.filesChanged} CSS file(s).`,
    );
  } else {
    console.log("PUBLIC_ASSET_BASE_URL is unset; using same-origin assets.");
  }
}
