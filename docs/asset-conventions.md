# Asset conventions

## Directory policy

- `src/assets/`: assets imported by Astro/Vite modules, such as SVG icons that should be fingerprinted or bundled.
- `public/assets/brand/`: stable brand marks used by URL at runtime.
- `public/assets/badges/`: decorative badge/label SVGs.
- `public/assets/decor/`: reusable ornamental dividers, borders, and rules.
- `public/assets/textures/`: repeatable textures used by CSS or component styles.
- `public/covers/`: generated book covers and spine samples. Do not hand-edit these files.
- `public/fonts/`: vendored font files. Preserve upstream font names unless there is a strong reason to rename.

## Naming policy

- Use lowercase kebab-case for project-authored assets.
- Use role-first names for generic UI assets: `badge-download.svg`, `border-vertical-repeat.svg`.
- Prefix project-specific brand marks: `culturalsimmer-wordmark.svg`.
- Avoid opaque export names, hashes, frame numbers, and historical labels such as `Group13`, `page1`, `home-source`, or `Homepage Implementation`.
- Keep source/design exports out of the runtime tree. If a design contract is still useful, preserve it as a concise Markdown document under `docs/`, not as a full Figma Make project dump.

## Runtime path policy

Astro pages and components should build public URLs with `joinBasePath(import.meta.env.BASE_URL, ...)` where possible. CSS-only background URLs must include the GitHub Pages base path until they are moved behind CSS variables or imported modules.
