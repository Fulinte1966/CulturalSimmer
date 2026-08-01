import assert from "node:assert/strict";
import test from "node:test";
import { orderBooksByInitialListing } from "../../src/lib/bookOrdering";

test("orders listed books by their initial listing time", () => {
  const books = [
    { id: "A-1", listedAt: new Date("2026-07-01T00:00:00Z") },
    { id: "B-1", listedAt: new Date("2026-08-01T00:00:00Z") },
    { id: "C-1", listedAt: new Date("2026-07-15T00:00:00Z") },
  ];

  assert.deepEqual(
    orderBooksByInitialListing(books).map((book) => book.id),
    ["B-1", "C-1", "A-1"],
  );
  assert.deepEqual(books.map((book) => book.id), ["A-1", "B-1", "C-1"]);
});

test("uses the book id as a stable tie breaker", () => {
  const listedAt = new Date("2026-08-01T00:00:00Z");
  const books = [
    { id: "B-1", listedAt },
    { id: "A-1", listedAt },
  ];

  assert.deepEqual(
    orderBooksByInitialListing(books).map((book) => book.id),
    ["A-1", "B-1"],
  );
});
