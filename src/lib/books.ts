import fs from "node:fs";
import path from "node:path";
import { getCollection } from "astro:content";
import type { ParsedBookId } from "./bookId";
import { getPdfFilename, getReleaseTag, parseBookId } from "./bookId";
import { siteConfig } from "./site";
import { getClassificationLabel } from "./classification";

const rootDir = process.cwd();

export { getClassificationLabel } from "./classification";

export function getDownloadUrl(id: string, edition: number): string {
  const tag = getReleaseTag(id, edition);
  const file = getPdfFilename(id, edition);
  return `https://github.com/${siteConfig.githubOwner}/${siteConfig.githubRepo}/releases/download/${tag}/${file}`;
}

export interface ReadingMetrics {
  pageCount: number;
  cjkCharacterCount?: number;
  latinTokenCount?: number;
  estimatedMinutes?: number;
  fileSizeBytes?: number;
}

export type CoverKind = "explicit" | "generated" | "placeholder";

export interface BookMeta {
  id: string;
  title: string;
  description?: string;
  subtitle?: string;
  author?: string;
  language?: string;
  series?: string;
  publisher?: string;
  source?: string;
  rights?: string;
  licenseUrl?: string;
  edition: number;
  editionDate: string;
  date: Date;
  editions: EditionRecord[];
  tags: string[];
  cover?: string;
  coverUrl?: string;
  spineUrl?: string;
  coverKind: CoverKind;
  totalVolumes?: number;
  reading?: ReadingMetrics;
  parsed: ParsedBookId;
  downloadUrl: string;
  outlinePath: string;
}

export interface EditionRecord {
  edition: number;
  editionDate: string;
  releaseTag?: string;
  manifest?: string;
}

function withBasePath(value: string): string {
  if (/^https?:\/\//i.test(value)) {
    return value;
  }

  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  const normalized = value.replace(/^\/+/, "");
  return `${base}/${normalized}`;
}

function resolveCover(
  id: string,
  edition: number,
  explicitCover?: string
): { coverUrl?: string; spineUrl?: string; coverKind: CoverKind } {
  if (explicitCover) {
    return {
      coverUrl: withBasePath(explicitCover),
      coverKind: "explicit",
    };
  }

  const filename = `${id}_v${edition}.png`;
  const spineFilename = `${id}_v${edition}_spine.png`;
  const generatedPath = path.join(rootDir, "public", "covers", filename);
  const spinePath = path.join(rootDir, "public", "covers", spineFilename);
  if (fs.existsSync(generatedPath)) {
    return {
      coverUrl: withBasePath(`covers/${filename}`),
      spineUrl: fs.existsSync(spinePath)
        ? withBasePath(`covers/${spineFilename}`)
        : undefined,
      coverKind: "generated",
    };
  }

  return { coverKind: "placeholder" };
}

function loadReadingMetrics(
  id: string,
  edition: number
): ReadingMetrics | undefined {
  const metricsPath = path.join(
    rootDir,
    "src",
    "data",
    "reading",
    `${id}_v${edition}.json`
  );

  if (!fs.existsSync(metricsPath)) {
    return undefined;
  }

  try {
    const value = JSON.parse(
      fs.readFileSync(metricsPath, "utf-8")
    ) as ReadingMetrics;
    if (!Number.isInteger(value.pageCount) || value.pageCount < 1) {
      return undefined;
    }
    return value;
  } catch {
    return undefined;
  }
}

function dateFromEditionDate(value: string): Date {
  return new Date(`${value}-01T00:00:00+08:00`);
}

function resolveEditions(
  editionsInput?: EditionRecord[]
): EditionRecord[] {
  const editions = [...(editionsInput ?? [])].sort(
    (a, b) => a.edition - b.edition
  );

  return editions;
}

function getLatestEdition(editions: EditionRecord[]): EditionRecord {
  const latest = editions.at(-1);
  if (!latest) {
    throw new Error("Book entry must define at least one edition");
  }
  return latest;
}

export async function getAllBooks(): Promise<BookMeta[]> {
  const books = await getCollection("books");

  return books
    .map((entry) => {
      const {
        id,
        title,
        description,
        subtitle,
        editions: rawEditions,
        tags,
        cover,
        totalVolumes,
        author,
        language,
        series,
        publisher,
        source,
        rights,
        licenseUrl,
      } = entry.data;
      const editions = resolveEditions(rawEditions);
      const latestEdition = getLatestEdition(editions);
      const parsed = parseBookId(id);
      const resolvedCover = resolveCover(id, latestEdition.edition, cover);
      const reading = loadReadingMetrics(id, latestEdition.edition);

      return {
        id,
        title,
        description,
        subtitle,
        author,
        language,
        series,
        publisher,
        source,
        rights,
        licenseUrl,
        edition: latestEdition.edition,
        editionDate: latestEdition.editionDate,
        date: dateFromEditionDate(latestEdition.editionDate),
        editions,
        tags,
        cover,
        ...resolvedCover,
        totalVolumes,
        reading,
        parsed,
        downloadUrl: getDownloadUrl(id, latestEdition.edition),
        outlinePath: `src/data/outlines/${id}_v${latestEdition.edition}.json`,
      };
    })
    .sort((a, b) => b.date.getTime() - a.date.getTime());
}

export async function getBooksByClassification(
  classification: string
): Promise<BookMeta[]> {
  const all = await getAllBooks();
  return all.filter((book) => book.parsed.classification === classification);
}

export async function getBookById(
  id: string
): Promise<BookMeta | undefined> {
  const all = await getAllBooks();
  return all.find((book) => book.id === id);
}

export function getUniqueClassifications(
  books: BookMeta[]
): { code: string; label: string }[] {
  const seen = new Set<string>();
  const result: { code: string; label: string }[] = [];

  for (const book of books) {
    const code = book.parsed.classification;
    if (!seen.has(code)) {
      seen.add(code);
      result.push({ code, label: getClassificationLabel(code) });
    }
  }

  return result.sort((a, b) => a.code.localeCompare(b.code));
}
