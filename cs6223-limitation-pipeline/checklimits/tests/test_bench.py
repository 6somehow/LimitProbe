"""Unit tests of the benchmark bookkeeping (the cases themselves run via `python -m checklimits bench`)."""
import ast

import pytest

from checklimits import bench
from checklimits.models import PIPELINE_ROOT

SRC = PIPELINE_ROOT / "third_party" / "FlexPrefill" / bench.SRC
needs_repo = pytest.mark.skipif(not SRC.exists(), reason="FlexPrefill checkout missing")


def row(claim, final, level="L1", acceptable=("yes",), max_level=None):
    r = {"claim_true": claim, "final_verdict": final, "level": level, "acceptable": list(acceptable), "max_level": max_level}
    r["class"] = bench.classify(r)
    r["ok"] = bench.is_ok(r)
    return r


def test_classes():
    assert [row(True, "yes")["class"], row(False, "yes")["class"], row(True, "no")["class"], row(False, "no")["class"],
            row(True, "inconclusive")["class"], row(True, None)["class"]] == ["TP", "FP", "FN", "TN", "ABSTAIN", "ERROR"]


def test_ok_checks_acceptable_set_and_level_cap():
    assert row(True, "yes")["ok"]
    assert not row(True, "no")["ok"]
    assert row(True, "yes", "L1", max_level="L1")["ok"] and not row(True, "yes", "L3", max_level="L1")["ok"]


def test_summary_counts_levels_and_flags_false_positives():
    rows = [row(True, "yes", "L3"), row(True, "yes", "L3"), row(False, "yes", "L3", acceptable=("no",)),
            row(False, "no", "L1", acceptable=("no",)), row(True, "inconclusive", "n/a", acceptable=("inconclusive",))]
    s = bench.summarize([{**r, "id": f"c{i}"} for i, r in enumerate(rows)])
    assert s["by_class"] == {"TP": 2, "FP": 1, "TN": 1, "ABSTAIN": 1}
    assert s["false_positives"] == ["c2"] and s["decided"] == 4 and s["abstained"] == 1
    assert s["by_level"]["L3"]["accuracy"] == pytest.approx(2 / 3, abs=1e-3) and s["by_level"]["L1"]["accuracy"] == 1.0
    assert s["by_level"]["n/a"]["decided"] == 0 and s["unacceptable"] == ["c2"]


@needs_repo
@pytest.mark.parametrize("finding", ["F01", "F04", "F07"])
def test_every_edit_applies_once_and_still_parses(finding):
    src = SRC.read_text()
    assert src.split("\n")[bench.TARGET_LINE[finding] - 1] == bench.TARGET[finding]
    for name, edit in [("delete", bench._delete_target), ("relax", bench._replace_target(bench.RELAXED)),
                       ("invert", bench._replace_target(bench.INVERTED)), ("otherexc", bench._replace_target(bench.OTHER_EXC)),
                       ("shift", bench._shift_target), ("collide", bench._collide_target)]:
        new = edit(finding, src)
        ast.parse(new)
        assert new != src, name


@needs_repo
def test_cases_are_well_formed():
    cases = bench.build_cases()
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids)) and len(cases) == 31 + len(bench.step4_cases()) == 82
    assert all(c.claim_true or "yes" not in c.acceptable for c in cases)   # a false claim is never acceptable as `yes`


@pytest.mark.parametrize("finding", sorted(bench.STEP4_TARGETS))
def test_step4_edits_change_exactly_the_target_line_and_still_parse(finding):
    art, file, line, text, kind = bench.STEP4_TARGETS[finding]
    repo = bench.ARTIFACTS[art]["repo"]
    if not (repo / file).exists():
        pytest.skip(f"{repo} not checked out")
    src = (repo / file).read_text()
    lines = src.split("\n")
    assert lines[line - 1] == text, "the pinned commit has a different statement on this line"
    ops = ("delete", "invert", "otherexc") if kind == "reject" else ("false", "invert", "always")
    for op in ops:
        new = bench._gen_edit(op)(finding, src)
        ast.parse(new)
        changed = [i + 1 for i, (a, b) in enumerate(zip(lines, new.split("\n"))) if a != b]
        assert changed == [line], (op, changed)
    for edit in (bench._shift_target, bench._collide_generic):
        ast.parse(edit(finding, src))


def test_generated_edits_read_the_condition_with_the_parser():
    assert bench._stmt_parts('        assert a == 1, "msg, with a comma"') == ("        ", "assert", "a == 1")
    assert bench._stmt_parts("    elif x in (1, 2):") == ("    ", "elif", "x in (1, 2)")
    assert bench._stmt_parts("if f(a, b):") == ("", "if", "f(a, b)")
