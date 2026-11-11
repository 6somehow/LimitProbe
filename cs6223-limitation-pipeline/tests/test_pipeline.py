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
