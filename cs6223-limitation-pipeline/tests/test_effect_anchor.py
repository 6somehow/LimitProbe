"""Effect labels must fit the statement they point at (codeside/effect_anchor.py)."""

from pathlib import Path

from codeside.effect_anchor import check_effect, check_effects
from schema.models import CodeLocation, Condition, Limitation

REPO = Path(__file__).parent / "fixtures"
FILE = "effect_module.py"
LINES = (REPO / FILE).read_text().splitlines()


def line_of(text: str) -> int:
    return next(i for i, l in enumerate(LINES, 1) if l.strip().startswith(text))


def lim(text: str, effect: str, cond: str = "c") -> Limitation:
    loc = CodeLocation(file=FILE, line_start=line_of(text), function=f"{FILE}::run", snippet=text)
    return Limitation(limitation_id="L1", artifact_id="a", origin="code", condition_text=cond,
                      condition=Condition(expr=cond), effect_type=effect, effect_text="e", code_evidence=[loc],
                      provenance="llm")


def test_labels_that_fit_are_kept():
    for text, effect in [("assert x >= 0", "reject"), ("if x > 100", "reject"), ("while retries > 3", "path_change"),
                         ("if mode == ", "path_change"), ("if mode == ", "state"), ("level = ", "other")]:
        out, rec = check_effect(lim(text, effect), REPO)
        assert rec is None and out.effect_type == effect, text


def test_reject_on_a_branch_without_raise_becomes_other():
    out, rec = check_effect(lim("while retries > 3", "reject"), REPO)
    assert out.effect_type == "other" and rec["action"] == "relabelled"
    assert out.code_evidence[0].line_start == line_of("while retries > 3")
    assert "no raise in its body" in out.notes


def test_reject_on_a_call_or_assignment_becomes_other():
    out, rec = check_effect(lim("check(x != 7", "reject"), REPO)
    assert out.effect_type == "other" and "callee" in rec["reason"]
    out, rec = check_effect(lim("level = ", "reject"), REPO)
    assert out.effect_type == "other" and "callee" in rec["reason"]  # os.getenv is a call too


def test_reject_on_except_header_moves_to_the_raise():
    out, rec = check_effect(lim("except ValueError", "reject"), REPO)
    assert out.effect_type == "reject" and rec["action"] == "moved"
    assert out.code_evidence[0].line_start == line_of("raise e") and out.code_evidence[0].snippet == "raise e"


def test_path_change_in_a_branch_body_moves_to_the_branch_with_the_same_test():
    out, rec = check_effect(lim("x = x + 1", "path_change", cond="mode == 'fast'"), REPO)
    assert rec["action"] == "moved" and out.effect_type == "path_change"
    assert out.code_evidence[0].line_start == line_of("elif mode == ")
    assert out.code_evidence[0].snippet == "if mode == 'fast':"


def test_path_change_on_a_non_branch_with_another_condition_becomes_other():
    out, rec = check_effect(lim("x = x + 1", "path_change", cond="x > 5"), REPO)
    assert out.effect_type == "other" and "not a branch decision" in rec["reason"]
    out, _ = check_effect(lim("level = ", "state", cond="level != '1'"), REPO)
    assert out.effect_type == "other"


def test_missing_repo_or_file_changes_nothing():
    l = lim("level = ", "reject")
    assert check_effects([l], None) == ([l], [])
    assert check_effect(l, REPO / "nowhere")[1] is None


def test_moved_target_is_reported_as_effect_location_in_the_hint():
    from codeside.integrate import Context, Rules, integrate
    fixed, recs = check_effects([lim("except ValueError", "reject")], REPO)
    ctx = Context(repo=REPO, effect_moves={r["limitation_id"]: r for r in recs if r["action"] == "moved"})
    (f,), _ = integrate("a", fixed, [], [], None, Rules(), ctx)
    h = f.witness_hint
    assert h["effect_location"] == f"{FILE}:{line_of('raise e')}" == h["location"]
    assert h["labelled_location"] == f"{FILE}:{line_of('except ValueError')}"


def test_snippets_are_written_in_one_form():
    from codeside.effect_anchor import canonical_snippet, normalise_snippet
    import ast
    tree = ast.parse((REPO / FILE).read_text())
    at = lambda text: next(n for n in ast.walk(tree) if isinstance(n, ast.stmt) and n.lineno == line_of(text))
    assert canonical_snippet(at("assert x >= 0")) == "assert x >= 0"  # message dropped
    assert canonical_snippet(at("elif mode == ")) == "if mode == 'fast':"
    l = lim("if x > 100", "reject").model_copy()
    l.code_evidence[0].snippet = "if ("
    assert normalise_snippet(l, REPO).code_evidence[0].snippet == "if x > 100:"
