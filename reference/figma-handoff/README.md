# Claude Code UI handoff

This directory is the implementation source of truth for the Figma-led UI
refactor and the PDF metadata automation work.

Claude Code must not call Figma MCP or depend on image recognition. The Figma
Starter plan is currently rate-limited, and all information required for code
implementation has been normalized into text and JSON here.

## Reading order

1. `claude-code-prompt.md` - task boundaries and required delivery format.
2. `design-tokens.json` - machine-readable design values and font roles.
3. `screens.json` - Figma frame-to-route mapping and page composition.
4. `implementation-spec.md` - route, data, search, classification, and
   responsive behavior.
5. `component-specs.md` - component markup and styling contracts.
6. `pdf-metadata-contract.md` - PDF/XMP fields and generated content schema.
7. `automation-spec.md` - GitHub Release ingestion and deployment workflow.
8. `acceptance-checklist.md` - completion and QA criteria.
9. `assets-status.json` - source-asset availability and blocking conditions.
10. `source/page2.svg` - normative original Page 2 export for Codex visual QA.
11. `source/page1.svg` - contextual Figma export; not a route specification.

## Figma source

- File: `DIMEpyuMSATUkeAjau7CGU`
- Page: `Page 2` (`43:1195`)
- Desktop frame size: `1280 x 832`
- URL: <https://www.figma.com/design/DIMEpyuMSATUkeAjau7CGU/Untitled?node-id=43-1195>

The seven frames are mapped in `screens.json`. The Figma file contains no
mobile frame and no book-detail frame. Mobile behavior and the detail page are
therefore governed by the written rules in this package.

## Priority order

When documents appear to conflict, use this order:

1. Data integrity and automation rules in `pdf-metadata-contract.md` and
   `automation-spec.md`.
2. Machine-readable values in `design-tokens.json` and `screens.json`.
3. Component behavior in `component-specs.md`.
4. Route composition in `implementation-spec.md`.
5. Existing code only where the handoff explicitly says to preserve it.

Do not infer missing values from the old Metro UI.

## Asset status

The original red `文火` wordmark is available at
`public/brand/wordmark.svg`. It is a path-only SVG with no font or raster
dependency. Use the file unchanged and provide a meaningful accessible label.

The original Page 1 and Page 2 Figma SVG exports are retained under `source/`.
Page 2 is the normative UI reference. Claude Code is not expected to parse the
multi-megabyte SVGs; the normalized JSON and Markdown remain its implementation
interface. Codex can render Page 2 during visual acceptance without consuming
additional Figma MCP calls.

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
