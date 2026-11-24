"""Call chains with arguments (codeside/callgraph.py), names in entry terms (codeside/chain_bind.py),
and their use by the witness solver and step 4."""

from pathlib import Path

from codeside.callgraph import RepoCallGraph, locate
from codeside.chain_bind import ChainBinder, frame_definitions
from codeside.integrate import Context, Rules, integrate
from codeside.witness import solve
from schema.models import CodeLocation, Condition, Limitation

REPO = Path(__file__).parent / "fixtures" / "chain_repo"
ENTRY = "pkg/entry.py::attention"
K = "pkg/kernels.py"
G = RepoCallGraph(REPO)


def line_of(file: str, text: str) -> int:
    return next(i for i, l in enumerate((REPO / file).read_text().splitlines(), 1) if l.strip().startswith(text))


def info(file: str, text: str) -> dict:
    return locate(G, [ENTRY], file, line_of(file, text))


def binder(file: str, text: str, chain: int = 0) -> ChainBinder:
    r = info(file, text)
    return ChainBinder(G, r["entry"], r["chains"][chain], line_of(file, text))


# --------------------------------------------------------------------------- call graph
def test_chain_through_imported_function_with_arguments():
    r = info(K, "assert d in")
    assert r["status"] == "resolved"
    assert r["call_chain"] == [ENTRY, "pkg/entry.py::helper", f"{K}::pool"]
    first, second = r["call_sites"]
    assert first["args"] == {"q": "q", "k": "k", "block_size": "block_size", "interleave": "interleave"}
    assert second["args"] == {"x": "k", "kernel_size": "block_size"} and second["resolved_by"] == "direct"
    assert r["other_chains"] == [r["call_chain"]]  # the second call site of pool, with mode="max"
    assert r["chains"][1][-1].args["mode"] == "'max'"


def test_module_attribute_call_and_star_args():
    sites = [c for c in G.calls_from(ENTRY) if c.callee == f"{K}::scale"]
    assert [c.resolved_by for c in sites] == ["import", "import"]
    assert sites[0].args == {"t": "q", "factor": "heads"} and not sites[0].star
    assert sites[1].star and sites[1].args == {}


def test_typed_local_self_call_and_override():
    r = info(K, "assert x is not None")
    assert r["call_chain"] == [ENTRY, f"{K}::Base.run", f"{K}::Child.step"]
    assert [c["resolved_by"] for c in r["call_sites"]] == ["direct", "override"]
    assert r["uncertain_steps"]  # which `step` runs depends on the object


def test_unique_method_name_is_a_guess_and_nested_function_is_a_reference():
    r = info("pkg/entry.py", "assert code == 0")
    assert r["call_sites"][0]["resolved_by"] == "unique_name" and r["uncertain_steps"]
    hook = [c for c in G.calls_from(f"{K}::make_hook")]
    assert [(c.callee, c.resolved_by, c.args) for c in hook] == [(f"{K}::make_hook.hook", "reference", {})]


def test_statuses_entry_module_not_found_and_caller_of_entry():
    assert info("pkg/entry.py", "assert head_dim")["status"] == "entry_is_target"
    assert locate(G, [ENTRY], K, 1)["status"] == "module_level"
    assert info(K, "assert v < limit")["status"] == "not_found"  # make_hook is not on the entry's path
    r = locate(G, [ENTRY], "pkg/entry.py", line_of("pkg/entry.py", "return attention"))
    assert r["status"] == "not_found" and r["calls_entry"] == [ENTRY]


# --------------------------------------------------------------------------- names in entry terms
def test_definitions_take_the_last_straight_line_assignment():
    fn = G.funcs[ENTRY].node
    defs = frame_definitions(fn, line_of("pkg/entry.py", "out = helper"))
    import ast
    assert ast.unparse(defs["head_dim"]) == "k.shape[3]" and ast.unparse(defs["batch"]) == "k.shape[0]"
    assert ast.unparse(defs["q_len"]) == "q.shape[1]"


def test_callee_names_in_entry_terms():
    b = binder(K, "assert d in")
    assert b.term("d") == "k.shape[3]" and b.term("kernel_size") == "block_size"
    assert b.term("head_dim") == "k.shape[3]" and b.term("block_size") is None  # same name all the way
    assert b.term("mode") == "'avg'"  # default value: the first call site does not pass it
    assert binder(K, "assert d in", chain=1).term("mode") == "'max'"
    assert b.frame_of("head_dim in {16, 32, 64}") == 0 and b.frame_of("not interleave") == 1
    assert b.rewrite("not (d in {16, 32, 64})", b.last) == "not k.shape[3] in {16, 32, 64}"


def test_reassigned_parameter_is_refused():
    b = binder(K, "assert factor > 0")
    assert b.term("factor") == "q.shape[2]"
    assert b.term("t") is None and "re-assigned" in b.refused["t"]


# --------------------------------------------------------------------------- solver
def cond(expr, prefix=()):
    return Condition(expr=expr, params=[], path_prefix=list(prefix))


def test_check_already_made_by_the_entry_is_infeasible_through_the_chain():
    c = cond("not (d in {16, 32, 64})", ["head_dim in {16, 32, 64}", "not (q_len == 1)", "not interleave"])
    assert solve(c, None, "reject")["status"] == "solved"  # without the chain `d` looks like a free input
    h = solve(c, None, "reject", None, binder(K, "assert d in"))
    assert h["status"] == "infeasible" and h["infeasible_because"] == "call_chain"
    assert h["entry_terms"]["condition"] == "not k.shape[3] in {16, 32, 64}"


def test_reachable_check_gets_consistent_values_in_entry_terms():
    c = cond("not (kernel_size in {16, 32, 64, 128})", ["head_dim in {16, 32, 64}", "d in {16, 32, 64}"])
    h = solve(c, None, "reject", None, binder(K, "assert kernel_size"))
    assert h["status"] == "solved"
    t = h["trigger"]
    assert t["kernel_size"] == t["block_size"] and t["d"] == t["head_dim"] == t["k.shape[3]"]
    assert h["entry_terms"]["names"]["kernel_size"] == "block_size"


def test_guessed_chain_never_proves_infeasible():
    b = binder("pkg/entry.py", "assert code == 0")
    assert not b.certain
    h = solve(cond("not (code == 0)", ["code == 0"]), None, "reject", None, b)
    assert h["status"] == "infeasible" and "infeasible_because" not in h  # infeasible on its own text, not by the chain


# --------------------------------------------------------------------------- step 4
def lim(lid, file, text, expr, prefix=()):
    loc = CodeLocation(file=file, line_start=line_of(file, text), function=G.func_at(file, line_of(file, text)).id)
    return Limitation(limitation_id=lid, artifact_id="a", origin="code", condition_text=expr,
                      condition=cond(expr, prefix), effect_type="reject", effect_text="AssertionError",
                      code_evidence=[loc], provenance="ast")


def test_step4_hands_over_chain_and_keeps_finding_ids():
    lims = [lim("CL-1", K, "assert d in", "not (d in {16, 32, 64})", ["head_dim in {16, 32, 64}"]),
            lim("CL-2", K, "assert kernel_size", "not (kernel_size in {16, 32, 64, 128})"),
            lim("CL-3", "pkg/entry.py", "assert head_dim", "not (head_dim in {16, 32, 64})")]
    ctx = Context(repo=REPO, entry_points=[ENTRY], callgraph=G)
    findings, report = integrate("a", lims, [], [], None, Rules(), ctx)
    by = {f.limitation_ids[0]: f for f in findings}
    h = by["CL-1"].witness_hint
    assert h["status"] == "infeasible" and by["CL-1"].priority == 3
    assert h["call_chain"][0] == ENTRY and h["call_sites"][1]["args"]["x"] == "k"
    assert "all 2 call chains" in h["note"]
    assert by["CL-2"].witness_hint["status"] == "solved" and by["CL-2"].witness_hint["call_chain_status"] == "resolved"
    assert by["CL-3"].witness_hint["call_chain_status"] == "entry_is_target"
    assert report["call_chain_status"] == {"resolved": 2, "entry_is_target": 1}
    # a rerun with one more limitation: old findings keep their ids, the new one gets the next number
    ctx.known_ids = {tuple(f.limitation_ids): f.finding_id for f in findings}
    more = [lim("CL-0", K, "assert factor", "not (factor > 0)"), *lims]
    again, _ = integrate("a", more, [], [], None, Rules(), ctx)
    assert {f.limitation_ids[0]: f.finding_id for f in again if f.limitation_ids[0] != "CL-0"} == \
           {k: f.finding_id for k, f in by.items()}
    assert next(f for f in again if f.limitation_ids[0] == "CL-0").finding_id == "a-F004"
