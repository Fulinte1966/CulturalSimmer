---
name: figma-make-page-deployment
description: Use when deploying a Figma Make exported page into the CulturalSimmer Astro site, especially homepage or book detail pages. Applies to replacing or adapting generated Figma Make HTML/CSS/assets into maintainable Astro pages while preserving the project's PDF data pipeline, base path, fonts, and browser QA workflow.
---

# Figma Make Page Deployment

Use this skill when the user says things like:

- "把 Figma Make 搭建的页面部署进项目"
- "参考 `reference/figma-make/...` 制作页面"
- "弃用已有 UI, 按 Figma Make 重新做某个页面"
- "主页/详情页和设计稿不一致, 调整页面"

This skill is specific to `D:\Claude\projects\CulturalSimmer`.

## Project Fit

Keep the implementation in the existing Astro stack:

- Astro pages and components
- plain CSS files under `src/styles/`
- static assets under `public/`
- no React, Tailwind, shadcn, client-side framework, database, SSR, or CMS

Preserve the ebook data pipeline. Do not refactor PDF ingestion, reading metrics, book ID parsing, release URLs, or content schema unless the user explicitly asks.

## Source Order

Before editing a page, read these in order:

1. `AGENTS.md`
2. `CLAUDE.md`
3. The relevant Figma Make folder, for example `reference/figma-make/Homepage/` or `reference/figma-make/BookDetail/`
4. The current route file, for example `src/pages/index.astro` or `src/pages/books/[id].astro`
5. The current page-specific stylesheet, for example `src/styles/home.css`
6. Related assets under `public/brand/`, `public/fonts/`, and `public/covers/`

Do not call Figma MCP during implementation unless the user explicitly asks. Prefer local frozen Figma Make files and local exported SVG/HTML/CSS.

## Deployment Pattern

Use Figma Make as a visual scaffold, not as a framework migration.

1. Extract the page structure and measurements from the Figma Make source.
2. Keep dynamic content in Astro expressions instead of hard-coded generated text.
3. Move page-specific CSS into a dedicated stylesheet with a unique prefix:
   - homepage: `fm-*` classes in `src/styles/home.css`
   - book detail: prefer `bd-*` or another route-specific prefix
4. Keep global CSS minimal. Do not pile Figma page rules into `global.css`.
5. Copy only necessary static assets to `public/`, and reference them through `import.meta.env.BASE_URL` helpers or stable `/ebook-library/...` paths already used by the page.
6. Preserve internal links with `joinBasePath(base, "...")`.

## Layout Lessons From Homepage

The homepage started as a fixed Figma frame, but a fixed page height caused footer clipping. For future pages:

- Fixed width is acceptable when the user asks to reproduce a desktop Figma frame.
- Page height should usually be content-driven:
  - use `height: auto`
  - use top/bottom padding for page margins
  - avoid clipping page-level wrappers with `overflow: hidden`
- If the user asks for a fixed canvas with margins, prefer:
  - outer page: fixed width, `height: auto`, `padding: <top> <side> <bottom>`
  - inner frame: `position: relative`, `height: auto`, `overflow: visible`
- Only use `overflow: hidden` on individual visual elements that are meant to clip, such as book covers, scroll strips, or framed decorations.
- Validate actual positions with browser measurements, not only screenshots.

Good measurement checks:

```js
const page = document.querySelector(".figma-homepage").getBoundingClientRect();
const frame = document.querySelector(".fm-frame").getBoundingClientRect();
const footer = document.querySelector(".fm-contact").getBoundingClientRect();
({
  pageHeight: page.height,
  frameTop: frame.top - page.top,
  footerBottomGap: page.bottom - footer.bottom,
});
```

## Assets And SVG

Prefer real exported assets over approximations:

- Use source SVGs from `reference/figma-make/...` or `reference/figma-handoff/source/` when available.
- For small repeating patterns, convert SVG snippets to CSS masks when they need to inherit hover/focus color.
- Use `currentColor` for icon/pattern fills that should change together with text.
- Keep theme red consistent: `#e22626`.
- Do not embed whole pages as a single image or giant SVG when the text should remain dynamic or interactive.

Example pattern rule:

```css
.button-marker {
  background: currentcolor;
  mask: url("data:image/svg+xml,...") center / 12px 12px no-repeat;
  -webkit-mask: url("data:image/svg+xml,...") center / 12px 12px no-repeat;
}

.button:hover,
.button:focus,
.button:focus-visible {
  color: #e22626;
}
```

## Fonts

Font fidelity matters for this project.

- Use local/static fonts from `public/fonts/`.
- Define explicit `@font-face` names in CSS.
- Do not rely on system fallback when the Figma design specifies a local Chinese font.
- Check browser rendering, not just build output.
- If PowerShell displays mojibake while browser output is correct, do not rewrite Chinese source strings wholesale. Treat it as console encoding unless the page itself is wrong.

## Dynamic Date And Weather

The homepage uses `src/lib/uapis.ts` and static generation. Keep these distinctions clear:

- `npm run dev` and `npm run preview` may show different cached or freshly built API data.
- Run `npm run build` to verify static generation actually calls the API.
- Inspect `dist/index.html` when deciding whether a date/weather issue is API data or CSS clipping.
- If API output is correct in `dist` but browser display is stale, rebuild and reload the preview server/page.

For date/weather bugs, first ask:

1. Is the text missing from `dist/index.html`?
2. Is the text present but visually clipped?
3. Is the preview serving stale CSS/HTML?

## Links And Interaction

Keep interaction areas intentional:

- If only the "索引" button should navigate, make only that button an anchor.
- Do not wrap large decorative panels in links unless the user asks.
- Hover/focus states should apply to the whole component, not just the selected text node.
- For links in dense footer text, use consistent hover/focus red `#e22626`.
- Always include keyboard focus behavior when adding hover.

## Browser QA Loop

For rendered UI changes, use the in-app browser if available.

Minimum checks:

1. Page identity: URL and title are correct.
2. Not blank: meaningful text and assets render.
3. No framework overlay.
4. Console has no relevant errors.
5. Visual screenshot around the edited area.
6. DOM measurement for clipping/spacing issues.
7. Interaction proof for links, hover/focus, or scroll strips when changed.

Important browser lessons:

- Horizontal scroll can move target coordinates off-screen; reset scroll before hit-testing.
- Browser automation may not always trigger `:hover` reliably. If so, verify:
  - loaded CSS contains the hover rule
  - focus uses the same visual rule
  - screenshots or manual browser state match user expectation
- Rebuild before validating preview if the server serves `dist`.

Useful commands:

```bash
npm run validate
npm run check
npm run build
```

Run page-specific browser checks after build; passing build alone is not enough for visual work.

## Common Pitfalls

- Do not keep old UI experiments active when the user says to discard previous UI.
- Do not mix multiple design languages in one page.
- Do not let fixed Figma height crop real dynamic content.
- Do not assume screenshots are source of truth when exported SVG/HTML exists.
- Do not derive `subtitle` from title parentheses. It must come from metadata/frontmatter.
- Do not hand-write derived book fields in markdown (`download_url`, `release_tag`, `pdf_filename`, `classification`, `volume`).
- Do not edit unrelated data pipeline files while working on page visuals.
- Do not use online fonts or external runtime assets.

## Handoff Notes For Future Pages

When starting a new page such as BookDetail:

1. Make a fresh inventory of Figma Make files and assets.
2. Map generated sections to existing Astro data:
   - book title, subtitle, author, series
   - cover URL and cover kind
   - call number
   - reading metrics
   - outline
   - download URL
3. Decide what is decorative asset and what is semantic/dynamic text.
4. Implement one route first.
5. Validate at the target Figma desktop size before attempting responsive behavior.
6. Keep a short mismatch list for deliberate deviations.

## Completion Criteria

Before reporting completion:

- The page builds with `npm run build`.
- The route renders at `/ebook-library/...`.
- No edited area is clipped.
- Required assets return correctly under the `/ebook-library/` base path.
- Links navigate only where intended.
- Hover/focus states use `#e22626` consistently.
- Any remaining Figma mismatch is named explicitly.
