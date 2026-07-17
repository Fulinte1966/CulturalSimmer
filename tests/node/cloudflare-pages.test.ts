import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  CLOUDFLARE_PAGES_FILE_SIZE_LIMIT,
  prepareCloudflarePages,
} from "../../scripts/prepare-cloudflare-pages.mjs";

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
  assert.match(
    fs.readFileSync(path.join(destinationDirectory, "_headers"), "utf8"),
    /X-Robots-Tag: noindex/,
  );

  fs.rmSync(temporaryDirectory, { recursive: true, force: true });
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
