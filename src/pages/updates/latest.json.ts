import type { APIRoute } from "astro";
import { loadPublicUpdateFeed } from "../../lib/loadUpdateFeed";
import { latestPublicUpdateFeed } from "../../lib/updateFeed";

export const prerender = true;

export const GET: APIRoute = async () => {
  const feed = latestPublicUpdateFeed(await loadPublicUpdateFeed());
  return new Response(`${JSON.stringify(feed, null, 2)}\n`, {
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
};
