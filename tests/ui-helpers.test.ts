import assert from "node:assert/strict";
import test from "node:test";
import { joinBasePath } from "../src/lib/basePath";

test("joins a GitHub Pages base path without duplicate slashes", () => {
  assert.equal(
    joinBasePath("/ebook-library/", "/pagefind/pagefind.js"),
    "/ebook-library/pagefind/pagefind.js"
  );
});

test("joins the root base path", () => {
  assert.equal(joinBasePath("/", "books/F0-1-1/"), "/books/F0-1-1/");
});
