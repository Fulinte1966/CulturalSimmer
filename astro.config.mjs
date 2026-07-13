import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  site: "https://fulinte1966.github.io",
  base: "/CulturalSimmer",
  output: "static",
  redirects: {
    "/updates": "https://github.com/Fulinte1966/CulturalSimmer/blob/main/docs/site-updates-archive.md",
  },
  server: { host: "127.0.0.1" },
});
