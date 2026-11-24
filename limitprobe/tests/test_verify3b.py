import json
from pathlib import Path

import pytest

pytest.importorskip("z3")
pytest.importorskip("rank_bm25")

from codeside.doc_index import MIN_QUOTE_CHARS, Passage, Retriever, clean, repo_passages, tokens, verify_quote
from codeside.scope_check import ScopeChecker
from codeside.verify3b import Judgement, Verifier, compose, gate, majority, parse_json, run_paper_tier
from concurrent.futures import ThreadPoolExecutor
from schema.models import Binding, CodeLocation, Condition, EvalPoint, Limitation, ScopeItem

FIX = Path(__file__).resolve().parent / "fixtures"


def lim(lid="CL1", expr="batch_size != 1", text="batch size above 1"):
    return Limitation(limitation_id=lid, artifact_id="t", origin="code", condition_text=text,
                      condition=Condition(expr=expr, params=["batch_size"]), effect_type="reject",
                      effect_text="assert fails", provenance="manual")


PASSAGES = [Passage("P1", "paper", "§1, p.1", "We use a block size of 128 in all our experiments."),
            Passage("P2", "paper", "§2, p.2", "The current version only supports a batch size of 1 for inference."),
            Passage("D1", "readme", "README", "Only tested with bfloat16 precision on recent GPUs.")]
BY_ID = {p.passage_id: p for p in PASSAGES}


# ---------------------------------------------------------------- quote gate
def test_quote_must_occur_verbatim():
    t = PASSAGES[1].text
    assert verify_quote("only supports a batch size of 1", t) == "only supports a batch size of 1"
    assert verify_quote("only supports batch size 1 here", t) is None


def test_quote_gate_folds_typography_only_and_returns_source_text():
    text = "the model’s budget – at least 1024 tokens"
    assert verify_quote("the model's budget - at least 1024", text) == "the model’s budget – at least 1024"
    assert verify_quote("the MODEL's budget - at least 1024", text) is None


def test_quote_gate_rejects_short_and_elided_quotes():
    t = PASSAGES[1].text
    assert verify_quote("x" * (MIN_QUOTE_CHARS - 1), "x" * 50) is None
    assert verify_quote("only supports ... inference", t) is None
    assert verify_quote(None, t) is None


def test_clean_repairs_line_end_hyphenation_and_ligatures():
    assert clean("atten-\ntion in the ﬁrst   step") == "attention in the first step"
    assert clean("cross-\nAttention") == "cross- Attention"


def test_found_without_verified_quote_becomes_not_found():
    j = gate("t", {"result": "found", "evidence": [{"passage_id": "P2", "quote": "made up sentence not there"}]}, BY_ID)
    assert j.result == "not_found" and j.evidence == [] and len(j.gate_failures) == 2


def test_quote_from_uncited_passage_does_not_count():
    j = gate("t", {"result": "found", "evidence": [{"passage_id": "P1", "quote": "only supports a batch size of 1"}]}, BY_ID)
    assert j.result == "not_found"


def test_verified_evidence_keeps_source_and_locator():
    j = gate("t", {"result": "found", "evidence": [{"passage_id": "P2", "quote": "only supports a batch size of 1"}]}, BY_ID)
    assert j.result == "found"
    assert j.evidence[0]["source"] == "paper" and j.evidence[0]["locator"] == "§2, p.2"


def test_unknown_label_is_not_trusted():
    j = gate("t", {"result": "probably", "evidence": []}, BY_ID)
    assert j.result == "not_found" and j.gate_failures


# ---------------------------------------------------------------- retrieval & repo docs
def test_tokens_split_code_names():
    assert {"block", "size"} <= set(tokens("block_size")) and "128" in tokens("block_size != 128")


def test_retriever_ranks_the_matching_passage_first():
    assert Retriever(PASSAGES).search("batch_size", 1)[0].passage_id == "P2"


def test_repo_passages_collect_readme_docstrings_comments():
    out = repo_passages(FIX, ["toy_docs.py"])
    assert {p.source for p in out} == {"docstring", "code_comment"}
    assert any(p.locator.startswith("toy_docs.py:") and "block sizes" in p.text for p in out)


# ---------------------------------------------------------------- scope and evaluation
def binding(sym, term=None):
    return Binding(binding_id=sym, artifact_id="t", paper_term=term or sym, kind="parameter", code_symbol=sym)


def scope_item(param, explicit=True, **kw):
    return ScopeItem(scope_id=param, artifact_id="t", param=param, explicit=explicit, evidence=[], **kw)


CHECKER = ScopeChecker(
    [scope_item("context_length", explicit=False, kind="interval", lower=4096, upper=131072),
     scope_item("block_size", kind="set", values=[128]),
     scope_item("min_budget", kind="set", values=[1024]),
     scope_item("beta", kind="interval", lower=0, upper=10)],
    [EvalPoint(eval_id="E1", artifact_id="t", config={"context_length": 4096, "block_size": 128, "min_budget": 1024},
               evidence=[])],
    [binding("q_len", "context length"), binding("block_size"), binding("min_budget", "minimum budget"), binding("b", "beta")])


def check(expr, prefix=()):
    return CHECKER.check(Condition(expr=expr, path_prefix=list(prefix)))


def test_region_below_scope_lower_bound_is_out_of_scope():
    r = check("q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size)")
    assert r.scope_status == "out_of_scope" and r.evaluated_in_paper is False


def test_config_dependent_boundary_is_computed_from_scope_values():
    assert check("q_len <= max(2 * block_size, math.ceil(min_budget / block_size) * block_size) + 3072").scope_status == "scope_edge"


def test_excluding_the_only_scoped_value_is_out_of_scope():
    assert check("block_size != 128").scope_status == "out_of_scope"
    assert check("block_size not in {32, 64, 128}").scope_status == "out_of_scope"


def test_inferred_scope_gives_scope_edge_explicit_gives_in_scope():
    assert check("q_len > 8192").scope_status == "scope_edge"
    assert check("b > 5").scope_status == "in_scope"


def test_no_binding_is_unknown_not_a_guess():
    r = check("batch_size != 1")
    assert r.scope_status == "unknown" and r.evaluated_in_paper is None and r.unbound_names == ["batch_size"]


def test_untranslatable_conditions_are_unknown():
    assert check("q.shape[1] != k.shape[1]").scope_status == "unknown"
    assert check("causal_mask was built by an earlier call").scope_status == "unknown"


def test_partly_bound_condition_can_still_be_refuted():
    assert check("block_size != 128 and batch_size != 1").scope_status == "out_of_scope"
    assert check("block_size == 128 and batch_size != 1").evaluated_in_paper is None


def test_path_prefix_constrains_the_region():
    assert check("q_len > 8192", prefix=["q_len < 5000"]).scope_status == "out_of_scope"


def test_untranslatable_prefix_is_dropped_and_reported():
    r = check("q_len > 8192", prefix=["q.dtype == torch.bfloat16"])
    assert r.scope_status == "scope_edge" and r.dropped_prefix == ["q.dtype == torch.bfloat16"]


def test_evaluated_when_an_eval_point_satisfies_the_condition():
    assert check("q_len == 4096 and block_size == 128").evaluated_in_paper is True
    assert check("q_len == 5000").evaluated_in_paper is False


# ---------------------------------------------------------------- skills with a fake model
class FakeLLM:
    model = "fake"

    def __init__(self, replies):
        self.replies, self.prompts = replies, []

    def complete(self, system, user, key):
        self.prompts.append((key, user))
        for marker, reply in self.replies:
            if marker in key:
                return reply if isinstance(reply, str) else json.dumps(reply)
        return "[]" if "sweep" in key or "expand" in key else json.dumps({"result": "not_found", "evidence": []})


GOOD = {"result": "found", "evidence": [{"passage_id": "P2", "quote": "only supports a batch size of 1"}]}


def verifier(llm):
    return Verifier(llm, "T", PASSAGES[:2], PASSAGES[2:], [])


def test_consensus_stays_not_found_without_asking_the_skeptic():
    llm = FakeLLM([])
    with ThreadPoolExecutor(2) as pool:
        out = run_paper_tier(verifier(llm), [lim()], "consensus", pool)
    assert out["CL1"]["consensus"].result == "not_found"
    assert not any("skeptic" in k for k, _ in llm.prompts)


def test_skeptic_can_overturn_a_skill():
    llm = FakeLLM([("fullpaper", GOOD), ("skeptic", {"result": "not_found", "evidence": []})])
    with ThreadPoolExecutor(2) as pool:
        out = run_paper_tier(verifier(llm), [lim()], "consensus", pool)
    assert out["CL1"]["fullpaper"].result == "found" and out["CL1"]["consensus"].result == "not_found"


def test_skeptic_output_passes_the_same_gate():
    bad = {"result": "found", "evidence": [{"passage_id": "P2", "quote": "words that are not in the passage"}]}
    llm = FakeLLM([("fullpaper", GOOD), ("skeptic", bad)])
    with ThreadPoolExecutor(2) as pool:
        out = run_paper_tier(verifier(llm), [lim()], "consensus", pool)
    assert out["CL1"]["consensus"].result == "not_found"


def test_sweep_merges_section_reports_and_ignores_unknown_ids():
    llm = FakeLLM([("sweep", [{"limitation_id": "CL1", **GOOD}, {"limitation_id": "CL9", **GOOD}])])
    with ThreadPoolExecutor(2) as pool:
        out = run_paper_tier(verifier(llm), [lim()], "sweep", pool)
    assert out["CL1"]["sweep"].result == "found" and set(out) == {"CL1"}


def test_unparseable_replies_raise_instead_of_reading_as_not_found():
    llm = FakeLLM([("fullpaper", "I could not decide.")])
    with ThreadPoolExecutor(2) as pool, pytest.raises(RuntimeError, match="no parseable"):
        run_paper_tier(verifier(llm), [lim()], "fullpaper", pool)


def test_parse_json_skips_prose_and_fences():
    assert parse_json('Sure:\n```json\n{"result": "found"}\n```') == {"result": "found"}
    with pytest.raises(ValueError):
        parse_json("nothing here")


def test_majority_reports_agreement():
    best, agree = majority([Judgement("x", "found"), Judgement("x", "not_found"), Judgement("x", "found")])
    assert best.result == "found" and agree == pytest.approx(2 / 3)


# ---------------------------------------------------------------- composing the record
def _scope():
    return CHECKER.check(Condition(expr="batch_size != 1"))


def _ev(pid):
    p = BY_ID[pid]
    return {"passage_id": pid, "quote": p.text[:20], "source": p.source, "locator": p.locator}


def test_compose_paper_decides_when_it_speaks():
    v = compose(lim(), Judgement("c", "found", [_ev("P2")]), Judgement("e", "weaker", [_ev("D1")]), _scope(), "llm:x", 0)
    assert v.result == "found" and v.documented_in == ["paper", "readme"] and v.direction == "code_to_paper"


def test_compose_falls_back_to_other_docs_and_records_where():
    v = compose(lim(), Judgement("c"), Judgement("e", "weaker", [_ev("D1")]), _scope(), "llm:x", 0)
    assert v.result == "weaker" and v.documented_in == ["readme"] and v.matching_evidence[0].source == "readme"


def test_compose_not_found_has_no_evidence():
    v = compose(lim(), Judgement("c"), Judgement("e"), _scope(), "llm:x", 0)
    assert v.result == "not_found" and v.documented_in == [] and v.matching_evidence == []


def test_comment_next_to_the_code_reaches_the_judge_even_with_no_shared_words():
    near = Passage("D9", "code_comment", "a.py:87", "use default setting, maybe not optimal")
    far = Passage("D8", "code_comment", "a.py:400", "use default setting, maybe not optimal")
    other = Passage("D7", "code_comment", "b.py:87", "use default setting, maybe not optimal")
    case = lim(text="GPU other than H100")
    case.code_evidence = [CodeLocation(file="a.py", line_start=86, line_end=88)]
    llm = FakeLLM([])
    Verifier(llm, "T", [], [near, far, other], []).judge_elsewhere(case)
    prompt = llm.prompts[-1][1]
    assert "[D9]" in prompt


def test_near_location_matches_file_and_line_window():
    near = Passage("D9", "code_comment", "a.py:87", "x" * 20)
    far = Passage("D8", "code_comment", "a.py:400", "x" * 20)
    other = Passage("D7", "code_comment", "b.py:87", "x" * 20)
    readme = Passage("D6", "readme", "a.py:87", "x" * 20)
    case = lim()
    case.code_evidence = [CodeLocation(file="a.py", line_start=86, line_end=88)]
    assert [p.passage_id for p in Verifier(FakeLLM([]), "T", [], [near, far, other, readme], []).near_location(case)] == ["D9"]


def test_same_quote_from_two_passages_is_kept_once():
    twin = Passage("P3", "paper", "§3, p.3", PASSAGES[1].text)
    ev = [{"passage_id": "P2", "quote": "only supports a batch size of 1"}, {"passage_id": "P3", "quote": "only supports a batch size of 1"}]
    assert len(gate("t", {"result": "found", "evidence": ev}, {**BY_ID, "P3": twin}).evidence) == 1


def test_non_boolean_conditions_give_unknown_instead_of_crashing():
    # Route B writes conditions such as a bare integer name; z3 cannot use these as constraints.
    assert check("block_size").scope_status == "unknown"
    r = check("block_size != 128", prefix=["q_len"])
    assert r.scope_status == "out_of_scope" and "q_len" in r.dropped_prefix
    r = check("block_size != 128", prefix=["not q_len"])
    assert r.scope_status == "out_of_scope" and "not q_len" in r.dropped_prefix
