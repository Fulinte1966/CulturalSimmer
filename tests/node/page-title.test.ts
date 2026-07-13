import assert from "node:assert/strict";
import test from "node:test";
import { formatPageTitle } from "../../src/lib/pageTitle";

test("formats the home page title without duplication", () => {
  assert.equal(formatPageTitle("文火"), "文火");
});

test("appends the site title with a full-width middle dot", () => {
  assert.equal(formatPageTitle("政治经济学基础知识"), "政治经济学基础知识・文火");
  assert.equal(formatPageTitle("索引"), "索引・文火");
  assert.equal(formatPageTitle("检查更新"), "检查更新・文火");
});
