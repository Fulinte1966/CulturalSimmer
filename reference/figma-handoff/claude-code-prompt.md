# Claude Code implementation prompt

Implement the Figma-led ebook-library UI refactor and PDF metadata automation
in this repository.

## Mandatory preparation

Read, in order:

1. `AGENTS.md`
2. `reference/figma-handoff/README.md`
3. every remaining file in `reference/figma-handoff/`
4. the current implementations under `src/components/`, `src/lib/`,
   `src/pages/`, `scripts/`, and `.github/workflows/`

Treat `design-tokens.json` and `screens.json` as the Figma source of truth.

## Hard constraints

- Do not call Figma MCP. It is rate-limited and unnecessary for implementation.
- Do not depend on screenshots or image recognition.
- Do not guess values from the old UI when the handoff specifies them.
- Use `public/brand/wordmark.svg` unchanged for the `文火` brand. Do not redraw,
  trace, recolor, or replace it with text.
- Do not derive a subtitle from full-width parentheses or any title text.
- `subtitle` must come from PDF XMP metadata and generated frontmatter.
- Preserve the existing CSS book-model geometry, including the spine seam
  repaint workaround and the mobile flat-cover fallback.
- Preserve the CJK/Latin reading-time algorithm and sparse-page behavior.
- Preserve `import.meta.env.BASE_URL` for every internal URL and asset.
- Do not commit, push, deploy, publish, edit, or delete a real GitHub Release.
- Do not overwrite unrelated user changes.

## Required implementation sequence

1. Establish metadata types, subtitle schema, XMP extraction, validation, and
   tests before changing UI components.
2. Add classification-tree and display-call-number helpers with unit tests.
3. Refactor the shared Layout, BookCover, and BookCard.
4. Implement `/`, `/books/`, `/categories/`, and category routes.
5. Replace default Pagefind UI with the written custom search behavior.
6. Integrate explicit subtitle metadata into the detail page without rewriting
   the book model.
7. Add GitHub ingestion workflow files and dry-runable scripts. Do not trigger
   them against the real repository.
8. Apply responsive styling and run browser QA against the acceptance matrix.
9. Update documentation only after behavior and tests are correct.

Work in focused patches. Run `npm run check` after each TypeScript/Astro batch.
Inspect the diff before moving to the next subsystem.

## Required commands

At minimum, complete successfully:

```powershell
npm run test:metadata
npm run test:reading
npm run test:ui
npm run validate
npm run check
npm run build
```

If Windows sandbox permissions block Python's system temporary directory, set
`TEMP` and `TMP` to a workspace-local `.tmp` directory for the test process.
Do not weaken or delete the affected test.

Use production build plus preview to verify Pagefind. `astro dev` does not
contain the Pagefind index.

## Delivery format

Return all of the following:

- changed and added files grouped by subsystem;
- public interfaces or schemas added or changed;
- exact command results;
- production preview URL;
- desktop and mobile browser-check results;
- known differences from this handoff;
- confirmation that the supplied wordmark is used without modification;
- any GitHub permission, default-branch, or branch-protection assumptions.

Do not claim completion while required checks fail. Leave the worktree
uncommitted for Codex acceptance and debugging.
