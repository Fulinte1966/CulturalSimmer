import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import {
  normalizePublicAssetOrigin,
  resolvePublicAsset,
} from "../../src/lib/publicAssets";
import {
  addPublicAssetVersions,
  addFontFallbackSources,
  buildPublicAssetVersions,
  normalizeAssetOrigin,
} from "../../scripts/apply-public-asset-origin.mjs";

test("normalizes a public asset origin", () => {
  assert.equal(
    normalizePublicAssetOrigin("https://static.example.com/"),
    "https://static.example.com",
  );
  assert.equal(normalizePublicAssetOrigin("  "), undefined);
  assert.throws(() => normalizePublicAssetOrigin("http://example.com"));
  assert.throws(() => normalizePublicAssetOrigin("https://example.com/assets"));
  assert.equal(
    normalizeAssetOrigin("https://static.example.com/"),
    "https://static.example.com",
  );
});

test("uses the mirror as primary and preserves the local fallback", () => {
  assert.deepEqual(
    resolvePublicAsset(
      "/CulturalSimmer/covers/F0-1-1_v2.png",
      "https://static.example.com",
    ),
    {
      primaryUrl:
        "https://static.example.com/CulturalSimmer/covers/F0-1-1_v2.png",
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
    "https://static.example.com",
  );

  assert.equal(result.replacements, 1);
  assert.match(
    result.css,
    /url\("https:\/\/static\.example\.com\/CulturalSimmer\/fonts\/subset\/example\.woff2"\) format\("woff2"\),url\("\/CulturalSimmer\/fonts\/subset\/example\.woff2"\) format\("woff2"\)/,
  );
  assert.equal(
    addFontFallbackSources(
      result.css,
      "https://static.example.com",
    ).existingSources,
    1,
  );
  assert.equal(
    addFontFallbackSources(
      result.css,
      "https://static.example.com",
    ).replacements,
    0,
  );
});

test("adds content versions to local and mirrored public asset URLs", () => {
  const versions = new Map([
    ["fonts/subset/example.woff2", "abc123def456"],
    ["covers/example.png", "987654fedcba"],
  ]);
  const result = addPublicAssetVersions(
    [
      'url("/CulturalSimmer/fonts/subset/example.woff2")',
      'src="https://mirror.example/CulturalSimmer/covers/example.png"',
      'data-public-asset-fallback="/CulturalSimmer/covers/example.png?v=old"',
    ].join("\n"),
    versions,
  );

  assert.equal(result.replacements, 3);
  assert.match(
    result.source,
    /\/CulturalSimmer\/fonts\/subset\/example\.woff2\?v=abc123def456/,
  );
  assert.match(
    result.source,
    /https:\/\/mirror\.example\/CulturalSimmer\/covers\/example\.png\?v=987654fedcba/,
  );
  assert.doesNotMatch(result.source, /\?v=old/);
});

test("derives stable public asset versions from file contents", () => {
  const directory = fs.mkdtempSync(path.join(process.cwd(), ".tmp-assets-"));
  try {
    const fontDirectory = path.join(directory, "fonts", "subset");
    fs.mkdirSync(fontDirectory, { recursive: true });
    fs.writeFileSync(path.join(fontDirectory, "example.woff2"), "font data");

    const first = buildPublicAssetVersions(directory);
    const second = buildPublicAssetVersions(directory);
    assert.equal(
      first.get("fonts/subset/example.woff2"),
      second.get("fonts/subset/example.woff2"),
    );

    fs.writeFileSync(path.join(fontDirectory, "example.woff2"), "new font data");
    const changed = buildPublicAssetVersions(directory);
    assert.notEqual(
      first.get("fonts/subset/example.woff2"),
      changed.get("fonts/subset/example.woff2"),
    );
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
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
