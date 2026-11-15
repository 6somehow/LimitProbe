"""The one-command pipeline (pipeline/run.py): stage gating that must hold without running any model."""

from types import SimpleNamespace

import pytest

from pipeline.run import STAGES, Paths, StageError, main, stage_paper


def test_stage_order_runs_code_before_paper_and_3b_after():
    # finalize_handoff (paper side) reads the code-side limitations; 3b needs the paper side
    assert STAGES.index("code") < STAGES.index("paper") < STAGES.index("verify3b") < STAGES.index("step4")


def test_unknown_artifact_is_a_clear_stop():
    with pytest.raises(StageError, match="pipeline init"):
        Paths("no_such_artifact")


def test_paper_side_needs_explicit_opt_in():
    P = Paths("nnsmith")
    P.handoff = P.handoff.parent / "zz_missing"
    with pytest.raises(StageError, match="--run-paper-side"):
        stage_paper(P, SimpleNamespace(run_paper_side=False))


def test_package_roots_default_and_override():
    assert Paths("infinigen").package_roots([]) == ["--package-root", "speedup/infinigen",
                                                    "--package-root", "speedup/flexgen"]
    assert Paths("nnsmith").package_roots(["src"]) == ["--package-root", "src"]


def test_init_refuses_to_overwrite(capsys):
    with pytest.raises(SystemExit, match="exists"):
        main(["init", "--id", "nnsmith", "--title", "t", "--paper-url", "u", "--repo-url", "r", "--commit", "c",
              "--domain", "d", "--entry", "a.py::f"])


# --------------------------------------------------------------------------- test stage (W6)
import json  # noqa: E402
import subprocess  # noqa: E402

import pipeline.run as run  # noqa: E402

_REAL_PATHS = run.Paths


def _args(**kw):
    base = dict(run_agent=False, only=None, workers=3, fast=False, strict=False, skip_envcheck=False, python=None)
    return SimpleNamespace(**{**base, **kw})


def test_last_json_reads_a_multiline_summary_after_other_output():
    text = 'progress {not json\n{\n "artifact": "x",\n "exit_code": 0\n}\n'
    assert run.last_json(text) == {"artifact": "x", "exit_code": 0}
    assert run.last_json("no json here") is None


def test_command_follows_the_contract():
    cmd = run.test_cmd("nnsmith", _args(run_agent=True, strict=True, only=["nnsmith-F004"]))
    assert cmd[1:5] == ["-m", "checklimits", "test", "nnsmith"]
    assert cmd[cmd.index("--results-root") + 1] == str(run.ROOT / "results")
    assert "--run-agent" in cmd and "--strict" in cmd and cmd[-2:] == ["--only", "nnsmith-F004"]


def _fake(monkeypatch, tmp_path, code, summary):
    seen = {}

    def fake_run(cmd, cwd, env, stdout, text):
        seen["cwd"] = cwd
        return subprocess.CompletedProcess(cmd, code, stdout="log line\n" + json.dumps(summary, indent=1) + "\n")
    monkeypatch.setattr(run.subprocess, "run", fake_run)
    monkeypatch.setattr(run, "Paths", lambda aid: _paths(tmp_path, aid))
    return seen


def _paths(tmp_path, aid):
    P = _REAL_PATHS.__new__(_REAL_PATHS)
    P.aid, P.results = aid, tmp_path / "results"
    P.step4 = run.ROOT / "results/step4/nnsmith/limitations_for_tests.json"
    P.test_index, P.report = P.results / "tests" / aid / "index.json", run.ROOT / "results/report" / aid / "LIMITATIONS.md"
    return P


def test_runs_in_checklimits_and_accepts_exit_0(monkeypatch, tmp_path):
    seen = _fake(monkeypatch, tmp_path, 0, {"artifact": "nnsmith", "n_input": 38, "one_to_one": True, "counts": {},
                                            "exit_code": 0})
    assert run.test("nnsmith", _args())["n_input"] == 38
    assert seen["cwd"] == run.CHECKLIMITS
    assert (tmp_path / "results/tests/nnsmith/pipeline_test.log").read_text().startswith("log line")


@pytest.mark.parametrize("code,match", [(2, "input error"), (3, "one to one"), (4, "report is written"),
                                        (1, "unhandled")])
def test_nonzero_exit_codes_stop_with_the_contract_reason(monkeypatch, tmp_path, code, match):
    _fake(monkeypatch, tmp_path, code, {"error": "x", "one_to_one": code != 3, "exit_code": code})
    with pytest.raises(StageError, match=match):
        run.test("nnsmith", _args())


def test_status_reports_test_state(tmp_path):
    P = _paths(tmp_path, "nnsmith")
    P.report = tmp_path / "LIMITATIONS.md"
    assert run.test_state(P)[0] == "todo"
    P.test_index.parent.mkdir(parents=True)
    P.report.write_text("# r\n")
    idx = {"one_to_one": True, "n_input": 38, "n_records": 38, "counts": {"tested": 1, "not_run_by_code": {"x": 37}},
           "findings_sha256": run.sha256(P.step4)}
    P.test_index.write_text(json.dumps(idx))
    assert run.test_state(P)[0] == "done"
    P.test_index.write_text(json.dumps({**idx, "findings_sha256": "old"}))
    assert run.test_state(P)[0] == "stale"
    P.test_index.write_text(json.dumps({**idx, "one_to_one": False}))
    assert run.test_state(P)[0] == "todo"
