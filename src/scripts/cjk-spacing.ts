import Heti from "heti/js/heti-addon.js";

const typography = new Heti(".heti");

export const applyCjkSpacing = (root: ParentNode = document) => {
  const containers: Element[] = [];
  if (root instanceof Element && root.matches(".heti")) {
    containers.push(root);
  }
  containers.push(...root.querySelectorAll(".heti"));
  typography.spacingElements(containers);
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => applyCjkSpacing(), {
    once: true,
  });
} else {
  applyCjkSpacing();
}
