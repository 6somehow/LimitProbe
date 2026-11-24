"""Stand-in fidelity checks (simcheck.py): agrees, disagrees, vacuous, error."""
import sys
from pathlib import Path

import pytest

from checklimits import simcheck as S
from checklimits.models import MockDecl


SIM = '''
import numpy as np
def softmax_sim(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)
def softmax_wrong(x):
    return np.exp(x) / 2.0
'''

CHECK = '''
import numpy as np
def good(sim):
    rng = np.random.default_rng(0)
    x = rng.normal(size=(4, 8))
    y = sim(x)
    ref = np.exp(x) / np.exp(x).sum(axis=-1, keepdims=True)
    return {"ok": bool(np.allclose(y, ref, atol=1e-6)), "detail": "matches the closed form", "kind": "numeric"}
def vacuous(sim):
    sim(np.zeros((2, 2)))
    return {"ok": True, "detail": "calls it and says fine", "kind": "numeric"}
def broken(sim):
    raise RuntimeError("check crashed")
'''


def _decl(impl, check):
    return MockDecl(symbol=f"lib.{impl}", kind="patch", reason="r", behavior="sim", impl=f"sim.py::{impl}",
                    sim_class="independent_native", sim_check=f"check.py::{check}")


def _run(tmp_path, impl, check):
    (tmp_path / "sim.py").write_text(SIM)
    (tmp_path / "check.py").write_text(CHECK)
    repo = tmp_path / "repo"
    repo.mkdir()
    d = _decl(impl, check)
    return S.run_sim_checks([d], tmp_path, repo, sys.executable, scratch=tmp_path / "scr")[d.symbol]


def test_faithful_stand_in_agrees(tmp_path):
    r = _run(tmp_path, "softmax_sim", "good")
    assert r["status"] == "agrees", r


def test_wrong_stand_in_disagrees(tmp_path):
    assert _run(tmp_path, "softmax_wrong", "good")["status"] == "disagrees"


def test_check_that_cannot_see_errors_is_vacuous(tmp_path):
    r = _run(tmp_path, "softmax_sim", "vacuous")
    assert r["status"] == "vacuous" and r["corrupted_passed"]


def test_crashing_check_is_error(tmp_path):
    assert _run(tmp_path, "softmax_sim", "broken")["status"] == "error"


def test_mock_without_sim_check_is_not_listed(tmp_path):
    d = MockDecl(symbol="lib.x", kind="patch", reason="r", behavior="sim", impl="sim.py::softmax_sim")
    assert S.run_sim_checks([d], tmp_path, tmp_path, sys.executable) == {}
