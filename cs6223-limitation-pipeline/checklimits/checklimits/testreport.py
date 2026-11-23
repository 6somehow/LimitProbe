"""Per-Finding test records and the LIMITATIONS.md report (contract: CONTRACT_TEST_REPORT.md).

Every Finding of the step 4 file gets exactly one record, tested or not. A record never hides why a Finding was not
judged, and every level is labelled "uncalibrated" (CONFIDENCE_SPEC.md §12)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

SCHEMA = "checklimits-test-report/1"
NOT_RUN_CODES = ("no_code_location", "outcome_unsupported", "witness_unusable", "env_unavailable",
                 "input_unreadable", "not_attempted", "agent_failed", "harness_error")
ENV_CODES = ("env_unavailable", "agent_failed", "harness_error")      # what --strict treats as a failure


class _M(BaseModel):
    model_config = {"extra": "forbid"}


class NotRun(_M):
    code: str
    reason: str


class Doubt(_M):
    id: str
    name: str
    status: str
    evidence: str = ""


class TestRecord(_M):
    __test__ = False                                      # not a pytest class
    schema_version: str = SCHEMA
    finding_id: str
    artifact_id: str
    status: str                                           # tested | not_run
    not_run: Optional[NotRun] = None
    verdict: Optional[str] = None                         # yes | no | inconclusive
    level: Optional[str] = None                           # L0..L3 | invalid | n/a
    calibrated: bool = False
    confidence_label: str = "uncalibrated"
    level_note: str = ""
    verdict_reason: str = ""
    observed: dict[str, str] = Field(default_factory=dict)
    defeaters: dict[str, str] = Field(default_factory=dict)
    open_doubts: list[Doubt] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    finding: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    files: dict[str, str] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    analysis: Optional[dict[str, Any]] = None             # analysis lane (analysis.py); never a test verdict


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- what step 4 said about the Finding
def _cut(s: Any, n: int) -> str:
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def finding_block(raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """(finding summary, evidence) copied from a step 4 Finding record, nothing re-worded."""
    wh = raw.get("witness_hint") or {}
    lims = raw.get("limitations") or []
    code: list[dict[str, Any]] = []
    paper: list[dict[str, Any]] = []
    for lim in lims:
        for c in lim.get("code_evidence") or []:
            item = {"file": c.get("file"), "line_start": c.get("line_start"), "function": c.get("function"),
                    "snippet": _cut(c.get("snippet"), 400)}
            if item not in code:
                code.append(item)
        for e in lim.get("paper_evidence") or []:
            item = {"quote": _cut(e.get("quote"), 500), "source": e.get("source"), "locator": e.get("locator")}
            if item not in paper:
                paper.append(item)
    for v in raw.get("verifications") or []:
        for e in v.get("matching_evidence") or []:
            item = {"quote": _cut(e.get("quote"), 500), "source": e.get("source"), "locator": e.get("locator")}
            if item not in paper:
                paper.append(item)
    location = wh.get("location")
    if not location and code and code[0].get("file"):
        location = f"{code[0]['file']}:{code[0].get('line_start')}"
    fin = {"category": raw.get("category"), "step4_level": raw.get("level"), "effect_type": raw.get("effect_type"),
           "priority": raw.get("priority"), "summary": raw.get("summary"), "review": raw.get("review"),
           "review_note": raw.get("review_note"), "scope_status": raw.get("scope_status"),
           "witness_status": wh.get("status"), "location": location, "function": wh.get("function"),
           "condition": wh.get("condition"),
           # code side's static process confidence (step 4, docs/11_process_confidence.md); None if absent
           "process_confidence": raw.get("process_confidence")}
    return fin, {"paper": paper[:3], "code": code[:3]}


# --------------------------------------------------------------------------- records
def not_run_record(raw: dict[str, Any], code: str, reason: str, provenance: Optional[dict[str, Any]] = None
                   ) -> TestRecord:
    assert code in NOT_RUN_CODES, code
    fin, ev = finding_block(raw)
    return TestRecord(finding_id=raw["finding_id"], artifact_id=raw["artifact_id"], status="not_run",
                      not_run=NotRun(code=code, reason=reason), finding=fin, evidence=ev,
                      provenance=provenance or {})


def tested_record(raw: dict[str, Any], report: Any, files: dict[str, str], provenance: dict[str, Any]
                  ) -> TestRecord:
    """report: an ExecutionReport (checklimits.models)."""
    fin, ev = finding_block(raw)
    c = report.confidence
    doubts = [Doubt(id=d.id, name=d.name, status=d.status, evidence=d.evidence)
              for d in c.defeaters if d.status != "eliminated"]
    return TestRecord(
        finding_id=raw["finding_id"], artifact_id=raw["artifact_id"], status="tested",
        verdict=report.final_verdict, level=c.level, calibrated=False, level_note=c.level_note,
        verdict_reason=report.verdict_reason or "",
        observed={"positive": report.positive.observed_text or "", "negative": report.negative.observed_text or ""},
        defeaters={d.id: d.status for d in c.defeaters}, open_doubts=doubts, next_steps=list(c.next_steps),
        finding=fin, evidence=ev, files=files,
        provenance={**provenance, "profile": c.profile.name})


# --------------------------------------------------------------------------- 1:1
def check_one_to_one(input_ids: list[str], records: list[TestRecord], md: Optional[str] = None) -> list[str]:
    """Problems found; empty = every input Finding has exactly one record (and one table row and one section)."""
    problems: list[str] = []
    ids = [r.finding_id for r in records]
    if len(input_ids) != len(set(input_ids)):
        problems.append("input has duplicate finding ids")
    for fid in sorted(set(input_ids) - set(ids)):
        problems.append(f"no record for {fid}")
    for fid in sorted(set(ids) - set(input_ids)):
        problems.append(f"record for {fid}, which is not in the input")
    for fid in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"{fid} has {ids.count(fid)} records")
    for r in records:
        if r.status == "not_run" and r.not_run is None:
            problems.append(f"{r.finding_id}: not_run without a reason")
        if r.status == "tested" and (r.verdict is None or r.level is None):
            problems.append(f"{r.finding_id}: tested without verdict or level")
        if r.calibrated or r.confidence_label != "uncalibrated":
            problems.append(f"{r.finding_id}: a level must be labelled uncalibrated")
    if md is not None:
        for fid in input_ids:
            if md.count(f"\n## {fid} ") + md.count(f"\n## {fid}\n") != 1:
                problems.append(f"{fid}: not exactly one section in LIMITATIONS.md")
            if md.count(f"| [{fid}](#") != 1:
                problems.append(f"{fid}: not exactly one row in the summary table")
    return problems


def counts(records: list[TestRecord]) -> dict[str, Any]:
    from collections import Counter
    tested = [r for r in records if r.status == "tested"]
    return {"tested": len(tested), "not_run": len(records) - len(tested),
            "verdict": dict(Counter(r.verdict for r in tested)),
            "level": dict(Counter(r.level for r in tested)),
            "not_run_by_code": dict(Counter(r.not_run.code for r in records if r.not_run)),
            "analysis_tiers": dict(Counter(r.analysis["tier"] for r in records if r.analysis))}


# --------------------------------------------------------------------------- LIMITATIONS.md
def _verdict_text(verdict: Optional[str], effect_type: Optional[str]) -> str:
    """What a verdict means for this effect type. For a branch effect the harness only observes that the branch at the
    location is taken, so the report says that and not more (an LLM reviewer pointed this out on 3 of 20 sampled items)."""
    if verdict == "yes":
        if effect_type in ("path_change", "state"):
            return ("with the trigger the branch at the location is taken and with the contrast it is not; "
                    "what the claim says happens after the branch was not checked")
        if effect_type == "reject":
            return "with the trigger the exception is raised at the location and with the contrast it is not"
        return "the effect was observed with the trigger and not with the contrast"
    if verdict == "no":
        return "the effect was not observed where the Finding says it should be, and the oracle was shown to see it when it exists"
    return "no verdict: the test was invalid or could not separate the cases"


_LEVEL_TEXT = {
    "invalid": "a fatal defeater was refuted (for example the target line was not reached): no verdict is drawn",
    "n/a": "no verdict, so no level",
    "L0": "no fatal defeater was refuted, but at least one fatal check was not done",
    "L1": "indicative: the fatal checks passed; some important checks are residual or open",
    "L2": "supported: fatal checks, mutation, repeat runs and clean-checkout replay passed; some checks are residual",
    "L3": "established: every defeater was measured and ruled out",
}


def _anchor(fid: str) -> str:
    return fid.lower().replace(".", "")


def _render_analysis(A, an: dict[str, Any]) -> None:
    from .analysis import TIER_TEXT
    A(f"**Analysis only, tier {an['tier']} (uncalibrated; this is not a test verdict).** "
      f"{TIER_TEXT.get(an['tier'], '')}. {_cut(an.get('tier_note'), 200)}")
    A("")
    A(f"- reading: **{an.get('assessment')}**. {_cut(an.get('reasoning'), 500)}")
    st = an.get("static") or {}
    if st.get("cited"):
        A(f"- cited code found at the pinned commit: {'yes' if st.get('grounded') else '**no**'} "
          f"({st['cited']} location(s))")
    for p in an.get("probes") or []:
        A(f"- probe `{p.get('regex')}` in `{p.get('file')}` expected {p.get('expect')}: **{p.get('status')}** "
          f"({p.get('hits', 0)} hit(s)). {_cut(p.get('meaning'), 120)}")
    ac = an.get("arithmetic_check")
    if ac:
        A(f"- arithmetic check `{ac.get('expr')}` = {ac.get('value')} (paper needs: {_cut(ac.get('expect'), 80)}): "
          f"*{ac.get('status')}*. {_cut(ac.get('meaning'), 120)}")
    if an.get("hardware_needed"):
        A("- the claim concerns behaviour that needs a GPU, an accelerator or a real run")
    if an.get("would_confirm"):
        A(f"- what would settle it: {_cut(an['would_confirm'], 250)}")
    A("")


def render_markdown(artifact: dict[str, Any], records: list[TestRecord], env: Optional[dict[str, Any]],
                    findings_file: str, findings_sha: str, generated_at: Optional[str] = None) -> str:
    cs = counts(records)
    L: list[str] = []
    A = L.append
    A(f"# Limitations report: {artifact.get('paper_title') or artifact['artifact_id']}")
    A("")
    A(f"- artifact: `{artifact['artifact_id']}` ({artifact.get('venue') or 'venue unknown'}), "
      f"repository {artifact.get('repo_url')}" + (f" at `{str(artifact['commit'])[:10]}`" if artifact.get("commit") else ""))
    A(f"- input: `{findings_file}` (sha256 `{findings_sha[:12]}`), {len(records)} Findings")
    A(f"- generated: {generated_at or now_iso()} by `checklimits test` (contract `{SCHEMA}`)")
    if env:
        A(f"- environment: **{env.get('status')}**" + (f" ({'; '.join(env.get('reasons') or [])})" if env.get("reasons") else ""))
    A("")
    A("## How to read this")
    A("")
    A("* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.")
    A("* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. "
      "A code agent designed the test; the harness re-ran it and checked what the agent declared.")
    A("* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong "
      "(the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. "
      "**All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.")
    A("* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.")
    A("* A Finding that was not tested may carry an **analysis** (tier A0 to A2): a reading of the paper and code "
      "evidence, with text probes run by the harness. It is a weaker kind of evidence than a test, has its own "
      "uncalibrated tiers, and never says yes or no.")
    A("* Step 4 labels (`review`) come from a blind LLM review, not a human.")
    A("")
    A("## Summary")
    A("")
    A(f"| | |\n|---|---|\n| Findings | {len(records)} |\n| tested | {cs['tested']} |\n| not tested | {cs['not_run']} |")
    if cs["verdict"]:
        A("| verdicts | " + ", ".join(f"{k} {v}" for k, v in sorted(cs["verdict"].items())) + " |")
        A("| levels | " + ", ".join(f"{k} {v}" for k, v in sorted(cs["level"].items())) + " |")
    if cs.get("analysis_tiers"):
        A("| analysis only (not tests) | " + ", ".join(f"{k} {v}" for k, v in sorted(cs["analysis_tiers"].items())) + " |")
    if cs["not_run_by_code"]:
        A("| not tested, by reason | " + ", ".join(f"`{k}` {v}" for k, v in sorted(cs["not_run_by_code"].items())) + " |")
    A("")
    A("| Finding | category | effect | location | result |")
    A("|---|---|---|---|---|")
    for r in records:
        f = r.finding
        res = (f"**{r.verdict}** / {r.level} (uncalibrated)" if r.status == "tested"
               else f"not tested: `{r.not_run.code}`" + (f", analysis {r.analysis['tier']}/{r.analysis['assessment']}"
                                                         if r.analysis else ""))
        A(f"| [{r.finding_id}](#{_anchor(r.finding_id)}) | {f.get('category') or ''} | {f.get('effect_type') or ''} "
          f"| {('`' + f['location'] + '`') if f.get('location') else ''} | {res} |")
    A("")
    for r in records:
        f = r.finding
        A(f"## {r.finding_id}")
        A("")
        A(f"**{_cut(f.get('summary'), 600)}**")
        A("")
        A(f"- category `{f.get('category')}`, effect `{f.get('effect_type')}`, step 4 level {f.get('step4_level')}, "
          f"priority {f.get('priority')}, scope `{f.get('scope_status')}`")
        if f.get("location"):
            A(f"- code: `{f['location']}`" + (f" in `{f['function']}`" if f.get("function") else ""))
        if f.get("condition"):
            A(f"- condition: `{_cut(f['condition'], 200)}`")
        if f.get("review") and f["review"] != "unreviewed":
            A(f"- step 4 review: `{f['review']}`: {_cut(f.get('review_note'), 300)}")
        for e in r.evidence.get("paper", [])[:2]:
            A(f"- paper/docs ({e.get('source')}, {e.get('locator')}): “{_cut(e.get('quote'), 300)}”")
        for e in r.evidence.get("code", [])[:1]:
            if e.get("snippet"):
                A(f"- code snippet (`{e.get('file')}:{e.get('line_start')}`): `{_cut(e['snippet'], 200)}`")
        A("")
        if r.status == "not_run":
            A(f"**Not tested** (`{r.not_run.code}`): {r.not_run.reason}")
            A("")
            if r.analysis:
                _render_analysis(A, r.analysis)
            continue
        A(f"**Verdict `{r.verdict}`**: {_verdict_text(r.verdict, r.finding.get('effect_type'))}.")
        if r.verdict_reason:
            A(f"  {_cut(r.verdict_reason, 400)}")
        A("")
        A(f"**Level {r.level}, uncalibrated.** {_LEVEL_TEXT.get(r.level or '', '')}. {_cut(r.level_note, 300)}".rstrip())
        A("")
        A(f"- trigger run: {r.observed.get('positive') or 'n/a'}")
        A(f"- contrast run: {r.observed.get('negative') or 'n/a'}")
        if r.open_doubts:
            A("- open doubts:")
            for d in r.open_doubts:
                A(f"  - {d.id} {d.name}: *{d.status}*. {_cut(d.evidence, 220)}")
        else:
            A("- open doubts: none")
        if r.next_steps:
            A("- what would raise the level: " + "; ".join(_cut(s, 160) for s in r.next_steps[:3]))
        if r.files.get("execution_report"):
            A(f"- evidence: `tests/{r.artifact_id}/{r.finding_id}/{r.files['execution_report']}`")
        A("")
    return "\n".join(L) + "\n"


def write_record(dir_: Path, rec: TestRecord) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    p = dir_ / "report.json"
    p.write_text(rec.model_dump_json(indent=1) + "\n")
    return p


def read_record(p: Path) -> TestRecord:
    return TestRecord.model_validate(json.loads(p.read_text()))
