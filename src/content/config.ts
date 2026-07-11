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
    zlibraryUrl: z.string().url().optional(),
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
  type: "content",
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
        code: z.ZodIssueCode.custom,
        message: "important errata require bookId and edition",
      });
    }
  }),
});

export const collections = { books, announcements };
