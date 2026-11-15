"""Run the whole limitation pipeline for one artifact: everything that is missing, in order.

Stages (each is skipped when its output exists, so a stopped run resumes and the five development papers reuse
their results; delete a stage's output to redo it):

  fetch     third_party/<Repo> at the pinned commit; third_party/papers/<id>.pdf (from --pdf)
  code      step 2, final route B (docs/06_two_routes.md): B-sweep and B-agent (each starts from route A),
            relevance filter on both, merge -> Limitations           out/routes_*/<id>/, out/pipeline_ps/<id>/
  paper     steps 1 + 3a, Zhaopeng (paperside/): run_complete_corpus.py then finalize_handoff.py
                                                                       paperside/handoffs/paper-side-v1/<id>/
  verify3b  step 3b with the paper side                              out/pipeline_ps/<id>/3b.json
  step4     dedup, classify, priority, witness_hint                  results/step4/<id>/limitations_for_tests.json
  doc       hand-off page for the test side                          results/step4/<id>/HANDOFF.md
            (step4 and doc always rerun: cheap, LLM answers cached; they also refresh the all-paper files
             results/step4/limitations_for_tests.json and HANDOFF.md)

`code`, `paper` and `verify3b` call models and cost money; `paper` only runs with --run-paper-side because
Zhaopeng's pipeline is the most expensive part (Pi coding agent per mechanism) and writes into paperside/.

After `run`, `python -m pipeline test <id>` runs the test side (Shanghao, checklimits/; contract in
checklimits/CONTRACT_TEST_REPORT.md):

  test      one report.json per Finding, LIMITATIONS.md          results/tests/<id>/, results/report/<id>/LIMITATIONS.md

It is a separate command, not a stage of `run`: with --run-agent it runs a code agent per Finding (5 to 15 minutes
each). `status` shows it as done, stale (made from an older step 4 file) or todo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
PAPERSIDE = ROOT / "paperside"
HANDOFFS = PAPERSIDE / "handoffs/paper-side-v1"
PINS = PAPERSIDE / "workstreams/zhaopeng/team-reviewed.json"
PACKAGE_ROOTS = {"infinigen": ["speedup/infinigen", "speedup/flexgen"]}  # same as scripts/run_routes.py
STAGES = ["fetch", "code", "paper", "verify3b", "step4", "doc"]
CHECKLIMITS = ROOT / "checklimits"
TEST_CONTRACT = "checklimits-test-report/1"
# exit codes of `python -m checklimits test` (CONTRACT_TEST_REPORT.md section 6)
TEST_EXIT = {0: "report complete", 1: "unhandled error in checklimits", 2: "input error (artifact or step 4 file)",
             3: "report incomplete: Findings and records do not match one to one",
             4: "report complete, but some Findings were not run for environment, agent or harness reasons (--strict)"}


class StageError(RuntimeError):
    pass


# --------------------------------------------------------------------------- paths
def artifact_json(aid: str) -> Path:
    for p in sorted((ROOT / "data").glob("*/artifact.json")):
        if json.loads(p.read_text())["artifact_id"] == aid:
            return p
    raise StageError(f"no data/*/artifact.json with artifact_id {aid!r}; create one with `python -m pipeline init`")


class Paths:
    def __init__(self, aid: str):
        self.aid = aid
        self.art_json = artifact_json(aid)
        self.art = json.loads(self.art_json.read_text())
        self.repo = ROOT / "third_party" / self.art["repo_url"].rstrip("/").split("/")[-1]
        self.pdf = ROOT / "third_party/papers" / f"{aid}.pdf"
        r = f"{aid}/%s_run1.json"
        self.sweep, self.agent = ROOT / "out/routes_sweep" / (r % "sweep"), ROOT / "out/routes_agent" / (r % "agent")
        self.fsweep, self.fagent = ROOT / "out/routes_filtered" / (r % "sweep"), ROOT / "out/routes_filtered" / (r % "agent")
        self.merged = ROOT / "out/routes_merged" / (r % "merged")
        self.code_dir = ROOT / "out/pipeline_ps" / aid
        self.lims = self.code_dir / "limitations.json"
        self.lims_for_paperside = ROOT / "results/pipeline" / aid / "limitations.json"  # finalize_handoff reads it
        self.handoff = HANDOFFS / aid
        self.verify3b = self.code_dir / "3b.json"
        self.step4 = ROOT / "results/step4" / aid / "limitations_for_tests.json"
        self.doc = ROOT / "results/step4" / aid / "HANDOFF.md"
        self.results = ROOT / "results"  # --results-root of the test side
        self.test_index = self.results / "tests" / aid / "index.json"
        self.report = self.results / "report" / aid / "LIMITATIONS.md"
        cfg = self.art_json.parent / "pipeline.json"
        self.config = json.loads(cfg.read_text()) if cfg.is_file() else {}

    def package_roots(self, extra: list[str]) -> list[str]:
        roots = extra or self.config.get("package_roots") or PACKAGE_ROOTS.get(self.aid, [])
        return [x for r in roots for x in ("--package-root", r)]

    def entries(self) -> list[str]:
        if not self.art.get("entry_points"):
            raise StageError(f"{self.art_json.relative_to(ROOT)} has no entry_points; step 2 needs at least one")
        return [x for e in self.art["entry_points"] for x in ("--entry", e)]


# --------------------------------------------------------------------------- helpers
def env() -> dict:
    """Process environment plus .env (API key); values are never printed."""
    e = dict(os.environ)
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                k = k.strip().removeprefix("export").strip()
                e.setdefault(k, v.strip().strip('"').strip("'"))
    e["PAPERPROBE_TEAM_REPO"] = str(ROOT)
    return e


def sh(cmd: list, cwd: Path = ROOT, log: Optional[Path] = None) -> None:
    shown = " ".join(str(c) for c in cmd)
    print(f"  $ {shown}", flush=True)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as f:
            p = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env(), stdout=f, stderr=subprocess.STDOUT)
    else:
        p = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env())
    if p.returncode != 0:
        raise StageError(f"command failed ({p.returncode}): {shown}" + (f"; log: {log}" if log else ""))


def cli(*args) -> list:
    return [sys.executable, "-m", "codeside.cli", *args]


def git_head(repo: Path) -> Optional[str]:
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- stage checks
def done(stage: str, P: Paths) -> bool:
    return {
        "fetch": git_head(P.repo) == P.art["commit"] and P.pdf.is_file(),
        "code": P.lims.is_file(),
        "paper": (P.handoff / "paper_side.json").is_file() and (P.handoff / "binding_provenance.json").is_file(),
        "verify3b": P.verify3b.is_file(),
        "step4": P.step4.is_file(),
        "doc": P.doc.is_file(),
    }[stage]


def paperside_problems(P: Paths) -> list[str]:
    """What Zhaopeng's pipeline needs before it can run on this artifact."""
    out = []
    probe = subprocess.run([sys.executable, "-c", "import paperprobe, pypdf, fitz"], capture_output=True)
    if probe.returncode != 0:
        out.append("paper-side Python packages missing: run `python -m pipeline setup-paperside`")
    if not (PAPERSIDE / "tools/pi-mechanism-agent/node_modules").is_dir():
        out.append("Pi agent node_modules missing: run `python -m pipeline setup-paperside`")
    if shutil.which("node") is None:
        out.append("node (>=20) not on PATH")
    if not env().get("SOCLAAS_API_KEY"):
        out.append("SOCLAAS_API_KEY not set (environment or .env)")
    return out


# --------------------------------------------------------------------------- stages
def stage_fetch(P: Paths, a) -> None:
    if git_head(P.repo) != P.art["commit"]:
        if not P.repo.is_dir():
            sh(["git", "clone", "-q", P.art["repo_url"], P.repo])
        subprocess.run(["git", "-C", str(P.repo), "fetch", "-q", "--depth", "1", "origin", P.art["commit"]])
        sh(["git", "-C", P.repo, "checkout", "-q", P.art["commit"]])
    if not P.pdf.is_file():
        if not a.pdf:
            raise StageError(f"{P.pdf.relative_to(ROOT)} missing: pass --pdf <path to the paper PDF>")
        P.pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(a.pdf, P.pdf)
    print(f"  repo {P.repo.relative_to(ROOT)} @ {P.art['commit'][:10]}, pdf sha256 {sha256(P.pdf)[:16]}")


def stage_code(P: Paths, a) -> None:
    repo = str(P.repo.relative_to(ROOT))
    base = ["--repo", repo, *P.entries(), "--artifact", P.aid, "--paper", P.art["paper_title"],
            *P.package_roots(a.package_root), "--model", a.model]
    log = P.code_dir / "pipeline.log"
    if not P.sweep.is_file():
        sh(cli("extract-sweep", *base, "--out", P.sweep), log=log)
    if not P.agent.is_file():
        sh(cli("extract-agent", *base, "--out", P.agent), log=log)
    for src, dst in ((P.sweep, P.fsweep), (P.agent, P.fagent)):
        if not dst.is_file():
            sh(cli("filter", "--regions", src, "--repo", repo, *P.entries(), "--paper", P.art["paper_title"],
                   "--model", a.model, "--out", dst), log=log)
    if not P.merged.is_file():
        sh(cli("merge", P.fsweep, P.fagent, "--repo", repo, "--out", P.merged), log=log)
    P.code_dir.mkdir(parents=True, exist_ok=True)
    sh(cli("to-limitations", "--regions", P.merged, "--out", P.lims, "--include-variants"), log=log)
    if not P.lims_for_paperside.is_file():
        P.lims_for_paperside.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(P.lims, P.lims_for_paperside)
    print(f"  {len(json.loads(P.lims.read_text()))} code-side limitations")


def stage_paper(P: Paths, a) -> None:
    if not a.run_paper_side:
        raise StageError(
            f"no paper-side hand-off at {P.handoff.relative_to(ROOT)}. Zhaopeng's pipeline is expensive (one Pi coding "
            "agent per mechanism); rerun with --run-paper-side to start it, or put a finished hand-off package there.")
    problems = paperside_problems(P)
    if problems:
        raise StageError("paper side cannot start:\n    - " + "\n    - ".join(problems))
    # pin: his prepare_paper refuses to run unless the paper and commit are pinned in team-reviewed.json
    pins = json.loads(PINS.read_text())
    pin = pins.get(P.aid)
    if pin is None:
        pins[P.aid] = {"commit": P.art["commit"], "pdf_sha256": sha256(P.pdf)}
        PINS.write_text(json.dumps(pins, indent=2, ensure_ascii=False) + "\n")
        print(f"  pinned {P.aid} in {PINS.relative_to(ROOT)}")
    elif pin["commit"] != P.art["commit"] or pin["pdf_sha256"] != sha256(P.pdf):
        raise StageError(f"{PINS.relative_to(ROOT)} pins {P.aid} to another commit or PDF; resolve by hand")
    # his own clean checkout of the target repo
    team_repo = PAPERSIDE / "data/repos" / f"team-{P.aid}"
    if git_head(team_repo) != P.art["commit"]:
        if team_repo.exists():
            raise StageError(f"{team_repo.relative_to(ROOT)} exists at another commit; resolve by hand")
        team_repo.parent.mkdir(parents=True, exist_ok=True)
        sh(["git", "clone", "-q", P.repo, team_repo])
        sh(["git", "-C", team_repo, "checkout", "-q", "--detach", P.art["commit"]])
    log = ROOT / "out/paperside_logs" / f"{P.aid}.log"
    sh([sys.executable, "scripts/run_complete_corpus.py", "--papers", P.aid], cwd=PAPERSIDE, log=log)
    state_file = PAPERSIDE / "runs/team-complete-v1" / P.aid / "state.json"
    state = json.loads(state_file.read_text()).get("state") if state_file.is_file() else "no state.json"
    if not (P.handoff / "paper_side.json").is_file():
        raise StageError(f"paper side did not produce a hand-off (state: {state}); see {log.relative_to(ROOT)} and "
                         f"paperside/runs/team-complete-v1/{P.aid}/")
    sh([sys.executable, "scripts/finalize_handoff.py", P.handoff.relative_to(PAPERSIDE)], cwd=PAPERSIDE, log=log)
    print(f"  paper side state: {state}")


def stage_verify3b(P: Paths, a) -> None:
    sh([sys.executable, "scripts/run_pipeline.py", "--only", P.aid, "--out-dir", "out/pipeline_ps",
        "--paper-side-dir", str(HANDOFFS.relative_to(ROOT)), "--model", a.model, "--parallel", "1", "--workers", "3"])
    if not P.verify3b.is_file():
        raise StageError(f"3b produced no {P.verify3b.relative_to(ROOT)}; see the [FAIL] line above")


def stage_step4(P: Paths, a) -> None:
    sh([sys.executable, "scripts/run_step4.py", "--only", P.aid, "--model", a.model])


def stage_doc(P: Paths, a) -> None:
    sh([sys.executable, "scripts/make_handoff_doc.py", "--src", P.step4.relative_to(ROOT), "--out", P.doc.relative_to(ROOT)])
    sh([sys.executable, "scripts/make_handoff_doc.py"])


RUN = {"fetch": stage_fetch, "code": stage_code, "paper": stage_paper, "verify3b": stage_verify3b,
       "step4": stage_step4, "doc": stage_doc}
ALWAYS = {"step4", "doc"}


def run(aid: str, a) -> Path:
    """Run every missing stage for `aid`; return the path of its limitations_for_tests.json."""
    P = Paths(aid)
    last = STAGES.index(a.until) if a.until else len(STAGES) - 1
    for stage in STAGES[: last + 1]:
        if done(stage, P) and stage not in ALWAYS:
            print(f"[done] {stage}")
            continue
        print(f"[run ] {stage}", flush=True)
        RUN[stage](P, a)
    if last == len(STAGES) - 1:
        print(f"\nall limitations of {aid}: {P.step4.relative_to(ROOT)}\nexplained in:            {P.doc.relative_to(ROOT)}"
              f"\nall papers together:     results/step4/limitations_for_tests.json, results/step4/HANDOFF.md")
    return P.step4


def status(aid: str) -> None:
    P = Paths(aid)
    print(f"{aid}  ({P.art_json.relative_to(ROOT)}, {P.art['repo_url']} @ {P.art['commit'][:10]})")
    for s in STAGES:
        print(f"  {'done' if done(s, P) else 'todo'}  {s}")
    state, detail = test_state(P)
    print(f"  {state:<5} test   ({detail})")
    if not done("paper", P):
        problems = paperside_problems(P)
        print("  paper side can start with --run-paper-side" if not problems else
              "  paper side not ready:\n    - " + "\n    - ".join(problems))


# --------------------------------------------------------------------------- test (W6)
def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def test_state(P: Paths) -> tuple[str, str]:
    """('done' | 'stale' | 'todo', detail) of the test side for one artifact."""
    if not (P.test_index.is_file() and P.report.is_file()):
        return "todo", "no report yet: python -m pipeline test " + P.aid
    try:
        idx = json.loads(P.test_index.read_text())
    except (OSError, ValueError):
        return "todo", f"{_rel(P.test_index)} is unreadable"
    c = idx.get("counts") or {}
    by_code = c.get("not_run_by_code") or {}
    detail = (f"{idx.get('n_records')}/{idx.get('n_input')} Findings in {_rel(P.report)}; "
              f"tested {c.get('tested', '?')}, not run {sum(by_code.values()) if by_code else c.get('not_run', '?')}")
    if not idx.get("one_to_one"):
        return "todo", "last report is incomplete (one_to_one false); rerun"
    if not P.step4.is_file() or idx.get("findings_sha256") != sha256(P.step4):
        return "stale", detail + "; made from an older step 4 file, rerun `pipeline test`"
    return "done", detail


def last_json(text: str) -> Optional[dict]:
    """The last JSON object printed on stdout (the contract's summary; it may span several lines)."""
    lines = text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("{"):
            try:
                out = json.loads("\n".join(lines[i:]))
            except ValueError:
                continue
            return out if isinstance(out, dict) else None
    return None


def test_cmd(aid: str, a) -> list:
    cmd = [sys.executable, "-m", "checklimits", "test", aid, "--results-root", str(ROOT / "results"),
           "--workers", str(a.workers)]
    for flag in ("run_agent", "fast", "strict", "skip_envcheck"):
        if getattr(a, flag, False):
            cmd.append("--" + flag.replace("_", "-"))
    for fid in a.only or []:
        cmd += ["--only", fid]
    if a.python:
        cmd += ["--python", a.python]
    return cmd


def test(aid: str, a) -> dict:
    """Run the test side on the step 4 output of `aid` (contract checklimits-test-report/1) and check its result."""
    P = Paths(aid)
    if not P.step4.is_file():
        raise StageError(f"no step 4 output {_rel(P.step4)}; run `python -m pipeline run {aid}` first")
    if not (CHECKLIMITS / "checklimits" / "__main__.py").is_file():
        raise StageError(f"test side not found at {_rel(CHECKLIMITS)}")
    cmd = test_cmd(aid, a)
    print(f"[run ] test\n  $ (cd {_rel(CHECKLIMITS)}) {' '.join(cmd)}", flush=True)
    # cwd must be checklimits/: from the pipeline root `-m checklimits` resolves to the directory, not the package
    p = subprocess.run(cmd, cwd=CHECKLIMITS, env=env(), stdout=subprocess.PIPE, text=True)
    out = last_json(p.stdout) or {}
    if p.stdout:
        log = P.results / "tests" / aid / "pipeline_test.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(p.stdout)
    code = p.returncode
    reason = TEST_EXIT.get(code, f"unexpected exit code {code}")
    if code not in (0, 4):
        raise StageError(f"test: {reason}" + (f": {out.get('error') or out.get('problems')}" if out else ""))
    if not out:
        raise StageError("test: no summary JSON on stdout (contract section 6)")
    counts = out.get("counts") or {}
    print(f"  {reason}; {out.get('n_input')} Findings, one_to_one={out.get('one_to_one')}")
    print(f"  counts: {json.dumps(counts)}")
    print(f"  report: {_rel(P.report)}")
    if code == 4:
        raise StageError(f"test: {reason}; the report is written, see {_rel(P.report)}")
    return out


# --------------------------------------------------------------------------- init / setup
def init(a) -> None:
    from schema.models import Artifact
    dest = ROOT / "data" / a.id / "artifact.json"
    if dest.exists():
        raise StageError(f"{dest.relative_to(ROOT)} exists; edit it by hand")
    art = Artifact(artifact_id=a.id, paper_title=a.title, paper_url=a.paper_url, venue=a.venue, repo_url=a.repo_url,
                   commit=a.commit, domain=a.domain, entry_points=a.entry, execution_env=a.env or [], notes=a.notes)
    dest.parent.mkdir(parents=True)
    dest.write_text(json.dumps(art.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n")
    if a.package_root:
        (dest.parent / "pipeline.json").write_text(json.dumps({"package_roots": a.package_root}, indent=2) + "\n")
    print(f"wrote {dest.relative_to(ROOT)}; next: python -m pipeline run {a.id} --pdf <paper.pdf>")


def setup_paperside(_a) -> None:
    has_pip = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True).returncode == 0
    if has_pip:
        sh([sys.executable, "-m", "pip", "install", "-q", "-e", f"{PAPERSIDE}[team,vision]"])
    elif shutil.which("uv"):  # a uv-made venv has no pip
        sh(["uv", "pip", "install", "-q", "--python", sys.executable, "-e", f"{PAPERSIDE}[team,vision]"])
    else:
        raise StageError("neither pip nor uv available for this Python")
    sh(["npm", "ci", "--prefix", PAPERSIDE / "tools/pi-mechanism-agent", "--ignore-scripts", "--no-audit", "--no-fund"])


def main(argv: Optional[list] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run every missing stage; outputs all limitations of the artifact")
    r.add_argument("artifact_id")
    r.add_argument("--pdf", help="paper PDF, copied to third_party/papers/<id>.pdf")
    r.add_argument("--model", default="x-test-2")
    r.add_argument("--run-paper-side", action="store_true", help="allow Zhaopeng's (expensive) paper-side pipeline")
    r.add_argument("--package-root", action="append", default=[], help="import root inside the repo; repeatable")
    r.add_argument("--until", choices=STAGES, help="stop after this stage")
    s = sub.add_parser("status", help="show which stages are done")
    s.add_argument("artifact_id", nargs="*")
    i = sub.add_parser("init", help="write data/<id>/artifact.json for a new paper")
    i.add_argument("--id", required=True)
    i.add_argument("--title", required=True)
    i.add_argument("--paper-url", required=True)
    i.add_argument("--repo-url", required=True)
    i.add_argument("--commit", required=True, help="full commit hash to pin")
    i.add_argument("--domain", required=True)
    i.add_argument("--entry", action="append", required=True, help="file.py::function implementing the mechanism")
    i.add_argument("--venue")
    i.add_argument("--env", action="append", choices=["cpu", "cpu_mock", "simulator", "gpu"])
    i.add_argument("--notes")
    i.add_argument("--package-root", action="append")
    t = sub.add_parser("test", help="test side: one report per Finding and LIMITATIONS.md (checklimits test)")
    t.add_argument("artifact_id")
    t.add_argument("--run-agent", action="store_true",
                   help="run the code agent for judgeable Findings without a test package (5 to 15 min each)")
    t.add_argument("--only", action="append", help="test only this finding id (repeatable); the report keeps all")
    t.add_argument("--workers", type=int, default=3)
    t.add_argument("--fast", action="store_true", help="fewer repeats and mutants (smoke runs only; lower levels)")
    t.add_argument("--strict", action="store_true", help="fail when Findings are not run for env/agent/harness reasons")
    t.add_argument("--skip-envcheck", action="store_true")
    t.add_argument("--python", help="interpreter of the code under test (default: the test side's per-artifact venv)")
    sub.add_parser("setup-paperside", help="pip install paperside[team,vision] and npm ci for the Pi agent")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "run":
            run(a.artifact_id, a)
        elif a.cmd == "status":
            ids = a.artifact_id or [json.loads(p.read_text())["artifact_id"] for p in sorted((ROOT / "data").glob("*/artifact.json"))]
            for aid in ids:
                status(aid)
        elif a.cmd == "test":
            test(a.artifact_id, a)
        elif a.cmd == "init":
            init(a)
        else:
            setup_paperside(a)
    except StageError as e:
        sys.exit(f"stopped: {e}")
