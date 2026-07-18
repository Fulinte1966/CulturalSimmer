import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const PRIMARY_ORIGIN = "https://fulinte.pages.dev";

export function prepareLegacyRedirect(destinationDirectory) {
  fs.rmSync(destinationDirectory, { recursive: true, force: true });
  fs.mkdirSync(destinationDirectory, { recursive: true });
  fs.writeFileSync(
    path.join(destinationDirectory, "_redirects"),
    [
      `/ ${PRIMARY_ORIGIN}/CulturalSimmer/ 301`,
      `/CulturalSimmer ${PRIMARY_ORIGIN}/CulturalSimmer/ 301`,
      `/CulturalSimmer/* ${PRIMARY_ORIGIN}/CulturalSimmer/:splat 301`,
      `/* ${PRIMARY_ORIGIN}/CulturalSimmer/:splat 301`,
      "",
    ].join("\n"),
  );
  fs.writeFileSync(
    path.join(destinationDirectory, "_headers"),
    "/*\n  X-Robots-Tag: noindex\n",
  );

  return destinationDirectory;
}

const isMainModule = process.argv[1]
  ? path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
  : false;

if (isMainModule) {
  const destinationDirectory = path.resolve(
    process.argv[2] ?? "cloudflare-legacy-dist",
  );
  prepareLegacyRedirect(destinationDirectory);
  console.log(`Prepared legacy redirect site at ${destinationDirectory}.`);
}
