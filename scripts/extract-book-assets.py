"""CLI entry point for generating all static assets from a PDF."""

import argparse
from pathlib import Path

from book_assets import extract_book_assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("id")
    parser.add_argument("edition", type=int)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    outputs = extract_book_assets(
        args.pdf.resolve(),
        args.id,
        args.edition,
        args.root.resolve(),
    )
    for name, output in outputs.items():
        print(f"{name}: {output}")


if __name__ == "__main__":
    main()
