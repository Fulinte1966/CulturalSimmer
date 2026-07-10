import { resolveUpdateCheck } from "../lib/updateCheck";

interface ErrataBook {
  id: string;
  edition: number;
  detailUrl: string;
}

interface ErrataRouteData {
  books: ErrataBook[];
  checkUrl: string;
}

const dataElement = document.querySelector<HTMLScriptElement>("#errata-route-data");
const routeData = dataElement
  ? (JSON.parse(dataElement.textContent || "{}") as ErrataRouteData)
  : { books: [], checkUrl: "/check/" };
const params = new URLSearchParams(window.location.search);
const bookId = params.get("bookId");
const edition = params.get("edition");
const result = resolveUpdateCheck(routeData.books, bookId, edition);

if (result.status === "current" && result.book) {
  const destination = new URL(result.book.detailUrl, window.location.origin);
  destination.searchParams.set("errata", "1");
  window.location.replace(destination.href);
} else {
  const destination = new URL(routeData.checkUrl, window.location.origin);
  if (bookId) destination.searchParams.set("bookId", bookId);
  if (edition) destination.searchParams.set("edition", edition);
  window.location.replace(destination.href);
}
