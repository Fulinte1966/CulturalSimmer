import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import {
  normalizePublicAssetOrigin,
  resolvePublicAsset,
} from "../../src/lib/publicAssets";
import {
  addFontFallbackSources,
  normalizeAssetOrigin,
} from "../../scripts/apply-public-asset-origin.mjs";

test("normalizes a public asset origin", () => {
  assert.equal(
    normalizePublicAssetOrigin("https://culturalsimmer-mirror.netlify.app/"),
    "https://culturalsimmer-mirror.netlify.app",
  );
  assert.equal(normalizePublicAssetOrigin("  "), undefined);
  assert.throws(() => normalizePublicAssetOrigin("http://example.com"));
  assert.throws(() => normalizePublicAssetOrigin("https://example.com/assets"));
  assert.equal(
    normalizeAssetOrigin("https://culturalsimmer-mirror.netlify.app/"),
    "https://culturalsimmer-mirror.netlify.app",
  );
});

test("uses the mirror as primary and preserves the local fallback", () => {
  assert.deepEqual(
    resolvePublicAsset(
      "/CulturalSimmer/covers/F0-1-1_v2.png",
      "https://culturalsimmer-mirror.netlify.app",
    ),
    {
      primaryUrl:
        "https://culturalsimmer-mirror.netlify.app/CulturalSimmer/covers/F0-1-1_v2.png",
      fallbackUrl: "/CulturalSimmer/covers/F0-1-1_v2.png",
    },
  );
});

test("keeps same-origin assets when the mirror is disabled", () => {
  assert.deepEqual(
    resolvePublicAsset("/CulturalSimmer/covers/F0-1-1_v2.png"),
    { primaryUrl: "/CulturalSimmer/covers/F0-1-1_v2.png" },
  );
});

test("adds a remote WOFF2 source before the local fallback", () => {
  const source =
    '@font-face{src:url(/CulturalSimmer/fonts/subset/example.woff2) format("woff2")}';
  const result = addFontFallbackSources(
    source,
    "https://culturalsimmer-mirror.netlify.app",
  );

  assert.equal(result.replacements, 1);
  assert.match(
    result.css,
    /url\("https:\/\/culturalsimmer-mirror\.netlify\.app\/CulturalSimmer\/fonts\/subset\/example\.woff2"\) format\("woff2"\),url\("\/CulturalSimmer\/fonts\/subset\/example\.woff2"\) format\("woff2"\)/,
  );
  assert.equal(
    addFontFallbackSources(
      result.css,
      "https://culturalsimmer-mirror.netlify.app",
    ).existingSources,
    1,
  );
  assert.equal(
    addFontFallbackSources(
      result.css,
      "https://culturalsimmer-mirror.netlify.app",
    ).replacements,
    0,
  );
});

test("keeps every public font URL under the configured site base", () => {
  const css = fs.readFileSync(
    path.join(process.cwd(), "src", "styles", "global.css"),
    "utf8",
  );
  const fontUrls = [...css.matchAll(/url\("([^"]+\.woff2)"\)/g)].map(
    (match) => match[1],
  );

  assert.ok(fontUrls.length > 0);
  assert.equal(fontUrls.some((url) => url.startsWith("/fonts/")), false);
  assert.equal(
    fontUrls.every((url) => url.startsWith("/CulturalSimmer/fonts/")),
    true,
  );
});

test("keeps every CSS public asset URL under the configured site base", () => {
  const stylesDirectory = path.join(process.cwd(), "src", "styles");
  const assetUrls = fs
    .readdirSync(stylesDirectory)
    .filter((name) => name.endsWith(".css"))
    .flatMap((name) => {
      const css = fs.readFileSync(path.join(stylesDirectory, name), "utf8");
      return [...css.matchAll(/url\(["']?([^"')]+)["']?\)/g)]
        .map((match) => match[1])
        .filter((url) => url.startsWith("/"));
    });

  assert.ok(assetUrls.length > 0);
  assert.equal(
    assetUrls.some((url) => /^(?:\/assets|\/fonts|\/covers)\//.test(url)),
    false,
  );
  assert.equal(
    assetUrls.every((url) => url.startsWith("/CulturalSimmer/")),
    true,
  );
});
