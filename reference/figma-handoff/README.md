# Figma Handoff

This directory contains two kinds of material:

- `current-home/` is the active source of truth for the homepage rebuild.
- The remaining Markdown/JSON files are historical handoff notes plus still
  useful PDF metadata and automation references.

Do not call Figma MCP during implementation. Freeze Figma values into local
files first, then implement from those local files.

## Reading order

For homepage UI work:

1. `current-home/README.md`
2. `current-home/measurements.json`
3. `current-home/fonts.json`
4. `current-home/assets.json`
5. `current-home/qa-notes.md`

For PDF metadata and automation work:

1. `pdf-metadata-contract.md`
2. `automation-spec.md`
3. `acceptance-checklist.md`

## Figma source

Current homepage:

- File: `Cultural Simmer`
- Node: `41:4`
- Desktop frame size: `1440 x 1024`
- Local handoff: `current-home/`

Historical files such as `design-tokens.json`, `screens.json`, and
`source/page1.svg`/`source/page2.svg` came from earlier design attempts. Do not
use them as the active homepage source unless they are explicitly promoted into
`current-home/`.

## Priority order

When documents appear to conflict, use this order:

1. Data integrity and automation rules in `pdf-metadata-contract.md` and
   `automation-spec.md`.
2. Current homepage values in `current-home/`.
3. Historical machine-readable values only when working on their original
   handoff scope.
4. Existing code only where the handoff explicitly says to preserve it.

Do not infer missing values from the old Metro UI.

## Asset status

The original red `文火` wordmark is available at
`public/brand/wordmark.svg`. It is a path-only SVG with no font or raster
dependency. Use the file unchanged and provide a meaningful accessible label.

Figma exports retained under `source/` are reference artifacts only. Active
homepage implementation values live in `current-home/`.

Font source paths are recorded for identification only. Confirm each license
before creating or committing webfonts.

## Scope guardrails

- Preserve Astro static output, GitHub Pages, GitHub Releases, Pagefind, and
  base-path handling.
- Preserve the call-number parser, PDF download naming convention, reading
  algorithm, and existing CSS book-model geometry.
- `subtitle` is explicit metadata. Never derive it from parentheses in `title`.
- Do not add a database, accounts, CMS, online reader, EPUB, pagination,
  sorting controls, tags routes, or unrelated redesign work.
- Do not commit, push, publish a Release, or deploy during implementation.
