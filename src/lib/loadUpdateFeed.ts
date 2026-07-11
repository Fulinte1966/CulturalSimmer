import { getCollection } from "astro:content";
import generatedUpdates from "../data/generated-updates.json";
import { getAllBooks } from "./books";
import { siteConfig } from "./site";
import { buildPublicUpdateFeed, type PublicUpdateFeed } from "./updateFeed";
import type { GeneratedSiteUpdate } from "./siteUpdates";

export async function loadPublicUpdateFeed(generatedAt = new Date()): Promise<PublicUpdateFeed> {
  const [books, announcements] = await Promise.all([
    getAllBooks(),
    getCollection("announcements"),
  ]);
  const siteUrl = siteConfig.publicBaseUrl;
  return buildPublicUpdateFeed({
    generatedUpdates: generatedUpdates as GeneratedSiteUpdate[],
    announcements,
    books,
    generatedAt,
    siteUrl,
    updatesPageUrl: new URL("updates/", siteUrl).toString(),
  });
}
