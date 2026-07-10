export interface UpdateCheckBook {
  id: string;
  edition: number;
}

export type UpdateCheckStatus =
  | "current"
  | "outdated"
  | "invalid-edition"
  | "unknown-book"
  | "invalid-request";

export interface UpdateCheckResult<T extends UpdateCheckBook> {
  status: UpdateCheckStatus;
  book?: T;
  requestedEdition?: number;
}

export function resolveUpdateCheck<T extends UpdateCheckBook>(
  books: readonly T[],
  bookIdValue: string | null,
  editionValue: string | null,
): UpdateCheckResult<T> {
  const bookId = bookIdValue?.trim();
  if (!bookId) return { status: "invalid-request" };

  const book = books.find((candidate) => candidate.id === bookId);
  if (!book) return { status: "unknown-book" };

  if (!editionValue || !/^[1-9]\d*$/.test(editionValue)) {
    return { status: "invalid-edition", book };
  }

  const requestedEdition = Number(editionValue);
  if (!Number.isSafeInteger(requestedEdition)) {
    return { status: "invalid-edition", book };
  }
  if (requestedEdition === book.edition) {
    return { status: "current", book, requestedEdition };
  }
  if (requestedEdition < book.edition) {
    return { status: "outdated", book, requestedEdition };
  }
  return { status: "invalid-edition", book, requestedEdition };
}
