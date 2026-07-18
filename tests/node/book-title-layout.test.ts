import assert from "node:assert/strict";
import test from "node:test";

import {
  SEVEN_CHARACTER_TITLE_COUNT,
  getBookTitleLayout,
} from "../../src/lib/bookTitleLayout.ts";

test("marks titles shorter than seven characters for view-specific spacing", () => {
  const layout = getBookTitleLayout("狱中家书选");
  assert.deepEqual(layout.characters, ["狱", "中", "家", "书", "选"]);
  assert.equal(layout.fillsSevenCharacterWidth, true);
  assert.equal(SEVEN_CHARACTER_TITLE_COUNT, 7);
});

test("includes six-character titles and leaves seven or more characters natural", () => {
  assert.equal(getBookTitleLayout("一二三四五六").fillsSevenCharacterWidth, true);
  assert.equal(getBookTitleLayout("一二三四五六七").fillsSevenCharacterWidth, false);
  assert.equal(getBookTitleLayout("政治经济学基础知识").fillsSevenCharacterWidth, false);
  assert.equal(getBookTitleLayout("").fillsSevenCharacterWidth, false);
});
