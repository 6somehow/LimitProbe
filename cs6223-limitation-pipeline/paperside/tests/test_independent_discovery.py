import unittest
from contextlib import contextmanager


@contextmanager
def raises_value_error(match=None):
    with unittest.TestCase().assertRaisesRegex(ValueError, match or ".*"):
        yield

from paperprobe.independent_discovery import validate_candidates, validate_local, validate_merge


PAGES = ["while S⁄= /0 do\nreturn G;"]


def candidate(name="Propagation"):
    return dict(name=name, description="Process the worklist", pages=[1], boundary="Worklist loop",
                evidence=[dict(page=1, quote="while S ≠ ∅ do")])


def merge_row(members):
    return dict(candidate(), members=members, merge_reason="Same control flow", parent_name=None)


def test_visual_quotes_do_not_discard_candidates():
    row = validate_candidates(dict(mechanisms=[candidate()]), "A", PAGES)[0]
    assert row["id"] == "A01"
    assert row["mechanical"][0]["exact_text_match"] is False


def test_merge_retains_supported_singletons():
    candidates = [dict(id="A01"), dict(id="B01")]
    first, second = merge_row(["A01"]), merge_row(["B01"])
    second["name"] = "Code generation"
    result = validate_merge(dict(mechanisms=[first, second], exclusions=[]), candidates, PAGES)
    assert len(result["mechanisms"]) == 2


def test_merge_cannot_silently_lose_invent_or_repeat_candidates():
    for members in [["A01"], ["A01", "B01", "Z01"], ["A01", "B01", "A01"]]:
        with raises_value_error():
            validate_merge(dict(mechanisms=[merge_row(members)], exclusions=[]),
                           [dict(id="A01"), dict(id="B01")], PAGES)


def test_parent_cycles_rejected():
    row = merge_row(["A01"])
    row["parent_name"] = row["name"]
    with raises_value_error(match="cyclic"):
        validate_merge(dict(mechanisms=[row], exclusions=[]), [dict(id="A01")], PAGES)


def local_result():
    return dict(obligation_checks=[dict(id="O1", status="covered", behavior_ids=["B1"], reason="same clause")],
                behavior_reviews=[dict(id="B1", issues=[], replacements=[], reason="atomic")], additions=[])


def test_local_review_requires_both_sides_accounted_for():
    raw = local_result()
    assert validate_local(raw, [dict(id="O1")], [dict(id="B1")], PAGES, [1])["semantic_review"] == "pending"
    raw["behavior_reviews"] = []
    with raises_value_error(match="behavior_reviews"):
        validate_local(raw, [dict(id="O1")], [dict(id="B1")], PAGES, [1])


def test_local_covered_needs_real_behavior_and_additions_need_visible_evidence():
    raw = local_result()
    raw["obligation_checks"][0]["behavior_ids"] = []
    with raises_value_error(match="supporting"):
        validate_local(raw, [dict(id="O1")], [dict(id="B1")], PAGES, [1])
    raw = local_result()
    raw["additions"] = [dict(obligation_ids=["O1"], evidence=[dict(page=2, quote="X")])]
    with raises_value_error(match="evidence"):
        validate_local(raw, [dict(id="O1")], [dict(id="B1")], PAGES, [1])


def test_local_addition_cannot_duplicate_covered_obligation():
    raw = local_result()
    raw["additions"] = [dict(obligation_ids=["O1"], evidence=[dict(page=1, quote="return G;")])]
    result = validate_local(raw, [dict(id="O1")], [dict(id="B1")], PAGES, [1])
    assert result['consistency_flags'][0]['addition_index'] == 1


def test_exclusion_is_explicit_and_grounded_in_seen_page():
    raw = dict(mechanisms=[merge_row(["A01"])], exclusions=[dict(id="B01", reason="Background only",
               evidence=[dict(page=1, quote="return G;")])])
    result = validate_merge(raw, [dict(id="A01"), dict(id="B01")], PAGES)
    assert result["exclusions"][0]["id"] == "B01"


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(v) for k,v in globals().items() if k.startswith("test_") and callable(v))
