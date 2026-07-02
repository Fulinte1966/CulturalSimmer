# Component specifications

## Layout

Responsibilities:

- load global CSS and document metadata;
- render the shared brand slot and four-item navigation;
- mark the active navigation item;
- provide one constrained main-content container;
- set Pagefind ignore behavior for non-searchable pages.

The component must not render a marketing description or site footer.

Accessibility:

- brand link label: `返回新书页`;
- navigation label: `主导航`;
- active link uses `aria-current="page"`;
- keyboard focus remains visible in dark red;
- the missing SVG state still has a readable text name.

## BookCover

Supported modes remain `flat` and `model`. Cover kind remains explicit,
generated, or placeholder.

### Flat mode

- Aspect ratio: `148 / 210`.
- Desktop target width: `280px`, constrained responsively by the grid.
- Real cover: one-pixel dark-red border and five-pixel outer radius.
- Placeholder: one-pixel gray border and the same dimensions.
- The image fills the fixed surface without introducing a black edge.
- Width, height, border, and hover state must not shift adjacent layout.

### Placeholder mode

Content order:

1. optional series;
2. main title;
3. optional subtitle;
4. optional author;
5. display call number.

Use Chill Jinshu Song CompactBold/WideBold according to the text hierarchy.
Do not derive subtitle text from the main title.

### Model mode

- Keep the existing DOM layers for front cover, spine, page block, back cover,
  and shadow.
- Keep current CSS geometry variables and seam adjustments unless a browser
  test demonstrates a regression caused by surrounding layout.
- Do not reintroduce rounded corners at the spine connection.
- Preserve rounded outer cover corners, white back cover, gray outline, and
  first-column spine texture.
- At mobile breakpoint, hide 3D pseudo-elements and show the flat cover.

## BookCard

Required semantic structure:

```text
li.catalog-item
  article
    linked BookCover(flat)
    publication call number
    linked main title
    optional subtitle
    optional author
```

Text roles:

| Element | Font | Size | Alignment |
|---|---|---:|---|
| Call number | TeX Gyre Termes Bold | 16px | left |
| Main title | Source Han Sans SC Medium | 16px | center |
| Subtitle | Zhuque Fangsong Regular | 16px | center |
| Author | LXGW Neo ZhiSong Screen Regular | 16px | center |

Author always follows subtitle. If subtitle is absent, author follows title.
Absent optional fields render no node and reserve no row height. Long content
wraps; it is never ellipsized or clipped.

Remove from BookCard:

- date;
- edition and volume display;
- reading metrics;
- download action;
- `书目详情` action;
- action separators and metadata rules.

Cover and title link to the detail route. Download remains on the detail page.

## Classification index

The index is a typographic list, not cards.

- Top-level page centers single-letter codes.
- Child rows show the ancestor prefix in muted gray and the new code suffix in
  ink black.
- Classification label uses LXGW Neo ZhiSong Screen at 24px.
- Current classification heading uses the 36px page-heading role.
- Link focus and hover remain visible without adding a filled rectangle.

## Search form

- Use a semantic GET form with a search input and submit button.
- Desktop target is a centered, approximately 804px-wide underline treatment.
- The visible command label is `搜索`, 36px in the empty state.
- Do not replace the form with a rounded search box or card.
- Query is restored from `URLSearchParams` after navigation.

## Search result renderer

Search results are created on the client but use the same class contract as
BookCard. Keep one `<template>` in the Astro page or use explicit DOM factory
functions. Set text through `textContent`; set links and images through DOM
properties after validating Pagefind metadata.

Placeholder results must include title, optional subtitle, optional author,
and display call number. Do not generate a visual placeholder from unrelated
images.

## Detail metadata

BookMeta retains:

- display call number;
- volume when present;
- edition;
- release date;
- page count, character count, and PDF file size;
- PDF download.

It may additionally show PDF-derived series, publisher, source, rights, and
license URL when populated. Missing values are omitted.

Title stack order is main title, subtitle, author. Subtitle and author are
separate elements for Pagefind metadata and typography.

## Outline

Retain existing behavior:

- hidden when the extracted bookmark array is empty;
- display-only, without linking into PDF pages;
- page numbers are omitted in the Figma Make detail layout;
- long titles wrap without colliding with neighboring content.
