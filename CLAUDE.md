# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static PDF ebook library — Astro static site deployed to GitHub Pages, PDFs hosted on GitHub Releases. Personal public-welfare project.

Homepage design source of truth: `reference/figma-handoff/current-home/`.
Do not call Figma MCP during implementation; freeze design values locally first.
The older handoff files remain useful for PDF metadata and automation notes,
but they are not the active homepage UI source.

Site config (`astro.config.mjs`): `site: "https://fulinte1966.github.io"`, `base: "/CulturalSimmer"`, `output: "static"`.

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
      src/data/reading/{id}_v{edition}.json     — page count, character counts, file size

Markdown books (src/content/books/*.md)
  → Astro Content Collection (config.ts — Zod schema with optional subtitle)
    → books.ts (getAllBooks, getBookById, getBooksByClassification)
      └─ resolves covers (explicit → generated → placeholder), loads reading metrics
      → Homepage (index.astro + src/styles/home.css)
        → Components (BookCover)
      → Catalog/detail pages (Layout or NewspaperLayout)
        → Components (BookCard, BookCover, BookMeta, Outline, ReadingStats, DownloadButton)
```

All derived fields — `downloadUrl`, `release_tag`, `pdf_filename`, `classification`, `volume` — are computed from `id` + the latest `editions[].edition` by `bookId.ts` and `books.ts`. Never hand-write them in book markdown frontmatter.

`subtitle` is explicit metadata from frontmatter (or XMP). Never derive it from parentheses in `title`.

### Call number system (the core abstraction)

Every book has a call number `id` like `A12-8-2`. `src/lib/bookId.ts` parses it and **derives everything**:

- `A12-8-2` → classification `A12`, accession 8, volume 2, workId `A12-8`
- `A8-3` → classification `A8`, accession 3, no volume, workId `A8-3`
- Regex: `/^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/` — supports `A8-3`, `A12-8-2`, `I210.4-1`, `T-1`, `Z228-1`

Display call numbers (`formatDisplayCallNumber`):
- `F0-1-1` → `F0/1:1`
- `A8-3` → `A8/3`
- `I210.4-1` → `I210.4/1`

### Base path

All internal links and asset URLs must use `import.meta.env.BASE_URL` (resolves to `/CulturalSimmer/` in production). Use `joinBasePath(base, pathname)` from `src/lib/basePath.ts` — it avoids double slashes.

### Site config

`src/lib/site.ts` is the single source for GitHub owner/repo, weather city, and front-page slogan. The slogan renders on the homepage as the "毛主席语录" quote block.

### Key files

| File | Role |
|---|---|
| `src/lib/bookId.ts` | Parse call numbers, format edition/volume, display call number, release tags & filenames |
| `src/lib/books.ts` | Query layer over content collection — `getAllBooks()`, `getBookById()`, `getBooksByClassification()`, `getDownloadUrl()`. Resolves covers and loads reading metrics |
| `src/lib/classification.ts` | Classification tree — reads `classifications.yml`, builds parent-child hierarchy, provides `getClassificationNodes()`, `getClassificationNode()`, `getClassificationAncestors()` |
| `src/lib/site.ts` | `siteConfig` — `githubOwner`, `githubRepo`, `weatherCity`, `frontPageSlogan` |
| `src/lib/basePath.ts` | `joinBasePath(base, pathname)` — joins base URL and pathname avoiding double slashes |
| `src/lib/uapis.ts` | API client for uapis.cn — Chinese calendar (lunar dates, holidays) and weather data. Both server-side (Astro frontmatter) and client-side (`<script>` fetch in index.astro) |
| `src/content/config.ts` | Zod schema — validates id, title, subtitle, description, tags, author, cover, editions, total_volumes |
| `src/components/Layout.astro` | Standard catalog layout — branded header + 3-item nav (新书/索引/总览) |
| `src/components/NewspaperLayout.astro` | Full-page Figma-designed wrapper — no nav, minimal `<html>` skeleton. Used by homepage and book detail |
| `src/components/BookCover.astro` | Dual-mode cover component — `flat` (2D card) and `model` (3D CSS pseudo-elements) |
| `src/components/BookCard.astro` | Catalog list item — BookCover + call number + title |
| `src/components/EditionStatus.astro` | Reusable date/weather/lunar calendar bar (available but not used by current pages; pages fetch data directly) |
| `src/data/classifications.yml` | `key: label` map of classification codes to Chinese names (85 entries, A–P) |
| `scripts/book_assets.py` | Core module — extracts cover, spine, outline, and reading metrics via PyMuPDF |
| `scripts/extract_metadata.py` | PDF XMP metadata extraction + validation |
| `scripts/ebook_upload.py` | Local preflight + temporary ingest Release creation |
| `scripts/edition_policy.py` | Shared edition sequencing checks for local upload and CI ingest |
| `scripts/ingest_pdf.py` | GitHub Actions orchestration — validates, generates, publishes, and cleans up PDF ingestion |
| `scripts/validate-books.ts` | Standalone validator (used in CI) — checks call numbers, editions, classifications, outlines |
| `scripts/requirements.txt` | Python dependencies: PyMuPDF, PyYAML, defusedxml |
| `.github/workflows/deploy.yml` | CI/CD — `npm ci` → `test:ui` → `validate` → `check` → `build` → deploy to GitHub Pages. Also runs daily at UTC 16:00 (midnight Beijing time) to refresh weather data |
| `.github/workflows/ingest-pdf.yml` | PDF ingestion — triggers on `ingest-*` Release, extracts XMP, generates assets, creates canonical Release |
| `reference/figma-handoff/current-home/` | Active homepage design source of truth — frozen measurements, fonts, assets, QA notes |

### CSS architecture

Four stylesheets with strict separation:

| File | Scope |
|---|---|
| `src/styles/global.css` | CSS reset, shared typography, layout basics, `.book-cover--model` 3D geometry, `.book-cover--flat` styles, catalog grid, responsive breakpoints, `.site-header`/`.site-nav`, `.edition-status` |
| `src/styles/home.css` | Homepage-only — `.figma-homepage` frame, masthead, newsletter, shelf, weather footer. **Must NOT** leak into global.css |
| `src/styles/book-detail.css` | Book detail page — `.bd-*` grid/text/metadata/actions, 3D cover stage, abstract/outline/intro typography |
| `src/styles/category-index.css` | Classification index page — `.fm-index-*` tree browser, book grid, pagination |

CSS uses 2-space indentation. Always `Read` before `Edit`.

### Dual layout system

Two layout components serve different page types:

**`Layout.astro`** — Standard catalog layout with branded header + 3-item nav (新书/索引/总览). Used by reserved pages (`/books/`, `/search/`, `/categories/`, `/categories/[classification]/`). Accepts `activeNav` and optionally `searchable`.

| activeNav | Label | Route |
|---|---|---|
| `new` | 新书 | `/` |
| `categories` | 索引 | `/categories/` |
| `overview` | 总览 | `/books/` |

**`NewspaperLayout.astro`** — Full-page Figma-designed wrapper for the front page (`/`), book detail (`/books/[id]/`), and category index (`/categories/`). No nav, no branded header — just a minimal `<html>` wrapper.

### Page status

| Route | Status | Layout |
|---|---|---|
| `/` | **Complete** — Figma newspaper design with lead book, shelf, weather | NewspaperLayout |
| `/books/[id]/` | **Complete** — 3D book model, metadata, outline, download | NewspaperLayout |
| `/categories/` | **Complete** — classification tree browser with call number/keyword modes, book grid | NewspaperLayout |
| `/categories/[classification]/` | **Placeholder** — reserved page | Layout |
| `/books/` | **Placeholder** — reserved page ("总览页待设计") | Layout |
| `/search/` | **Placeholder** — "搜索功能暂时关闭" | Layout |

### Cover system

`books.ts` resolves covers in 3 tiers:

1. **Explicit** (`coverKind: "explicit"`) — book frontmatter has a `cover` field
2. **Generated** (`coverKind: "generated"`) — `public/covers/{id}_v{edition}.png` exists on disk
3. **Placeholder** (`coverKind: "placeholder"`) — typographic fallback (author + title rendered in CSS)

Flat covers: 148/210 aspect ratio, 280px desktop target. Real covers show 1px dark-red border + 5px radius. Placeholders show 1px gray border.

### Data directories

Two generated-data directories use the pattern `{id}_v{edition}.json`:

- `src/data/outlines/` — PDF bookmarks as `OutlineItem[]` (`{ level, title }`)
- `src/data/reading/` — `ReadingMetrics` (`{ page_count, cjk_character_count, latin_token_count, file_size_bytes }`)

Both are produced by `book_assets.py` and read by `books.ts` at build time. Missing outlines produce a warning in `validate-books`; missing reading metrics hide the reading-stats display.

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

### Weather/calendar dual-fetch

Both the homepage (`index.astro`) and book detail page (`[id].astro`) fetch calendar and weather data **server-side** in Astro frontmatter via `uapis.ts`. The homepage additionally runs a **client-side** `fetch()` in a `<script>` block to refresh weather after page load (gracefully degrades if rate-limited).

The deploy workflow runs daily at UTC 16:00 (midnight Beijing) to rebuild with fresh data.

### Responsive breakpoints

- Desktop ≥960px: 3-column gallery
- Tablet 560–959px: 2-column
- Mobile 361–559px: 2-column with mobile gutters, nav wraps
- Narrow ≤360px: 1-column
- ≤560px: book detail single-column with flat cover, model pseudo-elements hidden

### 3D book model

The `.book-cover--model` element uses CSS pseudo-elements for spine, back cover, page edges, and shadow. All dimensions controlled by CSS custom properties. At ≤560px, pseudo-elements are hidden and a flat cover is shown.

Model thickness is computed from page count: `Math.round(Math.sqrt(pageCount) * 1.9)`, clamped to 18–42px.

**Spine darkening**: Uses `background-image` gradient overlay (`linear-gradient(rgb(0 0 0 / calc(1 - brightness)), …)`) instead of global.css's `box-shadow: inset`.

**Unified border system**: Cover surface, spine `::after`, and back cover `volume::after` all share `border-color: var(--border-color, #555)`. Spine gets `border-right: 0` (cover junction); cover gets `border-left: 0` (spine junction). `--model-border` defaults to 3px.

**Shadow system**: `clip-path` trapezoid anchored to the 3D book's bottom contour. Gradient `linear-gradient(to bottom, 30% → 10% → 3% → 0)` simulates contact/penumbra/ambient layers. Left anchor fixed at 163px from element edge. Right anchor Y follows `-var(--book-size)` dynamically.

### Client-side JS patterns

No JS framework. Key interactive behaviors use vanilla JS with custom state management:

- **Homepage shelf** (`index.astro` `<script>`) — pointer-event-based scroll/drag with inertia glide, edge-pull resistance, snap-to-item, reduced-motion support. ~500 lines of custom physics.
- **Classification tree** (`categories/index.astro` `<script>`) — state machine for call number/keyword browsing modes, pagination, dynamic DOM rendering. Uses `byCode`/`parentOf` Maps over an in-memory tree.

### Pagefind

Custom JavaScript API (`search.astro`) — dynamic import of `pagefind/pagefind.js`, custom result renderer using BookCard DOM contract. No body snippets. Query survives navigation via `?q=`.

## Adding a book

### XMP-based ingestion

1. Compile PDF with XMP metadata (see `reference/figma-handoff/pdf-metadata-contract.md` for required fields)
2. Run `npm run ebook:upload path/to/book.pdf -- --dry-run`
3. Run `npm run ebook:upload path/to/book.pdf`
4. GitHub Actions (`ingest-pdf.yml`) extracts XMP, validates expected edition sequencing, generates all assets/manifests, creates canonical Release, commits generated files, and deletes the temporary ingest Release

Manual entries are discouraged. If emergency repair is needed, keep markdown in the `editions[]` shape and let generated asset names continue to use `{id}_v{edition}`.

## Constraints

- **No** database, user accounts, comments, CMS, SSR, online PDF reader
- **No** EPUB/MOBI/HTML formats — PDF only
- **No** dark mode, client framework, CSS framework
- **No** About page, standalone copyright page
- **No** outline-to-PDF page linking — outline is display-only
- **No** GitHub Release existence check at build time (offline-safe)
- `subtitle` must come from explicit metadata — never derived from title
- `public/brand/wordmark.svg` used unchanged — do not redraw, trace, or replace
- CSS uses 2-space indentation — always `Read` before `Edit`
- Homepage styles (`home.css`) must not leak into `global.css` — separate files, separate scopes
