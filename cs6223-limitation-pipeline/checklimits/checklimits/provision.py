"""`checklimits provision`: build the environment of the code under test and record whether it works (S3, B1).

Given a repository at a pinned commit it creates `scratch/venv_<name>` (the interpreter `envcheck` and the agent use
for that artifact), installs the dependencies the repository declares (torch first, from the CPU wheel index, at the
version the repository pins), runs the repository's own tests as a smoke test, and writes
`scratch/preflight/<name>/PREFLIGHT.{json,md}`: what was installed, what the tests did, and where the entry points
probably are. It never edits the repository. A failure is reported, not hidden: the Findings of such an artifact are
`not_run(env_unavailable)`, never a wrong verdict.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import time
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from .models import PROJECT_ROOT

CPU_INDEX = "https://download.pytorch.org/whl/cpu"
DEFAULT_PYTHON = "/home/somehow6/miniconda3/envs/ravel/bin/python"      # 3.11; only used to create the venv


# --------------------------------------------------------------------------- what the repository declares
def declared_requirements(repo: Path) -> dict[str, Any]:
    """{"pyproject": [...], "requirements": [...], "extras": {...}, "requires_python": str|None, "package": name}."""
    out: dict[str, Any] = {"pyproject": [], "requirements": [], "extras": {}, "requires_python": None, "package": None}
    pp = repo / "pyproject.toml"
    if pp.exists():
        try:
            proj = tomllib.loads(pp.read_text()).get("project", {})
        except tomllib.TOMLDecodeError:
            proj = {}
        out["pyproject"] = list(proj.get("dependencies", []))
        out["extras"] = {k: list(v) for k, v in proj.get("optional-dependencies", {}).items()}
        out["requires_python"] = proj.get("requires-python")
        out["package"] = proj.get("name")
    rq = repo / "requirements.txt"
    if rq.exists():
        out["requirements"] = [ln.strip() for ln in rq.read_text().splitlines()
                               if ln.strip() and not ln.strip().startswith(("#", "-"))]
    return out


def torch_spec(req: dict[str, Any]) -> Optional[str]:
    """The torch requirement to install first: an exact pin from requirements.txt if there is one, else the bare
    name if anything depends on torch, else None."""
    for line in req["requirements"] + req["pyproject"]:
        m = re.match(r"^torch\s*(==\s*[\w.+]+)?\s*(?:[<>=!~].*)?$", line.split(";")[0].strip())
        if m:
            return "torch" + (m.group(1).replace(" ", "") if m.group(1) else "")
    return None


# Known pairs the repositories do not state: when numpy is pinned below 2, the newest pyarrow (a dependency of
# `datasets`) is built for NumPy 2 and cannot be imported.
COMPAT_CONSTRAINTS = [(re.compile(r"^numpy\s*(<\s*2|<=\s*1|==\s*1)"), ["pyarrow<21"])]


def compat_pins(requirements: list[str]) -> list[str]:
    extra: list[str] = []
    for line in requirements:
        for pat, cons in COMPAT_CONSTRAINTS:
            if pat.match(line.split(";")[0].strip()):
                extra += [c for c in cons if c not in extra]
    return extra


# --------------------------------------------------------------------------- tests
def parse_pytest_summary(text: str) -> dict[str, Any]:
    """Counts from the last pytest summary line ('3 failed, 120 passed, 2 skipped in 4.2s')."""
    counts: dict[str, int] = {}
    for line in reversed(text.splitlines()):
        found = re.findall(r"(\d+) (passed|failed|skipped|error|errors|xfailed|xpassed|deselected)", line)
        if found and (" in " in line or line.startswith("=")):
            for n, k in found:
                counts["error" if k == "errors" else k] = int(n)
            break
    failed = re.findall(r"^FAILED (\S+)", text, flags=re.M) + re.findall(r"^ERROR (\S+)", text, flags=re.M)
    return {"counts": counts, "failed": failed[:30]}


# --------------------------------------------------------------------------- entry point candidates
def entry_candidates(repo: Path, package_root: str = "src", top: int = 12) -> list[dict[str, Any]]:
    """Public functions and methods of the package, ranked by how often the repository's tests and docs call them.
    A starting point for a human or for step 2, not a decision."""
    pkg = repo / package_root if (repo / package_root).is_dir() else repo
    defs: dict[str, list[str]] = {}
    for p in sorted(pkg.rglob("*.py")):
        rel = p.relative_to(pkg).as_posix()
        if rel.startswith(("tests/", "test_")) or "/tests/" in rel or "/." in rel:
            continue
        try:
            tree = ast.parse(p.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
                defs.setdefault(n.name, []).append(f"{rel}::{n.name}")
    calls: Counter[str] = Counter()
    for p in list((repo / "tests").rglob("*.py")) if (repo / "tests").is_dir() else []:
        try:
            tree = ast.parse(p.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
                if name in defs:
                    calls[name] += 1
    for p in list(repo.glob("*.md")) + list((repo / "docs").rglob("*.md") if (repo / "docs").is_dir() else []):
        for name in defs:
            calls[name] += len(re.findall(rf"\b{re.escape(name)}\(", p.read_text(errors="ignore")))
    ranked = [{"name": n, "defined_in": sorted(defs[n])[:3], "mentions": c} for n, c in calls.most_common() if c > 0][:top]
    return ranked


# --------------------------------------------------------------------------- the run
def _run(cmd: list[str], log: Path, timeout: int, cwd: Optional[Path] = None, env: Optional[dict] = None) -> tuple[int, str]:
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env)
        out, rc = (p.stdout or "") + (p.stderr or ""), p.returncode
    except subprocess.TimeoutExpired:
        out, rc = f"TIMEOUT after {timeout}s", 124
    with log.open("a") as f:
        f.write(f"$ {' '.join(cmd)}   [{time.monotonic() - t0:.0f}s, exit {rc}]\n{out[-6000:]}\n")
    return rc, out


def install_pins(vpy: Path, pins: list[str], pf: Path, log: Path, timeout: int) -> tuple[bool, list[str]]:
    """Install the repository's pinned requirements; when the batch fails, install them one by one and return the
    ones that cannot be installed on this machine (typically GPU-only wheels such as flashinfer), so that one
    unavailable package does not leave every other pin out."""
    pf.write_text("\n".join(pins) + "\n")
    rc, _ = _run([str(vpy), "-m", "pip", "install", "-q", "-r", str(pf)], log, timeout)
    if rc == 0:
        return True, []
    skipped = []
    for ln in pins:
        req = ln.split("#")[0].strip()          # a trailing comment is fine in a -r file but not as an argument
        if not req:
            continue
        rc, _ = _run([str(vpy), "-m", "pip", "install", "-q", req], log, timeout)
        if rc != 0:
            skipped.append(req)
    return False, skipped


def setup_py_requires(repo: Path) -> list[str]:
    """String requirements a setup.py lists in a literal INSTALL_REQUIRES / install_requires list (read, never executed)."""
    f = repo / "setup.py"
    if not f.is_file():
        return []
    m = re.search(r"(?:INSTALL_REQUIRES|install_requires)\s*=\s*(\[[^\]]*\])", f.read_text(errors="replace"), re.S)
    if not m:
        return []
    try:
        import ast
        v = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError):
        return []
    return [x for x in v if isinstance(x, str)]


def provision(name: str, repo: Path, commit: Optional[str] = None, python: str = DEFAULT_PYTHON,
              extras: Optional[list[str]] = None, install: bool = True, run_tests: bool = True,
              package_root: str = "src", pip_timeout: int = 1800, test_timeout: int = 900,
              out_dir: Optional[Path] = None) -> dict[str, Any]:
    out_dir = out_dir or PROJECT_ROOT / "scratch" / "preflight" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "provision.log"
    log.write_text("")
    venv = PROJECT_ROOT / "scratch" / f"venv_{name}"
    vpy = venv / "bin" / "python"
    req = declared_requirements(repo)
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    rec: dict[str, Any] = {
        "name": name, "repo": str(repo.relative_to(PROJECT_ROOT) if repo.is_relative_to(PROJECT_ROOT) else repo),
        "head": head, "pinned": commit, "pinned_matches": (not commit) or head.startswith(commit[:12]),
        "requires_python": req["requires_python"], "package": req["package"], "extras": extras or [],
        "declared": {"pyproject": req["pyproject"], "requirements_txt": len(req["requirements"])},
        "steps": [], "status": "ok", "reasons": []}
    if not rec["pinned_matches"]:
        rec["reasons"].append(f"HEAD {head[:10]} is not the pinned commit {str(commit)[:10]}")

    def step(label: str, rc: int, note: str = "") -> bool:
        note = note.replace(str(PROJECT_ROOT), "<checklimits>")
        rec["steps"].append({"step": label, "ok": rc == 0, "note": note})
        if rc != 0:
            rec["reasons"].append(f"{label} failed" + (f": {note}" if note else ""))
        return rc == 0


    if install:
        if not vpy.exists():
            rc, out = _run([python, "-m", "venv", str(venv)], log, 300)
            if not step("create venv", rc, out[-200:]):
                return _finish(rec, out_dir)
        _run([str(vpy), "-m", "pip", "install", "-q", "--upgrade", "pip"], log, 600)
        ts = torch_spec(req)
        if ts:
            rc, out = _run([str(vpy), "-m", "pip", "install", "-q", ts, "numpy<2", "--index-url", CPU_INDEX,
                            "--extra-index-url", "https://pypi.org/simple"], log, pip_timeout)
            rec["torch_spec"] = ts
            if not step(f"install {ts} (CPU wheel)", rc, out[-300:]):
                return _finish(rec, out_dir)
        pins = [ln for ln in req["requirements"] if not re.match(r"^torch\b", ln)]
        pins += compat_pins(pins)
        if pins:   # honour the versions the repository says it was evaluated with, not just the minimums
            ok, skipped = install_pins(vpy, pins, out_dir / "pins.txt", log, pip_timeout)
            rec["pins_installed"] = ok
            rec["skipped_requirements"] = skipped
            rec["steps"].append({"step": "install requirements.txt pins", "ok": ok,
                                 "note": ("not installable here, skipped: " + ", ".join(skipped)) if skipped else ""})
            if skipped:
                rec.setdefault("warnings", []).append(
                    "requirements that could not be installed on this machine and were skipped: " + ", ".join(skipped))
        target = ".[" + ",".join(extras) + "]" if extras else "."
        if not any((repo / f).is_file() for f in ("setup.py", "pyproject.toml")):
            # a research repository that is not a Python package (InfiniGen): nothing to install, run it from its directory
            rec["steps"].append({"step": "pip install -e", "ok": True,
                                 "note": "the repository has no setup.py or pyproject.toml; the checkout is used in place"})
            rec["installed"] = False
            rc, out = 0, ""
        else:
            rc, out = _run([str(vpy), "-m", "pip", "install", "-q", "-e", target], log, pip_timeout, cwd=repo)
            rec["installed"] = rc == 0
            if rc != 0 and "No module named 'torch'" in out and not ts:
                # setup.py imports torch while building (MInference): install the CPU wheel, build without isolation
                rc2, out2 = _run([str(vpy), "-m", "pip", "install", "-q", "torch", "numpy<2", "--index-url", CPU_INDEX,
                                  "--extra-index-url", "https://pypi.org/simple"], log, pip_timeout)
                rec["torch_spec"] = "torch"
                if rc2 == 0:
                    rc, out = _run([str(vpy), "-m", "pip", "install", "-q", "--no-build-isolation", "-e", target], log,
                                   pip_timeout, cwd=repo)
                    rec["installed"] = rc == 0
        if rc != 0 and rec.get("skipped_requirements"):
            # the build needs what could not be installed (a CUDA extension, for example): the checkout is used from
            # its own directory instead; envcheck and the harness decide whether the modules under test import
            rec["steps"].append({"step": f"pip install -e {target}", "ok": True,
                                 "note": "not installed (" + out[-120:].strip().replace("\n", " ") + "); the checkout is used in place"})
            rec.setdefault("warnings", []).append("the package itself was not installed; the checkout is used from its directory")
        elif rc != 0 and (repo / "setup.py").is_file():
            # the package cannot be built here (MInference: setup.py needs CUDA_HOME). Install what its setup.py
            # declares, one by one, and use the checkout in place.
            reqs = [r for r in setup_py_requires(repo) if not re.match(r"^torch\b", r)]
            ok, skipped = install_pins(vpy, reqs, out_dir / "setup_requires.txt", log, pip_timeout) if reqs else (True, [])
            rec["skipped_requirements"] = (rec.get("skipped_requirements") or []) + skipped
            rec["steps"].append({"step": f"pip install -e {target}", "ok": True,
                                 "note": "the package cannot be built on this machine; its setup.py requirements were installed"
                                         + (f" (skipped: {', '.join(skipped)})" if skipped else "") + "; the checkout is used in place"})
            rec.setdefault("warnings", []).append("the package itself was not built; the checkout is used from its directory")
        elif not step(f"pip install -e {target}", rc, out[-300:]):
            return _finish(rec, out_dir)
        # an editable install writes egg-info or build files into the repository; report if it did
        dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
        rec["repo_clean_after_install"] = not dirty.strip()
        if dirty.strip():
            rec["repo_dirty_files"] = dirty.strip().splitlines()[:10]
    if not vpy.exists():
        rec["reasons"].append(f"no interpreter at {vpy}")
        return _finish(rec, out_dir)
    rec["python"] = subprocess.run([str(vpy), "-c", "import sys; print(sys.version.split()[0])"], capture_output=True,
                                   text=True).stdout.strip()
    pk = rec["package"].replace("-", "_") if rec["package"] else None
    if pk:
        rc, out = _run([str(vpy), "-c", f"import {pk}; print({pk}.__file__)"], log, 300, cwd=out_dir)
        step(f"import {pk}", rc, out[-200:])
    rc, out = _run([str(vpy), "-m", "pip", "list", "--format=freeze"], log, 120)
    rec["packages"] = {ln.split("==")[0]: ln.split("==")[1] for ln in out.splitlines() if "==" in ln
                       and ln.split("==")[0].lower() in {"torch", "numpy", "transformers", "pytest", "tokenizers",
                                                         "datasets", "accelerate", "scipy"}}
    if run_tests and (repo / "tests").is_dir():
        env = {"PATH": "/usr/bin:/bin", "HOME": str(out_dir), "CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1",
               "PYTHONDONTWRITEBYTECODE": "1"}
        rc, out = _run([str(vpy), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--ignore=tests/gpu", "tests"], log,
                       test_timeout, cwd=repo, env=env)
        s = parse_pytest_summary(out)
        rec["tests"] = {**s, "exit": rc}
        # tests failing is information about the repository, not a reason the environment is unusable
        rec["steps"].append({"step": "repository tests", "ok": rc == 0, "note": json.dumps(s["counts"])})
        dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
        if dirty.strip():
            rec["repo_clean_after_install"] = False
            rec["repo_dirty_files"] = dirty.strip().splitlines()[:10]
    rec["entry_candidates"] = entry_candidates(repo, package_root)
    return _finish(rec, out_dir)


def _finish(rec: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    env_steps_ok = all(s["ok"] for s in rec["steps"] if s["step"] not in ("repository tests", "install requirements.txt pins"))
    rec["status"] = "ok" if env_steps_ok and not rec["reasons"] else "not_ok"
    (out_dir / "PREFLIGHT.json").write_text(json.dumps(rec, indent=1) + "\n")
    (out_dir / "PREFLIGHT.md").write_text(render(rec))
    rec["files"] = {"json": str(out_dir / "PREFLIGHT.json"), "md": str(out_dir / "PREFLIGHT.md")}
    return rec


def render(rec: dict[str, Any]) -> str:
    L = [f"# Preflight: {rec['name']}", "",
         f"- status: **{rec['status']}**" + (f" ({'; '.join(rec['reasons'])})" if rec["reasons"] else ""),
         f"- repository `{rec['repo']}` at `{rec['head'][:12]}`" + ("" if rec["pinned_matches"] else " (**not** the pinned commit)"),
         f"- python {rec.get('python', '?')} (requires {rec.get('requires_python')}), packages: {rec.get('packages', {})}",
         f"- declared dependencies: {rec['declared']['pyproject']}; requirements.txt lines: {rec['declared']['requirements_txt']}"]
    for w in rec.get("warnings", []):
        L.append(f"- warning: {w}")
    if rec.get("torch_spec"):
        L.append(f"- torch installed first as `{rec['torch_spec']}` from the CPU wheel index")
    if "repo_clean_after_install" in rec:
        L.append(f"- repository unchanged by the install and the tests: {rec['repo_clean_after_install']}"
                 + (f" ({rec.get('repo_dirty_files')})" if not rec["repo_clean_after_install"] else ""))
    L += ["", "## Steps", "", "| step | ok | note |", "|---|---|---|"]
    L += [f"| {s['step']} | {'yes' if s['ok'] else '**no**'} | {s['note'][:160].replace('|', '/')} |" for s in rec["steps"]]
    if rec.get("tests"):
        L += ["", f"## Repository tests (CPU, `tests/gpu` ignored): {rec['tests']['counts']}"]
        if rec["tests"]["failed"]:
            L += ["", "failed or errored:"] + [f"- `{t}`" for t in rec["tests"]["failed"]]
    if rec.get("entry_candidates"):
        L += ["", "## Entry point candidates (public functions the repository's tests and docs call most)", "",
              "| function | defined in | mentions |", "|---|---|---|"]
        L += [f"| `{c['name']}` | {', '.join(c['defined_in'])} | {c['mentions']} |" for c in rec["entry_candidates"]]
        L.append("\nThis ranking is a starting point. The entry points are decided by step 2 and the paper side.")
    return "\n".join(L) + "\n"
