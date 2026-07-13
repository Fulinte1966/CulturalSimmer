"""PDF ingestion orchestration for GitHub Actions.

Called by ``.github/workflows/ingest-pdf.yml``.  Subcommands:

    validate   — download + extract + validate → JSON metadata
    changelog  — compare the previous PDF edition and prepare Release assets
    generate   — produce Markdown / covers / spine / outline / reading
    publish    — create canonical GitHub Release
    cleanup    — remove temporary Release and tag
    commit-message  — print formatted commit message
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import yaml
from build_site_updates_archive import build_site_updates_archive
from changelog_model import normalize_changelog
from compare_content_snapshots import compare_content_snapshots
from edition_policy import (
    check_expected_edition,
    find_previous_edition_record,
    format_edition_check_lines,
)
from extract_content_snapshot import (
    NORMALIZATION_PROFILE,
    extract_content_snapshot,
    read_snapshot,
    write_snapshot,
)
from render_release_changelog import render_release_changelog
from site_updates_data import append_generated_update

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _dump_frontmatter(data: dict) -> str:
    return yaml.dump(
        data,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


def _run(cmd: list[str], **kwargs):
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def _gh(*args: str):
    return _run(["gh", *args], capture_output=True).stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download_release_asset(
    release_tag: str,
    asset_name: str,
    destination: Path,
    *,
    required: bool,
) -> Optional[Path]:
    """Download one exact Release asset, optionally returning None if absent."""

    destination.mkdir(parents=True, exist_ok=True)
    asset_path = destination / asset_name
    if asset_path.exists():
        asset_path.unlink()
    result = subprocess.run(
        [
            "gh",
            "release",
            "download",
            release_tag,
            "--pattern",
            asset_name,
            "--dir",
            str(destination),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0 and asset_path.exists():
        return asset_path
    if required:
        detail = result.stderr.strip() or result.stdout.strip() or "asset not found"
        raise SystemExit(
            f"Unable to download {asset_name} from Release {release_tag}: {detail}"
        )
    return None


def _load_classifications() -> dict[str, str]:
    path = ROOT / "src" / "data" / "classifications.yml"
    data = yaml.safe_load(path.read_text("utf-8"))
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("classifications.yml must use schemaVersion: 1")

    roots = data.get("classifications")
    if not isinstance(roots, list):
        raise ValueError("classifications.yml classifications must be a sequence")

    labels: dict[str, str] = {}
    source_codes: set = set()

    def format_code(source_code: str) -> str:
        if re.fullmatch(r"[A-Z]\d*", source_code) is None:
            raise ValueError(f"Invalid source classification code: {source_code}")
        prefix, digits = source_code[0], source_code[1:]
        groups = [digits[index : index + 3] for index in range(0, len(digits), 3)]
        return prefix + ".".join(groups)

    def visit(nodes: list, parent_code: Optional[str] = None) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Every classification entry must be a mapping")
            code = node.get("code")
            label = node.get("label")
            children = node.get("children", [])
            if not isinstance(code, str) or not isinstance(label, str) or not label.strip():
                raise ValueError("Every classification requires string code and label fields")
            if code in source_codes:
                raise ValueError(f"Duplicate classification code: {code}")
            if parent_code and not code.startswith(parent_code):
                raise ValueError(
                    f"Classification {code} must start with parent code {parent_code}"
                )
            if not isinstance(children, list):
                raise ValueError(f"Classification {code} children must be a sequence")
            source_codes.add(code)
            labels[format_code(code)] = label.strip()
            visit(children, code)

    visit(roots)
    return labels


def _load_frontmatter(path: Path) -> dict:
    text = path.read_text("utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Invalid frontmatter in {path}")
    _, frontmatter, _ = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid frontmatter in {path}")
    return data


def _load_markdown_parts(path: Path) -> tuple[dict, str]:
    text = path.read_text("utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Invalid frontmatter in {path}")
    _, frontmatter, body = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid frontmatter in {path}")
    return data, body.strip()


def _month_to_date(month: str) -> str:
    return f"{month}-01"


def _merge_edition_record(frontmatter: dict, meta: dict) -> list[dict]:
    existing: list[dict] = []

    raw_editions = frontmatter.get("editions")
    if isinstance(raw_editions, list):
        for item in raw_editions:
            if isinstance(item, dict) and isinstance(item.get("edition"), int):
                existing.append(dict(item))

    edition = int(meta["edition"])
    if any(item["edition"] == edition for item in existing):
        raise SystemExit(f"Book entry already contains edition {edition}")

    existing.append(
        {
            "edition": edition,
            "editionDate": meta["editionDate"],
            "releaseTag": meta["canonicalTag"],
            "manifest": f"src/data/manifests/{meta['canonicalTag']}.json",
        }
    )
    return sorted(existing, key=lambda item: item["edition"])


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


def cmd_validate(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--release-id", required=True)
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--allow-edition-skip", action="store_true")
    opts = ap.parse_args(args)

    if not opts.release_tag.startswith("ingest-"):
        raise SystemExit("Intake Release tag must start with ingest-")

    ws = Path(opts.workspace)
    pdfs = sorted(ws.glob("*.pdf"))
    if len(pdfs) != 1:
        raise SystemExit(f"Expected exactly 1 PDF, found {len(pdfs)}")

    pdf_path = pdfs[0]
    sha = _sha256(pdf_path)

    release = json.loads(
        _gh("api", f"repos/:owner/:repo/releases/{int(opts.release_id)}")
    )
    matching_assets = [
        asset for asset in release.get("assets", [])
        if asset.get("name") == pdf_path.name
    ]
    if len(matching_assets) != 1:
        raise SystemExit("Unable to identify the source PDF asset")
    published_at = release.get("published_at")
    if not published_at:
        raise SystemExit("Intake Release has no publication timestamp")

    # Extract metadata via shared extract_metadata module
    from extract_metadata import extract, MetadataError
    try:
        meta = extract(pdf_path, _load_classifications())
    except (ValueError, MetadataError) as exc:
        raise SystemExit(f"Metadata validation failed: {exc}")

    tag = f"{meta.id}_v{meta.edition}"
    filename = f"{tag}.pdf"

    allow_edition_skip = opts.allow_edition_skip or os.environ.get(
        "ALLOW_EDITION_SKIP", ""
    ).lower() in {"1", "true", "yes"}
    edition_check = check_expected_edition(
        ROOT,
        meta.id,
        meta.edition,
        allow_edition_skip=allow_edition_skip,
    )
    for line in format_edition_check_lines(edition_check):
        print(line)
    if not edition_check.ok:
        raise SystemExit(f"Edition validation failed: {edition_check.message}")

    # Dedup checks
    try:
        _gh("release", "view", tag)
        raise SystemExit(f"Canonical Release {tag} already exists")
    except subprocess.CalledProcessError:
        pass  # expected — Release does not exist yet

    remote_tag = _run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        capture_output=True,
    ).stdout.strip()
    if remote_tag:
        raise SystemExit(f"Canonical Git tag {tag} already exists")

    def _exists(path: Path) -> bool:
        return path.exists()

    md_path = ROOT / "src" / "content" / "books" / f"{meta.id}.md"
    if _exists(md_path):
        existing = _load_frontmatter(md_path)
        if existing.get("title") and existing.get("title") != meta.title:
            raise SystemExit(
                f"Book title mismatch: existing {existing.get('title')} != PDF {meta.title}"
            )

    duplicate_paths = (
        ROOT / "src" / "data" / "manifests" / f"{tag}.json",
        ROOT / "public" / "covers" / f"{tag}.png",
        ROOT / "public" / "covers" / f"{tag}_spine.png",
        ROOT / "src" / "data" / "outlines" / f"{tag}.json",
        ROOT / "src" / "data" / "reading" / f"{tag}.json",
        ROOT / "src" / "data" / "changelogs" / f"{tag}.changelog.json",
    )
    existing_paths = [
        str(path.relative_to(ROOT)) for path in duplicate_paths if path.exists()
    ]
    if existing_paths:
        raise SystemExit(
            f"Canonical generated assets already exist: {', '.join(existing_paths)}"
        )

    result = {
        "id": meta.id,
        "title": meta.title,
        "subtitle": meta.subtitle,
        "author": meta.author,
        "edition": meta.edition,
        "editionDate": meta.edition_date,
        "editionDateSource": meta.edition_date_source,
        "pdfCreateDate": meta.pdf_create_date,
        "description": meta.description,
        "tags": meta.tags,
        "language": meta.language,
        "date": _month_to_date(meta.edition_date),
        "sourcePublishedAt": published_at,
        "series": meta.series,
        "volume": meta.volume,
        "totalVolumes": meta.total_volumes,
        "publisher": meta.publisher,
        "source": meta.source,
        "rights": meta.rights,
        "licenseUrl": meta.license_url,
        "zlibraryUrl": meta.zlibrary_url,
        "canonicalTag": tag,
        "canonicalFilename": filename,
        "sourceReleaseId": int(opts.release_id),
        "sourceAssetId": int(matching_assets[0]["id"]),
        "sourceReleaseTag": opts.release_tag,
        "sourceSha256": sha,
        "sourcePdfPath": str(pdf_path),
    }
    Path(opts.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Validation OK: {tag}")


# ---------------------------------------------------------------------------
# changelog
# ---------------------------------------------------------------------------


def cmd_changelog(args: list[str]):
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--max-changes", type=int, default=200)
    ap.add_argument("--max-tokens", type=int, default=400_000)
    ap.add_argument("--timeout-seconds", type=int, default=30)
    opts = ap.parse_args(args)

    metadata_path = Path(opts.metadata)
    meta = json.loads(metadata_path.read_text("utf-8"))
    workspace = Path(opts.workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    tag = meta["canonicalTag"]

    current_snapshot = extract_content_snapshot(
        Path(meta["sourcePdfPath"]),
        book_id=meta["id"],
        edition=int(meta["edition"]),
        edition_date=meta["editionDate"],
    )
    snapshot_path = workspace / f"{tag}.content.json.gz"
    write_snapshot(snapshot_path, current_snapshot, force=True)

    previous = find_previous_edition_record(ROOT, meta["id"], int(meta["edition"]))
    previous_snapshot = None
    previous_tag = None
    if previous is not None:
        previous_tag = previous.get("releaseTag")
        previous_date = previous.get("editionDate")
        if not previous_tag or not previous_date:
            raise SystemExit("Previous edition record lacks releaseTag or editionDate")

        old_snapshot_name = f"{previous_tag}.content.json.gz"
        old_snapshot_path = _download_release_asset(
            previous_tag,
            old_snapshot_name,
            workspace,
            required=False,
        )
        if old_snapshot_path is not None:
            try:
                candidate = read_snapshot(old_snapshot_path)
                compatible = (
                    candidate.get("normalizationProfile") == NORMALIZATION_PROFILE
                    and candidate.get("bookId") == meta["id"]
                    and int(candidate.get("edition", -1)) == int(previous["edition"])
                    and candidate.get("editionDate") == previous_date
                )
            except (OSError, ValueError, TypeError):
                compatible = False
                candidate = None
            if compatible:
                previous_snapshot = candidate
            else:
                old_snapshot_path.unlink(missing_ok=True)
                print(
                    "Previous snapshot is incompatible; re-extracting the previous PDF"
                )

        if previous_snapshot is None:
            previous_pdf_name = f"{previous_tag}.pdf"
            previous_pdf = _download_release_asset(
                previous_tag,
                previous_pdf_name,
                workspace,
                required=True,
            )
            from extract_metadata import MetadataError, extract

            try:
                previous_meta = extract(previous_pdf, _load_classifications())
            except (ValueError, MetadataError) as exc:
                raise SystemExit(f"Previous PDF metadata validation failed: {exc}")
            if previous_meta.id != meta["id"]:
                raise SystemExit("Previous PDF belongs to a different book")
            if previous_meta.edition != int(previous["edition"]):
                raise SystemExit(
                    "Previous PDF edition does not match the repository edition record"
                )
            if previous_meta.edition_date != previous_date:
                raise SystemExit(
                    "Previous PDF date does not match the repository edition record"
                )
            previous_snapshot = extract_content_snapshot(
                previous_pdf,
                book_id=meta["id"],
                edition=int(previous["edition"]),
                edition_date=str(previous_date),
            )

    changelog = normalize_changelog(
        compare_content_snapshots(
            previous_snapshot,
            current_snapshot,
            max_tokens=opts.max_tokens,
            timeout_seconds=opts.timeout_seconds,
        )
    )
    changelog_path = workspace / f"{tag}.changelog.json"
    changelog_path.write_text(
        json.dumps(changelog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    notes_path = workspace / f"{tag}.release-notes.md"
    notes_path.write_text(
        render_release_changelog(changelog, max_changes=opts.max_changes),
        encoding="utf-8",
    )

    meta.update(
        {
            "previousEdition": previous["edition"] if previous else None,
            "previousReleaseTag": previous_tag,
            "contentSnapshotPath": str(snapshot_path),
            "changelogPath": str(changelog_path),
            "releaseNotesPath": str(notes_path),
            "changelogSummary": changelog["summary"],
        }
    )
    metadata_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Changelog prepared: {changelog['summary']['total']} content differences"
    )


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def cmd_generate(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--workspace", required=True)
    opts = ap.parse_args(args)

    meta = json.loads(Path(opts.metadata).read_text("utf-8"))
    id_ = meta["id"]
    edition = meta["edition"]
    pdf_path = Path(meta["sourcePdfPath"])
    tag = meta["canonicalTag"]

    # Cover / spine / outline / reading via book_assets.py
    from book_assets import extract_book_assets
    asset_paths = extract_book_assets(pdf_path, id_, edition, ROOT)
    print("Assets generated via book_assets")

    reading = json.loads(asset_paths["reading"].read_text(encoding="utf-8"))
    page_count = reading.get("pageCount")
    word_count = (reading.get("cjkCharacterCount") or 0) + (
        reading.get("latinTokenCount") or 0
    )

    changelog = normalize_changelog(
        json.loads(Path(meta["changelogPath"]).read_text(encoding="utf-8"))
    )
    changelog_dir = ROOT / "src" / "data" / "changelogs"
    changelog_dir.mkdir(parents=True, exist_ok=True)
    repository_changelog_path = changelog_dir / f"{tag}.changelog.json"
    repository_changelog_path.write_text(
        json.dumps(changelog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Markdown entry
    tags = meta.get("tags") or []

    md_path = ROOT / "src" / "content" / "books" / f"{id_}.md"
    existing_frontmatter: dict = {}
    if md_path.exists():
        existing_frontmatter, _ = _load_markdown_parts(md_path)

    frontmatter: dict = {
        "id": id_,
        "title": meta["title"],
        "description": meta["description"],
        "tags": tags,
    }
    for opt in (
        "subtitle",
        "author",
        "totalVolumes",
        "series",
        "publisher",
        "source",
        "rights",
        "licenseUrl",
        "zlibraryUrl",
        "language",
    ):
        if meta.get(opt) is not None:
            frontmatter[opt] = meta[opt]
    frontmatter["editions"] = _merge_edition_record(existing_frontmatter, meta)

    yaml_text = _dump_frontmatter(frontmatter)
    md_content = f"---\n{yaml_text}---\n\n{meta.get('description', '')}\n"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Written {md_path}")

    # Manifest
    manifest_dir = ROOT / "src" / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schemaVersion": 4,
        "bookId": id_,
        "title": meta["title"],
        "edition": edition,
        "editionDate": meta["editionDate"],
        "editionDateSource": meta["editionDateSource"],
        "pdfCreateDate": meta["pdfCreateDate"],
        "description": meta["description"],
        "creator": meta.get("author"),
        "language": meta.get("language") or "zh-CN",
        "releaseTag": meta["canonicalTag"],
        "pdfFilename": meta["canonicalFilename"],
        "downloadUrl": (
            "https://github.com/"
            f"{os.environ.get('GITHUB_REPOSITORY', 'Fulinte1966/CulturalSimmer')}"
            f"/releases/download/{meta['canonicalTag']}/{meta['canonicalFilename']}"
        ),
        "githubAssetDigest": None,
        "bytes": pdf_path.stat().st_size,
        "pageCount": page_count,
        "wordCount": word_count,
        "sourceReleaseId": meta["sourceReleaseId"],
        "sourceAssetId": meta["sourceAssetId"],
        "sourceSha256": meta["sourceSha256"],
        "canonicalTag": meta["canonicalTag"],
        "previousEdition": meta.get("previousEdition"),
        "contentSnapshotFilename": f"{tag}.content.json.gz",
        "changelogFilename": f"{tag}.changelog.json",
        "changelogPath": f"src/data/changelogs/{tag}.changelog.json",
        "changelogSummary": changelog["summary"],
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            key: meta.get(key)
            for key in (
                "title",
                "subtitle",
                "author",
                "language",
                "series",
                "publisher",
                "source",
                "rights",
                "licenseUrl",
                "zlibraryUrl",
            )
            if meta.get(key) is not None
        },
    }
    manifest_path = manifest_dir / f"{id_}_v{edition}.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Written {manifest_path}")

    # Summary stub
    summary_lines = [
        f"## Ingest {id_} edition {edition}",
        f"- SHA-256: `{meta['sourceSha256']}`",
        f"- Canonical tag: `{meta['canonicalTag']}`",
        f"- Entry: `{md_path.relative_to(ROOT)}`",
        f"- Content differences: `{(meta.get('changelogSummary') or {}).get('total', 0)}`",
    ]
    (ROOT / "_ingest_summary.md").write_text("\n".join(summary_lines))


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------

def cmd_publish(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--workspace", required=True)
    opts = ap.parse_args(args)

    meta = json.loads(Path(opts.metadata).read_text("utf-8"))
    pdf_path = Path(meta["sourcePdfPath"])
    normalized_pdf = Path(opts.workspace) / meta["canonicalFilename"]
    if pdf_path.resolve() != normalized_pdf.resolve():
        shutil.copyfile(pdf_path, normalized_pdf)

    snapshot_path = Path(meta["contentSnapshotPath"])
    changelog_path = Path(meta["changelogPath"])
    notes_path = Path(meta["releaseNotesPath"])
    for asset_path in (snapshot_path, changelog_path, notes_path):
        if not asset_path.exists():
            raise SystemExit(f"Required Release artifact is missing: {asset_path}")

    # Create canonical Release with all content-derived assets.
    _gh(
        "release", "create", meta["canonicalTag"],
        normalized_pdf.resolve().as_posix(),
        snapshot_path.resolve().as_posix(),
        changelog_path.resolve().as_posix(),
        "--title", meta["canonicalTag"],
        "--notes-file", notes_path.resolve().as_posix(),
    )
    digest = None
    release = {}
    release_json = _gh("api", f"repos/:owner/:repo/releases/tags/{meta['canonicalTag']}")
    if release_json:
        release = json.loads(release_json)
        for asset in release.get("assets", []):
            if asset.get("name") == meta["canonicalFilename"]:
                digest = asset.get("digest")
                break
    if not digest:
        raise SystemExit(
            f"GitHub did not return a digest for {meta['canonicalFilename']}"
        )

    published_at = release.get("published_at") or datetime.now(
        ZoneInfo("Asia/Shanghai")
    ).isoformat(timespec="seconds")
    is_first_edition = meta.get("previousEdition") is None
    generated_update = {
        "id": f"{meta['id']}-listed" if is_first_edition else meta["canonicalTag"].replace("_", "-"),
        "type": "book-added" if is_first_edition else "book-updated",
        "publishedAt": published_at,
        "bookId": meta["id"],
    }
    if not is_first_edition:
        generated_update["edition"] = meta["edition"]
    append_generated_update(
        ROOT / "src" / "data" / "generated-updates.json", generated_update
    )
    build_site_updates_archive(ROOT)

    manifest_path = ROOT / "src" / "data" / "manifests" / f"{meta['canonicalTag']}.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["githubAssetDigest"] = digest
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        release_manifest = Path(opts.workspace) / f"{meta['canonicalTag']}.manifest.json"
        shutil.copyfile(manifest_path, release_manifest)
        _gh(
            "release",
            "upload",
            meta["canonicalTag"],
            release_manifest.resolve().as_posix(),
        )
    print(f"Canonical Release {meta['canonicalTag']} created")


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

def cmd_cleanup(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata")
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--push-success", required=True)
    opts = ap.parse_args(args)

    push_succeeded = opts.push_success.lower() == "true"
    if push_succeeded:
        try:
            _gh("release", "delete", opts.release_tag, "--yes")
            _gh("api", f"repos/:owner/:repo/git/refs/tags/{opts.release_tag}",
                "-X", "DELETE")
            print(f"Temporary Release {opts.release_tag} deleted")
        except subprocess.CalledProcessError as exc:
            print(f"Warning: cleanup failed: {exc}")
    else:
        if opts.metadata and Path(opts.metadata).exists():
            meta = json.loads(Path(opts.metadata).read_text("utf-8"))
            try:
                _gh(
                    "release",
                    "delete",
                    meta["canonicalTag"],
                    "--yes",
                    "--cleanup-tag",
                )
                print(f"Rolled back canonical Release {meta['canonicalTag']}")
            except subprocess.CalledProcessError:
                pass
        print(f"Push did not succeed; keeping {opts.release_tag} for inspection")


# ---------------------------------------------------------------------------
# commit-message
# ---------------------------------------------------------------------------

def cmd_commit_message(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    opts = ap.parse_args(args)

    meta = json.loads(Path(opts.metadata).read_text("utf-8"))
    print(f"content: ingest {meta['id']} edition {meta['edition']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = {
    "validate": cmd_validate,
    "changelog": cmd_changelog,
    "generate": cmd_generate,
    "publish": cmd_publish,
    "cleanup": cmd_cleanup,
    "commit-message": cmd_commit_message,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(COMMANDS)}> [...]", file=sys.stderr)
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
