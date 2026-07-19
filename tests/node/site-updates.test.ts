import assert from "node:assert/strict";
import test from "node:test";

import {
  HOME_RECENT_UPDATE_LIMIT,
  announcementHasBody,
  buildAutomaticSiteUpdate,
  buildManualSiteUpdate,
  canOpenSiteUpdateDetail,
  formatSiteUpdateDate,
  formatSiteUpdateDateParts,
  normalizeAnnouncementId,
  splitSiteUpdates,
  upsertGeneratedUpdate,
  validateAnnouncementLabel,
  type GeneratedSiteUpdate,
  type SiteFeedItem,
} from "../../src/lib/siteUpdates.ts";

const books = [
  {
    id: "F-1-1",
    title: "政治经济学基础知识",
    subtitle: "（资本主义部分）",
    editions: [{ edition: 1 }, { edition: 2 }],
  },
];

const update = (
  id: string,
  publishedAt: string,
  source: "automatic" | "manual" = "manual"
): SiteFeedItem => ({
  id,
  source,
  publishedAt: new Date(publishedAt),
  label: "功能",
  message: id,
  hasBody: false,
});

test("formats Shanghai dates as reusable numeric fields", () => {
  const date = new Date("2026-07-09T00:00:00+08:00");
  assert.deepEqual(formatSiteUpdateDateParts(date), {
    year: "2026",
    month: "7",
    day: "9",
  });
  assert.equal(formatSiteUpdateDate(date), "2026 年 7 月 9 日讯");
  assert.throws(() => formatSiteUpdateDateParts(new Date("invalid")));
});

test("derives automatic labels and messages without links", () => {
  const added = buildAutomaticSiteUpdate(
    {
      id: "F-1-1-listed",
      type: "book-added",
      publishedAt: "2026-07-08T18:01:03Z",
      bookId: "F-1-1",
    },
    books
  );
  assert.equal(added.label, "新书");
  assert.equal(added.message, "《政治经济学基础知识（资本主义部分）》已上架。");
  assert.equal("href" in added, false);

  const changed = buildAutomaticSiteUpdate(
    {
      id: "F-1-1-v2",
      type: "book-updated",
      publishedAt: "2026-07-11T10:00:00+08:00",
      bookId: "F-1-1",
      edition: 2,
    },
    books
  );
  assert.equal(changed.label, "更新");
  assert.equal(changed.message, "《政治经济学基础知识（资本主义部分）》已更新第 2 版。");
  assert.equal("href" in changed, false);
});

test("detects manual Markdown bodies without a duplicated flag", () => {
  assert.equal(announcementHasBody(), false);
  assert.equal(announcementHasBody(" \n\t"), false);
  assert.equal(announcementHasBody("正文"), true);
  const item = buildManualSiteUpdate({
    id: "notice",
    data: { title: "公告", label: "通知", publishedAt: new Date("2026-07-09T00:00:00Z") },
    body: "正文",
  });
  assert.equal(item.hasBody, true);
  assert.equal(item.announcementId, "notice");
  assert.equal(canOpenSiteUpdateDetail(item), true);
  assert.equal(normalizeAnnouncementId("notice.md"), "notice");
});

test("rejects invalid and reserved manual labels", () => {
  for (const label of ["", "［公告］", "[公告]", "<b>公告</b>", "新书", "更新"]) {
    assert.throws(() => validateAnnouncementLabel(label));
  }
  assert.equal(validateAnnouncementLabel(" 公告 "), "公告");
});

test("rejects invalid automatic data and missing book relations", () => {
  const base: GeneratedSiteUpdate = {
    id: "F-1-1-v2",
    type: "book-updated",
    publishedAt: "2026-07-11T10:00:00+08:00",
    bookId: "F-1-1",
    edition: 2,
  };
  assert.throws(() => buildAutomaticSiteUpdate({ ...base, bookId: "missing" }, books));
  assert.throws(() => buildAutomaticSiteUpdate({ ...base, edition: undefined }, books));
  assert.throws(() => buildAutomaticSiteUpdate({ ...base, edition: 0 }, books));
  assert.throws(() => buildAutomaticSiteUpdate({ ...base, edition: 3 }, books));
  assert.throws(() => buildAutomaticSiteUpdate({ ...base, publishedAt: "invalid" }, books));
});

test("preserves pin order, removes duplicates and limits recent updates", () => {
  const items = Array.from({ length: 8 }, (_, index) =>
    update(`manual:${index}`, `2026-07-${String(index + 1).padStart(2, "0")}T00:00:00Z`)
  );
  const result = splitSiteUpdates(items, ["manual:1", "manual:0"]);
  assert.deepEqual(result.pinnedItems.map((item) => item.id), ["manual:1", "manual:0"]);
  assert.equal(result.recentItems.length, HOME_RECENT_UPDATE_LIMIT);
  assert.deepEqual(result.recentItems.map((item) => item.id), [
    "manual:7",
    "manual:6",
    "manual:5",
    "manual:4",
    "manual:3",
  ]);
  assert.equal(result.showDivider, true);
});

test("sorts recent items by time, source and stable ID", () => {
  const time = "2026-07-09T00:00:00Z";
  const result = splitSiteUpdates(
    [update("manual:b", time), update("automatic:z", time, "automatic"), update("manual:a", time)],
    []
  );
  assert.deepEqual(result.recentItems.map((item) => item.id), [
    "automatic:z",
    "manual:a",
    "manual:b",
  ]);
});

test("validates pin IDs and divider states", () => {
  const item = update("manual:a", "2026-07-09T00:00:00Z");
  for (const pins of [[""], ["a"], ["other:a"], ["manual:missing"], ["manual:a", "manual:a"]]) {
    assert.throws(() => splitSiteUpdates([item], pins));
  }
  assert.equal(splitSiteUpdates([item], ["manual:a"]).showDivider, false);
  assert.equal(splitSiteUpdates([item], []).showDivider, false);
  assert.equal(splitSiteUpdates([], []).showDivider, false);
});

test("unpinning leaves the original timestamp and returns an eligible item", () => {
  const item = update("manual:a", "2026-07-09T00:00:00Z");
  const pinned = splitSiteUpdates([item], [item.id]);
  const unpinned = splitSiteUpdates([item], []);
  assert.equal(pinned.recentItems.length, 0);
  assert.equal(unpinned.recentItems[0], item);
  assert.equal(unpinned.recentItems[0].publishedAt.toISOString(), "2026-07-09T00:00:00.000Z");
});

test("generated update insertion is idempotent and rejects conflicts", () => {
  const incoming: GeneratedSiteUpdate = {
    id: "F-1-1-v2",
    type: "book-updated",
    publishedAt: "2026-07-11T10:00:00+08:00",
    bookId: "F-1-1",
    edition: 2,
  };
  const once = upsertGeneratedUpdate([], incoming);
  assert.equal(upsertGeneratedUpdate(once, incoming).length, 1);
  assert.throws(() =>
    upsertGeneratedUpdate(once, { ...incoming, publishedAt: "2026-07-12T10:00:00+08:00" })
  );
});
