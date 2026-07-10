import assert from "node:assert/strict";
import test from "node:test";

import { resolveUpdateCheck } from "../../src/lib/updateCheck.ts";

const books = [{ id: "F0-1-1", edition: 3, title: "测试书" }];

test("recognizes the latest edition", () => {
  assert.deepEqual(resolveUpdateCheck(books, "F0-1-1", "3"), {
    status: "current",
    book: books[0],
    requestedEdition: 3,
  });
});

test("recognizes an older edition", () => {
  assert.equal(resolveUpdateCheck(books, "F0-1-1", "2").status, "outdated");
});

test("rejects missing books and invalid editions", () => {
  assert.equal(resolveUpdateCheck(books, "A1-1", "1").status, "unknown-book");
  assert.equal(resolveUpdateCheck(books, "F0-1-1", "0").status, "invalid-edition");
  assert.equal(resolveUpdateCheck(books, "F0-1-1", "4").status, "invalid-edition");
  assert.equal(resolveUpdateCheck(books, null, null).status, "invalid-request");
});
