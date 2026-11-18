"""Analysis lane for Findings the harness cannot test (not a test verdict).

A Finding that is not_run (no code location, outcome the harness cannot judge, no repository at all, a GPU-only path)
still gets an *analysis*: what the evidence in the paper and the pinned code says about the claim, with its own, lower
confidence scale. The analysis never produces `yes` / `no` and never an L-level (CONFIDENCE_SPEC.md §22).

Three steps, in order of how much they can be trusted:
  1. static evidence check (deterministic): the files the Finding cites exist at the pinned commit, the cited lines are
     in range, and the cited snippet really is there.
  2. probes (deterministic once chosen): a language model may propose regular-expression probes over the cited files
     ("the script contains no `wget`"). The harness, not the model, runs them and reports what they found.
  3. a language-model reading of the evidence (cached): supports / contradicts / unclear, with reasons.

Tiers (uncalibrated, like every level here):
  A2  the cited code was found and at least one probe ran and agrees with the reading (an "absent" probe counts only
      with a control regex that matches in the same file)
  A1  the reading rests on text only (paper-only Finding, no repository, or no probe was possible)
  A0  nothing could be grounded (cited files or snippets missing) or the reading and the probes disagree
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

ANALYSIS_VERSION = "analysis-v1"
PROMPT_VERSION = "analysis-prompt-v1"
MAX_EXCERPT_LINES = 80
MAX_PROBES = 4
TIER_TEXT = {
    "A2": "code found at the pinned commit and a deterministic probe agrees with the reading",
    "A1": "text-only reading (no runnable code, no probe): the lowest tier",
    "A0": "evidence could not be grounded, or the reading and the probes disagree",
}

SYSTEM = ("You review claims that a research artifact differs from its paper. Judge only from the evidence shown. "
          "Answer with one JSON object and nothing else.")

TASK = """Finding: {summary}
Category: {category}   Effect: {effect}   Step 4 level: {level}
{paper}
{code}
Decide whether the evidence supports the Finding.
Return {{"assessment": "supports|contradicts|unclear", "reasoning": "<at most 90 words>",
"hardware_needed": true|false, "probes": [{{"file": "<path inside the repository, from the code shown>",
"regex": "<python regular expression>", "expect": "present|absent", "control": "<regex that DOES match somewhere in the same file; required when expect is absent>", "meaning": "<what a hit or a miss shows, 15 words>"}}],
"would_confirm": "<one sentence: what test or measurement would settle it>"}}
Rules: at most {max_probes} probes; use a probe only when a text search of one file can show the claim (a miss only counts
when the control regex hits in the same file (it shows you searched the right place); for example a
script has no download command, a flag is never read, a constant has another value); "hardware_needed" is true when the
claim concerns behaviour only visible on a GPU, an accelerator or a real run. If you cannot tell, say "unclear"."""


# --------------------------------------------------------------------------- 1. static evidence
def _read_lines(repo: Path, rel: str) -> Optional[list[str]]:
    p = (repo / rel).resolve()
    try:
        p.relative_to(repo.resolve())
    except ValueError:
        return None                                   # a path that leaves the repository is never read
    if not p.is_file():
        return None
    return p.read_text(errors="replace").splitlines()


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def static_check(raw: dict[str, Any], repo: Optional[Path]) -> dict[str, Any]:
    """Do the cited locations exist, and does the cited snippet appear there? Reads files only."""
    items: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for lim in raw.get("limitations") or []:
        for c in lim.get("code_evidence") or []:
            key = (c.get("file"), c.get("line_start"))
            if not c.get("file") or key in seen:
                continue
            seen.add(key)
            lo, hi = c.get("line_start") or 1, c.get("line_end") or c.get("line_start") or 1
            it: dict[str, Any] = {"file": c["file"], "lines": f"{lo}-{hi}", "exists": False, "in_range": False,
                                  "snippet_found": None}
            lines = _read_lines(repo, c["file"]) if repo else None
            if lines is not None:
                it["exists"] = True
                it["in_range"] = 1 <= lo <= len(lines)
                it["kind"] = _kind(c["file"])
                snip = _norm(c.get("snippet") or "")
                if snip:
                    body = _norm("\n".join(lines[max(0, lo - 1): max(hi, lo) + 5]))
                    it["snippet_found"] = snip[:200] in body or snip[:60] in _norm("\n".join(lines))
            items.append(it)
    grounded = bool(items) and all(i["exists"] and i["in_range"] for i in items)
    return {"cited": len(items), "grounded": grounded, "items": items[:6]}


def _kind(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {".py": "python", ".sh": "shell", ".md": "doc", ".txt": "doc", ".v": "rtl", ".sv": "rtl",
            ".cu": "cuda", ".cpp": "c++", ".h": "c++", ".yaml": "config", ".yml": "config", ".json": "config",
            }.get(ext, "other")


def excerpt(repo: Path, rel: str, lo: int, hi: int) -> str:
    lines = _read_lines(repo, rel)
    if not lines:
        return ""
    lo = max(1, lo)
    hi = min(len(lines), max(hi, lo), lo + MAX_EXCERPT_LINES - 1)
    return "\n".join(f"{i:5d} {lines[i - 1]}" for i in range(lo, hi + 1))


# --------------------------------------------------------------------------- 2. probes (run by the harness)
def run_probe(repo: Path, probe: dict[str, Any], cited_files: set[str]) -> dict[str, Any]:
    out = {"file": probe.get("file"), "regex": probe.get("regex"), "expect": probe.get("expect"),
           "meaning": probe.get("meaning", ""), "status": "not_run", "hits": 0}
    f, rx, exp = probe.get("file"), probe.get("regex"), probe.get("expect")
    if exp not in ("present", "absent") or not f or not rx:
        out["note"] = "malformed probe"
        return out
    if f not in cited_files:
        out["note"] = "file is not one the Finding cites"      # a probe may only look where the evidence points
        return out
    lines = _read_lines(repo, f)
    if lines is None:
        out["note"] = "file not found at the pinned commit"
        return out
    try:
        pat = re.compile(rx)
    except re.error as e:
        out["note"] = f"bad regex: {e}"
        return out
    hits = [i + 1 for i, l in enumerate(lines) if pat.search(l)]
    if exp == "absent":
        # "absent" is cheap to satisfy (any typo passes), so it only counts when a control regex shows the file
        # really is the one under discussion
        ctl = probe.get("control")
        try:
            anchored = bool(ctl) and any(re.search(ctl, l) for l in lines)
        except re.error:
            anchored = False
        out["control"] = ctl
        if not anchored:
            out["status"] = "unanchored"
            out["hits"] = len(hits)
            out["note"] = "an absence probe needs a control regex that matches in the same file"
            return out
    out["hits"] = len(hits)
    out["hit_lines"] = hits[:5]
    out["status"] = "confirmed" if (bool(hits) == (exp == "present")) else "refuted"
    return out


# --------------------------------------------------------------------------- 3. the reading
def _prompt(raw: dict[str, Any], repo: Optional[Path]) -> tuple[str, set[str]]:
    paper, code, files = [], [], set()
    for lim in raw.get("limitations") or []:
        for e in (lim.get("paper_evidence") or [])[:2]:
            paper.append(f"- paper ({e.get('locator')}): {_norm(e.get('quote'))[:500]}")
        for c in (lim.get("code_evidence") or [])[:3]:
            f = c.get("file")
            if not f:
                continue
            files.add(f)
            lo, hi = c.get("line_start") or 1, c.get("line_end") or c.get("line_start") or 1
            ex = excerpt(repo, f, lo, hi) if repo else ""
            code.append(f"- code {f}:{lo}-{hi}\n{ex or '(not available)'}" if ex else f"- code {f}:{lo}-{hi} (not available)")
    for v in (raw.get("verifications") or [])[:1]:
        for e in (v.get("matching_evidence") or [])[:1]:
            paper.append(f"- paper ({e.get('locator')}): {_norm(e.get('quote'))[:500]}")
    wh = raw.get("witness_hint") or {}
    text = TASK.format(summary=_norm(raw.get("summary"))[:600], category=raw.get("category"),
                       effect=raw.get("effect_type"), level=raw.get("level"),
                       paper="\n".join(paper[:4]) or "(no paper evidence recorded)",
                       code=("Code at the pinned commit:\n" + "\n".join(code[:3])) if code else "(no code evidence recorded)",
                       max_probes=MAX_PROBES)
    if wh.get("note"):
        text += f"\nStep 4 note: {_norm(wh['note'])[:300]}"
    return text, files


def chat(prompt: str, model: str, base_url: str, key: str, timeout: int = 300, max_tokens: int = 6000,
         opener: Optional[Callable] = None) -> str:
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from the model gateway") from None      # never echo headers or the key
    return data["choices"][0]["message"].get("content") or ""


def parse_answer(text: str) -> dict[str, Any]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in the answer")
    d = json.loads(m.group(0))
    if d.get("assessment") not in ("supports", "contradicts", "unclear"):
        d["assessment"] = "unclear"
    d["probes"] = [p for p in (d.get("probes") or []) if isinstance(p, dict)][:MAX_PROBES]
    d["hardware_needed"] = bool(d.get("hardware_needed"))
    return d


def tier(static: dict[str, Any], reading: Optional[dict[str, Any]], probes: list[dict[str, Any]]) -> tuple[str, str]:
    if reading is None:
        return "A0", "the language model gave no usable reading"
    ran = [p for p in probes if p["status"] in ("confirmed", "refuted")]
    if static["cited"] and not static["grounded"]:
        return "A0", "a cited file or line does not exist at the pinned commit"
    if not static["cited"]:
        return "A1", "no code is cited: the reading rests on the paper text alone"
    a = reading["assessment"]
    if ran:
        ok = [p for p in ran if p["status"] == "confirmed"]
        if a == "supports" and len(ok) == len(ran):
            return "A2", "the probes confirm what the Finding says"
        if a == "contradicts" and not ok:
            return "A2", "the probes agree with the reading that the Finding is wrong"
        if a == "unclear":
            return "A1", "the reading is unclear; probes alone do not decide it"
        return "A0", "the reading and the probes disagree"
    return "A1", "code was found but no probe could be run on it"


def analyze(raw: dict[str, Any], repo: Optional[Path], *, model: str, base_url: str, key: str,
            cache_dir: Optional[Path] = None, ask: Optional[Callable[[str], str]] = None) -> dict[str, Any]:
    """One analysis block for a Finding. `ask` replaces the model call in tests."""
    st = static_check(raw, repo)
    prompt, files = _prompt(raw, repo)
    ck = hashlib.sha256((PROMPT_VERSION + model + prompt).encode()).hexdigest()[:20]
    cache = cache_dir / f"{raw['finding_id']}-{ck}.json" if cache_dir else None
    reading: Optional[dict[str, Any]] = None
    err = ""
    if cache and cache.exists():
        reading = json.loads(cache.read_text())
    else:
        try:
            fn = ask or (lambda p: chat(p, model, base_url, key))
            for attempt in range(2):                      # an empty or cut-off answer is retried once
                try:
                    reading = parse_answer(fn(prompt))
                    break
                except (ValueError, KeyError):
                    if attempt:
                        raise
            if cache:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(reading, indent=1))
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:200]}"
    probes = [run_probe(repo, p, files) for p in (reading or {}).get("probes", [])] if repo else []
    t, why = tier(st, reading, probes)
    return {"version": ANALYSIS_VERSION, "kind": "analysis_only", "tier": t, "tier_note": why, "calibrated": False,
            "assessment": (reading or {}).get("assessment", "unclear"),
            "reasoning": (reading or {}).get("reasoning", ""),
            "hardware_needed": (reading or {}).get("hardware_needed", False),
            "would_confirm": (reading or {}).get("would_confirm", ""),
            "static": st, "probes": probes, "model": model, "error": err or None}
