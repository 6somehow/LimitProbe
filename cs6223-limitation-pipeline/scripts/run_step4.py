#!/usr/bin/env python3
"""Step 4 on all five artifacts: code side (out/pipeline_ps) + paper side (paperside handoff) -> Findings.

Writes, per artifact, <out>/<id>/findings.json, findings.report.json, llm_records.json (every LLM
"same issue?" vote and every paper-side condition with its code check) and limitations_for_tests.json (that
artifact only), then, over every artifact in <out> (also ones not re-run with --only):
  <out>/limitations_for_tests.json   the hand-off to Shanghao: one record per Finding, self-contained
                                     (finding fields + the full Limitations + 3b Verifications behind it);
  <out>/review_queue.json            the same findings in test order, one line each;
  <out>/summary.md                   counts per artifact.
LLM calls (dedup and paper-side conditions) use verify3b.ChatLLM with a disk cache in <cache>/<id>;
--no-llm skips them (no cross-side merge, paper-side witness stays no_condition).
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(ROOT))
from codeside.callgraph import RepoCallGraph  # noqa: E402
from codeside.effect_anchor import check_effects  # noqa: E402
from codeside.integrate import Context, Rules, integrate  # noqa: E402
from codeside.scope_check import ScopeChecker  # noqa: E402
from codeside.verify3b import load_paper_side  # noqa: E402
from schema.models import SCHEMA_VERSION, Limitation, Verification  # noqa: E402

PACKAGE_ROOTS = {"infinigen": ["speedup/infinigen", "speedup/flexgen"]}  # same as pipeline/run.py
CATS = ["undisclosed", "contradicts_docs", "stated_differently", "docs_only", "paper_stated", "impl_deviates",
        "not_implemented"]


def artifact_json(aid: str) -> Path:
    for p in sorted((ROOT / "data").glob("*/artifact.json")):
        if json.loads(p.read_text())["artifact_id"] == aid:
            return p
    raise FileNotFoundError(f"no data/*/artifact.json with artifact_id {aid}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-dir", default="out/pipeline_ps", help="run_pipeline.py output (limitations + 3b)")
    ap.add_argument("--paper-dir", default="paperside/handoffs/paper-side-v1")
    ap.add_argument("--labels", default="results/review/blind_review_labels.json")
    ap.add_argument("--out", default="results/step4")
    ap.add_argument("--cache", default="out/step4_cache")
    ap.add_argument("--model", default="x-test-2")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--strict-scope", action="store_true")
    ap.add_argument("--only", nargs="*", help="artifact ids to (re)run; the top-level files still cover all")
    a = ap.parse_args()
    rules = Rules(a.strict_scope)
    labels: dict = {}
    if (ROOT / a.labels).is_file():
        for r in json.loads((ROOT / a.labels).read_text())["labels"]:
            labels.setdefault(r["artifact"], {})[(r["file"], r["line"])] = r
    load = lambda p, m: [m.model_validate(x) for x in json.loads(Path(p).read_text())]
    usage = Counter()
    for code in sorted((ROOT / a.code_dir).iterdir()):
        aid = code.name
        if not (code / "3b.json").is_file() or (a.only and aid not in a.only):
            continue
        art = json.loads(artifact_json(aid).read_text())
        repo = ROOT / "third_party" / art["repo_url"].rstrip("/").split("/")[-1]
        pd = ROOT / a.paper_dir / aid
        checker, paper_lims, groups = None, [], []
        if (pd / "paper_side.json").is_file():
            checker = ScopeChecker(*load_paper_side(str(pd / "paper_side.json")))
            paper_lims = load(pd / "limitations.json", Limitation) if (pd / "limitations.json").is_file() else []
        if (pd / "finding_candidates.json").is_file():
            groups = [set(c["behavior_ids"]) for c in json.loads((pd / "finding_candidates.json").read_text())]
        conformance = {}
        if (pd / "conformance.json").is_file():
            conformance = {x["id"]: x for x in json.loads((pd / "conformance.json").read_text())}
        judge = llm = None
        if not a.no_llm:
            from codeside.step4_llm import Judge
            from codeside.verify3b import ChatLLM
            llm = ChatLLM(a.model, cache_dir=ROOT / a.cache / aid, max_tokens=2000, retries=6)
            judge = Judge(llm, aid, repo if repo.is_dir() else None)
        cfg = artifact_json(aid).parent / "pipeline.json"  # written by `pipeline init --package-root`
        roots = (json.loads(cfg.read_text()).get("package_roots") if cfg.is_file() else None) or PACKAGE_ROOTS.get(aid)
        graph = RepoCallGraph(repo, tuple(roots or (".",))) if repo.is_dir() else None
        ctx = Context(repo=repo if repo.is_dir() else None, judge=judge, paper_groups=groups, conformance=conformance,
                      callgraph=graph, known_ids=known_ids(ROOT / a.out / aid / "findings.json"),
                      labels=labels.get(aid, {}), entry_points=[e if isinstance(e, str) else e.get("entry", "")
                                                                for e in art.get("entry_points", [])])
        code_lims, code_vers = load(code / "limitations.json", Limitation), load(code / "3b.json", Verification)
        # effect labels must fit the statement they point at (the test side judges the effect there)
        code_lims, effect_checks = check_effects(code_lims, ctx.repo)
        ctx.effect_moves = {r["limitation_id"]: r for r in effect_checks if r["action"] == "moved"}
        findings, report = integrate(aid, code_lims, code_vers, paper_lims, checker, rules, ctx)
        report["effect_checks"] = effect_checks
        records = report.pop("llm_records")
        if llm is not None:
            from codeside.step4_llm import PROMPT_VERSION as P4
            report["llm"] = {**llm.settings(), "prompt_version": P4}
            usage.update({k: v for k, v in llm.settings().items() if isinstance(v, int)})
        out = ROOT / a.out / aid
        out.mkdir(parents=True, exist_ok=True)
        (out / "findings.json").write_text(json.dumps([f.model_dump(mode="json") for f in findings], indent=1,
                                                      ensure_ascii=False))
        (out / "findings.report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
        (out / "llm_records.json").write_text(json.dumps(records, indent=1, ensure_ascii=False))
        lims = {l.limitation_id: l for l in code_lims + paper_lims}
        vers = {v.verification_id: v for v in code_vers}
        records = []
        for f in findings:
            d = f.model_dump(mode="json")
            d["limitations"] = [lims[i].model_dump(mode="json") for i in f.limitation_ids]
            d["verifications"] = [vers[i].model_dump(mode="json") for i in f.verification_ids]
            records.append(d)
        (out / "limitations_for_tests.json").write_text(json.dumps(envelope(records, rules), indent=1, ensure_ascii=False))
        print(aid, json.dumps({k: report[k] for k in ("findings", "pairs_judged_same", "by_category",
                                                        "by_priority", "witness_status")}))
    combine(ROOT / a.out, rules, usage)


def known_ids(findings_json: Path) -> dict:
    """Finding ids of the last run, by the limitations each finding is made of (ids stay stable across runs)."""
    if not findings_json.is_file():
        return {}
    return {tuple(sorted(f["limitation_ids"])): f["finding_id"] for f in json.loads(findings_json.read_text())}


def envelope(records: list, rules: Rules) -> dict:
    return {"schema_version": SCHEMA_VERSION, "witness_format": "witness-v2", "rules": rules.__dict__,
            "note": "One record per Finding (step 4). `limitations` and `verifications` are the full records behind it. "
                    "Sorted by artifact, then priority. review comes from an LLM blind review, not a human.",
            "findings": records}


def combine(out: Path, rules: Rules, usage: Counter) -> None:
    """Top-level files over every artifact that has step-4 output (not only the ones just run)."""
    handoff, queue, rows = [], [], []
    for d in sorted(p for p in out.iterdir() if (p / "limitations_for_tests.json").is_file()):
        recs = json.loads((d / "limitations_for_tests.json").read_text())["findings"]
        handoff += recs
        rows.append((d.name, json.loads((d / "findings.report.json").read_text())))
        for f in recs:
            queue.append({"finding_id": f["finding_id"], "category": f["category"], "priority": f["priority"],
                          "effect": f["effect_type"], "review": f["review"], "witness": f["witness_hint"].get("status"),
                          "where": f["witness_hint"].get("location"),
                          "sides": "+".join(sorted({l["origin"] for l in f["limitations"]})), "summary": f["summary"]})
    order = {"worth_testing": 0, "unreviewed": 1, "real_but_minor": 2, "wrong": 3}
    queue.sort(key=lambda q: (q["priority"], order[q["review"]], CATS.index(q["category"]), q["finding_id"]))
    (out / "review_queue.json").write_text(json.dumps(queue, indent=1, ensure_ascii=False))
    (out / "limitations_for_tests.json").write_text(json.dumps(envelope(handoff, rules), indent=1, ensure_ascii=False))
    lines = ["| artifact | limitations (code+paper) | findings | merged both sides | " + " | ".join(CATS) +
             " | p1/p2/p3 | witness usable |", "|---" * (len(CATS) + 6) + "|"]
    for aid, r in rows:
        cat, pr = r["by_category"], {int(k): v for k, v in r["by_priority"].items()}
        ws = r["witness_status"]
        usable = sum(n for k, n in ws.items() if k and (k.startswith("solved") or k in ("trigger_only", "always")))
        lines.append(f"| {aid} | {r['code_limitations']}+{r['paper_limitations']} | {r['findings']} | "
                     f"{r['findings_merged_both_sides']} | " + " | ".join(str(cat.get(c, 0)) for c in CATS) +
                     f" | {pr.get(1, 0)}/{pr.get(2, 0)}/{pr.get(3, 0)} | {usable}/{r['findings']} |")
    p1 = [q for q in queue if q["priority"] == 1]
    lines += ["", f"rules: {json.dumps(rules.__dict__)}; schema {SCHEMA_VERSION}; witness-v2",
              f"p1 by review: {dict(Counter(q['review'] for q in p1))}",
              f"all findings by review: {dict(Counter(q['review'] for q in queue))}",
              f"witness status: {dict(Counter(q['witness'] for q in queue))}",
              f"LLM usage (this run): {dict(usage)}"]
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
