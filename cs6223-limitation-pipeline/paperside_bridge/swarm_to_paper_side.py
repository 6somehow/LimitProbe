"""Convert a frozen Swarm report or gap receipt to the shared paper handoff."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import get_args

from schema.models import SCHEMA_VERSION, Limitation, SwarmCategory, TextEvidence

CATEGORIES = get_args(SwarmCategory)
CANDIDATE_KEYS = ("candidates", "findings", "results", "records", "limitations", "hypotheses", "items",
                  "method_limitations")
CANDIDATE_KINDS = {
    "disclosed_boundary": "applicability_limitation",
    "method_hypothesis": "method_shortcoming",
    "implementation_discrepancy": "method_shortcoming",
}
BLIND_DIRS = {"labels", "reference_material", "evaluator_evidence", "LLM_API_KEY"}


def input_path(path: Path) -> Path:
    resolved = path.resolve()
    if BLIND_DIRS.intersection(path.absolute().parts) or BLIND_DIRS.intersection(resolved.parts):
        raise ValueError("Swarm inputs must come from the paper or generation archive")
    return resolved


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pages(pdf: Path, extractor: str) -> list[str]:
    if extractor == "pypdf":
        from pypdf import PdfReader
        with pdf.open("rb") as source:
            return [page.extract_text() or "" for page in PdfReader(source).pages]
    if extractor == "pymupdf":
        import pymupdf
        with pymupdf.open(pdf) as doc:
            return [page.get_text() for page in doc]
    raise ValueError(f"unknown PDF extractor {extractor!r}")


def _text(*values) -> str:
    for value in values:
        if isinstance(value, list):
            value = "; ".join(str(item) for item in value)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _evidence(candidate: dict, pages: list[str]) -> list[TextEvidence]:
    citations = candidate.get("paper_evidence")
    if not isinstance(citations, list) or not citations:
        raise ValueError("missing paper_evidence")
    evidence = []
    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError("expected a paper citation with page and quote")
        page, quote = citation.get("page"), citation.get("quote")
        if type(page) is not int or not 1 <= page <= len(pages):
            raise ValueError(f"invalid physical PDF page {page!r}")
        if not isinstance(quote, str) or not quote.strip() or " ".join(quote.split()) not in pages[page - 1]:
            raise ValueError(f"quote does not occur on PDF page {page}")
        evidence.append(TextEvidence(quote=quote, locator=f"PDF p.{page}"))
    return evidence


def convert(artifact_id: str, report: Path, pdf: Path, *, extractor: str = "pypdf"
            ) -> tuple[dict, list[Limitation]]:
    if not re.fullmatch(r"[\w.-]+", artifact_id) or artifact_id in {".", ".."}:
        raise ValueError(f"invalid artifact ID {artifact_id!r}")
    report, pdf = input_path(report), input_path(pdf)
    raw = report.read_bytes()
    source = raw.decode("utf-8").strip()
    fence = re.fullmatch(r"\x60\x60\x60(?:json)?\s*(.*?)\s*\x60\x60\x60", source, re.S)
    data = json.loads(fence[1] if fence else source)
    if isinstance(data, list):
        data = {"candidates": data}
    if not isinstance(data, dict):
        raise ValueError("expected a report or receipt object")
    candidates = next((data[key] for key in CANDIDATE_KEYS if isinstance(data.get(key), list)), None)
    if candidates is None:
        raise ValueError("expected a report or receipt with a candidates list")
    if any(data[key] != artifact_id for key in ("paper_id", "artifact_id") if key in data):
        raise ValueError("report artifact does not match the requested artifact ID")
    pages = [" ".join(page.split()) for page in _pages(pdf, extractor)]
    provenance = {"report": str(report), "report_sha256": _digest(raw), "pdf_sha256": _digest(pdf.read_bytes()),
                  "extractor": extractor, "receipt_verdict": data.get("verdict")}
    limitations, dropped, seen = [], [], set()
    for index, candidate in enumerate(candidates, 1):
        if not isinstance(candidate, dict):
            raise ValueError(f"candidate #{index} must be an object")
        cid = _text(candidate.get("id"), candidate.get("candidate_id")) or f"candidate-{index}"
        if cid in seen:
            raise ValueError(f"duplicate candidate ID {cid!r}")
        seen.add(cid)
        if candidate.get("status") == "withdrawn" or data.get("verdict") == "refutes":
            dropped.append({"id": cid, "reason": "withdrawn or refuted"})
            continue
        kind = _text(candidate.get("kind"))
        category = candidate.get("category") or (
            kind if kind in CATEGORIES else CANDIDATE_KINDS.get(kind, "method_shortcoming"))
        if category not in CATEGORIES:
            raise ValueError(f"candidate {cid}: unknown category {category!r}")
        try:
            evidence = _evidence(candidate, pages)
        except ValueError as error:
            dropped.append({"id": cid, "reason": str(error)})
            continue
        effect = _text(candidate.get("consequence"), candidate.get("claim"), candidate.get("causal_argument"),
                       candidate.get("limitation"), candidate.get("title"))
        if not effect:
            raise ValueError(f"candidate {cid}: missing consequence, claim or title")
        limitations.append(Limitation(
            limitation_id=f"{artifact_id}-swarm-{cid}", artifact_id=artifact_id, origin="paper",
            level="L3", condition_text=_text(candidate.get("trigger"), candidate.get("conditions"),
                                              candidate.get("condition")) or "Unspecified",
            effect_type="other", effect_text=effect, paper_evidence=evidence, provenance="llm",
            swarm_category=category, swarm_provenance={**provenance, "candidate_id": cid, "candidate": candidate}))
    handoff = {"schema_version": SCHEMA_VERSION, "origin": "swarm", "artifact_id": artifact_id,
               "claims": [], "scope": [], "eval_points": [], "bindings": [],
               "candidate_evidence": [e.model_dump(mode="json") for lim in limitations for e in lim.paper_evidence],
               "provenance": provenance, "dropped": dropped}
    return handoff, limitations


def write_handoff(out: Path, handoff: dict, limitations: list[Limitation]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in (("limitations.json", [lim.model_dump(mode="json") for lim in limitations]),
                          ("paper_side.json", handoff)):
        (out / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_id")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--pdf-extractor", choices=("pypdf", "pymupdf"), default="pypdf")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        handoff, limitations = convert(args.artifact_id, args.report, args.pdf, extractor=args.pdf_extractor)
        write_handoff(args.out, handoff, limitations)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({"retained": len(limitations), "dropped": handoff["dropped"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
