import assert from "node:assert/strict";
import test from "node:test";

import { summarizeChangelog } from "../../src/lib/changelog.ts";

test("derives changelog statistics from edited entries", () => {
  assert.deepEqual(
    summarizeChangelog([
      { type: "insert" },
      { type: "insert", needsReview: true },
      { type: "delete" },
      { type: "replace" },
    ]),
    { total: 4, added: 2, removed: 1, changed: 1 },
  );
});
