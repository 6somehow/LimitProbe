"""An LLM as the first labeller of the human labelling sheets (C1b, first pass).

The sheets (`labels.py`) ask two questions per tested Finding:
  q1  is the claim true of the code at that location?        true / false / unclear
  q2  does the test, as designed, show it?                    valid / invalid / unclear
This module answers them with an OpenAI model, without ever showing it the harness verdict, the level or the
defeaters, and writes one sheet per independent sample, in the same format as the human sheets, so that
`labels evaluate` treats them like any other rater. The LLM labels are a first pass for the humans to check
(`compare` lists the items where they disagree with the harness); they are not ground truth.

The API key is read from a file at run time, kept in memory only, sent only in the Authorization header, and
removed from every error message. It is never written to the sheets, the prompts or the logs.
"""
from __future__ import annotations

import csv
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Optional

from .labels import COLUMNS, Q1, Q2, read_sheet
from .models import PIPELINE_ROOT

API = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-6.1-sol"
CONTEXT_LINES = 30

SYSTEM = """You are a careful reviewer of software test claims. You are given a claim about what a piece of research code \
does, the code around the location the claim is about, and an automated test written for the claim. Judge only from \
what you are shown. Answer with one JSON object and nothing else."""

QUESTIONS = """Answer two questions.

q1 "is the claim true of the code?": read the claim, the condition and the code. Is it true that, when the condition \
holds, the code at that location does what the claim says (for example raises that exception, or takes that branch)? \
A claim that is true but trivial still counts as true. Answer "true", "false" or "unclear" (unclear only if the shown \
code is not enough to decide).

q2 "does the test show it?": decide whether the test, as designed, demonstrates the claim:
  * the driver calls the product's own entry point or a function the product itself calls (not a copy of the logic);
  * the trigger run takes the claimed path or raises the claimed exception at that location, and the contrast run does \
not, and the only difference between the two inputs is the condition under test;
  * nothing in the test replaces the code being judged with a stand-in that decides the outcome.
Answer "valid", "invalid" or "unclear". Calling an inner function directly is acceptable when the driver says why, \
but say so in the reason if the product's entry point cannot reach it.

Return {"q1": "true|false|unclear", "q1_reason": "<at most 50 words>", "q2": "valid|invalid|unclear", \
"q2_reason": "<at most 50 words>"}."""


# --------------------------------------------------------------------------- context for one item
def _numbered(path: Path, line: int, n: int = CONTEXT_LINES) -> str:
    lines = path.read_text(errors="replace").splitlines()
    a, b = max(1, line - n), min(len(lines), line + n)
    return "\n".join(f"{i:5d}{'>' if i == line else ' '} {lines[i - 1]}" for i in range(a, b + 1))


def _first_line(loc: str) -> tuple[str, int]:
    m = re.match(r"^(.*?):(\d+)", loc or "")
    return (m.group(1), int(m.group(2))) if m else ("", 0)


def build_prompt(row: dict[str, str], results_root: Path, repo_rel: str, max_driver_chars: int = 9000) -> str:
    """Everything a reviewer needs, none of what the harness concluded."""
    fid, art = row["finding_id"], row["artifact"]
    tdir = results_root / "tests" / art / fid
    form = json.loads((tdir / "attempt" / "form.json").read_text())
    rep = json.loads((tdir / "execution_report.json").read_text())
    file, line = _first_line(row["code_location"])
    code = ""
    if file and (PIPELINE_ROOT / repo_rel / file).exists():
        code = _numbered(PIPELINE_ROOT / repo_rel / file, line)
    d = form.get("design", {})
    ex = form.get("execution", {})
    driver = (tdir / "attempt" / "driver.py").read_text()
    if len(driver) > max_driver_chars:
        driver = driver[:max_driver_chars] + "\n# ... (truncated)"
    mocks = [{k: m.get(k) for k in ("symbol", "kind", "behavior", "reason")} for m in ex.get("mocks", [])]
    parts = [
        "## Claim", row["claim"], "",
        f"Condition under which the claim applies: {row['condition'] or '(not given)'}",
        f"Location: {row['code_location']}",
        f"Where the claim came from: {row['step4_category']}",
    ]
    if row["paper_or_docs_quote"]:
        parts += ["", "Paper or documentation text the claim is about:", f"> {row['paper_or_docs_quote']}"]
    parts += ["", f"## Code around the location (`>` marks the line; {repo_rel}/{file})", "```python", code or "(not available)", "```", "",
              "## The test",
              f"Entry the driver calls: {ex.get('entry_called')}  (reason for a deeper entry, if any: {ex.get('entry_reason')})",
              f"Inputs, trigger run: {json.dumps(rep['positive']['inputs'])[:600]}",
              f"Inputs, contrast run: {json.dumps(rep['negative']['inputs'])[:600]}",
              f"Declared expectation: trigger {d.get('expected', {}).get('positive')!r}; contrast {d.get('expected', {}).get('negative')!r}",
              f"Stand-ins (mocks) used: {json.dumps(mocks) if mocks else 'none'}",
              f"What happened, trigger run: {row['trigger_run']}",
              f"What happened, contrast run: {row['contrast_run']}", "",
              "driver.py:", "```python", driver, "```", "", QUESTIONS]
    return "\n".join(parts)


# --------------------------------------------------------------------------- the API call
class LLMError(RuntimeError):
    pass


def _scrub(text: str, key: str) -> str:
    return text.replace(key, "<KEY>") if key else text


def chat(prompt: str, key: str, model: str = DEFAULT_MODEL, n: int = 1, timeout: int = 300,
         opener: Optional[Callable[..., Any]] = None) -> dict[str, Any]:
    body = {"model": model, "n": n, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise LLMError(_scrub(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}", key)) from None
    except Exception as e:
        raise LLMError(_scrub(f"{type(e).__name__}: {str(e)[:200]}", key)) from None


def parse_answer(text: str) -> dict[str, str]:
    """The model's JSON, with the answers clamped to the allowed values (anything else becomes 'unclear')."""
    try:
        d = json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        try:
            d = json.loads(m.group(0)) if m else {}
        except ValueError:
            d = {}
    q1 = str(d.get("q1", "")).strip().lower()
    q2 = str(d.get("q2", "")).strip().lower()
    return {"q1": q1 if q1 in Q1 else "unclear", "q2": q2 if q2 in Q2 else "unclear",
            "q1_reason": " ".join(str(d.get("q1_reason", "")).split())[:400],
            "q2_reason": " ".join(str(d.get("q2_reason", "")).split())[:400]}


# --------------------------------------------------------------------------- the run
def label(sheet: Path, results_root: Path, out_dir: Path, key_file: Path, samples: int = 3, model: str = DEFAULT_MODEL,
          workers: int = 4, repo_of: Optional[Callable[[str], str]] = None,
          opener: Optional[Callable[..., Any]] = None) -> dict[str, Any]:
    from .agent_batch import artifact_paths
    key = key_file.read_text().strip()
    if not key:
        raise LLMError(f"{key_file} is empty")
    repo_of = repo_of or (lambda art: artifact_paths(art)[2])
    rows = list(read_sheet(sheet).values())
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(row: dict[str, str]) -> dict[str, Any]:
        prompt = build_prompt(row, results_root, repo_of(row["artifact"]))
        try:
            resp = chat(prompt, key, model, n=samples, opener=opener)
            answers = [parse_answer(c["message"]["content"] or "") for c in resp["choices"]]
            usage = resp.get("usage", {})
        except LLMError as e:
            answers, usage = [], {"error": str(e)}
        return {"item_id": row["item_id"], "finding_id": row["finding_id"], "prompt_chars": len(prompt),
                "answers": answers, "usage": usage, "prompt": prompt}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, rows))
    name = model.replace(".", "")
    for s in range(samples):
        p = out_dir / f"sheet_{name}_{s + 1}.csv"
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            for row, res in zip(rows, results):
                a = res["answers"][s] if s < len(res["answers"]) else {"q1": "", "q2": "", "q1_reason": "no answer", "q2_reason": ""}
                w.writerow({**{k: row[k] for k in COLUMNS[:11]}, "q1_finding_true": a["q1"], "q2_test_valid": a["q2"],
                            "notes": f"q1: {a['q1_reason']} | q2: {a['q2_reason']}"})
    (out_dir / "llm_log.json").write_text(json.dumps(
        {"model": model, "samples": samples, "items": [{k: v for k, v in r.items() if k != "prompt"} for r in results]},
        indent=1) + "\n")
    (out_dir / "llm_prompts.jsonl").write_text("".join(json.dumps({"item_id": r["item_id"], "prompt": r["prompt"]}) + "\n" for r in results))
    errors = [r["item_id"] for r in results if not r["answers"]]
    toks = sum(r["usage"].get("total_tokens", 0) for r in results)
    return {"model": model, "items": len(rows), "samples": samples, "errors": errors, "total_tokens": toks,
            "sheets": sorted(p.name for p in out_dir.glob("sheet_*.csv"))}


def compare(sheets: list[Path], key: Path) -> list[dict[str, Any]]:
    """Items where the LLM's majority label does not confirm the harness (for a human to read first)."""
    from .labels import majority
    data = [read_sheet(p) for p in sheets]
    k = json.loads(key.read_text())["items"]
    out = []
    for i, info in k.items():
        q1 = majority([d[i]["q1_finding_true"] for d in data if i in d])
        q2 = majority([d[i]["q2_test_valid"] for d in data if i in d])
        confirmed = q1 == "true" and q2 == "valid"
        if (info["verdict"] == "yes" and not confirmed) or (info["verdict"] != "yes" and confirmed):
            notes = [d[i]["notes"] for d in data if i in d][:1]
            out.append({"item_id": i, "finding_id": info["finding_id"], "harness": f"{info['verdict']}/{info['level']}",
                        "llm_q1": q1, "llm_q2": q2, "note": notes[0] if notes else ""})
    return out
