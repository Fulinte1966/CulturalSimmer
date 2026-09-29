import { validatePublicUpdateFeed, type PublicUpdate, type PublicUpdateFeed } from "./updateFeed";

const labels: Record<PublicUpdate["type"], string> = {
  new_book: "新书上架",
  book_version: "新版发布",
  important_erratum: "重要勘误",
  site_announcement: "本站公告",
};

function escapeXml(value: string): string {
  const valid = Array.from(value).filter((character) => {
    const point = character.codePointAt(0)!;
    return point === 9 || point === 10 || point === 13
      || (point >= 0x20 && point <= 0xd7ff)
      || (point >= 0xe000 && point <= 0xfffd)
      || (point >= 0x10000 && point <= 0x10ffff);
  }).join("");
  return valid.replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}

function element(name: string, value: string): string {
  return `<${name}>${escapeXml(value)}</${name}>`;
}

export function buildUpdateRss(feed: PublicUpdateFeed): string {
  validatePublicUpdateFeed(feed);
  const selfUrl = new URL("updates/rss.xml", feed.siteUrl).toString();
  const items = feed.updates.map((update) => {
    const eventUrl = new URL(update.url);
    eventUrl.searchParams.set("update", update.id);
    const title = `${labels[update.type]}：${update.title}${update.version ? `（${update.version}）` : ""}`;
    const description = (update.summary.length ? update.summary : [title])
      .map((paragraph) => `<p>${escapeXml(paragraph)}</p>`).join("");
    return [
      "<item>",
      element("title", title),
      element("link", eventUrl.toString()),
      `<guid isPermaLink="false">${escapeXml(update.id)}</guid>`,
      element("pubDate", new Date(update.publishedAt).toUTCString()),
      element("description", description),
      "</item>",
    ].join("\n");
  });
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
    "<channel>",
    element("title", "CulturalSimmer"),
    element("link", feed.siteUrl),
    element("description", "新书上架、版本更新、重要勘误与本站公告。"),
    element("language", "zh-CN"),
    `<atom:link href="${escapeXml(selfUrl)}" rel="self" type="application/rss+xml" />`,
    ...items,
    "</channel>",
    "</rss>",
    "",
  ].join("\n");
}
