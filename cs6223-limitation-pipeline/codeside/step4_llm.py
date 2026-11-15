"""Step 4 LLM helpers (docs/09_step4_findings.md): the two judgements rules cannot make.

  same      are two limitations the same issue? Asked only for candidate pairs chosen mechanically
            (paper-paper: same Zhaopeng finding candidate or identical code evidence; code-paper: overlapping
            code locations). Up to three samples, majority; "same" needs two yes votes.
  condition turn a paper-side limitation (text + cited code) into a Python condition over code names, so
            the witness solver can run on it. The reply is checked against the code: every name in the
            expression must occur in the cited lines, otherwise it is rejected.

Every call goes through verify3b.ChatLLM (disk cache, retries, usage) and every answer is returned with
its votes so step 4 can store it.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Optional

from codeside.verify3b import parse_json
from schema.models import Limitation

PROMPT_VERSION = "step4-v1"
SAMPLES = 3
MAX_CODE_LINES = 40

SYSTEM = ("You review limitations of research software: conditions under which the code behaves differently "
          "from what its paper describes, or rejects / changes / degrades its work. Answer only with JSON.")

SAME_PROMPT = """Do these two records describe the SAME limitation of the artifact {artifact}?

Same means: one concrete behaviour of the code (one check, one hard-coded choice, one missing feature) that a
single test would exercise. Two different checks in the same function, or a general design gap and one specific
check inside it, are NOT the same. Different wording or different source (paper side vs code side) of one
behaviour IS the same.

Record A
{a}

Record B
{b}

Reply as JSON: {{"same": "yes" | "no" | "unsure", "reason": "<one sentence>"}}"""

COND_PROMPT = """A paper-side review of the artifact {artifact} found this gap between the paper and its code.

{record}

Write the INPUT condition under which this gap shows up when the code runs, as one Python boolean expression
over names that appear in the code above (function parameters, locals, attributes such as `q.shape[1]`).
- Use only names that occur in the code lines shown. No new helper names.
- If the gap shows up on every call (a design or formula difference, a missing feature), answer kind "always".
- If it depends on something that is not an input value (hardware, build, timing), answer kind "not_input".
- path_prefix: conditions of enclosing branches that must hold to reach the code, same rules; may be empty.

Reply as JSON: {{"kind": "condition" | "always" | "not_input", "expr": "<python or empty>",
"path_prefix": ["<python>", ...], "reason": "<one sentence>"}}"""


def read_lines(repo: Optional[Path], file: str, start: int, end: Optional[int]) -> str:
    if repo is None:
        return ""
    p = repo / file
    if not p.is_file():
        return ""
    lines = p.read_text(errors="replace").splitlines()
    end = min(end or start, start + MAX_CODE_LINES - 1)
    return "\n".join(f"{i:5d}  {lines[i - 1]}" for i in range(max(start, 1), min(end, len(lines)) + 1))


def describe(lim: Limitation, repo: Optional[Path]) -> str:
    out = [f"origin: {lim.origin}", f"condition: {lim.condition.expr if lim.condition else lim.condition_text}"[:700],
           f"effect: {lim.effect_text}"[:500]]
    for q in lim.paper_evidence[:1]:
        out.append(f"paper quote: {' '.join(q.quote.split())}"[:400])
    for c in lim.code_evidence[:2]:
        out.append(f"code {c.file}:{c.line_start}-{c.line_end or c.line_start}")
        text = read_lines(repo, c.file, c.line_start, c.line_end)
        if text:
            out.append(text)
    return "\n".join(out)


def _names(tree: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out - {"True", "False", "None", "len", "min", "max", "abs", "isinstance", "int", "float", "any", "all",
                  "sum", "range", "bool", "str", "tuple", "list", "dict", "set"}


def check_condition(expr: str, prefix: list[str], code: str) -> Optional[str]:
    """None if expr and prefix parse and every name occurs in `code`, else why not."""
    words = set(re.findall(r"[A-Za-z_]\w*", code))
    for e in [expr, *prefix]:
        try:
            tree = ast.parse(e.strip(), mode="eval")
        except SyntaxError:
            return f"not a Python expression: {e!r}"
        missing = sorted(_names(tree) - words)
        if missing:
            return f"names not in the cited code: {', '.join(missing)}"
    return None


class Judge:
    def __init__(self, llm, artifact_id: str, repo: Optional[Path]):
        self.llm, self.artifact_id, self.repo = llm, artifact_id, repo

    def _ask(self, prompt: str, key: str) -> Any:
        for attempt in range(3):
            try:
                return parse_json(self.llm.complete(SYSTEM, prompt, f"{PROMPT_VERSION}:{key}#{attempt}"))
            except ValueError:
                continue
        return None

    def same(self, a: Limitation, b: Limitation) -> dict:
        da, db = describe(a, self.repo), describe(b, self.repo)
        if a.limitation_id > b.limitation_id:  # order-independent cache key and prompt
            a, b, da, db = b, a, db, da
        prompt = SAME_PROMPT.format(artifact=self.artifact_id, a=da, b=db)
        votes = []
        for i in range(SAMPLES):
            r = self._ask(prompt, f"same:{a.limitation_id}|{b.limitation_id}:{i}") or {}
            votes.append({"same": str(r.get("same", "unsure")).lower(), "reason": r.get("reason", "")})
            yes = sum(v["same"] == "yes" for v in votes)
            if i == 1 and yes in (0, 2) and votes[0]["same"] == votes[1]["same"]:
                break  # two agreeing samples decide
        yes = sum(v["same"] == "yes" for v in votes)
        return {"pair": [a.limitation_id, b.limitation_id], "same": yes >= 2, "votes": votes}

    def condition(self, lim: Limitation) -> dict:
        record = describe(lim, self.repo)
        r = self._ask(COND_PROMPT.format(artifact=self.artifact_id, record=record), f"cond:{lim.limitation_id}") or {}
        kind = r.get("kind") if r.get("kind") in ("condition", "always", "not_input") else "none"
        if kind == "condition" and (r.get("expr") or "").strip() in ("", "True") and not r.get("path_prefix"):
            kind = "always"  # "condition: True" with no path is the same answer as "always"
        out = {"kind": kind, "expr": (r.get("expr") or "").strip(), "path_prefix": [p for p in r.get("path_prefix") or []
                                                                                  if isinstance(p, str) and p.strip()],
               "reason": r.get("reason", ""), "model": getattr(self.llm, "model", "?")}
        if kind == "condition":
            code = "\n".join(read_lines(self.repo, c.file, c.line_start, c.line_end) for c in lim.code_evidence)
            why = check_condition(out["expr"], out["path_prefix"], code) if out["expr"] else "empty expression"
            if why:
                out.update(kind="rejected", rejected_because=why)
        return out


def dump(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=1, ensure_ascii=False))
