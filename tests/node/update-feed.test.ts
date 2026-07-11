import assert from "node:assert/strict";
import test from "node:test";

import {
  buildPublicUpdateFeed,
  latestPublicUpdateFeed,
  validatePublicUpdateFeed,
} from "../../src/lib/updateFeed.ts";

const book = {
  id: "F0-1-1",
  title: "政治经济学基础知识",
  subtitle: "（资本主义部分）",
  editions: [
    { edition: 1, editionDate: "2026-07" },
    { edition: 2, editionDate: "2026-08" },
  ],
};

function build() {
  return buildPublicUpdateFeed({
    generatedUpdates: [
      { id: "F0-1-1-listed", type: "book-added", publishedAt: "2026-07-08T18:01:03Z", bookId: "F0-1-1" },
      { id: "F0-1-1-v2", type: "book-updated", publishedAt: "2026-08-01T00:00:00Z", bookId: "F0-1-1", edition: 2 },
    ],
    announcements: [{
      id: "2026-08-02-maintenance",
      data: { title: "维护完成", publishedAt: "2026-08-02T00:00:00Z", summary: ["恢复正常访问"] },
    }],
    books: [book],
    generatedAt: new Date("2026-08-03T00:00:00Z"),
    siteUrl: "https://example.com/CulturalSimmer/",
    updatesPageUrl: "https://example.com/CulturalSimmer/updates/",
  });
}

test("builds stable IDs from existing book and edition data", () => {
  const first = build();
  const second = build();
  assert.deepEqual(first, second);
  assert.deepEqual(first.updates.map((item) => item.id), [
    "announcement-2026-08-02-maintenance",
    "book-version-F0-1-1-v2",
    "new-book-F0-1-1-v1",
  ]);
});

test("builds an important erratum linked to an existing edition", () => {
  const feed = buildPublicUpdateFeed({
    generatedUpdates: [],
    announcements: [{
      id: "2026-08-04-f0-1-1-v2-01",
      data: {
        title: "第 12 页重要勘误",
        publishedAt: "2026-08-04T00:00:00Z",
        kind: "important-erratum",
        bookId: "F0-1-1",
        edition: 2,
        summary: ["修正正文错字"],
      },
    }],
    books: [book],
    generatedAt: new Date("2026-08-04T01:00:00Z"),
    siteUrl: "https://example.com/CulturalSimmer/",
    updatesPageUrl: "https://example.com/CulturalSimmer/updates/",
  });
  assert.equal(feed.updates[0].type, "important_erratum");
  assert.equal(feed.updates[0].version, "v2");
});

test("rejects duplicate IDs, local paths and forbidden configuration names", () => {
  const feed = build();
  assert.throws(() => validatePublicUpdateFeed({ ...feed, updates: [feed.updates[0], feed.updates[0]] }), /duplicate/i);
  assert.throws(() => validatePublicUpdateFeed({ ...feed, siteUrl: "file:///Users/test/site" }));
  assert.throws(() => validatePublicUpdateFeed({ ...feed, updatesPageUrl: "https://example.com/NAPCAT_ACCESS_TOKEN" }), /forbidden/i);
});

test("latest feed returns the newest timestamp group", () => {
  const latest = latestPublicUpdateFeed(build());
  assert.equal(latest.updates.length, 1);
  assert.equal(latest.updates[0].type, "site_announcement");
});
