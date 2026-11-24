"""Deterministic JSON, checksums, and workspace boundary helpers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inside(root: Path, relative: str | Path) -> Path:
    base = Path(root).resolve()
    result = (base / relative).resolve()
    if not result.is_relative_to(base):
        raise ValueError(f"Path escapes workspace: {relative}")
    return result


def stable_id(prefix: str, *parts: Any) -> str:
    value = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return prefix + "-" + text_sha256(value)[:16]
