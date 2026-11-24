"""Step 3b, documentation side: turn a paper PDF and a repo's docs into quotable passages.

Everything here is deterministic. A passage is the unit an LLM may quote from, and
`verify_quote` is the gate rule: a quote counts only if it occurs in the passage.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

from rank_bm25 import BM25Plus

MAX_PASSAGE_CHARS = 1200
MIN_QUOTE_CHARS = 12  # a shorter quote ("4k", "128") proves nothing about a limitation

_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-",
                       "—": "-", "−": "-", " ": " ", "‐": "-", "‑": "-"})
_HEADING = re.compile(r"^(?:\d+(?:\.\d+){0,3}\.?|[A-Z](?:\.\d+){0,3}\.?)\s+[A-Z]")
_NAMED = re.compile(r"^(abstract|introduction|related work|background|conclusions?|discussion|evaluation|"
                    r"references|acknowledge?ments?|appendix|supplementary)\b", re.I)


@dataclass
class Passage:
    passage_id: str
    source: str  # DocSource value
    locator: str
    text: str


def clean(text: str) -> str:
    """Ligatures and spacing only. Characters otherwise stay as extracted, so quotes stay verbatim."""
    text = "".join(unicodedata.normalize("NFKC", c) if c in "ﬀﬁﬂﬃﬄﬅﬆ" else c
                   for c in text)
    text = re.sub(r"(?<=[a-z])-\s*\n\s*(?=[a-z])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def verify_quote(quote: str, passage_text: str) -> Optional[str]:
    """Return the exact passage slice the quote matches, or None if it does not occur.

    Only typography and whitespace are folded, never words. Returning the slice means the
    stored evidence is always the source's own text, not the model's copy.
    """
    if not isinstance(quote, str):
        return None
    q = re.sub(r"\s+", " ", clean(quote)).strip().translate(_FOLD)
    if len(q) < MIN_QUOTE_CHARS or "..." in q or "…" in q:
        return None
    i = passage_text.translate(_FOLD).find(q)
    return passage_text[i:i + len(q)] if i >= 0 else None


def _ordered_blocks(page) -> list[dict]:
    """Text blocks in reading order, handling two-column pages with full-width bands."""
    width, height = page.rect.width, page.rect.height
    blocks = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        spans = [s for line in b["lines"] for s in line["spans"] if s["text"].strip()]
        if not spans:
            continue
        text = "\n".join("".join(s["text"] for s in line["spans"]) for line in b["lines"])
        x0, y0, x1, y1 = b["bbox"]
        blocks.append({"text": text, "x0": x0, "x1": x1, "y0": y0, "y1": y1,
                       "size": max(s["size"] for s in spans),
                       "bold": any("bold" in s["font"].lower() or s["flags"] & 16 for s in spans),
                       "margin": y1 < height * 0.06 or y0 > height * 0.94})
    left = [b for b in blocks if b["x1"] <= width * 0.55]
    right = [b for b in blocks if b["x0"] >= width * 0.45]
    if len(left) < 3 or len(right) < 3:  # single column
        return sorted(blocks, key=lambda b: (round(b["y0"]), b["x0"]))
    full = sorted((b for b in blocks if b not in left and b not in right), key=lambda b: b["y0"])
    ordered, top = [], -1.0
    for fb in full + [None]:
        bottom = fb["y0"] if fb else float("inf")
        band = [b for b in left + right if top <= b["y0"] < bottom]
        ordered += sorted((b for b in band if b in left), key=lambda b: b["y0"])
        ordered += sorted((b for b in band if b in right), key=lambda b: b["y0"])
        if fb:
            ordered.append(fb)
            top = fb["y0"]
    return ordered


def _split(text: str, limit: int = MAX_PASSAGE_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text):
        if cur and len(cur) + len(sent) + 1 > limit:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out


def _is_heading(text: str, block: dict, body_size: float) -> bool:
    if len(text) > 90 or text.endswith((".", ",", ":", ";")) or len(text.split()) > 14:
        return False
    if _NAMED.match(text) and (block["bold"] or block["size"] > body_size or len(text.split()) <= 3):
        return True
    number = re.match(r"\d+", text)
    if (number and int(number.group()) > 12) or re.search(r"[:\u2190=;{}]", text):
        return False  # a numbered line of pseudo-code, not a section
    return bool(_HEADING.match(text)) and (block["bold"] or block["size"] > body_size + 0.3)


def pdf_passages(pdf_path: str | Path) -> list[Passage]:
    """Sectioned passages of a paper. The reference list is dropped; later text is the appendix."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    pages = [(i + 1, _ordered_blocks(p)) for i, p in enumerate(doc)]
    all_blocks = [b for _, bs in pages for b in bs]
    sizes = Counter(round(b["size"], 1) for b in all_blocks for _ in range(len(b["text"])))
    body = sizes.most_common(1)[0][0]
    repeated = Counter(re.sub(r"\d+", "#", clean(b["text"])) for b in all_blocks)

    out: list[Passage] = []
    section, source, in_refs, buf = "front matter", "paper", False, ""
    buf_page = 1

    def flush() -> None:
        nonlocal buf
        if buf and not in_refs:
            for piece in _split(buf):
                out.append(Passage(f"P{len(out) + 1:04d}", source, f"{section}, p.{buf_page}", piece))
        buf = ""

    for page_no, blocks in pages:
        for b in blocks:
            text = clean(b["text"])
            if not text or b["margin"] or "is included in the Proceedings" in text:
                continue
            if repeated[re.sub(r"\d+", "#", text)] >= 3 and len(text) < 120:
                continue  # running header or footer
            if _is_heading(text, b, body):
                flush()
                section = text
                if re.match(r"(\d+\.?\s+)?references\b", text, re.I):
                    in_refs = True
                elif in_refs or re.match(r"[A-Z](\.\d+)*\.?\s", text) \
                        or re.match(r"appendix|supplementary", text, re.I):
                    in_refs, source = False, "appendix"
                continue
            if len(buf) >= 400 or (buf and len(text) >= 400):
                flush()
            if not buf:
                buf_page = page_no
            buf = f"{buf} {text}".strip()
    flush()
    return out


def _doc_files(repo: Path) -> Iterable[Path]:
    return sorted(p for p in repo.glob("*") if p.is_file() and p.name.lower().startswith("readme"))


def repo_passages(repo: str | Path, code_files: Iterable[str]) -> list[Passage]:
    """README sections, plus the docstrings and comments of the given source files."""
    repo = Path(repo)
    out: list[Passage] = []

    def add(source: str, locator: str, text: str) -> None:
        for piece in _split(clean(text)):
            if len(piece) >= MIN_QUOTE_CHARS:
                out.append(Passage(f"D{len(out) + 1:04d}", source, locator, piece))

    for f in _doc_files(repo):
        heading = f.name
        for chunk in re.split(r"\n\s*\n", f.read_text(encoding="utf-8", errors="replace")):
            first = chunk.strip().splitlines()[0] if chunk.strip() else ""
            if first.startswith("#"):
                heading = f"{f.name} / {first.lstrip('# ').strip()}"
            add("readme", heading, chunk)

    for rel in sorted(set(code_files)):
        path = repo / rel
        if not path.is_file():
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                ds = ast.get_docstring(node, clean=True)
                if ds:
                    name = getattr(node, "name", "<module>")
                    line = node.body[0].lineno
                    add("docstring", f"{rel}:{line} ({name})", ds)
        group: list[str] = []
        start = last = 0
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type != tokenize.COMMENT:
                continue
            if group and tok.start[0] != last + 1:
                add("code_comment", f"{rel}:{start}", " ".join(group))
                group = []
            if not group:
                start = tok.start[0]
            group.append(tok.string.lstrip("# "))
            last = tok.start[0]
        if group:
            add("code_comment", f"{rel}:{start}", " ".join(group))
    return out


def tokens(text: str) -> list[str]:
    """Lower-case words and numbers; snake_case and camelCase split, plus the joined form."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    words = re.findall(r"[A-Za-zͰ-Ͽ]+|\d+(?:\.\d+)?", text.replace("_", " "))
    return [w.lower() for w in words if len(w) > 1 or w.isdigit() or "Ͱ" <= w <= "Ͽ"]


class Retriever:
    def __init__(self, passages: list[Passage]):
        self.passages = passages
        self._bm25 = BM25Plus([tokens(p.text) or ["_"] for p in passages]) if passages else None

    def search(self, query: str, k: int) -> list[Passage]:
        if not self._bm25 or not tokens(query):
            return []
        scores = self._bm25.get_scores(tokens(query))
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
        return [self.passages[i] for i in order[:k]]


def to_jsonable(passages: list[Passage]) -> list[dict]:
    return [asdict(p) for p in passages]
