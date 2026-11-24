"""Small shared helpers: hashing, IO, layout-normalised text, secrets."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load(path: Path):
    return json.loads(Path(path).read_text())


def norm(text: str) -> str:
    """Layout-insensitive comparison only; stored quotations stay verbatim."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(?<=\w)[-\u00ad]\s*\n\s*(?=\w)", "", text)
    return "".join(text.split()).casefold()


def estimate_tokens(messages) -> int:
    """Conservative estimate for prompt sizing (English/code heavy)."""
    total = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            total += len(json.dumps(content, ensure_ascii=False))
        for call in message.get("tool_calls") or []:
            total += len(json.dumps(call, ensure_ascii=False))
        total += len(message.get("reasoning") or "") // 4
    return int(total / 3.0) + 64 * len(messages)


def secret_env() -> dict:
    values = {}
    path = Path.home() / ".config/soclaas/soclaas.env"
    for row in path.read_text().splitlines() if path.is_file() else ():
        key, sep, value = row.removeprefix("export ").partition("=")
        if sep:
            values[key.strip()] = value.strip().strip("\"'")
    for name in ("SOCLAAS_API_KEY", "SOCLAAS_BASE_URL"):
        if os.environ.get(name):
            values[name] = os.environ[name]
    if not values.get("SOCLAAS_API_KEY"):
        raise ValueError("Set SOCLAAS_API_KEY or configure ~/.config/soclaas/soclaas.env")
    return values


def git(repo: str, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], timeout=30)


def require(condition, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_jsonl(path: Path):
    if not Path(path).is_file():
        return []
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
