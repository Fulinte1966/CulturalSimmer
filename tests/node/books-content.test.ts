import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import { hasBookContentFiles } from "../../src/lib/bookContentFiles";

function fixtureRoot(): string {
  const root = mkdtempSync(path.join(tmpdir(), "culturalsimmer-books-"));
  mkdirSync(path.join(root, "src", "content", "books"), { recursive: true });
  return root;
}

test("treats an empty book collection as a supported state", () => {
  const root = fixtureRoot();
  writeFileSync(path.join(root, "src", "content", "books", ".gitkeep"), "");
  assert.equal(hasBookContentFiles(root), false);
});

test("detects a real Markdown book entry", () => {
  const root = fixtureRoot();
  writeFileSync(path.join(root, "src", "content", "books", "F-1-1.md"), "---\n---\n");
  assert.equal(hasBookContentFiles(root), true);
});

test("ignores underscored helper Markdown files", () => {
  const root = fixtureRoot();
  writeFileSync(path.join(root, "src", "content", "books", "_notes.md"), "local\n");
  assert.equal(hasBookContentFiles(root), false);
});

test("ignores hidden helper Markdown files", () => {
  const root = fixtureRoot();
  writeFileSync(path.join(root, "src", "content", "books", ".notes.md"), "local\n");
  assert.equal(hasBookContentFiles(root), false);
});
