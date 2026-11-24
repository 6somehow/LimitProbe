"""Targets that run at import time (Region.location.function == '<module>'): the AST check must find them, and the
module dictionary that serves as the frame's locals must not leak absolute paths into the canonical trace.
Found by the NNSmith batch (nnsmith-F011: `if FLOPS_LIM == "off":` at module level)."""
import ast
import json

from checklimits import fidelity, harness
from checklimits.harness import RunOptions
from checklimits.profile import Profile
from toyhelper import build

DRIVER = '''import importlib
import os

import toypkg.core as core


def run(inputs):
    os.environ["TOY_LIMIT"] = inputs["limit"]
    importlib.reload(core)           # the target is module-level code: re-run it under the tracer
    return core.entry(0, 0)
'''
KW = dict(kind="module", driver_src=DRIVER, pos={"limit": "off"}, neg={"limit": "auto"},
          design_extra={"boundary_variable": "limit"}, witness={"limit": "off"})


def test_module_level_statements_helper():
    tree = ast.parse("import os\nX = 1\nif X:\n    Y = 2\ndef f():\n    Z = 3\nclass K:\n    W = 4\n")
    got = [type(s).__name__ for s in fidelity.module_level_statements(tree)]
    assert got.count("Assign") == 2 and "If" in got            # X = 1, Y = 2; not Z or W
    assert "Import" in got


def test_ast_diff_finds_a_module_level_target(tmp_path):
    b = build(tmp_path, with_ext=False, kind="module")
    ad = fidelity.ast_diff(b["repo"], b["commit"], ["toypkg/core.py::<module>"], "toypkg/core.py", b["line"],
                           'if LIMIT == "off":', "<module>")
    assert ad.target_statement_intact and ad.snippet_matches_region and ad.git_status_clean
    assert ad.statements_total > 0 and ad.statements_changed == 0


def test_ast_diff_notices_an_edited_module_level_target(tmp_path):
    b = build(tmp_path, with_ext=False, kind="module")
    core = b["repo"] / "toypkg" / "core.py"
    core.write_text(core.read_text().replace('LIMIT == "off"', 'LIMIT == "none"'))
    ad = fidelity.ast_diff(b["repo"], b["commit"], ["toypkg/core.py::<module>"], "toypkg/core.py", b["line"],
                           'if LIMIT == "off":', "<module>")
    assert not ad.target_statement_intact


def test_module_level_branch_end_to_end_with_replay(tmp_path):
    b = build(tmp_path, with_ext=False, **KW)
    opts = RunOptions(probe_effect=False, repeats=2, bva=False, mutation=False, replay=True)
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=opts, profile=Profile(n_rep=2))["report"]
    st = {d.id: d.status for d in r.confidence.defeaters}
    assert (r.verdict, r.final_verdict) == ("yes", "yes")
    assert r.positive.effect and not r.negative.effect and r.positive.target_kind == "if"
    assert st["D11"] == "eliminated" and st["D12"] == "eliminated"
    assert r.checks.replay.ok and st["D9"] == "eliminated"            # the replay runs in a different directory
    for h in r.positive.target_hits + r.negative.target_hits:
        assert not any(k.startswith("__") for k in h.locals)          # module bookkeeping is not captured
        assert not any(str(b["repo"]) in v for v in h.locals.values())


def test_captured_locals_never_contain_the_repo_path(tmp_path):
    b = build(tmp_path, with_ext=False, kind="module", driver_src=DRIVER, pos={"limit": "off"}, neg={"limit": "auto"},
              design_extra={"boundary_variable": "limit"}, witness={"limit": "off"})
    ctx = harness._Ctx(b["attempt"], b["root"])
    raw, _ = ctx.run("positive", {"limit": "off"})
    assert str(b["repo"]) not in json.dumps(raw["trace"]["target_hits"])
