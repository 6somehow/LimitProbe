#!/usr/bin/env python3
"""Summarise out/pipeline/: 3b results per artifact, split by where the limitation came from.

Route A limitations have region ids without the B prefix; route B's additions are B###.
With --labels (a JSON {"file:line": "useful" | "real_not_useful" | "wrong"}), the blind-review label is
shown next to each candidate, so candidates can be read with their quality in mind.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels")
    a = ap.parse_args()
    labels = json.loads(Path(a.labels).read_text()) if a.labels else {}
    print("| artifact | source | limitations | paper silent (not_found) | written somewhere | needs review |")
    print("|---|---|---|---|---|---|")
    cands = []
    for d in sorted((ROOT / "out/pipeline").iterdir()):
        ver, lim = d / "3b.json", d / "limitations.json"
        if not ver.is_file():
            continue
        lims = {l["limitation_id"]: l for l in json.loads(lim.read_text())}
        detail = {x["limitation_id"]: x for x in json.loads((d / "3b.detail.json").read_text())["items"]}
        rows = {"A": Counter(), "B": Counter()}
        for v in json.loads(ver.read_text()):
            l = lims[v["limitation_id"]]
            src = "B" if l["region_ids"][0].startswith("B") else "A"
            c = rows[src]
            c["n"] += 1
            c["silent" if v["result"] == "not_found" else "written"] += 1
            c["review"] += bool(detail[v["limitation_id"]]["needs_review"])
            loc = l["code_evidence"][0]
            key = f"{loc['file']}:{loc['line_start']}"
            cands.append({"artifact": d.name, "source": src, "where": key, "result": v["result"],
                          "documented_in": v.get("documented_in") or [], "label": labels.get(key, "-"),
                          "condition": l["condition_text"][:80], "effect": (l.get("effect_text") or "")[:90],
                          "needs_review": detail[v["limitation_id"]]["needs_review"]})
        for src, c in rows.items():
            if c["n"]:
                print(f"| {d.name} | {src} | {c['n']} | {c['silent']} | {c['written']} | {c['review']} |")
    out = ROOT / "out/pipeline/candidates.json"
    out.write_text(json.dumps(cands, indent=1, ensure_ascii=False))
    print(f"\nresults: {dict(Counter(c['result'] for c in cands))}")
    print(f"labels of candidates: {dict(Counter((c['source'], c['label'], c['result'] == 'not_found') for c in cands))}")
    print(f"all rows -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
