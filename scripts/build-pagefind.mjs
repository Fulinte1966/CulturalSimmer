import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join } from "node:path";

const booksDir = join(process.cwd(), "src", "content", "books");
const hasBooks = readdirSync(booksDir).some((file) => file.endsWith(".md"));

if (!hasBooks) {
  console.log("No book markdown entries found; skipping Pagefind index.");
  process.exit(0);
}

const result = spawnSync("pagefind", ["--site", "dist", "--glob", "books/**/*.html"], {
  stdio: "inherit",
  shell: process.platform === "win32",
});

process.exit(result.status ?? 1);
