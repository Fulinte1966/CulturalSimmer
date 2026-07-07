import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  site: "https://fulinte1966.github.io",
  base: "/CulturalSimmer",
  output: "static",
  server: { host: "127.0.0.1" },
});
