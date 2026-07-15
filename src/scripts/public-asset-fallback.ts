const fallbackAttribute = "data-public-asset-fallback";
const appliedAttribute = "data-public-asset-fallback-applied";

const applyFallback = (image: HTMLImageElement) => {
  const fallbackUrl = image.getAttribute(fallbackAttribute);
  if (!fallbackUrl || image.hasAttribute(appliedAttribute)) return;

  image.setAttribute(appliedAttribute, "");
  image.removeAttribute(fallbackAttribute);
  image.src = fallbackUrl;
};

document.addEventListener(
  "error",
  (event) => {
    const image = event.target;
    if (!(image instanceof HTMLImageElement)) return;
    applyFallback(image);
  },
  true,
);

document
  .querySelectorAll<HTMLImageElement>(`img[${fallbackAttribute}]`)
  .forEach((image) => {
    if (image.complete && image.naturalWidth === 0) applyFallback(image);
  });
