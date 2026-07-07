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

Readable trigger examples for this project:

- "把 Figma Make 搭建的页面部署进项目"
- "参照 `reference/figma-make/...` 制作页面"
- "弃用已有 UI，按 Figma Make 重新做某个页面"
- "主页/详情页和设计稿不一致，调整页面"
- "更新 Figma Make 页面部署经验"

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

## Index Page Lessons

The index/category page has several coupled layout and interaction details. Preserve them deliberately instead of treating them as generic list styling.

- Keep the page height content-driven. Do not hard-code the Figma frame height; use consistent page padding, usually `25px`, and let book results or footer content extend the page.
- Keep the index panel's horizontal position stable when content expansion adds a vertical scrollbar. Prefer stable layout dimensions and `scrollbar-gutter: stable` or equivalent browser-verified compensation.
- The book/keyword switcher icon should use the real project SVG asset when the user supplies one, but the label should remain an independent text layer so it can be moved and recolored separately.
- Hover/focus on the switcher changes only the label text to theme red unless the design specifically says the whole icon should recolor.
- If the switcher has different labels such as `书目索引` and `关键词`, allow per-label offsets. Do not force both labels through one shared margin when the Figma positions differ.
- Use the 12px dotted source pattern for horizontal separators when it comes from the same button-marker component. Check that the horizontal rule repeats complete cells and does not crop a partial dot at either end.
- Category call-number rows should be a fixed two-column grid based on the Figma row model, not an auto-resizing text table. Keep the code column and label column gap explicit.
- For call-number hover, color only the opaque/highlighted digit span. Do not color the translucent prefix span.
- Disabled pagination buttons should use text color `rgba(0, 0, 0, 0.15)`, not reduced element opacity, so layout and descendants stay predictable.
- Use the exact pagination copy when requested, for example `首　页` and `尾　页` with the ideographic spacing preserved.
- Breadcrumb `主页` links should return to the site homepage route under `import.meta.env.BASE_URL`, not the browser's previous route.

## Book Cards And Shelf Dragging

Book cover components repeat across homepage, category results, shelves, and detail models. Keep their interaction treatment unified.

- If the design removes rounded corners, remove them everywhere the cover image appears, including category results, homepage shelves, and detail-page book models.
- The hover/focus outline belongs to the interactive cover frame, with a small visual gap around the book. Do not draw the outline directly on the image edge unless that is the established component style.
- Make hover and keyboard focus use the same outline geometry and color. For this project the cover outline is black unless the user asks for theme red.
- Avoid clipping hover/focus rings with parent frames. If a Figma frame must hide scrolling overflow, add padding or an inner focus frame so the ring still has room.
- For the homepage shelf, keep the `上架书目` label/blank area stationary and put the moving books in their own inner rail frame.
- The drag listener should cover the whole book rail, including the book cards, not only the empty space between cards.
- For drag feel, use pointer events with captured pointers, velocity tracking, inertia, and a small rubber-band overscroll. Keep left and right boundaries symmetrical.
- When using auto-return or snap-back, do not let it fight the rubber-band return. During rebound/inertia, the boundary should be computed from the rail viewport, not from the outer shelf blank area.
- If the first or last book appears clipped during rebound, debug the transform boundary and focus-frame width before adding more masks or overlays.
- Do not add fading or blocking overlays to hide overscroll unless the design asks for it; these layers can cover the last book and break hit testing.
- Align the shelf row vertically by the hover/focus frame, not by the raw cover image, so the visible interactive component centers in the shelf band.

## Book Detail Lessons

The book detail page has several fragile visual contracts. Treat these as part of the design, not incidental polish:

- Keep the Figma Make detail layout in Astro/CSS. Do not replace semantic sections with one large SVG.
- Preserve the current CSS book model geometry, but derive book thickness from real PDF page count when the data exists. Clamp thickness with a clear minimum and maximum so thin pamphlets and large books remain stable.
- Use generated cover, spine sample, and page texture as data-driven assets. Do not hard-code one book's visual dimensions into all books.
- Keep the top navigation logo asset shared with the homepage when requested, but force the detail nav logo to black when it sits in the newspaper rule bar.
- Use the fullwidth middle dot `・` in breadcrumbs and dense newspaper navigation text.
- Remove PDF page numbers from the visible outline list unless the user explicitly asks for page references.
- Center the outline frame inside the right column, but keep the outline text left-aligned and content-width driven.

### Book Detail Metadata

Book detail metadata is a compact centered frame, not loose inline text.

- Show volume first. For `total_volumes: 2`, map volume 1/2 to `上册`/`下册`. For `total_volumes: 3`, map 1/2/3 to `上册`/`中册`/`下册`. Fall back to `第 N 册` for other totals.
- Do not show reading time on the detail metadata block.
- Format metrics in this order: volume label, page count, character count, file size, edition dates, display call number.
- Use the Figma frame spacing:
  - outer metadata frame: column, centered, `gap: 6px`
  - metrics body: column, centered, `gap: 2px`, about `30px` tall
  - page/char/size row: inline flex, `gap: 10px`
- If there is one edition line, center it. If there are multiple edition lines, use a two-column auto grid/list and left-align the entries inside that frame.
- Keep call number text as `内部书号 F0/1:1` style using `formatDisplayCallNumber`.

### Book Detail Badges And Buttons

When Figma Make provides badge SVGs, use the source SVG as the shape and overlay dynamic text in HTML/SVG when text needs font fidelity.

- `proof-badge.svg` and `download-badge.svg` are decorative backing marks; the words `勘误` and `传阅` should remain text layers.
- For the `勘误` badge, use two stacked text layers:
  - back/under text: white fill plus white stroke for outline
  - front text: black fill
  - use SVG text when `text-shadow` makes ugly corners; set `stroke-linejoin: round` and `stroke-linecap: round`
  - tune `stroke-width` from browser screenshots; do not assume the Figma value survives font rasterization
- The download mark is a non-clickable circulation prompt. Remove extra PDF link text when the design only wants the badge and adjacent station buttons.
- Station buttons should reuse the dotted button component:
  - left marker + text + right marker
  - marker fill inherits `currentColor`
  - hover/focus changes the whole component to `#e22626`
  - text examples from this project: `基核技术站`, `择览资料站`
- Use `Glow Sans SC` extra-bold for badge words like `传阅` and `勘误`.

### Detail Font Checks

Some Chinese font faces are visually close but wrong. Verify in Chromium, not only CSS.

- If `青年自学丛书` appears too heavy on the detail page, inspect the loaded face with `document.fonts` and confirm the intended WideRegular/subset face is actually used.
- Avoid relying on `font-weight` alone when multiple local faces share a family name. Use explicit `@font-face` family names for `WideRegular`, compact title, and badge fonts.
- If a source font loads but Chromium still synthesizes or picks the wrong face, create a subset/static alias for the exact glyph set rather than fighting generic fallback.

## Assets And SVG

Prefer real exported assets over approximations:

- Use source SVGs from `reference/figma-make/...` or `reference/figma-handoff/source/` when available.
- Prefer local source assets provided by the user, for example project-level `SVG/*.svg`, when they supersede generated approximations.
- For small repeating patterns, convert SVG snippets to CSS masks when they need to inherit hover/focus color.
- Use `currentColor` for icon/pattern fills that should change together with text.
- Keep theme red consistent: `#e22626`.
- Do not embed whole pages as a single image or giant SVG when the text should remain dynamic or interactive.
- For repeating rule textures, confirm direction and repeat boundaries in the browser. Avoid clipped half-glyph repeats at the start or end of a rule; prefer content-box sizing or masks that repeat complete 12px cells.

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
- Keep CJK and Latin font responsibilities separate. If Latin or number glyphs need TeX Gyre Termes, use a dedicated Latin face with a narrow `unicode-range`; do not let that face claim CJK punctuation ranges such as `U+2000-206F`.
- When Chinese text uses a heavy/medium/regular design weight, map the Chinese face explicitly and let western letters and digits use the matching Latin bold/regular face.
- For weather/footer text, avoid halfwidth compression features when the design wants natural Chinese spacing. Split digits into small inline spans only when the digit font must be Latin while surrounding Chinese remains CJK.
- For punctuation width, set it by context: body copy can use fullwidth punctuation features, while titles and compact headings can use proportional/halfwidth punctuation features. Verify the actual rendered punctuation, not only the CSS rule.
- When an outline or content line appears to have an extra blank after a marker such as `一、`, inspect the generated JSON and Unicode code points before blaming CSS. The space may already be present in extracted data.

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
