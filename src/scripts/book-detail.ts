const syncCoverStagePosition = () => {
  const frame = document.querySelector<HTMLElement>(".bd-frame");
  const coverStage = document.querySelector<HTMLElement>(".bd-cover-stage");
  if (!frame || !coverStage) return;

  const compactLayout = window.matchMedia(
    "(max-width: 899px), (min-width: 900px) and (max-width: 1199px) and (orientation: portrait)",
  );
  if (compactLayout.matches) {
    coverStage.style.removeProperty("left");
    return;
  }

  const frameRect = frame.getBoundingClientRect();
  const tabletLayout = window.matchMedia(
    "(min-width: 900px) and (max-width: 1199px) and (orientation: landscape)",
  );
  const frameOffset = tabletLayout.matches ? 12 : 72;
  coverStage.style.left = `${frameRect.left + frameOffset}px`;
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

const tallyScriptSource = "https://tally.so/widgets/embed.js";

const hydrateTallyFrame = () => {
  const iframe = document.querySelector<HTMLIFrameElement>("iframe[data-tally-src]");
  if (iframe && !iframe.getAttribute("src")) {
    iframe.src = iframe.dataset.tallySrc ?? "";
  }
};

const loadTallyEmbed = () => {
  const tallyWindow = window as Window & {
    Tally?: { loadEmbeds: () => void };
  };
  const run = () => {
    if (tallyWindow.Tally) {
      tallyWindow.Tally.loadEmbeds();
    } else {
      hydrateTallyFrame();
    }
  };

  if (tallyWindow.Tally) {
    run();
    return;
  }

  const existing = document.querySelector<HTMLScriptElement>(
    `script[src="${tallyScriptSource}"]`,
  );
  if (existing) {
    existing.addEventListener("load", run, { once: true });
    existing.addEventListener("error", hydrateTallyFrame, { once: true });
    return;
  }

  const script = document.createElement("script");
  script.src = tallyScriptSource;
  script.onload = run;
  script.onerror = hydrateTallyFrame;
  document.body.appendChild(script);
};

const reloadTallyEmbed = () => {
  const iframe = document.querySelector<HTMLIFrameElement>("iframe[data-tally-src]");
  if (!iframe) return;

  const replacement = document.createElement("iframe");
  replacement.dataset.tallySrc = iframe.dataset.tallySrc ?? "";
  replacement.loading = "lazy";
  replacement.width = "100%";
  replacement.height = "100";
  replacement.title = iframe.title;
  iframe.replaceWith(replacement);
  loadTallyEmbed();
};

const region = document.querySelector<HTMLElement>("[data-errata-region]");
const content = document.querySelector<HTMLElement>("[data-book-detail-content]");
const panel = document.querySelector<HTMLElement>("[data-errata-panel]");
const errataPrompt = document.querySelector<HTMLElement>("[data-errata-prompt]");
const form = document.querySelector<HTMLElement>("[data-errata-form]");
const toggle = document.querySelector<HTMLElement>("[data-errata-toggle]");
let errataMode: "prompt" | "form" = "prompt";
let detailScrollPosition = window.scrollY;

const setToggleState = (open: boolean) => {
  if (!toggle) return;
  toggle.setAttribute("aria-expanded", String(open));
  const label = open
    ? toggle.dataset.errataLabelOpen ?? "返回"
    : toggle.dataset.errataLabelClosed ?? "勘误";
  toggle.setAttribute("aria-label", label);
  toggle
    .querySelectorAll<SVGTextElement>("[data-errata-toggle-text]")
    .forEach((text) => {
      text.textContent = label;
    });
};

const setErrataMode = (mode: "prompt" | "form") => {
  errataMode = mode;
  if (errataPrompt) errataPrompt.hidden = mode !== "prompt";
  if (form) form.hidden = mode !== "form";
  panel?.classList.toggle("bd-errata-panel--form", mode === "form");
};

const setErrataOpen = (open: boolean) => {
  if (!region || !content || !panel) return;
  if (open) detailScrollPosition = window.scrollY;
  panel.hidden = !open;
  content.hidden = open;
  region.classList.toggle("bd-text--errata", open);
  setToggleState(open);
  scheduleCoverStageSync();
  if (open) {
    if (errataMode === "form") loadTallyEmbed();
    panel.focus({ preventScroll: true });
  } else {
    requestAnimationFrame(() => window.scrollTo(0, detailScrollPosition));
    if (errataMode === "form") reloadTallyEmbed();
  }
};

document.querySelectorAll<HTMLElement>("[data-errata-toggle]").forEach((toggle) => {
  toggle.addEventListener("click", () => {
    setErrataOpen(panel?.hidden ?? false);
  });
});

const detailUrl = new URL(window.location.href);
if (detailUrl.searchParams.get("errata") === "1") {
  detailUrl.searchParams.delete("errata");
  window.history.replaceState(
    window.history.state,
    "",
    `${detailUrl.pathname}${detailUrl.search}${detailUrl.hash}`,
  );
  setErrataMode("form");
  setErrataOpen(true);
}
