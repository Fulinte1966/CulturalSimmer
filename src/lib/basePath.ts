export function joinBasePath(base: string, pathname: string): string {
  const normalizedBase = base.endsWith("/") ? base : `${base}/`;
  return `${normalizedBase}${pathname.replace(/^\/+/, "")}`;
}
