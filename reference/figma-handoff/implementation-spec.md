# Implementation specification

## Architecture to preserve

The project remains an Astro static site. Generated Markdown book entries flow
through the Astro content collection into `src/lib/books.ts`, route pages, and
Astro components. PDFs remain hosted in GitHub Releases and Pagefind remains a
post-build static index.

The UI refactor must not introduce a client framework or CSS framework.

## Presentation data

Add a pure presentation helper for display call numbers:

```ts
formatDisplayCallNumber(parsed: ParsedBookId): string
```

Required output:

- `F0-1-1` -> `F0/1:1`
- `A8-3` -> `A8/3`
- `I210.4-1` -> `I210.4/1`

Internal IDs, routes, Release tags, PDF names, outline names, and reading-data
names remain unchanged.

Add `subtitle?: string` to the content schema and `BookMeta`. No title-splitting
helper is allowed. Existing entries without a subtitle remain valid.

## Shared layout

`Layout.astro` accepts:

```ts
type ActiveNav = "new" | "search" | "categories" | "overview";

interface Props {
  title: string;
  description?: string;
  searchable?: boolean;
  activeNav: ActiveNav;
}
```

Navigation mapping:

| Active value | Label | Route |
|---|---|---|
| `new` | 新书 | `/` |
| `search` | 搜索 | `/search/` |
| `categories` | 分类 | `/categories/` |
| `overview` | 总览 | `/books/` |

Use `aria-current="page"` for the active item. Remove the old descriptive
masthead and footer. Render `public/brand/wordmark.svg` unchanged and provide
the brand link with an accessible `文火` label.

## Routes

### `/`

- Active navigation: `new`.
- Fetch books with the existing date-descending order.
- Render only the first three books.
- Render no hero, statistics, search form, category index, or footer.

### `/books/`

- Active navigation: `overview`.
- Render all books in the same gallery and order as `/`.
- Do not embed search or category controls.

### `/categories/`

- Add an index route.
- Render top-level classifications from the complete YAML classification map,
  not from currently populated book categories.
- Keep the index typographic and unframed.

### `/categories/[classification]/`

- Generate paths for every classification in the YAML file.
- Parent is the longest existing proper code prefix.
- Preserve YAML source order for siblings.
- Examples: `A11 -> A1 -> A` and `K926.3 -> K926 -> K9 -> K`.
- Render child categories first.
- Render a BookCard gallery only for books whose parsed classification exactly
  equals the current code.
- Never include descendant-category books in a parent result.
- If a node has children and exact books, children precede the gallery.

### `/search/`

- Active navigation: `search`.
- GET query parameter is `q`.
- Empty query renders the centered underline input state.
- Production search dynamically imports `${BASE_URL}/pagefind/pagefind.js`.
- Use Pagefind's JavaScript API, not the default Pagefind UI widget.
- Resolve result data and render BookCard-equivalent DOM with `textContent` and
  element properties; do not inject metadata through raw HTML strings.
- Search results show cover or typographic placeholder, call number, title,
  subtitle, and author. They do not show body snippets.
- Handle loading, zero results, unavailable index, and unexpected errors.
- Development mode must not emit an unhandled 404 or console rejection.

### `/books/[id]/`

- Active navigation: `overview`.
- Preserve the current two-column detail workflow and CSS book model.
- Render title, optional subtitle, and optional author as distinct elements.
- Display the publication-form call number while preserving raw ID metadata.
- Preserve reading statistics, PDF download, summary, tags, and outline.
- Remove the production `BookModelDebug` panel.
- Keep the double-`requestAnimationFrame` repaint and narrow the query to
  `HTMLElement` so TypeScript accepts `.style`.
- At `<= 560px`, keep the existing flat-cover model fallback.

## Classification module

Create a dedicated pure module with:

```ts
interface ClassificationNode {
  code: string;
  label: string;
  parentCode?: string;
  depth: number;
  children: ClassificationNode[];
}

getClassificationNodes(): ClassificationNode[]
getTopLevelClassifications(): ClassificationNode[]
getClassificationNode(code: string): ClassificationNode | undefined
getClassificationAncestors(code: string): ClassificationNode[]
```

`books.ts` uses this module rather than maintaining a second YAML parser.

## Pagefind metadata

Every detail page supplies:

- `title`
- `book_subtitle`
- `author`
- `book_id`
- `call_number`
- `cover_kind`
- `image`
- `image_alt`

Missing optional values are omitted rather than serialized as `undefined` or
empty display rows.

## Responsive behavior

- Desktop `>= 960px`: three-column gallery.
- `560px-959px`: two columns.
- `361px-559px`: two columns with mobile gutters.
- `<= 360px`: one column.
- At `<= 560px`, brand and navigation may wrap to two rows and search occupies
  full available width.
- Never scale font size continuously with viewport width.
- Long Chinese titles, authors, and category names wrap naturally.
- No horizontal page scrolling at `1280`, `390`, `360`, or `320` pixels.

## Visual restrictions

- White paper, black ink, gray rules, and limited dark red only.
- No gradients, decorative shadows, Metro color blocks, pills, bokeh, or
  rounded page-section containers.
- No nested cards.
- Cards are content records, not decorated panels.
- Letter spacing is zero.
- Preserve stable cover dimensions while text changes.
