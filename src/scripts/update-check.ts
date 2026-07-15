import {
  resolveUpdateCheck,
  type UpdateCheckStatus,
} from "../lib/updateCheck";
import { applyCjkSpacing } from "./cjk-spacing";

interface CheckBook {
  id: string;
  title: string;
  subtitle?: string;
  author?: string;
  series?: string;
  edition: number;
  coverUrl?: string;
  coverFallbackUrl?: string;
  spineUrl?: string;
  coverKind: "explicit" | "generated" | "placeholder";
  modelThickness: number;
  detailUrl: string;
  changelogUrl: string;
}

const statusLabels: Record<UpdateCheckStatus, string> = {
  current: "已是最新",
  outdated: "已有新版",
  "invalid-edition": "版本有误",
  "unknown-book": "书目未录",
  "invalid-request": "链接有误",
};

const dataElement = document.querySelector<HTMLScriptElement>("#check-book-data");
const books = dataElement
  ? (JSON.parse(dataElement.textContent || "[]") as CheckBook[])
  : [];
const params = new URLSearchParams(window.location.search);
const result = resolveUpdateCheck(
  books,
  params.get("bookId"),
  params.get("edition"),
);

const setText = (selector: string, value: string) => {
  const element = document.querySelector<HTMLElement>(selector);
  if (element) element.textContent = value;
};

const renderStatus = (status: UpdateCheckStatus) => {
  const label = statusLabels[status];
  document
    .querySelectorAll<HTMLElement>("[data-check-status-character]")
    .forEach((character, index) => {
      character.textContent = label[index] ?? "";
    });
  const statusLink = document.querySelector<HTMLAnchorElement>(
    "[data-check-status-link]",
  );
  if (statusLink) {
    statusLink.dataset.status = status;
    statusLink.hidden = false;
  }
  setText("[data-check-live-status]", label);
};

const renderBook = (book: CheckBook) => {
  setText("[data-check-series]", book.series ?? "");
  setText("[data-check-title]", book.title);
  setText("[data-check-subtitle]", book.subtitle ?? "");
  setText("[data-check-author]", book.author ?? "");

  const title = document.querySelector<HTMLElement>("[data-check-title]");
  title?.classList.toggle("bd-title--long", book.title.length > 12);

  const detailLinks = document.querySelectorAll<HTMLAnchorElement>(
    "[data-check-status-link]",
  );
  detailLinks.forEach((link) => {
    link.href = book.detailUrl;
  });
  const changelog = document.querySelector<HTMLAnchorElement>(
    "[data-check-changelog]",
  );
  if (changelog) {
    changelog.href = book.changelogUrl;
    changelog.hidden = false;
  }

  const cover = document.querySelector<HTMLElement>("[data-check-cover]");
  const image = document.querySelector<HTMLImageElement>("[data-check-cover-image]");
  const placeholder = document.querySelector<HTMLElement>(
    "[data-check-cover-placeholder]",
  );
  if (!cover || !image || !placeholder) return;

  cover.classList.remove(
    "book-cover--explicit",
    "book-cover--generated",
    "book-cover--placeholder",
  );
  cover.classList.add(`book-cover--${book.coverKind}`);
  cover.style.setProperty("--book-size", `${book.modelThickness}px`);
  if (book.spineUrl) {
    cover.style.setProperty("--spine-texture", `url("${book.spineUrl}")`);
  } else {
    cover.style.removeProperty("--spine-texture");
  }

  if (book.coverUrl) {
    if (book.coverFallbackUrl) {
      image.dataset.publicAssetFallback = book.coverFallbackUrl;
    } else {
      delete image.dataset.publicAssetFallback;
    }
    delete image.dataset.publicAssetFallbackApplied;
    image.src = book.coverUrl;
    image.alt = `${book.title}封面`;
    image.hidden = false;
    placeholder.hidden = true;
  } else {
    image.removeAttribute("src");
    image.alt = "";
    image.hidden = true;
    placeholder.hidden = false;
    setText("[data-check-placeholder-author]", book.author ?? "");
    setText("[data-check-placeholder-title]", book.title);
    setText("[data-check-placeholder-subtitle]", book.subtitle ?? "");
  }
  cover.hidden = false;
};

if (result.book) {
  renderBook(result.book);
} else {
  const coverStage = document.querySelector<HTMLElement>(".bd-cover-stage");
  if (coverStage) coverStage.hidden = true;
  setText("[data-check-title]", "检查更新");
  setText("[data-check-author]", "未找到对应书目");
}
renderStatus(result.status);

const bookInfo = document.querySelector<HTMLElement>(".check-book-info");
if (bookInfo) applyCjkSpacing(bookInfo);

const page = document.querySelector<HTMLElement>("[data-check-page]");
page?.setAttribute("aria-busy", "false");

const syncCoverStagePosition = () => {
  const frame = document.querySelector<HTMLElement>(".bd-frame");
  const coverStage = document.querySelector<HTMLElement>(".bd-cover-stage");
  const compactLayout = window.matchMedia(
    "(max-width: 899px), (min-width: 900px) and (max-width: 1199px) and (orientation: portrait)",
  );
  if (!frame || !coverStage || compactLayout.matches) {
    coverStage?.style.removeProperty("left");
    return;
  }
  const tabletLayout = window.matchMedia(
    "(min-width: 900px) and (max-width: 1199px) and (orientation: landscape)",
  );
  const frameOffset = tabletLayout.matches ? 12 : 72;
  coverStage.style.left = `${frame.getBoundingClientRect().left + frameOffset}px`;
};

let positionFrame = 0;
const schedulePositionSync = () => {
  if (positionFrame) return;
  positionFrame = requestAnimationFrame(() => {
    positionFrame = 0;
    syncCoverStagePosition();
  });
};

syncCoverStagePosition();
window.addEventListener("resize", schedulePositionSync, { passive: true });
window.addEventListener("scroll", schedulePositionSync, { passive: true });

requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    const model = document.querySelector<HTMLElement>(".book-cover--model");
    if (model && !model.hidden) {
      model.style.transform = getComputedStyle(model).transform;
    }
  });
});
