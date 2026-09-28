import type { APIRoute } from "astro";
import { loadPublicUpdateFeed } from "../../lib/loadUpdateFeed";
import { buildUpdateRss } from "../../lib/updateRss";

export const prerender = true;

export const GET: APIRoute = async () => new Response(
  buildUpdateRss(await loadPublicUpdateFeed()),
  { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } },
);
