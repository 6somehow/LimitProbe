"""End-to-end harness tests on a throw-away repository (real subprocesses, real sys.monitoring)."""
import json

import pytest

from checklimits import harness
from toyhelper import DRIVER, build


def run(tmp_path, **kw):
    b = build(tmp_path, **kw)
    res = harness.run_attempt(b["attempt"], pipeline_root=b["root"])
    return b, res["report"], res


def test_confirmed_with_full_evidence(tmp_path):
    b, r, res = run(tmp_path, with_ext=False)
    assert (r.verdict, r.final_verdict, r.exec_result) == ("yes", "yes", "confirmed")
    p, n = r.positive, r.negative
    assert p.target_reached and p.effect and p.exception.type == "AssertionError"
    assert p.exception.raised_at == b["loc"]
    assert n.target_reached and n.effect is False and n.exception is None
    assert [h.outcome for h in p.target_hits] == ["false"] and [h.outcome for h in n.target_hits] == ["true"]
    assert p.target_hits[0].condition_value is True and n.target_hits[0].condition_value is False
    assert p.target_hits[0].locals["n"] == "2" and n.target_hits[0].locals["n"] == "1"
    assert r.audit.rate == 1.0 and r.audit.matched_checks == 6
    assert r.fidelity.entry_index == 0 and r.fidelity.s_entry == 1.0 and r.fidelity.probe_effect_free
    assert r.fidelity.ast_diff.statements_changed == 0 and r.fidelity.ast_diff.git_status_clean
    assert r.fidelity.ast_diff.target_statement_intact and r.fidelity.ast_diff.snippet_matches_region
    assert r.checks.differing_factors == ["n"] and r.checks.boundary_adjacent is True and r.checks.controls_differ
    assert r.checks.mutation is None and r.checks.replay is None
    assert r.scorecard.gates["G2_replay_ok"] is None and r.scorecard.dims["mutation"] == 0.0
    assert r.oracle.verified_tier == "O4" and r.oracle.revisions_after_first_run == 0
    assert p.coverage.lines_executed < p.coverage.lines_total
    # the negative run goes further down the chain than the positive one
    assert n.coverage.lines_executed > p.coverage.lines_executed


def test_testcase_validates_against_shared_schema(tmp_path):
    _, r, res = run(tmp_path, with_ext=False)
    from schema.models import TestCase
    tc = TestCase.model_validate(res["testcase"].model_dump(mode="json"))
    assert tc.result == "confirmed" and tc.oracle_type == "exception" and tc.executable_on == "cpu"
    out = harness.write_outputs(res, tmp_path / "out")
    data = json.loads(out["testcase"].read_text())
    assert isinstance(data, list) and len(data) == 1  # codeside.cli validate wants a list of records
    json.loads(out["report"].read_text())


def test_mock_on_path_is_computed_from_access_order(tmp_path):
    _, r, _ = run(tmp_path, with_ext=True)
    by = {m.symbol: m for m in r.fidelity.mocks}
    assert by["extlib_before"].on_path and by["extlib_before"].accesses_before_target >= 1
    assert not by["extlib_after"].on_path
    assert r.evidence.mocks_on_path == 1 and r.evidence.mocks_off_path == 1
    assert r.fidelity.s_mock == pytest.approx(1 - 0.4 - 0.05)
    assert r.verdict == "yes"


def test_entry_depth_from_first_started_function(tmp_path):
    _, r, _ = run(tmp_path, with_ext=False, pos={"n": 2, "direct": True}, neg={"n": 1, "direct": True},
                  form_overrides={})
    assert r.fidelity.entry_index == 1 and r.fidelity.s_entry == 0.0
    assert any("entry observed first" in n for n in r.notes)


def test_modified_repo_fails_gate_g3(tmp_path):
    b = build(tmp_path, with_ext=False)
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace("assert n == 1,", "assert n >= 1,"))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"])["report"]
    ad = r.fidelity.ast_diff
    assert not ad.target_statement_intact and not ad.git_status_clean and ad.files_changed == ["toypkg/core.py"]
    assert ad.statements_changed >= 1 and not ad.snippet_matches_region
    assert r.scorecard.gates["G3_no_critical_modification"] is False
    assert r.final_verdict == "inconclusive" and r.scorecard.final <= 0.49
    assert any("repo_files_modified" in n for n in r.notes)


def test_logging_probe_is_not_a_semantic_change(tmp_path):
    b = build(tmp_path, with_ext=False)
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace("    base = n + 1\n", "    base = n + 1\n    print('probe')\n"))
    # line numbers moved by one, so the target is now one line lower than Region says
    # -> the snippet check must notice, but the statement diff itself must be 0
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"])["report"]
    assert r.fidelity.ast_diff.statements_changed == 0
    assert not r.fidelity.ast_diff.snippet_matches_region


def test_target_not_reached_gives_test_error_or_gate(tmp_path):
    # positive input that returns before ... no such path in toy; use a driver error before the target
    drv = DRIVER.replace("def run(inputs):\n", "def run(inputs):\n    if inputs.get('boom'):\n        raise KeyError('x')\n")
    _, r, _ = run(tmp_path, with_ext=False, driver_src=drv, pos={"n": 2, "boom": True})
    assert r.positive.effect is None and not r.positive.target_reached
    assert (r.verdict, r.exec_result) == ("inconclusive", "test_error")
    assert "before the target was reached" in r.verdict_reason


def test_timeout_is_test_error(tmp_path):
    _, r, _ = run(tmp_path, with_ext=False, pos={"n": 2, "sleep": 30}, manifest_overrides={"timeout_s": 3})
    assert r.positive.status == "timeout" and r.positive.effect is None
    assert (r.verdict, r.exec_result) == ("inconclusive", "test_error")


def test_child_environment_is_scrubbed(tmp_path, monkeypatch):
    monkeypatch.setenv("SOCLAAS_API_KEY", "dummy-secret")
    monkeypatch.setenv("https_proxy", "http://x")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-secret")
    from checklimits import runner
    env = runner.clean_env()
    assert not [k for k in env if k.startswith(("SOCLAAS_", "OPENAI_")) or k.lower().endswith("_proxy")]
    b = build(tmp_path, with_ext=False, pos={"n": 1, "leak_probe": True})
    raw = harness.runner.run_child(harness.runner.build_spec(
        harness.AttemptManifest.model_validate_json((b["attempt"] / "manifest.json").read_text()), b["attempt"],
        b["root"], harness.load_task("F1", b["root"] / "data").region("R1"), {"n": 1, "m": 1, "leak_probe": True},
        [], None, False), 60)
    assert raw["status"] == "ok" and raw["returned"] == "0"
    assert "dummy-secret" not in json.dumps(raw)


def test_probe_effect_detected(tmp_path):
    # driver behaves differently when a monitoring tool is registered -> traced != untraced
    _, r, _ = run(tmp_path, with_ext=False, neg={"n": 1, "probe_sensitive": True})
    assert not r.fidelity.probe_effect_free and r.fidelity.s_probe == 0.0
    assert r.scorecard.dims["fidelity"] == 0.0


def test_oracle_revisions_are_counted(tmp_path):
    b = build(tmp_path, with_ext=False)
    r1 = harness.run_attempt(b["attempt"], pipeline_root=b["root"], probe=False)["report"]
    assert r1.oracle.preregistered and r1.oracle.revisions_after_first_run == 0
    r2 = harness.run_attempt(b["attempt"], pipeline_root=b["root"], probe=False)["report"]
    assert r2.oracle.revisions_after_first_run == 0 and r2.oracle.sha256 == r1.oracle.sha256
    form = json.loads((b["attempt"] / "form.json").read_text())
    form["design"]["oracle"]["spec"] += " (edited after the first run)"
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    r3 = harness.run_attempt(b["attempt"], pipeline_root=b["root"], probe=False)["report"]
    assert r3.oracle.revisions_after_first_run == 1
    assert r3.scorecard.dims["oracle"] == pytest.approx(0.75)


def test_wrong_claims_lower_form_integrity(tmp_path):
    b = build(tmp_path, with_ext=False)
    form = json.loads((b["attempt"] / "form.json").read_text())
    form["claims"]["target_reached"] = False
    form["claims"]["decision_outcomes_seen"] = ["true"]
    form["claims"]["positive_observed"] = "ValueError at :3"
    (b["attempt"] / "form.json").write_text(json.dumps(form))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], probe=False)["report"]
    assert r.audit.matched_checks == 3 and r.scorecard.form_integrity == 0.5
    assert [i.claim for i in r.audit.items if not i.match] == ["target_reached", "decision_outcomes_seen", "positive_observed"]
    assert r.verdict == "yes"  # the harness verdict does not depend on what the agent claimed


def test_both_inputs_show_effect_is_inconclusive(tmp_path):
    _, r, _ = run(tmp_path, with_ext=False, neg={"n": 3})
    assert (r.verdict, r.exec_result) == ("inconclusive", "test_error")
    assert "both inputs" in r.verdict_reason


def test_neither_input_shows_effect_is_no_but_g5_fails_without_mutation(tmp_path):
    _, r, _ = run(tmp_path, with_ext=False, pos={"n": 1})
    assert r.verdict == "no"
    assert r.final_verdict == "inconclusive" and r.exec_result == "test_error"  # G5 needs a mutation kill rate; not run in P1
    assert r.scorecard.gates["G5_no_requires_infection_and_sensitive_oracle"] is False


def test_unsupported_outcome_is_not_run(tmp_path):
    b = build(tmp_path, with_ext=False)
    reg = json.loads((b["root"] / "data" / "gold_regions.json").read_text())
    reg[0]["outcome"] = "fallback"
    (b["root"] / "data" / "gold_regions.json").write_text(json.dumps(reg))
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], probe=False)["report"]
    assert (r.verdict, r.exec_result) == ("inconclusive", "not_run")
