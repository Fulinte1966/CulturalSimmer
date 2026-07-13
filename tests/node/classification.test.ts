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
    ["A", "B", "D", "F", "H", "I", "J", "K", "T", "Z", "P"],
  );
  assert.equal(getFlatClassificationMap().size, 75);
});

test("stores only the local label at each classification level", () => {
  assert.deepEqual(getClassificationNode("A11"), {
    code: "A11",
    label: "选集、文集、选读",
    parentCode: "A1",
    depth: 3,
    children: [],
  });
  assert.equal(getClassificationNode("K926.3")?.label, "湖北省");
  assert.equal(getClassificationNode("K926.3")?.parentCode, "K926");
});

test("adds call-number separators without storing them in YAML codes", () => {
  assert.equal(formatClassificationCode("I2104"), "I210.4");
  assert.equal(formatClassificationCode("K9263"), "K926.3");
  assert.equal(formatClassificationCode("A1234567"), "A123.456.7");
  assert.throws(() => formatClassificationCode("I210.4"), /Invalid source/);
});
