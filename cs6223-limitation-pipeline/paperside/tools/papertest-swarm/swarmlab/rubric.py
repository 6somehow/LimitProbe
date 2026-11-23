"""Structured rubric grading: four auditable yes/no questions per report.

Holistic core/partial/miss grading drifted on boundary cases. This scorer asks the
same decomposition the reference rubric uses (rule, trigger, consequence, and the
reference's own partial-clue allowance) and derives the label deterministically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contract import parse_json
from .grade import MATCHES, reference_rows, summarize
from .llm import Client
from .util import dump, load, secret_env

RUBRIC_SYSTEM = """You audit one frozen finding report against one human reference diagnosis. Judge only the single retained record that best matches the reference's rule. Answer four factual questions about THAT record; do not infer an average over records.

Definitions:
- rule: the decision, representation or mechanism the reference names.
- trigger: the input transformation, variation or condition under which the reference's problem appears.
- consequence: what the reference says may then be missed or degraded.
- clue: the reference explicitly treats an observed signal (for example a score or position change) as a partial clue rather than a full diagnosis.

Return only JSON:
{"record_id":"<best id or null>",
 "same_rule":true|false,
 "same_trigger":true|false,
 "same_consequence":true|false,
 "clue_only":true|false,
 "reason":"<=100 Chinese characters naming the decisive overlap or difference",
 "test_ready_ids":["ids with a controlled comparison and an oracle"],
 "supported_ids":["ids whose own evidence supports their scoped claim"]}
Answer false when the record only discusses a related but different rule (a different variable, a different decision, or a different representation), even if the topic overlaps."""


def derive(answers: dict) -> str:
    if answers.get("same_rule") and answers.get("same_trigger") and answers.get("same_consequence"):
        return "core"
    if answers.get("clue_only"):
        return "partial"
    if answers.get("same_rule") and (answers.get("same_trigger") or answers.get("same_consequence")):
        return "partial"
    return "miss"


def grade(packet_dir: Path, grades_dir: Path, client: Client) -> None:
    grades_dir = Path(grades_dir)
    grades_dir.mkdir(parents=True, exist_ok=True)
    references = reference_rows(Path("/Users/pp/Desktop/AgentSwarm/reference/reference-rubric-20261121.md"))
    for path in sorted(Path(packet_dir).glob("*.json")):
        if path.name == "mapping.json":
            continue
        ident = path.stem
        if (grades_dir / f"{ident}.json").exists():
            continue
        packet = load(path)
        reference = packet.get("reference") or references[packet["case"]]
        user = {"reference": reference, "records": packet["records"]}
        response = client.chat(
            [{"role": "system", "content": RUBRIC_SYSTEM},
             {"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
            tools=[], max_tokens=4000, thinking=False,
        )
        text = response["message"].get("content") or ""
        try:
            answers = parse_json(text)
        except ValueError:
            answers = {"record_id": None, "same_rule": False, "same_trigger": False,
                       "same_consequence": False, "clue_only": False,
                       "reason": "grader produced no parsable JSON"}
        ids = {record["id"] for record in packet["records"]}
        if answers.get("record_id") not in ids:
            answers["record_id"] = None
        match = derive(answers)
        if match not in MATCHES:
            raise ValueError(f"bad derived match {match}")
        out = {
            "report_id": ident, "match": match,
            "record_id": answers.get("record_id"),
            "reason": str(answers.get("reason") or "")[:160],
            "answers": {key: bool(answers.get(key)) for key in
                        ("same_rule", "same_trigger", "same_consequence", "clue_only")},
            "test_ready_ids": [x for x in (answers.get("test_ready_ids") or []) if x in ids],
            "supported_ids": [x for x in (answers.get("supported_ids") or []) if x in ids],
        }
        dump(grades_dir / f"{ident}.json", out)
        print(f"{ident} {packet['paper']} {match} {out['record_id']} {out['answers']}", flush=True)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packets", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    env = secret_env()
    client = Client(env["SOCLAAS_API_KEY"],
                    env.get("SOCLAAS_BASE_URL", "https://soclaas-api.comp.nus.edu.sg/v1"),
                    archive=args.out / "requests", max_tokens=4000, timeout=300)
    for packet_dir in args.packets:
        grade(packet_dir, args.out, client)
    if args.summary:
        dump(args.summary, summarize(args.packets, args.out))
        print(json.dumps(load(args.summary), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
