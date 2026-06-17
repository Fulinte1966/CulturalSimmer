import { getCollection } from "astro:content";
import type { ParsedBookId } from "./bookId";
import { getReleaseTag, getPdfFilename, parseBookId } from "./bookId";
import { siteConfig } from "./site";

export function getDownloadUrl(id: string, edition: number): string {
  const tag = getReleaseTag(id, edition);
  const file = getPdfFilename(id, edition);
  return `https://github.com/${siteConfig.githubOwner}/${siteConfig.githubRepo}/releases/download/${tag}/${file}`;
}

export interface BookMeta {
  id: string;
  title: string;
  author?: string;
  edition: number;
  date: Date;
  tags: string[];
  cover?: string;
  total_volumes?: number;
  parsed: ParsedBookId;
  downloadUrl: string;
  outlinePath: string;
}

export async function getAllBooks(): Promise<BookMeta[]> {
  const books = await getCollection("books");

  return books
    .map((entry) => {
      const { id, title, edition, date, tags, cover, total_volumes } =
        entry.data;
      const author = entry.data.author;
      const parsed = parseBookId(id);

      return {
        id,
        title,
        author,
        edition,
        date,
        tags,
        cover,
        total_volumes,
        parsed,
        downloadUrl: getDownloadUrl(id, edition),
        outlinePath: `src/data/outlines/${id}_v${edition}.json`,
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
      result.push({ code, label: code });
    }
  }

  return result.sort((a, b) => a.code.localeCompare(b.code));
}
