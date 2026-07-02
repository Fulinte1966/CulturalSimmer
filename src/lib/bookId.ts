export interface ParsedBookId {
  id: string;
  classification: string;
  accessionNumber: number;
  volumeNumber: number | null;
  workId: string;
  isVolume: boolean;
}

const bookIdRegex = /^([A-Z](?:\d+(?:\.\d+)?)?)-(\d+)(?:-(\d+))?$/;

export function parseBookId(id: string): ParsedBookId {
  const match = id.match(bookIdRegex);
  if (!match) {
    throw new Error(`Invalid book ID: ${id}`);
  }

  const classification = match[1];
  const accessionNumber = parseInt(match[2], 10);
  const volumeNumber = match[3] ? parseInt(match[3], 10) : null;
  const isVolume = volumeNumber !== null;
  const workId = isVolume ? `${classification}-${accessionNumber}` : id;

  return {
    id,
    classification,
    accessionNumber,
    volumeNumber,
    workId,
    isVolume,
  };
}

export function formatEdition(edition: number): string {
  return `第 ${edition} 版`;
}

export function formatEditionWithDate(date: Date, edition: number): string {
  return `${date.getFullYear()} 年 ${date.getMonth() + 1} 月第 ${edition} 版`;
}

export function formatVolume(
  volumeNumber: number,
  totalVolumes?: number
): string {
  if (totalVolumes !== undefined) {
    return `第 ${volumeNumber} 册 / 共 ${totalVolumes} 册`;
  }
  return `第 ${volumeNumber} 册`;
}

export function formatShortVolume(
  volumeNumber: number,
  totalVolumes?: number
): string {
  if (totalVolumes === 2) {
    const labels = ["上册", "下册"];
    return labels[volumeNumber - 1] ?? formatVolume(volumeNumber, totalVolumes);
  }

  if (totalVolumes === 3) {
    const labels = ["上册", "中册", "下册"];
    return labels[volumeNumber - 1] ?? formatVolume(volumeNumber, totalVolumes);
  }

  return formatVolume(volumeNumber, totalVolumes);
}

export function getReleaseTag(id: string, edition: number): string {
  return `${id}_v${edition}`;
}

export function getPdfFilename(id: string, edition: number): string {
  return `${id}_v${edition}.pdf`;
}

export function formatDisplayCallNumber(parsed: ParsedBookId): string {
  const { classification, accessionNumber, volumeNumber } = parsed;
  const base = `${classification}/${accessionNumber}`;
  return volumeNumber !== null ? `${base}:${volumeNumber}` : base;
}

export function getOutlinePath(id: string, edition: number): string {
  return `src/data/outlines/${id}_v${edition}.json`;
}
