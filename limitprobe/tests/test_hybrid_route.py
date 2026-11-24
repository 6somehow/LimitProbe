import json
from pathlib import Path

from codeside.evaluate import evaluate_regions, stability
from codeside.extractor import ExtractConfig, extract
from codeside.hybrid_extractor import DISCOVER_SYSTEM, EDGE_SYSTEM, extract_hybrid

FIX = Path(__file__).resolve().parent / "fixtures"
FILE = "hybrid_module.py"
CFG = ExtractConfig(repo=FIX, entry=f"{FILE}::top", artifact_id="toy")


class Router:
    """Fake model: one canned answer per stage."""

    def __init__(self, edges=None, discover=None, fail=()):
        self.answers = {EDGE_SYSTEM: edges or {"targets": []}, DISCOVER_SYSTEM: discover or []}
        self.fail = {EDGE_SYSTEM: "edges", DISCOVER_SYSTEM: "discover"}
        self.failing = set(fail)
        self.users = []

    def complete(self, system, user):
        self.users.append(user)
        if self.fail[system] in self.failing:
            return "no json here"
        ans = self.answers[system]
        return json.dumps(ans(user) if callable(ans) else ans)


def _edge_to(*targets):
    return lambda user: {"targets": [t for t in targets if f"[{t}]" in user]}


def test_llm_edge_reaches_code_the_static_route_cannot():
    assert not [r for r in extract(CFG) if "mode" in r.condition.expr]
    res = extract_hybrid(CFG, Router(edges=_edge_to(f"{FILE}::Impl.run", f"{FILE}::Base.helper")), workers=1)
    hits = [r for r in res.regions if r.location.function == f"{FILE}::Base.helper"]
    assert hits and all(r.provenance == "llm" for r in hits)
    assert any(c.endswith("Impl.run") for c in hits[0].call_chain)
    assert res.meta["edges"]["accepted"]


def test_edge_to_a_definition_that_is_not_a_candidate_is_rejected():
    res = extract_hybrid(CFG, Router(edges={"targets": ["hybrid_module.py::does_not_exist"]}), workers=1)
    assert res.meta["edges"]["rejected"] and not res.meta["edges"]["accepted"]


def test_external_library_calls_are_not_sent_to_the_model():
    router = Router()
    extract_hybrid(CFG, router, workers=1)
    assert not any(u.startswith(f"Call site in {FILE}, line 37") for u in router.users)


def test_every_static_region_stays_in_the_output():
    answer = [_found()]
    res = extract_hybrid(CFG, Router(discover=lambda u: answer if f"# --- {FILE}::top" in u else []), workers=1)
    static = {r.region_id for r in extract(CFG)}
    assert static <= {r.region_id for r in res.regions}
    assert len(res.regions) == len(static) + 1 and res.meta["added_regions"] == 1
    assert "triage" not in res.meta


def _found(line=34, code="if warm:", cond="warm", outcome="mechanism_variant"):
    return {"line": line, "code": code, "condition": cond, "outcome": outcome, "detail": "d", "path_prefix": []}


def test_discover_adds_validated_regions_only():
    def answer(user):
        if f"# --- {FILE}::top" not in user:
            return []
        return [_found(cond="invented_name"),  # name not in the function
                _found(),  # good
                _found(line=33, code="if warm:"),  # quote not on that line
                _found(line=33, code="assert x is not None", cond="x is None", outcome="reject")]  # duplicate
    res = extract_hybrid(CFG, Router(discover=answer), workers=1)
    added = [r for r in res.regions if r.region_id.startswith("D")]
    assert [r.condition.expr for r in added] == ["warm"] and added[0].provenance == "llm"
    assert added[0].call_chain == [f"{FILE}::top"]
    assert res.meta["discover"]["duplicates"] == 1 and len(res.meta["discover"]["rejected"]) == 2


def test_failed_calls_keep_static_results_and_are_reported():
    res = extract_hybrid(CFG, Router(fail={"edges", "discover"}), workers=1)
    assert {r.region_id for r in res.regions} == {r.region_id for r in extract(CFG)}
    assert {f["stage"] for f in res.meta["failed_calls"]} == {"edges", "discover"}


def test_one_to_one_matching_stops_neighbours_sharing_a_gold_region():
    regions = [r for r in extract(CFG) if r.outcome == "reject"][:2]
    gold = [regions[0].model_copy(update={"region_id": "G"})]
    near = regions[1].model_copy(update={"location": regions[0].location.model_copy(
        update={"line_start": regions[0].location.line_start + 1})})
    loose = evaluate_regions([regions[0], near], gold, tol=2)
    strict = evaluate_regions([regions[0], near], gold, tol=2, one_to_one=True)
    assert not loose.extra and len(strict.extra) == 1 and strict.matched["G"] == [regions[0].region_id]


def test_stability_is_one_for_identical_runs():
    run = extract(CFG)
    assert stability([run, run], gold=run) == {"regions_jaccard": 1.0, "gold_jaccard": 1.0}
