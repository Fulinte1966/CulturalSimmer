/// <reference path="../.astro/types.d.ts" />

declare global {
  interface ImportMetaEnv {
    readonly PUBLIC_ASSET_BASE_URL?: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }

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
