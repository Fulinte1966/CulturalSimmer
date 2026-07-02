import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  site: "https://poyinte.github.io",
  base: "ebook-library",
  output: "static",
  server: { host: "127.0.0.1" },
});
