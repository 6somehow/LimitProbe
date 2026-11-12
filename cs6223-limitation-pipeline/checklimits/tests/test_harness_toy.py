"""End-to-end harness tests on a throw-away repository (real subprocesses, real tracers)."""
import json

import pytest

from checklimits import harness
from checklimits.harness import RunOptions
from checklimits.profile import Profile
from toyhelper import DRIVER, build

QUICK = Profile(n_rep=2)                      # two repeats instead of five, to keep tests fast
FULL = RunOptions(repeats=2)                  # everything on
FAST = RunOptions.fast()


def go(tmp_path, options=FAST, **kw):
    b = build(tmp_path, **kw)
    res = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=options, profile=QUICK)
    return b, res["report"], res


def st(r):
    return {d.id: d.status for d in r.confidence.defeaters}


# --- the whole pipeline ---------------------------------------------------------------------------
def test_full_run_eliminates_every_defeater(tmp_path):
    b, r, _ = go(tmp_path, FULL, with_ext=False)
    assert (r.verdict, r.final_verdict, r.exec_result) == ("yes", "yes", "confirmed")
    assert r.confidence.level == "L3" and not r.confidence.calibrated and r.confidence.next_steps == []
    assert set(st(r).values()) == {"eliminated"}
    p, n = r.positive, r.negative
    assert p.target_reached and p.effect and p.exception.type == "AssertionError" and p.exception.raised_at == b["loc"]
    assert n.target_reached and n.effect is False and n.exception is None
    assert [h.outcome for h in p.target_hits] == ["false"] and [h.outcome for h in n.target_hits] == ["true"]
    assert p.target_hits[0].condition_value is True and n.target_hits[0].condition_value is False
    assert r.audit.rate == 1.0 and r.fidelity.entry_index == 0 and r.fidelity.probe_effect_free
    m = r.checks.mutation
    assert m.generated == 4 and m.killed == 4 and m.wilson_lower == pytest.approx(0.510, abs=1e-3)   # negate, 1->2, 1->0, delete
    assert r.checks.bva.adjacent and r.checks.bva.full_scale_positive and r.checks.bva.full_scale_negative is False
    assert r.checks.repeat.runs == 2 and r.checks.repeat.identical and r.checks.replay.ok
    assert r.confidence.profile.name == "default-v1"


def test_fast_run_leaves_optional_defeaters_open(tmp_path):
    _, r, _ = go(tmp_path, FAST, with_ext=False)
    assert st(r)["D3"] == st(r)["D7"] == st(r)["D8"] == st(r)["D9"] == "open"
    assert r.confidence.level == "L0" and "D7" in r.confidence.level_note   # D7 is fatal and unevaluated
    assert any("D3" in s for s in r.confidence.next_steps) and r.checks.mutation is None
    assert any("not run" in n for n in r.notes)


def test_testcase_validates_against_shared_schema(tmp_path):
    _, r, res = go(tmp_path, with_ext=False)
    from schema.models import TestCase
    tc = TestCase.model_validate(res["testcase"].model_dump(mode="json"))
    assert tc.result == "confirmed" and tc.oracle_type == "exception" and tc.executable_on == "cpu"
    assert "confidence=L0" in tc.result_notes and "uncalibrated" in tc.result_notes
    out = harness.write_outputs(res, tmp_path / "out")
    data = json.loads(out["testcase"].read_text())
    assert isinstance(data, list) and len(data) == 1  # codeside.cli validate wants a list of records
    json.loads(out["report"].read_text())


# --- D6: stand-ins and the causal prefix --------------------------------------------------------------
def test_stub_before_target_makes_verdict_bearing_observation_simulated(tmp_path):
    _, r, _ = go(tmp_path, with_ext=True)
    by = {m.symbol: m for m in r.fidelity.mocks}
    assert by["extlib_before"].on_path and not by["extlib_after"].on_path
    bearing = [i for i in r.information if i.verdict_bearing]
    assert {i.evidence_state for i in bearing} == {"simulated:stub"} and bearing[0].depends_on_mocks == ["extlib_before"]
    assert st(r)["D6"] == "refuted" and r.verdict == "yes"
    after = next(i for i in r.information if not i.verdict_bearing)
    assert sorted(after.depends_on_mocks) == ["extlib_after", "extlib_before"]


def test_stand_in_touched_only_at_import_time_still_precedes_the_target(tmp_path):
    # regression (found by the fault-injection benchmark): events recorded while the repo was imported
    # were dropped, so a stub used only at import time looked like it was not on the path
    _, r, _ = go(tmp_path, with_ext="import")
    by = {m.symbol: m for m in r.fidelity.mocks}
    assert by["extlib_before"].on_path and by["extlib_before"].accesses_before_target >= 1
    bearing = [i for i in r.information if i.verdict_bearing]
    assert {i.evidence_state for i in bearing} == {"simulated:stub"} and st(r)["D6"] == "refuted"


def test_no_stand_in_means_direct_evidence(tmp_path):
    _, r, _ = go(tmp_path, with_ext=False)
    assert [i.evidence_state for i in r.information] == ["direct", "direct", "direct"]
    assert st(r)["D6"] == "eliminated"


def test_sim_mock_before_target_is_fake_and_residual(tmp_path):
    mocks = [{"symbol": "toypkg.core.pre", "kind": "patch", "behavior": "sim", "impl": "sim.py::pre",
              "sim_class": "independent_native", "reason": "t"}]
    b = build(tmp_path, with_ext=False, mocks_override=mocks)
    (b["attempt"] / "sim.py").write_text("def pre(n):\n    return n + 1\n")
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    assert r.fidelity.mocks[0].on_path and r.fidelity.mocks[0].sim_class == "independent_native"
    assert {i.evidence_state for i in r.information if i.verdict_bearing} == {"simulated:fake"}
    assert st(r)["D6"] == "residual" and r.verdict == "yes"


# --- D14, D11, D12 ------------------------------------------------------------------------------------
def test_entry_depth_defeater(tmp_path):
    kw = dict(with_ext=False, pos={"n": 2, "direct": True}, neg={"n": 1, "direct": True})
    _, r, _ = go(tmp_path / "a", **kw)
    assert r.fidelity.entry_index == 1 and st(r)["D14"] == "refuted" and r.confidence.level == "L0"
    assert any("entry observed first" in n for n in r.notes)
    _, r, _ = go(tmp_path / "b", entry_reason="check() is the unit under test", **kw)
    assert st(r)["D14"] == "residual"


def test_modified_target_is_invalid(tmp_path):
    b = build(tmp_path, with_ext=False)
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace('"n must be 1"', '"n must equal 1"'))  # behaviour unchanged, statement edited
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    ad = r.fidelity.ast_diff
    assert not ad.target_statement_intact and not ad.git_status_clean and ad.files_changed == ["toypkg/core.py"]
    # D11 sees the edited message (full statement); D12 compares the decision only, which did not change
    assert st(r)["D11"] == "refuted" and st(r)["D12"] == "eliminated"
    assert (r.confidence.level, r.verdict, r.final_verdict) == ("invalid", "yes", "inconclusive")
    assert r.exec_result == "test_error" and any("repo_files_modified" in n for n in r.notes)


def test_logging_probe_is_not_a_semantic_change(tmp_path):
    b = build(tmp_path, with_ext=False)
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace("    base = pre(n)\n", "    base = pre(n)\n    print('probe')\n"))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    assert r.fidelity.ast_diff.statements_changed == 0 and r.fidelity.ast_diff.target_statement_intact
    assert st(r)["D11"] == "eliminated"
    assert st(r)["D12"] == "refuted"   # the print moved the target down one line, so Region.location no longer matches


# --- verdict table paths -----------------------------------------------------------------------------
def test_target_not_reached_is_inconclusive(tmp_path):
    drv = DRIVER.replace("def run(inputs):\n", "def run(inputs):\n    if inputs.get('boom'):\n        raise KeyError('x')\n")
    _, r, _ = go(tmp_path, with_ext=False, driver_src=drv, pos={"n": 2, "boom": True})
    assert r.positive.effect is None and not r.positive.target_reached
    assert (r.verdict, r.exec_result, r.confidence.level) == ("inconclusive", "test_error", "n/a")
    assert st(r)["D1"] == "refuted"


def test_timeout_is_test_error(tmp_path):
    _, r, _ = go(tmp_path, with_ext=False, pos={"n": 2, "sleep": 30}, manifest_overrides={"timeout_s": 3})
    assert r.positive.status == "timeout" and (r.verdict, r.exec_result) == ("inconclusive", "test_error")


def test_both_inputs_show_effect(tmp_path):
    _, r, _ = go(tmp_path, with_ext=False, neg={"n": 3})
    assert (r.verdict, r.exec_result) == ("inconclusive", "test_error") and "both inputs" in r.verdict_reason


def test_neither_input_shows_effect_is_no(tmp_path):
    _, r, _ = go(tmp_path, with_ext=False, pos={"n": 1})
    # no effect on either input, but the Region condition is false on the "positive" input too (D2),
    # so the 'no' cannot stand: nothing was tested that should have fired
    assert r.verdict == "no" and st(r)["D2"] == "refuted" and st(r)["D5"] == "refuted"
    assert (r.confidence.level, r.final_verdict, r.exec_result) == ("invalid", "inconclusive", "test_error")


def test_unsupported_outcome_is_not_run(tmp_path):
    b = build(tmp_path, with_ext=False)
    reg = json.loads((b["root"] / "data" / "gold_regions.json").read_text())
    reg[0]["outcome"] = "fallback"
    (b["root"] / "data" / "gold_regions.json").write_text(json.dumps(reg))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FULL, profile=QUICK)["report"]
    assert (r.verdict, r.exec_result) == ("inconclusive", "not_run") and r.checks.mutation is None


# --- D7, D8, D9 ----------------------------------------------------------------------------------------
def test_probe_effect_detected(tmp_path):
    _, r, _ = go(tmp_path, RunOptions(probe_effect=True, repeats=1, bva=False, mutation=False, replay=False),
                 with_ext=False, neg={"n": 1, "probe_sensitive": True})
    assert not r.fidelity.probe_effect_free and st(r)["D7"] == "refuted" and r.confidence.level == "invalid"


def test_nondeterminism_refutes_d8(tmp_path):
    drv = DRIVER.replace("def run(inputs):\n", "def run(inputs):\n    import random\n    if inputs.get('flaky'):\n"
                         "        return random.random()\n")
    _, r, _ = go(tmp_path, RunOptions(probe_effect=False, repeats=3, bva=False, mutation=False, replay=False),
                 with_ext=False, driver_src=drv, neg={"n": 1, "flaky": True})
    assert r.checks.repeat.runs == 3 and not r.checks.repeat.identical and st(r)["D8"] == "refuted"


def test_replay_in_fresh_checkout_detects_uncommitted_dependence(tmp_path):
    # an uncommitted edit to a NON-target statement changes what the run does; a fresh checkout of the
    # pinned commit does not have the edit, so the replay must disagree
    b = build(tmp_path, with_ext=False)
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace("    return n + 1\n", "    return n + 2\n", 1))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"],
                            options=RunOptions(probe_effect=False, repeats=1, bva=False, mutation=False, replay=True),
                            profile=QUICK)["report"]
    assert not r.checks.replay.ok and "different canonical traces" in r.checks.replay.detail
    assert st(r)["D9"] == "refuted" and not r.fidelity.ast_diff.git_status_clean


# --- D4 --------------------------------------------------------------------------------------------------
def test_oracle_revisions_are_counted(tmp_path):
    b = build(tmp_path, with_ext=False)
    run = lambda: harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    r1, r2 = run(), run()
    assert r1.oracle.preregistered and r1.oracle.revisions_after_first_run == 0 and r2.oracle.sha256 == r1.oracle.sha256
    assert st(r2)["D4"] == "eliminated"
    form = json.loads((b["attempt"] / "form.json").read_text())
    form["design"]["oracle"]["spec"] += " (edited after the first run)"
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    r3 = run()
    assert r3.oracle.revisions_after_first_run == 1 and st(r3)["D4"] == "residual"


def test_changing_inputs_after_a_run_is_not_an_oracle_revision(tmp_path):
    b = build(tmp_path, with_ext=False)
    harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)
    form = json.loads((b["attempt"] / "form.json").read_text())
    form["design"]["positive_input"] = {"n": 3}
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    assert r.oracle.revisions_after_first_run == 0


def test_wrong_claims_lower_form_integrity(tmp_path):
    b = build(tmp_path, with_ext=False)
    form = json.loads((b["attempt"] / "form.json").read_text())
    form["claims"]["target_reached"] = False
    form["claims"]["decision_outcomes_seen"] = ["true"]
    form["claims"]["positive_observed"] = "ValueError at :3"
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=FAST)["report"]
    assert r.audit.matched_checks == 3 and r.audit.rate == 0.5
    assert [i.claim for i in r.audit.items if not i.match] == ["target_reached", "decision_outcomes_seen", "positive_observed"]
    assert r.verdict == "yes"  # the harness verdict does not depend on what the agent claimed


# --- D10 -------------------------------------------------------------------------------------------------
def test_scale_checked_by_full_scale_probes(tmp_path):
    scale = {"factor": 0.5, "scaled": ["m"], "reason": "t", "invariance_argument": "guard reads n only"}
    # witness_hint is {"n": 2, "m": 1}; the scaled run uses m=0
    b, r, _ = go(tmp_path, RunOptions(probe_effect=False, repeats=1, bva=True, mutation=False, replay=False),
                 with_ext=False, scale=scale, pos={"n": 2, "m": 0}, neg={"n": 1, "m": 0})
    assert st(r)["D10"] == "eliminated" and not any(n.startswith("T3") for n in r.notes)
    assert r.checks.bva.full_scale_positive is True


def test_scale_disagreement_refutes_d10(tmp_path):
    drv = DRIVER.replace('out = entry(inputs["n"], inputs["m"])',
                         'out = entry(inputs["n"] if inputs["m"] == 0 else 1, inputs["m"])')
    assert drv != DRIVER
    scale = {"factor": 0.5, "scaled": ["m"], "reason": "t", "invariance_argument": "wrongly assumed"}
    _, r, _ = go(tmp_path, RunOptions(probe_effect=False, repeats=1, bva=True, mutation=False, replay=False),
                 with_ext=False, scale=scale, pos={"n": 2, "m": 0}, neg={"n": 1, "m": 0}, driver_src=drv)
    assert st(r)["D10"] == "refuted" and r.checks.bva.full_scale_positive is False


# --- backends and environment --------------------------------------------------------------------------
def test_settrace_backend_gives_the_same_report(tmp_path):
    b, r, _ = go(tmp_path, with_ext=False, manifest_overrides={"env": {"CHECKLIMITS_TRACER": "settrace"}})
    assert (r.verdict, r.final_verdict) == ("yes", "yes")
    assert [h.outcome for h in r.positive.target_hits] == ["false"] and [h.outcome for h in r.negative.target_hits] == ["true"]
    assert r.positive.exception.raised_at == b["loc"] and r.fidelity.entry_index == 0 and r.audit.rate == 1.0


def test_child_environment_is_scrubbed(tmp_path, monkeypatch):
    monkeypatch.setenv("SOCLAAS_API_KEY", "dummy-secret")
    monkeypatch.setenv("https_proxy", "http://x")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-secret")
    from checklimits import runner
    env = runner.clean_env()
    assert not [k for k in env if k.startswith(("SOCLAAS_", "OPENAI_")) or k.lower().endswith("_proxy")]
    b = build(tmp_path, with_ext=False, pos={"n": 1, "leak_probe": True})
    ctx = harness._Ctx(b["attempt"], b["root"])
    raw, _ = ctx.run("positive", {"n": 1, "m": 1, "leak_probe": True}, trace=False)
    assert raw["status"] == "ok" and raw["returned"] == "0" and "dummy-secret" not in json.dumps(raw)
