/// <reference path="../.astro/types.d.ts" />

declare global {
  interface PagefindUIInstance {
    triggerSearch(term: string): void;
  }

  interface Window {
    PagefindUI?: new (opts: {
      element: string;
      showSubResults?: boolean;
      showImages?: boolean;
    }) => PagefindUIInstance;
  }
}

export {};
