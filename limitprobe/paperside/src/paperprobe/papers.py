"""PDF extraction and auditable, conservative paper evidence retrieval.

Retrieved sentences are evidence candidates, not automatically verified claims.
The module never turns an evaluation range into a supported-input contract.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .io import file_sha256, stable_id, text_sha256, write_json

_STOP = set("the a an and or for to of in on is are as by with this that we our from it at be can which using also into its each these their has have will not than more may must should".split())
_SCOPE = re.compile(r"\b(support\w*|assum\w*|require\w*|only|constraint\w*|compatible|limitation\w*|valid|restrict\w*|cannot)\b", re.I)
_MECHANISM = re.compile(r"\b(adapt\w*|spars\w*|query|queries|cache|kernel\w*|index|indices|split\w*|threshold\w*|block\w*|configuration\w*|attention|propagat\w*|prefetch\w*|head\w*|insert\w*|window\w*|fallback)\b", re.I)
_EVALUATION = re.compile(r"\b(evaluat\w*|benchmark\w*|experiment\w*|speedup|accuracy|throughput|latency|performance)\b", re.I)


def terms(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text.lower())
    return {w for w in words if w not in _STOP}


def _sentences(text: str) -> list[str]:
    # Keep original whitespace so quotes can be checked against the extracted page.
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z(])|\n\s*\n", text)
    result = []
    for piece in pieces:
        piece = piece.strip()
        if len(piece) < 45:
            continue
        if len(piece) > 1200:
            for start in range(0, len(piece), 900):
                part = piece[start:start + 900].strip()
                if len(part) >= 45:
                    result.append(part)
        else:
            result.append(piece)
    return result


def build_profile(paper_id: str, pages: list[dict[str, Any]], paper_sha256: str,
                  title: str = "", max_claims: int = 50) -> dict[str, Any]:
    if max_claims < 1:
        raise ValueError("max_claims must be positive")
    claims = []
    for page in pages:
        for quote in _sentences(page["text"]):
            scope = bool(_SCOPE.search(quote))
            mechanism = bool(_MECHANISM.search(quote))
            evaluation = bool(_EVALUATION.search(quote))
            if not (scope or mechanism):
                continue
            kind = "scope_candidate" if scope else "mechanism_candidate"
            if evaluation:
                kind = "evaluation_or_mechanism_candidate"
            claims.append({
                "evidence_id": stable_id("paper", paper_id, page["page"], quote),
                "paper_id": paper_id, "page": page["page"], "quote": quote,
                "sha256": text_sha256(quote), "kind": kind,
                "review_status": "pending", "scope_constraint": None,
                "retrieval_score": 3 * scope + 2 * mechanism + int(page["page"] <= 3),
            })
    claims.sort(key=lambda e: (-e["retrieval_score"], e["page"], e["evidence_id"]))
    seen, selected = set(), []
    for claim in claims:
        normalized = " ".join(claim["quote"].lower().split())
        if normalized in seen:
            continue
        seen.add(normalized)
        selected.append(claim)
        if len(selected) >= max_claims:
            break
    return {
        "schema_version": "1.0", "paper_id": paper_id, "title": title,
        "paper_sha256": paper_sha256, "page_count": len(pages),
        "backend": "deterministic_evidence_retrieval", "evidence": selected,
        "scope_constraints": [], "scope_review_status": "pending",
        "limitations": [
            "Retrieved passages require semantic review; lexical retrieval does not establish a claim.",
            "Experimental settings are not automatically converted into supported-input constraints.",
            "Formula and table extraction requires checking the original PDF.",
        ],
    }


def extract_paper(paper_id: str, pdf_path: Path, output_dir: Path,
                  title: str = "", max_claims: int = 50) -> dict[str, Any]:
    from pypdf import PdfReader

    pdf_path, output_dir = Path(pdf_path), Path(output_dir)
    if not pdf_path.is_file() or pdf_path.read_bytes()[:5] != b"%PDF-":
        raise ValueError(f"Not a PDF: {pdf_path}")
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")
    if len(reader.pages) > 300:
        raise ValueError("PDF exceeds the 300-page extraction limit")
    pages = []
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        pages.append({"page": number, "text": text, "sha256": text_sha256(text)})
    if sum(len(p["text"].strip()) for p in pages) < 100:
        raise ValueError("PDF has insufficient extractable text; OCR/manual transcription is required")
    digest = file_sha256(pdf_path)
    profile = build_profile(paper_id, pages, digest, title, max_claims)
    write_json(output_dir / "pages.json", {"paper_id": paper_id, "paper_sha256": digest, "pages": pages})
    write_json(output_dir / "profile.json", profile)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "paper.txt").write_text("\n\n".join(f"=== PDF PAGE {p['page']} ===\n{p['text']}" for p in pages), encoding="utf-8")
    return profile


def retrieve_evidence(profile: dict[str, Any], query: str, limit: int = 8) -> list[dict[str, Any]]:
    query_terms = terms(query)
    scored = []
    for evidence in profile.get("evidence", []):
        overlap = query_terms & terms(evidence["quote"])
        scored.append((len(overlap), evidence.get("retrieval_score", 0), evidence))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]["page"], x[2]["evidence_id"]))
    return [dict(e, lexical_overlap=score) for score, _, e in scored[:limit]]
