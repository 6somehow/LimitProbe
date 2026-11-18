"""Defeater evaluation and confidence level (CONFIDENCE_SPEC.md sections 4 to 6).

No weights and no combined number. Each defeater (a reason the verdict could be wrong) gets one
of four states from a fixed rule over harness measurements:
  eliminated  measured evidence rules it out
  residual    argued but not measured (or measured only partly)
  open        not evaluated
  refuted     the check failed
The level follows from the states and the profile (profile.py); same evidence + same profile =
same level.

  invalid  a fatal defeater is refuted; the verdict is forced to inconclusive
  L0       no fatal defeater refuted, but one is still open
  L1       fatal defeaters are eliminated or residual; important ones may be open or refuted
  L2       all fatal eliminated; D3 D8 D9 eliminated; D5 D6 D10 D14 eliminated or residual
  L3       everything eliminated (D13 scope may be residual or refuted: it is reported, not scored)
A 'no' verdict is only reported when D3 (the oracle can see the effect when it exists) is eliminated; otherwise it
becomes inconclusive (CONFIDENCE_SPEC.md section 18; before 2026-11-17 it was kept at level L1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .models import (BvaResult, Confidence, DefeaterResult, InfoItem, Level, MutationResult, RepeatResult,
                     ReplayResult, Verdict)
from .profile import Profile

FATAL = ("D1", "D2", "D4", "D7", "D11", "D12")
IMPORTANT = ("D3", "D5", "D6", "D8", "D9", "D10", "D14")
NAMES = {
    "D1": ("target statement executed", "Reachability (RIPR; Ammann & Offutt)", "fatal"),
    "D2": ("condition holds on positive, fails on negative", "Infection (RIPR; Voas PIE)", "fatal"),
    "D3": ("oracle can see the effect", "Propagation/Revealability; mutation testing", "important"),
    "D4": ("oracle is specified, located, pre-registered", "Test oracle problem (Barr et al.)", "fatal"),
    "D5": ("control pair differs in one factor, negative adjacent to the boundary",
           "Ceteris paribus; domain testing ON/OFF points; delta debugging", "important"),
    "D6": ("verdict-bearing observations do not depend on stand-ins", "Test doubles (Meszaros); causal prefix", "important"),
    "D7": ("observation unchanged by the tracer", "Probe effect (Gait)", "fatal"),
    "D8": ("result is stable across independent runs", "Flaky tests (Luo et al.); rule of three", "important"),
    "D9": ("result reproduces in a clean checkout", "Reproducibility; clean-environment replay", "important"),
    "D10": ("scaled-down run agrees with full witness scale", "External validity (representativeness)", "important"),
    "D11": ("code under test unmodified", "Fidelity of the test object", "fatal"),
    "D12": ("Region location and snippet match the repository", "Input validity (upstream)", "fatal"),
    "D13": ("inputs inside the paper's scope", "Scope gate (T9)", "note"),
    "D14": ("official entry point was called", "Integration level (T4)", "important"),
}
REMEDY = {
    "D1": "choose inputs that reach the target line (check Region.condition.path_prefix)",
    "D2": "pick inputs so the Region condition is true on the positive and false on the negative; write a predicate if it cannot be evaluated",
    "D3": "run mutation; if kill rate is low, strengthen the oracle so it names the exception type and the target location",
    "D4": "state the oracle as exception type + Region.location and register it before the first run",
    "D5": "change exactly one factor between positive and negative, and make the negative the point next to the boundary",
    "D6": "move stand-ins after the target line, or replace stubs with a fake or the repository's own reference implementation",
    "D7": "remove behaviour that depends on tracing; keep hooks read-only",
    "D8": "fix seeds and thread counts; find the source of non-determinism",
    "D9": "make the attempt self-contained so a clean checkout reproduces it",
    "D10": "run the full-scale witness at least up to the target, or give up the scale reduction",
    "D11": "do not edit the repository; use external stand-ins only",
    "D12": "re-check Region.location against the pinned commit",
    "D13": "record as out of scope; do not count in main results",
    "D14": "call the official entry, or record why a deeper function is called (execution.entry_reason)",
}
_STATE_RANK = {"direct": 0, "simulated:reference": 1, "simulated:fake": 2, "simulated:stub": 3}


@dataclass
class Measurements:
    verdict: Verdict
    outcome_supported: bool = True
    # D1, D2
    target_reached: bool = False
    cond_true_on_positive: Optional[bool] = None
    cond_false_on_negative: Optional[bool] = None
    condition_translated: bool = False
    region_cond_true_on_positive: Optional[bool] = None    # Region.condition itself, evaluated beside an agent predicate
    region_cond_false_on_negative: Optional[bool] = None
    # D3
    mutation: Optional[MutationResult] = None
    # D4
    declared_tier: str = "O1"
    verified_tier: str = "O1"
    preregistered: bool = False
    oracle_revisions: int = 0
    # D5
    differing_factors: list[str] = field(default_factory=list)
    controls_differ: bool = False
    extra_negatives_clean: Optional[bool] = None   # None: none given; False: one of them showed the effect
    bva: Optional[BvaResult] = None
    # D6
    info: list[InfoItem] = field(default_factory=list)
    sim_checks: dict = field(default_factory=dict)       # {mock symbol: simcheck result}
    # D7
    probe_effect_free: Optional[bool] = None
    # D8, D9
    repeat: Optional[RepeatResult] = None
    replay: Optional[ReplayResult] = None
    # D10
    scale_declared: bool = False
    main_positive_effect: Optional[bool] = None
    main_negative_effect: Optional[bool] = None
    # D11, D12
    target_intact: bool = True
    stmts_changed: int = 0
    stmts_total: int = 0
    snippet_matches: bool = True
    # D13
    scope_status: str = "unknown"
    # D14
    entry_index: Optional[int] = None
    entry_on_stack: Optional[bool] = None    # was call_chain[0] still running when the target line executed (None: not known)
    entry_reason: Optional[str] = None


def worst_state(states: list[str]) -> str:
    return max(states, key=lambda s: _STATE_RANK[s], default="direct")


def _d(id_: str, status: str, evidence: str, **measured: Any) -> DefeaterResult:
    name, concept, sev = NAMES[id_]
    return DefeaterResult(id=id_, name=name, concept=concept, severity=sev, status=status,  # type: ignore[arg-type]
                          evidence=evidence, measured=measured)


def evaluate_defeaters(m: Measurements, p: Profile) -> list[DefeaterResult]:
    from .stats import wilson_lower  # noqa: F401  (kept for symmetry; mutation carries its own bound)
    out: list[DefeaterResult] = []

    out.append(_d("D1", "eliminated" if m.target_reached else "refuted",
                  "positive run executed the target line" if m.target_reached else "positive run never executed the target line"))

    pos, neg = m.cond_true_on_positive, m.cond_false_on_negative
    rpos, rneg = m.region_cond_true_on_positive, m.region_cond_false_on_negative
    if m.condition_translated and (rpos is False or rneg is False):
        what = ("does not hold on the positive run" if rpos is False else "") + (" and " if rpos is False and rneg is False else "") \
            + ("does not fail on the negative run" if rneg is False else "")
        out.append(_d("D2", "refuted", f"the agent's predicate and Region.condition disagree: Region.condition itself {what}",
                      cond_true_on_positive=pos, cond_false_on_negative=neg))
    elif m.condition_translated and rpos is True and rneg is True and pos is True and neg is True:
        out.append(_d("D2", "eliminated", "Region.condition itself (evaluated beside the agent's predicate) is true on the "
                      "positive run and false on the negative run", cond_true_on_positive=pos, cond_false_on_negative=neg))
    elif pos is True and neg is True:
        out.append(_d("D2", "residual" if m.condition_translated else "eliminated",
                      "agent-written predicate holds on positive and fails on negative; its fidelity to the Region condition is not verified"
                      if m.condition_translated else "Region.condition evaluated on the target-line locals: true on positive, false on negative",
                      cond_true_on_positive=pos, cond_false_on_negative=neg))
    elif pos is False or neg is False:
        out.append(_d("D2", "refuted", "condition does not hold on the positive or does not fail on the negative",
                      cond_true_on_positive=pos, cond_false_on_negative=neg))
    else:
        out.append(_d("D2", "open", "condition could not be evaluated on the captured locals; no predicate registered",
                      cond_true_on_positive=pos, cond_false_on_negative=neg))

    mu = m.mutation
    if mu is None:
        out.append(_d("D3", "open", "mutation not run"))
    elif mu.generated == 0:
        out.append(_d("D3", "open", "no mutation operator applies to the target statement"))
    elif mu.generated < p.n_min:
        out.append(_d("D3", "residual", f"only {mu.generated} mutants (< n_min={p.n_min}); killed {mu.killed}",
                      generated=mu.generated, killed=mu.killed, wilson_lower=mu.wilson_lower))
    elif mu.wilson_lower >= p.kill_lb:
        out.append(_d("D3", "eliminated", f"killed {mu.killed}/{mu.generated}; Wilson lower bound {mu.wilson_lower:.2f} >= {p.kill_lb}",
                      generated=mu.generated, killed=mu.killed, wilson_lower=mu.wilson_lower))
    else:
        out.append(_d("D3", "refuted", f"killed {mu.killed}/{mu.generated}; Wilson lower bound {mu.wilson_lower:.2f} < {p.kill_lb}",
                      generated=mu.generated, killed=mu.killed, wilson_lower=mu.wilson_lower))

    if m.verified_tier in ("O1", "O2") or not m.preregistered:
        out.append(_d("D4", "refuted", f"verified tier {m.verified_tier}, pre-registered={m.preregistered}"))
    elif m.verified_tier == "O4" and m.oracle_revisions == 0:
        out.append(_d("D4", "eliminated", "exception type and Region.location named; registered before the first run"))
    else:
        why = f"tier {m.verified_tier} (location not named)" if m.verified_tier != "O4" else \
            f"oracle changed {m.oracle_revisions} time(s) after the first run"
        out.append(_d("D4", "residual", why, revisions=m.oracle_revisions))

    single = len(m.differing_factors) == 1
    if m.extra_negatives_clean is False:
        out.append(_d("D5", "refuted", "an extra negative input shows the effect (or never reached the target): "
                      "the no-effect region is not what the pair suggests"))
    elif not single:
        out.append(_d("D5", "refuted", f"positive and negative differ in {m.differing_factors}, not in exactly one factor"))
    elif m.verdict == "yes" and not m.controls_differ:
        out.append(_d("D5", "refuted", "positive and negative behave the same"))
    elif m.verdict == "no":
        out.append(_d("D5", "eliminated", "one factor differs (adjacency is not required for a 'no' verdict)"))
    elif m.bva is None:
        out.append(_d("D5", "open", "boundary analysis not run"))
    elif not m.bva.applicable:
        out.append(_d("D5", "residual", "one factor differs; adjacency not measurable: " + m.bva.note))
    elif m.bva.adjacent is None:
        out.append(_d("D5", "open", m.bva.note or "neighbour probes undecided"))
    elif m.bva.adjacent:
        out.append(_d("D5", "eliminated", "one factor differs and a neighbour of the negative input shows the effect: " + m.bva.pattern))
    else:
        out.append(_d("D5", "refuted", m.bva.pattern))

    bearing = [i for i in m.info if i.verdict_bearing]
    if not bearing:
        out.append(_d("D6", "open", "no verdict-bearing observation recorded"))
    else:
        w = worst_state([i.evidence_state for i in bearing])
        st = {"direct": "eliminated", "simulated:reference": "residual", "simulated:fake": "residual",
              "simulated:stub": "refuted"}[w]
        note = ""
        if m.sim_checks:
            note = "; stand-in checks: " + ", ".join(f"{k} {v.get('status')}" for k, v in sorted(m.sim_checks.items()))
            if any(v.get("status") == "disagrees" for v in m.sim_checks.values()):
                st = "refuted"                       # a stand-in that disagrees with its own reference is wrong
        out.append(_d("D6", st, "verdict-bearing observations: " + ", ".join(f"{i.run} {i.evidence_state}" for i in bearing)
                      + note, worst=w))

    out.append(_d("D7", "open" if m.probe_effect_free is None else "eliminated" if m.probe_effect_free else "refuted",
                  {None: "untraced run not made", True: "traced and untraced runs show the same observable result",
                   False: "traced and untraced runs differ"}[m.probe_effect_free]))

    r = m.repeat
    if r is None or r.runs < 2:
        out.append(_d("D8", "open", "repeat runs not made"))
    elif not r.identical:
        out.append(_d("D8", "refuted", f"{r.distinct_hashes} distinct canonical traces in {r.runs} runs", runs=r.runs))
    elif r.runs < p.n_rep:
        out.append(_d("D8", "residual", f"{r.runs} identical runs (< n_rep={p.n_rep}); flake bound {r.flake_bound:.2f}", runs=r.runs))
    else:
        out.append(_d("D8", "eliminated", f"{r.runs} identical canonical traces; flake probability <= {r.flake_bound:.2f} (rule of three)",
                      runs=r.runs, flake_bound=r.flake_bound))

    out.append(_d("D9", "open" if m.replay is None else "eliminated" if m.replay.ok else "refuted",
                  "replay not run" if m.replay is None else m.replay.detail))

    if not m.scale_declared:
        out.append(_d("D10", "eliminated", "no scale reduction"))
    elif m.bva is None or m.bva.full_scale_positive is None or m.bva.full_scale_negative is None:
        out.append(_d("D10", "open", "full-scale probes not run or undecided"))
    elif (m.bva.full_scale_positive, m.bva.full_scale_negative) == (m.main_positive_effect, m.main_negative_effect):
        out.append(_d("D10", "eliminated", "target decision at full witness scale equals the scaled run for both inputs"))
    else:
        out.append(_d("D10", "refuted", f"full scale: positive={m.bva.full_scale_positive}, negative={m.bva.full_scale_negative}; "
                      f"scaled: positive={m.main_positive_effect}, negative={m.main_negative_effect}"))

    ratio = m.stmts_changed / m.stmts_total if m.stmts_total else 0.0
    if not m.target_intact:
        out.append(_d("D11", "refuted", "the target statement differs from the pinned commit"))
    elif ratio > p.mod_max:
        out.append(_d("D11", "refuted", f"{ratio:.2%} of call-chain statements edited (> {p.mod_max:.0%})"))
    else:
        out.append(_d("D11", "eliminated", f"target statement intact; {m.stmts_changed}/{m.stmts_total} call-chain statements edited"))

    out.append(_d("D12", "eliminated" if m.snippet_matches else "refuted",
                  "Region snippet equals the repository line" if m.snippet_matches else "Region snippet differs from the repository line"))

    out.append(_d("D13", {"in_scope": "eliminated", "scope_edge": "eliminated", "out_of_scope": "refuted"}.get(m.scope_status, "residual"),
                  f"scope_status={m.scope_status}"))

    if m.entry_index == 0 and m.entry_on_stack is not False:
        out.append(_d("D14", "eliminated", "the official entry (call_chain[0]) started first and was running when the target executed"))
    elif m.entry_index == 0:
        # the entry was called, but the target ran outside it (a call made first and then a direct call to the target
        # function): the entry did not lead to the target
        out.append(_d("D14", "residual" if m.entry_reason else "refuted",
                      "the official entry started first but the target line did not run inside it"
                      + (f"; reason recorded: {m.entry_reason}" if m.entry_reason else " and no reason is recorded")))
    elif m.entry_reason:
        out.append(_d("D14", "residual", f"deeper entry (index {m.entry_index}); reason recorded: {m.entry_reason}"))
    else:
        out.append(_d("D14", "refuted", f"entry index {m.entry_index} (None = not in the call chain) and no reason recorded"))
    return out


def decide_level(defs: list[DefeaterResult], verdict: Verdict, outcome_supported: bool = True
                 ) -> tuple[Level, Verdict, str]:
    """Return (level, final verdict, note)."""
    st = {d.id: d.status for d in defs}
    if verdict == "inconclusive":
        return "n/a", "inconclusive", "verdict is inconclusive; no confidence is assigned to it"
    fatal_refuted = [i for i in FATAL if st[i] == "refuted"]
    if fatal_refuted:
        return "invalid", "inconclusive", "refuted fatal defeaters: " + ", ".join(fatal_refuted)
    if verdict == "no" and st["D3"] != "eliminated":
        # "the effect was not there" is only worth reporting if the oracle was shown to see the effect when it is there
        # (mutants of the target killed). In the 82-case benchmark half of the L1 `no` verdicts were wrong, all of them
        # claims that were true but whose oracle was too narrow.
        return "n/a", "inconclusive", (f"a 'no' verdict needs the oracle shown to see the effect (D3 eliminated); "
                                       f"D3 is {st['D3']}: {next((d.evidence for d in defs if d.id == 'D3'), '')}")
    if any(st[i] == "open" for i in FATAL):
        level: Level = "L0"
        note = "open fatal defeaters: " + ", ".join(i for i in FATAL if st[i] == "open")
    else:
        level = "L1"
        note = ""
        fatal_ok = all(st[i] == "eliminated" for i in FATAL)
        l2 = (fatal_ok and all(st[i] == "eliminated" for i in ("D3", "D8", "D9"))
              and all(st[i] in ("eliminated", "residual") for i in ("D5", "D6", "D10", "D14")))
        if l2:
            level = "L2"
        if l2 and all(st[i] == "eliminated" for i in FATAL + IMPORTANT):
            level = "L3"
    if st["D13"] == "refuted":
        note = (note + "; " if note else "") + "out of scope: record only, not part of main results"
    return level, verdict, note


def next_steps(defs: list[DefeaterResult], mutation: Optional[MutationResult] = None) -> list[str]:
    out = []
    for d in defs:
        if d.status not in ("open", "residual", "refuted") or d.id == "D13":
            continue
        text = REMEDY[d.id]
        if d.id == "D3" and mutation is not None:
            alive = [f"{m.operator} (`{m.mutated}`)" for m in mutation.mutants if not m.killed]
            if alive:
                text = (f"{len(alive)} mutant(s) survived because no input separates them from the original: "
                        + "; ".join(alive[:6]) + (" ..." if len(alive) > 6 else "")
                        + ". Add inputs that distinguish them (for a set-membership guard, one input per member), "
                          "or strengthen the oracle if it cannot see the effect")
        out.append(f"{d.id} ({d.status}): {text}")
    return out


def build(m: Measurements, p: Profile) -> tuple[Confidence, Verdict]:
    defs = evaluate_defeaters(m, p)
    level, final, note = decide_level(defs, m.verdict, m.outcome_supported)
    return Confidence(profile=p, defeaters=defs, level=level, level_note=note, calibrated=False,
                      next_steps=next_steps(defs, m.mutation)), final
