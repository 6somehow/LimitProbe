"""Build the source-audited team handoff separately from model-draft outputs."""
import argparse
import json
import subprocess
from pathlib import Path

from .io import file_sha256, inside, read_json, stable_id, write_json
from .team_paper_side import evidence, export


def location(repo, spec):
    path, start, end, anchor = spec
    # Read the Git object, not a similarly named working-tree file.
    body = subprocess.check_output(["git","-C",str(repo),"show",f"HEAD:{path}"],text=True)
    snippet = "\n".join(body.splitlines()[start-1:end])
    if not 1 <= start <= end <= len(body.splitlines()) or anchor not in snippet:
        raise ValueError(f"Pinned code anchor missing at {path}:{start}-{end}")
    return {"file":path,"line_start":start,"line_end":end,"snippet":snippet}


def build(root, team, output):
    from pypdf import PdfReader
    source = read_json(root/"workstreams/zhaopeng/team-reviewed.json")
    artifacts = {a["artifact_id"]:a for p in team.glob("data/*/artifact.json") if (a:=read_json(p))}
    if set(artifacts) != set(source):
        raise ValueError("Handoff and team artifact sets differ")
    if output.exists():
        raise ValueError("Use a new output directory")
    prepared = {}
    for pid, spec in source.items():
        artifact = artifacts[pid]
        pdf = team/"third_party/papers"/f"{pid}.pdf"
        repo = inside(root,f"data/repos/team-{pid}")
        commit = subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
        if commit != artifact["commit"] or commit != spec["commit"] or file_sha256(pdf) != spec["pdf_sha256"]:
            raise ValueError(f"Source snapshot mismatch for {pid}")
        pages = [p.extract_text() or "" for p in PdfReader(pdf).pages]
        records = export({"id":pid},pages,spec)
        for row in spec.get("eval_envelopes",[]):
            param = row["param"]
            values = sorted({e["config"][param] for e in records["eval_points"] if param in e["config"]})
            if not values or any(type(v) not in (int,float) for v in values):
                raise ValueError(f"No numeric evaluation values for {param}")
            records["scope"].append({"scope_id":stable_id("eval-envelope",pid,param),"artifact_id":pid,
                "param":param,"kind":"set","values":values,"explicit":False,"evidence":evidence(row,pages)})
            records["bindings"].append({"binding_id":stable_id("binding",pid,param),"artifact_id":pid,
                "paper_term":param,"kind":"parameter","code_symbol":row["code_symbol"],
                "location":location(repo,row["code"]),"certain":True,"rationale":row["rationale"]})
        limitations, verification, unresolved = [], [], []
        for row in spec["cases"]:
            uid = stable_id("paper-lim",pid,row["condition_text"],row["effect_text"])
            ev = evidence(row,pages)
            locs = [location(repo,c) for c in row["code"]]
            limitations.append({"limitation_id":uid,"artifact_id":pid,"origin":"paper",
                **{k:row[k] for k in ("condition_text","effect_text","level","effect_type")},
                "paper_evidence":ev,"code_evidence":locs,"provenance":"llm",
                "notes":"Source-audited AI-assisted draft; independent team review pending. "+row["rationale"]})
            if row["result"] == "unresolved":
                unresolved.append({"limitation_id":uid,"reason":row["rationale"],"matching_code":locs})
            else:
                if row["result"] not in {"found","boundary_mismatch","weaker","contradicted"} or not locs:
                    raise ValueError("Resolved 3a requires checked code evidence")
                verification.append({"verification_id":stable_id("3a",uid),"limitation_id":uid,
                    "direction":"paper_to_code","result":row["result"],"matching_code":locs,
                    "verifier":"llm:source-audited","rationale":row["rationale"]})
        records["paper_limitations"] = limitations
        prepared[pid] = (records,verification,unresolved,
            {"artifact":pid,"commit":commit,"pdf_sha256":file_sha256(pdf),"source":"source-audited AI-assisted handoff",
             "target_execution":"not_run","independent_team_review":"pending",
             "spec_sha256":file_sha256(root/"workstreams/zhaopeng/team-reviewed.json")})
    for pid,(records,verification,unresolved,manifest) in prepared.items():
        write_json(output/pid/"paper-side.json",records)
        write_json(output/pid/"3a.json",verification)
        write_json(output/pid/"3a.unresolved.json",unresolved)
        write_json(output/pid/"manifest.json",manifest)
    print(json.dumps({p:{"paper_limitation":len(r["paper_limitations"]),"3a":len(v),"unresolved":len(u)}
                      for p,(r,v,u,_) in prepared.items()}))


if __name__ == "__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--team",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    build(Path.cwd().resolve(),args.team.resolve(),args.output.resolve())
