"""Create and verify immutable ebook candidate approval locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metadata(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Candidate metadata must be a JSON object")
    return value


def create_lock(metadata_path: Path, output: Path) -> dict[str, Any]:
    metadata = _metadata(metadata_path)
    pdf_path = Path(metadata["sourcePdfPath"])
    lock = {
        "schemaVersion": 1,
        "bookId": metadata["id"],
        "edition": int(metadata["edition"]),
        "canonicalTag": metadata["canonicalTag"],
        "draftTag": metadata["sourceReleaseTag"],
        "draftReleaseId": int(metadata["sourceReleaseId"]),
        "sourceCommit": metadata.get("sourceCommit"),
        "allowEditionSkip": bool(metadata.get("allowEditionSkip")),
        "pdfFilename": pdf_path.name,
        "pdfBytes": pdf_path.stat().st_size,
        "pdfSha256": _sha256(pdf_path),
    }
    output.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return lock


def verify_lock(metadata_path: Path, lock_path: Path, source_commit: str) -> None:
    metadata = _metadata(metadata_path)
    lock = _metadata(lock_path)
    pdf_path = Path(metadata["sourcePdfPath"])
    expected = {
        "bookId": metadata["id"],
        "edition": int(metadata["edition"]),
        "canonicalTag": metadata["canonicalTag"],
        "draftTag": metadata["sourceReleaseTag"],
        "draftReleaseId": int(metadata["sourceReleaseId"]),
        "sourceCommit": source_commit,
        "allowEditionSkip": bool(metadata.get("allowEditionSkip")),
        "pdfFilename": pdf_path.name,
        "pdfBytes": pdf_path.stat().st_size,
        "pdfSha256": _sha256(pdf_path),
    }
    mismatches = [key for key, value in expected.items() if lock.get(key) != value]
    if mismatches:
        raise ValueError(
            "Candidate approval is stale; mismatched fields: " + ", ".join(mismatches)
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--metadata", required=True)
    create_parser.add_argument("--output", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--metadata", required=True)
    verify_parser.add_argument("--lock", required=True)
    verify_parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            lock = create_lock(Path(args.metadata), Path(args.output))
            print(lock["pdfSha256"])
        else:
            verify_lock(
                Path(args.metadata), Path(args.lock), args.source_commit
            )
            print("Candidate approval lock verified")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Candidate lock failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
