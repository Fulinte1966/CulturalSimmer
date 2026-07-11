const roots = document.querySelectorAll<HTMLElement>("[data-site-updates]");

for (const root of roots) {
  if (root.dataset.siteUpdatesReady === "true") continue;
  root.dataset.siteUpdatesReady = "true";

  const list = root.querySelector<HTMLElement>("[data-site-updates-list]");
  if (!list) continue;

  let activeAnnouncementId: string | null = null;
  let listScrollTop = 0;
  let lastTrigger: HTMLElement | null = null;

  const closeDetail = () => {
    if (!activeAnnouncementId) return;
    const detail = root.querySelector<HTMLElement>(
      `[data-site-update-detail="${CSS.escape(activeAnnouncementId)}"]`
    );
    if (detail) detail.hidden = true;
    activeAnnouncementId = null;
    list.hidden = false;
    list.scrollTop = listScrollTop;
    lastTrigger?.focus({ preventScroll: true });
  };

  const openDetail = (trigger: HTMLElement, announcementId: string) => {
    const detail = root.querySelector<HTMLElement>(
      `[data-site-update-detail="${CSS.escape(announcementId)}"]`
    );
    if (!detail) return;
    listScrollTop = list.scrollTop;
    lastTrigger = trigger;
    activeAnnouncementId = announcementId;
    list.hidden = true;
    detail.hidden = false;
    const scrollArea = detail.querySelector<HTMLElement>("[data-site-updates-scroll]");
    if (scrollArea) {
      scrollArea.scrollTop = 0;
      scrollArea.focus({ preventScroll: true });
    }
  };

  root.addEventListener("click", (event) => {
    const target = event.target as HTMLElement;
    const open = target.closest<HTMLElement>("[data-site-update-open]");
    if (open) {
      const announcementId = open.dataset.siteUpdateOpen;
      if (announcementId) openDetail(open, announcementId);
      return;
    }
    if (target.closest("[data-site-update-back]")) closeDetail();
  });

  root.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && activeAnnouncementId) {
      event.preventDefault();
      closeDetail();
    }
  });

}
