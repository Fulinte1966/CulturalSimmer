import assert from "node:assert/strict";
import test from "node:test";

import {
  SIX_CHARACTER_TITLE_COUNT,
  getBookTitleLayout,
} from "../../src/lib/bookTitleLayout.ts";

test("marks short titles for a view-specific six-character measure", () => {
  const layout = getBookTitleLayout("狱中家书选");
  assert.deepEqual(layout.characters, ["狱", "中", "家", "书", "选"]);
  assert.equal(layout.fillsSixCharacterWidth, true);
  assert.equal(SIX_CHARACTER_TITLE_COUNT, 6);
});

test("leaves six-character and longer titles at their natural measure", () => {
  assert.equal(getBookTitleLayout("一二三四五六").fillsSixCharacterWidth, false);
  assert.equal(getBookTitleLayout("政治经济学基础知识").fillsSixCharacterWidth, false);
  assert.equal(getBookTitleLayout("").fillsSixCharacterWidth, false);
});
