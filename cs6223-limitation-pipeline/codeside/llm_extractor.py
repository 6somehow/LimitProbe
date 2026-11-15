"""Step 2, route B: region-table extraction by an LLM.

Same input and output as the static route (`extractor.py`), so the two can be
compared on the same gold:

  1. Context: starting from the entry function, collect the source of every
     reachable function (same call resolution as the static route, so both
     routes see the same code). Each line is prefixed with `file:line`.
  2. Prompt: ask the model for a JSON list of regions (condition -> outcome).
  3. Validation (identical rules for any route): the file/function must be in
     the context, the line must fall inside that function, the condition must
     parse as a Python expression, the outcome must be a known value.
     Rejected items are counted, not silently dropped (`hallucination rate`).

The LLM client is pluggable; tests use a fake client. No API key is read here.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Optional, Protocol

from codeside.extractor import ExtractConfig, RegionExtractor
from schema.models import CodeLocation, Condition, Outcome, Region

OUTCOMES = [o.value for o in Outcome]
PROMPT_VERSION = "direct-v1"


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class AnthropicClient:
    """Minimal wrapper; requires `pip install anthropic` and ANTHROPIC_API_KEY."""

    def __init__(self, model: str, max_tokens: int = 8000, temperature: float = 0.0):
        import anthropic  # imported lazily so the package works without it

        self._client = anthropic.Anthropic()
        self.model, self.max_tokens, self.temperature = model, max_tokens, temperature

    def complete(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=system, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


class SoclaasClient:
    """OpenAI-compatible endpoint; reads SOCLAAS_API_KEY / SOCLAAS_BASE_URL from the env or `.env`."""

    def __init__(self, model: str, max_tokens: int = 8000, temperature: float = 0.0,
                 reasoning_effort: str = "none"):
        import os

        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        self._client = OpenAI(api_key=os.environ["SOCLAAS_API_KEY"],
                              base_url=os.environ["SOCLAAS_BASE_URL"].rstrip("/"))
        self.model, self.max_tokens, self.temperature = model, max_tokens, temperature
        self.reasoning_effort = reasoning_effort
        self.resolved_model: Optional[str] = None  # the served model; an ID like x-test-2 can be repointed
        self.prompt_tokens = self.completion_tokens = 0
        self._lock = Lock()

    def _create(self, **kwargs):
        resp = self._client.chat.completions.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            reasoning_effort=self.reasoning_effort, **kwargs)
        with self._lock:
            self.resolved_model = resp.model
            if resp.usage:
                self.prompt_tokens += resp.usage.prompt_tokens or 0
                self.completion_tokens += resp.usage.completion_tokens or 0
        if resp.choices[0].finish_reason == "length":
            raise RuntimeError(f"LLM output truncated at max_tokens={self.max_tokens}")
        return resp

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        """One turn with tool calling; returns the assistant message, ready to append to `messages`."""
        msg = self._create(messages=messages, tools=tools).choices[0].message
        out: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            out["tool_calls"] = [{"id": c.id, "type": "function",
                                  "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                 for c in msg.tool_calls]
        return out

    def complete(self, system: str, user: str) -> str:
        resp = self._create(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        choice = resp.choices[0]
        return choice.message.content or ""


def client_settings(client) -> dict:
    """What the comparison protocol requires us to record about a run."""
    keys = ("model", "resolved_model", "temperature", "max_tokens", "reasoning_effort",
            "prompt_tokens", "completion_tokens")
    return {k: getattr(client, k) for k in keys if hasattr(client, k)}


@dataclass
class FunctionSource:
    file: str
    qual: str
    start: int
    end: int
    text: str  # numbered source


@dataclass
class LLMExtractResult:
    regions: list[Region]
    raw_items: int
    rejected: list[dict] = field(default_factory=list)
    context_functions: int = 0
    context_chars: int = 0

    @property
    def hallucination_rate(self) -> float:
        return len(self.rejected) / self.raw_items if self.raw_items else 0.0


SYSTEM = """You analyse the source code of a research prototype. List every condition under
which the code's behaviour differs from the default path of the entry function.
Use only the code shown. Quote line numbers exactly as shown. Answer with JSON only."""

USER_TEMPLATE = """Entry function: {entry}

Outcome labels:
- mechanism: the default path of the entry function (the paper's mechanism runs)
- mechanism_variant: a branch that selects a variant of the mechanism
- fallback: silently runs a baseline / dense / simpler implementation instead
- reject: an assert or raise stops execution
- env_dependent: depends on installed packages, versions, or GPU model
- state_dependent: depends on module-level or cached state from earlier calls
- suspicious: e.g. a hard-coded constant that ignores a parameter in scope

Code (each line is prefixed with file:line):
{code}

Return a JSON list. Each item:
{{"file": "...", "function": "qualified name as in the headers", "line": <int>,
  "condition": "<Python boolean expression over names in the code>",
  "outcome": "<one label>", "detail": "<what happens>",
  "path_prefix": ["<enclosing conditions, outermost first>"]}}
Include one `mechanism` item for the default path. Do not include conditions that can
never hold given the enclosing conditions."""


def collect_context(cfg: ExtractConfig) -> list[FunctionSource]:
    """Reachable functions from the entry, using the static route's call resolution."""
    rx = RegionExtractor(cfg)
    rel, fname = cfg.entry.split("::")
    res = rx._resolve(rel, fname)
    if res is None:
        raise ValueError(f"entry not found: {cfg.entry}")
    out: list[FunctionSource] = []
    seen: set[tuple[str, str]] = set()
    queue = [(res[0], fname, rx._class_of(res[0], fname), 0)]
    while queue:
        file, qual, cls, depth = queue.pop(0)
        if (file, qual) in seen or depth > cfg.max_depth:
            continue
        seen.add((file, qual))
        fn = rx._funcs[file][qual]
        lines = (Path(cfg.repo) / file).read_text(encoding="utf-8").splitlines()
        start = min([d.lineno for d in fn.decorator_list] + [fn.lineno])
        end = fn.end_lineno or fn.lineno
        numbered = "\n".join(f"{file}:{i}: {lines[i - 1]}" for i in range(start, end + 1))
        out.append(FunctionSource(file, qual, start, end, f"# --- {file}::{qual}\n{numbered}"))
        for n in ast.walk(fn):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Name):
                name, c = n.func.id, None
            elif (isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                  and n.func.value.id == "self" and cls):
                name, c = n.func.attr, cls
            else:
                continue
            r = rx._resolve(file, name, c)
            if r:
                q = next(k for k, v in rx._funcs[r[0]].items() if v is r[1])
                queue.append((r[0], q, c if r[0] == file else rx._class_of(r[0], q), depth + 1))
    return out


class LLMOutputError(ValueError):
    """The model's answer could not be read; must not be mistaken for an empty answer."""


def parse_json(text: str, expect: type = list):
    """First JSON value of the expected type in `text`, tolerating prose and code fences around it."""
    starts = [i for i in (text.find("["), text.find("{")) if i >= 0]
    if expect is dict:
        starts = [i for i in [text.find("{")] if i >= 0]
    if not starts:
        raise LLMOutputError(f"no JSON {expect.__name__} in output: {text[:120]!r}")
    start = min(starts)
    try:
        data, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        raise LLMOutputError(f"malformed JSON: {exc}") from exc
    if expect is list and isinstance(data, dict):  # a one-item list written without its brackets
        return [data]
    return data


def _parse_json_list(text: str) -> list[dict]:
    return [d for d in parse_json(text, list) if isinstance(d, dict)]


def _names_in_function(fs: FunctionSource, repo: Path) -> set[str]:
    """Identifiers visible in the function: its names and attributes, plus module-level names."""
    source = (repo / fs.file).read_text(encoding="utf-8")
    body = "\n".join(source.splitlines()[fs.start - 1:fs.end])
    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", body))
    for node in ast.parse(source).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            words |= {(a.asname or a.name).split(".")[0] for a in node.names}
    return words | {"len", "isinstance", "int", "float", "str", "bool", "max", "min", "abs", "sum", "any", "all",
                    "None", "True", "False", "hasattr", "getattr", "type", "tuple", "list", "set", "dict", "math"}


def validate_items(items: list[dict], context: list[FunctionSource], cfg: ExtractConfig,
                   provenance: str = "llm") -> tuple[list[Region], list[dict]]:
    """Shared validation: anything that cannot be checked against the source is rejected."""
    by_key = {(f.file, f.qual): f for f in context}
    regions, rejected = [], []
    for it in items:
        reason = None
        # The context headers read `file::qual`, so accept that form as well as the bare `qual`.
        fn_name = str(it.get("function") or "").split("::")[-1]
        fs = by_key.get((it.get("file"), fn_name))
        line = it.get("line")
        cond = it.get("condition", "")
        if fs is None:
            reason = "function not in context"
        elif not isinstance(line, int) or not fs.start <= line <= fs.end:
            reason = "line outside function"
        elif it.get("outcome") not in OUTCOMES:
            reason = "unknown outcome"
        elif cond != "otherwise":
            try:
                ast.parse(cond, mode="eval")
            except (SyntaxError, ValueError):
                reason = "condition does not parse"
            else:
                used = {n.id for n in ast.walk(ast.parse(cond, mode="eval")) if isinstance(n, ast.Name)}
                unknown = used - _names_in_function(fs, Path(cfg.repo))
                if unknown:
                    reason = f"condition uses names not in the function: {sorted(unknown)}"
                elif not used:
                    reason = "condition has no names"
        if reason:
            rejected.append({**it, "_reason": reason})
            continue
        src = (Path(cfg.repo) / fs.file).read_text(encoding="utf-8").splitlines()[line - 1].strip()
        names = [] if cond == "otherwise" else sorted(
            {n.id for n in ast.walk(ast.parse(cond, mode="eval")) if isinstance(n, ast.Name)})
        regions.append(Region(
            region_id=f"L{len(regions) + 1:03d}", artifact_id=cfg.artifact_id, entry_point=cfg.entry,
            condition=Condition(expr=cond, params=names, path_prefix=list(it.get("path_prefix") or [])),
            outcome=it["outcome"], outcome_detail=it.get("detail"),
            location=CodeLocation(file=fs.file, line_start=line, function=f"{fs.file}::{fs.qual}",
                                  snippet=src[:200]),
            call_chain=[], provenance=provenance))
    return regions, rejected


def extract_with_llm(cfg: ExtractConfig, client: LLMClient,
                     max_context_chars: int = 120_000) -> LLMExtractResult:
    context = collect_context(cfg)
    code, used = [], 0
    for fs in context:
        if used + len(fs.text) > max_context_chars:
            break
        code.append(fs.text)
        used += len(fs.text)
    shown = context[:len(code)]
    raw = client.complete(SYSTEM, USER_TEMPLATE.format(entry=cfg.entry, code="\n\n".join(code)))
    items = _parse_json_list(raw)
    regions, rejected = validate_items(items, shown, cfg)
    return LLMExtractResult(regions=regions, raw_items=len(items), rejected=rejected,
                            context_functions=len(shown), context_chars=used)
