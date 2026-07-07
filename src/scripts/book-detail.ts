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

const loadTallyEmbeds = () => {
  const source = "https://tally.so/widgets/embed.js";
  const hydrateFrames = () => {
    document
      .querySelectorAll<HTMLIFrameElement>("iframe[data-tally-src]:not([src])")
      .forEach((iframe) => {
        iframe.src = iframe.dataset.tallySrc ?? "";
      });
  };

  const run = () => {
    const tallyWindow = window as Window & {
      Tally?: { loadEmbeds: () => void };
    };

    if (typeof tallyWindow.Tally !== "undefined") {
      tallyWindow.Tally.loadEmbeds();
      return;
    }
    hydrateFrames();
  };

  const tallyWindow = window as Window & {
    Tally?: { loadEmbeds: () => void };
  };

  if (typeof tallyWindow.Tally !== "undefined") {
    run();
    return;
  }

  const existingScript = document.querySelector<HTMLScriptElement>(`script[src="${source}"]`);

  if (!existingScript) {
    const script = document.createElement("script");
    script.src = source;
    script.onload = run;
    script.onerror = hydrateFrames;
    document.body.appendChild(script);
  } else {
    existingScript.addEventListener("load", run, { once: true });
    existingScript.addEventListener("error", hydrateFrames, { once: true });
  }
};

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
      loadTallyEmbeds();
      scheduleCoverStageSync();
      panel.focus({ preventScroll: true });
    }
  });
});
