# CLAUDE.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project

Static PDF ebook library — Astro static site deployed to GitHub Pages, PDFs hosted on GitHub Releases. Personal public-welfare project. Design tokens and component specs are in `reference/figma-handoff/`.

## Commands

```bash
npm run dev          # Astro dev server (no Pagefind — search won't work locally)
npm run check        # astro check — TypeScript diagnostics
npm run validate     # tsx scripts/validate-books.ts — validates all book entries
npm run test:reading # python scripts/test-reading-metrics.py — reading-metric unit tests
npm run test:metadata # python scripts/test_metadata.py — XMP extraction unit tests
npm run build        # astro build && pagefind --site dist — production build
npm run preview      # astro preview — serves dist/ locally
```

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
      → Astro pages (index, books/[id], books/, categories/, categories/[classification], search/)
        → Components (Layout, BookCover, BookCard, BookMeta, DownloadButton, ReadingStats, Outline)
```

### Call number system (the core abstraction)

Every book has a call number `id` like `A12-8-2`. `src/lib/bookId.ts` parses it and **derives everything**:

- `A12-8-2` → classification `A12`, accession 8, volume 2, workId `A12-8`
- `A8-3` → classification `A8`, accession 3, no volume, workId `A8-3`
- Regex: `/^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/` — supports `A8-3`, `A12-8-2`, `I210.4-1`, `T-1`, `Z228-1`

Display call numbers (`formatDisplayCallNumber`):
- `F0-1-1` → `F0/1:1`
- `A8-3` → `A8/3`

**Never hand-write** `download_url`, `release_tag`, `pdf_filename`, `classification`, or `volume` in book markdown. Markdown stores book-level metadata plus `editions[]`; the current display/download edition is derived from the largest `editions[].edition`.

`subtitle` is explicit metadata. Never derive it from parentheses in `title`.

### Key files

| File | Role |
|---|---|
| `src/lib/bookId.ts` | Parse call numbers, format edition/volume, display call number, release tags & filenames |
| `src/lib/books.ts` | Query layer — `getAllBooks()`, `getBookById()`, `getBooksByClassification()`, cover resolution, reading metrics |
| `src/lib/classification.ts` | Classification tree — parent-child hierarchy from YAML |
| `src/lib/site.ts` | `siteConfig` — `githubOwner` and `githubRepo` |
| `src/content/config.ts` | Zod schema — validates id, title, subtitle, description, tags, author, cover, editions, total_volumes |
| `scripts/ebook_upload.py` | Local preflight + temporary ingest Release creation |
| `scripts/edition_policy.py` | Shared edition sequencing checks for local upload and CI ingest |
| `scripts/book_assets.py` | Core module — extracts cover, spine, outline, reading metrics via PyMuPDF |
| `scripts/extract_metadata.py` | PDF XMP metadata extraction + validation |
| `scripts/test_metadata.py` | Unit tests for XMP extraction and validation |
| `scripts/ingest_pdf.py` | GitHub Actions orchestration for PDF ingestion |
| `scripts/requirements.txt` | Python dependencies |
| `scripts/validate-books.ts` | Standalone validator (used in CI) |
| `.github/workflows/deploy.yml` | CI/CD — deploy to GitHub Pages |
| `.github/workflows/ingest-pdf.yml` | PDF ingestion workflow |

### Layout and navigation

`Layout.astro` accepts `activeNav: "new" | "search" | "categories" | "overview"` and renders the brand wordmark (`public/brand/wordmark.svg`) and four-item nav.

### Cover system

Flat covers: 148/210 ratio, 280px target. Real covers: 1px dark-red border + 5px radius. Placeholders: 1px gray border. Model mode preserved.

### Design tokens

Colors: `--paper: #FFF`, `--ink: #171717`, `--muted: #8A8882`, `--rule: #DCDAD3`, `--accent: #84251F`, `--accent-hover: #5E1713`. Full tokens in `reference/figma-handoff/design-tokens.json`.

### Responsive breakpoints

Desktop ≥960px: 3-col. Tablet 560–959px: 2-col. Mobile 361–559px: 2-col with mobile gutters. Narrow ≤360px: 1-col. ≤560px: single-column detail, flat cover.

### 3D book model (preserved)

CSS pseudo-elements for spine, back cover, page edges, shadow. At ≤560px pseudo-elements hidden. Spine seam repaint workaround preserved.

### Base path

All internal links use `import.meta.env.BASE_URL` (`/CulturalSimmer/` in production).

## Constraints

- **No** database, accounts, CMS, SSR, online reader, EPUB, client framework, CSS framework, dark mode
- **No** gradient, decorative shadow, Metro blocks, pills, nested cards
- `subtitle` explicit only — never derived from title
- `public/brand/wordmark.svg` used unchanged
