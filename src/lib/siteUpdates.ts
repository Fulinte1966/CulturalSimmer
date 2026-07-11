export const HOME_RECENT_UPDATE_LIMIT = 5;
export const RESERVED_SITE_UPDATE_LABELS = new Set(["新书", "更新"]);

export type GeneratedUpdateType = "book-added" | "book-updated";

export interface GeneratedSiteUpdate {
  id: string;
  type: GeneratedUpdateType;
  publishedAt: string;
  bookId: string;
  edition?: number;
}

export interface SiteUpdateBook {
  id: string;
  title: string;
  subtitle?: string;
  editions: Array<{ edition: number }>;
}

export interface SiteAnnouncement {
  id: string;
  data: {
    title: string;
    label: string;
    publishedAt: string | Date;
  };
  body?: string;
}

export interface SiteFeedItem {
  id: string;
  source: "automatic" | "manual";
  publishedAt: Date;
  label: string;
  message: string;
  announcementId?: string;
  hasBody: boolean;
}

export interface SplitSiteUpdates {
  pinnedItems: SiteFeedItem[];
  recentItems: SiteFeedItem[];
  showDivider: boolean;
}

export function validateAnnouncementLabel(label: string): string {
  const normalized = label.trim();
  if (!normalized) throw new Error("Announcement label must not be empty");
  if (/[\[\]［］]/.test(normalized)) {
    throw new Error("Announcement label must not contain brackets");
  }
  if (/<[^>]*>|[<>]/.test(normalized)) {
    throw new Error("Announcement label must not contain HTML");
  }
  if (RESERVED_SITE_UPDATE_LABELS.has(normalized)) {
    throw new Error(`Announcement label is reserved: ${normalized}`);
  }
  if (Array.from(normalized).length > 6) {
    throw new Error("Announcement label must not exceed 6 characters");
  }
  return normalized;
}

export function announcementHasBody(body?: string): boolean {
  return Boolean(body?.trim());
}

export function normalizeAnnouncementId(id: string): string {
  return id.replace(/\.md$/i, "");
}

export function formatSiteUpdateDate(date: Date): string {
  if (Number.isNaN(date.getTime())) throw new Error("Invalid site update date");
  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "numeric",
    day: "numeric",
  }).formatToParts(date);
  const value = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value;
  return `${value("year")} 年 ${value("month")} 月 ${value("day")} 日讯`;
}

function parsePublishedAt(value: string | Date, id: string): Date {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid publishedAt for site update: ${id}`);
  }
  return date;
}

function displayBookTitle(book: SiteUpdateBook): string {
  return `${book.title}${book.subtitle ?? ""}`;
}

export function buildAutomaticSiteUpdate(
  update: GeneratedSiteUpdate,
  books: SiteUpdateBook[]
): SiteFeedItem {
  if (!update.id || !update.bookId) {
    throw new Error("Generated site update requires id and bookId");
  }
  if (!(["book-added", "book-updated"] as string[]).includes(update.type)) {
    throw new Error(`Unknown generated site update type: ${update.type}`);
  }
  const book = books.find((candidate) => candidate.id === update.bookId);
  if (!book) {
    throw new Error(`Book does not exist for site update: ${update.bookId}`);
  }

  const publishedAt = parsePublishedAt(update.publishedAt, update.id);
  const title = displayBookTitle(book);
  if (update.type === "book-added") {
    return {
      id: `automatic:${update.id}`,
      source: "automatic",
      publishedAt,
      label: "新书",
      message: `《${title}》已上架。`,
      hasBody: false,
    };
  }

  if (!Number.isInteger(update.edition) || (update.edition ?? 0) < 1) {
    throw new Error(`Generated book update requires a positive edition: ${update.id}`);
  }
  if (!book.editions.some((record) => record.edition === update.edition)) {
    throw new Error(`Edition ${update.edition} does not exist for book ${book.id}`);
  }

  return {
    id: `automatic:${update.id}`,
    source: "automatic",
    publishedAt,
    label: "更新",
    message: `《${title}》已更新第 ${update.edition} 版。`,
    hasBody: false,
  };
}

export function buildManualSiteUpdate(
  announcement: SiteAnnouncement
): SiteFeedItem {
  const announcementId = normalizeAnnouncementId(announcement.id);
  const label = validateAnnouncementLabel(announcement.data.label);
  const hasBody = announcementHasBody(announcement.body);
  return {
    id: `manual:${announcementId}`,
    source: "manual",
    publishedAt: parsePublishedAt(announcement.data.publishedAt, announcement.id),
    label,
    message: announcement.data.title.trim(),
    announcementId: hasBody ? announcementId : undefined,
    hasBody,
  };
}

export function buildSiteUpdates(
  generatedUpdates: GeneratedSiteUpdate[],
  announcements: SiteAnnouncement[],
  books: SiteUpdateBook[]
): SiteFeedItem[] {
  const ids = new Set<string>();
  const items = [
    ...generatedUpdates.map((update) =>
      buildAutomaticSiteUpdate(update, books)
    ),
    ...announcements.map(buildManualSiteUpdate),
  ];
  for (const item of items) {
    if (ids.has(item.id)) throw new Error(`Duplicate site update ID: ${item.id}`);
    ids.add(item.id);
  }
  return items;
}

export function splitSiteUpdates(
  allItems: SiteFeedItem[],
  pinnedIds: string[],
  recentLimit = HOME_RECENT_UPDATE_LIMIT
): SplitSiteUpdates {
  const byId = new Map(allItems.map((item) => [item.id, item]));
  const pinnedSet = new Set<string>();
  const pinnedItems = pinnedIds.map((id) => {
    if (!id || !/^(automatic|manual):/.test(id)) {
      throw new Error(`Invalid pinned site update ID: ${id || "(empty)"}`);
    }
    if (pinnedSet.has(id)) throw new Error(`Duplicate pinned site update ID: ${id}`);
    const item = byId.get(id);
    if (!item) throw new Error(`Pinned site update does not exist: ${id}`);
    pinnedSet.add(id);
    return item;
  });
  const recentItems = allItems
    .filter((item) => !pinnedSet.has(item.id))
    .sort(
      (a, b) =>
        b.publishedAt.getTime() - a.publishedAt.getTime() ||
        a.source.localeCompare(b.source) ||
        a.id.localeCompare(b.id)
    )
    .slice(0, Math.max(0, recentLimit));

  return {
    pinnedItems,
    recentItems,
    showDivider: pinnedItems.length > 0 && recentItems.length > 0,
  };
}

export function canOpenSiteUpdateDetail(item: SiteFeedItem): boolean {
  return item.source === "manual" && item.hasBody && Boolean(item.announcementId);
}

export function upsertGeneratedUpdate(
  updates: GeneratedSiteUpdate[],
  incoming: GeneratedSiteUpdate
): GeneratedSiteUpdate[] {
  const existing = updates.find((item) => item.id === incoming.id);
  if (existing) {
    if (JSON.stringify(existing) !== JSON.stringify(incoming)) {
      throw new Error(`Conflicting generated site update ID: ${incoming.id}`);
    }
    return [...updates];
  }
  return [...updates, incoming].sort(
    (a, b) =>
      new Date(a.publishedAt).getTime() - new Date(b.publishedAt).getTime() ||
      a.id.localeCompare(b.id)
  );
}
