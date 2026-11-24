"""Command line for the code side.

  python -m codeside.cli extract  --repo third_party/FlexPrefill \
      --entry flex_prefill/ops/flex_prefill_attention.py::flex_prefill_attention \
      --artifact flexprefill --out out/flexprefill_regions.json
  python -m codeside.cli evaluate --pred out/flexprefill_regions.json \
      --gold data/pilot_flexprefill/gold_regions.json
  python -m codeside.cli to-limitations --regions out/flexprefill_regions.json \
      --out out/flexprefill_code_limitations.json
  python -m codeside.cli validate data/pilot_flexprefill/*.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from codeside.evaluate import compare_routes, evaluate_regions, stability
from codeside.extractor import ExtractConfig, extract
from schema.models import ALL_MODELS, Limitation, Region

EFFECT = {"reject": "reject", "fallback": "path_change", "env_dependent": "other",
          "state_dependent": "state", "suspicious": "other"}


def _load_regions(path: str) -> list[Region]:
    return TypeAdapter(list[Region]).validate_json(Path(path).read_text())


def _llm_client(a: argparse.Namespace):
    from codeside.llm_extractor import AnthropicClient, SoclaasClient

    return (AnthropicClient if a.provider == "anthropic" else SoclaasClient)(model=a.model)


def _dump(objs, out: str) -> None:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps([o.model_dump(mode="json") for o in objs], indent=2,
                                    ensure_ascii=False) + "\n")


def cmd_extract(a: argparse.Namespace) -> None:
    regions = extract(ExtractConfig(repo=Path(a.repo), entry=a.entry, artifact_id=a.artifact,
                                    max_depth=a.max_depth,
                                    package_roots=tuple(a.package_root or ["."])))
    _dump(regions, a.out)
    print(f"{len(regions)} regions -> {a.out}")


def cmd_evaluate(a: argparse.Namespace) -> None:
    pred, gold = _load_regions(a.pred), _load_regions(a.gold)
    print(evaluate_regions(pred, gold, tol=a.tol, one_to_one=a.one_to_one).report(gold, pred))


def cmd_extract_llm(a: argparse.Namespace) -> None:
    from codeside.llm_extractor import PROMPT_VERSION, client_settings, extract_with_llm

    cfg = ExtractConfig(repo=Path(a.repo), entry=a.entry, artifact_id=a.artifact,
                        max_depth=a.max_depth, package_roots=tuple(a.package_root or ["."]))
    client = _llm_client(a)
    res = extract_with_llm(cfg, client)
    _dump(res.regions, a.out)
    meta = {"route": "direct", "prompt_version": PROMPT_VERSION, **client_settings(client),
            "raw_items": res.raw_items, "rejected": len(res.rejected),
            "hallucination_rate": res.hallucination_rate, "context_functions": res.context_functions,
            "context_chars": res.context_chars, "rejected_items": res.rejected}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"{len(res.regions)} regions ({len(res.rejected)} rejected) -> {a.out}")


def cmd_extract_hybrid(a: argparse.Namespace) -> None:
    from codeside.hybrid_extractor import extract_hybrid
    from codeside.llm_extractor import client_settings

    cfg = ExtractConfig(repo=Path(a.repo), entry=a.entry, artifact_id=a.artifact,
                        max_depth=a.max_depth, package_roots=tuple(a.package_root or ["."]))
    client = _llm_client(a)
    res = extract_hybrid(cfg, client, workers=a.workers)
    _dump(res.regions, a.out)
    meta = {**res.meta, **client_settings(client)}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"{meta['candidates_from_static']} candidates + {meta['added_regions']} added = {meta['final_regions']} regions "
          f"(failed calls {len(meta['failed_calls'])}) -> {a.out}")


def cmd_extract_agent(a: argparse.Namespace) -> None:
    from codeside.agent_extractor import extract_agent
    from codeside.llm_extractor import SoclaasClient, client_settings

    cfgs = [ExtractConfig(repo=Path(a.repo), entry=e, artifact_id=a.artifact, max_depth=a.max_depth,
                          package_roots=tuple(a.package_root or ["."])) for e in a.entry]
    client = SoclaasClient(model=a.model)
    res = extract_agent(cfgs, client, paper=a.paper or "", max_steps=a.max_steps, max_total_tokens=a.max_tokens)
    _dump(res.regions, a.out)
    meta = {**res.meta, **client_settings(client)}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"{meta['candidates_from_static']} candidates + {meta['added_regions']} added "
          f"({meta['added_outside_static_walk']} outside the static walk), {meta['rejected']} rejected, "
          f"stop={meta['stop_reason']}, steps={meta['steps']} -> {a.out}")


def cmd_extract_sweep(a: argparse.Namespace) -> None:
    from codeside.llm_extractor import SoclaasClient, client_settings
    from codeside.sweep_extractor import extract_sweep

    cfgs = [ExtractConfig(repo=Path(a.repo), entry=e, artifact_id=a.artifact, max_depth=a.max_depth,
                          package_roots=tuple(a.package_root or ["."])) for e in a.entry]
    client = SoclaasClient(model=a.model)
    res = extract_sweep(cfgs, client, paper=a.paper or "", workers=a.workers)
    _dump(res.regions, a.out)
    meta = {**res.meta, **client_settings(client)}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"{meta['candidates_from_static']} candidates + {meta['added_regions']} added "
          f"({meta['added_outside_static_walk']} outside the static walk), {meta['rejected']} rejected, "
          f"{meta['chunks']} chunks in {meta['python_files_read']} files, failed {len(meta['failed_calls'])} -> {a.out}")


def cmd_filter(a: argparse.Namespace) -> None:
    from codeside.llm_extractor import SoclaasClient, client_settings
    from codeside.relevance_filter import filter_additions

    regions = _load_regions(a.regions)
    side = Path(a.regions).with_suffix(".meta.json")
    base = json.loads(side.read_text())["candidates_from_static"] if side.is_file() else a.static_count
    if base is None:
        sys.exit("need the .meta.json next to --regions, or --static-count")
    client = SoclaasClient(model=a.model)
    kept, log = filter_additions(client, Path(a.repo), regions[base:], a.paper or "", a.entry, workers=a.workers)
    _dump(regions[:base] + kept, a.out)
    meta = {"route": "filter", "source": a.regions, "candidates_from_static": base,
            "added_before": len(regions) - base, "added_regions": len(kept), **log, **client_settings(client)}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"{base} route-A regions kept, additions {len(regions) - base} -> {len(kept)} {log['counts']} -> {a.out}")


def cmd_merge(a: argparse.Namespace) -> None:
    from codeside.dedup import dedup_additions

    static, added, sources = None, [], []
    for path in a.inputs:
        regions = _load_regions(path)
        base = json.loads(Path(path).with_suffix(".meta.json").read_text())["candidates_from_static"]
        if static is None:
            static = regions[:base]
        elif [r.location for r in regions[:base]] != [r.location for r in static]:
            sys.exit(f"{path}: route-A regions differ from {a.inputs[0]}; merge outputs of the same entries only")
        seen = {(r.location.file, r.location.line_start) for r in added}
        new = [r for r in regions[base:] if (r.location.file, r.location.line_start) not in seen]
        sources.append({"file": path, "additions": len(regions) - base, "new": len(new)})
        added += new
    kept, log = dedup_additions(Path(a.repo), static, added)
    kept = [r.model_copy(update={"region_id": f"B{i + 1:03d}"}) for i, r in enumerate(kept)]
    _dump(static + kept, a.out)
    meta = {"route": "merged", "candidates_from_static": len(static), "sources": sources,
            "added_before_dedup": len(added), "added_regions": len(kept), "final_regions": len(static) + len(kept),
            "dedup": log}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"{len(static)} route-A regions + {len(kept)} additions (from {len(added)}; "
          f"{len(log['checked_upstream'])} checked upstream, {len(log['merged_same_switch'])} merged) -> {a.out}")


def cmd_stability(a: argparse.Namespace) -> None:
    gold = _load_regions(a.gold) if a.gold else None
    print(json.dumps(stability([_load_regions(p) for p in a.runs], gold), indent=2))


def cmd_compare(a: argparse.Namespace) -> None:
    gold = _load_regions(a.gold)
    routes, meta = {}, {}
    for spec in a.pred:
        name, path = spec.split("=", 1)
        routes[name] = _load_regions(path)
        side = Path(path).with_suffix(".meta.json")
        if side.is_file():
            meta[name] = json.loads(side.read_text())
    print(compare_routes(gold, routes, tol=a.tol, meta=meta, one_to_one=a.one_to_one))


def cmd_to_limitations(a: argparse.Namespace) -> None:
    effect = {**EFFECT, "mechanism_variant": "path_change"} if a.include_variants else EFFECT
    out = []
    for r in _load_regions(a.regions):
        if r.outcome not in effect:
            continue
        out.append(Limitation(
            limitation_id=f"CL-{r.region_id}", artifact_id=r.artifact_id, origin="code",
            condition_text=r.condition.expr, condition=r.condition, effect_type=effect[r.outcome],
            effect_text=r.outcome_detail or r.outcome, code_evidence=[r.location],
            region_ids=[r.region_id], provenance=r.provenance))
    _dump(out, a.out)
    print(f"{len(out)} code-side limitations -> {a.out}")


def cmd_validate(a: argparse.Namespace) -> None:
    bad = 0
    for path in a.files:
        data = json.loads(Path(path).read_text())
        records = data if isinstance(data, list) else (
            [data] if "artifact_id" in data and "_note" not in data
            else [r for k, v in data.items() if isinstance(v, list) for r in v])
        for rec in records:
            ok = False
            for model in ALL_MODELS.values():
                try:
                    model.model_validate(rec)
                    ok = True
                    break
                except ValidationError:
                    continue
            if not ok:
                bad += 1
                print(f"INVALID in {path}: {str(rec)[:120]}")
        print(f"checked {path}: {len(records)} records")
    sys.exit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser(prog="codeside")
    sub = ap.add_subparsers(required=True)
    e = sub.add_parser("extract")
    e.add_argument("--repo", required=True)
    e.add_argument("--entry", required=True, help="relative/path.py::function")
    e.add_argument("--artifact", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--max-depth", type=int, default=3)
    e.add_argument("--package-root", action="append",
                   help="directory (relative to repo) for absolute imports; repeatable")
    e.set_defaults(fn=cmd_extract)
    v = sub.add_parser("evaluate")
    v.add_argument("--pred", required=True)
    v.add_argument("--gold", required=True)
    v.add_argument("--tol", type=int, default=2)
    v.add_argument("--one-to-one", action="store_true", help="a prediction can claim only one gold region")
    v.set_defaults(fn=cmd_evaluate)
    el = sub.add_parser("extract-llm", help="route B: LLM extraction (needs .[llm] + API key)")
    el.add_argument("--repo", required=True)
    el.add_argument("--entry", required=True)
    el.add_argument("--artifact", required=True)
    el.add_argument("--out", required=True)
    el.add_argument("--model", required=True, help="model id, e.g. the team's chosen Claude model")
    el.add_argument("--provider", choices=["soclaas", "anthropic"], default="soclaas")
    el.add_argument("--max-depth", type=int, default=3)
    el.add_argument("--package-root", action="append")
    el.set_defaults(fn=cmd_extract_llm)
    h = sub.add_parser("extract-hybrid", help="route B: route A + LLM (edges, discover); never removes A regions")
    h.add_argument("--repo", required=True)
    h.add_argument("--entry", required=True)
    h.add_argument("--artifact", required=True)
    h.add_argument("--out", required=True)
    h.add_argument("--model", required=True)
    h.add_argument("--provider", choices=["soclaas", "anthropic"], default="soclaas")
    h.add_argument("--max-depth", type=int, default=3)
    h.add_argument("--workers", type=int, default=6)
    h.add_argument("--package-root", action="append")
    h.set_defaults(fn=cmd_extract_hybrid)
    ag = sub.add_parser("extract-agent", help="route B-agent: route A + an LLM exploring the whole repo with tools")
    ag.add_argument("--repo", required=True)
    ag.add_argument("--entry", required=True, action="append", help="starting point; repeatable")
    ag.add_argument("--artifact", required=True)
    ag.add_argument("--out", required=True)
    ag.add_argument("--model", required=True)
    ag.add_argument("--paper", help="paper title, shown to the agent")
    ag.add_argument("--max-depth", type=int, default=3)
    ag.add_argument("--max-steps", type=int, default=60)
    ag.add_argument("--max-tokens", type=int, default=800_000, help="token budget for the whole run")
    ag.add_argument("--package-root", action="append")
    ag.set_defaults(fn=cmd_extract_agent)
    sw = sub.add_parser("extract-sweep", help="route B-sweep: route A + an LLM reading every chunk of code-chosen files")
    sw.add_argument("--repo", required=True)
    sw.add_argument("--entry", required=True, action="append", help="repeatable")
    sw.add_argument("--artifact", required=True)
    sw.add_argument("--out", required=True)
    sw.add_argument("--model", required=True)
    sw.add_argument("--paper", help="paper title, shown to the model")
    sw.add_argument("--max-depth", type=int, default=3)
    sw.add_argument("--workers", type=int, default=6)
    sw.add_argument("--package-root", action="append")
    sw.set_defaults(fn=cmd_extract_sweep)
    fl = sub.add_parser("filter", help="second look at route B's additions; route A regions are never removed")
    fl.add_argument("--regions", required=True)
    fl.add_argument("--repo", required=True)
    fl.add_argument("--entry", required=True, action="append")
    fl.add_argument("--paper")
    fl.add_argument("--out", required=True)
    fl.add_argument("--model", required=True)
    fl.add_argument("--workers", type=int, default=6)
    fl.add_argument("--static-count", type=int, help="number of route-A regions at the start, if no .meta.json")
    fl.set_defaults(fn=cmd_filter)
    mg = sub.add_parser("merge", help="route A + several route-B outputs, deduplicated without an LLM")
    mg.add_argument("inputs", nargs="+", help="B outputs with .meta.json, all from the same entries")
    mg.add_argument("--repo", required=True)
    mg.add_argument("--out", required=True)
    mg.set_defaults(fn=cmd_merge)
    st = sub.add_parser("stability", help="agreement across repeated runs")
    st.add_argument("runs", nargs="+")
    st.add_argument("--gold")
    st.set_defaults(fn=cmd_stability)
    cp = sub.add_parser("compare", help="compare routes on the same gold")
    cp.add_argument("--gold", required=True)
    cp.add_argument("--pred", action="append", required=True, help="name=path, repeatable")
    cp.add_argument("--tol", type=int, default=2)
    cp.add_argument("--one-to-one", action="store_true", help="a prediction can claim only one gold region")
    cp.set_defaults(fn=cmd_compare)
    t = sub.add_parser("to-limitations")
    t.add_argument("--regions", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--include-variants", action="store_true",
                   help="also export mechanism_variant regions (as effect_type path_change); off by default")
    t.set_defaults(fn=cmd_to_limitations)
    c = sub.add_parser("validate")
    c.add_argument("files", nargs="+")
    c.set_defaults(fn=cmd_validate)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
