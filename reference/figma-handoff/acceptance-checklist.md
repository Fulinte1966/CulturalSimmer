# Acceptance checklist

## Handoff integrity

- [ ] `design-tokens.json`, `screens.json`, and `assets-status.json` parse as
      valid JSON.
- [ ] All seven Figma frame IDs and names match across the handoff.
- [ ] Routes and active-navigation values match across JSON and Markdown.
- [ ] Typography roles are consistent across tokens and component specs.
- [ ] No implementation instruction requires Claude Code to call Figma MCP or
      inspect a screenshot.
- [ ] Supplied `public/brand/wordmark.svg` is used unchanged.

## Automated checks

- [ ] `npm run test:metadata`
- [ ] `npm run test:reading`
- [ ] `npm run test:ui`
- [ ] `npm run validate`
- [ ] `npm run check`
- [ ] `npm run build`
- [ ] Pagefind indexes every book detail page.
- [ ] No test is skipped merely to obtain a green run.

## Metadata ingestion

- [ ] Complete XMP fixture extracts required fields.
- [ ] `pdfsubtitle` is read from `prism:subtitle`.
- [ ] Missing subtitle succeeds and creates no blank UI row.
- [ ] Parentheses in `title` remain part of title and are not interpreted.
- [ ] Missing required XMP fails before generated files are committed.
- [ ] Invalid ID, edition, classification, or volume relationship fails.
- [ ] Encrypted, empty, and non-A5 PDFs fail clearly.
- [ ] Custom total-volume values accept only positive integers.
- [ ] Tags are normalized and deduplicated in source order.
- [ ] Generated Markdown uses safe YAML serialization.
- [ ] Manifest records source IDs and SHA-256.
- [ ] Existing legacy PDF works only through explicit assets-only mode.

## Release workflow

- [ ] Only `ingest-*` published Releases enter the job.
- [ ] Canonical Release creation does not recurse.
- [ ] Exactly one PDF is required.
- [ ] Canonical tag and filename come from validated metadata.
- [ ] Duplicate call number and edition are rejected without overwrite.
- [ ] Validation and build finish before canonical publication.
- [ ] Push failure removes a newly created canonical Release and tag.
- [ ] Successful push deletes the temporary Release and tag.
- [ ] Downloaded PDFs never enter Git history.
- [ ] No force push, embedded PAT, or shell evaluation of metadata exists.
- [ ] Workflow job summary reports the processing result.

## Desktop visual QA: 1280 x 832

Check production preview at:

- [ ] `/ebook-library/`
- [ ] `/ebook-library/books/`
- [ ] `/ebook-library/search/`
- [ ] `/ebook-library/search/?q=政治经济学`
- [ ] `/ebook-library/categories/`
- [ ] `/ebook-library/categories/F/`
- [ ] `/ebook-library/categories/F0/`
- [ ] `/ebook-library/books/F0-1-1/`

For each applicable page:

- [ ] Content is constrained to approximately 1078px.
- [ ] Header shows the four navigation labels in the specified order.
- [ ] Header renders the supplied `文火` wordmark with an accessible label.
- [ ] Current navigation is visibly active and has `aria-current`.
- [ ] No old hero, Metro block, descriptive footer, gradient, pill, or nested
      card remains.
- [ ] Gallery is three columns and cover geometry is stable.
- [ ] Real and placeholder covers use their specified border colors.
- [ ] Call number is left aligned; title, subtitle, and author are centered.
- [ ] Author uses LXGW Neo ZhiSong Screen Regular at 16px.
- [ ] Optional subtitle/author rows collapse when absent.
- [ ] Long Chinese content wraps without collision or clipping.

## Responsive QA

At `390 x 844`, `360 x 800`, and `320 x 720`:

- [ ] No horizontal scrolling.
- [ ] Gallery uses two columns at 390 and one column at 360 or narrower as
      specified by tokens.
- [ ] Header wraps coherently without overlapping content.
- [ ] Search control fits the viewport.
- [ ] Classification codes and labels wrap without collision.
- [ ] Book detail becomes a single column.
- [ ] CSS model pseudo-elements are hidden and a flat cover is shown.
- [ ] Touch targets and visible focus states remain usable.

## Book model regression

- [ ] Front cover joins the spine without a black or white seam.
- [ ] Spine-side cover corners remain square.
- [ ] Outer front-cover corners remain rounded.
- [ ] Back cover is white with a gray outline and matching outer corners.
- [ ] Page block does not expose a large black edge.
- [ ] Existing first-pixel-column spine texture remains in use.
- [ ] Hover motion respects reduced-motion preference.
- [ ] Book model never covers title, metadata, or body content.

## Search QA

- [ ] Search query survives navigation through `?q=`.
- [ ] Production Pagefind module loads under the configured base path.
- [ ] Results use BookCard presentation and correct metadata.
- [ ] Generated cover and placeholder results both render.
- [ ] No body snippet appears.
- [ ] Loading, no-results, unavailable-index, and failure states are readable.
- [ ] `astro dev` absence of Pagefind causes no unhandled console error.

## Browser and accessibility

- [ ] Browser console contains no errors.
- [ ] All images have meaningful alternate text.
- [ ] Heading order is coherent.
- [ ] Keyboard navigation reaches brand, navigation, search, covers, titles,
      category links, and download action.
- [ ] Focus is visible against white and red elements.
- [ ] Color is not the only active-navigation indicator.
- [ ] Text remains readable at 200% browser zoom.

## Claude Code delivery

- [ ] Changed files are grouped by subsystem.
- [ ] Schema and public-interface changes are listed.
- [ ] Exact test results are included.
- [ ] Production preview URL is included.
- [ ] Desktop and mobile check results are included.
- [ ] Known deviations and GitHub permission assumptions are explicit.
- [ ] Worktree remains uncommitted, unpushed, and undeployed for Codex review.
