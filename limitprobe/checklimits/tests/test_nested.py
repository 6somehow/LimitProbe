"""Region.location.function names a nested function 'outer.inner'; CPython's co_qualname says 'outer.<locals>.inner'.
Found by the batch (flexprefill-F020: patch_vllm_model.flex_prefill_forward)."""
import pytest

from checklimits import fidelity, harness
from checklimits.harness import RunOptions
from checklimits.tracer import norm_qual
from toyhelper import build

FULL = RunOptions(repeats=2)


def test_norm_qual():
    assert norm_qual("outer.<locals>.inner") == "outer.inner"
    assert norm_qual("A.m") == "A.m" and norm_qual("a.<locals>.b.<locals>.c") == "a.b.c"


def test_functions_by_qualname_uses_dotted_names():
    import ast
    fns = fidelity.functions_by_qualname(ast.parse("def a():\n    def b():\n        def c(): pass\nclass K:\n    def m(self): pass\n"))
    assert set(fns) == {"a", "a.b", "a.b.c", "K.m"}


def test_nested_target_is_reached_intact_and_judged(tmp_path):
    from profile_helper import QUICK
    drv = "from toypkg.core import entry\n\n\ndef run(inputs):\n    return entry(inputs['n'], inputs['m'])\n"
    b = build(tmp_path, with_ext=False, kind="nested", pos={"n": 2, "m": 1}, neg={"n": 1, "m": 1}, driver_src=drv)
    r = harness.run_attempt(b["attempt"], pipeline_root=b["root"], options=RunOptions.fast(), profile=QUICK)["report"]
    assert (r.verdict, r.final_verdict) == ("yes", "yes")
    assert r.positive.target_reached and r.fidelity.ast_diff.target_statement_intact
    st = {d.id: d.status for d in r.confidence.defeaters}
    assert st["D1"] == "eliminated" and st["D11"] == "eliminated" and st["D12"] == "eliminated"
    assert r.fidelity.entry_index == 0
    assert r.positive.coverage.lines_executed > 0          # coverage found the nested function under its dotted name
