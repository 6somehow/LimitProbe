"""task / init / lint, oracle-lock history, extra negatives, and the agent runtime's sandbox and budgets."""
import json
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from checklimits import agent_cli, agent_loop, confidence, harness
from checklimits.harness import RunOptions, lock_is_extension, register_oracle
from checklimits.models import PIPELINE_ROOT
from toyhelper import build

FAST = RunOptions.fast()
PILOT_OK = (PIPELINE_ROOT / "third_party" / "FlexPrefill" / "flex_prefill").exists()


def lint(b):
    return agent_cli.lint_attempt(b["attempt"], b["root"])


def codes(issues, level=None):
    return [i.code for i in issues if level is None or i.level == level]


def edit_form(b, fn):
    p = b["attempt"] / "form.json"
    d = json.loads(p.read_text())
    fn(d)
    p.write_text(json.dumps(d))


# --- lint -------------------------------------------------------------------------------------------------
def test_clean_attempt_has_no_lint_errors(tmp_path):
    drv = "from toypkg.core import entry\n\n\ndef run(inputs):\n    return entry(inputs['n'], inputs['m'])\n"
    b = build(tmp_path, with_ext=False, driver_src=drv)
    assert codes(lint(b), "error") == []


@pytest.mark.parametrize("change,code", [
    (lambda d: d["design"].update(negative_input=dict(d["design"]["positive_input"])), "L009"),
    (lambda d: d["design"].update(positive_input={"n": 2, "m": 5}, negative_input={"n": 1, "m": 6}), "L009"),
    (lambda d: d["design"].update(boundary_variable="m"), "L010"),
    (lambda d: d["design"]["oracle"].update(signal_location="toypkg/core.py:1"), "L008"),
    (lambda d: d["design"]["oracle"].update(spec="TODO: fill in"), "L008"),
    (lambda d: d["execution"].update(entry_called="toypkg/core.py::check"), "L016"),
    (lambda d: d["execution"].update(repo_files_modified=["toypkg/core.py"]), "L018"),
    (lambda d: d["execution"]["mocks"].append({"symbol": "toypkg.core.pre", "kind": "patch", "behavior": "sim",
                                               "impl": "sim.py::pre", "sim_class": "independent_native", "reason": "long enough"}), "L013"),
])
def test_lint_error_codes(tmp_path, change, code):
    b = build(tmp_path, with_ext=False)
    edit_form(b, change)
    assert code in codes(lint(b), "error")


def test_lint_flags_undisclosed_inputs_and_defaults(tmp_path):
    drv = "from toypkg.core import entry\n\n\ndef run(inputs):\n    return entry(inputs['n'], inputs['hidden']) if inputs.get('flag', 0) else entry(inputs['n'], inputs.get('m', 1))\n"
    b = build(tmp_path, with_ext=False, driver_src=drv)
    issues = lint(b)
    assert any(i.code == "L012" and i.level == "error" and "hidden" in i.message for i in issues)
    assert any(i.code == "L012" and i.level == "warn" and "'flag'" in i.message for i in issues)


def test_lint_warns_about_asserts_network_and_stub_sims(tmp_path):
    drv = "import socket\nfrom toypkg.core import entry\n\n\ndef run(inputs):\n    assert inputs['n']\n    return entry(inputs['n'], inputs['m'])\n"
    b = build(tmp_path, with_ext=False, driver_src=drv)
    c = codes(lint(b), "warn")
    assert "L007" in c and "L023" in c


def test_lint_accepts_a_declared_scale_and_complains_about_a_missing_one(tmp_path):
    b = build(tmp_path, with_ext=False, pos={"n": 2, "m": 0}, neg={"n": 1, "m": 0})
    hint_m = [i for i in lint(b) if i.code == "L011"]
    assert hint_m and hint_m[0].level == "warn"                      # m=0 differs from witness m=1, no scale declared
    edit_form(b, lambda d: d["design"].update(scale={"factor": 0.5, "scaled": ["m"], "reason": "t",
                                                     "invariance_argument": "the guard reads n only, never m"}))
    assert "L011" not in codes(lint(b))


# --- task / init on the real pilot data ----------------------------------------------------------------------
@pytest.mark.skipif(not PILOT_OK, reason="FlexPrefill checkout missing")
def test_task_text_names_the_target_and_shows_the_source():
    t = agent_cli.task_text("F07")
    assert "flex_prefill/ops/flex_prefill_attention.py:1824" in t and "assert batch_size == 1" in t
    assert "1824>" in t and "Region R01" in t and "scope_edge" in t


@pytest.mark.skipif(not PILOT_OK, reason="FlexPrefill checkout missing")
def test_init_creates_a_skeleton_that_lint_rejects_until_filled(tmp_path):
    files = agent_cli.init_attempt("F07", tmp_path / "a")
    assert {f.name for f in files} == {"manifest.json", "form.json", "driver.py"}
    c = codes(agent_cli.lint_attempt(tmp_path / "a"), "error")
    assert "L006" in c and "L008" in c and "L009" in c


STEP4 = "results/step4/flexprefill/limitations_for_tests.json"


@pytest.mark.skipif(not (PIPELINE_ROOT / STEP4).exists() or not PILOT_OK, reason="step 4 hand-off or checkout missing")
def test_init_from_step4_prefills_the_trigger_contrast_pair(tmp_path):
    agent_cli.init_attempt("flexprefill-F014", tmp_path / "a", findings_file=STEP4)
    form = json.loads((tmp_path / "a" / "form.json").read_text())
    d = form["design"]
    assert d["positive_input"]["head_dim"] == 127 and d["negative_input"]["head_dim"] == 128 and d["boundary_variable"] == "head_dim"
    assert json.loads((tmp_path / "a" / "manifest.json").read_text())["findings_file"] == STEP4
    t = agent_cli.task_text("flexprefill-F014", findings_file=STEP4)
    assert "**trigger**" in t and "**contrast**" in t and "witness-v2" in t


# --- oracle lock -------------------------------------------------------------------------------------------
def test_lock_history_and_tamper_detection(tmp_path):
    lock = tmp_path / "L" / "t.json"
    assert register_oracle(lock, "h1") == (True, 0)
    assert register_oracle(lock, "h1") == (True, 0)
    assert register_oracle(lock, "h2") == (True, 1)
    saved = json.loads(lock.read_text())
    assert saved["history"] == ["h1", "h2"]
    assert register_oracle(lock, "h3") == (True, 2)
    assert lock_is_extension(saved, json.loads(lock.read_text()))
    lock.unlink()                                               # the agent deletes the lock to reset the count
    register_oracle(lock, "h3")
    assert not lock_is_extension(saved, json.loads(lock.read_text()))
    assert not lock_is_extension(saved, None)
    forged = {"sha256": "h3", "revisions": 0, "history": ["h1", "h2", "h3"]}
    assert not lock_is_extension(saved, forged)                 # revisions were lowered


def test_env_var_redirects_the_lock_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("CHECKLIMITS_LOCKS_DIR", str(tmp_path / "elsewhere"))
    b = build(tmp_path, with_ext=False)
    harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)
    assert (tmp_path / "elsewhere" / "toy" / "T1.json").exists()


# --- extra negatives ---------------------------------------------------------------------------------------
def test_extra_negative_that_shows_the_effect_refutes_d5(tmp_path):
    b = build(tmp_path, with_ext=False)
    edit_form(b, lambda d: d["design"].update(extra_negatives=[{"n": 5}]))     # n=5 raises, so it is no negative
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    d5 = next(d for d in r.confidence.defeaters if d.id == "D5")
    assert d5.status == "refuted" and "extra negative" in d5.evidence
    assert len(r.extra_negatives) == 1 and r.extra_negatives[0].effect is True


def test_clean_extra_negative_is_recorded_and_keeps_d5_open_to_probing(tmp_path):
    b = build(tmp_path, with_ext=False)
    edit_form(b, lambda d: d["design"].update(extra_negatives=[{"n": 1, "m": 9}]))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    assert r.extra_negatives[0].effect is False
    assert next(d for d in r.confidence.defeaters if d.id == "D5").status == "open"   # boundary probes were not run


def test_extra_negatives_kill_mutants_that_one_negative_cannot(tmp_path):
    # `assert n in (1, 2)` style guard: with a single negative n=1 the mutant 2->3 survives; an extra negative n=2 kills it
    b = build(tmp_path, with_ext=False)
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace("assert n == 1,", "assert n in (1, 2),"))
    harness.subprocess.run(["git", "-C", str(b["repo"]), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "set guard"], check=True)
    commit = harness.subprocess.run(["git", "-C", str(b["repo"]), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    m = json.loads((b["attempt"] / "manifest.json").read_text())
    m["repo_commit"] = commit
    (b["attempt"] / "manifest.json").write_text(json.dumps(m))
    regs = json.loads((b["root"] / "data" / "gold_regions.json").read_text())
    regs[0]["location"]["snippet"] = 'assert n in (1, 2), "n must be 1"'
    (b["root"] / "data" / "gold_regions.json").write_text(json.dumps(regs))
    opts = RunOptions(probe_effect=False, repeats=1, bva=False, mutation=True, replay=False)
    base = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=opts)["report"]
    edit_form(b, lambda d: d["design"].update(extra_negatives=[{"n": 1, "m": 3}]))
    with_extra = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=opts)["report"]
    assert with_extra.checks.mutation.killed >= base.checks.mutation.killed


# --- agent runtime -------------------------------------------------------------------------------------------
def test_sandbox_command_hides_solutions_and_credentials_and_binds_only_the_run_dir(tmp_path):
    cmd = agent_loop.sandbox_cmd(tmp_path / "run", ["opencode", "run"])
    j = " ".join(cmd)
    assert cmd[0] == "bwrap" and "--ro-bind / /" in j and "--unshare-pid" in j and "--die-with-parent" in j
    assert f"--bind {tmp_path / 'run'} {tmp_path / 'run'}" in j
    assert j.count("--bind ") == 1                        # the run directory is the only writable mount
    for hidden in ("attempts", "results", "locks", "tests", "scratch"):
        assert f"--tmpfs {agent_loop.PROJECT_ROOT / hidden}" in j
    assert f"--tmpfs {agent_loop.PIPELINE_ROOT.parent / '.git'}" in j
    assert f"--tmpfs {agent_loop.PIPELINE_ROOT / 'results'}" not in j     # step 4 inputs stay readable
    assert cmd[-2:] == ["opencode", "run"]


def test_agent_env_has_no_secrets_and_points_into_the_run_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SOCLAAS_API_KEY", "dummy")
    env = agent_loop.agent_env(tmp_path / "run")
    assert not any("SOCLAAS" in k or "API_KEY" in k or "proxy" in k.lower() for k in env)
    assert env["CHECKLIMITS_LOCKS_DIR"].startswith(str(tmp_path / "run")) and env["HOME"].startswith(str(tmp_path / "run"))
    assert env["npm_config_offline"] == "true" and env["OPENCODE_DISABLE_MODELS_FETCH"] == "1"


def test_prompt_contains_instructions_wrapper_and_step4_flag(tmp_path):
    p = agent_loop.build_prompt("F07", tmp_path / "run")
    assert "defeaters" in p and str(agent_loop.CL) in p and "task F07" in p and "--findings-file" not in p
    p = agent_loop.build_prompt("flexprefill-F014", tmp_path / "run", findings_file="results/step4/x.json")
    assert "--findings-file results/step4/x.json" in p
    fb = agent_loop.build_prompt("F07", tmp_path / "run", feedback="level=L1")
    assert "level=L1" in fb and "defeaters" not in fb


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bwrap missing")
def test_budgets_stop_a_runaway_session(tmp_path, monkeypatch):
    base = agent_loop.PROJECT_ROOT / "scratch" / "pytest_agent_budget"   # not under /tmp: the sandbox mounts a tmpfs there
    base.mkdir(parents=True, exist_ok=True)
    fake = base / "fake_opencode"
    fake.write_text("#!/bin/sh\nfor i in 1 2 3 4 5 6 7 8 9 10; do\n"
                    "echo '{\"type\":\"tool_use\",\"sessionID\":\"s1\",\"part\":{\"state\":{\"status\":\"completed\"}}}'\n"
                    "echo '{\"type\":\"step_finish\",\"sessionID\":\"s1\",\"part\":{\"tokens\":{\"total\":1000}}}'\n"
                    "sleep 0.2\ndone\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(agent_loop, "OPENCODE", fake)
    monkeypatch.setattr(agent_loop, "HIDE_PATHS_DIRS", [])
    monkeypatch.setattr(agent_loop, "HIDE_PATHS_FILES", [])
    monkeypatch.setattr(agent_loop, "HIDE_DIRS", [])
    monkeypatch.setattr(agent_loop, "SCRATCH_KEEP_RO", [])
    run = base / "run"
    run.mkdir(exist_ok=True)
    st = agent_loop.run_session(run, "go", agent_loop.Budget(tool_calls=3), None, "e.jsonl")
    assert st.stopped_by == "tool_calls" and st.tool_calls == 4 and st.session_id == "s1"
    st = agent_loop.run_session(run, "go", agent_loop.Budget(tokens=2500), None, "e.jsonl")
    assert st.stopped_by == "tokens" and st.tokens == 3000
    st = agent_loop.run_session(run, "go", agent_loop.Budget(), None, "e.jsonl")
    assert st.stopped_by == "finished" and st.tool_calls == 10 and st.llm_steps == 10


def test_feedback_text_lists_next_steps(tmp_path):
    b = build(tmp_path, with_ext=False)
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    t = agent_loop.feedback_text(r)
    assert "level=L0" in t and "next_steps:" in t and "D3" in t and "form_integrity=1.0" in t


# --- call chain section (step 4 witness_hint.call_chain / call_sites) -------------------------------------------
def test_chain_section_lists_call_sites_and_name_mapping():
    hint = {"call_chain_status": "resolved",
            "call_chain": ["a.py::entry", "a.py::mid", "a.py::target"],
            "call_sites": [{"caller": "a.py::entry", "callee": "a.py::mid", "line": 10, "resolved_by": "direct",
                            "args": {"x": "k", "size": "block_size"}},
                           {"caller": "a.py::mid", "callee": "a.py::target", "line": 20, "resolved_by": "unique_name",
                            "args": {"d": "x.shape[3]"}}],
            "uncertain_steps": ["a.py::mid -> a.py::target"],
            "entry_terms": {"names": {"d": "k.shape[3]"}}}
    t = "\n".join(agent_cli.chain_section(hint))
    assert "`entry` calls `mid` at line 10 (direct): x=k, size=block_size" in t
    assert "`mid` calls `target` at line 20 (unique_name): d=x.shape[3]" in t
    assert "`d` = `k.shape[3]`" in t and "resolved by a guess" in t and "call `call_chain[0]`" in t


def test_chain_section_without_a_chain_allows_a_deeper_entry_with_a_reason():
    t = "\n".join(agent_cli.chain_section({"call_chain_status": "not_found"}))
    assert "entry_reason" in t and "no call chain" in t
    assert agent_cli.chain_section({}) == []                     # pilot data has no chain information
    assert "directly" in "\n".join(agent_cli.chain_section({"call_chain_status": "entry_is_target"}))


@pytest.mark.skipif(not (PIPELINE_ROOT / STEP4).exists() or not PILOT_OK, reason="step 4 hand-off or checkout missing")
def test_task_text_for_a_real_finding_has_the_chain_section():
    t = agent_cli.task_text("flexprefill-F007", findings_file=STEP4)
    assert "## How the entry reaches the target" in t and "triton_block_wise_attention" in t


# --- what the agent cannot see ---------------------------------------------------------------------------------
def test_archived_results_are_hidden_from_the_agent():
    cmd = " ".join(agent_loop.sandbox_cmd(Path("/tmp/run"), ["x"]))
    assert f"--tmpfs {agent_loop.PROJECT_ROOT / 'agent_results'}" in cmd
    assert f"--ro-bind /dev/null {agent_loop.PROJECT_ROOT / 'BATCH_RESULTS.md'}" in cmd
    # the rule documents and the harness source stay readable unless the run is blind
    assert "CONFIDENCE_SPEC.md" not in cmd and "blind_pkg" not in cmd


def test_blind_mode_hides_the_rules_and_swaps_the_source_for_compiled_modules():
    cmd = " ".join(agent_loop.sandbox_cmd(Path("/tmp/run"), ["x"], blind=True))
    assert f"--ro-bind /dev/null {agent_loop.PROJECT_ROOT / 'CONFIDENCE_SPEC.md'}" in cmd
    assert f"--ro-bind {agent_loop.BLIND_PKG / 'checklimits'} {agent_loop.PROJECT_ROOT / 'checklimits'}" in cmd


def test_blind_package_has_no_source(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_loop, "BLIND_PKG", tmp_path / "blind")
    out = agent_loop.build_blind_package()
    assert not list(out.glob("*.py")) and (out / "harness.pyc").exists() and (out / "__main__.pyc").exists()
    assert agent_loop.build_blind_package() == out                       # second call reuses it


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bwrap missing")
def test_blind_sandbox_really_hides_the_source_and_the_spec_but_cl_still_runs(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    root = agent_loop.PROJECT_ROOT
    inner = ["sh", "-c", f"ls {root}/checklimits/*.py 2>&1 | head -1; cat {root}/CONFIDENCE_SPEC.md 2>/dev/null | wc -c; "
             f"ls {root}/agent_results | wc -l; {root}/agent/cl lint --help | head -1"]
    out = subprocess.run(agent_loop.sandbox_cmd(run, inner, blind=True), capture_output=True, text=True).stdout.split("\n")
    assert "No such file" in out[0] and out[1].strip() == "0" and out[2].strip() == "0" and out[3].startswith("usage")
    out = subprocess.run(agent_loop.sandbox_cmd(run, inner, blind=False), capture_output=True, text=True).stdout.split("\n")
    assert out[0].endswith(".py") and int(out[1]) > 1000 and out[2].strip() == "0" and out[3].startswith("usage")
