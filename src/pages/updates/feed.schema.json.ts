import type { APIRoute } from "astro";
import schema from "../../../schemas/update-feed.schema.json";

export const prerender = true;

export const GET: APIRoute = () =>
  new Response(`${JSON.stringify(schema, null, 2)}\n`, {
    headers: { "Content-Type": "application/schema+json; charset=utf-8" },
  });
