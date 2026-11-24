#!/usr/bin/env python3
"""Write results/step4/HANDOFF.md: what the limitations of both sides look like, for Shanghao (steps 5-6).

Generated from results/step4/limitations_for_tests.json, so it stays in sync with every step-4 run:
  python scripts/run_step4.py && python scripts/make_handoff_doc.py
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATS = ["undisclosed", "contradicts_docs", "stated_differently", "docs_only", "paper_stated", "impl_deviates",
        "not_implemented", "paper_hypothesis"]
CAT_ZH = {
    "undisclosed": "The code has this limitation, but no user-facing source documents it (core finding)",
    "contradicts_docs": "The documentation contradicts the code behavior",
    "stated_differently": "The documentation states a different or weaker boundary (e.g. “only tested bf16” vs code requiring bf16)",
    "docs_only": "The README / public docstring states it, but the paper does not",
    "paper_stated": "The paper states it with the same boundary as the code",
    "impl_deviates": "The implementation differs from the paper",
    "not_implemented": "The paper describes it, but the code does not implement it",
    "paper_hypothesis": "A hypothesis proposed by Swarm from paper evidence",
}
WSTATUS = ["solved", "solved_contrast_outside_scope", "trigger_only", "always", "infeasible", "untranslatable",
           "unknown", "no_condition"]
ORACLE = [
    ("reject", "Raises an exception / fails an assertion", "Assert that trigger raises the specified exception and contrast does not"),
    ("path_change", "Changes execution path (fallback, kernel, or strategy)", "path hook: instrument both path entries; trigger takes the limited branch and contrast does not"),
    ("accuracy", "Reduced result accuracy", "differential: compare with a reference implementation; trigger error exceeds the threshold"),
    ("state", "Depends on state left by previous calls", "event_sequence: call in order to establish the trigger state, then check"),
    ("resource / performance", "Memory / time", "resource: measure and compare with contrast"),
    ("other (almost all paper-side findings)", "The implementation differs from the paper, with no established runtime consequence",
     "When witness is always: use any input that reaches the cited code and compare with the paper formula / description using differential or metamorphic tests; "
     "3a made only a static judgment; the consequence is unconfirmed"),
]


def side(f: dict) -> str:
    o = {l["origin"] for l in f["limitations"]}
    return "Merged" if len(o) == 2 else ("Code side" if "code" in o else "Paper side")


def short(s: str, n: int = 90) -> str:
    s = " ".join((s or "").split()).replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def counter_table(rows, cols, get, row_name, col_names=None) -> list[str]:
    out = [f"| {row_name} | " + " | ".join(col_names or cols) + " | Total |", "|---" * (len(cols) + 2) + "|"]
    for r, items in rows:
        c = Counter(get(f) for f in items)
        out.append(f"| {r} | " + " | ".join(str(c.get(x, 0)) for x in cols) + f" | {len(items)} |")
    return out


def compact(f: dict) -> str:
    """One finding as trimmed JSON: what Shanghao reads first."""
    keep = {k: f[k] for k in ("finding_id", "category", "priority", "effect_type", "scope_status", "review", "summary")}
    w = {k: v for k, v in f["witness_hint"].items()
         if k in ("kind", "status", "condition", "path_prefix", "aliases", "trigger", "contrast", "atoms", "note",
                  "location", "code_locations", "condition_source", "call_chain_status", "call_chain", "entry_terms",
                  "infeasible_because")}
    if "note" in w:
        w["note"] = short(w["note"], 200)
    if len(w.get("atoms", {})) > 6:  # long atom lists add nothing to an example
        w["atoms"] = f"... {len(w['atoms'])} atoms, see json"
    keep["witness_hint"] = w
    keep["limitations"] = [{"limitation_id": l["limitation_id"], "origin": l["origin"],
                            "condition_text": short(l["condition_text"], 160), "effect_text": short(l["effect_text"], 160),
                            "code_evidence": [f"{c['file']}:{c['line_start']}-{c['line_end'] or c['line_start']}"
                                              for c in l["code_evidence"]][:3],
                            "paper_quote": short(l["paper_evidence"][0]["quote"], 140) if l["paper_evidence"] else None}
                           for l in f["limitations"]]
    keep["verifications"] = [{"result": v["result"], "documented_in": v["documented_in"],
                              "quote": short(v["matching_evidence"][0]["quote"], 120) if v["matching_evidence"] else None}
                             for v in f["verifications"]]
    keep["rationale"] = short(f["rationale"], 300)
    b = f.get("process_confidence")
    if b:
        t, i = b["testability"], b["importance"]
        keep["process_confidence"] = {"checks": {k: c["status"] for k, c in b["checks"].items()},
                                      "found_in_runs": b["repeats"]["extraction_runs"].get("found_in"),
                                      "ceiling": t.get("ceiling") or t.get("expect_not_run"),
                                      "limited_by": t.get("limited_by"),
                                      "decision_on": i["path"].get("decision_on"),
                                      "guarded_statements": i["impact"].get("guarded_statements"),
                                      "note": "... evidence per check and the full numbers are in the json"}
    return json.dumps(keep, ensure_ascii=False, indent=1)


def pick(fs, pred, used: set):
    """First finding that matches, not used before, with a short witness (readable as an example)."""
    for limit in (900, 10 ** 9):
        for f in fs:
            if f["finding_id"] not in used and pred(f) and len(json.dumps(f["witness_hint"])) <= limit:
                used.add(f["finding_id"])
                return f
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="results/step4/limitations_for_tests.json")
    ap.add_argument("--out", default="results/step4/HANDOFF.md")
    a = ap.parse_args()
    data = json.loads((ROOT / a.src).read_text())
    fs = data["findings"]
    papers = list(dict.fromkeys(f["artifact_id"] for f in fs))
    by_paper = [(p, [f for f in fs if f["artifact_id"] == p]) for p in papers]
    by_side = [(s, [f for f in fs if side(f) == s]) for s in ("Code side", "Paper side", "Merged")]
    n_lim = sum(len(f["limitations"]) for f in fs)
    L = []
    scope =", ".join(papers) if len(papers) <= 6 else f"{len(papers)} papers"
    L += [f"# Step 4 handoff: limitations from both sides (for Shanghao; {scope})", "",
          f"> Generated automatically(`scripts/make_handoff_doc.py`), data from `{a.src}`. schema {data['schema_version']}, "
          f"witness format {data['witness_format']}. method details:  `docs/09_step4_findings.md`.", "",
          "> Quoted Chinese excerpts come from model-written records.", "",
          "## Summary", "",
          f"{len(papers)} papers contain **{n_lim} limitations**(Code side + Paper side), after deduplication **{len(fs)} Findings**. "
          "Each Finding is an object to test: it describes the conditions and resulting code behavior, with trigger and contrast points (witness_hint), "
          f"and includes all underlying records. The only file you need is: `{a.src}`.", "",
          "## 1. How limitations differ between the two sides", "",
          "| | Code side(Wanting, step 2 + 3b) | Paper side(Zhaopeng, step 1 + 3a) |",
          "|---|---|---|",
          "| Source | Checks, branches, and fallbacks found by static analysis from the entry function and an LLM | Read each paper mechanism description and find the corresponding implementation in code |",
          "| Description | “When input meets condition X, code raises an exception / changes path / changes state” | “The paper describes A; the code does B (or does not implement it)” |",
          "| Condition | A Python expression in the code(`condition.expr` + `path_prefix`) | Absent from original records; written by an LLM in step 4 and checked against code |",
          "| Consequence(effect_type) | reject / path_change / state / other …… | Almost all other: only statically assessed; consequences unconfirmed |",
          "| Evidence | Code location (single line) + text found by 3b in paper / README / docstring | Paper quote + code location (often a line range) |",
          "| ID form | `CL-X###`(route A static), `CL-B###`(route B plus LLM) | `<paper>-gap-<mechanism>-<behavior>`, e.g. `infinigen-gap-M01-B03` |",
          "| Category | undisclosed / contradicts_docs / stated_differently / docs_only / paper_stated | impl_deviates / not_implemented |",
          "| Typical witness | solved: z3 provides two concrete points on opposite sides of the boundary | always: occurs whenever the cited code is reached |",
          "| Suitable tests | Exception assertions and path instrumentation; relatively easy to write | Differential / metamorphic comparison with the paper formula; harder to write |",
          "", "When an LLM merges records from both sides about the same issue, `limitations` contains records from both sides.",
          "",
          "## 2. Counts", ""]
    L += counter_table(by_paper, ["Code side", "Paper side", "Merged"], side, "Paper") + [""]
    L += ["By category:", ""] + counter_table(by_side, CATS, lambda f: f["category"], "Side") + [""]
    L += ["| Category | Meaning |", "|---|---|"] + [f"| `{c}` | {CAT_ZH[c]} |" for c in CATS] + [""]
    L += ["By priority (1 = test first):", ""] + counter_table(by_side, [1, 2, 3], lambda f: f["priority"], "Side",
                                                         ["p1", "p2", "p3"]) + [""]
    L += ["By effect_type:", ""] + counter_table(by_side, ["reject", "path_change", "state", "accuracy", "resource",
                                                            "performance", "other"], lambda f: f["effect_type"], "Side") + [""]
    L += ["By witness status:", ""] + counter_table(by_side, WSTATUS, lambda f: f["witness_hint"].get("status"), "Side") + [""]
    L += ["By review status (blind review by LLM subagents, not humans; covers only some Code side entries):", ""] + counter_table(
        by_side, ["worth_testing", "real_but_minor", "wrong", "unreviewed"], lambda f: f["review"], "Side") + [""]

    L += ["## 3. What a record contains", "",
          "`limitations_for_tests.json` has the structure `{schema_version, witness_format, rules, note, findings: [...]}`. "
          "`findings` Each record in `findings` has the following fields:", "",
          "| Field | Content | Use in testing |", "|---|---|---|",
          "| `finding_id` | `<paper>-F###`, ordered by priority within each paper | TestCase.finding_id Use it |",
          "| `category` | See table above | Distinguish documentation, implementation, and paper hypotheses |",
          "| `priority` | 1 / 2 / 3 | Test 1 first |",
          "| `effect_type` | reject / path_change / state / … | Choose an oracle; see section 5 |",
          "| `summary` | One sentence: conditions, behavior, and location | For readers |",
          "| `witness_hint` | Trigger and contrast points and meanings of names; see section 4 | Construct test inputs |",
          "| `scope_status` | Whether within the paper scope; almost all are unknown (few Paper side parameter mappings) | Exclude out_of_scope from the main results |",
          "| `review` / `review_note` | worth_testing / real_but_minor / wrong / unreviewed, reviewer and rationale | wrong may be skipped |",
          "| `rationale` | Classification basis, merged records, priority rationale, and other Findings judged related but distinct | Inspect rationale |",
          "| `limitation_ids` / `limitations` | Full underlying Limitation records (possibly from both sides) | Inspect original conditions, paper quotes, and code locations |",
          "| `verification_ids` / `verifications` | Code side3b results: where documentation was found and its text | Inspect what the documentation says |",
          "| `confidence` | Currently all llm_assisted | — |",
          "| `process_confidence` | Code-side static evidence: status of 8 checks, repeated measurements, predicted test tier ceiling, and importance numbers (no assigned tier); see section 6; "
          "null for paper-side-only Findings | Input to tier assignment; not a test conclusion |", "",
          "Note: Some paper-side original records use “same as above” in `effect_text`, referring to the local_entry description in the same 3a record. "
          "The Finding `summary` expands it; `limitations` preserves the original.", "",
          "## 4. How to read witness_hint", "",
          "- `trigger`: a point satisfying the condition and taking the limited branch; `contrast`: the closest point to trigger that does not take that branch. Both satisfy `path_prefix`.",
          "- `atoms` explains how to construct each name: `input` takes a value directly; `local` is a local variable constructed using the expression in `aliases`"
          "(e.g. `q_len` = `q.shape[1]`); `derived` requires constructing that value (e.g. a tensor whose dimension 1 is 2); "
          "`predicate` is a boolean; mock it or choose an input(e.g. `is_flash_attn_2_available()`); "
          "`category` is a string or enum; `{\"not_in\": [...]}` means any value other than those listed.",
          "- `kind: event_sequence`(effect=state): use earlier calls to establish the trigger state, then check.",
          "- Statuses:", "",
          "| status | Meaning | How to test |", "|---|---|---|",
          "| solved | Both points are available | Use trigger / contrast directly |",
          "| solved_contrast_outside_scope | contrast is only available outside paper scope | As above; note contrast is outside paper scope |",
          "| trigger_only | The condition always holds on the path; no contrast point | Use trigger only |",
          "| always | Paper side: occurs whenever the cited code is reached | Any input reaching `code_locations` |",
          "| infeasible | The condition conflicts with the path prefix and is unreachable from the entry. `infeasible_because: call_chain` means the conflict arose after "
          "replacing callee names with entry-function names (see call chain below) | Downgraded to p3; do not spend budget |",
          "| no_condition | Paper side: no usable condition | Read `note` and summary and judge manually |",
          "| untranslatable / unknown | Condition cannot be translated / solver timed out | Read the original condition |", "",
          "Call chain (`call_chain_status`):", "",
          "| Value | Meaning |", "|---|---|",
          "| resolved | `call_chain` is the actual call chain from the entry function to the target function (entry first). `call_sites` gives the call line at each level, "
          "resolution method (`resolved_by`), and argument mapping `args` (callee parameter -> expression in caller) |",
          "| entry_is_target | The target is in the entry function |",
          "| module_level | The target is a module-level statement executed on import; no call chain |",
          "| not_found | Static analysis cannot find a call chain from entry to target (dynamic dispatch, callbacks, or target outside the entry path). "
          "`calls_entry` means this function calls the entry (e.g. framework integration); drive it directly |", "",
          "- `uncertain_steps` lists calls resolved by inference (unique method name in the repository, subclass override, or passed nested function).",
          "- `other_chains` lists other call chains (e.g. two call sites for one function).",
          "- `entry_terms`: condition and path prefix expressed in entry-function names, and the entry expression for each name"
          "(e.g. `d` -> `k.shape[3]`). When present, `aliases` also uses entry-function names.", "",
          "Known limitations:",
          "- Without a call chain (not_found), `path_prefix` still mixes conditions from different functions; the same name in caller and callee may not refer to "
          "the same thing. Aliases are used for solving only within one level; the rest are listed in `aliases_not_applied`.",
          "- For multiline statements, `snippet` is the first line after `ast.unparse`: joined into one line, with assert messages and extra parentheses removed, at most 200 characters. "
          "Compare the parsed condition, not the literal text.",
          "- Paper-side conditions are written by an LLM and checked only for names appearing in the cited code. **Their meaning may be wrong**; use them as hints.",
          "- None of the values has been verified by execution.", "",
          "## 5. Choose an oracle by effect (suggestions)", "",
          "| effect_type | Meaning | Suggested oracle |", "|---|---|---|"]
    L += [f"| {e} | {m} | {o} |" for e, m, o in ORACLE] + [""]

    pc = [f for f in fs if f.get("process_confidence")]
    if pc:
        by_paper_pc = [(p, [f for f in items if f.get("process_confidence")]) for p, items in by_paper]

        def ceiling(f):
            t = f["process_confidence"]["testability"]
            return "Not measured" if not t.get("measured") else t["ceiling"] if t.get("testable") else "Untestable"

        L += ["## 6. Code-side static evidence (uncalibrated, no assigned tier)", "",
              "Each Finding with a code-side record has a `process_confidence` block (format `process-confidence-v2`, rules in "
              "`docs/11_process_confidence.md`). It supplements your tier: **the code side does not assign a tier; your test evidence alone determines it**. "
              "It executes no code and calls no model; identical inputs produce identical results. The block has four parts.", "",
              "**1. `checks`: checklist. ** The terms match your defeater table: "
              "`eliminated`(checked by a tool), `residual`(argument or model judgment only), `open`(not assessed), `refuted`(check failed).", "",
              "| Check | Corresponding test concept | Your equivalent | Condition for `eliminated` |", "|---|---|---|---|",
              "| C1 location | Input validity | D12 | The statement at the line in the pinned commit is the recorded snippet |",
              "| C2 condition | Statement decision | D2 | Condition is the statement decision expression or its negation |",
              "| C3 reachability | Reachability (R in RIPR) | D1, D14 | A static call chain runs from the official entry to the target with no inferred steps |",
              "| C4 feasibility | Infeasible path | witness | z3 finds trigger and contrast points under the full path prefix |",
              "| C5 extraction | Analysis repeatability | D8 | Found by the static route, or by the LLM route in every extraction run (same file and line) |",
              "| C6 effect_label | Oracle matches statement | D4, effect type | The labeled effect can be determined at the statement (reject must raise an exception; path_change must be if / while) |",
              "| C7 documentation | Absence claim, informational only | — | 3b found the original text; not_found cannot prove absence and is residual; inconsistent results across 3 repeats are also residual |",
              "| C8 review | Inspection | — | Reviewed by a human; LLM blind review is residual, unreviewed is open |", "",
              "**2. `repeats`: repeated measurements. ** `extraction_runs`: number of extraction runs containing this location (`found_in` / `of`); "
              "`documentation_check`: number of 3b repeats and result agreement rate; `routes`: routes that found it (`ast` static, `llm`).", "",
              "**3. `testability`: predicted ceiling for your test tier. ** Derived from your rules, not a forecast; the actual tier may be lower.", "",
              "| Field | Meaning |", "|---|---|",
              "| `testable: false` + `expect_not_run` | C4 refuted predicts `witness_unusable`; effect `other` predicts `outcome_unsupported` |",
              "| `mutants` / `mutants_needed` | Number of mutants your `mutate.generate` can create at the target line; fewer than `n_min`(4) leaves D3 unresolved |",
              "| `ceiling` | `L1`: Too few mutants; `L2`: No call chain, D14 at most residual; `L3`: No static restriction |",
              "| `limited_by` | Which defeater limits the tier and why |",
              "| `condition_has_calls`, `integer_boundary` | Whether the condition contains calls (affects direct evaluation for D2); whether boundary variables are all integers (affects adjacent points for D5) |", "",
              "Comparison with existing test reports (130 tested across 7 papers): **none had an actual tier above the predicted ceiling**, and 98 equaled it; "
              "all 48 predicted `outcome_unsupported` and 12 predicted `witness_unusable` matched. This uses the same data and is not independent validation.", "",
              "**4. `importance`: importance, separate from confidence. **", "",
              "- `path.decision_on`: `main` evaluates the decision on every call; `side` places it inside an `if` / `except` / `case` "
              "(see `enclosing_conditions` within the function, `conditional_call_sites` on the call chain); `unknown` has no call chain and cannot see the caller.",
              "- `impact`: number of statements controlled by the decision (branch body, or statements remaining after assert / raise), total statements in the function, "
              "number of call chains from the entry, and resolved call sites to this function in the repository.",
              "- `coverage`: number of decisions (if / while / assert) in the target function, how many the code side listed, and whether the entry can statically reach it. "
              "This is **analysis coverage**, not execution coverage; execution coverage is in your `execution_report.json`.", "",
              "**Suggested use**: Before testing, allocate budget by `ceiling` (skip `Untestable`, spend less time on `L1`); after testing, put `limited_by` "
              "beside the tier to explain whether the statement limits the tier or testing was insufficient; for untested Findings, list `checks` and `repeats` together as deterministic evidence; "
              "use `importance` only for ordering, not tier assignment.", "",
              "Predicted test tier ceiling:", ""]
        L += counter_table(by_paper_pc, ["Untestable", "L1", "L2", "L3", "Not measured"], ceiling, "Paper") + [""]
        L += ["Decision on main or side path:", ""] + counter_table(
            by_paper_pc, ["main", "side", "unknown"],
            lambda f: f["process_confidence"]["importance"]["path"].get("decision_on"), "Paper") + [""]

    L += ["## 7. Typical examples", "", "Each example is a compact Finding with long fields truncated; full content is in the json. "
          "Examples are the first automatically selected by the rules. The “Paper side · LLM-written condition” example illustrates its limitation: "
          "the condition is formally solvable but may not capture the essence of the paper difference, so use paper-side conditions only as hints.", ""]
    ex = [
        ("Code side · undisclosed · p1 · with aliases", lambda f: side(f) == "Code side" and f["priority"] == 1
         and f["witness_hint"].get("aliases")),
        ("Code side · stated_differently(documentation is weaker than code)", lambda f: side(f) == "Code side"
         and f["category"] == "stated_differently" and f["witness_hint"].get("status") == "solved"),
        ("Code side · docs_only(in README / docstring, absent from paper)", lambda f: side(f) == "Code side" and f["category"] == "docs_only"),
        ("Code side · state(event sequence)", lambda f: side(f) == "Code side" and f["effect_type"] == "state"),
        ("Code side · infeasible(likely unreachable, p3)", lambda f: f["witness_hint"].get("status") == "infeasible"),
        ("Merged", lambda f: side(f) == "Merged"),
        ("Paper side · impl_deviates · always", lambda f: side(f) == "Paper side" and f["witness_hint"].get("status") == "always"
         and len(f["limitations"]) > 1),
        ("Paper side · LLM-written condition solved", lambda f: side(f) == "Paper side" and f["witness_hint"].get("status") == "solved"),
        ("Paper side · not_implemented", lambda f: f["category"] == "not_implemented"),
        ("Paper side · no_condition", lambda f: f["witness_hint"].get("status") == "no_condition"),
    ]
    used: set = set()
    for title, pred in ex:
        f = pick(fs, pred, used)
        if f:
            L += [f"### {title}: `{f['finding_id']}`", "", "```json", compact(f), "```", ""]

    L += ["## 8. Index of all Findings", "",
          "Each paper is sorted by priority. Columns: Side = Code / Paper / Merged; "
          "Review = review status (✓ worth_testing, ~ real_but_minor, ✗ wrong, blank = unreviewed); "
          "Ceiling Path = process-confidence ceiling and decision path (section 6; blank for Paper side).", ""]
    mark = {"worth_testing": "✓", "real_but_minor": "~", "wrong": "✗", "unreviewed": ""}
    sd = {"Code side": "Code", "Paper side": "Paper", "Merged": "Merged"}
    for p, items in by_paper:
        L += [f"### {p}({len(items)} findings)", "",
              "| ID | Side | Category | P | effect | witness | Review | Ceiling Path | Location | Content |", "|---|---|---|---|---|---|---|---|---|---|"]
        for f in items:
            w = f["witness_hint"]
            loc = w.get("location") or (w.get("code_locations") or [""])[0]
            b = f.get("process_confidence")
            t = b["testability"] if b else {}
            proc = (f"{t.get('ceiling') or ('Untestable' if t.get('measured') else '')} "
                    f"{b['importance']['path'].get('decision_on', '')}").strip() if b else ""
            L.append(f"| {f['finding_id'].split('-')[-1]} | {sd[side(f)]} | {f['category']} | {f['priority']} | "
                     f"{f['effect_type']} | {w.get('status')} | {mark[f['review']]} | {proc} | `{short(loc, 60)}` | "
                     f"{short(f['summary'].rsplit(' (', 1)[0] if side(f) != 'Paper side' else f['summary'], 100)} |")
        L.append("")
    (ROOT / a.out).write_text("\n".join(L))
    print(f"wrote {a.out}: {len(fs)} findings, {len(L)} lines")


if __name__ == "__main__":
    main()
