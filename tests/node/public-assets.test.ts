import assert from "node:assert/strict";
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
