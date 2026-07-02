import { defineCollection, z } from "astro:content";

const bookIdRegex = /^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/;

const books = defineCollection({
  type: "content",
  schema: z.object({
    id: z.string().regex(bookIdRegex, "id must be a valid call number like A8-3 or A12-8-2"),
    title: z.string().min(1),
    edition: z.number().int().positive("edition must be a positive integer"),
    date: z.date(),
    author: z.string().optional(),
    subtitle: z.string().optional(),
    language: z.string().optional(),
    series: z.string().optional(),
    publisher: z.string().optional(),
    source: z.string().optional(),
    rights: z.string().optional(),
    license_url: z.string().url().optional(),
    tags: z.array(z.string()).default([]),
    cover: z.string().optional(),
    total_volumes: z
      .number()
      .int()
      .positive("total_volumes must be a positive integer")
      .optional(),
    readtime: z
      .number()
      .int()
      .positive("readtime must be a positive integer")
      .optional(),
  }),
});

export const collections = { books };
