"""Create manual announcements and manage the ordered homepage pin list."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from site_updates_data import atomic_write_json, load_generated_updates

ROOT = Path(__file__).resolve().parents[1]
ANNOUNCEMENTS = ROOT / "src/content/announcements"
GENERATED = ROOT / "src/data/generated-updates.json"
PINS = ROOT / "src/data/site-update-pins.json"
RESERVED_LABELS = {"新书", "更新"}


def validate_label(value: str) -> str:
    label = value.strip()
    if not label:
        raise ValueError("标签不得为空")
    if re.search(r"[\[\]［］]", label):
        raise ValueError("标签不得包含方括号")
    if re.search(r"[<>]", label):
        raise ValueError("标签不得包含 HTML")
    if label in RESERVED_LABELS:
        raise ValueError(f"“{label}”是自动消息保留标签")
    if len(label) > 6:
        raise ValueError("标签不得超过 6 个字符")
    return label


def load_pins() -> list[str]:
    if not PINS.exists():
        return []
    value = yaml.safe_load(PINS.read_text("utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("site-update-pins.json 必须是字符串数组")
    if len(value) != len(set(value)):
        raise ValueError("site-update-pins.json 存在重复 ID")
    return value


def load_announcements() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for path in sorted(ANNOUNCEMENTS.glob("*.md")):
        text = path.read_text("utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"公告缺少 frontmatter: {path}")
        data = yaml.safe_load(parts[1]) or {}
        result[f"manual:{path.stem}"] = (
            validate_label(str(data.get("label", ""))),
            str(data.get("title", "")).strip(),
        )
    return result


def all_messages() -> dict[str, tuple[str, str]]:
    result = load_announcements()
    for item in load_generated_updates(GENERATED):
        label = "新书" if item["type"] == "book-added" else "更新"
        result[f"automatic:{item['id']}"] = (label, item["bookId"])
    return result


def prompt_value(current: str | None, prompt: str) -> str:
    return current if current is not None else input(prompt).strip()


def command_new(args: argparse.Namespace) -> None:
    title = prompt_value(args.title, "标题：").strip()
    label = validate_label(prompt_value(args.label, "标签："))
    slug = prompt_value(args.slug, "英文 slug（kebab-case）：").strip()
    if not title or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("标题不得为空，slug 必须使用小写 kebab-case")

    if args.with_body is None:
        wants_body = input("是否包含全文？[y/N]：").strip().lower() in {"y", "yes"}
    else:
        wants_body = args.with_body
    body = args.body
    if wants_body and body is None:
        body = input("正文（可稍后直接编辑文件）：").strip()
    if wants_body and not body:
        raise ValueError("选择全文公告后，正文不得为空")

    published_at = args.published_at or datetime.now(
        ZoneInfo("Asia/Shanghai")
    ).isoformat(timespec="seconds")
    date_prefix = published_at[:10]
    target = ANNOUNCEMENTS / f"{date_prefix}-{slug}.md"
    if target.exists():
        raise FileExistsError(f"公告已存在: {target}")
    frontmatter = yaml.safe_dump(
        {"title": title, "label": label, "publishedAt": published_at},
        allow_unicode=True,
        sort_keys=False,
    ).strip()
    content = f"---\n{frontmatter}\n---\n"
    if body:
        content += f"\n{body.rstrip()}\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".md.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(target)
    print(f"已创建 {target.relative_to(ROOT)}")

    should_pin = args.pin
    if should_pin is None:
        should_pin = input("是否立即置顶？[y/N]：").strip().lower() in {"y", "yes"}
    if should_pin:
        pin_id(f"manual:{target.stem}", None)


def choose_message(candidates: list[str]) -> str:
    messages = all_messages()
    for index, item_id in enumerate(candidates, start=1):
        label, title = messages[item_id]
        print(f"{index}. [{label}] {title} ({item_id})")
    selection = int(input("序号："))
    if selection < 1 or selection > len(candidates):
        raise ValueError("选择序号超出范围")
    return candidates[selection - 1]


def pin_id(item_id: str | None, position: int | None) -> None:
    messages = all_messages()
    pins = load_pins()
    if item_id is None:
        candidates = [candidate for candidate in messages if candidate not in pins]
        if not candidates:
            print("没有可置顶的消息")
            return
        item_id = choose_message(candidates)
    if item_id not in messages:
        raise ValueError(f"消息不存在: {item_id}")
    if item_id in pins:
        raise ValueError(f"消息已经置顶: {item_id}")
    insert_at = len(pins) if position is None else position - 1
    if insert_at < 0 or insert_at > len(pins):
        raise ValueError("置顶位置超出范围")
    pins.insert(insert_at, item_id)
    atomic_write_json(PINS, pins)
    print(f"已置顶 {item_id}")


def command_unpin(item_id: str | None) -> None:
    pins = load_pins()
    if item_id is None:
        if not pins:
            print("当前没有置顶消息")
            return
        item_id = choose_message(pins)
    if item_id not in pins:
        raise ValueError(f"消息未置顶: {item_id}")
    pins.remove(item_id)
    atomic_write_json(PINS, pins)
    print(f"已取消置顶 {item_id}")


def command_list() -> None:
    messages = all_messages()
    pins = load_pins()
    if not pins:
        print("当前没有置顶消息")
    for index, item_id in enumerate(pins, start=1):
        if item_id not in messages:
            raise ValueError(f"置顶消息不存在: {item_id}")
        label, title = messages[item_id]
        print(f"{index}. [{label}] {title} ({item_id})")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("announcement-new")
    create.add_argument("--title")
    create.add_argument("--label")
    create.add_argument("--slug")
    create.add_argument("--published-at")
    create.add_argument("--body")
    create.add_argument("--with-body", action=argparse.BooleanOptionalAction)
    create.add_argument("--pin", action=argparse.BooleanOptionalAction)
    pin = commands.add_parser("pin")
    pin.add_argument("id", nargs="?")
    pin.add_argument("--position", type=int)
    unpin = commands.add_parser("unpin")
    unpin.add_argument("id", nargs="?")
    commands.add_parser("pins")
    args = parser.parse_args()
    if args.command == "announcement-new":
        command_new(args)
    elif args.command == "pin":
        pin_id(args.id, args.position)
    elif args.command == "unpin":
        command_unpin(args.id)
    else:
        command_list()


if __name__ == "__main__":
    main()
