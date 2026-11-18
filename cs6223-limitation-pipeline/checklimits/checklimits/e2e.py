"""`checklimits test | report | envcheck`: step 4 Findings in, one test record per Finding and LIMITATIONS.md out.

Contract: CONTRACT_TEST_REPORT.md. The orchestration here decides nothing about verdicts or levels: that stays in
the harness. It only selects, runs (or re-audits an existing attempt package), and records, so that every input
Finding ends up as exactly one record with either a result or the reason it was not tested."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from .agent_batch import classify_finding
from .models import PIPELINE_ROOT, PROJECT_ROOT, ExecutionReport
from .testreport import (ENV_CODES, SCHEMA, TestRecord, check_one_to_one, counts, file_sha256, not_run_record,
                         now_iso, read_record, render_markdown, tested_record, write_record)

DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results" / "e2e"
DEFAULT_ARCHIVE = PROJECT_ROOT / "agent_results"
EXIT_OK, EXIT_ERROR, EXIT_INPUT, EXIT_ONE_TO_ONE, EXIT_STRICT = 0, 1, 2, 3, 4


class InputError(Exception):
    """The step 4 file or the artifact registration cannot be used (exit code 2)."""


# --------------------------------------------------------------------------- inputs
def _load_inputs(findings_file: str, data_dir: str, root: Path = PIPELINE_ROOT
                 ) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    ff = root / findings_file
    if not ff.exists():
        raise InputError(f"{findings_file} does not exist (run the pipeline's step 4 first)")
    try:
        data = json.loads(ff.read_text())
        findings = data["findings"]
    except (ValueError, KeyError, TypeError) as e:
        raise InputError(f"{findings_file} is not a step 4 hand-off file: {e}")
    if not str(data.get("schema_version", "")).startswith("0.2"):
        raise InputError(f"{findings_file} has schema_version {data.get('schema_version')!r}; expected 0.2.x")
    for f in findings:
        if "finding_id" not in f or "artifact_id" not in f:
            raise InputError("a Finding without finding_id/artifact_id")
    ids = [f["finding_id"] for f in findings]
    if len(ids) != len(set(ids)):
        raise InputError("duplicate finding_id in the input")
    af = root / data_dir / "artifact.json"
    if not af.exists():
        raise InputError(f"{data_dir}/artifact.json does not exist")
    return findings, json.loads(af.read_text()), file_sha256(ff)


# --------------------------------------------------------------------------- environment pre-check (S3)
_IMPORT_PROBE = r"""
import importlib, json, sys
repo, roots, mods = sys.argv[1], json.loads(sys.argv[2]), json.loads(sys.argv[3])
sys.path[:0] = [repo] + [repo + "/" + r for r in roots if r]
out = []
for m in mods:
    try:
        importlib.import_module(m)
        out.append({"module": m, "ok": True, "error": None})
    except BaseException as e:
        out.append({"module": m, "ok": False, "error": (type(e).__name__ + ": " + str(e))[:300]})
print(json.dumps(out))
"""


def _module_names(art: dict[str, Any]) -> tuple[list[str], list[str]]:
    roots = [r for r in (art.get("package_roots") or [art.get("package_root")]) if r]
    mods: list[str] = []
    for ep in art.get("entry_points", []):
        f = ep.split("::")[0]
        for r in roots:
            if f.startswith(r.rstrip("/") + "/"):
                f = f[len(r.rstrip("/")) + 1:]
                break
        parts = f.removesuffix(".py").split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        m = ".".join(parts)
        if m and m not in mods:
            mods.append(m)
    return mods, roots


def envcheck(artifact_id: str, data_dir: str, repo_rel: str, python: Optional[str] = None, timeout_s: int = 180,
             root: Path = PIPELINE_ROOT) -> dict[str, Any]:
    """Check, do not install: repository at the pinned commit, interpreter for the code under test, entry modules
    importable. `not_ok` makes every judgeable Finding `not_run(env_unavailable)`."""
    from .agent_cli import _venv_python
    from .runner import resolve_python

    art = json.loads((root / data_dir / "artifact.json").read_text())
    reasons: list[str] = []
    repo = root / repo_rel
    r: dict[str, Any] = {"path": repo_rel, "exists": repo.is_dir(), "head": None, "expected": art.get("commit"),
                         "matches": False, "clean": None}
    if not repo.is_dir():
        reasons.append(f"repository {repo_rel} is not checked out")
    else:
        try:
            r["head"] = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                                       timeout=30).stdout.strip() or None
            r["clean"] = not subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True,
                                            text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        r["matches"] = bool(r["head"] and art.get("commit") and r["head"].startswith(art["commit"][:12]))
        if not r["matches"]:
            reasons.append(f"repository HEAD {str(r['head'])[:10]} is not the pinned commit {str(art.get('commit'))[:10]}")
    py_rel = python or _venv_python(artifact_id)
    py = resolve_python(py_rel)
    p: dict[str, Any] = {"path": py_rel or "harness interpreter", "exists": Path(py).exists(), "version": None}
    imports: list[dict[str, Any]] = []
    if not p["exists"]:
        reasons.append(f"interpreter {py} does not exist")
    else:
        try:
            p["version"] = subprocess.run([py, "-c", "import sys; print(sys.version.split()[0])"], capture_output=True,
                                          text=True, timeout=60).stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            reasons.append(f"interpreter {py} does not run")
    mods, roots = _module_names(art)
    if r["exists"] and p["exists"] and not any("does not run" in x for x in reasons):
        try:
            res = subprocess.run([py, "-c", _IMPORT_PROBE, str(repo), json.dumps(roots), json.dumps(mods)],
                                 capture_output=True, text=True, timeout=timeout_s, cwd=str(repo))
            imports = json.loads(res.stdout.strip().splitlines()[-1])
        except (subprocess.TimeoutExpired, ValueError, IndexError, OSError) as e:
            imports = [{"module": m, "ok": False, "error": f"import probe failed: {type(e).__name__}"} for m in mods]
        for i in imports:
            if not i["ok"]:
                reasons.append(f"cannot import {i['module']}: {i['error']}")
    return {"artifact_id": artifact_id, "status": "ok" if not reasons else "not_ok", "reasons": reasons,
            "repo": r, "python": p, "imports": imports, "execution_env": art.get("execution_env", [])}


def _provision_then_check(artifact: str, art: dict[str, Any], data_dir: str, repo_rel: str, python: Optional[str],
                          root: Path, tdir: Path, before: dict[str, Any]) -> dict[str, Any]:
    """The environment is not usable and the repository is there: build scratch/venv_<artifact> (`provision`), check again.
    What was tried and why it was needed stays in ENV.json."""
    from . import provision as pv
    try:
        rec = pv.provision(artifact, root / repo_rel, art.get("commit"), run_tests=False, out_dir=tdir / "provision")
        note = {"status": rec["status"], "reasons": rec["reasons"], "log": "provision/provision.log"}
    except Exception as e:      # a failed provisioning is a reason, not a crash
        note = {"status": "error", "reasons": [f"{type(e).__name__}: {str(e)[:300]}"]}
    after = envcheck(artifact, data_dir, repo_rel, python, root=root)
    after["provisioned"] = {"before": before["reasons"], **note}
    return after


# --------------------------------------------------------------------------- attempts
def find_attempts(roots: list[Path], max_depth: int = 4) -> dict[str, list[Path]]:
    """{finding_id: [attempt dirs]} for every directory with a manifest.json below the roots (first root first)."""
    found: dict[str, list[Path]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for m in sorted(root.rglob("manifest.json")):
            rel = m.relative_to(root).parts
            if len(rel) > max_depth or "scratch" in rel:
                continue
            try:
                d = json.loads(m.read_text())
                fid = d["finding_id"]
                if not (m.parent / d.get("driver", "driver.py")).exists():
                    continue
            except (ValueError, KeyError, OSError):
                continue
            found.setdefault(fid, []).append(m.parent)
    return found


def pick_attempt(attempts: list[Path], roots: list[Path]) -> Path:
    """The first root that has a package for the Finding wins; inside it the last one by name."""
    for root in roots:
        c = [a for a in attempts if root.resolve() in a.resolve().parents]
        if c:
            return c[-1]
    return attempts[-1]


def _copy_attempt(src: Path, dst: Path) -> None:
    if dst.exists():
        if dst.resolve() == src.resolve():
            return
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _rel(p: Path, base: Path) -> str:
    try:
        return p.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(p)


# --------------------------------------------------------------------------- one Finding
def _audit(attempt: Path, fast: bool, root: Path) -> dict[str, Any]:
    from .harness import RunOptions, run_attempt
    with tempfile.TemporaryDirectory(dir=_scratch()) as td:       # fresh oracle lock: the package is re-audited as is
        return run_attempt(attempt, pipeline_root=root, options=RunOptions.fast() if fast else RunOptions(),
                           locks_dir=Path(td))


def _scratch() -> Path:
    from .models import scratch_root
    p = scratch_root()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _write_tested(raw: dict[str, Any], report: ExecutionReport, testcase_json: str, attempt: Path, fdir: Path,
                  prov: dict[str, Any], results_root: Path) -> TestRecord:
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "execution_report.json").write_text(report.model_dump_json(indent=1) + "\n")
    (fdir / "testcase.json").write_text(testcase_json)
    _copy_attempt(attempt, fdir / "attempt")
    files = {"execution_report": "execution_report.json", "testcase": "testcase.json", "attempt": "attempt"}
    return tested_record(raw, report, files, prov)


def _agent_run(fid: str, findings_file: str, data_dir: str, fast: bool) -> tuple[Optional[Path], dict[str, Any]]:
    from .agent_loop import RUNS, Budget, run_agent
    from .harness import RunOptions
    run_id = f"e2e-{fid.split('-')[-1].lower()}-{uuid.uuid4().hex[:6]}"
    res = run_agent(fid, run_id, Budget(), RunOptions.fast() if fast else RunOptions(), findings_file=findings_file,
                    data_dir=data_dir)
    run_dir = RUNS / run_id
    ok = res.get("test_id") and (run_dir / "final").is_dir()
    return (run_dir if ok else None), res


def _test_one(raw: dict[str, Any], *, status: Optional[tuple[str, str]], env_ok: bool, env_reason: str,
              attempts: list[Path], roots: list[Path], results_root: Path, artifact: str, findings_file: str,
              findings_sha: str, data_dir: str, run_agent: bool, fast: bool, root: Path) -> TestRecord:
    fid = raw["finding_id"]
    fdir = results_root / "tests" / artifact / fid
    prov = {"findings_file": findings_file, "findings_sha256": findings_sha, "generated_at": now_iso()}
    if status is not None:
        return not_run_record(raw, status[0], status[1], prov)
    if not env_ok:
        return not_run_record(raw, "env_unavailable", env_reason, prov)
    try:
        if attempts:
            src = pick_attempt(attempts, roots)
            res = _audit(src, fast, root)
            prov.update({"source": "reaudit", "attempt_origin": _rel(src, PROJECT_ROOT),
                         "n_attempts_found": len(attempts)})
            tc = json.dumps([res["testcase"].model_dump(mode="json")], indent=1) + "\n"
            return _write_tested(raw, res["report"], tc, src, fdir, prov, results_root)
        if not run_agent:
            return not_run_record(raw, "not_attempted",
                                  "the harness can judge this Finding but no test package exists; "
                                  "run with --run-agent to have the code agent design one", prov)
        run_dir, ares = _agent_run(fid, findings_file, data_dir, fast)
        if run_dir is None:
            return not_run_record(raw, "agent_failed",
                                  f"the agent produced no auditable test package (run {ares.get('run_id')}, "
                                  f"{ares.get('tokens')} tokens, {ares.get('wall_s')} s)", prov)
        rep = ExecutionReport.model_validate(json.loads(next((run_dir / "final").glob("*.report.json")).read_text()))
        tc = next((run_dir / "final").glob("*.testcase.json")).read_text()
        prov.update({"source": "agent", "attempt_origin": f"scratch/agent_runs/{run_dir.name}",
                     "agent_tokens": ares.get("tokens"), "agent_wall_s": ares.get("wall_s"),
                     "lock_tampered": ares.get("lock_tampered")})
        return _write_tested(raw, rep, tc, run_dir / "workspace" / "attempt", fdir, prov, results_root)
    except Exception as e:      # one Finding failing is a record, not the end of the run
        return not_run_record(raw, "harness_error", f"{type(e).__name__}: {e}"[:400], prov)


# --------------------------------------------------------------------------- the run
def run_test(artifact: str, *, findings_file: str, data_dir: str, repo_rel: str,
             results_root: Path = DEFAULT_RESULTS_ROOT, attempts_roots: Optional[list[Path]] = None,
             run_agent: bool = False, only: Optional[list[str]] = None, workers: int = 3, fast: bool = False,
             strict: bool = False, skip_envcheck: bool = False, python: Optional[str] = None,
             root: Path = PIPELINE_ROOT, provision: bool = False, analyze: bool = False,
             model: Optional[str] = None) -> dict[str, Any]:
    findings, art, sha = _load_inputs(findings_file, data_dir, root)
    tdir = results_root / "tests" / artifact
    tdir.mkdir(parents=True, exist_ok=True)
    if skip_envcheck:
        env = {"artifact_id": artifact, "status": "ok", "reasons": ["environment pre-check skipped"], "repo": {},
               "python": {}, "imports": [], "execution_env": art.get("execution_env", [])}
    else:
        env = envcheck(artifact, data_dir, repo_rel, python, root=root)
        if env["status"] != "ok" and provision and env["repo"]["exists"]:
            env = _provision_then_check(artifact, art, data_dir, repo_rel, python, root, tdir, env)
    (tdir / "ENV.json").write_text(json.dumps(env, indent=1) + "\n")
    env_ok = env["status"] == "ok"
    env_reason = "; ".join(env["reasons"]) or "environment not usable"

    roots = list(attempts_roots) if attempts_roots is not None else [tdir, DEFAULT_ARCHIVE]
    found = find_attempts(roots)
    todo = [f for f in findings if not only or f["finding_id"] in only]
    kept = {f["finding_id"] for f in findings} - {f["finding_id"] for f in todo}

    status = {f["finding_id"]: classify_finding(f["finding_id"], data_dir, findings_file, repo_rel, root) for f in findings}
    by_id: dict[str, TestRecord] = {}

    def one(raw: dict[str, Any]) -> tuple[str, TestRecord]:
        fid = raw["finding_id"]
        rec = _test_one(raw, status=status[fid], env_ok=env_ok, env_reason=env_reason, attempts=found.get(fid, []), roots=roots,
                        results_root=results_root, artifact=artifact, findings_file=findings_file,
                        findings_sha=sha, data_dir=data_dir, run_agent=run_agent, fast=fast, root=root)
        if rec.not_run and rec.not_run.code == "agent_failed":
            # a re-run that produced nothing must not erase an earlier valid test of the same Finding
            try:
                prev = read_record(tdir / fid / "report.json")
            except Exception:
                prev = None
            if prev is not None and prev.status == "tested":
                prev.provenance = {**prev.provenance, "last_agent_rerun": rec.not_run.reason}
                rec = prev
        write_record(tdir / fid, rec)
        return fid, rec

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for fid, rec in ex.map(one, todo):
            by_id[fid] = rec
    for raw in findings:                      # Findings outside --only keep their earlier record
        fid = raw["finding_id"]
        if fid in kept:
            p = tdir / fid / "report.json"
            try:
                by_id[fid] = read_record(p)
            except Exception:
                rec = not_run_record(raw, *(status[fid] or ("not_attempted", "not selected by --only; no earlier record")),
                                     provenance={"findings_file": findings_file, "findings_sha256": sha,
                                                 "generated_at": now_iso()})
                write_record(tdir / fid, rec)
                by_id[fid] = rec
    recs = [by_id[f["finding_id"]] for f in findings]
    if analyze:
        _analyze_records(findings, recs, tdir, repo_rel, model, root, workers)
    return _finish(artifact, art, findings, recs, env, findings_file, sha, results_root, strict)


def _analyze_records(findings: list[dict[str, Any]], recs: list[TestRecord], tdir: Path, repo_rel: str,
                     model: Optional[str], root: Path, workers: int, force: bool = False) -> int:
    """Add an analysis (analysis.py) to every not_run record that has none; the record stays not_run."""
    from .analysis import analyze
    model = model or os.environ.get("PIPELINE_MODEL") or "x-test-2"
    base = os.environ.get("SOCLAAS_BASE_URL") or ""
    key = os.environ.get("SOCLAAS_API_KEY") or ""
    if not base or not key:
        raise InputError("analysis needs SOCLAAS_BASE_URL and SOCLAAS_API_KEY (through the relay: python -m pipeline doctor)")
    repo = root / repo_rel
    repo = repo if repo.is_dir() else None
    raw_by = {f["finding_id"]: f for f in findings}
    todo = [r for r in recs if r.status == "not_run" and (force or r.analysis is None)]

    def one(r: TestRecord) -> None:
        r.analysis = analyze(raw_by[r.finding_id], repo, model=model, base_url=base, key=key,
                             cache_dir=tdir / "analysis_cache")
        write_record(tdir / r.finding_id, r)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))
    return len(todo)


def run_analysis(artifact: str, *, findings_file: str, data_dir: str, repo_rel: str,
                 results_root: Path = DEFAULT_RESULTS_ROOT, model: Optional[str] = None, workers: int = 3,
                 force: bool = False, root: Path = PIPELINE_ROOT) -> dict[str, Any]:
    """Analyse the not_run records already on disk; no test is run."""
    findings, art, sha = _load_inputs(findings_file, data_dir, root)
    tdir = results_root / "tests" / artifact
    recs = [read_record(tdir / f["finding_id"] / "report.json") for f in findings]
    n = _analyze_records(findings, recs, tdir, repo_rel, model, root, workers, force)
    env = json.loads((tdir / "ENV.json").read_text()) if (tdir / "ENV.json").exists() else None
    out = _finish(artifact, art, findings, recs, env, findings_file, sha, results_root, False)
    out["analysed"] = n
    return out


def run_report(artifact: str, *, findings_file: str, data_dir: str, results_root: Path = DEFAULT_RESULTS_ROOT,
               strict: bool = False, root: Path = PIPELINE_ROOT) -> dict[str, Any]:
    """Regenerate LIMITATIONS.md from the records already on disk (no test is run)."""
    findings, art, sha = _load_inputs(findings_file, data_dir, root)
    tdir = results_root / "tests" / artifact
    recs: list[TestRecord] = []
    for raw in findings:
        p = tdir / raw["finding_id"] / "report.json"
        if p.exists():
            recs.append(read_record(p))
    env = json.loads((tdir / "ENV.json").read_text()) if (tdir / "ENV.json").exists() else None
    return _finish(artifact, art, findings, recs, env, findings_file, sha, results_root, strict)


def _finish(artifact: str, art: dict[str, Any], findings: list[dict[str, Any]], records: list[TestRecord],
            env: Optional[dict[str, Any]], findings_file: str, sha: str, results_root: Path, strict: bool
            ) -> dict[str, Any]:
    ids = [f["finding_id"] for f in findings]
    md = render_markdown(art, records, env, findings_file, sha)
    rdir = results_root / "report" / artifact
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "LIMITATIONS.md").write_text(md)
    problems = check_one_to_one(ids, records, md)
    # what was written must read back
    tdir = results_root / "tests" / artifact
    for fid in ids:
        try:
            read_record(tdir / fid / "report.json")
        except Exception as e:
            problems.append(f"{fid}: report.json does not read back ({type(e).__name__})")
    cs = counts(records)
    index = {"schema_version": SCHEMA, "artifact_id": artifact, "findings_file": findings_file,
             "findings_sha256": sha, "n_input": len(ids), "n_records": len(records), "counts": cs,
             "one_to_one": not problems, "problems": problems, "generated_at": now_iso(),
             "findings": [{"finding_id": r.finding_id, "status": r.status, "verdict": r.verdict, "level": r.level,
                           "not_run": r.not_run.code if r.not_run else None} for r in records]}
    (tdir / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    code = EXIT_OK
    if problems:
        code = EXIT_ONE_TO_ONE
    elif strict and any(c in ENV_CODES for c in cs["not_run_by_code"]):
        code = EXIT_STRICT
    return {"artifact": artifact, "n_input": len(ids), "counts": cs, "one_to_one": not problems, "problems": problems,
            "report": str(rdir / "LIMITATIONS.md"),
            "exit_code": code}
