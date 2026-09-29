import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import test from "node:test";
import { buildPublicUpdateFeed } from "../../src/lib/updateFeed.ts";
import { buildUpdateRss } from "../../src/lib/updateRss.ts";

function feed() {
  return buildPublicUpdateFeed({
    generatedUpdates: [
      { id: "A1-listed", type: "book-added", publishedAt: "2026-09-01T00:00:00Z", bookId: "A1" },
      { id: "A1-v2", type: "book-updated", publishedAt: "2026-09-02T00:00:00Z", bookId: "A1", edition: 2 },
    ],
    books: [{ id: "A1", title: "甲 & 乙 <丙>", editions: [
      { edition: 1, editionDate: "2026-09" }, { edition: 2, editionDate: "2026-09" },
    ] }],
    announcements: [{ id: "notice", data: {
      title: "公告 🚩", publishedAt: "2026-09-03T00:00:00Z",
      summary: ['文字 <script> & "引号"\u0000', "第二段"],
    } }],
    generatedAt: new Date("2026-09-04T00:00:00Z"),
    siteUrl: "https://example.com/CulturalSimmer/",
    updatesPageUrl: "https://example.com/archive?a=1&b=2",
  });
}

function parse(xml: string) {
  return JSON.parse(execFileSync("python3", ["-c", [
    "import json, sys, xml.etree.ElementTree as ET",
    "root = ET.fromstring(sys.stdin.read())",
    "channel = root.find('channel')",
    "items = [{tag: item.findtext(tag) for tag in ('title', 'link', 'guid', 'pubDate', 'description')} | {'isPermaLink': item.find('guid').get('isPermaLink')} for item in channel.findall('item')]",
    "print(json.dumps({'items': items, 'self': channel.find('{http://www.w3.org/2005/Atom}link').get('href')}))",
  ].join("\n")], { input: xml, encoding: "utf8" }));
}

test("RSS gives editions distinct links while preserving event IDs and dates", () => {
  const input = feed();
  const output = parse(buildUpdateRss(input));
  assert.deepEqual(output.items.map((item: { guid: string }) => item.guid), input.updates.map((item) => item.id));
  assert.notEqual(output.items[1].link, output.items[2].link);
  for (const [index, item] of output.items.entries()) {
    const target = new URL(item.link);
    assert.equal(target.searchParams.get("update"), input.updates[index].id);
    target.searchParams.delete("update");
    assert.equal(target.toString(), input.updates[index].url);
  }
  assert.notEqual(output.items[1].guid, output.items[2].guid);
  assert.equal(output.items[1].isPermaLink, "false");
  assert.equal(output.items[1].pubDate, "Wed, 02 Sep 2026 00:00:00 GMT");
  assert.equal(output.self, "https://example.com/CulturalSimmer/updates/rss.xml");
});

test("RSS safely round-trips XML punctuation and Unicode without markup injection", () => {
  const output = parse(buildUpdateRss(feed()));
  assert.equal(output.items[0].title, "本站公告：公告 🚩");
  const target = new URL(output.items[0].link);
  assert.equal(target.searchParams.get("a"), "1");
  assert.equal(target.searchParams.get("b"), "2");
  assert.equal(target.searchParams.get("update"), "announcement-notice");
  assert.equal(output.items[0].description, '<p>文字 &lt;script&gt; &amp; &quot;引号&quot;</p><p>第二段</p>');
  assert.equal(output.items[1].title, "新版发布：甲 & 乙 <丙>（v2）");
});

test("RSS keeps existing target queries and fragments for distinct announcements", () => {
  const input = feed();
  const original = input.updates[0];
  input.updates = [original, { ...original, id: "announcement-second" }].map((item) => ({
    ...item, url: "https://example.com/archive?a=1&update=old#details",
  }));
  const output = parse(buildUpdateRss(input));
  assert.notEqual(output.items[0].link, output.items[1].link);
  for (const [index, item] of output.items.entries()) {
    const target = new URL(item.link);
    assert.equal(target.searchParams.get("a"), "1");
    assert.equal(target.hash, "#details");
    assert.deepEqual(target.searchParams.getAll("update"), [input.updates[index].id]);
  }
});

test("rebuilds do not rewrite RSS events or fabricate updates for an empty catalog", () => {
  const input = feed();
  assert.equal(buildUpdateRss(input), buildUpdateRss({ ...input, generatedAt: "2026-09-05T00:00:00Z" }));
  assert.deepEqual(parse(buildUpdateRss({ ...input, updates: [] })).items, []);
});
