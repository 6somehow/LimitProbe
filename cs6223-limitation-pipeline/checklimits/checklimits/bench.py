"""Fault-injection benchmark (CONFIDENCE_SPEC.md section 7).

Each case is an attempt run against a system whose ground truth we control:

  repo_fault     the FlexPrefill checkout is cloned, one line is edited and committed, and the edited
                 checkout is the system under test. `claim_true` says whether the finding's claim
                 ("the witness input is rejected at this line, the neighbouring input is not") holds
                 in that variant.
  attempt_fault  the repository is the original (claim true) but the attempt is made worse in one
                 specific way. The verdict may stay right; the level must drop.

Per case the benchmark records the verdict, the level, the defeater states and whether the outcome
is acceptable. Outcome classes for decided verdicts (yes / no): TP, FP, TN, FN. `inconclusive` is an
abstention. A false positive (yes while the claim is false) is the failure the confidence level exists
to prevent.

Honest scope: a few dozen deterministic cases are a smoke test of the rules, not a calibration.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .harness import RunOptions, run_attempt
from .models import PIPELINE_ROOT, PROJECT_ROOT
from .stats import wilson_lower

SRC = "flex_prefill/ops/flex_prefill_attention.py"
REPO = PIPELINE_ROOT / "third_party" / "FlexPrefill"
COMMIT = "a24b27bf117fd6ad4ba34b0db82c598e7786fd59"
LEVEL_ORDER = {"n/a": -2, "invalid": -1, "L0": 0, "L1": 1, "L2": 2, "L3": 3}

# target statement of each finding, exactly as in the pinned commit (4-space indent)
TARGET = {
    "F07": '    assert batch_size == 1, "only support batch size 1 for now"',
    "F01": "    assert q.shape[1] == k.shape[1]",
    "F04": "    assert head_dim in {16, 32, 64, 128}",
}
RELAXED = {
    "F07": '    assert batch_size <= 2, "only support batch size 1 for now"',
    "F01": "    assert q.shape[1] * 4 >= k.shape[1]",
    "F04": "    assert head_dim in {16, 32, 64, 96, 128}",
}
INVERTED = {
    "F07": '    assert batch_size != 1, "only support batch size 1 for now"',
    "F01": "    assert q.shape[1] != k.shape[1]",
    "F04": "    assert head_dim not in {16, 32, 64, 128}",
}
OTHER_EXC = {
    "F07": '    if not (batch_size == 1): raise ValueError("only support batch size 1 for now")',
    "F01": "    if not (q.shape[1] == k.shape[1]): raise ValueError('q/k length mismatch')",
    "F04": "    if not (head_dim in {16, 32, 64, 128}): raise ValueError('bad head_dim')",
}


@dataclass
class Case:
    id: str
    finding: str
    kind: str                                   # control | repo_fault | attempt_fault
    description: str
    claim_true: bool
    acceptable: set[str]                        # final verdicts that count as a correct outcome
    repo_edit: Optional[Callable[[str, str], str]] = None   # (finding, source text) -> new source text
    attempt_edit: Optional[Callable[[Path], None]] = None   # edits the copied attempt directory
    max_level: Optional[str] = None             # for attempt faults: the level must not exceed this
    tags: list[str] = field(default_factory=list)
    # True: the Region's snippet is regenerated from the edited line (an extractor that read the variant
    # correctly) while Region.condition stays as the original finding stated it (an extractor that misread
    # the condition). False: the whole Region is stale (derived from the unmodified repository).
    fresh_snippet: bool = False


TARGET_LINE = {"F07": 1824, "F01": 1836, "F04": 1837}   # the same statement text also occurs elsewhere in the file


def _edit_line(finding: str, src: str, new_text: str) -> str:
    """Replace the target line (by number, after checking its text) with new_text (may be several lines)."""
    lines = src.split("\n")
    i = TARGET_LINE[finding] - 1
    assert lines[i] == TARGET[finding], f"{finding}: line {i + 1} is {lines[i]!r}"
    lines[i] = new_text
    return "\n".join(lines)


def _replace_target(new: dict[str, str]) -> Callable[[str, str], str]:
    return lambda finding, src: _edit_line(finding, src, new[finding])


def _delete_target(finding: str, src: str) -> str:
    return _edit_line(finding, src, "    pass")


def _shift_target(finding: str, src: str) -> str:
    return _edit_line(finding, src, "    # unrelated comment that moves the statement down one line\n" + TARGET[finding])


def _collide_target(finding: str, src: str) -> str:
    """Put a different, harmless assert on the target line; the original statement moves down one line."""
    return _edit_line(finding, src, "    assert batch_size > 0\n" + TARGET[finding])


def _edit_form(att: Path, fn: Callable[[dict], None]) -> None:
    p = att / "form.json"
    d = json.loads(p.read_text())
    fn(d)
    p.write_text(json.dumps(d, indent=2) + "\n")


def _att_fake_einops(att: Path) -> None:
    def f(d):
        d["execution"]["mocks"].append({"symbol": "einops", "kind": "fake_module", "behavior": "return_first_arg",
                                        "sim_class": "stub",
                                        "reason": "BENCH: stands in for a library imported before the target"})
        d["strategy"] = "S1"
    _edit_form(att, f)


def _att_scale_dependent(att: Path) -> None:
    p = att / "driver.py"
    s = p.read_text()
    p.write_text(s.replace("def run(inputs):\n",
                           "def run(inputs):\n    if inputs[\"q_len\"] < 1024:   # BENCH: behaviour depends on the scale\n"
                           "        inputs = dict(inputs, batch_size=1)\n", 1))


def _att_no_location(att: Path) -> None:
    def f(d):
        d["design"]["oracle"]["tier"] = "O3"
        d["design"]["oracle"]["signal_location"] = None
        d["design"]["oracle"]["spec"] = "AssertionError raised"
    _edit_form(att, f)


def _att_false_claims(att: Path) -> None:
    def f(d):
        d["claims"]["target_reached"] = False
        d["claims"]["condition_true_on_positive"] = False
        d["claims"]["positive_observed"] = "ValueError at :1"
    _edit_form(att, f)


def build_cases() -> list[Case]:
    cases: list[Case] = []
    for f in ("F07", "F01", "F04"):
        cases += [
            Case(f"{f}-orig", f, "control", "unmodified repository", True, {"yes"}),
            Case(f"{f}-delete-stale", f, "repo_fault", "target replaced by `pass`; Region is stale (still shows the assert)",
                 False, {"no", "inconclusive"}, repo_edit=_delete_target, tags=["stale-region"]),
            Case(f"{f}-delete-snip", f, "repo_fault",
                 "target replaced by `pass`; Region snippet is current but its condition still claims a rejection",
                 False, {"no"}, repo_edit=_delete_target, fresh_snippet=True, tags=["wrong-condition"]),
            Case(f"{f}-relax-stale", f, "repo_fault", "guard relaxed so the witness is accepted; Region is stale",
                 False, {"no", "inconclusive"}, repo_edit=_replace_target(RELAXED), tags=["stale-region"]),
            Case(f"{f}-relax-snip", f, "repo_fault",
                 "guard relaxed so the witness is accepted; Region snippet current, condition still the original",
                 False, {"no"}, repo_edit=_replace_target(RELAXED), fresh_snippet=True, tags=["wrong-condition"]),
            Case(f"{f}-invert-snip", f, "repo_fault", "guard inverted (boundary direction reversed); Region snippet current",
                 False, {"no", "inconclusive"}, repo_edit=_replace_target(INVERTED), fresh_snippet=True),
            Case(f"{f}-otherexc-snip", f, "repo_fault",
                 "same rejection raised as ValueError instead of AssertionError; Region snippet current",
                 True, {"yes", "inconclusive"}, repo_edit=_replace_target(OTHER_EXC), fresh_snippet=True,
                 tags=["oracle-too-specific"]),
            Case(f"{f}-shifted", f, "repo_fault", "a comment is inserted above the target: Region.location is stale",
                 True, {"inconclusive"}, repo_edit=_shift_target, tags=["stale-location"]),
            Case(f"{f}-collide", f, "repo_fault",
                 "a different assert now sits on the target line; the original moved down",
                 True, {"inconclusive"}, repo_edit=_collide_target, tags=["stale-location"]),
        ]
    cases += [
        Case("F07-att-fake-einops", "F07", "attempt_fault", "a stub module is touched before the target line",
             True, {"yes"}, attempt_edit=_att_fake_einops, max_level="L1"),
        Case("F07-att-scale-dependent", "F07", "attempt_fault", "driver behaves differently at small scale",
             True, {"inconclusive"}, attempt_edit=_att_scale_dependent),
        Case("F07-att-no-location", "F07", "attempt_fault", "oracle names the exception type but not the location",
             True, {"yes"}, attempt_edit=_att_no_location, max_level="L1"),
        Case("F07-att-false-claims", "F07", "attempt_fault", "form claims contradict what happened",
             True, {"yes"}, attempt_edit=_att_false_claims),
    ]
    return cases


def _git(repo: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=bench", "-c", "user.email=b@b", *a],
                          check=True, capture_output=True, text=True, timeout=120).stdout


def prepare(case: Case, work: Path) -> Path:
    """Create work/<case.id>/{attempt, repo?}; returns the attempt directory."""
    root = work / case.id
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    att = root / "attempt"
    shutil.copytree(PROJECT_ROOT / "attempts" / "flexprefill" / case.finding, att,
                    ignore=shutil.ignore_patterns("oracle.lock.json", "__pycache__"))
    manifest = json.loads((att / "manifest.json").read_text())
    manifest["test_id"] = f"B-{case.id}"
    if case.repo_edit is not None:
        repo = root / "repo"
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", "--no-checkout", str(REPO), str(repo)],
                       check=True, capture_output=True, timeout=120)
        _git(repo, "checkout", "-q", COMMIT)
        f = repo / SRC
        f.write_text(case.repo_edit(case.finding, f.read_text()))
        _git(repo, "commit", "-q", "-am", f"bench fault {case.id}")
        manifest["repo_dir"] = str(repo.relative_to(PIPELINE_ROOT))
        manifest["repo_commit"] = _git(repo, "rev-parse", "HEAD").strip()
        if case.fresh_snippet:
            data = root / "data"
            shutil.copytree(PIPELINE_ROOT / manifest["data_dir"], data)
            regions = json.loads((data / "gold_regions.json").read_text())
            for reg in regions:
                if reg["region_id"] == manifest["region_id"]:
                    line = reg["location"]["line_start"]
                    reg["location"]["snippet"] = f.read_text().splitlines()[line - 1].strip()
            (data / "gold_regions.json").write_text(json.dumps(regions, indent=1))
            manifest["data_dir"] = str(data.relative_to(PIPELINE_ROOT))
    (att / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    form = json.loads((att / "form.json").read_text())
    form["test_id"] = f"B-{case.id}"
    (att / "form.json").write_text(json.dumps(form, indent=2) + "\n")
    if case.attempt_edit is not None:
        case.attempt_edit(att)
    return att


def run_case(case: Case, work: Path, options: RunOptions) -> dict[str, Any]:
    t0 = time.monotonic()
    base = {"id": case.id, "finding": case.finding, "kind": case.kind, "description": case.description,
            "claim_true": case.claim_true, "acceptable": sorted(case.acceptable), "max_level": case.max_level,
            "tags": case.tags}
    try:
        att = prepare(case, work)
        r = run_attempt(att, options=options)["report"]
        out = {**base, "verdict": r.verdict, "final_verdict": r.final_verdict, "level": r.confidence.level,
               "level_note": r.confidence.level_note, "defeaters": {d.id: d.status for d in r.confidence.defeaters},
               "next_steps": r.confidence.next_steps, "form_integrity": r.audit.rate,
               "positive": r.positive.observed_text, "negative": r.negative.observed_text, "error": None}
    except Exception as e:  # a harness crash is itself a benchmark result
        out = {**base, "verdict": None, "final_verdict": None, "level": None, "level_note": "", "defeaters": {},
               "next_steps": [], "form_integrity": None, "positive": "", "negative": "",
               "error": f"{type(e).__name__}: {e}"[:300]}
    out["seconds"] = round(time.monotonic() - t0, 1)
    out["class"] = classify(out)
    out["ok"] = is_ok(out)
    return out


def classify(r: dict[str, Any]) -> str:
    fv = r["final_verdict"]
    if fv is None:
        return "ERROR"
    if fv == "inconclusive":
        return "ABSTAIN"
    return {(True, "yes"): "TP", (False, "yes"): "FP", (True, "no"): "FN", (False, "no"): "TN"}[(r["claim_true"], fv)]


def is_ok(r: dict[str, Any]) -> bool:
    if r["final_verdict"] not in r["acceptable"]:
        return False
    if r["max_level"] and LEVEL_ORDER[r["level"]] > LEVEL_ORDER[r["max_level"]]:
        return False
    return True


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    for r in results:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    levels: dict[str, dict[str, Any]] = {}
    for r in results:
        lv = levels.setdefault(str(r["level"]), {"cases": 0, "decided": 0, "correct": 0})
        lv["cases"] += 1
        if r["class"] in ("TP", "TN", "FP", "FN"):
            lv["decided"] += 1
            lv["correct"] += r["class"] in ("TP", "TN")
    for lv in levels.values():
        lv["accuracy"] = round(lv["correct"] / lv["decided"], 3) if lv["decided"] else None
        lv["wilson_lower"] = round(wilson_lower(lv["correct"], lv["decided"]), 3) if lv["decided"] else None
    decided = sum(by_class.get(k, 0) for k in ("TP", "TN", "FP", "FN"))
    return {"cases": len(results), "by_class": by_class, "decided": decided,
            "abstained": by_class.get("ABSTAIN", 0), "false_positives": [r["id"] for r in results if r["class"] == "FP"],
            "false_negatives": [r["id"] for r in results if r["class"] == "FN"],
            "unacceptable": [r["id"] for r in results if not r["ok"]], "by_level": levels}


def markdown(results: list[dict[str, Any]], summary: dict[str, Any], options: RunOptions) -> str:
    L = ["# Fault-injection benchmark", "",
         f"Generated by `python -m checklimits bench`. Options: repeats={options.repeats}, mutation={options.mutation}, "
         f"replay={options.replay}, boundary probes={options.bva}. Levels are **uncalibrated**; with this few cases the "
         "table is a smoke test of the rules, not a calibration.", "",
         "| case | kind | claim true | verdict | final | level | class | ok | note |", "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        note = r["error"] or r["level_note"] or "; ".join(
            k + "=" + v for k, v in r["defeaters"].items() if v in ("refuted", "residual"))
        L.append(f"| {r['id']} | {r['kind']} | {r['claim_true']} | {r['verdict']} | {r['final_verdict']} | {r['level']} | "
                 f"{r['class']} | {'yes' if r['ok'] else '**NO**'} | {note[:90]} |")
    L += ["", "## Summary", "",
          f"- cases: {summary['cases']}, decided: {summary['decided']}, abstained: {summary['abstained']}",
          f"- by class: {summary['by_class']}",
          f"- false positives (yes while the claim is false): {summary['false_positives'] or 'none'}",
          f"- false negatives (no while the claim is true): {summary['false_negatives'] or 'none'}",
          f"- outcomes outside the acceptable set: {summary['unacceptable'] or 'none'}", "",
          "| level | cases | decided | correct | accuracy | Wilson lower bound |", "|---|---|---|---|---|---|"]
    for lv, v in sorted(summary["by_level"].items(), key=lambda kv: LEVEL_ORDER.get(kv[0], -9), reverse=True):
        L.append(f"| {lv} | {v['cases']} | {v['decided']} | {v['correct']} | {v['accuracy']} | {v['wilson_lower']} |")
    return "\n".join(L) + "\n"


def run_bench(case_ids: Optional[list[str]], out_dir: Path, options: RunOptions, workers: int = 3) -> dict[str, Any]:
    cases = [c for c in build_cases() if not case_ids or c.id in case_ids]
    work = PROJECT_ROOT / "scratch" / "bench"
    work.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda c: run_case(c, work, options), cases))
    summary = summarize(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bench.json").write_text(json.dumps({"summary": summary, "results": results}, indent=1) + "\n")
    (out_dir / "BENCH.md").write_text(markdown(results, summary, options))
    return {"summary": summary, "results": results}
