"""Process confidence (codeside/process_confidence.py): one minimal repo, one case per rule."""
import json
import textwrap
from pathlib import Path

import pytest

from codeside.process_confidence import ProcessContext, assess, assess_all
from schema.models import Finding

SRC = textwrap.dedent('''\
    def entry(x, mode):
        assert x > 0
        if mode == "fast":
            return helper(x)
        y = x if x < 10 else 10
        return y


    def helper(d):
        if d not in {16, 32}:
            raise ValueError("bad d")
        return d


    def orphan(k):
        if k is None:
            return 0
        return k
''')
ENTRY = "pkg/mod.py::entry"


@pytest.fixture()
def pc(tmp_path: Path) -> ProcessContext:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg/mod.py").write_text(SRC)
    return ProcessContext(tmp_path, (".",), [ENTRY])


def lim(line, snippet, expr, function, effect="reject", provenance="ast", lid="CL-X001"):
    return {"limitation_id": lid, "origin": "code", "provenance": provenance, "effect_type": effect,
            "condition": {"expr": expr, "params": [], "path_prefix": []},
            "code_evidence": [{"file": "pkg/mod.py", "line_start": line, "line_end": line,
                               "function": f"pkg/mod.py::{function}", "snippet": snippet}]}


def record(l, status="solved", chain="entry_is_target", effect=None, review="unreviewed", ver="not_found", **hint):
    h = {"status": status, "condition": l["condition"]["expr"], "path_prefix": [], "call_chain_status": chain,
         "location": f"pkg/mod.py:{l['code_evidence'][0]['line_start']}", **hint}
    if chain in ("entry_is_target", "resolved"):
        h.setdefault("call_chain", [ENTRY])
    return {"finding_id": "t-F001", "effect_type": effect or l["effect_type"], "witness_hint": h, "review": review,
            "review_note": None, "limitations": [l],
            "verifications": [{"limitation_id": l["limitation_id"], "result": ver, "verifier": "llm:m",
                               "matching_evidence": [{"quote": "q"}] if ver != "not_found" else []}]}


def run(pc, rec):
    pc.register(rec["limitations"])
    return assess(rec, pc)


def states(block):
    return {k: c["status"] for k, c in block["checks"].items()}


def imp(block):
    return block["importance"]


def test_static_guard_on_the_main_path(pc):
    b = run(pc, record(lim(2, "assert x > 0", "not (x > 0)", "entry")))
    s = states(b)
    assert "level" not in b and b["calibrated"] is False  # the code side sets no level of its own
    assert [s[k] for k in ("C1", "C2", "C3", "C4", "C5", "C6")] == ["eliminated"] * 6
    assert s["C7"] == "residual"  # 3b not_found is an absence: never eliminated by a model, and never in the level
    assert s["C8"] == "open"
    assert imp(b)["path"]["decision_on"] == "main" and imp(b)["path"]["enclosing_conditions"] == []
    assert imp(b)["impact"]["guards"] == "rest_of_function" and imp(b)["impact"]["guarded_statements"] == 4
    assert imp(b)["coverage"] == {"measured": True, "function": ENTRY, "function_decisions": 2,
                             "function_decisions_listed": 1, "function_reached_from_entry": True}


def test_llm_route_without_repeated_runs_is_residual(pc):
    b = run(pc, record(lim(3, 'if mode == "fast":', 'mode == "fast"', "entry", "path_change", "llm")))
    assert states(b)["C5"] == "residual" and b["repeats"]["extraction_runs"]["measured"] is False
    assert imp(b)["impact"]["guards"] == "branch_body" and imp(b)["impact"]["guarded_statements"] == 1


def test_raise_in_a_branch_is_decided_by_the_branch_and_sits_on_a_side_path(pc):
    l = lim(11, "raise ValueError('bad d')", "d not in {16, 32}", "helper")
    sites = [{"caller": ENTRY, "callee": "pkg/mod.py::helper", "line": 4, "resolved_by": "name", "args": {"d": "x"}}]
    b = run(pc, record(l, chain="resolved", call_chain=[ENTRY, "pkg/mod.py::helper"], call_sites=sites))
    assert states(b)["C2"] == "eliminated" and "enclosing branch at line 10" in b["checks"]["C2"]["evidence"]
    assert imp(b)["path"]["decision_on"] == "side"  # helper is only called under `if mode == "fast"`
    assert imp(b)["path"]["conditional_call_sites"] and imp(b)["path"]["chain_depth"] == 1
    assert imp(b)["impact"]["call_sites_of_function"] == 1 and imp(b)["coverage"]["function_reached_from_entry"] is True


def test_condition_inside_a_statement(pc):
    b = run(pc, record(lim(5, "y = x if x < 10 else 10", "x >= 10", "entry", "other")))
    s = states(b)
    assert s["C2"] == "eliminated" and s["C6"] == "open"  # effect `other`: nothing a test can judge
    assert b["testability"]["testable"] is False and b["testability"]["expect_not_run"] == "outcome_unsupported"


def test_paraphrased_condition_is_residual_and_unknown_names_are_refuted(pc):
    assert states(run(pc, record(lim(3, 'if mode == "fast":', "len(mode) == 4", "entry", "path_change"))))["C2"] == "residual"
    b = run(pc, record(lim(3, 'if mode == "fast":', "batch_size > 1", "entry", "path_change")))
    assert states(b)["C2"] == "refuted" and "C2" in b["open_doubts"]


def test_stale_location_is_refuted(pc):
    b = run(pc, record(lim(2, "assert x >= 1", "not (x >= 1)", "entry")))
    assert states(b)["C1"] == "refuted"
    b = run(pc, record(lim(1, "def entry(x, mode):", "x > 0", "entry", "other")))
    assert states(b)["C1"] == "residual"  # the text is there, but it is not a statement


def test_infeasible_is_not_testable_and_no_chain_caps_the_ceiling(pc):
    l = lim(10, "if d not in {16, 32}:", "d not in {16, 32}", "helper")
    t = run(pc, record(l, status="infeasible", chain="resolved", infeasible_because="call_chain"))["testability"]
    assert t["testable"] is False and t["expect_not_run"] == "witness_unusable"
    # `if d not in {16, 32}`: negate, swap `not in`, 16 +/- 1, 32 +/- 1 -> enough mutants; the chain decides
    t = run(pc, record(l, chain="resolved"))["testability"]
    assert t["mutants"] >= t["mutants_needed"] == 4 and t["ceiling"] == "L3" and t["limited_by"] == []
    b = run(pc, record(l, chain="not_found"))
    assert states(b)["C3"] == "open" and b["testability"]["ceiling"] == "L2"
    assert b["testability"]["limited_by"][0].startswith("D14")
    assert imp(b)["path"]["decision_on"] == "side" or imp(b)["path"]["decision_on"] == "unknown"
    o = lim(16, "if k is None:", "k is None", "orphan", "path_change")
    b = run(pc, record(o, chain="not_found"))
    assert imp(b)["path"]["decision_on"] == "unknown" and imp(b)["coverage"]["function_reached_from_entry"] is False


def test_few_mutants_cap_the_ceiling_at_l1(pc):
    # `if k is None` gives fewer mutants than D3 needs (4), so the test level cannot pass L1
    t = run(pc, record(lim(16, "if k is None:", "k is None", "orphan", "path_change")))["testability"]
    assert 0 < t["mutants"] < 4 and t["ceiling"] == "L1" and t["limited_by"][0].startswith("D3")
    assert t["condition_has_calls"] is False


def test_extraction_runs_and_3b_agreement(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg/mod.py").write_text(SRC)
    region = lambda line: {"location": {"file": "pkg/mod.py", "line_start": line}}
    l = lim(3, 'if mode == "fast":', 'mode == "fast"', "entry", "path_change", "llm")
    item = {"limitation_id": "CL-X001", "paper_agreement": 2 / 3, "elsewhere_agreement": 1.0, "per_run": [{}, {}, {}]}
    pc = ProcessContext(tmp_path, (".",), [ENTRY], runs=[[region(3)], [region(3)], [region(10)]],
                        agreement={"CL-X001": item})
    b = run(pc, record(l))
    assert b["repeats"]["extraction_runs"] == {"measured": True, "found_in": 2, "of": 3, "match": "same file and line"}
    assert states(b)["C5"] == "residual" and "2 of 3" in b["checks"]["C5"]["evidence"]
    assert b["repeats"]["documentation_check"]["paper_agreement"] == 2 / 3
    assert states(b)["C7"] == "residual" and "disagree" in b["checks"]["C7"]["evidence"]
    assert b["repeats"]["routes"] == ["llm"]
    pc = ProcessContext(tmp_path, (".",), [ENTRY], runs=[[region(3)]] * 3)
    assert states(run(pc, record(l)))["C5"] == "eliminated"  # the LLM route found it in every run


def test_review_wrong_and_dropped_prefix(pc):
    l = lim(2, "assert x > 0", "not (x > 0)", "entry")
    assert states(run(pc, record(l, review="wrong")))["C8"] == "refuted"
    assert states(run(pc, record(l, dropped_prefix=["f(x)"])))["C4"] == "residual"


def test_wrong_effect_label_is_refuted(pc):
    b = run(pc, record(lim(5, "y = x if x < 10 else 10", "x >= 10", "entry", "reject")))
    assert states(b)["C6"] == "refuted"


def test_without_repo_source_checks_are_open(tmp_path):
    b = run(ProcessContext(tmp_path / "missing", (".",), [ENTRY]), record(lim(2, "assert x > 0", "not (x > 0)", "entry")))
    s = states(b)
    assert s["C1"] == "open" and s["C2"] == "open" and b["testability"]["measured"] is False
    assert s["C3"] == "eliminated" and s["C4"] == "eliminated"  # these come from the record
    assert imp(b)["path"] == {"measured": False, "reason": "repo not available"}


def test_paper_only_finding_gets_no_block(pc):
    rec = {"finding_id": "t-F002", "effect_type": "other", "witness_hint": {"status": "always"}, "review": "unreviewed",
           "limitations": [{"limitation_id": "t-gap-M01-B01", "origin": "paper", "code_evidence": []}], "verifications": []}
    assert assess(rec, pc) is None
    summary = assess_all([rec], pc)
    assert rec["process_confidence"] is None and summary["assessed"] == 0 and summary["not_assessed_paper_only"] == 1


def test_summary_counts_and_block_is_not_a_schema_field(pc):
    recs = [record(lim(2, "assert x > 0", "not (x > 0)", "entry")),
            record(lim(16, "if k is None:", "k is None", "orphan", "path_change", lid="CL-X002"), chain="not_found")]
    summary = assess_all(recs, pc)
    assert summary["ceiling"] == {"L1": 1, "L3": 1} and summary["decision_on"] == {"main": 1, "unknown": 1}
    assert summary["coverage"] == {"measured": True, "entry_reachable_functions": 2, "decisions": 3,
                                   "decisions_listed": 1, "listed_outside_entry_reach": 1}
    block = json.loads(json.dumps(recs[0]["process_confidence"]))  # plain JSON
    assert block["format"] == "process-confidence-v2" and set(block["checks"]) == {f"C{i}" for i in range(1, 9)}
    # the shared schema is not changed: the block is a key of the hand-off record, like `limitations`
    assert "process_confidence" not in Finding.model_fields
