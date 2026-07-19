import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  CLOUDFLARE_PAGES_FILE_SIZE_LIMIT,
  prepareCloudflarePages,
  prepareCloudflareSite,
} from "../../scripts/prepare-cloudflare-pages.mjs";
import {
  PRIMARY_ORIGIN,
  prepareLegacyRedirect,
} from "../../scripts/prepare-cloudflare-legacy-redirect.mjs";

function createCloudflareFixture() {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "culturalsimmer-cloudflare-"),
  );
  const sourceDirectory = path.join(temporaryDirectory, "dist");
  const destinationDirectory = path.join(
    temporaryDirectory,
    "cloudflare-dist",
  );
  const repositoryDirectory = path.join(temporaryDirectory, "repository");
  const booksDirectory = path.join(
    repositoryDirectory,
    "src",
    "content",
    "books",
  );
  const manifestsDirectory = path.join(
    repositoryDirectory,
    "src",
    "data",
    "manifests",
  );
  fs.mkdirSync(path.join(sourceDirectory, "books", "A9-1"), {
    recursive: true,
  });
  fs.mkdirSync(booksDirectory, { recursive: true });
  fs.mkdirSync(manifestsDirectory, { recursive: true });

  const latestPdf = Buffer.from("%PDF-1.7 latest fixture");
  const latestSha256 = createHash("sha256").update(latestPdf).digest("hex");
  fs.writeFileSync(
    path.join(booksDirectory, "A9-1.md"),
    `---
id: A9-1
title: Fixture
description: Fixture
editions:
  - edition: 1
    editionDate: 2026-06
    releaseTag: A9-1_v1
    manifest: src/data/manifests/A9-1_v1.json
  - edition: 2
    editionDate: 2026-07
    releaseTag: A9-1_v2
    manifest: src/data/manifests/A9-1_v2.json
---
Fixture
`,
  );
  fs.writeFileSync(
    path.join(manifestsDirectory, "A9-1_v1.json"),
    JSON.stringify({
      bookId: "A9-1",
      edition: 1,
      releaseTag: "A9-1_v1",
      pdfFilename: "A9-1_v1.pdf",
      downloadUrl:
        "https://github.com/Fulinte1966/CulturalSimmer/releases/download/A9-1_v1/A9-1_v1.pdf",
      bytes: 1,
      sourceSha256: "0".repeat(64),
    }),
  );
  const latestManifestPath = path.join(
    manifestsDirectory,
    "A9-1_v2.json",
  );
  fs.writeFileSync(
    latestManifestPath,
    JSON.stringify({
      bookId: "A9-1",
      edition: 2,
      releaseTag: "A9-1_v2",
      pdfFilename: "A9-1_v2.pdf",
      downloadUrl:
        "https://github.com/Fulinte1966/CulturalSimmer/releases/download/A9-1_v2/A9-1_v2.pdf",
      bytes: latestPdf.length,
      sourceSha256: latestSha256,
      githubAssetDigest: `sha256:${latestSha256}`,
    }),
  );
  fs.writeFileSync(
    path.join(sourceDirectory, "books", "A9-1", "index.html"),
    `<!doctype html><html><head><link rel="canonical" href="https://fulinte.pages.dev/CulturalSimmer/books/A9-1/"></head><body><a class="bd-download" href="https://github.com/Fulinte1966/CulturalSimmer/releases/download/A9-1_v2/A9-1_v2.pdf" data-cloudflare-download="A9-1_v2.pdf">Download</a></body></html>`,
  );

  return {
    destinationDirectory,
    latestManifestPath,
    latestPdf,
    repositoryDirectory,
    sourceDirectory,
    temporaryDirectory,
  };
}

test("wraps the existing build under the public base path", () => {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "culturalsimmer-cloudflare-"),
  );
  const sourceDirectory = path.join(temporaryDirectory, "dist");
  const destinationDirectory = path.join(
    temporaryDirectory,
    "cloudflare-dist",
  );
  fs.mkdirSync(sourceDirectory);
  fs.writeFileSync(path.join(sourceDirectory, "index.html"), "site");

  const result = prepareCloudflarePages(
    sourceDirectory,
    destinationDirectory,
  );

  assert.equal(result.fileCount, 3);
  assert.equal(
    fs.readFileSync(
      path.join(destinationDirectory, "CulturalSimmer", "index.html"),
      "utf8",
    ),
    "site",
  );
  assert.match(
    fs.readFileSync(path.join(destinationDirectory, "_redirects"), "utf8"),
    /^\/ \/CulturalSimmer\/ 301/m,
  );
  assert.doesNotMatch(
    fs.readFileSync(path.join(destinationDirectory, "_headers"), "utf8"),
    /X-Robots-Tag: noindex/,
  );

  fs.rmSync(temporaryDirectory, { recursive: true, force: true });
});

test("hosts only the latest PDF and rewrites only the Cloudflare copy", async () => {
  const fixture = createCloudflareFixture();
  const requestedUrls: string[] = [];

  const result = await prepareCloudflareSite({
    sourceDirectory: fixture.sourceDirectory,
    destinationDirectory: fixture.destinationDirectory,
    repositoryDirectory: fixture.repositoryDirectory,
    downloadImpl: async (url, destinationPath) => {
      requestedUrls.push(String(url));
      fs.writeFileSync(destinationPath, fixture.latestPdf);
    },
  });

  assert.equal(result.hostedPdfCount, 1);
  assert.equal(result.rewrittenLinkCount, 1);
  assert.deepEqual(requestedUrls, [
    "https://github.com/Fulinte1966/CulturalSimmer/releases/download/A9-1_v2/A9-1_v2.pdf",
  ]);
  assert.deepEqual(
    fs.readFileSync(
      path.join(
        fixture.destinationDirectory,
        "CulturalSimmer",
        "downloads",
        "A9-1_v2.pdf",
      ),
    ),
    fixture.latestPdf,
  );
  assert.equal(
    fs.existsSync(
      path.join(
        fixture.destinationDirectory,
        "CulturalSimmer",
        "downloads",
        "A9-1_v1.pdf",
      ),
    ),
    false,
  );

  const cloudflareHtml = fs.readFileSync(
    path.join(
      fixture.destinationDirectory,
      "CulturalSimmer",
      "books",
      "A9-1",
      "index.html",
    ),
    "utf8",
  );
  assert.match(
    cloudflareHtml,
    /href="\/CulturalSimmer\/downloads\/A9-1_v2\.pdf"/,
  );
  assert.match(cloudflareHtml, /download="A9-1_v2\.pdf"/);
  assert.doesNotMatch(cloudflareHtml, /data-cloudflare-download/);
  assert.match(
    cloudflareHtml,
    /rel="canonical" href="https:\/\/fulinte\.pages\.dev\/CulturalSimmer\/books\/A9-1\/"/,
  );

  const githubHtml = fs.readFileSync(
    path.join(fixture.sourceDirectory, "books", "A9-1", "index.html"),
    "utf8",
  );
  assert.match(githubHtml, /github\.com\/Fulinte1966\/CulturalSimmer\/releases/);
  assert.match(githubHtml, /data-cloudflare-download="A9-1_v2\.pdf"/);

  const cloudflareHeaders = fs.readFileSync(
    path.join(fixture.destinationDirectory, "_headers"),
    "utf8",
  );
  assert.doesNotMatch(cloudflareHeaders, /X-Robots-Tag: noindex/);
  assert.match(
    cloudflareHeaders,
    /\/CulturalSimmer\/downloads\/\*[\s\S]*Cache-Control: public, max-age=31536000, immutable/,
  );
  assert.match(cloudflareHeaders, /Content-Disposition: attachment/);

  fs.rmSync(fixture.temporaryDirectory, { recursive: true, force: true });
});

test("uses the local candidate PDF without requesting the canonical Release", async () => {
  const fixture = createCloudflareFixture();
  const candidateDirectory = path.join(fixture.temporaryDirectory, "candidate");
  fs.mkdirSync(candidateDirectory);
  fs.writeFileSync(
    path.join(candidateDirectory, "A9-1_v2.pdf"),
    fixture.latestPdf,
  );

  const result = await prepareCloudflareSite({
    sourceDirectory: fixture.sourceDirectory,
    destinationDirectory: fixture.destinationDirectory,
    repositoryDirectory: fixture.repositoryDirectory,
    localPdfDirectory: candidateDirectory,
    downloadImpl: async () => {
      throw new Error("The canonical Release must not be requested");
    },
  });

  assert.equal(result.hostedPdfCount, 1);
  assert.deepEqual(
    fs.readFileSync(
      path.join(
        fixture.destinationDirectory,
        "CulturalSimmer",
        "downloads",
        "A9-1_v2.pdf",
      ),
    ),
    fixture.latestPdf,
  );
  fs.rmSync(fixture.temporaryDirectory, { recursive: true, force: true });
});

test("removes an incomplete Cloudflare site when PDF verification fails", async () => {
  const fixture = createCloudflareFixture();

  await assert.rejects(
    prepareCloudflareSite({
      sourceDirectory: fixture.sourceDirectory,
      destinationDirectory: fixture.destinationDirectory,
      repositoryDirectory: fixture.repositoryDirectory,
      downloadImpl: async (_url, destinationPath) => {
        fs.writeFileSync(destinationPath, Buffer.from("wrong content"));
      },
    }),
    /byte count mismatch/,
  );
  assert.equal(fs.existsSync(fixture.destinationDirectory), false);

  fs.rmSync(fixture.temporaryDirectory, { recursive: true, force: true });
});

test("rejects a PDF whose SHA-256 does not match the manifest", async () => {
  const fixture = createCloudflareFixture();
  const manifest = JSON.parse(
    fs.readFileSync(fixture.latestManifestPath, "utf8"),
  );
  manifest.sourceSha256 = "f".repeat(64);
  manifest.githubAssetDigest = `sha256:${"f".repeat(64)}`;
  fs.writeFileSync(fixture.latestManifestPath, JSON.stringify(manifest));

  await assert.rejects(
    prepareCloudflareSite({
      sourceDirectory: fixture.sourceDirectory,
      destinationDirectory: fixture.destinationDirectory,
      repositoryDirectory: fixture.repositoryDirectory,
      downloadImpl: async (_url, destinationPath) => {
        fs.writeFileSync(destinationPath, fixture.latestPdf);
      },
    }),
    /SHA-256 mismatch/,
  );
  assert.equal(fs.existsSync(fixture.destinationDirectory), false);

  fs.rmSync(fixture.temporaryDirectory, { recursive: true, force: true });
});

test("rejects a manifest above the Pages limit before downloading", async () => {
  const fixture = createCloudflareFixture();
  const manifest = JSON.parse(
    fs.readFileSync(fixture.latestManifestPath, "utf8"),
  );
  manifest.bytes = CLOUDFLARE_PAGES_FILE_SIZE_LIMIT + 1;
  fs.writeFileSync(fixture.latestManifestPath, JSON.stringify(manifest));
  let requested = false;

  await assert.rejects(
    prepareCloudflareSite({
      sourceDirectory: fixture.sourceDirectory,
      destinationDirectory: fixture.destinationDirectory,
      repositoryDirectory: fixture.repositoryDirectory,
      downloadImpl: async (_url, destinationPath) => {
        requested = true;
        fs.writeFileSync(destinationPath, fixture.latestPdf);
      },
    }),
    /25 MiB file limit exceeded/,
  );
  assert.equal(requested, false);
  assert.equal(fs.existsSync(fixture.destinationDirectory), false);

  fs.rmSync(fixture.temporaryDirectory, { recursive: true, force: true });
});

test("rejects assets above the Cloudflare Pages file size limit", () => {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "culturalsimmer-cloudflare-"),
  );
  const sourceDirectory = path.join(temporaryDirectory, "dist");
  const destinationDirectory = path.join(
    temporaryDirectory,
    "cloudflare-dist",
  );
  fs.mkdirSync(sourceDirectory);
  const oversizedFile = path.join(sourceDirectory, "oversized.bin");
  const descriptor = fs.openSync(oversizedFile, "w");
  fs.ftruncateSync(descriptor, CLOUDFLARE_PAGES_FILE_SIZE_LIMIT + 1);
  fs.closeSync(descriptor);

  assert.throws(
    () => prepareCloudflarePages(sourceDirectory, destinationDirectory),
    /25 MiB file limit exceeded/,
  );

  fs.rmSync(temporaryDirectory, { recursive: true, force: true });
});

test("prepares a noindex redirect from the former Cloudflare project", () => {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "culturalsimmer-cloudflare-legacy-"),
  );

  prepareLegacyRedirect(temporaryDirectory);

  const redirects = fs.readFileSync(
    path.join(temporaryDirectory, "_redirects"),
    "utf8",
  );
  const headers = fs.readFileSync(
    path.join(temporaryDirectory, "_headers"),
    "utf8",
  );
  assert.match(
    redirects,
    new RegExp(
      `^/CulturalSimmer/\\* ${PRIMARY_ORIGIN.replaceAll(".", "\\.")}/CulturalSimmer/:splat 301$`,
      "m",
    ),
  );
  assert.match(headers, /X-Robots-Tag: noindex/);

  fs.rmSync(temporaryDirectory, { recursive: true, force: true });
});
