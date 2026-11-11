"""Commands for the code agent: `task`, `init`, `lint` (PLAN.md D3).

The agent calls these through its shell tool. They only read the repository and the pilot data and
write inside the directory the agent names; they never run repository code. `lint` is a static
check of an attempt package against the test design requirements T1 to T9 (SCORECARD.md section 2)
so that cheap mistakes are found before the 30-second harness run.
"""
from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .adapter import load_task
from .models import PIPELINE_ROOT, PROJECT_ROOT, AgentForm, AttemptManifest

DEFAULT_DATA = "data/pilot_flexprefill"
_NETWORK_MODULES = {"requests", "urllib", "socket", "http", "subprocess", "httpx", "aiohttp"}


def _artifact(data_dir: Path) -> dict[str, Any]:
    return json.loads((data_dir / "artifact.json").read_text())


def _repo_dir_for(artifact: dict[str, Any]) -> str:
    return "third_party/" + artifact["repo_url"].rstrip("/").split("/")[-1].removesuffix(".git")


def _venv_python() -> Optional[str]:
    p = PROJECT_ROOT / "scratch" / "venv311" / "bin" / "python"
    return "scratch/venv311/bin/python" if p.exists() else None


# --------------------------------------------------------------------------- task
def task_text(finding_id: str, data_dir_rel: str = DEFAULT_DATA, context: int = 12) -> str:
    data_dir = PIPELINE_ROOT / data_dir_rel
    t = load_task(finding_id, data_dir)
    art = _artifact(data_dir)
    f = t.finding
    repo_rel = _repo_dir_for(art)
    L = [f"# Task: verify finding {f.finding_id}", "",
         f"**Claim to test.** {f.summary}", "",
         f"- category: {f.category}, level: {f.level}, effect type: {f.effect_type}, scope: {f.scope_status}",
         f"- upstream confidence (reported separately, not yours to change): {f.confidence}",
         f"- witness type: `{t.witness_type}`; witness_hint: `{json.dumps(f.witness_hint)}`",
         f"- inputs derived from the witness: `{json.dumps(t.inputs)}`", ""]
    for lim in t.limitations:
        L += [f"**Limitation {lim.limitation_id}.** condition: {lim.condition_text} -> effect: {lim.effect_text}", ""]
    for r in t.regions:
        loc = r.location
        L += [f"## Region {r.region_id}",
              f"- target: `{loc.file}:{loc.line_start}` in `{loc.function}`",
              f"- statement: `{loc.snippet}`",
              f"- condition (Python, over the names in the function): `{r.condition.expr}`; "
              f"path prefix (must hold to get there): {r.condition.path_prefix}",
              f"- outcome: `{r.outcome}` ({r.outcome_detail})",
              f"- call chain (entry first): {r.call_chain}", ""]
        src = PIPELINE_ROOT / repo_rel / loc.file
        if src.exists():
            lines = src.read_text().splitlines()
            a, b = max(1, loc.line_start - context), min(len(lines), loc.line_start + context)
            L += [f"Source around the target ({repo_rel}/{loc.file}, read-only):", "```python"]
            L += [f"{i:5d}{'>' if i == loc.line_start else ' '} {lines[i - 1]}" for i in range(a, b + 1)]
            L += ["```", ""]
    py = _venv_python()
    L += ["## Environment",
          f"- repository (pinned, read-only): `{repo_rel}` at `{art['commit']}`",
          f"- python for the code under test: `{py or 'harness interpreter'}` "
          "(torch 2.4.0 CPU, triton 3.0.0, transformers 4.44.0: the versions the repository pins; no GPU)",
          "- stand-ins for GPU-only calls are allowed only as declared mocks (see INSTRUCTIONS.md)", "",
          "## Next",
          f"`init {f.finding_id} --out <dir>` creates the attempt package skeleton; then read INSTRUCTIONS.md."]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- init
def init_attempt(finding_id: str, out: Path, data_dir_rel: str = DEFAULT_DATA, test_id: Optional[str] = None,
                 python: Optional[str] = None) -> list[Path]:
    data_dir = PIPELINE_ROOT / data_dir_rel
    t = load_task(finding_id, data_dir)
    if not t.regions:
        raise SystemExit(f"{finding_id} has no linked Region: nothing to test")
    r = t.regions[0]
    art = _artifact(data_dir)
    loc = f"{r.location.file}:{r.location.line_start}"
    out.mkdir(parents=True, exist_ok=True)
    manifest = AttemptManifest(
        test_id=test_id or f"A-{finding_id}", finding_id=finding_id, artifact_id=art["artifact_id"],
        region_id=r.region_id, repo_dir=_repo_dir_for(art), repo_commit=art["commit"], data_dir=data_dir_rel,
        python=python or _venv_python())
    witness = dict(t.inputs[0]) if t.witness_type == "input_value" else {}
    reject = r.outcome == "reject"
    form = {
        "test_id": manifest.test_id, "finding_id": finding_id, "strategy": "S0",
        "design": {
            "witness_source": "witness_hint",
            "free_parameters": [],
            "positive_input": witness,
            "negative_input": dict(witness),
            "boundary_variable": "TODO",
            "scale": None, "condition_predicate_file": None,
            "oracle": {"tier": "O4" if reject else "O3", "type": "exception" if reject else "path_hook",
                       "spec": f"TODO: <ExceptionType> raised at {loc}", "signal_location": loc},
            "expected": {"positive": f"TODO: <ExceptionType> at {loc}", "negative": f"no exception at {loc}"},
        },
        "execution": {"entry_called": r.call_chain[0] if r.call_chain else r.entry_point, "entry_reason": None,
                      "call_chain_index": 0, "repo_files_modified": [], "mocks": [], "hooks": [],
                      "replay_commands": ["python -m checklimits run --attempt <this directory>"]},
        "claims": {"target_reached": False, "decision_outcomes_seen": [], "condition_true_on_positive": None,
                   "condition_false_on_negative": None, "positive_observed": "TODO", "negative_observed": "TODO"},
        "evidence": {},
    }
    (out / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
    (out / "form.json").write_text(json.dumps(form, indent=2) + "\n")
    (out / "driver.py").write_text(
        '"""Driver: call the official entry with the inputs the harness passes in.\n\n'
        "Rules: import the code under test at module level (the harness loads this file before it starts\n"
        "tracing); build tensors / objects from `inputs` only; set seeds; CPU only; no assertions of your own\n"
        "(the harness decides from the trace and the exception); do not catch the exception you are\n"
        "looking for; do not write into the repository.\n"
        '"""\n\n\ndef run(inputs):\n    raise NotImplementedError("call the entry point with values from `inputs`")\n')
    return [out / "manifest.json", out / "form.json", out / "driver.py"]


# --------------------------------------------------------------------------- lint
@dataclass
class Issue:
    level: str   # error | warn
    code: str
    message: str


def _inputs_keys(driver_src: str) -> tuple[set[str], set[str]]:
    """Names read from the `inputs` argument: (required: inputs["x"] / inputs.get("x"),
    defaulted: inputs.get("x", default)). A defaulted key is a free parameter hidden in the driver."""
    required: set[str] = set()
    defaulted: set[str] = set()
    for n in ast.walk(ast.parse(driver_src)):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == "inputs" \
                and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
            required.add(n.slice.value)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "inputs" and n.args \
                and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            (defaulted if len(n.args) > 1 else required).add(n.args[0].value)
    return required, defaulted


def lint_attempt(attempt: Path, pipeline_root: Path = PIPELINE_ROOT) -> list[Issue]:
    issues: list[Issue] = []
    err = lambda c, m: issues.append(Issue("error", c, m))
    warn = lambda c, m: issues.append(Issue("warn", c, m))
    try:
        manifest = AttemptManifest.model_validate_json((attempt / "manifest.json").read_text())
    except Exception as e:
        return [Issue("error", "L001", f"manifest.json: {str(e)[:300]}")]
    try:
        form = AgentForm.model_validate_json((attempt / manifest.form).read_text())
    except Exception as e:
        return [Issue("error", "L002", f"{manifest.form}: {str(e)[:400]}")]
    if (form.test_id, form.finding_id) != (manifest.test_id, manifest.finding_id):
        err("L003", "form.json and manifest.json disagree on test_id / finding_id")
    try:
        task = load_task(manifest.finding_id, pipeline_root / manifest.data_dir)
        region = task.region(manifest.region_id)
    except Exception as e:
        return issues + [Issue("error", "L004", f"finding/region lookup failed: {e}")]
    loc = f"{region.location.file}:{region.location.line_start}"
    repo = pipeline_root / manifest.repo_dir
    if not (repo / region.location.file).exists():
        err("L005", f"repository file {repo / region.location.file} not found")
    else:
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        if head != manifest.repo_commit:
            err("L005", f"repository HEAD {head[:8]} is not the pinned commit {manifest.repo_commit[:8]}")
    d = form.design
    drv = attempt / manifest.driver
    keys: set[str] = set()
    defaulted: set[str] = set()
    if not drv.exists():
        err("L006", f"{manifest.driver} not found")
    else:
        try:
            src = drv.read_text()
            tree = ast.parse(src)
            if not any(isinstance(n, ast.FunctionDef) and n.name == manifest.driver_fn for n in tree.body):
                err("L006", f"{manifest.driver} defines no top-level function {manifest.driver_fn}(inputs)")
            if "NotImplementedError" in src and "call the entry point" in src:
                err("L006", "driver.py is still the init stub")
            if any(isinstance(n, ast.Assert) for n in ast.walk(tree)):
                warn("L007", "driver contains an assert: the harness judges from the trace; asserts in the driver can hide the effect (T7)")
            imports = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
                      {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
            if imports & _NETWORK_MODULES:
                warn("L023", f"driver imports {sorted(imports & _NETWORK_MODULES)}: tests must be offline (T6)")
            if "cuda" in src.lower() and "is_available" not in src:
                warn("L024", "driver mentions cuda: tests run on CPU only (T6)")
            if ("'w'" in src or '"w"' in src) and "open(" in src:
                warn("L022", "driver may write files; it must not write into the repository (T5)")
            keys, defaulted = _inputs_keys(src)
        except SyntaxError as e:
            err("L006", f"driver.py does not parse: {e}")
    # T1 / T7: oracle
    o = d.oracle
    if o.tier == "O4" and o.signal_location != loc:
        err("L008", f"oracle tier O4 needs signal_location == Region.location ({loc}); got {o.signal_location!r}")
    if "TODO" in o.spec or "TODO" in d.expected.positive or "TODO" in form.claims.positive_observed:
        err("L008", "form.json still contains TODO placeholders")
    # T2: control pair
    diff = sorted(k for k in set(d.positive_input) | set(d.negative_input) if d.positive_input.get(k) != d.negative_input.get(k))
    if not diff:
        err("L009", "positive_input and negative_input are identical (T2: they must differ in exactly one factor)")
    elif len(diff) > 1:
        err("L009", f"positive and negative differ in {diff}; T2 requires exactly one factor")
    if diff and d.boundary_variable not in diff:
        err("L010", f"boundary_variable {d.boundary_variable!r} is not the differing factor {diff}")
    # T3: provenance and free parameters
    hint = task.finding.witness_hint or {}
    sc = d.scale
    if task.witness_type == "input_value":
        for k, hv in hint.items():
            got = d.positive_input.get(k)
            scaled_ok = sc and k in sc.scaled and isinstance(hv, (int, float)) and got == int(hv * sc.factor)
            if got != hv and not scaled_ok:
                (warn if got is not None else err)(
                    "L011", f"witness_hint[{k!r}]={hv!r} but positive_input[{k!r}]={got!r}: use the witness value, "
                            "or declare a scale (design.scale)")
    declared = set(d.positive_input) | set(d.negative_input) | {fp.name for fp in d.free_parameters}
    for k in sorted(keys - declared):
        err("L012", f"driver reads inputs[{k!r}] but it is neither in positive_input/negative_input nor in "
                    "free_parameters (T3: disclose every free parameter with a reason)")
    for k in sorted(defaulted - declared):
        warn("L012", f"driver defaults inputs[{k!r}] itself: that is a free parameter hidden in the driver; "
                     "list it in free_parameters with a reason, or pass it in the inputs")
    for fp in d.free_parameters:
        if len(fp.why.strip()) < 8:
            warn("L012", f"free parameter {fp.name!r} has no real justification")
    # T4: entry
    if form.execution.entry_called not in region.call_chain:
        err("L016", f"entry_called {form.execution.entry_called!r} is not in Region.call_chain {region.call_chain}")
    elif region.call_chain.index(form.execution.entry_called) > 0 and not form.execution.entry_reason:
        err("L016", "a function deeper than call_chain[0] is called: record execution.entry_reason (T4)")
    # T5: no repository edits; mocks
    if form.execution.repo_files_modified:
        err("L018", "repo_files_modified must be empty: do not edit the repository (T5)")
    if form.strategy == "S0" and form.execution.mocks:
        warn("L017", "strategy S0 means no mocks; you declared some: use S1")
    for m in form.execution.mocks:
        if m.behavior == "sim":
            if not m.impl or "::" not in m.impl:
                err("L013", f"mock {m.symbol}: behavior 'sim' needs impl 'file.py::function'")
            else:
                f, fn = m.impl.split("::", 1)
                if not (attempt / f).exists():
                    err("L013", f"mock {m.symbol}: {f} not found in the attempt directory")
                else:
                    try:
                        if not any(isinstance(n, ast.FunctionDef) and n.name == fn for n in ast.parse((attempt / f).read_text()).body):
                            err("L013", f"mock {m.symbol}: {f} defines no function {fn}")
                    except SyntaxError as e:
                        err("L013", f"{f} does not parse: {e}")
            if m.sim_class == "stub":
                warn("L014", f"mock {m.symbol}: behavior 'sim' with sim_class 'stub'; say whether it is repo_reference or independent_native")
        elif m.sim_class != "stub":
            warn("L014", f"mock {m.symbol}: sim_class {m.sim_class!r} only makes sense with behavior 'sim'")
        if m.kind != "env_var" and len(m.reason.strip()) < 8:
            warn("L014", f"mock {m.symbol}: give a real reason")
    if sc is not None:
        if not sc.scaled:
            err("L015", "design.scale.scaled is empty")
        if len(sc.invariance_argument.strip()) < 20:
            warn("L015", "design.scale.invariance_argument is too short to be an argument")
    if d.condition_predicate_file and not (attempt / d.condition_predicate_file).exists():
        err("L019", f"condition_predicate_file {d.condition_predicate_file} not found")
    if not form.execution.replay_commands:
        warn("L020", "replay_commands is empty (T8)")
    return issues


def format_issues(issues: list[Issue]) -> str:
    if not issues:
        return "lint: no issues\n"
    return "".join(f"{i.level.upper():5s} {i.code} {i.message}\n" for i in issues) + \
        f"lint: {sum(i.level == 'error' for i in issues)} error(s), {sum(i.level == 'warn' for i in issues)} warning(s)\n"
