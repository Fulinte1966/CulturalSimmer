"""Normalize one repository changelog and render its GitHub Release notes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from changelog_model import normalize_changelog
from render_release_changelog import render_release_changelog


ROOT = Path(__file__).resolve().parents[1]


def synchronize_changelog(
    release_tag: str,
    *,
    root: Path = ROOT,
    notes_output: Path | None = None,
    max_changes: int = 200,
) -> dict:
    changelog_path = (
        root / "src" / "data" / "changelogs" / f"{release_tag}.changelog.json"
    )
    manifest_path = root / "src" / "data" / "manifests" / f"{release_tag}.json"
    if not changelog_path.is_file():
        raise ValueError(f"Missing repository changelog: {changelog_path}")
    if not manifest_path.is_file():
        raise ValueError(f"Missing release manifest: {manifest_path}")

    changelog = normalize_changelog(
        json.loads(changelog_path.read_text(encoding="utf-8"))
    )
    expected_tag = (
        f"{changelog['bookId']}_v{changelog['toEdition']['edition']}"
    )
    if release_tag != expected_tag:
        raise ValueError(
            f"Release tag does not match changelog target edition: {expected_tag}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("releaseTag") != release_tag:
        raise ValueError("Release manifest tag does not match the requested release")
    manifest["changelogSummary"] = changelog["summary"]

    notes = render_release_changelog(changelog, max_changes=max_changes)
    changelog_path.write_text(
        json.dumps(changelog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if notes_output is not None:
        notes_output.parent.mkdir(parents=True, exist_ok=True)
        notes_output.write_text(notes, encoding="utf-8")
    return changelog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_tag")
    parser.add_argument("--notes-output", type=Path)
    parser.add_argument("--max-changes", type=int, default=200)
    args = parser.parse_args(argv)
    try:
        changelog = synchronize_changelog(
            args.release_tag,
            notes_output=args.notes_output,
            max_changes=args.max_changes,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Changelog synchronization failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Changelog synchronized: {args.release_tag} "
        f"({changelog['summary']['total']} differences)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
