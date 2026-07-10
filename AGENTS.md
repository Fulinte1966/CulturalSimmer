# AGENTS.md

Guidance for Codex and other coding agents working in this repository.

## Project

CulturalSimmer is an Astro static PDF ebook library. GitHub Pages hosts the site, GitHub Releases host PDF files, and GitHub Actions ingests PDFs into generated book data and public cover assets.

## Commands

```bash
npm run dev           # Astro dev server; Pagefind search is not indexed here
npm run check         # astro check
npm run validate      # validate generated/content book data
npm run test:ui       # Node tests under tests/node/
npm run test:reading  # Python reading metric tests under tests/python/
npm run test:metadata # Python XMP metadata tests under tests/python/
npm run test:ingest   # Python ingest orchestration tests under tests/python/
npm run test:changelog # PDF snapshot, content diff, and Release Markdown tests
npm run build         # Astro build plus Pagefind index
npm run preview       # serve dist/ locally
```

Run the relevant tests before changing ingestion, metadata, book data, or asset paths. For broad cleanup, run all tests plus `npm run validate`, `npm run check`, and `npm run build`.

## Architecture

PDF intake flow:

```text
temporary ingest-* GitHub Release
  -> scripts/extract_metadata.py validates PDF XMP
  -> scripts/extract_content_snapshot.py normalizes final PDF content
  -> scripts/compare_content_snapshots.py compares adjacent editions
  -> scripts/ingest_pdf.py orchestrates generation and publishing
  -> scripts/book_assets.py generates covers, spine samples, outlines, and reading metrics
  -> src/content/books/, src/data/, and public/covers/ update the static site
```

Runtime site code lives in `src/`:

- `src/pages/`: Astro routes.
- `src/components/`: shared Astro components.
- `src/lib/`: base path, book, classification, outline, site, and API helpers.
- `src/scripts/`: browser-side TypeScript modules.
- `src/styles/`: page and global CSS.
- `src/content/books/`: generated Markdown book records.
- `src/data/`: classifications plus generated manifests, outlines, and reading metrics.

Automation and tooling:

- `.github/workflows/deploy.yml`: tests, validates, builds, and deploys GitHub Pages.
- `.github/workflows/ingest-pdf.yml`: release-triggered PDF ingestion.
- `scripts/ebook_upload.py`: local preflight and temporary release creation.
- `scripts/validate-books.ts`: standalone content/data validator.
- `scripts/requirements.txt`: Python dependencies for ingestion and PDF asset extraction.

## Book Data Rules

The book call number `id` is the core identifier, parsed by `src/lib/bookId.ts`.

- Do not hand-write `downloadUrl`, `releaseTag`, `pdfFilename`, `classification`, or `volume` in Markdown.
- Do not infer `subtitle` from parentheses in `title`; `subtitle` is explicit metadata.
- Current display and download edition are derived from the largest `editions[].edition`.
- PDF metadata requirements are documented in `docs/pdf/metadata-contract.md`.
- The LaTeX helper for XMP metadata is in `docs/latex/culturalsimmer-ebook-metadata.sty`.
- Never use Git tag diffs, commit history, LaTeX source diffs, or PDF binary diffs as an electronic-book content changelog.
- Release changelogs must come from normalized final-PDF snapshots; see `docs/release-changelog-conventions.md`.

## Asset Rules

Runtime decorative assets live under `public/assets/`:

- `public/assets/brand/`: stable brand marks, such as `culturalsimmer-wordmark.svg`.
- `public/assets/badges/`: badge, label, and stamp SVGs.
- `public/assets/decor/`: ornamental dividers, borders, and rules.
- `public/assets/textures/`: repeatable textures.
- `public/covers/`: generated book covers and spine samples; do not hand-edit or rename.
- `public/fonts/`: vendored font files; preserve upstream font names unless there is a strong reason.
- `src/assets/icons/`: assets imported by Astro/Vite modules.

Use lowercase kebab-case for project-authored assets and prefer role-first names. See `docs/asset-conventions.md`.

For public URLs in Astro components and pages, use `joinBasePath(import.meta.env.BASE_URL, "...")`. CSS-only URLs currently include the GitHub Pages base path.

## Repository Hygiene

- Do not reintroduce Figma Make export projects, shadcn component dumps, full-page SVG source exports, historical planning files, or local-only PDFs into the runtime repository.
- Preserve concise, durable contracts as Markdown under `docs/`.
- Do not commit `node_modules/`, `dist/`, `.astro/`, `.cache/`, or `__pycache__/`.
- Keep cleanup PRs focused on file organization, references, naming, documentation, and necessary path/test fixes.
