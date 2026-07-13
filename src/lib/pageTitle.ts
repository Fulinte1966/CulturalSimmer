export const SITE_TITLE = "文火";

export function formatPageTitle(pageTitle: string): string {
  const title = pageTitle.trim();
  return !title || title === SITE_TITLE ? SITE_TITLE : `${title}・${SITE_TITLE}`;
}
