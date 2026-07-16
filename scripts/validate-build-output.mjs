import fs from "node:fs";
import path from "node:path";
import { parse as parseYaml } from "yaml";

const root = process.cwd();
const sourceDirectory = path.join(root, "src", "content", "books");
const outputDirectory = path.join(root, "dist", "books");
const bookEntryPattern = /^[^._].*\.md$/i;

function readBookIds() {
  if (!fs.existsSync(sourceDirectory)) {
    return [];
  }

  return fs
    .readdirSync(sourceDirectory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && bookEntryPattern.test(entry.name))
    .map((entry) => {
      const source = fs.readFileSync(path.join(sourceDirectory, entry.name), "utf8");
      const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
      if (!match) {
        throw new Error(`Missing YAML front matter in ${entry.name}`);
      }
      const metadata = parseYaml(match[1]);
      if (!metadata || typeof metadata.id !== "string" || metadata.id.length === 0) {
        throw new Error(`Missing book id in ${entry.name}`);
      }
      return metadata.id;
    })
    .sort();
}

function readBuiltBookIds() {
  if (!fs.existsSync(outputDirectory)) {
    return [];
  }

  return fs
    .readdirSync(outputDirectory, { withFileTypes: true })
    .filter(
      (entry) =>
        entry.isDirectory() &&
        fs.existsSync(path.join(outputDirectory, entry.name, "index.html")),
    )
    .map((entry) => entry.name)
    .sort();
}

const expected = readBookIds();
const actual = readBuiltBookIds();

if (JSON.stringify(expected) !== JSON.stringify(actual)) {
  throw new Error(
    `Book detail output mismatch. Expected [${expected.join(", ")}], received [${actual.join(", ")}].`,
  );
}

console.log(`Validated ${actual.length} generated book detail page(s).`);
