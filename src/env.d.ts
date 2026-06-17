/// <reference path="../.astro/types.d.ts" />

declare global {
  interface Window {
    PagefindUI?: new (opts: {
      element: string;
      showSubResults?: boolean;
    }) => void;
  }
}

export {};
