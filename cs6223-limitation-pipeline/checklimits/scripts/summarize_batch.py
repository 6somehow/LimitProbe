"""Summarise an agent batch: python scripts/summarize_batch.py scratch/batches/b1 [more result dirs] > BATCH_RESULTS.md

Reads <dir>/b*-*.json written by checklimits.agent_batch plus the findings file for category / effect type / review.
Distributions only: these Findings have no ground truth."""
import json
import sys
from collections import Counter
from pathlib import Path

FF = Path(__file__).resolve().parents[2] / "results/step4/flexprefill/limitations_for_tests.json"
import os
if os.environ.get("BATCH_FINDINGS"):
    FF = Path(os.environ["BATCH_FINDINGS"])


def main(dirs):
    recs = {r["finding_id"]: r for r in json.loads(FF.read_text())["findings"]}
    runs = []
    for d in dirs:
        for f in sorted(Path(d).glob("*.json")):
            if f.name == "summary.json":
                continue
            runs.append(json.loads(f.read_text()))
    out = ["# Agent batch over step 4 FlexPrefill findings", "",
           f"{len(runs)} runs. Distributions only: there is no ground truth for these Findings, so `yes` is not accuracy, "
           "and the levels are uncalibrated.", ""]
    ok = [r for r in runs if r.get("level")]
    out += ["## Verdicts and levels", "", "| | count |", "|---|---|"]
    for k, v in sorted(Counter((r.get("final_verdict"), r.get("level")) for r in runs).items(), key=str):
        out.append(f"| {k[0]} / {k[1]} | {v} |")
    out += ["", "## Per finding", "", "| finding | outcome | review | verdict | level | integrity | calls | tokens (M) | s | not eliminated |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(runs, key=lambda r: r["finding"]):
        rec = recs.get(r["finding"], {})
        t = ""
        out.append("| {f} | {o} | {rv} | {v} | {l} | {i} | {c} | {tk:.2f} | {w} | {d} |".format(
            f=r["finding"].split("-")[-1], o=rec.get("effect_type", "?"), rv=rec.get("review", "?"), v=r.get("final_verdict"),
            l=r.get("level"), i=r.get("form_integrity"), c=r.get("tool_calls"), tk=(r.get("tokens") or 0) / 1e6,
            w=int(r.get("wall_s") or 0), d=", ".join(f"{k}={v[:3]}" for k, v in (r.get("defeaters") or {}).items()
                                                      if v != "eliminated" and k != "D13") or (r.get("error") or "")[:60]))
    dc = Counter()
    for r in ok:
        for k, v in (r.get("defeaters") or {}).items():
            if v != "eliminated" and k != "D13":
                dc[(k, v)] += 1
    out += ["", "## What keeps findings below L3", "", "| defeater | state | runs |", "|---|---|---|"]
    out += [f"| {k} | {s} | {n} |" for (k, s), n in sorted(dc.items())]
    odd = [r for r in runs if r.get("final_verdict") != "yes"]
    out += ["", "## Runs that did not end in `yes` (read these first)", ""]
    for r in odd:
        out += [f"* **{r['finding']}**: verdict={r.get('verdict')} final={r.get('final_verdict')} level={r.get('level')}; "
                f"{r.get('positive')} | {r.get('negative')}; {r.get('error') or ''}"]
        out += [f"    - {s[:200]}" for s in (r.get("next_steps") or [])[:3]]
    if not odd:
        out.append("none")
    tot = lambda k: sum(r.get(k) or 0 for r in runs)
    out += ["", "## Cost", "", f"tool calls {tot('tool_calls')}, LLM steps {tot('llm_steps')}, tokens {tot('tokens') / 1e6:.1f}M "
            "(counts every re-sent context), agent wall time {:.0f} min summed over runs.".format(tot("wall_s") / 60)]
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
