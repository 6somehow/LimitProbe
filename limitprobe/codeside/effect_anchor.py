"""Step 4: check that the effect label of a code-side limitation fits the statement it points at.

Convention agreed with the test side (checklimits/REQUESTS_TO_STEP4.md, request 5). The test side judges an
effect at the target location (checklimits/runner.py, `outcome_support`):

  reject        an exception raised by the target statement itself: `assert`, `raise`, or an
                `if` / `while` / `for` / `with` / `try` with a `raise` in its body;
  path_change   a branch decision: the target is an `if` or a `while`;
  state         the same, after earlier calls.

Route B (LLM) sometimes labels what the program does in the end ("rejected") on a statement that only
starts it (`while not check_sat():`, a flag assignment). The harness then looks for an exception that can
never come from that line. This module repairs the label with the AST only, no LLM:

  reject, target cannot raise
      `except X:` header with a raise in the handler  -> target moves to that raise          (moved)
      anything else (`if` / `while` without a raise,
      a call, an assignment)                           -> other, with the reason               (relabelled)
      A `reject` on a branch is not turned into `path_change`: "the branch is taken" is a weaker claim than
      "the input is rejected", and a `yes` for it would read as a confirmed rejection.
  path_change / state, target is not a branch
      directly in the body of an `if` / `while` whose test is the limitation's condition
                                                       -> target moves to that branch          (moved)
      anything else                                    -> other, with the reason               (relabelled)

`other` is the honest label for "the effect is a changed value or an exception from a callee": it needs
another oracle (differential), and the report can say why the finding was not tested.
A moved target is also reported in the Finding's witness_hint as `effect_location` (the statement that produces
the effect, now also `code_evidence[0]`) next to `labelled_location` (where the label pointed).
Nothing is changed when the file or the statement cannot be found.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path
from typing import Optional

from codeside.dedup import normalise
from schema.models import Limitation

RAISE_CAPABLE = (ast.If, ast.While, ast.For, ast.With, ast.Try)
BRANCH_EFFECTS = ("path_change", "state")
_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@lru_cache(maxsize=256)
def _tree(path: str) -> Optional[ast.Module]:
    try:
        return ast.parse(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return None


def _has_raise(stmts: list[ast.stmt]) -> bool:
    return any(isinstance(n, ast.Raise) for s in stmts for n in ast.walk(s))


def can_raise(node: ast.stmt) -> bool:
    """Same rule as checklimits.tracer.can_raise_here."""
    if isinstance(node, (ast.Assert, ast.Raise)):
        return True
    if isinstance(node, RAISE_CAPABLE):
        return _has_raise([*getattr(node, "body", []), *getattr(node, "orelse", [])])
    return False


def _statement_at(tree: ast.Module, line: int) -> Optional[ast.stmt]:
    """The innermost statement that starts at `line` (not a def or a class)."""
    best = None
    for n in ast.walk(tree):
        if isinstance(n, ast.stmt) and not isinstance(n, _DEFS) and n.lineno == line:
            best = n  # ast.walk is breadth-first: later hits are deeper
    return best


def _handler_at(tree: ast.Module, line: int) -> Optional[ast.ExceptHandler]:
    return next((n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler) and n.lineno == line), None)


def _enclosing_branch(tree: ast.Module, target: ast.stmt) -> Optional[ast.stmt]:
    """The `if` / `while` whose body directly holds `target`."""
    for n in ast.walk(tree):
        if isinstance(n, (ast.If, ast.While)) and any(s is target for s in n.body):
            return n
    return None


def _kind(node: ast.AST) -> str:
    return type(node).__name__.lower()


def check_effect(lim: Limitation, repo: Path) -> tuple[Limitation, Optional[dict]]:
    """Return the limitation (a corrected copy if needed) and a record of the change, or None."""
    if lim.origin != "code" or not lim.code_evidence:
        return lim, None
    effect = lim.effect_type
    if effect != "reject" and effect not in BRANCH_EFFECTS:
        return lim, None
    loc = lim.code_evidence[0]
    tree = _tree(str(Path(repo) / loc.file))
    if tree is None:
        return lim, None
    line = loc.line_start
    node = _statement_at(tree, line)
    where = f"{loc.file}:{line}"
    move_to, new_effect, why = None, None, ""

    if effect == "reject":
        if node is not None and can_raise(node):
            return lim, None
        handler = _handler_at(tree, line) if node is None else None
        raises = [n for s in (handler.body if handler else []) for n in ast.walk(s) if isinstance(n, ast.Raise)]
        if raises:
            move_to, why = raises[0], f"{where} is an `except` header; the exception is raised by the raise in its handler"
        elif isinstance(node, (ast.If, ast.While)):
            new_effect = "other"
            why = (f"the {_kind(node)} statement at {where} has no raise in its body, so no exception comes from it "
                   "(the program rejects later, or by skipping or retrying)")
        elif node is None:
            new_effect, why = "other", f"no statement starts at {where}"
        else:
            callee = " (the exception, if any, comes from a callee)" if any(
                isinstance(n, ast.Call) for n in ast.walk(node)) else ""
            new_effect, why = "other", f"the {_kind(node)} statement at {where} does not raise by itself{callee}"
    else:
        if isinstance(node, (ast.If, ast.While)):
            return lim, None
        branch = _enclosing_branch(tree, node) if node is not None else None
        cond = normalise(lim.condition.expr) if lim.condition else None
        if branch is not None and cond is not None and normalise(ast.unparse(branch.test)) == cond:
            move_to = branch
            why = (f"the {_kind(node)} statement at {where} is not a branch; it runs in the body of the "
                   f"{_kind(branch)} at line {branch.lineno}, whose test is the limitation's condition")
        elif node is None:
            new_effect, why = "other", f"no statement starts at {where}"
        else:
            new_effect = "other"
            why = (f"the {_kind(node)} statement at {where} is not a branch decision; the effect is a changed value, "
                   "which needs a differential check")

    record = {"limitation_id": lim.limitation_id, "from_effect": effect, "from_location": where, "reason": why}
    update: dict = {}
    if move_to is not None:
        header_end = move_to.test.end_lineno if isinstance(move_to, (ast.If, ast.While)) else move_to.end_lineno
        new_loc = loc.model_copy(update={"line_start": move_to.lineno, "line_end": header_end,
                                         "snippet": canonical_snippet(move_to)})
        update["code_evidence"] = [new_loc, *lim.code_evidence[1:]]
        record.update(action="moved", to_effect=effect, to_location=f"{loc.file}:{move_to.lineno}")
        text = f"effect check: target moved from line {line} to line {move_to.lineno} ({why})"
    else:
        update["effect_type"] = new_effect
        record.update(action="relabelled", to_effect=new_effect, to_location=where)
        text = f"effect check: {effect} -> {new_effect} ({why})"
    update["notes"] = f"{lim.notes}; {text}" if lim.notes else text
    return lim.model_copy(update=update), record


def canonical_snippet(node: ast.stmt) -> str:
    """The snippet convention (docs/09_step4_findings.md): one line, no assert message, no redundant parentheses.

    assert       `assert <test>`
    if / while   `if <test>:` / `while <test>:` (the header; an `elif` is written as `if`)
    otherwise    the first line of `ast.unparse` of the statement
    Cut to 200 characters. The same for route A and route B, so a multi-line statement is never cut at `if (`.
    """
    if isinstance(node, ast.Assert):
        text = f"assert {ast.unparse(node.test)}"
    elif isinstance(node, (ast.If, ast.While)):
        text = f"{'if' if isinstance(node, ast.If) else 'while'} {ast.unparse(node.test)}:"
    else:
        text = ast.unparse(node).splitlines()[0]
    return text[:200]


def normalise_snippet(lim: Limitation, repo: Path) -> Limitation:
    """Rewrite code_evidence[0].snippet in the canonical form (nothing else changes)."""
    if lim.origin != "code" or not lim.code_evidence:
        return lim
    loc = lim.code_evidence[0]
    tree = _tree(str(Path(repo) / loc.file))
    node = _statement_at(tree, loc.line_start) if tree is not None else None
    if node is None:
        return lim
    text = canonical_snippet(node)
    if text == loc.snippet:
        return lim
    return lim.model_copy(update={"code_evidence": [loc.model_copy(update={"snippet": text}), *lim.code_evidence[1:]]})


def check_effects(lims: list[Limitation], repo: Optional[Path]) -> tuple[list[Limitation], list[dict]]:
    """Apply `check_effect` to every limitation, then write every snippet in the canonical form.
    Without a repo nothing is changed."""
    if repo is None or not Path(repo).is_dir():
        return list(lims), []
    out, records = [], []
    for lim in lims:
        fixed, rec = check_effect(lim, Path(repo))
        out.append(normalise_snippet(fixed, Path(repo)))
        if rec:
            records.append(rec)
    return out, records
