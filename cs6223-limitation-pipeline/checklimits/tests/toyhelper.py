"""Builds a throw-away repository + data dir + attempt package for harness tests."""
import json
import subprocess
from pathlib import Path

CORE_WITH_EXT = '''import extlib_before
import extlib_after


def pre(n):
    return n + 1


def check(n, m):
    extlib_before.touch()
    base = pre(n)
    assert n == 1, "n must be 1"
    extlib_after.touch()
    if m > 3:
        return "big"
    return "small"


def entry(n, m):
    return check(n, m)
'''

CORE_IMPORT_TOUCH = CORE_WITH_EXT.replace("    extlib_before.touch()\n", "").replace(
    "import extlib_after\n", "import extlib_after\n\n_CFG = extlib_before.CONFIG   # touched at import time only\n")

CORE_PLAIN = '''def pre(n):
    return n + 1


def check(n, m):
    base = pre(n)
    assert n == 1, "n must be 1"
    if m > 3:
        return "big"
    return "small"


def entry(n, m):
    return check(n, m)
'''

DRIVER = '''import os, sys
from toypkg.core import entry, check


def run(inputs):
    if inputs.get("sleep"):
        import time
        time.sleep(inputs["sleep"])
    if inputs.get("leak_probe"):
        return len([k for k in os.environ if k.startswith(("SOCLAAS_", "OPENAI_")) or k.lower().endswith("_proxy")])
    if inputs.get("direct"):
        return check(inputs["n"], inputs["m"])
    out = entry(inputs["n"], inputs["m"])
    if inputs.get("probe_sensitive") and sys.monitoring.get_tool(2) is not None:
        return out + "-seen-by-tracer"   # behaves differently when a monitoring tool is registered
    return out
'''


def git(repo, *a):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                   check=True, capture_output=True)


def target_line(src):
    return next(i for i, l in enumerate(src.splitlines(), 1) if l.strip().startswith("assert n == 1"))


def build(tmp: Path, with_ext=True, form_overrides=None, driver_src=DRIVER, manifest_overrides=None,
          pos=None, neg=None, scale=None, mocks_override=None, entry_reason=None):
    repo = tmp / "repo"
    (repo / "toypkg").mkdir(parents=True)
    src = CORE_IMPORT_TOUCH if with_ext == "import" else CORE_WITH_EXT if with_ext else CORE_PLAIN
    (repo / "toypkg" / "__init__.py").write_text("")
    (repo / "toypkg" / "core.py").write_text(src)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    line = target_line(src)
    loc = f"toypkg/core.py:{line}"
    data = tmp / "data"
    data.mkdir()
    region = {"schema_version": "0.1.0", "region_id": "R1", "artifact_id": "toy", "entry_point": "toypkg/core.py::entry",
              "condition": {"expr": "n != 1", "params": ["n"], "path_prefix": []}, "outcome": "reject",
              "location": {"file": "toypkg/core.py", "line_start": line, "function": "toypkg/core.py::check",
                           "snippet": 'assert n == 1, "n must be 1"'},
              "call_chain": ["toypkg/core.py::entry", "toypkg/core.py::check"], "provenance": "manual"}
    lim = {"schema_version": "0.1.0", "limitation_id": "CL1", "artifact_id": "toy", "origin": "code",
           "condition_text": "n != 1", "effect_type": "reject", "effect_text": "assert", "region_ids": ["R1"],
           "provenance": "manual"}
    fnd = {"schema_version": "0.1.0", "finding_id": "F1", "artifact_id": "toy", "category": "undisclosed",
           "level": "L2", "limitation_ids": ["CL1"], "scope_status": "scope_edge", "effect_type": "reject",
           "summary": "n must be 1", "witness_hint": {"n": 2, "m": 1}, "confidence": "mechanical"}
    (data / "gold_regions.json").write_text(json.dumps([region]))
    (data / "gold_code_limitations.json").write_text(json.dumps([lim]))
    (data / "draft_findings.json").write_text(json.dumps([fnd]))
    att = tmp / "attempt"
    att.mkdir()
    (att / "driver.py").write_text(driver_src)
    mocks = mocks_override if mocks_override is not None else ([{"symbol": "extlib_before", "kind": "fake_module", "reason": "touched before the target", "behavior": "return_none"},
              {"symbol": "extlib_after", "kind": "fake_module", "reason": "touched after the target", "behavior": "return_none"}]
             if with_ext else [])
    form = {
        "test_id": "T1", "finding_id": "F1", "strategy": "S1" if with_ext else "S0",
        "design": {"witness_source": "witness_hint", "free_parameters": [{"name": "m", "value": 1, "why": "unused"}],
                   "positive_input": pos or {"n": 2}, "negative_input": neg or {"n": 1}, "boundary_variable": "n",
                   "condition_predicate_file": None,
                   "oracle": {"tier": "O4", "type": "exception", "spec": f"AssertionError raised at {loc}",
                              "signal_location": loc},
                   "expected": {"positive": f"AssertionError at {loc}", "negative": f"no exception at {loc}"}},
        "execution": {"entry_called": "toypkg/core.py::entry", "entry_reason": entry_reason, "call_chain_index": 0,
                      "repo_files_modified": [],
                      "mocks": mocks, "hooks": [], "replay_commands": []},
        "claims": {"target_reached": True, "decision_outcomes_seen": ["false", "true"],
                   "condition_true_on_positive": True, "condition_false_on_negative": True,
                   "positive_observed": f"AssertionError at {loc}", "negative_observed": f"no exception at {loc}"},
    }
    if scale:
        form["design"]["scale"] = scale
    for k, v in (form_overrides or {}).items():
        form[k] = v
    manifest = {"test_id": "T1", "finding_id": "F1", "artifact_id": "toy", "region_id": "R1", "repo_dir": "repo",
                "repo_commit": commit, "data_dir": "data", "timeout_s": 60}
    manifest.update(manifest_overrides or {})
    (att / "form.json").write_text(json.dumps(form))
    (att / "manifest.json").write_text(json.dumps(manifest))
    return {"root": tmp, "repo": repo, "attempt": att, "line": line, "loc": loc, "form": form, "commit": commit}
