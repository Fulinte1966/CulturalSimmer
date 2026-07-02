# Homepage QA Notes

- The page intentionally targets the fixed Figma viewport `1440 x 1024`.
- Date, lunar date, and weather remain dynamic through local data helpers/API.
- The slogan is local configuration from `src/lib/site.ts`; it is not fetched
  from an API.
- Homepage styling lives in `src/styles/home.css`; `src/styles/global.css`
  only contains reset, shared typography, layout basics, and BookCover styles.
- Known build warning: Vite does not statically resolve `public/fonts` URLs
  referenced from CSS, but production preview must verify those URLs return 200.
