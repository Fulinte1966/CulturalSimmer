interface InitiallyListedBook {
  id: string;
  listedAt: Date;
}

export function orderBooksByInitialListing<T extends InitiallyListedBook>(
  books: readonly T[],
): T[] {
  return [...books].sort(
    (a, b) =>
      b.listedAt.getTime() - a.listedAt.getTime() ||
      a.id.localeCompare(b.id),
  );
}
