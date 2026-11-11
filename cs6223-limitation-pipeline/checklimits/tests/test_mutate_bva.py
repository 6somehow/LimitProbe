import ast
import textwrap

import pytest

from checklimits import bva, mutate
from checklimits.models import AgentForm, ScaleDecl

SRC = textwrap.dedent('''\
    def f(a, b):
        x = 1
        assert a == 1 and b < 5, "msg"
        return x
''')


def ops(mutants):
    return [m.operator for m in mutants]


def test_assert_mutants_keep_line_count_and_parse():
    ms = mutate.generate(SRC, 3)
    assert len(ms) == 8
    assert set(ops(ms)) >= {"negate_condition", "delete_statement", "swap_comparison ==->!=", "swap_comparison <-><="}
    for m in ms:
        assert m.source.count("\n") == SRC.count("\n") and m.line == 3
        ast.parse(m.source)
        assert m.source != SRC
        assert m.source.splitlines()[0] == SRC.splitlines()[0] and m.source.splitlines()[3] == SRC.splitlines()[3]
    neg = next(m for m in ms if m.operator == "negate_condition")
    assert neg.mutated == 'assert not (a == 1 and b < 5), "msg"'
    dele = next(m for m in ms if m.operator == "delete_statement")
    assert dele.mutated == "pass"


def test_swap_picks_the_right_operator_token():
    src = "def f(a, b):\n    if a <= b and a != 2:\n        return 1\n    return 0\n"
    ms = {m.operator: m for m in mutate.generate(src, 2)}
    assert ms["swap_comparison <=-><"].mutated == "if a < b and a != 2:"
    assert ms["swap_comparison !=->=="].mutated == "if a <= b and a == 2:"
    assert "delete_statement" not in ms           # only assert / raise can be deleted


def test_multiline_assert_is_deleted_without_shifting_lines():
    src = 'def f(a):\n    assert (a ==\n            1), "m"\n    return a\n'
    dele = next(m for m in mutate.generate(src, 2) if m.operator == "delete_statement")
    assert dele.source.count("\n") == src.count("\n") and dele.source.splitlines()[3] == "    return a"
    ast.parse(dele.source)


def test_non_decision_statements_have_no_mutants():
    assert mutate.generate(SRC, 2) == []
    assert mutate.generate(SRC, 99) == []


def test_raise_can_be_deleted():
    src = "def f(a):\n    raise ValueError(a)\n"
    assert ops(mutate.generate(src, 2)) == ["delete_statement"]


def test_unicode_before_the_expression_does_not_shift_offsets():
    src = 'def f(a):\n    assert a == 1, "不支持"\n'
    m = next(m for m in mutate.generate(src, 2) if m.operator.startswith("swap"))
    assert m.mutated == 'assert a != 1, "不支持"'


# --- bva ---------------------------------------------------------------------------------------------
def form(pos, neg, var, scale=None):
    d = {"test_id": "t", "finding_id": "f", "strategy": "S0",
         "design": {"witness_source": "w", "positive_input": pos, "negative_input": neg, "boundary_variable": var,
                    "scale": scale,
                    "oracle": {"tier": "O4", "type": "exception", "spec": "AssertionError", "signal_location": "a:1"},
                    "expected": {"positive": "p", "negative": "n"}},
         "execution": {"entry_called": "a::b"},
         "claims": {"target_reached": True, "decision_outcomes_seen": [], "condition_true_on_positive": True,
                    "condition_false_on_negative": True, "positive_observed": "x", "negative_observed": "y"}}
    return AgentForm.model_validate(d)


def test_plan_without_scale_probes_neighbours_of_the_negative():
    cases, var, why = bva.plan(form({"x": 2}, {"x": 1}, "x"), {"x": 2}, 1)
    assert var == "x" and why == ""
    assert dict(cases) == {"pos_full": {"x": 2}, "neg_full": {"x": 1}, "neg+": {"x": 2}, "neg-": {"x": 0}}


def test_plan_scales_inputs_back_to_the_witness():
    sc = ScaleDecl(factor=0.125, scaled=["q", "k"], reason="r", invariance_argument="i")
    f = form({"q": 512, "k": 1024}, {"q": 512, "k": 512}, "k", sc)
    cases = dict(bva.plan(f, {"q": 4096, "k": 8192}, 1)[0])
    assert cases["pos_full"] == {"q": 4096, "k": 8192} and cases["neg_full"] == {"q": 4096, "k": 4096}
    assert cases["neg+"]["k"] == 4097 and cases["neg-"]["k"] == 4095


@pytest.mark.parametrize("pos,neg,var,fragment", [
    ({"x": 2, "y": 1}, {"x": 1, "y": 2}, "x", "differ in"),
    ({"x": 2.5}, {"x": 1.5}, "x", "not an integer"),
])
def test_plan_not_measurable(pos, neg, var, fragment):
    cases, v, why = bva.plan(form(pos, neg, var), None, 1)
    assert v is None and fragment in why and [c[0] for c in cases] == ["pos_full", "neg_full"]


def test_evaluate_patterns():
    inp = {"neg+": {"x": 2}, "neg-": {"x": 0}}
    both = bva.evaluate("x", {"pos_full": True, "neg_full": False, "neg+": True, "neg-": True}, inp, True, "")
    assert both.adjacent and "single point" in both.pattern
    one = bva.evaluate("x", {"neg+": True, "neg-": False}, inp, True, "")
    assert one.adjacent and "half-space" in one.pattern
    none = bva.evaluate("x", {"neg+": False, "neg-": False}, inp, True, "")
    assert none.adjacent is False and "NOT adjacent" in none.pattern
    undecided = bva.evaluate("x", {"neg+": True, "neg-": None}, inp, True, "")
    assert undecided.adjacent is None
    na = bva.evaluate("x", {"pos_full": True}, inp, False, "float")
    assert not na.applicable and na.adjacent is None and na.full_scale_positive is True
