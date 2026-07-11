import type { APIRoute } from "astro";
import { loadPublicUpdateFeed } from "../../lib/loadUpdateFeed";

export const prerender = true;

export const GET: APIRoute = async () => {
  const feed = await loadPublicUpdateFeed();
  return new Response(`${JSON.stringify(feed, null, 2)}\n`, {
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
};
