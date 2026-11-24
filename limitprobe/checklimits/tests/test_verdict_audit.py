import pytest

from checklimits import audit, verdict
from checklimits.models import ExceptionInfo, Observation, OracleDecl, TargetHit


def obs(role, effect, exc=None, hits=None, note=""):
    return Observation(role=role, inputs={}, status="exception" if exc else "ok", exception=exc,
                       target_reached=bool(hits), target_hits=hits or [], effect=effect, effect_note=note,
                       observed_text="")


@pytest.mark.parametrize("p,n,verdict_,result", [
    (True, False, "yes", "confirmed"),
    (False, False, "no", "refuted"),
    (True, True, "inconclusive", "test_error"),
    (False, True, "inconclusive", "test_error"),
    (None, False, "inconclusive", "test_error"),
    (True, None, "inconclusive", "test_error"),
])
def test_table(p, n, verdict_, result):
    r = verdict.decide(obs("positive", p), obs("negative", n))
    assert (r.verdict, r.exec_result) == (verdict_, result)


def test_unsupported_outcome_is_not_run():
    r = verdict.decide(obs("positive", None, note="outcome 'fallback' not supported in P1"), obs("negative", None), False)
    assert (r.verdict, r.exec_result) == ("inconclusive", "not_run")


LOC = "a/b.py:10"


def test_tier_verification():
    o4 = OracleDecl(tier="O4", type="exception", spec="AssertionError raised at a/b.py:10", signal_location=LOC)
    assert verdict.verify_tier(o4, LOC) == "O4"
    assert verdict.verify_tier(o4.model_copy(update={"signal_location": "a/b.py:11"}), LOC) == "O3"
    assert verdict.verify_tier(o4.model_copy(update={"spec": "something raised"}), LOC) == "O2"
    assert verdict.verify_tier(o4.model_copy(update={"tier": "O3"}), LOC) == "O3"  # never raised above declared
    assert verdict.verify_tier(OracleDecl(tier="O4", type="differential", spec="x"), LOC) == "O3"
    assert verdict.expected_exception_type(o4) == "AssertionError"


@pytest.mark.parametrize("text,expect", [
    ("AssertionError at :1836", ("exc", "AssertionError", 1836)),
    ("AssertionError raised at flex_prefill/ops/x.py:1824", ("exc", "AssertionError", 1824)),
    ("no exception at :1836", ("none", None, 1836)),
    ("No exception", ("none", None, None)),
    ("it exploded", ("unparsed", None, None)),
])
def test_parse_observed(text, expect):
    assert audit.parse_observed(text) == expect


def test_observed_matching_is_location_scoped():
    later = ExceptionInfo(type="RuntimeError", message="x", raised_at="triton/driver.py:20")
    n = obs("negative", False, exc=later)
    assert audit.observed_matches("no exception at :10", n)       # failure elsewhere is allowed
    assert not audit.observed_matches("no exception", n)           # unscoped claim: any exception contradicts it
    at = ExceptionInfo(type="AssertionError", message="", raised_at="a/b.py:10")
    p = obs("positive", True, exc=at)
    assert audit.observed_matches("AssertionError at a/b.py:10", p)
    assert not audit.observed_matches("AssertionError at :11", p)
    assert not audit.observed_matches("ValueError at :10", p)
    assert not audit.observed_matches("no exception at :10", p)


def test_cond_value_none_when_not_evaluable():
    h = TargetHit(seq=1, outcome="true", condition_value=None, condition_error="NameError")
    assert audit.cond_value(obs("positive", True, hits=[h]), True) is None
    assert audit.cond_value(obs("positive", False), True) is False  # target never reached
