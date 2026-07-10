export type ChangelogChangeType = "insert" | "delete" | "replace";

export interface ChangelogChange {
  type: ChangelogChangeType;
  needsReview?: boolean;
}

export interface ChangelogSummary {
  total: number;
  added: number;
  removed: number;
  changed: number;
}

/** Derive display statistics from entries; persisted summary fields are caches only. */
export function summarizeChangelog(
  changes: readonly ChangelogChange[],
): ChangelogSummary {
  const summary: ChangelogSummary = {
    total: changes.length,
    added: 0,
    removed: 0,
    changed: 0,
  };
  for (const change of changes) {
    if (change.type === "insert") summary.added += 1;
    else if (change.type === "delete") summary.removed += 1;
    else if (change.type === "replace") summary.changed += 1;
    else throw new Error(`Unsupported changelog change type: ${change.type}`);
  }
  return summary;
}
