#!/usr/bin/env python
"""Measure the 3b skills on cases with known answers. See tests/fixtures/eval_3b_cases.json."""

from __future__ import annotations

import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

from codeside.doc_index import pdf_passages
from codeside.verify3b import ChatLLM, Verifier, load_paper_side, run_paper_tier
from schema.models import Condition, Limitation

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/pilot_flexprefill"
SKILLS = ("retrieve", "fullpaper", "sweep", "consensus")
TITLES = {a: json.loads((ROOT / f"data/{a}/artifact.json").read_text())["paper_title"]
          for a in ("minference", "nnsmith", "infinigen", "sparta")}


def make_limitation(c: dict, artifact: str) -> Limitation:
    return Limitation(limitation_id=c["id"], artifact_id=artifact, origin="code", condition_text=c["condition_text"],
                      condition=Condition(expr=c["expr"], params=c["params"]), effect_type=c["effect_type"],
                      effect_text=c["effect_text"], provenance="manual")


class PlantVerifier(Verifier):
    """Sweeps only the section holding the plant, still asking about every limitation at once."""

    def __init__(self, *a, plant_id: str, all_lims: list[Limitation], **kw):
        super().__init__(*a, **kw)
        self.plant_id, self.all_lims = plant_id, all_lims

    def sections(self):
        return [s for s in super().sections() if any(p.passage_id == self.plant_id for p in s[1])]

    def sweep_section(self, section, passages, lims):
        return super().sweep_section(section, passages, self.all_lims)


def plant(paper, case):
    """A copy of the paper with the sentence added to a body passage chosen by the case id."""
    body = [p for p in paper if p.source == "paper" and p.locator.split()[0] in ("3", "4", "6")]
    target = random.Random(case["id"]).choice(body)
    return [replace(p, text=f"{p.text} {case['text']}") if p is target else p for p in paper], target.passage_id


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="x-test-2")
    ap.add_argument("--out", default="out/3b/eval_cases.json")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    out_path = ROOT / a.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    llm = ChatLLM(a.model, cache_dir=out_path.parent / "llm_cache")
    cases = json.loads((ROOT / "tests/fixtures/eval_3b_cases.json").read_text())
    lims = {l["limitation_id"]: Limitation.model_validate(l)
            for l in json.loads((DATA / "gold_code_limitations.json").read_text())}
    _, _, bindings = load_paper_side(str(DATA / "paper_side_stub.json"))
    title = json.loads((DATA / "artifact.json").read_text())["paper_title"]
    paper = pdf_passages(ROOT / "third_party/papers/flexprefill.pdf")
    rows = []
    with ThreadPoolExecutor(a.workers) as pool:
        def planted_case(c):
            with ThreadPoolExecutor(4) as inner:
                text, pid = plant(paper, c)
                v = PlantVerifier(llm, title, text, [], bindings, plant_id=pid, all_lims=list(lims.values()), repeat=hash_key(c))
                res = run_paper_tier(v, [lims[c["limitation"]]], "consensus", inner)[c["limitation"]]
            plant_quote = c["text"]
            return [{"kind": "planted", "case": c["id"], "skill": s, "expected": [c["label"]], "got": res[s].result,
                     "cites_plant": any(e["quote"] in plant_quote or plant_quote in e["quote"] for e in res[s].evidence),
                     "evidence": res[s].evidence, "gate_failures": res[s].gate_failures, "rationale": res[s].rationale}
                    for s in SKILLS]

        for rs in pool.map(planted_case, cases["planted"]):
            rows += rs

        near = [make_limitation(c, "flexprefill") for c in cases["near_miss"]]
        res = run_paper_tier(Verifier(llm, title, paper, [], bindings), near, "consensus", pool)
        for lid, judged in res.items():
            for s in SKILLS:
                rows.append({"kind": "near_miss", "case": lid, "skill": s, "expected": ["not_found"], "got": judged[s].result,
                             "evidence": judged[s].evidence, "gate_failures": judged[s].gate_failures,
                             "rationale": judged[s].rationale})

        for art in sorted({c["paper"] for c in cases["real_positive"]}):
            group = [c for c in cases["real_positive"] if c["paper"] == art]
            ps = pdf_passages(ROOT / f"third_party/papers/{art}.pdf")
            judged_all = run_paper_tier(Verifier(llm, TITLES[art], ps, [], []),
                                        [make_limitation(c, art) for c in group], "consensus", pool)
            for c in group:
                for s in SKILLS:
                    j = judged_all[c["id"]][s]
                    rows.append({"kind": "real_positive", "case": c["id"], "skill": s, "expected": c["expected"],
                                 "got": j.result, "evidence": j.evidence, "gate_failures": j.gate_failures,
                                 "rationale": j.rationale})

    out_path.write_text(json.dumps({"settings": llm.settings(), "rows": rows}, indent=2, ensure_ascii=False))
    print(llm.settings())
    report(rows)


def hash_key(case: dict) -> int:
    return sum(map(ord, case["id"]))


def report(rows: list[dict]) -> None:
    print(f"{'skill':<11}{'planted label ok':<20}{'planted detected':<20}{'near-miss false +':<20}{'real positive ok':<18}")
    for s in SKILLS:
        sub = [r for r in rows if r["skill"] == s]
        pl = [r for r in sub if r["kind"] == "planted"]
        nm = [r for r in sub if r["kind"] == "near_miss"]
        rp = [r for r in sub if r["kind"] == "real_positive"]
        ok = sum(r["got"] in r["expected"] for r in pl)
        det = sum(r["got"] != "not_found" and r["cites_plant"] for r in pl)
        fp = sum(r["got"] != "not_found" for r in nm)
        rok = sum(r["got"] in r["expected"] for r in rp)
        print(f"{s:<11}{f'{ok}/{len(pl)}':<20}{f'{det}/{len(pl)}':<20}{f'{fp}/{len(nm)}':<20}{f'{rok}/{len(rp)}':<18}")
    print("\nby planted label (label correct / detected):")
    for label in ("found", "boundary_mismatch", "weaker", "contradicted"):
        cells = []
        for s in SKILLS:
            pl = [r for r in rows if r["skill"] == s and r["kind"] == "planted" and r["expected"] == [label]]
            cells.append(f"{s} {sum(r['got'] == label for r in pl)}/{sum(r['got'] != 'not_found' for r in pl)}/{len(pl)}")
        print(f"  {label:<18}", "  ".join(cells))


if __name__ == "__main__":
    main()
