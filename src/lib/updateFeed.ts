import Ajv2020, { type ErrorObject } from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import updateFeedSchema from "../../schemas/update-feed.schema.json";
import type { GeneratedSiteUpdate } from "./siteUpdates";

export const UPDATE_FEED_SCHEMA_VERSION = 1 as const;
export const UPDATE_FEED_LIMIT = 100;

export type PublicUpdateType =
  | "new_book"
  | "book_version"
  | "important_erratum"
  | "site_announcement";

export interface PublicUpdate {
  id: string;
  type: PublicUpdateType;
  publishedAt: string;
  bookId?: string;
  title: string;
  version?: string;
  summary: string[];
  url: string;
}

export interface PublicUpdateFeed {
  schemaVersion: typeof UPDATE_FEED_SCHEMA_VERSION;
  generatedAt: string;
  siteUrl: string;
  updatesPageUrl: string;
  updates: PublicUpdate[];
}

export interface FeedBook {
  id: string;
  title: string;
  subtitle?: string;
  editions: Array<{ edition: number; editionDate: string }>;
}

export interface FeedAnnouncement {
  id: string;
  data: {
    title: string;
    publishedAt: Date | string;
    kind?: "site-announcement" | "important-erratum";
    bookId?: string;
    edition?: number;
    summary?: string[];
  };
}

interface BuildFeedOptions {
  generatedUpdates: GeneratedSiteUpdate[];
  announcements: FeedAnnouncement[];
  books: FeedBook[];
  generatedAt: Date;
  siteUrl: string;
  updatesPageUrl: string;
}

const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validateSchema = ajv.compile<PublicUpdateFeed>(updateFeedSchema);

function bookTitle(book: FeedBook): string {
  return `${book.title}${book.subtitle ?? ""}`;
}

function bookUrl(siteUrl: string, bookId: string): string {
  return new URL(`books/${bookId}/`, siteUrl).toString();
}

function editionSummary(editionDate: string, edition: number): string[] {
  const [year, month] = editionDate.split("-");
  return [`${year} 年 ${Number(month)} 月第 ${edition} 版`];
}

function findEdition(book: FeedBook, edition: number) {
  const record = book.editions.find((candidate) => candidate.edition === edition);
  if (!record) throw new Error(`Edition v${edition} does not exist for ${book.id}`);
  return record;
}

function automaticUpdate(
  update: GeneratedSiteUpdate,
  books: FeedBook[],
  siteUrl: string
): PublicUpdate {
  const book = books.find((candidate) => candidate.id === update.bookId);
  if (!book) throw new Error(`Update ${update.id} references missing book ${update.bookId}`);
  const edition = update.type === "book-added" ? Math.min(...book.editions.map((item) => item.edition)) : update.edition;
  if (!Number.isInteger(edition) || (edition ?? 0) < 1) {
    throw new Error(`Update ${update.id} requires a positive edition`);
  }
  const record = findEdition(book, edition as number);
  const isNewBook = update.type === "book-added";
  return {
    id: `${isNewBook ? "new-book" : "book-version"}-${book.id}-v${edition}`,
    type: isNewBook ? "new_book" : "book_version",
    publishedAt: new Date(update.publishedAt).toISOString(),
    bookId: book.id,
    title: bookTitle(book),
    version: `v${edition}`,
    summary: editionSummary(record.editionDate, edition as number),
    url: bookUrl(siteUrl, book.id),
  };
}

function manualUpdate(
  announcement: FeedAnnouncement,
  books: FeedBook[],
  siteUrl: string,
  updatesPageUrl: string
): PublicUpdate {
  const kind = announcement.data.kind ?? "site-announcement";
  const normalizedId = announcement.id.replace(/\.md$/i, "").replace(/[^a-zA-Z0-9.-]+/g, "-").toLowerCase();
  if (kind === "important-erratum") {
    const book = books.find((candidate) => candidate.id === announcement.data.bookId);
    if (!book || !announcement.data.edition) {
      throw new Error(`Important erratum ${announcement.id} requires a valid bookId and edition`);
    }
    findEdition(book, announcement.data.edition);
    return {
      id: `erratum-${normalizedId}`,
      type: "important_erratum",
      publishedAt: new Date(announcement.data.publishedAt).toISOString(),
      bookId: book.id,
      title: announcement.data.title.trim(),
      version: `v${announcement.data.edition}`,
      summary: announcement.data.summary ?? [],
      url: bookUrl(siteUrl, book.id),
    };
  }
  return {
    id: `announcement-${normalizedId}`,
    type: "site_announcement",
    publishedAt: new Date(announcement.data.publishedAt).toISOString(),
    title: announcement.data.title.trim(),
    summary: announcement.data.summary ?? [],
    url: updatesPageUrl,
  };
}

function validationMessage(errors: ErrorObject[] | null | undefined): string {
  return (errors ?? []).map((error) => `${error.instancePath || "/"} ${error.message}`).join("; ");
}

export function validatePublicUpdateFeed(feed: unknown): asserts feed is PublicUpdateFeed {
  if (!validateSchema(feed)) {
    throw new Error(`Invalid public update feed: ${validationMessage(validateSchema.errors)}`);
  }
  const value = feed as PublicUpdateFeed;
  const ids = value.updates.map((update) => update.id);
  if (new Set(ids).size !== ids.length) throw new Error("Public update feed contains duplicate IDs");
  const serialized = JSON.stringify(value);
  if (/file:\/\/|(?:^|["'])\/(?:Users|home|tmp)\//i.test(serialized)) {
    throw new Error("Public update feed contains a local path");
  }
  if (/NAPCAT|QQ_GROUP_ID|ACCESS_TOKEN|PASSPHRASE/i.test(serialized)) {
    throw new Error("Public update feed contains a forbidden configuration name");
  }
}

export function buildPublicUpdateFeed(options: BuildFeedOptions): PublicUpdateFeed {
  const updates = [
    ...options.generatedUpdates.map((update) => automaticUpdate(update, options.books, options.siteUrl)),
    ...options.announcements.map((announcement) => manualUpdate(announcement, options.books, options.siteUrl, options.updatesPageUrl)),
  ]
    .sort((a, b) => Date.parse(b.publishedAt) - Date.parse(a.publishedAt) || a.id.localeCompare(b.id))
    .slice(0, UPDATE_FEED_LIMIT);
  const feed: PublicUpdateFeed = {
    schemaVersion: UPDATE_FEED_SCHEMA_VERSION,
    generatedAt: options.generatedAt.toISOString(),
    siteUrl: options.siteUrl,
    updatesPageUrl: options.updatesPageUrl,
    updates,
  };
  validatePublicUpdateFeed(feed);
  return feed;
}

export function latestPublicUpdateFeed(feed: PublicUpdateFeed): PublicUpdateFeed {
  const latestTimestamp = feed.updates[0]?.publishedAt;
  const latest = {
    ...feed,
    updates: latestTimestamp ? feed.updates.filter((update) => update.publishedAt === latestTimestamp) : [],
  };
  validatePublicUpdateFeed(latest);
  return latest;
}
