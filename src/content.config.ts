import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const bookIdRegex = /^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/;

const books = defineCollection({
  loader: glob({ pattern: "**/[^_]*.md", base: "./src/content/books" }),
  schema: z.object({
    id: z.string().regex(bookIdRegex, "id must be a valid call number like A9-1 or F-1-1"),
    title: z.string().min(1),
    description: z.string().min(1),
    author: z.string().optional(),
    subtitle: z.string().optional(),
    language: z.string().optional(),
    series: z.string().optional(),
    publisher: z.string().optional(),
    source: z.string().optional(),
    rights: z.string().optional(),
    licenseUrl: z.url().optional(),
    zlibraryUrl: z.url().optional(),
    notifyUpdates: z.boolean().default(true),
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

const announcements = defineCollection({
  loader: glob({ pattern: "**/[^_]*.md", base: "./src/content/announcements" }),
  schema: z.object({
    title: z
      .string()
      .trim()
      .min(1, "announcement title must not be empty")
      .max(80, "announcement title must not exceed 80 characters")
      .refine((value) => !/[<>]/.test(value), "announcement title must not contain HTML"),
    label: z
      .string()
      .trim()
      .min(1, "announcement label must not be empty")
      .max(6, "announcement label should not exceed 6 characters")
      .refine((value) => !/[\[\]［］]/.test(value), "announcement label must not contain brackets")
      .refine((value) => !/[<>]/.test(value), "announcement label must not contain HTML")
      .refine((value) => !["新书", "更新"].includes(value), "announcement label is reserved"),
    publishedAt: z.coerce.date(),
    kind: z.enum(["site-announcement", "important-erratum"]).default("site-announcement"),
    bookId: z.string().trim().min(1).optional(),
    edition: z.number().int().positive().optional(),
    summary: z.array(z.string().trim().min(1)).max(8).default([]),
  }).superRefine((value, context) => {
    if (value.kind === "important-erratum" && (!value.bookId || !value.edition)) {
      context.addIssue({
        code: "custom",
        message: "important errata require bookId and edition",
      });
    }
  }),
});

export const collections = { books, announcements };
