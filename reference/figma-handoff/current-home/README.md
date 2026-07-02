# Current Home Handoff

This folder is the local source of truth for the current homepage rebuild.
Do not call Figma MCP during implementation. Use these frozen measurements,
assets, and notes when adjusting `/`.

## Source

- Figma file: Cultural Simmer
- Node: `41:4`
- Route: `/`
- Canvas: `1440 x 1024`
- Inner frame: `1152 x 943` at `x=144`, `y=50`

## Local References

- Quote export: `../source/Quote.svg`
- Newsletter export: `../source/Newsletter.svg`
- Contextual full-page export: `../source/page1.svg`
- Measurements: `measurements.json`
- Fonts: `fonts.json`
- Assets: `assets.json`
- QA notes: `qa-notes.md`

## Implementation Rule

The homepage uses Astro markup plus `src/styles/home.css`. Global CSS must not
contain homepage positioning rules or old `front-*` selectors.
