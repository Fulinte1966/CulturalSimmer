import assert from "node:assert/strict";
import test from "node:test";
import {
  formatClassificationCode,
  getClassificationNode,
  getClassificationNodes,
  getFlatClassificationMap,
} from "../../src/lib/classification";

test("loads the ordered classification tree from structured YAML", () => {
  assert.deepEqual(
    getClassificationNodes().map((node) => node.code),
    ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"],
  );
  assert.equal(getFlatClassificationMap().size, 18);
});

test("stores only the local label at each classification level", () => {
  assert.deepEqual(getClassificationNode("A9"), {
    code: "A9",
    label: "张春桥、姚文元著作",
    parentCode: "A",
    depth: 2,
    children: [],
  });
  assert.equal(getClassificationNode("B")?.label, "哲学、宗教");
  assert.equal(getClassificationNode("B")?.parentCode, undefined);
  assert.equal(getClassificationNode("B")?.depth, 1);
  assert.equal(getClassificationNode("A93"), undefined);
});

test("adds call-number separators without storing them in YAML codes", () => {
  assert.equal(formatClassificationCode("I2104"), "I210.4");
  assert.equal(formatClassificationCode("K9263"), "K926.3");
  assert.equal(formatClassificationCode("A1234567"), "A123.456.7");
  assert.throws(() => formatClassificationCode("I210.4"), /Invalid source/);
});
