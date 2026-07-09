# Font subsetting

The site serves WOFF2 subsets from `public/fonts/subset/`. Full source fonts live
under `tools/font-sources/` so Astro does not copy them into the GitHub Pages
artifact.

Regenerate subsets after changing visible site copy, book metadata, category
labels, or UI text. The preferred flow is to build once so generated HTML in
`dist/` includes build-time API text, subset from that output, then build again
so the final artifact contains the latest WOFF2 files:

```sh
python3 -m pip install --user fonttools brotli
npm run build
npm run fonts:subset
npm run build
```

The generator reads text from `src/`, `public/assets/`, and `dist/` when it
exists. It also adds a conservative Chinese punctuation/UI safelist and writes
one WOFF2 subset per source font. Keep CSS `@font-face` rules pointed at
`public/fonts/subset/*.woff2` and use `font-display: swap` for web delivery.

The weather safelist follows the UAPI `/misc/weather` documentation's listed
common Chinese `weather` values. That field is documented as free-form text
rather than a fixed enum, so build-time `dist/` extraction handles the rendered
static value and unexpected client-side refresh text must still be allowed to
fall through to the CSS fallback stack. Calendar safelist characters cover the
`/misc/lunartime` fields currently rendered by the site: weekday, sexagenary
year, lunar month, and lunar day.
