"""A bounded, guided 3a check using a fixed set of source-audited excerpts."""
import argparse
from pathlib import Path

from paperprobe.io import read_json, stable_id, write_json
from paperprobe.team_run import CODE_PROMPT, call, verify_checks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--handoff", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--model", required=True)
    args = ap.parse_args()
    targets, source, reference = [], {}, {}
    for path in sorted(args.handoff.glob("*/paper-side.json")):
        known = {v["limitation_id"]: v["result"] for v in read_json(path.with_name("3a.json"))}
        for row in read_json(path)["paper_limitations"]:
            uid = row["limitation_id"]
            targets.append({"id":uid,"kind":"limitation","artifact":row["artifact_id"],
                "text":row["condition_text"]+"; "+row["effect_text"],"paper_evidence":row["paper_evidence"]})
            source[uid] = {stable_id("src", uid, loc):loc for loc in row["code_evidence"]}
            reference[uid] = known.get(uid,"unresolved")
    if len(targets) != 5:
        raise SystemExit("Expected exactly five fixed guided cases")
    args.output.mkdir(parents=True,exist_ok=False)
    raw, meta = call(args.model,CODE_PROMPT,{"targets":targets,"source":source},args.output/"response.json")
    checks, verifications = verify_checks(raw,targets,source,meta["model"])
    write_json(args.output/"3a.json",verifications)
    write_json(args.output/"3a.detail.json",{"checks":checks,"model":meta,
        "source_audited_draft_labels":reference,"independent_gold":False,
        "design":"One guided batch; supplied relevant source excerpts; cannot measure automatic localization."})
    print("resolved",len(verifications),"of",len(targets))


if __name__ == "__main__":
    main()
