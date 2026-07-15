export interface PublicAssetLocation {
  primaryUrl: string;
  fallbackUrl?: string;
}

export function normalizePublicAssetOrigin(value?: string): string | undefined {
  const candidate = value?.trim();
  if (!candidate) return undefined;

  const url = new URL(candidate);
  if (url.protocol !== "https:") {
    throw new Error("PUBLIC_ASSET_BASE_URL must use HTTPS");
  }
  if (
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    (url.pathname !== "/" && url.pathname !== "")
  ) {
    throw new Error("PUBLIC_ASSET_BASE_URL must be an HTTPS origin without a path");
  }

  return url.origin;
}

export function resolvePublicAsset(
  localUrl: string,
  assetBaseUrl?: string,
): PublicAssetLocation {
  const origin = normalizePublicAssetOrigin(assetBaseUrl);
  if (!origin || !localUrl.startsWith("/")) {
    return { primaryUrl: localUrl };
  }

  return {
    primaryUrl: `${origin}${localUrl}`,
    fallbackUrl: localUrl,
  };
}
