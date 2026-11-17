"""Run one attempt package and assemble the ExecutionReport + TestCase.

Attempt package layout (checklimits/attempts/<artifact>/<finding>/):
  manifest.json    AttemptManifest
  form.json        AgentForm (what the agent declared)
  driver.py        def run(inputs: dict) -> object   (calls the entry; no assertions of its own)
  condition.py     optional: def predicate(locals: dict) -> bool
  sim.py           optional: implementations for mocks with behavior "sim"
  (the oracle lock is not in the package: locks/<artifact>/<test_id>.json, written by the harness at the first run, T1)

What the harness runs (each is a source of evidence for one defeater, see confidence.py):
  main pair        positive and negative input, traced, one process per input        D1 D2 D4 D6 D11 D12 D14
  untraced pair    same inputs without the tracer                                    D7
  repeats          the main pair again in fresh processes, canonical trace hashes     D8
  boundary probes  full-scale inputs and the neighbours of the negative input,
                   stopped at the target decision                                    D5 D10
  mutation         mutants of the target statement in a temporary repo copy          D3
  replay           fresh checkout of the pinned commit, fresh copy of the attempt    D9
The probe, mutation and replay runs are never used for the verdict itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Optional

from . import audit as audit_mod
from . import bva as bva_mod
from . import confidence, fidelity, mutate, runner, verdict
from .adapter import load_task
from .models import (PIPELINE_ROOT, PROJECT_ROOT, scratch_root, AgentForm, AttemptManifest, Checks, Cost, Env, ExecutionReport,
                     Fidelity, MutantResult, MutationResult, Observation, OracleRecord, RepeatResult, ReplayResult,
                     design_sha256, make_testcase)
from .profile import DEFAULT, Profile
from .stats import rule_of_three, wilson_lower


@dataclass
class RunOptions:
    probe_effect: bool = True
    repeats: Optional[int] = None  # None = profile.n_rep
    bva: bool = True
    mutation: bool = True
    replay: bool = True

    @classmethod
    def fast(cls) -> "RunOptions":
        """Main pair only. Every optional defeater stays 'open'; used by unit tests."""
        return cls(probe_effect=False, repeats=1, bva=False, mutation=False, replay=False)


LOCKS_DIR = PROJECT_ROOT / "locks"


def register_oracle(lock: Path, sha: str) -> tuple[bool, int]:
    """T1: record the oracle hash at the first run; count later changes. Returns (preregistered, revisions).

    The lock lives in a harness-owned directory (locks/<artifact>/<test_id>.json), not inside the attempt
    package, so an agent that edits its package cannot reset the revision count by deleting the lock.
    `history` lists every hash seen, oldest first; a caller that keeps its own copy can detect tampering
    with `lock_is_extension`."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    if not lock.exists():
        lock.write_text(json.dumps({"sha256": sha, "revisions": 0, "history": [sha]}, indent=1) + "\n")
        return True, 0
    data = json.loads(lock.read_text())
    if data["sha256"] != sha:
        data = {"sha256": sha, "revisions": data["revisions"] + 1, "history": data.get("history", []) + [sha]}
        lock.write_text(json.dumps(data, indent=1) + "\n")
    return True, data["revisions"]


def lock_is_extension(old: dict[str, Any], new: Optional[dict[str, Any]]) -> bool:
    """True if `new` is `old` with zero or more later entries (history preserved, revisions not lower)."""
    if new is None:
        return False
    oh, nh = old.get("history", []), new.get("history", [])
    return nh[:len(oh)] == oh and new.get("revisions", 0) >= old.get("revisions", 0)


def _pkg_versions(python: str) -> dict[str, str]:
    code = ("import importlib.metadata as m, json\nout={}\n"
            "for n in ('torch','triton','transformers','einops','numpy','pydantic'):\n"
            "    try: out[n]=m.version(n)\n    except m.PackageNotFoundError: pass\n"
            "print(json.dumps(out))")
    try:
        return json.loads(subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=30).stdout)
    except Exception:
        return {}


def differing_factors(pos: dict[str, Any], neg: dict[str, Any]) -> list[str]:
    return sorted(k for k in set(pos) | set(neg) if pos.get(k) != neg.get(k))


_ADDR = re.compile(r"0x[0-9a-fA-F]+")


def condition_names(expr: Optional[str]) -> Optional[set[str]]:
    """Names (and dotted roots) a condition expression reads. None = not parseable, so keep every local."""
    import ast as _ast
    if not expr:
        return None
    try:
        tree = _ast.parse(expr.split("#")[0].strip(), mode="eval")
    except SyntaxError:
        return None
    names: set[str] = set()
    for n in _ast.walk(tree):
        if isinstance(n, _ast.Name):
            names.add(n.id)
    return names


def canonical_hash(raw: dict, obs: Observation, relevant: Optional[set[str]] = None) -> str:
    """Hash of everything observable about a run except timing, sequence numbers and unrelated locals.

    Locals are only hashed for the names the Region condition reads (`relevant`; None = all). A local such as
    `init_time = time.time()` or an object address differs on every run of a deterministic program and would
    make D8 / D9 fail for a reason that has nothing to do with the finding. All locals stay in the report."""
    exc = raw.get("exception") or {}
    trace = raw.get("trace") or {}
    payload = {
        "status": raw.get("status"),
        "exc": [exc.get("type"), exc.get("raised_at"), _ADDR.sub("0x", exc.get("message") or "")],
        "returned": raw.get("returned"),
        "hits": [[h["outcome"], h["condition_value"],
                  {k: v for k, v in h["locals"].items() if relevant is None or k in relevant}]
                 for h in trace.get("target_hits", [])],
        "guard": [h["condition_value"] for h in trace.get("decision_hits", [])],
        "starts": [[s["file"], s["fn"]] for s in trace.get("starts", [])],
        "lines": trace.get("lines", {}),
        "effect": obs.effect,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class _Ctx:
    """Everything needed to run cases of one attempt."""

    def __init__(self, attempt_dir: Path, pipeline_root: Path) -> None:
        self.attempt_dir = attempt_dir.resolve()
        self.pipeline_root = pipeline_root
        self.manifest = AttemptManifest.model_validate_json((self.attempt_dir / "manifest.json").read_text())
        self.form = AgentForm.model_validate_json((self.attempt_dir / self.manifest.form).read_text())
        ff = pipeline_root / self.manifest.findings_file if self.manifest.findings_file else None
        self.task = load_task(self.manifest.finding_id, pipeline_root / self.manifest.data_dir, ff)
        self.region = self.task.region(self.manifest.region_id)
        self.loc = f"{self.region.location.file}:{self.region.location.line_start}"
        self.repo = (pipeline_root / self.manifest.repo_dir).resolve()
        self.mocks = self.form.execution.mocks
        self.pred_file = self.form.design.condition_predicate_file
        # a predicate file can read any local; with the Region's own condition only its names matter
        self.relevant = None if self.pred_file else condition_names(self.region.condition.expr)
        self.exp_type = verdict.expected_exception_type(self.form.design.oracle)
        from .tracer import statement_span, target_span
        self.span = target_span(self.repo, self.region.location.file, self.region.location.line_start)
        self.full_span = statement_span(self.repo, self.region.location.file, self.region.location.line_start)
        self.free = {fp.name: fp.value for fp in self.form.design.free_parameters}  # disclosed free parameters (T3)
        if self.form.test_id != self.manifest.test_id or self.form.finding_id != self.manifest.finding_id:
            raise ValueError("form.json and manifest.json disagree on test_id / finding_id")

    def prelude_for(self, role_or_label: str) -> list[dict[str, Any]]:
        """Calls made before the checked call (state_dependent findings). Positive labels use the positive prelude,
        everything else (negative, extra negatives, neighbours) the negative one."""
        d = self.form.design
        pre = d.positive_prelude if role_or_label.startswith("pos") else d.negative_prelude
        return [{**self.free, **p} for p in pre]

    def run(self, role: str, design_inputs: dict[str, Any], *, trace: bool = True, stop: bool = False,
            repo: Optional[Path] = None, attempt_dir: Optional[Path] = None) -> tuple[dict, Observation]:
        inputs = {**self.free, **design_inputs}
        spec = runner.build_spec(self.manifest, attempt_dir or self.attempt_dir, self.pipeline_root, self.region,
                                 inputs, self.mocks, self.pred_file, trace, repo_dir=repo, stop_after_target=stop)
        spec["seed"] = self.manifest.seed
        spec["prelude"] = self.prelude_for(role)
        raw = runner.run_child(spec, self.manifest.timeout_s, self.manifest.env, python=self.manifest.python)
        return raw, runner.to_observation(raw, role, inputs, self.region, self.exp_type, self.span, self.full_span)

    def run_many(self, cases: list[tuple[str, dict[str, Any]]], *, repo: Optional[Path] = None
                 ) -> dict[str, Observation]:
        """Probe runs: several inputs in one process, each stopped at the target decision."""
        spec = runner.build_spec(self.manifest, self.attempt_dir, self.pipeline_root, self.region,
                                 {}, self.mocks, self.pred_file, True, repo_dir=repo, stop_after_target=True)
        spec["seed"] = self.manifest.seed
        cs = [{"id": label, "inputs": {**self.free, **inp}, "prelude": self.prelude_for(label)} for label, inp in cases]
        raws = runner.run_cases(spec, cs, self.manifest.timeout_s, self.manifest.env, python=self.manifest.python)
        return {label: runner.to_observation(raws[label], "negative" if label.startswith("neg") else "positive",
                                             {**self.free, **inp}, self.region, self.exp_type, self.span, self.full_span)
                for label, inp in cases}


BVA_RETRIES = 2


def _run_bva(ctx: _Ctx, profile: Profile) -> Optional[bva_mod.BvaResult]:
    cases, bvar, reason = bva_mod.plan(ctx.form, ctx.task.trigger, profile.probe_step)
    obs = ctx.run_many(cases)
    effects = {k: o.effect for k, o in obs.items()}
    # A neighbour probe that never decided the target (for example a time-limited generator that timed out under
    # machine load) is run again, at most BVA_RETRIES times, one case at a time. Only undecided probes are retried,
    # so a decided effect is never overwritten and a retry can only turn 'open' into a measured result.
    for _ in range(BVA_RETRIES):
        undecided = [(k, inp) for k, inp in cases if k in ("neg+", "neg-") and effects.get(k) is None]
        if not undecided:
            break
        for k, o in ctx.run_many(undecided).items():
            effects[k] = o.effect
    inputs = {label: inp for label, inp in cases}
    return bva_mod.evaluate(ctx.form.design.boundary_variable, effects, inputs, bvar is not None, reason)


def _run_mutation(ctx: _Ctx, original_verdict: str, profile: Profile) -> MutationResult:
    src = (ctx.repo / ctx.region.location.file).read_text()
    mutants = mutate.generate(src, ctx.region.location.line_start)
    results: list[MutantResult] = []
    scratch = scratch_root()
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix="mut_") as td:
        copy = Path(td) / "repo"
        shutil.copytree(ctx.repo, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        target = copy / ctx.region.location.file
        try:
            for m in mutants:
                target.write_text(m.source)
                cases = [("pos_m", ctx.form.design.positive_input), ("neg_m", ctx.form.design.negative_input)] + \
                        [(f"neg_x{i}", inp) for i, inp in enumerate(ctx.form.design.extra_negatives)]
                obs = ctx.run_many(cases, repo=copy)
                after = verdict.decide(obs["pos_m"], obs["neg_m"]).verdict
                extra_hit = any(obs[f"neg_x{i}"].effect is not False for i in range(len(ctx.form.design.extra_negatives)))
                killed = after != original_verdict or extra_hit
                results.append(MutantResult(operator=m.operator, line=m.line, original=m.original, mutated=m.mutated,
                                            killed=killed, verdict_after=after + (" + extra negative fired" if extra_hit else "")))
        finally:
            target.write_text(src)
    killed = sum(r.killed for r in results)
    return MutationResult(generated=len(results), killed=killed,
                          wilson_lower=round(wilson_lower(killed, len(results), profile.wilson_z), 3),
                          mutants=results,
                          note="a mutant is killed when the verdict computed from its runs differs from the original verdict; "
                               "equivalent mutants are not removed")


def _run_replay(ctx: _Ctx, main_hashes: dict[str, str]) -> ReplayResult:
    """SCORECARD 3.6: new temp dir, fresh checkout of the pinned commit, fresh copy of the attempt,
    new processes, scrubbed environment. The harness replays its own invocation instead of executing
    the agent's replay_commands strings, so an attempt cannot make the harness run arbitrary commands."""
    scratch = scratch_root()
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix="replay_") as td:
        co = Path(td) / "repo"
        try:
            subprocess.run(["git", "clone", "-q", "--no-hardlinks", "--no-checkout", str(ctx.repo), str(co)],
                           check=True, capture_output=True, timeout=120)
            subprocess.run(["git", "-C", str(co), "checkout", "-q", ctx.manifest.repo_commit],
                           check=True, capture_output=True, timeout=120)
        except subprocess.CalledProcessError as e:
            return ReplayResult(ok=False, detail=f"checkout of {ctx.manifest.repo_commit[:8]} failed: {e.stderr[-200:]!r}")
        att = Path(td) / "attempt"
        shutil.copytree(ctx.attempt_dir, att, ignore=shutil.ignore_patterns("__pycache__"))
        raw_p, pos = ctx.run("positive", ctx.form.design.positive_input, repo=co, attempt_dir=att)
        raw_n, neg = ctx.run("negative", ctx.form.design.negative_input, repo=co, attempt_dir=att)
    got = {"positive": canonical_hash(raw_p, pos, ctx.relevant), "negative": canonical_hash(raw_n, neg, ctx.relevant)}
    ok = got == main_hashes
    return ReplayResult(ok=ok, detail="fresh checkout reproduces both runs (identical canonical traces)" if ok else
                        "fresh checkout gave different canonical traces: " +
                        ", ".join(k for k in got if got[k] != main_hashes[k]))


def run_attempt(attempt_dir: Path, pipeline_root: Path = PIPELINE_ROOT, options: Optional[RunOptions] = None,
                profile: Profile = DEFAULT, probe: Optional[bool] = None,
                locks_dir: Optional[Path] = None) -> dict[str, Any]:
    t_start = time.monotonic()
    options = options or RunOptions()
    if probe is not None:  # backwards-compatible switch used by early tests
        options.probe_effect = probe
    ctx = _Ctx(attempt_dir, pipeline_root)
    form, region, task, manifest = ctx.form, ctx.region, ctx.task, ctx.manifest
    notes: list[str] = list(task.notes)

    # T1: register the oracle before running anything
    pred_bytes = (ctx.attempt_dir / ctx.pred_file).read_bytes() if ctx.pred_file else None
    sha = design_sha256(form, pred_bytes)
    env_locks = os.environ.get("CHECKLIMITS_LOCKS_DIR")
    lock = (locks_dir or (Path(env_locks) if env_locks else LOCKS_DIR)) / manifest.artifact_id / f"{manifest.test_id}.json"
    prereg, revisions = register_oracle(lock, sha)

    # main pair (traced)
    raw_p, pos = ctx.run("positive", form.design.positive_input)
    raw_n, neg = ctx.run("negative", form.design.negative_input)
    supported, support_note = runner.outcome_support(region, ctx.repo)
    if not supported:
        pos.effect_note = neg.effect_note = support_note
    v = verdict.decide(pos, neg, supported)

    # extra negatives: more inputs that must show no effect
    extra_obs = [ctx.run("negative", inp)[1] for inp in form.design.extra_negatives]
    extras_clean = None if not extra_obs else all(o.effect is False and o.target_reached for o in extra_obs)

    # D7: untraced pair
    probe_ok: Optional[bool] = None
    probe_note = "untraced runs not made"
    if options.probe_effect:
        untraced = [ctx.run("positive", form.design.positive_input, trace=False)[0],
                    ctx.run("negative", form.design.negative_input, trace=False)[0]]
        probe_ok, probe_note = fidelity.probe_effect([raw_p, raw_n], untraced)

    # D8: repeats in fresh processes
    n_rep = options.repeats if options.repeats is not None else profile.n_rep
    hashes = {"positive": [canonical_hash(raw_p, pos, ctx.relevant)], "negative": [canonical_hash(raw_n, neg, ctx.relevant)]}
    for _ in range(n_rep - 1):
        rp, op = ctx.run("positive", form.design.positive_input)
        rn, on = ctx.run("negative", form.design.negative_input)
        hashes["positive"].append(canonical_hash(rp, op, ctx.relevant))
        hashes["negative"].append(canonical_hash(rn, on, ctx.relevant))
    repeat = None
    if n_rep >= 2:
        distinct = max(len(set(hashes["positive"])), len(set(hashes["negative"])))
        repeat = RepeatResult(runs=n_rep, identical=distinct == 1, distinct_hashes=distinct,
                              flake_bound=round(rule_of_three(n_rep), 3),
                              trace_hash=hashlib.sha256((hashes["positive"][0] + hashes["negative"][0]).encode()).hexdigest()[:16])

    # coverage, fidelity
    chain = list(region.call_chain)
    pos.coverage = fidelity.coverage(ctx.repo, chain, (raw_p.get("trace") or {}).get("lines", {}))
    neg.coverage = fidelity.coverage(ctx.repo, chain, (raw_n.get("trace") or {}).get("lines", {}))
    ad = fidelity.ast_diff(ctx.repo, manifest.repo_commit, chain, region.location.file,
                           region.location.line_start, region.location.snippet,
                           (region.location.function or "").partition("::")[2])
    first_hit = lambda raw: min((h["seq"] for h in (raw.get("trace") or {}).get("target_hits", [])
                                if h.get("call", 0) == raw.get("final_call", 0)), default=None)
    mock_recs = fidelity.mock_records(
        ctx.mocks, [(raw_p["mock_events"], first_hit(raw_p)), (raw_n["mock_events"], first_hit(raw_n))], chain)
    entry_idx = fidelity.entry_index(chain, pos.entry_first_started)
    entry_on_stack = fidelity.entry_on_stack(chain, region.location.function, pos)
    fid = Fidelity(strategy=form.strategy, ast_diff=ad, mocks=mock_recs, entry_index=entry_idx,
                   call_chain_len=len(chain), probe_effect_free=bool(probe_ok), probe_note=probe_note)
    if entry_idx is None or chain[entry_idx] != form.execution.entry_called:
        notes.append(f"entry observed first: {pos.entry_first_started!r}; form declares {form.execution.entry_called!r}")
    if sorted(form.execution.repo_files_modified) != sorted(ad.files_changed):
        notes.append(f"form.repo_files_modified={form.execution.repo_files_modified} but git shows {ad.files_changed}")

    # T3: positive input against the witness hint
    hint = task.trigger
    sc = form.design.scale
    if task.witness_type == "input_value" and hint:
        for k in sorted(task.witness.input_keys & set(hint)):
            hv = hint[k]
            got = form.design.positive_input.get(k)
            if sc and k in sc.scaled and isinstance(hv, (int, float)) and got == int(hv * sc.factor):
                continue
            if got != hv:
                notes.append(f"T3: positive_input[{k!r}]={got!r} differs from the witness trigger value {hv!r}")
        if sc:
            notes.append(f"scaled down by {sc.factor} for {sc.scaled}: {sc.reason}")

    info = fidelity.info_items(pos, neg, raw_p, raw_n, ctx.mocks, ctx.loc)
    au = audit_mod.audit(form, pos, neg)
    factors = differing_factors(form.design.positive_input, form.design.negative_input)
    if form.design.positive_prelude != form.design.negative_prelude:
        factors = sorted(set(factors) | {"prelude"})
    controls_differ = pos.effect is not None and neg.effect is not None and pos.effect != neg.effect

    # D5, D10: boundary probes at full scale
    bva_res = _run_bva(ctx, profile) if options.bva and supported else None
    # D3: mutation
    mut_res = _run_mutation(ctx, v.verdict, profile) if options.mutation and supported and v.verdict != "inconclusive" else None
    # D9: replay
    replay_res = None
    if options.replay and supported:
        replay_res = _run_replay(ctx, {"positive": hashes["positive"][0], "negative": hashes["negative"][0]})

    verified = verdict.verify_tier(form.design.oracle, ctx.loc)
    if verified != form.design.oracle.tier:
        notes.append(f"oracle tier declared {form.design.oracle.tier}, verified {verified}")
    orec = OracleRecord(declared_tier=form.design.oracle.tier, verified_tier=verified, type=form.design.oracle.type,
                        spec=form.design.oracle.spec, signal_location=form.design.oracle.signal_location,
                        sha256=sha, preregistered=prereg, revisions_after_first_run=revisions)

    m = confidence.Measurements(
        verdict=v.verdict, outcome_supported=supported, target_reached=pos.target_reached,
        cond_true_on_positive=audit_mod.cond_value(pos, True), cond_false_on_negative=audit_mod.cond_value(neg, False),
        condition_translated=bool(ctx.pred_file),
        region_cond_true_on_positive=audit_mod.region_cond_value(pos, True) if ctx.pred_file else None,
        region_cond_false_on_negative=audit_mod.region_cond_value(neg, False) if ctx.pred_file else None, mutation=mut_res,
        declared_tier=form.design.oracle.tier, verified_tier=verified, preregistered=prereg, oracle_revisions=revisions,
        differing_factors=factors, controls_differ=controls_differ, extra_negatives_clean=extras_clean,
        bva=bva_res, info=info,
        probe_effect_free=probe_ok, repeat=repeat, replay=replay_res, scale_declared=sc is not None,
        main_positive_effect=pos.effect, main_negative_effect=neg.effect,
        target_intact=ad.target_statement_intact, stmts_changed=ad.statements_changed, stmts_total=ad.statements_total,
        snippet_matches=ad.snippet_matches_region, scope_status=str(task.finding.scope_status),
        entry_index=entry_idx, entry_on_stack=entry_on_stack, entry_reason=form.execution.entry_reason)
    conf, final_verdict = confidence.build(m, profile)
    exec_result = v.exec_result
    if final_verdict == "inconclusive" and v.verdict != "inconclusive":
        if conf.level == "invalid":
            exec_result = "test_error"
        notes.append("verdict forced to inconclusive: " + conf.level_note)
    skipped = [n for n, on in (("probe effect", options.probe_effect), ("boundary probes", options.bva),
                               ("mutation", options.mutation), ("replay", options.replay)) if not on]
    if skipped or n_rep < 2:
        notes.append("not run (defeaters stay open): " + ", ".join(skipped + (["repeats"] if n_rep < 2 else [])))

    report = ExecutionReport(
        test_id=manifest.test_id, finding_id=manifest.finding_id, artifact_id=manifest.artifact_id,
        region_id=region.region_id, verdict=v.verdict, final_verdict=final_verdict, exec_result=exec_result,
        verdict_reason=v.reason, strategy=form.strategy, oracle=orec, positive=pos, negative=neg,
        extra_negatives=extra_obs,
        checks=Checks(controls_differ=controls_differ, differing_factors=factors, bva=bva_res, mutation=mut_res,
                      repeat=repeat, replay=replay_res),
        fidelity=fid, audit=au, information=info, confidence=conf, finding_confidence=task.finding.confidence,
        env=Env(executable_on="cpu_mock" if ctx.mocks else "cpu", python=platform.python_version(),
                packages=_pkg_versions(runner.resolve_python(manifest.python)), repo_commit=manifest.repo_commit),
        cost=Cost(wall_seconds=round(time.monotonic() - t_start, 1)), notes=notes)

    tc_inputs = [{"role": "positive", **form.design.positive_input}, {"role": "negative", **form.design.negative_input}]
    if task.witness_type == "event_sequence":
        tc_inputs = [{"role": r, "call": i + 1, **c} for r, calls in
                     (("positive", [form.design.positive_input]), ("negative", [form.design.negative_input]))
                     for i, c in enumerate(calls)]
    testcase = make_testcase(report, form, manifest, task.witness_type, tc_inputs)
    return {"report": report, "testcase": testcase, "raw": {"positive": raw_p, "negative": raw_n}}


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
