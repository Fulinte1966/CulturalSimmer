import fs from "node:fs";
import path from "node:path";

const bookEntryPattern = /^[^._].*\.md$/i;

export function hasBookContentFiles(root = process.cwd()): boolean {
  const directory = path.join(root, "src", "content", "books");
  if (!fs.existsSync(directory)) {
    return false;
  }

  return fs.readdirSync(directory, { withFileTypes: true }).some(
    (entry) => entry.isFile() && bookEntryPattern.test(entry.name),
  );
}
