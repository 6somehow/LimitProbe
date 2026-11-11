"""Run one attempt package and assemble the ExecutionReport + TestCase.

Attempt package layout (checklimits/attempts/<artifact>/<finding>/):
  manifest.json    AttemptManifest
  form.json        AgentForm (what the agent declared)
  driver.py        def run(inputs: dict) -> object   (calls the entry; no assertions of its own)
  condition.py     optional: def predicate(locals: dict) -> bool
  oracle.lock.json written by the harness: hash of the design at its first run (T1)

Cases run: positive (traced), negative (traced), then both again untraced to measure the
probe effect. Mutation, replay and repeats are not run in P1; scoring treats them as not run.
"""
from __future__ import annotations

import json
import platform
import time
from importlib import metadata
from pathlib import Path
from typing import Any, Optional

from . import audit as audit_mod
from . import fidelity, runner, scoring, verdict
from .adapter import load_task
from .models import (PIPELINE_ROOT, AgentForm, AttemptManifest, Checks, Cost, Env, EvidenceRecord,
                     ExecutionReport, Fidelity, Observation, OracleRecord, design_sha256, make_testcase)


def register_oracle(attempt_dir: Path, sha: str) -> tuple[bool, int]:
    """T1: record the design hash at the first run; count later changes. Returns (preregistered, revisions)."""
    lock = attempt_dir / "oracle.lock.json"
    if not lock.exists():
        lock.write_text(json.dumps({"sha256": sha, "revisions": 0}, indent=1) + "\n")
        return True, 0
    data = json.loads(lock.read_text())
    if data["sha256"] != sha:
        data = {"sha256": sha, "revisions": data["revisions"] + 1}
        lock.write_text(json.dumps(data, indent=1) + "\n")
    return True, data["revisions"]


def _pkg_versions() -> dict[str, str]:
    out = {}
    for name in ("torch", "triton", "transformers", "einops", "numpy", "pydantic"):
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pass
    return out


def differing_factors(pos: dict[str, Any], neg: dict[str, Any]) -> list[str]:
    return sorted(k for k in set(pos) | set(neg) if pos.get(k) != neg.get(k))


def boundary_adjacent(pos: dict[str, Any], neg: dict[str, Any], boundary_var: str,
                      factors: list[str]) -> Optional[bool]:
    """Heuristic (see report): one differing integer factor that is the boundary variable, and the two
    values are neighbours: differ by 1, or are a factor of two apart (shape parameters are powers of two)."""
    if factors != [boundary_var]:
        return None
    a, b = pos.get(boundary_var), neg.get(boundary_var)
    if not (isinstance(a, int) and isinstance(b, int)) or isinstance(a, bool) or isinstance(b, bool):
        return None
    if abs(a - b) == 1:
        return True
    lo, hi = sorted((abs(a), abs(b)))
    return lo > 0 and hi == 2 * lo


def run_attempt(attempt_dir: Path, pipeline_root: Path = PIPELINE_ROOT, probe: bool = True) -> dict[str, Any]:
    t_start = time.monotonic()
    attempt_dir = attempt_dir.resolve()
    manifest = AttemptManifest.model_validate_json((attempt_dir / "manifest.json").read_text())
    form = AgentForm.model_validate_json((attempt_dir / manifest.form).read_text())
    task = load_task(manifest.finding_id, pipeline_root / manifest.data_dir)
    region = task.region(manifest.region_id)
    loc = f"{region.location.file}:{region.location.line_start}"
    repo = (pipeline_root / manifest.repo_dir).resolve()
    notes: list[str] = list(task.notes)
    if form.test_id != manifest.test_id or form.finding_id != manifest.finding_id:
        raise ValueError("form.json and manifest.json disagree on test_id / finding_id")

    # T1: register the oracle/design before running anything
    pred_file = form.design.condition_predicate_file
    pred_bytes = (attempt_dir / pred_file).read_bytes() if pred_file else None
    sha = design_sha256(form, pred_bytes)
    prereg, revisions = register_oracle(attempt_dir, sha)

    exp_type = verdict.expected_exception_type(form.design.oracle)
    mocks = form.execution.mocks

    free = {fp.name: fp.value for fp in form.design.free_parameters}  # disclosed free parameters (T3)

    def case(role: str, design_inputs: dict[str, Any], trace: bool) -> tuple[dict, Observation]:
        inputs = {**free, **design_inputs}
        spec = runner.build_spec(manifest, attempt_dir, pipeline_root, region, inputs, mocks, pred_file, trace)
        spec["seed"] = manifest.seed
        raw = runner.run_child(spec, manifest.timeout_s, manifest.env, python=manifest.python)
        return raw, runner.to_observation(raw, role, inputs, region, exp_type)

    raw_p, pos = case("positive", form.design.positive_input, True)
    raw_n, neg = case("negative", form.design.negative_input, True)
    untraced = []
    if probe:
        untraced = [case("positive", form.design.positive_input, False)[0],
                    case("negative", form.design.negative_input, False)[0]]

    hint = task.finding.witness_hint or {}
    sc = form.design.scale
    if task.witness_type == "input_value":
        for k, hv in hint.items():
            got = form.design.positive_input.get(k)
            if sc and k in sc.scaled and isinstance(hv, (int, float)) and got == int(hv * sc.factor):
                continue  # declared scale-down
            if got != hv:
                notes.append(f"T3: positive_input[{k!r}]={got!r} differs from witness_hint {hv!r}")
        if sc:
            notes.append(f"scaled down by {sc.factor} for {sc.scaled}: {sc.reason}")
    # scale check: the positive run stops at the target, so it is cheap to repeat at full witness scale
    scale_pos_verified = None
    scale_obs = None
    if sc:
        full = dict(form.design.positive_input)
        for k in sc.scaled:
            if k in hint:
                full[k] = hint[k]
        _, scale_obs = case("positive", full, True)
        scale_pos_verified = bool(scale_obs.effect) == bool(pos.effect) and scale_obs.effect is not None
    supported = region.outcome == "reject"
    v = verdict.decide(pos, neg, supported)

    # coverage from the positive trace
    chain = list(region.call_chain)
    pos.coverage = fidelity.coverage(repo, chain, (raw_p.get("trace") or {}).get("lines", {}))
    neg.coverage = fidelity.coverage(repo, chain, (raw_n.get("trace") or {}).get("lines", {}))

    # fidelity
    ad = fidelity.ast_diff(repo, manifest.repo_commit, chain, region.location.file,
                           region.location.line_start, region.location.snippet)
    first_hit = lambda raw: min((h["seq"] for h in (raw.get("trace") or {}).get("target_hits", [])), default=None)
    mock_recs = fidelity.mock_records(
        mocks, [(raw_p["mock_events"], first_hit(raw_p)), (raw_n["mock_events"], first_hit(raw_n))], chain)
    entry_idx = fidelity.entry_index(chain, pos.entry_first_started)
    probe_ok, probe_note = fidelity.probe_effect([raw_p, raw_n], untraced)
    on_path = sum(m.on_path for m in mock_recs)
    off_path = len(mock_recs) - on_path
    fid = Fidelity(
        strategy=form.strategy, ast_diff=ad, mocks=mock_recs, entry_index=entry_idx, call_chain_len=len(chain),
        probe_effect_free=probe_ok, probe_note=probe_note,
        s_mod=round(fidelity.s_mod(ad.statements_changed, ad.statements_total), 3),
        s_mock=round(fidelity.s_mock(on_path, off_path), 3),
        s_entry=round(fidelity.s_entry(entry_idx, len(chain)), 3),
        s_probe=1.0 if probe_ok else 0.0)
    declared_entry = form.execution.entry_called
    if entry_idx is None or chain[entry_idx] != declared_entry:
        notes.append(f"entry observed first: {pos.entry_first_started!r}; form declares {declared_entry!r}")
    if sorted(form.execution.repo_files_modified) != sorted(ad.files_changed):
        notes.append(f"form.repo_files_modified={form.execution.repo_files_modified} but git shows {ad.files_changed}")

    info = fidelity.info_items(pos, neg, raw_p, raw_n, mocks, loc, sc is not None, scale_pos_verified)
    if scale_obs is not None:
        notes.append("scale check (positive at full witness scale): " + scale_obs.observed_text)

    # audit
    au = audit_mod.audit(form, pos, neg)

    # control pair
    factors = differing_factors(form.design.positive_input, form.design.negative_input)
    controls_differ = pos.effect is not None and neg.effect is not None and pos.effect != neg.effect
    adjacent = boundary_adjacent(form.design.positive_input, form.design.negative_input,
                                 form.design.boundary_variable, factors)
    checks = Checks(controls_differ=controls_differ, differing_factors=factors, boundary_adjacent=adjacent,
                    mutation=None, replay=None, runs=1, consistent_runs=1)

    # oracle
    verified = verdict.verify_tier(form.design.oracle, loc)
    if verified != form.design.oracle.tier:
        notes.append(f"oracle tier declared {form.design.oracle.tier}, verified {verified}")
    orec = OracleRecord(declared_tier=form.design.oracle.tier, verified_tier=verified,
                        type=form.design.oracle.type, spec=form.design.oracle.spec,
                        signal_location=form.design.oracle.signal_location, sha256=sha, preregistered=prereg,
                        revisions_after_first_run=revisions)

    seen = audit_mod.outcomes_seen(pos, neg)
    cond_pos = audit_mod.cond_value(pos, True)
    cond_neg = audit_mod.cond_value(neg, False)
    ev = EvidenceRecord(
        target_reached=pos.target_reached, decision_outcomes=len(seen),
        cond_true_on_positive=cond_pos, cond_false_on_negative=cond_neg,
        condition_translated=bool(pred_file), oracle_tier=verified, preregistered=prereg,
        oracle_revisions_after_first_run=revisions, controls_differ=controls_differ,
        differing_factors=len(factors), boundary_adjacent=adjacent, mutants_generated=None, mutants_killed=None,
        critical_modification=not ad.target_statement_intact,
        modified_stmt_ratio=(ad.statements_changed / ad.statements_total) if ad.statements_total else 0.0,
        mocks_on_path=on_path, mocks_off_path=off_path, entry_index=entry_idx, call_chain_len=len(chain),
        probe_effect_free=probe_ok, replay_ok=None, runs=1, consistent_runs=1,
        declared_checks=au.declared_checks, matched_checks=au.matched_checks, verdict=v.verdict)
    card, final_verdict = scoring.score(ev)
    exec_result = v.exec_result
    if final_verdict == "inconclusive" and v.verdict != "inconclusive":
        exec_result = "test_error"
        notes.append("verdict forced to inconclusive by gate: " + card.level_note)
    if not ad.snippet_matches_region:
        notes.append("Region.location.snippet differs from the repository line")
    notes.append("mutation and replay were not run (P1); reliability and mutation score 0, gate G2 not evaluated")

    report = ExecutionReport(
        test_id=manifest.test_id, finding_id=manifest.finding_id, artifact_id=manifest.artifact_id,
        region_id=region.region_id, verdict=v.verdict, final_verdict=final_verdict, exec_result=exec_result,
        verdict_reason=v.reason, strategy=form.strategy, oracle=orec, positive=pos, negative=neg, checks=checks,
        fidelity=fid, audit=au, information=info, evidence=ev, scorecard=card, finding_confidence=task.finding.confidence,
        env=Env(executable_on="cpu_mock" if mocks else "cpu", python=platform.python_version(),
                packages=_pkg_versions(), repo_commit=manifest.repo_commit),
        cost=Cost(wall_seconds=round(time.monotonic() - t_start, 1)), notes=notes)

    tc_inputs = [{"role": "positive", **form.design.positive_input}, {"role": "negative", **form.design.negative_input}]
    if task.witness_type == "event_sequence":
        tc_inputs = [{"role": r, "call": i + 1, **c} for r, calls in
                     (("positive", [form.design.positive_input]), ("negative", [form.design.negative_input]))
                     for i, c in enumerate(calls)]
    testcase = make_testcase(report, form, manifest, task.witness_type, tc_inputs)
    return {"report": report, "testcase": testcase, "raw": {"positive": raw_p, "negative": raw_n,
                                                            "untraced": untraced}}


def write_outputs(result: dict[str, Any], out_dir: Path, runs_dir: Path | None = None) -> dict[str, Path]:
    report: ExecutionReport = result["report"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rp = out_dir / f"{report.test_id}.report.json"
    tp = out_dir / f"{report.test_id}.testcase.json"
    rp.write_text(report.model_dump_json(indent=1) + "\n")
    # codeside.cli validate expects a JSON list of records
    tp.write_text(json.dumps([result["testcase"].model_dump(mode="json")], indent=1) + "\n")
    paths = {"report": rp, "testcase": tp}
    if runs_dir is not None:
        runs_dir.mkdir(parents=True, exist_ok=True)
        rawp = runs_dir / f"{report.test_id}.raw.json"
        rawp.write_text(json.dumps(result["raw"], indent=1, default=str))
        paths["raw"] = rawp
    return paths
