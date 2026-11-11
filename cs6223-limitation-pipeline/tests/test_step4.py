"""Step 4: witness_hint solver (codeside/witness.py) and Finding integration (codeside/integrate.py)."""

from codeside.integrate import Context, Rules, classify, integrate, priority
from codeside.scope_check import ScopeChecker
from codeside.witness import solve
from schema.models import Binding, CodeLocation, Condition, EvalPoint, Limitation, ScopeItem, TextEvidence, Verification


def cond(expr, prefix=()):
    return Condition(expr=expr, params=[], path_prefix=list(prefix))


def checker():
    scope = [ScopeItem(scope_id="S1", artifact_id="a", param="threshold_tau", kind="interval", lower=0.0, upper=1.0,
                       explicit=True, evidence=[]),
             ScopeItem(scope_id="S2", artifact_id="a", param="block size", kind="set", values=[64, 128],
                       explicit=True, evidence=[])]
    binds = [Binding(binding_id="B1", artifact_id="a", paper_term="threshold_tau", kind="parameter", code_symbol="tau",
                     certain=True),
             Binding(binding_id="B2", artifact_id="a", paper_term="block size", kind="parameter",
                     code_symbol="block_size", certain=True)]
    evals = [EvalPoint(eval_id="E1", artifact_id="a", config={"tau": 0.1, "block_size": 128, "q_len": 4096},
                       evidence=[])]
    return ScopeChecker(scope, evals, binds)


# --------------------------------------------------------------------------- witness
def test_boundary_pair_for_integer_threshold():
    h = solve(cond("x < 0"), None, "reject")
    assert h["status"] == "solved" and h["trigger"] == {"x": -1} and h["contrast"] == {"x": 0}


def test_set_membership_and_eval_preference():
    h = solve(cond("not (head_dim in {16, 32, 64, 128})"), checker(), "reject")
    assert h["trigger"]["head_dim"] not in {16, 32, 64, 128}
    assert h["contrast"]["head_dim"] in {16, 32, 64, 128}
    assert abs(h["trigger"]["head_dim"] - h["contrast"]["head_dim"]) == 1


def test_scope_and_eval_point_on_bound_real():
    h = solve(cond("kl_div < tau"), checker(), "path_change")
    assert h["eval_preference"] == {"tau": 0.1} and "tau" in h["from_paper"]
    assert h["trigger"]["tau"] == 0.1 and h["trigger"]["kl_div"] < 0.1 <= h["contrast"]["kl_div"]


def test_scope_set_restricts_both_points():
    h = solve(cond("block_size < 100"), checker(), "reject")
    assert h["trigger"]["block_size"] == 64 and h["contrast"]["block_size"] == 128


def test_category_predicate_and_derived_atoms():
    h = solve(cond("not (q.dtype == torch.bfloat16) and is_flash_attn_2_available() and q.shape[1] != k.shape[1]"),
              None, "reject")
    assert h["status"] == "solved"
    assert h["trigger"]["q.dtype"] == {"not_in": ["torch.bfloat16"]}
    assert h["trigger"]["is_flash_attn_2_available()"] is True
    assert h["atoms"]["q.shape[1]"] == {"kind": "derived", "sort": "int"}
    assert h["atoms"]["q.dtype"]["kind"] == "category"


def test_prefix_contradiction_is_infeasible():
    h = solve(cond("not (head_dim in {16, 32})", ["head_dim in {16, 32}"]), None, "reject")
    assert h["status"] == "infeasible"


def test_condition_equal_to_prefix_has_no_contrast():
    h = solve(cond("q_len != 1", ["q_len != 1"]), None, "reject")
    assert h["status"] == "trigger_only" and "contrast" not in h


def test_untranslatable_and_missing_condition():
    assert solve(cond("x <"), None, "reject")["status"] == "untranslatable"
    h = solve(None, None, "reject")
    assert h["status"] == "untranslatable" and h["condition"] is None


def test_state_effect_is_event_sequence():
    h = solve(cond("cache is None"), None, "state")
    assert h["kind"] == "event_sequence" and "sequence_note" in h


def test_bad_prefix_is_dropped_not_fatal():
    h = solve(cond("q_len == 1", ["x = 1", "foo(**kw) @ y > 2"]), None, "reject")
    assert h["status"] == "solved" and len(h["dropped_prefix"]) == 2


def test_alias_ties_local_to_its_definition():
    from codeside.witness import find_aliases
    src = ("def f(q, k, n):\n    b, q_len, h, d = q.shape\n    k_len = k.shape[1]\n    n2 = 1\n    n2 = 2\n"
           "    if q_len != k_len:\n        raise ValueError\n")
    al = find_aliases(src, 6)
    assert al["q_len"] == "q.shape[1]" and al["k_len"] == "k.shape[1]" and "n2" not in al and "n" not in al
    h = solve(cond("q_len != k_len"), None, "reject", al)
    assert h["trigger"]["q.shape[1]"] == h["trigger"]["q_len"] != h["trigger"]["k.shape[1]"]
    assert h["atoms"]["q_len"]["kind"] == "local"


def test_alias_that_makes_prefix_infeasible_is_dropped():
    # caller says q.shape[1] <= 1, callee's q_len is a different tensor's length
    h = solve(cond("q_len > 1", ["not (q.shape[1] > 1)"]), None, "reject", {"q_len": "q.shape[1]"})
    assert h["status"] == "solved" and h["aliases_dropped"] == {"q_len": "q.shape[1]"}


# --------------------------------------------------------------------------- classification
def ver(result, sources=(), quotes=(), scope="unknown", locators=None):
    ev = [TextEvidence(quote=q, source=s, locator=(locators or {}).get(s, "x")) for q, s in zip(quotes, sources)]
    return Verification(verification_id="V1", limitation_id="CL1", direction="code_to_paper", result=result,
                        documented_in=list(dict.fromkeys(sources)), matching_evidence=ev, scope_status=scope,
                        verifier="llm:test")


def test_decision_table():
    assert classify(ver("not_found"))[0] == "undisclosed"
    assert classify(ver("found", ["paper"], ["we only support 128"]))[0] == "paper_stated"
    assert classify(ver("weaker", ["paper"], ["tested with 128"]))[0] == "stated_differently"
    assert classify(ver("found", ["readme"], ["only supports batch size 1"]))[0] == "docs_only"
    assert classify(ver("boundary_mismatch", ["docstring"], ["16, 32, 64"]))[0] == "stated_differently"
    assert classify(ver("contradicted", ["paper"], ["x"]))[0] == "contradicts_docs"


def test_only_user_facing_docs_count():
    todo = ver("found", ["code_comment"], ["TODO: support more than one block size"])
    cat, notes = classify(todo)
    assert cat == "undisclosed" and "code comment" in notes[0]
    assert classify(ver("found", ["code_comment"], ["seq_len <= 16k, use vertical slash"]))[0] == "undisclosed"
    both = ver("found", ["code_comment", "docstring"], ["TODO: one block size", "only one block size"])
    assert classify(both)[0] == "docs_only"
    private = ver("found", ["docstring"], ["only one block size"], locators={"docstring": "a.py:3 (_helper)"})
    assert classify(private)[0] == "undisclosed"
    assert classify(ver("found", ["readme"], ["requires triton>=2.1.0"]))[0] == "undisclosed"
    assert classify(ver("found", ["readme"], ["The current version only supports batch size 1"]))[0] == "docs_only"


def test_priority_rules():
    r, strict = Rules(), Rules(strict_scope=True)
    assert priority("undisclosed", "reject", "yes", "unknown", "unreviewed", r)[0] == 1
    assert priority("undisclosed", "reject", "yes", "unknown", "unreviewed", strict)[0] == 2
    assert priority("undisclosed", "reject", "unknown", "in_scope", "unreviewed", r)[0] == 2
    assert priority("undisclosed", "reject", "no", "in_scope", "unreviewed", r)[0] == 3
    assert priority("undisclosed", "reject", "yes", "out_of_scope", "unreviewed", r)[0] == 3
    assert priority("undisclosed", "reject", "yes", "unknown", "wrong", r)[0] == 3
    assert priority("undisclosed", "path_change", "yes", "unknown", "unreviewed", r)[0] == 2
    assert priority("undisclosed", "other", "yes", "unknown", "unreviewed", r)[0] == 3
    assert priority("impl_deviates", "other", "unknown", "unknown", "unreviewed", r)[0] == 2
    assert priority("not_implemented", "other", "unknown", "unknown", "unreviewed", r)[0] == 3
    assert priority("docs_only", "reject", "yes", "unknown", "unreviewed", r)[0] == 3


# --------------------------------------------------------------------------- integration
def lim(lid, expr, line, fn="f.py::g", effect="reject", origin="code", prefix=(), notes=None, end=None):
    return Limitation(limitation_id=lid, artifact_id="a", origin=origin, condition_text=expr or "text",
                      condition=cond(expr, prefix) if expr else None, effect_type=effect, effect_text="rejects",
                      code_evidence=[CodeLocation(file="f.py", line_start=line, line_end=end or line,
                                                  function=fn)],
                      region_ids=["X1"] if origin == "code" else [], provenance="ast" if origin == "code" else "llm",
                      level="L2" if origin == "paper" else None, notes=notes)


def _inputs():
    code = [lim("CL1", "not (q_len == k_len)", 10), lim("CL2", "q_len != k_len", 30),
            lim("CL3", "not (h in {1, 2})", 50, prefix=["h in {1, 2}"])]
    vers = [ver("not_found").model_copy(update={"limitation_id": i, "verification_id": f"V{i}"})
            for i in ("CL1", "CL2", "CL3")]
    paper = [lim("a-gap-M1", None, 5, origin="paper", notes="Original verdict=deviates", end=20, effect="other"),
             lim("a-gap-M2", None, 90, origin="paper", notes="Original verdict=absent", effect="other"),
             lim("a-gap-M3", None, 90, origin="paper", notes="Original verdict=absent", effect="other")]
    return code, vers, paper


def test_integrate_without_llm():
    code, vers, paper = _inputs()
    fs, rep = integrate("a", code, vers, paper, None, Rules())
    by_lim = {f.limitation_ids[0]: f for f in fs}
    assert by_lim["CL1"].limitation_ids == ["CL1", "CL2"] and "same check merged" in by_lim["CL1"].rationale
    assert by_lim["CL1"].priority == 1 and by_lim["CL1"].category == "undisclosed"
    assert by_lim["CL3"].priority == 3 and "unreachable" in by_lim["CL3"].rationale
    assert by_lim["a-gap-M1"].category == "impl_deviates" and by_lim["a-gap-M1"].priority == 2
    assert by_lim["a-gap-M2"].category == "not_implemented" and by_lim["a-gap-M2"].priority == 3
    assert by_lim["a-gap-M2"].witness_hint["status"] == "no_condition"
    assert [f.finding_id for f in fs] == [f"a-F{i:03d}" for i in range(1, 6)] and fs[0].priority == 1
    assert rep["findings"] == 5 and rep["code_limitations"] == 3 and rep["candidate_pairs"] == 2


class FakeJudge:
    """Same issue: CL1 with M1 (overlapping lines), M2 with M3 (identical evidence)."""

    def __init__(self):
        self.asked = []

    def same(self, a, b):
        self.asked.append((a.limitation_id, b.limitation_id))
        ids = {a.limitation_id, b.limitation_id}
        return {"pair": sorted(ids), "same": ids in ({"CL1", "a-gap-M1"}, {"a-gap-M2", "a-gap-M3"}), "votes": []}

    def condition(self, l):
        return {"kind": "condition", "expr": "n > 4", "path_prefix": [], "reason": "r", "model": "fake"}


def test_integrate_with_llm_merges_and_solves_paper_condition():
    code, vers, paper = _inputs()
    judge = FakeJudge()
    fs, rep = integrate("a", code, vers, paper, None, Rules(),
                        Context(judge=judge, labels={("f.py", 10): {"label": "useful", "reason": "x", "round": 3}}))
    assert ("CL1", "a-gap-M1") in judge.asked and ("a-gap-M2", "a-gap-M3") in judge.asked
    assert ("CL3", "a-gap-M1") not in judge.asked  # no overlap: not a candidate pair
    by_lim = {f.limitation_ids[0]: f for f in fs}
    f1 = by_lim["CL1"]
    assert f1.limitation_ids == ["CL1", "CL2", "a-gap-M1"] and f1.category == "undisclosed"
    assert "paper side also reports: impl_deviates" in f1.rationale
    assert f1.review == "worth_testing" and "not human" in f1.review_note
    m2 = by_lim["a-gap-M2"]
    assert m2.limitation_ids == ["a-gap-M2", "a-gap-M3"]
    assert m2.witness_hint["status"] == "solved" and m2.witness_hint["trigger"]["n"] == 5
    assert rep["findings"] == 3 and rep["pairs_judged_same"] == 2 and rep["findings_merged_both_sides"] == 1
    assert len(rep["llm_records"]["condition"]) == 1


def test_llm_condition_is_checked_against_code():
    from codeside.step4_llm import check_condition
    code = "  10      if q_len > block_size * 2:\n  11          x = q.shape[1]"
    assert check_condition("q_len > block_size * 2", [], code) is None
    assert "seq_len" in check_condition("seq_len > 2", [], code)
    assert "not a Python" in check_condition("q_len >", [], code)


def test_same_as_above_is_expanded_from_conformance():
    from codeside.integrate import resolve_same_as_above
    l = lim("a-gap-M1-B2", None, 5, origin="paper", notes="Original verdict=deviates", effect="other")
    conf = {"M1-B2": {"local_entry": {"discrepancy": "A is sorted V, not V"}}}
    assert resolve_same_as_above(l.model_copy(update={"effect_text": "同上"}), conf) == "A is sorted V, not V"
    t = resolve_same_as_above(l.model_copy(update={"effect_text": "同上：无覆盖写"}), conf)
    assert t.startswith("A is sorted V, not V") and "无覆盖写" in t
    assert resolve_same_as_above(l, conf) is None


def test_condition_true_without_path_means_always():
    from codeside.step4_llm import Judge

    class LLM:
        model = "fake"

        def complete(self, system, user, key):
            return '{"kind": "condition", "expr": "True", "path_prefix": [], "reason": "r"}'

    l = lim("a-gap-M1", None, 5, origin="paper", effect="other")
    assert Judge(LLM(), "a", None).condition(l)["kind"] == "always"


def test_merged_finding_takes_the_higher_priority():
    # code side: undisclosed with effect `other` -> p3 alone; merged with a paper-side impl_deviates -> p2
    code = [lim("CL1", "x != 128", 10, effect="other")]
    vers = [ver("not_found").model_copy(update={"limitation_id": "CL1", "verification_id": "V1"})]
    paper = [lim("a-gap-M1", None, 5, origin="paper", notes="Original verdict=deviates", end=20, effect="other")]

    class J(FakeJudge):
        def same(self, a, b):
            return {"pair": [a.limitation_id, b.limitation_id], "same": True, "votes": []}

    fs, _ = integrate("a", code, vers, paper, None, Rules(), Context(judge=J()))
    assert len(fs) == 1 and fs[0].category == "undisclosed" and fs[0].priority == 2
