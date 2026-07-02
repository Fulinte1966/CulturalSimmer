# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static PDF ebook library — Astro static site deployed to GitHub Pages, PDFs hosted on GitHub Releases. Personal public-welfare project.

Homepage design source of truth: `reference/figma-handoff/current-home/`.
Do not call Figma MCP during implementation; freeze design values locally first.
The older handoff files remain useful for PDF metadata and automation notes,
but they are not the active homepage UI source.

Site config (`astro.config.mjs`): `site: "https://poyinte.github.io"`, `base: "ebook-library"`, `output: "static"`.

## Commands

```bash
npm run dev          # Astro dev server (no Pagefind — search won't work locally)
npm run check        # astro check — TypeScript diagnostics
npm run validate     # tsx scripts/validate-books.ts — validates all book entries
npm run test:reading # python scripts/test-reading-metrics.py — reading-metric unit tests
npm run test:metadata # python scripts/test_metadata.py — XMP extraction unit tests
npm run test:ingest  # python scripts/test_ingest_pdf.py — ingest orchestrator tests
npm run test:ui      # tsx --test tests/**/*.test.ts — UI utility unit tests
npm run build        # astro build && pagefind --site dist — production build
npm run preview      # astro preview — serves dist/ locally
```

**Important**: `astro dev` has no Pagefind index — search always returns empty.
Test search with `npm run build && npm run preview` instead.

## Architecture

### Data flow

```
PDF (GitHub Release)
  → extract_metadata.py (XMP extraction + validation)
    → ingest_pdf.py (markdown + manifest generation)
  → book_assets.py (PyMuPDF) generates:
      public/covers/{id}_v{edition}.png         — first-page cover image
      public/covers/{id}_v{edition}_spine.png   — 1px-wide spine sample
      src/data/outlines/{id}_v{edition}.json    — PDF bookmarks
      src/data/reading/{id}_v{edition}.json     — page count, character counts, estimated minutes

Markdown books (src/content/books/*.md)
  → Astro Content Collection (config.ts — Zod schema with optional subtitle)
    → books.ts (getAllBooks, getBookById, getBooksByClassification)
      └─ resolves covers (explicit → generated → placeholder), loads reading metrics
      → Homepage (NewspaperLayout + src/styles/home.css)
        → Components (BookCover, EditionStatus)
      → Catalog/detail/reserved pages (Layout)
        → Components (BookCard, BookCover, BookMeta, Outline)
```

### Call number system (the core abstraction)

Every book has a call number `id` like `A12-8-2`. `src/lib/bookId.ts` parses it and **derives everything**:

- `A12-8-2` → classification `A12`, accession 8, volume 2, workId `A12-8`
- `A8-3` → classification `A8`, accession 3, no volume, workId `A8-3`
- Regex: `/^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/` — supports `A8-3`, `A12-8-2`, `I210.4-1`, `T-1`, `Z228-1`

Display call numbers (`formatDisplayCallNumber`):
- `F0-1-1` → `F0/1:1`
- `A8-3` → `A8/3`
- `I210.4-1` → `I210.4/1`

**Never hand-write** `download_url`, `release_tag`, `pdf_filename`, `classification`, or `volume` in book markdown. These are all derived from `id` + `edition` by `bookId.ts` (+ `books.ts` for the GitHub URL using `siteConfig`).

`subtitle` is explicit metadata from frontmatter (or XMP). Never derive it from parentheses in `title`.

### Key files

| File | Role |
|---|---|
| `src/lib/bookId.ts` | Parse call numbers, format edition/volume, display call number, release tags & filenames |
| `src/lib/books.ts` | Query layer over content collection — `getAllBooks()`, `getBookById()`, `getBooksByClassification()`, `getDownloadUrl()`. Resolves covers and loads reading metrics |
| `src/lib/classification.ts` | Classification tree — reads `classifications.yml`, builds parent-child hierarchy, provides `getClassificationNodes()`, `getClassificationNode()`, `getClassificationAncestors()` |
| `src/lib/site.ts` | `siteConfig` — `githubOwner`, `githubRepo`, `weatherCity`, `frontPageSlogan` |
| `src/lib/basePath.ts` | `joinBasePath(base, pathname)` — joins base URL and pathname avoiding double slashes |
| `src/lib/uapis.ts` | API client for uapis.cn — Chinese calendar (lunar dates, holidays) and weather data |
| `src/content/config.ts` | Zod schema — validates id, title, subtitle, edition, date, tags, author, cover, total_volumes, readtime |
| `src/components/Layout.astro` | Standard catalog layout — branded header + 3-item nav |
| `src/components/NewspaperLayout.astro` | Full-page wrapper for the Figma-designed homepage — no nav |
| `src/components/EditionStatus.astro` | Real-time date/weather/lunar calendar bar (uapis API) |
| `src/data/classifications.yml` | `key: label` map of classification codes to Chinese names (85 entries, A–P) |
| `src/data/reading-config.json` | Reading speed config (CJK: 300 chars/min, Latin: 265 words/min) |
| `scripts/book_assets.py` | Core module — extracts cover, spine, outline, and reading metrics via PyMuPDF |
| `scripts/extract_metadata.py` | PDF XMP metadata extraction + validation (implements `pdf-metadata-contract.md`) |
| `scripts/test_metadata.py` | Unit tests for XMP extraction and validation (24 tests) |
| `scripts/test-reading-metrics.py` | Unit tests for `book_assets.py` |
| `scripts/test_ingest_pdf.py` | Unit tests for `ingest_pdf.py` |
| `scripts/ingest_pdf.py` | GitHub Actions orchestration — validates, generates, publishes, and cleans up PDF ingestion |
| `scripts/requirements.txt` | Python dependencies: PyMuPDF, PyYAML, defusedxml |
| `scripts/validate-books.ts` | Standalone validator (used in CI) |
| `.github/workflows/deploy.yml` | CI/CD — `npm ci` → `test:ui` → `validate` → `check` → `build` → deploy to GitHub Pages |
| `.github/workflows/ingest-pdf.yml` | PDF ingestion — triggers on `ingest-*` Release, extracts XMP, generates assets, creates canonical Release |
| `reference/figma-handoff/current-home/` | Active homepage design source of truth — frozen measurements, fonts, assets, QA notes |
| `reference/figma-handoff/` | Historical handoff notes plus PDF metadata and automation references |
| `plan.md` | Original implementation plan (22 sections, Chinese) |

### Dual layout system

Two layout components serve different page types:

**`Layout.astro`** — Standard catalog layout with branded header + 3-item nav (新书/索引/总览). Used by reserved pages (`/books/`, `/search/`, `/categories/`, `/categories/[classification]/`). Accepts `activeNav` and optionally `searchable`.

| activeNav | Label | Route |
|---|---|---|
| `new` | 新书 | `/` |
| `categories` | 索引 | `/categories/` |
| `overview` | 总览 | `/books/` |

**`NewspaperLayout.astro`** — Full-page Figma-designed wrapper for the front page (`/`). No nav, no branded header — just a minimal `<html>` wrapper. The homepage-specific CSS lives in `src/styles/home.css`.

### Cover system

`books.ts` resolves covers in 3 tiers:

1. **Explicit** (`coverKind: "explicit"`) — book frontmatter has a `cover` field
2. **Generated** (`coverKind: "generated"`) — `public/covers/{id}_v{edition}.png` exists on disk
3. **Placeholder** (`coverKind: "placeholder"`) — typographic fallback

Flat covers: 148/210 aspect ratio, 280px desktop target. Real covers show 1px dark-red border + 5px radius. Placeholders show 1px gray border. Model mode is unchanged from the original CSS geometry.

### Homepage handoff

Active homepage values live in `reference/figma-handoff/current-home/`:

| File | Role |
|---|---|
| `measurements.json` | Frozen Figma node dimensions and key component positions |
| `fonts.json` | Figma font names mapped to embedded files in `public/fonts/` |
| `assets.json` | Homepage asset inventory and usage |
| `qa-notes.md` | Known dynamic-data and preview caveats |

The homepage targets the fixed `1440 x 1024` Figma viewport. Do not add
responsive rules until a separate mobile/tablet design is supplied.

### Responsive breakpoints

- Desktop ≥960px: 3-column gallery
- Tablet 560–959px: 2-column
- Mobile 361–559px: 2-column with mobile gutters, nav wraps
- Narrow ≤360px: 1-column
- ≤560px: book detail single-column with flat cover, model pseudo-elements hidden

### 3D book model + debug workbench

The `.book-cover--model` element uses CSS pseudo-elements for spine, back cover, page edges, and shadow. All dimensions controlled by CSS custom properties. At ≤560px, pseudo-elements are hidden and a flat cover is shown.

**Spine darkening**: Uses `background-image` gradient overlay (`linear-gradient(rgb(0 0 0 / calc(1 - brightness)), …)`) instead of global.css's `box-shadow: inset`. The debug CSS overrides with `box-shadow: none` to prevent the inset shadow from darkening the spine border.

**Unified border system**: Cover surface, spine `::after`, and back cover `volume::after` all share `border-color: var(--border-color, #555)`. The `--border-color` is computed in JS from the `border-color-depth` slider. Spine gets `border-right: 0` (cover junction); cover gets `border-left: 0` (spine junction). `--model-border` defaults to 3px.

**Shadow system**: Replaced the global.css single blurred pill (`::before` with `blur(12px)` + `skewX(45deg)`) with a `clip-path` trapezoid anchored to the book's 3D bottom contour. Gradient `linear-gradient(to bottom, 30% → 10% → 3% → 0)` simulates contact/penumbra/ambient layers. Left anchor fixed at 163px from element edge. Right anchor Y follows `-var(--book-size)` dynamically.

**Debug workbench** (`/debug/book-model`):
- `src/pages/debug/book-model.astro` — interactive geometry tuning page
- `src/styles/book-model-debug.css` — debug-only overrides (higher specificity than global.css)
- Live controls for stage, cover image, surface alignment, spine/pages, border color/depth, shadow shape
- "隐藏封面" toggle for shadow tuning
- CSS output panel for copying tuned values to production (`book-detail.css`)
- localStorage persistence with versioned keys (`v4`)

### Pagefind

Custom JavaScript API (`search.astro`) — dynamic import of `pagefind/pagefind.js`, custom result renderer using BookCard DOM contract. No body snippets. Query survives navigation via `?q=`.

### Base path

All internal links must use `import.meta.env.BASE_URL` (resolves to `/ebook-library/` in production).

## Adding a book

### XMP-based ingestion

1. Compile PDF with XMP metadata (see `reference/figma-handoff/pdf-metadata-contract.md` for required fields)
2. Create temporary GitHub Release with tag `ingest-YYYYMMDD-HHMM`, attach PDF
3. GitHub Actions (`ingest-pdf.yml`) extracts XMP, validates, generates all assets, creates canonical Release

### Manual entry

1. Determine call number (e.g., `A12-8-2`)
2. Create `src/content/books/A12-8-2.md` with frontmatter (id, title, subtitle?, edition, date, tags, author?, cover?, total_volumes?, readtime?)
3. Generate static assets from PDF:
   ```bash
   pip install PyMuPDF
   python scripts/extract-book-assets.py path/to/A12-8-2_v1.pdf A12-8-2 1
   ```
   This produces: `public/covers/{id}_v{edition}.png`, `public/covers/{id}_v{edition}_spine.png`, `src/data/outlines/{id}_v{edition}.json`, `src/data/reading/{id}_v{edition}.json`
4. Commit the .md and all generated assets, push to `main`

## Constraints

- **No** database, user accounts, comments, CMS, SSR, online PDF reader
- **No** EPUB/MOBI/HTML formats — PDF only
- **No** dark mode, complex UI, client framework, CSS framework
- **No** About page, standalone copyright page
- **No** outline-to-PDF page linking — outline is display-only
- **No** GitHub Release existence check at build time (offline-safe)
- **No** gradient, decorative shadow, Metro blocks, pills, nested cards
- `subtitle` must come from explicit metadata — never derived from title
- `public/brand/wordmark.svg` used unchanged — do not redraw, trace, or replace
- CSS uses 2-space indentation — always `Read` before `Edit`
