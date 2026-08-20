import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { normalizeOutlinePunctuation } from "../../src/lib/outline";

const categoryStyles = readFileSync("src/styles/category-index.css", "utf8");
const detailPage = readFileSync("src/pages/books/[id].astro", "utf8");
const detailStyles = readFileSync("src/styles/book-detail.css", "utf8");
const globalStyles = readFileSync("src/styles/global.css", "utf8");

test("uses an unsubsetted system Songti stack for arbitrary search input", () => {
  assert.match(globalStyles, /--font-system-songti:\s*"Songti SC",\s*"STSong",\s*"SimSun"/);
  assert.match(
    categoryStyles,
    /\.fm-keyword-line input\s*\{[\s\S]*?font-family:\s*var\(--font-system-songti\);/,
  );
});

test("collapses only an empty series row in compact detail layouts", () => {
  assert.match(detailPage, /"bd-series--empty":\s*!book\.series/);
  assert.match(
    detailStyles,
    /@media \(max-width: 899px\),[\s\S]*?\.bd-series--empty\s*\{\s*display:\s*none;/,
  );
  assert.match(detailStyles, /\.bd-series--empty\s*\{\s*visibility:\s*hidden;/);
});

test("renders outline punctuation with half-width forms without mutating source data", () => {
  assert.equal(
    normalizeOutlinePunctuation("一、读《世界通史》：“为什么？”（一）……"),
    '一,读<世界通史>:"为什么?"(一)...',
  );
  assert.equal(normalizeOutlinePunctuation("ＡＢＣ：第一章——绪论"), "ABC:第一章--绪论");
  assert.match(detailPage, /normalizeOutlinePunctuation\(item\.title\)/);
});
