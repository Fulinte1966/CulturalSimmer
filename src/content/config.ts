import { defineCollection, z } from "astro:content";

const bookIdRegex = /^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/;

const books = defineCollection({
  type: "content",
  schema: z.object({
    id: z.string().regex(bookIdRegex, "id must be a valid call number like A8-3 or A12-8-2"),
    title: z.string().min(1),
    description: z.string().min(1),
    author: z.string().optional(),
    subtitle: z.string().optional(),
    language: z.string().optional(),
    series: z.string().optional(),
    publisher: z.string().optional(),
    source: z.string().optional(),
    rights: z.string().optional(),
    licenseUrl: z.string().url().optional(),
    tags: z.array(z.string()).default([]),
    cover: z.string().optional(),
    totalVolumes: z
      .number()
      .int()
      .positive("totalVolumes must be a positive integer")
      .optional(),
    editions: z
      .array(
        z.object({
          edition: z.number().int().positive(),
          editionDate: z.string().regex(/^\d{4}-\d{2}$/),
          releaseTag: z.string().optional(),
          manifest: z.string().optional(),
        })
      )
      .min(1),
  }),
});

export const collections = { books };
