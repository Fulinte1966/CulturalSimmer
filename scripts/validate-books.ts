/**
 * Validate all book entries in the content collection.
 *
 * Checks:
 * 1. id matches call number pattern
 * 2. edition is a positive integer
 * 3. date exists
 * 4. title exists
 * 5. totalVolumes (if present) is positive integer
 * 6. volumeNumber <= totalVolumes for multi-volume books
 * 7. classification exists in classifications.yml
 * 8. outline JSON exists (warning only)
 * 9. no duplicate ids
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { getFlatClassificationMap } from "../src/lib/classification";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

const BOOK_ID_REGEX = /^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/;
const ID_PARSE_REGEX = /^([A-Z](?:\d+(?:\.\d+)?)?)-(\d+)(?:-(\d+))?$/;

// ---- Load book entries from filesystem ----
interface BookEntry {
  id: string;
  title: string;
  editions: EditionEntry[];
  tags: string[];
  cover?: string;
  totalVolumes?: number;
  notifyUpdates?: boolean;
  author?: string;
  filename: string;
}

interface EditionEntry {
  edition: number;
  editionDate: string;
  manifest?: string;
  releaseTag?: string;
}

function parseFrontmatter(raw: string): Record<string, unknown> {
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const yaml = match[1];
  const result: Record<string, unknown> = {};

  // Simple YAML parser for frontmatter
  let currentKey = "";
  let inArray = false;
  const arrayValues: string[] = [];

  const lines = yaml.split("\n");
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    if (line === "editions:") {
      const editions: EditionEntry[] = [];
      let current: Partial<EditionEntry> | null = null;
      while (index + 1 < lines.length) {
        const next = lines[index + 1];
        if (!next.startsWith("  ")) break;
        index++;
        const editionStart = next.match(/^\s+-\s+edition:\s+(\d+)/);
        if (editionStart) {
          if (current?.edition) editions.push(current as EditionEntry);
          current = { edition: parseInt(editionStart[1], 10) };
          continue;
        }
        const field = next.match(/^\s+(\w[\w_]*):\s*(.*)/);
        if (current && field) {
          const key = field[1] as keyof EditionEntry;
          const value = field[2].trim().replace(/^"(.*)"$/, "$1").replace(/^'(.*)'$/, "$1");
          if (key === "edition") {
            current.edition = parseInt(value, 10);
          } else {
            (current as Record<string, string>)[key] = value;
          }
        }
      }
      if (current?.edition) editions.push(current as EditionEntry);
      result.editions = editions;
      continue;
    }

    const arrayMatch = line.match(/^\s+-\s+(.+)/);
    if (inArray && arrayMatch) {
      arrayValues.push(arrayMatch[1].trim());
      continue;
    } else if (inArray) {
      result[currentKey] = arrayValues;
      inArray = false;
    }

    const kvMatch = line.match(/^(\w[\w_]*):\s*(.*)/);
    if (kvMatch) {
      const key = kvMatch[1];
      const value = kvMatch[2].trim();

      if (value === "") {
        // Could be start of array
        currentKey = key;
        inArray = true;
        arrayValues.length = 0;
      } else if (/^\d{4}-\d{2}(-\d{2})?/.test(value)) {
        result[key] = value;
      } else if (/^\d+$/.test(value)) {
        result[key] = parseInt(value, 10);
      } else if (/^(true|false)$/.test(value)) {
        result[key] = value === "true";
      } else {
        result[key] = value.replace(/^"(.*)"$/, "$1").replace(/^'(.*)'$/, "$1");
      }
    }
  }

  if (inArray && arrayValues.length > 0) {
    result[currentKey] = arrayValues;
  }

  return result;
}

function loadBooks(): BookEntry[] {
  const booksDir = path.join(rootDir, "src", "content", "books");
  const files = fs.readdirSync(booksDir).filter((f) => f.endsWith(".md"));

  return files.map((file) => {
    const raw = fs.readFileSync(path.join(booksDir, file), "utf-8");
    const fm = parseFrontmatter(raw);
    return {
      id: fm.id as string,
      title: fm.title as string,
      editions: (fm.editions as EditionEntry[]) || [],
      tags: (fm.tags as string[]) || [],
      cover: fm.cover as string | undefined,
      totalVolumes: fm.totalVolumes as number | undefined,
      notifyUpdates: fm.notifyUpdates as boolean | undefined,
      author: fm.author as string | undefined,
      filename: file,
    };
  });
}

// ---- Main validation ----
function main() {
  const classifications = getFlatClassificationMap();
  const books = loadBooks();

  let errors = 0;
  let warnings = 0;

  console.log(`Validating ${books.length} book(s)...\n`);

  // Check for duplicates
  const seenIds = new Map<string, string>();
  for (const book of books) {
    if (seenIds.has(book.id)) {
      console.error(
        `ERROR: Duplicate id "${book.id}" in ${book.filename} (also in ${seenIds.get(book.id)})`
      );
      errors++;
    }
    seenIds.set(book.id, book.filename);
  }

  for (const book of books) {
    const prefix = `[${book.id}]`;

    // 1. id format
    if (!BOOK_ID_REGEX.test(book.id)) {
      console.error(`${prefix} ERROR: id "${book.id}" does not match call number pattern`);
      errors++;
      continue;
    }

    // Parse id
    const parsed = book.id.match(ID_PARSE_REGEX)!;
    const classification = parsed[1];
    const volumeNumber = parsed[3] ? parseInt(parsed[3], 10) : null;

    // 2. editions
    const editions = book.editions;
    if (editions.length === 0) {
      console.error(`${prefix} ERROR: editions must contain at least one edition`);
      errors++;
    }

    const editionNumbers = new Set<number>();
    for (const item of editions) {
      if (!Number.isInteger(item.edition) || item.edition < 1) {
        console.error(`${prefix} ERROR: edition must be a positive integer, got ${item.edition}`);
        errors++;
      }
      if (editionNumbers.has(item.edition)) {
        console.error(`${prefix} ERROR: duplicate edition ${item.edition}`);
        errors++;
      }
      editionNumbers.add(item.edition);
      if (!/^\d{4}-\d{2}$/.test(item.editionDate)) {
        console.error(`${prefix} ERROR: editionDate must be YYYY-MM, got "${item.editionDate}"`);
        errors++;
      }
    }

    // 4. title
    if (!book.title || book.title.trim() === "") {
      console.error(`${prefix} ERROR: title is required and must not be empty`);
      errors++;
    }

    if (
      book.notifyUpdates !== undefined &&
      typeof book.notifyUpdates !== "boolean"
    ) {
      console.error(`${prefix} ERROR: notifyUpdates must be true or false`);
      errors++;
    }

    // 5. totalVolumes
    if (book.totalVolumes !== undefined) {
      if (!Number.isInteger(book.totalVolumes) || book.totalVolumes < 1) {
        console.error(
          `${prefix} ERROR: totalVolumes must be a positive integer, got ${book.totalVolumes}`
        );
        errors++;
      }
    }

    // 6. volume consistency
    if (volumeNumber !== null && book.totalVolumes !== undefined) {
      if (volumeNumber > book.totalVolumes) {
        console.error(
          `${prefix} ERROR: volume ${volumeNumber} > totalVolumes ${book.totalVolumes}`
        );
        errors++;
      }
    }

    // 7. classification check
    if (!classifications.has(classification)) {
      console.error(
        `${prefix} ERROR: classification "${classification}" not found in classifications.yml`
      );
      errors++;
    }

    // 8. outline JSON check (warning only)
    if (editions.length === 0) {
      continue;
    }

    const latestEdition = Math.max(...editions.map((item) => item.edition));
    const outlinePath = path.join(
      rootDir,
      "src",
      "data",
      "outlines",
      `${book.id}_v${latestEdition}.json`
    );
    if (!fs.existsSync(outlinePath)) {
      console.warn(
        `${prefix} WARN: outline JSON not found at src/data/outlines/${book.id}_v${latestEdition}.json`
      );
      warnings++;
    }
  }

  console.log(`\n${errors} error(s), ${warnings} warning(s)`);

  if (errors > 0) {
    process.exit(1);
  } else {
    console.log("Validation passed.");
  }
}

main();
