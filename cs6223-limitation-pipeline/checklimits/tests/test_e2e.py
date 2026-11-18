"""`checklimits test | report | envcheck` on a throw-away pipeline root (toy repository, step 4 hand-off, one attempt)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from checklimits import cli, e2e, testreport
from checklimits.models import PIPELINE_ROOT
from toyhelper import build

FF = "results/step4/toy/limitations_for_tests.json"


def _finding(fid, line, snippet, status="solved", with_code=True, effect="reject", extra_trigger=True):
    wh = {"format": "witness-v2", "kind": "input_value", "status": status, "condition": "n != 1",
          "trigger": {"n": 2} if extra_trigger else None, "contrast": {"n": 1} if status == "solved" else None,
          "atoms": {"n": {"kind": "input", "sort": "int"}}, "location": f"toypkg/core.py:{line}"}
    if status == "infeasible":
        wh["infeasible_because"] = "call_chain"
    lim = {"schema_version": "0.1.0", "limitation_id": f"CL-{fid}", "artifact_id": "toy",
           "origin": "code" if with_code else "paper", "condition_text": "n != 1",
           "condition": {"expr": "n != 1", "params": ["n"], "path_prefix": []},
           "effect_type": effect, "effect_text": "the toy guard rejects", "paper_evidence":
               [{"quote": "n must be 1", "source": "paper", "locator": "p.1"}] if not with_code else [],
           "code_evidence": ([{"file": "toypkg/core.py", "line_start": line, "line_end": None,
                               "function": "toypkg/core.py::check", "snippet": snippet}] if with_code else []),
           "region_ids": [f"R-{fid}"], "provenance": "ast"}
    return {"schema_version": "0.2.0", "finding_id": fid, "artifact_id": "toy", "category": "undisclosed",
            "level": "L2", "limitation_ids": [lim["limitation_id"]], "verification_ids": [], "scope_status": "unknown",
            "evaluated_in_paper": None, "effect_type": effect, "summary": f"toy finding {fid}",
            "witness_hint": wh, "confidence": "llm_assisted", "priority": 1, "rationale": "", "review": "worth_testing",
            "review_note": "blind review by an LLM subagent", "limitations": [lim], "verifications": []}


@pytest.fixture
def toy(tmp_path):
    b = build(tmp_path, with_ext=False)
    root, line = b["root"], b["line"]
    assert_line = line
    assign_line = line - 1                                     # `base = pre(n)`: cannot raise by itself
    (root / "data" / "artifact.json").write_text(json.dumps({
        "schema_version": "0.1.0", "artifact_id": "toy", "paper_title": "A toy paper", "venue": "NOWHERE 2026",
        "repo_url": "https://example.org/repo", "commit": b["commit"], "entry_points": ["toypkg/core.py::entry"],
        "execution_env": ["cpu"]}))
    fs = [_finding("toy-F1", assert_line, 'assert n == 1, "n must be 1"'),                    # judgeable, has a package
          _finding("toy-F2", 0, "", with_code=False, status="unknown"),                      # paper-side only
          _finding("toy-F3", assert_line, 'assert n == 1, "n must be 1"', status="infeasible", extra_trigger=False),
          _finding("toy-F4", assign_line, "base = pre(n)"),                                  # reject on an assignment
          _finding("toy-F5", assert_line, 'assert n == 1, "n must be 1"')]                   # judgeable, no package
    ff = root / FF
    ff.parent.mkdir(parents=True)
    ff.write_text(json.dumps({"schema_version": "0.2.0", "findings": fs}))
    # one package, for toy-F1; its manifest names the step 4 hand-off like a real agent package does
    arch = root / "archive" / "F1-run"
    shutil.copytree(b["attempt"], arch / "attempt")
    m = json.loads((arch / "attempt" / "manifest.json").read_text())
    m.update(finding_id="toy-F1", findings_file=FF, region_id="R-toy-F1", data_dir="data")
    (arch / "attempt" / "manifest.json").write_text(json.dumps(m))
    form = json.loads((arch / "attempt" / "form.json").read_text())
    form["finding_id"] = "toy-F1"
    (arch / "attempt" / "form.json").write_text(json.dumps(form))
    return {"root": root, "archive": root / "archive", "results": root / "out", "commit": b["commit"]}


def _run(toy, **kw):
    args = dict(findings_file=FF, data_dir="data", repo_rel="repo", results_root=toy["results"],
                attempts_roots=[toy["archive"]], root=toy["root"], workers=1, fast=True)
    args.update(kw)
    return e2e.run_test("toy", **args)


def _records(toy):
    d = toy["results"] / "tests" / "toy"
    return {p.parent.name: testreport.read_record(p) for p in sorted(d.glob("*/report.json"))}


def test_every_finding_gets_one_record_with_a_result_or_a_reason(toy):
    out = _run(toy)
    assert out["exit_code"] == 0 and out["one_to_one"] and out["n_input"] == 5
    r = _records(toy)
    assert set(r) == {"toy-F1", "toy-F2", "toy-F3", "toy-F4", "toy-F5"}
    assert r["toy-F1"].status == "tested" and r["toy-F1"].not_run is None
    assert r["toy-F1"].verdict in ("yes", "no", "inconclusive") and r["toy-F1"].level is not None
    why = {k: v.not_run.code for k, v in r.items() if v.status == "not_run"}
    assert why == {"toy-F2": "no_code_location", "toy-F3": "witness_unusable", "toy-F4": "outcome_unsupported",
                   "toy-F5": "not_attempted"}
    assert all(v.not_run.reason for v in r.values() if v.not_run)
    assert "infeasible" in r["toy-F3"].not_run.reason and "call_chain" in r["toy-F3"].not_run.reason
    assert out["counts"]["not_run_by_code"] == {"no_code_location": 1, "witness_unusable": 1,
                                                "outcome_unsupported": 1, "not_attempted": 1}


def test_levels_are_labelled_uncalibrated_everywhere(toy):
    _run(toy)
    for rec in _records(toy).values():
        assert rec.calibrated is False and rec.confidence_label == "uncalibrated"
    md = (toy["results"] / "report" / "toy" / "LIMITATIONS.md").read_text()
    assert "uncalibrated" in md and "(uncalibrated)" in md
    raw = json.loads((toy["results"] / "tests" / "toy" / "toy-F1" / "report.json").read_text())
    assert raw["schema_version"] == "checklimits-test-report/1" and raw["calibrated"] is False


def test_report_has_one_section_and_one_table_row_per_finding(toy):
    _run(toy)
    md = (toy["results"] / "report" / "toy" / "LIMITATIONS.md").read_text()
    for fid in ("toy-F1", "toy-F2", "toy-F3", "toy-F4", "toy-F5"):
        assert md.count(f"\n## {fid}\n") == 1 and md.count(f"| [{fid}](#") == 1
    assert "**Not tested** (`no_code_location`)" in md and "**Verdict `" in md
    assert "A toy paper" in md and "NOWHERE 2026" in md
    idx = json.loads((toy["results"] / "tests" / "toy" / "index.json").read_text())
    assert idx["n_input"] == idx["n_records"] == 5 and idx["one_to_one"] and idx["problems"] == []


def test_tested_finding_keeps_the_files_a_reader_needs(toy):
    _run(toy)
    d = toy["results"] / "tests" / "toy" / "toy-F1"
    for f in ("report.json", "execution_report.json", "testcase.json", "attempt/manifest.json", "attempt/driver.py"):
        assert (d / f).exists(), f
    assert isinstance(json.loads((d / "testcase.json").read_text()), list)       # codeside.cli validate wants a list
    # the copied package re-audits to the same verdict
    again = _run(toy, attempts_roots=[], only=["toy-F1"])
    assert again["exit_code"] == 0
    assert _records(toy)["toy-F1"].verdict == json.loads((d / "report.json").read_text())["verdict"]


def test_only_reruns_the_named_findings_and_keeps_the_rest(toy):
    _run(toy)
    before = {k: v.model_dump() for k, v in _records(toy).items()}
    shutil.rmtree(toy["archive"])                              # F1's original package is gone; its copy remains
    out = _run(toy, only=["toy-F5"], attempts_roots=None)
    assert out["one_to_one"] and out["n_input"] == 5
    after = _records(toy)
    assert after["toy-F2"].model_dump() == before["toy-F2"]
    assert after["toy-F1"].model_dump() == before["toy-F1"]    # untouched: kept from the earlier run


def test_unusable_environment_is_not_a_finding_failure(toy):
    out = _run(toy, python="/nonexistent/python", strict=True)
    r = _records(toy)
    assert r["toy-F1"].status == "not_run" and r["toy-F1"].not_run.code == "env_unavailable"
    assert "does not exist" in r["toy-F1"].not_run.reason
    assert r["toy-F2"].not_run.code == "no_code_location"      # reasons unrelated to the environment stay as they were
    assert out["exit_code"] == e2e.EXIT_STRICT and out["one_to_one"]
    assert _run(toy, python="/nonexistent/python")["exit_code"] == 0       # not strict: complete report, exit 0
    env = json.loads((toy["results"] / "tests" / "toy" / "ENV.json").read_text())
    assert env["status"] == "not_ok"


def test_envcheck_checks_commit_interpreter_and_imports(toy):
    env = e2e.envcheck("toy", "data", "repo", root=toy["root"])
    assert env["status"] == "ok" and env["repo"]["matches"] and env["imports"] == [
        {"module": "toypkg.core", "ok": True, "error": None}]
    subprocess.run(["git", "-C", str(toy["root"] / "repo"), "commit", "-q", "--allow-empty", "-m", "moved"], check=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"})
    env = e2e.envcheck("toy", "data", "repo", root=toy["root"])
    assert env["status"] == "not_ok" and "pinned commit" in " ".join(env["reasons"])
    (toy["root"] / "repo" / "toypkg" / "core.py").write_text("import not_a_module_xyz\n")
    env = e2e.envcheck("toy", "data", "repo", root=toy["root"])
    assert any("cannot import toypkg.core" in x for x in env["reasons"])


def test_missing_record_breaks_one_to_one_and_exit_code(toy):
    _run(toy)
    (toy["results"] / "tests" / "toy" / "toy-F3" / "report.json").unlink()
    out = e2e.run_report("toy", findings_file=FF, data_dir="data", results_root=toy["results"], root=toy["root"])
    assert out["exit_code"] == e2e.EXIT_ONE_TO_ONE and not out["one_to_one"]
    assert any("toy-F3" in p for p in out["problems"])


def test_report_command_regenerates_markdown_from_records(toy):
    _run(toy)
    md = toy["results"] / "report" / "toy" / "LIMITATIONS.md"
    md.unlink()
    out = e2e.run_report("toy", findings_file=FF, data_dir="data", results_root=toy["results"], root=toy["root"])
    assert out["exit_code"] == 0 and md.exists()


def test_check_one_to_one_flags_every_kind_of_loss():
    mk = lambda fid, **kw: testreport.TestRecord(finding_id=fid, artifact_id="a", status="not_run",
                                                 not_run=testreport.NotRun(code="not_attempted", reason="x"), **kw)
    assert testreport.check_one_to_one(["a-1", "a-2"], [mk("a-1"), mk("a-2")]) == []
    assert any("no record for a-2" in p for p in testreport.check_one_to_one(["a-1", "a-2"], [mk("a-1")]))
    assert any("not in the input" in p for p in testreport.check_one_to_one(["a-1"], [mk("a-1"), mk("a-9")]))
    assert any("2 records" in p for p in testreport.check_one_to_one(["a-1"], [mk("a-1"), mk("a-1")]))
    bad = testreport.TestRecord(finding_id="a-1", artifact_id="a", status="not_run")
    assert any("without a reason" in p for p in testreport.check_one_to_one(["a-1"], [bad]))
    cal = mk("a-1")
    cal.calibrated = True
    assert any("uncalibrated" in p for p in testreport.check_one_to_one(["a-1"], [cal]))
    assert any("section" in p for p in testreport.check_one_to_one(["a-1"], [mk("a-1")], md="# empty\n"))


def test_unknown_reason_code_is_rejected():
    with pytest.raises(AssertionError):
        testreport.not_run_record({"finding_id": "a-1", "artifact_id": "a"}, "because", "x")


# ---- CLI exit codes (contract section 6) ----------------------------------------------------------------------
def test_cli_exit_code_2_for_an_unregistered_artifact(capsys):
    assert cli.main(["test", "no-such-artifact"]) == e2e.EXIT_INPUT
    assert "no-such-artifact" in capsys.readouterr().out


def test_cli_exit_code_2_for_a_missing_findings_file(tmp_path, capsys):
    rc = cli.main(["test", "sparta", "--findings-file", "results/step4/none.json", "--results-root", str(tmp_path)])
    assert rc == e2e.EXIT_INPUT


def test_input_with_wrong_schema_version_is_refused(toy):
    p = toy["root"] / FF
    d = json.loads(p.read_text())
    d["schema_version"] = "0.1.0"
    p.write_text(json.dumps(d))
    with pytest.raises(e2e.InputError, match="0.2"):
        _run(toy)


# ---- real step 4 data (tracked in the repository) --------------------------------------------------------------
@pytest.mark.skipif(not (PIPELINE_ROOT / "results/step4/sparta/limitations_for_tests.json").exists(),
                    reason="step 4 hand-off missing")
def test_artifact_without_agent_run_still_reports_every_finding(tmp_path, capsys):
    rc = cli.main(["test", "sparta", "--results-root", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    n = len(json.loads((PIPELINE_ROOT / "results/step4/sparta/limitations_for_tests.json").read_text())["findings"])
    assert rc == 0 and out["n_input"] == n == out["counts"]["not_run"] and out["one_to_one"]
    assert set(out["counts"]["not_run_by_code"]) <= {"no_code_location", "env_unavailable", "outcome_unsupported",
                                                     "witness_unusable", "not_attempted"}   # not_attempted: checked out, no --run-agent
    assert cli.main(["test", "sparta", "--results-root", str(tmp_path), "--strict"]) in (0, e2e.EXIT_STRICT)


def test_failed_agent_rerun_keeps_the_earlier_valid_test(toy, monkeypatch):
    _run(toy)                                                  # toy-F1 is tested from the archived package
    before = _records(toy)["toy-F1"]
    assert before.status == "tested"
    monkeypatch.setattr(e2e, "_agent_run", lambda *a, **k: (None, {"run_id": "x", "tokens": 1, "wall_s": 1}))
    # toy-F5 has no package: the agent is asked for it and fails; toy-F1 is re-run from an empty root and fails too
    out = _run(toy, attempts_roots=[toy["root"] / "empty"], run_agent=True, only=["toy-F1", "toy-F5"])
    r = _records(toy)
    assert r["toy-F5"].not_run.code == "agent_failed"
    assert r["toy-F1"].status == "tested" and r["toy-F1"].verdict == before.verdict
    assert "last_agent_rerun" in r["toy-F1"].provenance
    assert out["one_to_one"]


def test_other_effects_get_a_reason_that_says_what_would_be_needed():
    from checklimits.agent_batch import describe_other
    assert "reference implementation" in describe_other("Static discrepancy hypothesis, not a confirmed runtime effect", "")
    assert "assigns a value" in describe_other("", "gres_config = os.getenv('X', '4')")
    assert "assigns a value" in describe_other("", "self.ok &= y is not None")
    assert "warning" in describe_other("", "warnings.warn('triton too old')")
    assert "no raise in its body" in describe_other("", "if a > b:")
    assert "returns False" in describe_other("", "ConstraintCheck.true(x is None, 'msg')")
    assert "nothing to observe" in describe_other("", "")


def test_find_attempts_works_for_a_root_below_a_directory_called_scratch(toy, tmp_path):
    root = tmp_path / "scratch" / "staged"
    shutil.copytree(toy["archive"], root)
    assert list(e2e.find_attempts([root])) == ["toy-F1"]
    # a nested scratch directory below the root is still skipped (agent run workspaces are not packages to judge)
    shutil.copytree(toy["archive"] / "F1-run" / "attempt", root / "scratch" / "x" / "attempt")
    assert len(e2e.find_attempts([root])["toy-F1"]) == 1


def test_a_branch_verdict_says_only_that_the_branch_was_taken():
    from checklimits.testreport import _verdict_text
    assert "what the claim says happens after the branch was not checked" in _verdict_text("yes", "path_change")
    assert "exception is raised at the location" in _verdict_text("yes", "reject")
    assert "oracle was shown to see it" in _verdict_text("no", "reject")
    assert _verdict_text("inconclusive", None).startswith("no verdict")


def test_provision_flag_builds_the_environment_then_checks_again(toy, monkeypatch):
    from checklimits import provision as pv
    calls = []

    def fake(name, repo, commit=None, **kw):
        calls.append((name, repo.name, commit, kw.get("run_tests")))
        return {"status": "ok", "reasons": []}
    monkeypatch.setattr(pv, "provision", fake)
    out = _run(toy, python="/nonexistent/python", provision=True)
    env = json.loads((toy["results"] / "tests" / "toy" / "ENV.json").read_text())
    assert calls == [("toy", "repo", toy["commit"], False)]
    assert env["status"] == "not_ok" and env["provisioned"]["status"] == "ok" and any("does not exist" in r for r in env["provisioned"]["before"])
    assert out["one_to_one"]
    calls.clear()
    _run(toy, provision=True)                     # the environment is fine: nothing is provisioned
    assert calls == []


def test_provision_failure_is_recorded_not_raised(toy, monkeypatch):
    from checklimits import provision as pv
    monkeypatch.setattr(pv, "provision", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("pip exploded")))
    out = _run(toy, python="/nonexistent/python", provision=True)
    env = json.loads((toy["results"] / "tests" / "toy" / "ENV.json").read_text())
    assert env["provisioned"]["status"] == "error" and "pip exploded" in env["provisioned"]["reasons"][0] and out["one_to_one"]


def test_describe_other_survives_a_comment_only_snippet():
    from checklimits.agent_batch import describe_other
    assert describe_other("", "# just a comment") .startswith("the target statement")
