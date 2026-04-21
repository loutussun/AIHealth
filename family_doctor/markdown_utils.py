from __future__ import annotations

import os
import re
from pathlib import Path


def safe_slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    if normalized and set(normalized) == {"."}:
        return "item"
    return normalized or "item"


def ensure_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def relative_link(from_path: Path, to_path: Path) -> str:
    return Path(
        os.path.relpath(to_path.resolve(), start=from_path.resolve().parent)
    ).as_posix()


def append_lines_under_heading(path: Path, heading: str, lines_to_add: list[str]) -> bool:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    try:
        heading_index = lines.index(heading)
    except ValueError:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend([heading, *lines_to_add])
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    section_end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            section_end = index
            break

    existing = set(lines[heading_index + 1 : section_end])
    pending = [line for line in lines_to_add if line not in existing]
    if not pending:
        return False

    updated_lines = [*lines[:section_end], *pending, *lines[section_end:]]
    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return True
