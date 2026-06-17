# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static PDF ebook library — Astro static site deployed to GitHub Pages, PDFs hosted on GitHub Releases. Personal public-welfare project. v1: functional, no complex UI.

## Commands

```bash
npm run dev         # Astro dev server (no Pagefind — search won't work locally)
npm run check       # astro check — TypeScript diagnostics
npm run validate    # tsx scripts/validate-books.ts — validates all book entries
npm run build       # astro build && pagefind --site dist — production build
npm run preview     # astro preview — serves dist/ locally
```

## Architecture

### Data flow

```
Markdown books (src/content/books/*.md)
  → Astro Content Collection (config.ts — Zod schema)
    → books.ts (getAllBooks, getBookById, getBooksByClassification)
      → Astro pages (index, books/[id], categories/[classification])
        → Components (BookCard, BookMeta, DownloadButton, Outline)
```

### Call number system (the core abstraction)

Every book has a call number `id` like `A12-8-2`. `src/lib/bookId.ts` parses it and **derives everything**:

- `A12-8-2` → classification `A12`, accession 8, volume 2, workId `A12-8`
- `A8-3` → classification `A8`, accession 3, no volume, workId `A8-3`
- Regex: `/^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/` — supports `A8-3`, `A12-8-2`, `I210.4-1`, `T-1`, `Z228-1`

**Never hand-write** `download_url`, `release_tag`, `pdf_filename`, `classification`, or `volume` in book markdown. These are all derived from `id` + `edition` by `bookId.ts` (+ `books.ts` for the GitHub URL using `siteConfig`).

### Key files

| File | Role |
|---|---|
| `src/lib/bookId.ts` | Parse call numbers, format edition/volume, generate release tags & filenames |
| `src/lib/books.ts` | Query layer over content collection — `getAllBooks()`, `getBookById()`, `getBooksByClassification()`, `getDownloadUrl()` |
| `src/lib/site.ts` | `siteConfig` — `githubOwner` and `githubRepo` (change these if the repo moves) |
| `src/content/config.ts` | Zod schema for book frontmatter — validates id regex, edition, date, etc. |
| `src/data/classifications.yml` | `key: label` map of classification codes to Chinese names |
| `scripts/validate-books.ts` | Standalone validator (used in CI) — checks id format, classification existence, outline existence, duplicates |
| `scripts/extract-outline.py` | PyMuPDF script — extracts PDF bookmarks to `{level, title, page}` JSON |
| `scripts/extract-outline-from-release.sh` | Downloads a PDF from a GitHub Release then runs extract-outline.py |
| `astro.config.mjs` | `site: "https://poyinte.github.io"`, `base: "ebook-library"`, `output: "static"` |

### Outline JSON

Located at `src/data/outlines/{id}_v{edition}.json`. Structure: `[{ level, title, page }]`. Loaded at build time via `fs.readFileSync` in `[id].astro`. Empty array `[]` means no bookmarks — the Outline component won't render anything.

### Pagefind

Runs as a post-build step (`pagefind --site dist`). The search page (`search.astro`) loads Pagefind UI JS/CSS from the built `dist/pagefind/` at runtime. In dev mode (`astro dev`), search silently does nothing — that's expected.

### Base path

All internal links must use `import.meta.env.BASE_URL` (resolves to `/ebook-library/` in production). The pattern is `` `${base}/path/` `` — note the `/` separator between base and path. Astro config sets `base: "ebook-library"` (no leading/trailing slash — Astro normalizes it).

### Styling

Single global stylesheet (`src/styles/global.css`) with CSS custom properties. No CSS framework, no dark mode, no responsive breakpoints beyond basic max-width — v1 is functional only.

## Adding a book

1. Determine call number (e.g., `A12-8-2`)
2. Compile PDF, name it `A12-8-2_v1.pdf`
3. Create GitHub Release with tag `A12-8-2_v1`, upload PDF
4. Create `src/content/books/A12-8-2.md` with frontmatter (id, title, edition, date, tags — author/cover/total_volumes optional)
5. Run `./scripts/extract-outline-from-release.sh A12-8-2 1` (needs `gh` CLI + PyMuPDF)
6. Commit the .md and generated .json, push to `main`
7. GitHub Actions deploys automatically

## Constraints (v1)

- **No** database, user accounts, comments, CMS, SSR, online PDF reader
- **No** EPUB/MOBI/HTML formats — PDF only
- **No** complex UI, dark mode, responsive design beyond basic
- **No** About page, standalone copyright page
- **No** hierarchical classification browsing — `/categories/A12/` only shows exact `A12-*` books, not subcategories
- **No** outline-to-PDF page linking — outline is display-only
- **No** GitHub Release existence check at build time (offline-safe)
