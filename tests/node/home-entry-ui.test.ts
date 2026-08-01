import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const homePage = readFileSync("src/pages/index.astro", "utf8");
const homeStyles = readFileSync("src/styles/home.css", "utf8");
const globalStyles = readFileSync("src/styles/global.css", "utf8");

test("uses the shelf badge as the listed-books entry", () => {
  assert.match(homePage, /class="fm-shelf-badge"[\s\S]*?joinBasePath\(base, "books\/"\)/);
  assert.match(homePage, /class="fm-shelf-button"[\s\S]*?joinBasePath\(base, "categories\/"\)/);
});

test("uses the shared newspaper header without a duplicate listed-books heading", () => {
  const listedPage = readFileSync("src/pages/books/index.astro", "utf8");
  const listedStyles = readFileSync("src/styles/listed-books.css", "utf8");
  const categoryPage = readFileSync("src/pages/categories/index.astro", "utf8");
  const searchPage = readFileSync("src/pages/search.astro", "utf8");
  const classificationPage = readFileSync("src/pages/categories/[classification].astro", "utf8");

  assert.match(listedPage, /<NewspaperLayout/);
  assert.match(listedPage, /<NewspaperHeader[\s\S]*?currentLabel="上架书目"/);
  assert.match(categoryPage, /<NewspaperHeader[\s\S]*?currentLabel="索引"/);
  assert.match(searchPage, /<NewspaperHeader[\s\S]*?currentLabel="搜索"/);
  assert.match(classificationPage, /<NewspaperHeader[\s\S]*?currentLabel="索引"/);
  assert.doesNotMatch(listedPage, /listed-books-head|<h1/);
  assert.doesNotMatch(`${listedPage}${categoryPage}${searchPage}${classificationPage}`, /<Layout/);
  assert.match(listedStyles, /@media \(max-width: 899px\)/);
});

test("lays out the newsletter label with fixed glyph cells", () => {
  assert.match(homePage, /newsletterLabelChars\.map/);
  assert.match(homeStyles, /grid-template-rows:\s*repeat\(4, 24px\)/);
  assert.match(homeStyles, /\.fm-section-label-text[\s\S]*?letter-spacing:\s*0;/);
  assert.doesNotMatch(homeStyles, /\.fm-section-label[^}]*letter-spacing:\s*0\.5rem;/);
});

test("defines one visible cross-browser underline contract for text links", () => {
  assert.match(globalStyles, /--text-link-underline-width:\s*1px;/);
  assert.match(globalStyles, /a,\s*\.heti a\s*\{[\s\S]*?text-decoration-line:\s*underline;/);
  assert.match(globalStyles, /text-decoration-thickness:\s*var\(--text-link-underline-width\);/);
  assert.match(globalStyles, /text-decoration-skip-ink:\s*none;/);
  assert.match(globalStyles, /text-underline-position:\s*under;/);
  assert.match(homeStyles, /\.fm-site-update-open\s*\{[\s\S]*?text-decoration-thickness:\s*var\(--text-link-underline-width\);/);
  assert.match(
    homeStyles,
    /\.fm-site-update-fallback a\s*\{[\s\S]*?border-bottom:\s*var\(--text-link-underline-width\) solid currentcolor;[\s\S]*?text-decoration:\s*none;/,
  );
});
