"""Build our paper-to-code evidence matrix from frozen local artifacts."""
from collections import Counter
from pathlib import Path
import re
import subprocess

from paperprobe.io import read_json, write_json

ROOT = Path(__file__).resolve().parents[1]


def build():
    mappings = read_json(ROOT / "workstreams/zhaopeng/atomic-mappings.json")
    cases = {}
    for pid, specs in mappings.items():
        run = ROOT / "runs/team-final-20261108" / pid
        reviewed = ROOT / "runs/team-handoff-20261108" / pid
        manifest = read_json(run / "manifest.json")
        commit = manifest["commit"]
        assert commit == read_json(reviewed / "manifest.json")["commit"]
        paper = read_json(run / "paper-side.json")
        checks = {x["target_id"]: x for x in read_json(run / "3a.detail.json")["checks"]}
        rows = []
        for group, key in (("claims", "claim_id"), ("scope", "scope_id"),
                           ("eval_points", "eval_id"), ("paper_limitations", "limitation_id")):
            for row in paper[group]:
                uid = row[key]
                rows.append({"id": uid, "kind": group, "record": row,
                             "check": checks.get(uid), "origin": "model_draft"})
        reviewed_paper = read_json(reviewed / "paper-side.json")
        parent = reviewed_paper["paper_limitations"][0]
        atomic = []
        for label, statement, status, file, start, end, anchor, *basis in specs:
            base = reviewed_paper["claims"][0] if basis == ["claim"] or pid == "sparta" else parent
            src = None
            if file:
                repo = ROOT / "data/repos" / f"team-{pid}"
                lines = subprocess.check_output(["git","-C",str(repo),"show",f"{commit}:{file}"],
                                                text=True).splitlines()
                snippet = "\n".join(lines[start-1:end])
                if not 1 <= start <= end <= len(lines) or anchor not in snippet:
                    raise ValueError(f"Missing pinned anchor: {pid}:{file}:{start}")
                src = {"file":file,"start":start,"end":end,"quote":snippet}
            atomic.append({"label":label,"statement":statement,"status":status,"source":src,
                           "parent":base.get("claim_id") or base["limitation_id"],
                           "evidence":base.get("evidence", base.get("paper_evidence"))})
        rejected = read_json(run / "step1-rejected.json")
        reason_counts = Counter(re.sub(r"PDF page \d+", "PDF page", x["reason"]) for x in rejected)
        cases[pid] = {"commit":commit,"paper_evidence":parent["paper_evidence"],
                      "atomic":atomic,"records":rows,"rejected":dict(reason_counts)}
    return {"cases":cases,"execution":"not_run","review":"AI-assisted static notes; team review pending"}


if __name__ == "__main__":
    write_json(ROOT / "runs/paper-evidence-matrix/matrix.json", build())
