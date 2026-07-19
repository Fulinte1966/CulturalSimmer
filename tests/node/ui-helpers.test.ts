import assert from "node:assert/strict";
import test from "node:test";
import { joinBasePath } from "../../src/lib/basePath";

test("joins a GitHub Pages base path without duplicate slashes", () => {
  assert.equal(
    joinBasePath("/CulturalSimmer/", "/pagefind/pagefind.js"),
    "/CulturalSimmer/pagefind/pagefind.js"
  );
});

test("joins the root base path", () => {
  assert.equal(joinBasePath("/", "books/F-1-1/"), "/books/F-1-1/");
});
