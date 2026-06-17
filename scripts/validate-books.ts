/**
 * Validate all book entries in the content collection.
 *
 * Checks:
 * 1. id matches call number pattern
 * 2. edition is a positive integer
 * 3. date exists
 * 4. title exists
 * 5. total_volumes (if present) is positive integer
 * 6. volumeNumber <= total_volumes for multi-volume books
 * 7. classification exists in classifications.yml
 * 8. outline JSON exists (warning only)
 * 9. no duplicate ids
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

const BOOK_ID_REGEX = /^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/;
const ID_PARSE_REGEX = /^([A-Z](?:\d+(?:\.\d+)?)?)-(\d+)(?:-(\d+))?$/;

// ---- Load classifications ----
function loadClassifications(): Map<string, string> {
  const ymlPath = path.join(rootDir, "src", "data", "classifications.yml");
  const content = fs.readFileSync(ymlPath, "utf-8");
  const map = new Map<string, string>();

  for (const line of content.split("\n")) {
    const match = line.match(/^([A-Z][A-Za-z0-9.]*):\s*(.+)/);
    if (match) {
      map.set(match[1], match[2].trim());
    }
  }
  return map;
}

// ---- Load book entries from filesystem ----
interface BookEntry {
  id: string;
  title: string;
  edition: number;
  date: string;
  tags: string[];
  cover?: string;
  total_volumes?: number;
  author?: string;
  filename: string;
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

  for (const line of yaml.split("\n")) {
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
      } else if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
        result[key] = value;
      } else if (/^\d+$/.test(value)) {
        result[key] = parseInt(value, 10);
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
      edition: fm.edition as number,
      date: fm.date as string,
      tags: (fm.tags as string[]) || [],
      cover: fm.cover as string | undefined,
      total_volumes: fm.total_volumes as number | undefined,
      author: fm.author as string | undefined,
      filename: file,
    };
  });
}

// ---- Main validation ----
function main() {
  const classifications = loadClassifications();
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

    // 2. edition
    if (!Number.isInteger(book.edition) || book.edition < 1) {
      console.error(`${prefix} ERROR: edition must be a positive integer, got ${book.edition}`);
      errors++;
    }

    // 3. date
    if (!book.date) {
      console.error(`${prefix} ERROR: date is required`);
      errors++;
    } else if (!/^\d{4}-\d{2}-\d{2}$/.test(book.date)) {
      console.error(`${prefix} ERROR: date must be YYYY-MM-DD format, got "${book.date}"`);
      errors++;
    }

    // 4. title
    if (!book.title || book.title.trim() === "") {
      console.error(`${prefix} ERROR: title is required and must not be empty`);
      errors++;
    }

    // 5. total_volumes
    if (book.total_volumes !== undefined) {
      if (!Number.isInteger(book.total_volumes) || book.total_volumes < 1) {
        console.error(
          `${prefix} ERROR: total_volumes must be a positive integer, got ${book.total_volumes}`
        );
        errors++;
      }
    }

    // 6. volume consistency
    if (volumeNumber !== null && book.total_volumes !== undefined) {
      if (volumeNumber > book.total_volumes) {
        console.error(
          `${prefix} ERROR: volume ${volumeNumber} > total_volumes ${book.total_volumes}`
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
    const outlinePath = path.join(
      rootDir,
      "src",
      "data",
      "outlines",
      `${book.id}_v${book.edition}.json`
    );
    if (!fs.existsSync(outlinePath)) {
      console.warn(
        `${prefix} WARN: outline JSON not found at src/data/outlines/${book.id}_v${book.edition}.json`
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
