"""为测试目录生成并执行可审计的空书库初始化计划。

本脚本只处理 Git 仓库中的派生书目文件。远程 Release/tag 必须在空书库已经
成功部署后另行删除，避免页面先引用已经消失的 PDF。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION = "INITIALIZE TEST CATALOG"
GENERATED_DIRECTORIES = (
    "src/content/books",
    "src/data/manifests",
    "src/data/outlines",
    "src/data/reading",
    "src/data/changelogs",
    "public/covers",
)
GENERATED_FILES = ("src/data/generated-updates.json",)
PRESERVED_FILES = (
    "src/content/announcements/2026-07-16-site-updates-radio.md",
    "public/assets/announcements/site-updates-radio-qr.svg",
    "src/data/site-update-pins.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _entry(root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def create_plan(root: Path) -> dict[str, Any]:
    generated: list[dict[str, Any]] = []
    release_tags: set[str] = set()
    for directory in GENERATED_DIRECTORIES:
        for path in sorted((root / directory).glob("*")):
            if not path.is_file() or path.name == ".gitkeep":
                continue
            generated.append(_entry(root, path))
            if directory == "src/data/manifests" and path.suffix == ".json":
                release_tags.add(path.stem)
    for relative in GENERATED_FILES:
        path = root / relative
        if path.is_file():
            generated.append(_entry(root, path))

    preserved = []
    for relative in PRESERVED_FILES:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"必须保留的人工文件不存在：{relative}")
        preserved.append(_entry(root, path))

    return {
        "schemaVersion": 1,
        "generated": generated,
        "preserved": preserved,
        "releaseTags": sorted(release_tags),
    }


def _verify_entries(root: Path, entries: list[dict[str, Any]]) -> None:
    for item in entries:
        path = root / item["path"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise ValueError(f"初始化清单已经失效：{item['path']}")


def apply_plan(root: Path, plan: dict[str, Any], confirmation: str) -> None:
    if confirmation != CONFIRMATION:
        raise ValueError(f"确认短语必须为：{CONFIRMATION}")
    if plan.get("schemaVersion") != 1:
        raise ValueError("不支持的初始化清单版本")
    _verify_entries(root, plan.get("generated", []))
    _verify_entries(root, plan.get("preserved", []))

    preserved_paths = {item["path"] for item in plan["preserved"]}
    for item in plan["generated"]:
        relative = item["path"]
        if relative in preserved_paths:
            raise ValueError(f"清单错误地包含人工文件：{relative}")
        path = root / relative
        if relative == "src/data/generated-updates.json":
            path.write_text("[]\n", encoding="utf-8")
        else:
            path.unlink()

    _verify_entries(root, plan["preserved"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--output", type=Path, required=True)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--plan", type=Path, required=True)
    apply_parser.add_argument("--confirmation", required=True)

    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "plan":
        plan = create_plan(root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"初始化清单已生成：{args.output}")
        print(f"派生文件：{len(plan['generated'])}；Release：{len(plan['releaseTags'])}")
        return 0

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    apply_plan(root, plan, args.confirmation)
    print("测试目录已经初始化；请重新生成更新归档并运行 npm run verify。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
