const freezeModelTransform = () => {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const model = document.querySelector(
        ".book-cover--model"
      ) as HTMLElement | null;
      if (model) {
        const t = getComputedStyle(model).transform;
        model.style.transform = t;
      }
    });
  });
};

freezeModelTransform();

const syncCoverStagePosition = () => {
  const frame = document.querySelector<HTMLElement>(".bd-frame");
  const coverStage = document.querySelector<HTMLElement>(".bd-cover-stage");
  if (!frame || !coverStage) return;

  const frameRect = frame.getBoundingClientRect();
  coverStage.style.left = `${frameRect.left + 72}px`;
};

let coverStageFrame = 0;
const scheduleCoverStageSync = () => {
  if (coverStageFrame) return;
  coverStageFrame = requestAnimationFrame(() => {
    coverStageFrame = 0;
    syncCoverStagePosition();
  });
};

syncCoverStagePosition();
window.addEventListener("resize", scheduleCoverStageSync, { passive: true });
window.addEventListener("scroll", scheduleCoverStageSync, { passive: true });

document.querySelectorAll<HTMLElement>("[data-errata-toggle]").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const region = document.querySelector<HTMLElement>("[data-errata-region]");
    const content = document.querySelector<HTMLElement>("[data-book-detail-content]");
    const panel = document.querySelector<HTMLElement>("[data-errata-panel]");

    if (!region || !content || !panel) return;

    const isOpen = !panel.hidden;
    panel.hidden = isOpen;
    content.hidden = !isOpen;
    region.classList.toggle("bd-text--errata", !isOpen);
    toggle.setAttribute("aria-expanded", String(!isOpen));
    const nextLabel = !isOpen
      ? toggle.dataset.errataLabelOpen ?? "返回"
      : toggle.dataset.errataLabelClosed ?? "勘误";
    toggle.setAttribute("aria-label", nextLabel);
    toggle
      .querySelectorAll<SVGTextElement>("[data-errata-toggle-text]")
      .forEach((text) => {
        text.textContent = nextLabel;
      });

    if (!isOpen) {
      scheduleCoverStageSync();
      panel.focus({ preventScroll: true });
    }
  });
});
