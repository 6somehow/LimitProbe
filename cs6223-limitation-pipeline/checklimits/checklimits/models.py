"""Records for check_limits (PLAN.md section 7, SCORECARD.md section 6).

Four groups:
  AttemptManifest  what the harness needs to run an attempt package
  AgentForm        the table the code agent fills in (SCORECARD section 6)
  Confidence       defeater table and level (CONFIDENCE_SPEC.md; replaces the numeric Scorecard)
  ExecutionReport  the sidecar report written by the harness

`schema.models.TestCase` (shared, read-only) is produced by `make_testcase`.
All models are pydantic v2 with extra="forbid".
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .profile import Profile

REPORT_VERSION = "0.1.0"
PIPELINE_ROOT = Path(__file__).resolve().parents[2]  # .../cs6223-limitation-pipeline
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # .../cs6223-limitation-pipeline/checklimits


def scratch_root() -> Path:
    """Temporary working area for child processes, mutants and replays (git-ignored). Sandboxed agent runs
    point it into their own run directory with CHECKLIMITS_SCRATCH."""
    import os
    return Path(os.environ.get("CHECKLIMITS_SCRATCH") or (PROJECT_ROOT / "scratch"))


class _R(BaseModel):
    model_config = ConfigDict(extra="forbid")


Verdict = Literal["yes", "no", "inconclusive"]
ExecResultName = Literal["confirmed", "refuted", "test_error", "not_run"]
Tier = Literal["O1", "O2", "O3", "O4"]
Strategy = Literal["S0", "S1", "S2", "S3"]


# --------------------------------------------------------------------------- #
# AgentForm (SCORECARD section 6)
# --------------------------------------------------------------------------- #
class FreeParameter(_R):
    name: str
    value: Any
    why: str


class OracleDecl(_R):
    tier: Tier
    type: Literal["exception", "path_hook", "differential", "metamorphic", "resource"]
    spec: str
    signal_location: Optional[str] = Field(None, description="repo-relative 'file:line' the signal must point to")


class Expected(_R):
    positive: str
    negative: str


class ScaleDecl(_R):
    """The test runs smaller than the witness; only the control flow is being simulated."""
    factor: float = Field(description="run value / witness value, e.g. 0.125")
    scaled: list[str] = Field(description="input names that were scaled")
    reason: str
    invariance_argument: str = Field(description="why the target decision does not depend on the scale")


class Design(_R):
    witness_source: str
    scale: Optional[ScaleDecl] = None
    free_parameters: list[FreeParameter] = Field(default_factory=list)
    positive_input: dict[str, Any]
    negative_input: dict[str, Any]
    boundary_variable: str
    positive_prelude: list[dict[str, Any]] = Field(
        default_factory=list, description="state_dependent findings: inputs of the calls made BEFORE the checked "
                                          "positive call, in order, in the same process")
    negative_prelude: list[dict[str, Any]] = Field(default_factory=list, description="same, before the negative call")
    extra_negatives: list[dict[str, Any]] = Field(
        default_factory=list,
        description="more inputs that must show NO effect (full design inputs, like negative_input). They do not "
                    "change the verdict; they let the mutation check tell guards apart whose members one negative "
                    "cannot separate (e.g. one input per member of a set-membership guard)")
    condition_predicate_file: Optional[str] = None
    oracle: OracleDecl
    expected: Expected


SimClass = Literal["repo_reference", "independent_native", "stub"]


class MockDecl(_R):
    """An external stand-in. `behavior` is a closed vocabulary (see fakes.py).

    behavior "sim" runs a real implementation instead of returning a canned value:
      impl: "<file in the attempt dir>::<function>"; the function receives the same arguments as the
            replaced symbol. sim_class says what it is: "repo_reference" (it calls a reference
            implementation shipped in the repository), "independent_native" (written by us in plain
            torch), or "stub" (canned value).
    sim_class sets how much the harness trusts what the stand-in computed (see fidelity.SIM_WEIGHT).
    """
    symbol: str = Field(description="dotted path; for env_var kind, the variable name")
    kind: Literal["fake_module", "patch", "env_var"]
    reason: str
    behavior: Literal["return_first_arg", "return_none", "record_only", "sim"] = "return_first_arg"
    value: Optional[str] = Field(None, description="env_var only")
    impl: Optional[str] = None
    sim_class: SimClass = "stub"


class HookDecl(_R):
    name: str
    purpose: str


class Execution(_R):
    entry_called: str = Field(description="'file::function' of the function the driver calls")
    entry_reason: Optional[str] = Field(None, description="T4: why a function deeper than the official entry is called")
    call_chain_index: Optional[int] = None
    repo_files_modified: list[str] = Field(default_factory=list)
    mocks: list[MockDecl] = Field(default_factory=list)
    hooks: list[HookDecl] = Field(default_factory=list)
    replay_commands: list[str] = Field(default_factory=list)


class Claims(_R):
    """Every field is recomputed by audit.py."""
    target_reached: bool
    decision_outcomes_seen: list[Literal["true", "false"]]
    condition_true_on_positive: Optional[bool]
    condition_false_on_negative: Optional[bool]
    positive_observed: str
    negative_observed: str


class EvidenceFiles(_R):
    trace_file: Optional[str] = None
    stdout_file: Optional[str] = None
    diff_file: Optional[str] = None


class AgentForm(_R):
    test_id: str
    finding_id: str
    strategy: Strategy
    design: Design
    execution: Execution
    claims: Claims
    evidence: EvidenceFiles = Field(default_factory=EvidenceFiles)


# --------------------------------------------------------------------------- #
# Attempt manifest
# --------------------------------------------------------------------------- #
class AttemptManifest(_R):
    test_id: str
    finding_id: str
    artifact_id: str
    region_id: str
    repo_dir: str = Field(description="repository path relative to the pipeline root")
    repo_commit: str
    data_dir: str = Field("data/pilot_flexprefill", description="relative to the pipeline root")
    findings_file: Optional[str] = Field(
        None, description="step 4 hand-off (results/step4/<artifact>/limitations_for_tests.json), relative to the "
                          "pipeline root. When set, findings, limitations and witnesses come from it and data_dir "
                          "only supplies artifact.json")
    form: str = "form.json"
    driver: str = "driver.py"
    driver_fn: str = "run"
    timeout_s: int = 300
    seed: int = 0
    python: Optional[str] = Field(
        None, description="interpreter for the child process, relative to checklimits/ or absolute; "
                          "default: the harness interpreter")
    env: dict[str, str] = Field(default_factory=dict, description="extra environment for the child")


# --------------------------------------------------------------------------- #
# Observations, checks, fidelity
# --------------------------------------------------------------------------- #
class ExceptionInfo(_R):
    type: str
    message: str
    raised_at: Optional[str] = Field(None, description="innermost frame, repo-relative 'file:line' if inside the repo")
    frames: list[str] = Field(default_factory=list)


class TargetHit(_R):
    seq: int
    call: int = 0
    outcome: Optional[Literal["true", "false", "error"]] = None
    condition_value: Optional[bool] = None
    condition_error: Optional[str] = None
    locals: dict[str, str] = Field(default_factory=dict)


class CoverageScope(_R):
    scope: str = "call_chain"
    lines_executed: int
    lines_total: int


class Observation(_R):
    """What one run showed, after the harness interpreted the trace."""
    role: Literal["positive", "negative"]
    inputs: dict[str, Any]
    status: Literal["ok", "exception", "timeout", "crash", "load_error", "probe_stop"]
    exception: Optional[ExceptionInfo] = None
    target_reached: bool = False
    target_hits: list[TargetHit] = Field(default_factory=list)
    effect: Optional[bool] = Field(None, description="Region.outcome effect observed; None = cannot tell")
    effect_note: str = ""
    returned: Optional[str] = Field(None, description="summary of the return value, if the run returned")
    post_target_exception: Optional[ExceptionInfo] = Field(
        None, description="exception raised after the target line passed (does not count as the effect)")
    entry_first_started: Optional[str] = None
    target_span: Optional[list[int]] = Field(None, description="[first, last] line of the target statement or header")
    target_kind: Optional[str] = Field(None, description="assert | if | while | other: what the statement at Region.location is")
    observed_text: str = ""
    coverage: Optional[CoverageScope] = None
    stdout_tail: str = ""
    wall_s: float = 0.0


class MockRecord(_R):
    symbol: str
    kind: str
    sim_class: str = "stub"
    on_path: bool
    accesses_before_target: int
    accesses_total: int
    reason: str


class AstDiff(_R):
    files_checked: list[str]
    files_changed: list[str] = Field(default_factory=list)
    statements_total: int
    statements_changed: int
    target_statement_intact: bool
    snippet_matches_region: bool
    git_status_clean: bool


class Fidelity(_R):
    strategy: Strategy
    ast_diff: AstDiff
    mocks: list[MockRecord]
    entry_index: Optional[int]
    call_chain_len: int
    probe_effect_free: bool
    probe_note: str = ""


EvidenceState = Literal["direct", "simulated:reference", "simulated:fake", "simulated:stub"]


class InfoItem(_R):
    """One observation, with the stand-ins in its causal past (CONFIDENCE_SPEC.md section 5).

    direct               no stand-in was touched before the observation was produced
    simulated:reference  only stand-ins that call a reference implementation shipped in the repository
    simulated:fake       a stand-in with real computation written for the test
    simulated:stub       a stand-in that returns a canned value
    Only verdict_bearing observations decide the verdict; the others are supplementary."""
    statement: str
    run: Literal["positive", "negative"]
    verdict_bearing: bool
    depends_on_mocks: list[str] = Field(default_factory=list)
    evidence_state: EvidenceState
    basis: str


class BvaProbe(_R):
    label: str
    inputs: dict[str, Any]
    effect: Optional[bool]
    note: str = ""


class BvaResult(_R):
    """Harness-run boundary value analysis (domain testing ON/OFF points) at full witness scale."""
    applicable: bool
    boundary_variable: str
    full_scale_positive: Optional[bool] = None
    full_scale_negative: Optional[bool] = None
    neighbours: list[BvaProbe] = Field(default_factory=list)
    adjacent: Optional[bool] = Field(None, description="the negative input has a neighbour at distance probe_step with the effect")
    pattern: str = ""
    note: str = ""


class MutantResult(_R):
    operator: str
    line: int
    original: str
    mutated: str
    killed: bool
    verdict_after: str


class MutationResult(_R):
    generated: int
    killed: int
    wilson_lower: float
    mutants: list[MutantResult] = Field(default_factory=list)
    note: str = ""


class RepeatResult(_R):
    runs: int
    identical: bool
    distinct_hashes: int
    flake_bound: float = Field(description="approximate 95 % upper bound on the flake probability, 3/runs")
    trace_hash: str


class ReplayResult(_R):
    ok: bool
    detail: str


class Checks(_R):
    controls_differ: bool
    differing_factors: list[str]
    bva: Optional[BvaResult] = Field(None, description="None = not run")
    mutation: Optional[MutationResult] = Field(None, description="None = not run")
    repeat: Optional[RepeatResult] = Field(None, description="None = not run")
    replay: Optional[ReplayResult] = Field(None, description="None = not run")


DefStatus = Literal["eliminated", "residual", "open", "refuted"]
Severity = Literal["fatal", "important", "note"]
Level = Literal["invalid", "L0", "L1", "L2", "L3", "n/a"]


class DefeaterResult(_R):
    id: str
    name: str
    concept: str
    severity: Severity
    status: DefStatus
    evidence: str
    measured: dict[str, Any] = Field(default_factory=dict)


class AuditItem(_R):
    claim: str
    declared: Any
    recomputed: Any
    match: bool


class AuditResult(_R):
    declared_checks: int
    matched_checks: int
    rate: float
    items: list[AuditItem]
    extra_notes: list[str] = Field(default_factory=list)


class OracleRecord(_R):
    declared_tier: Tier
    verified_tier: Tier
    type: str
    spec: str
    signal_location: Optional[str]
    sha256: str
    preregistered: bool
    revisions_after_first_run: int


class Confidence(_R):
    profile: Profile
    defeaters: list[DefeaterResult]
    level: Level
    level_note: str = ""
    calibrated: bool = Field(False, description="True once the level has been checked against fault-injection ground truth")
    next_steps: list[str] = Field(default_factory=list, description="what would remove the open / residual / refuted defeaters")


class Env(_R):
    executable_on: str
    python: str
    packages: dict[str, str] = Field(default_factory=dict)
    repo_commit: str


class Cost(_R):
    llm_calls: int = 0
    tokens: int = 0
    wall_seconds: float = 0.0


class ExecutionReport(_R):
    report_version: str = REPORT_VERSION
    test_id: str
    finding_id: str
    artifact_id: str
    region_id: str
    verdict: Verdict = Field(description="from the SCORECARD 3.5 table, before gates")
    final_verdict: Verdict = Field(description="after the defeater rules: a refuted fatal defeater forces inconclusive")
    exec_result: ExecResultName
    verdict_reason: str
    strategy: Strategy
    oracle: OracleRecord
    positive: Observation
    negative: Observation
    extra_negatives: list[Observation] = Field(default_factory=list)
    checks: Checks
    fidelity: Fidelity
    audit: AuditResult
    information: list[InfoItem] = Field(default_factory=list)
    confidence: Confidence
    finding_confidence: Optional[str] = Field(None, description="upstream Finding.confidence, reported separately")
    env: Env
    cost: Cost = Field(default_factory=Cost)
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def design_sha256(form: AgentForm, predicate_bytes: bytes | None = None) -> str:
    """Hash of what T1 asks the agent to commit to before the first run: the oracle, the expected
    results for the positive and negative input, and the condition predicate (if any). Inputs, mocks
    and scale are not part of it: changing them after a run does not change what counts as the effect."""
    payload = {
        "oracle": form.design.oracle.model_dump(mode="json"),
        "expected": form.design.expected.model_dump(mode="json"),
    }
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode())
    if predicate_bytes:
        h.update(predicate_bytes)
    return h.hexdigest()


_ORACLE_TYPE = {
    "exception": "exception", "path_hook": "path_hook", "differential": "differential",
    "metamorphic": "metamorphic", "resource": "resource",
}


def make_testcase(report: ExecutionReport, form: AgentForm, manifest: AttemptManifest,
                  witness_type: str, inputs: list[dict[str, Any]]):
    """Build the standard `schema.models.TestCase` (shared schema, validated by codeside.cli)."""
    if str(PIPELINE_ROOT) not in sys.path:
        sys.path.insert(0, str(PIPELINE_ROOT))
    from schema.models import ExecEnv, ExecResult, OracleType, TestCase, WitnessType

    executable_on = ExecEnv.cpu_mock if form.execution.mocks else ExecEnv.cpu
    notes = (f"verdict={report.verdict} final_verdict={report.final_verdict} "
             f"confidence={report.confidence.level} (uncalibrated); {report.verdict_reason}")
    return TestCase(
        test_id=report.test_id,
        finding_id=report.finding_id,
        witness_type=WitnessType(witness_type),
        inputs=inputs,
        oracle_type=OracleType(_ORACLE_TYPE[form.design.oracle.type]),
        oracle_spec=form.design.oracle.spec,
        executable_on=executable_on,
        file=str(Path("checklimits/attempts") / manifest.artifact_id / manifest.finding_id / manifest.driver),
        result=ExecResult(report.exec_result),
        result_notes=notes,
    )
