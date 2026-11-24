"""Shared record schema (v0) for the CS6223 limitation pipeline.

Owner: Wanting (code side). Reviewers: Zhaopeng (paper side), Shanghao (tests & metrics).
Every module reads and writes these records as JSON. Do not add fields silently:
bump SCHEMA_VERSION and note the change in docs/02_schema.md.

Pipeline step -> record types it produces
  1  paper-side limitation finding (Zhaopeng) -> Claim, ScopeItem, EvalPoint, Binding, Limitation(origin=paper)
  2  code-side limitation finding (Wanting)   -> Region, Limitation(origin=code)
  3a paper -> code verification (Zhaopeng)    -> Verification(direction=paper_to_code)
  3b code -> paper verification (Wanting)     -> Verification(direction=code_to_paper)
  4  integration (Wanting)                    -> Finding
  5-6 tests and execution (Shanghao)          -> TestCase
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "0.2.1"

SwarmCategory = Literal["applicability_limitation", "mechanism_origin_unclear", "method_shortcoming"]


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


# --------------------------------------------------------------------------- #
# Shared building blocks
# --------------------------------------------------------------------------- #
class DocSource(str, Enum):
    paper = "paper"
    appendix = "appendix"
    readme = "readme"
    code_comment = "code_comment"
    docstring = "docstring"
    other = "other"


class TextEvidence(_Record):
    """A verbatim quote from the paper, README, a docstring or a comment."""

    quote: str = Field(description="Verbatim text. Gate rule: must occur in the source.")
    source: DocSource = DocSource.paper
    locator: Optional[str] = Field(None, description="Section, page, table, or README heading.")


class CodeLocation(_Record):
    file: str = Field(description="Path relative to the repo root.")
    line_start: int
    line_end: Optional[int] = None
    function: Optional[str] = Field(None, description="Qualified name, e.g. module.func.")
    snippet: Optional[str] = Field(None, description="Source text of the statement.")


class Provenance(str, Enum):
    ast = "ast"  # produced by deterministic static analysis
    llm = "llm"  # produced or completed by an LLM
    manual = "manual"  # hand annotation (gold data)


class Confidence(str, Enum):
    mechanical = "mechanical"  # every link in the evidence chain was checked by a tool
    llm_assisted = "llm_assisted"  # at least one link relied on an LLM judgment
    llm_only = "llm_only"


# --------------------------------------------------------------------------- #
# Artifact
# --------------------------------------------------------------------------- #
class Artifact(_Record):
    schema_version: str = SCHEMA_VERSION
    artifact_id: str
    paper_title: str
    paper_url: str
    venue: Optional[str] = None
    repo_url: str
    commit: str
    domain: str = Field(description="e.g. sparse_attention, kv_cache, cluster_scheduling")
    entry_points: list[str] = Field(
        default_factory=list,
        description="Qualified names of functions that implement the paper's mechanism.",
    )
    execution_env: list[str] = Field(
        default_factory=list, description="cpu, cpu_mock, simulator, gpu"
    )
    notes: Optional[str] = None


# --------------------------------------------------------------------------- #
# Step 1 (paper side, Zhaopeng)
# --------------------------------------------------------------------------- #
class ClaimKind(str, Enum):
    capability = "capability"  # "supports X"
    accuracy = "accuracy"
    performance = "performance"
    guarantee = "guarantee"  # e.g. "ensures coverage >= gamma"
    other = "other"


class Claim(_Record):
    schema_version: str = SCHEMA_VERSION
    claim_id: str
    artifact_id: str
    mechanism: str
    statement: str
    kind: ClaimKind
    evidence: list[TextEvidence]


class ScopeKind(str, Enum):
    interval = "interval"
    set = "set"
    boolean = "boolean"
    free_text = "free_text"


class ScopeItem(_Record):
    """One dimension of the paper's claimed scope, e.g. context length in [4K, 128K]."""

    schema_version: str = SCHEMA_VERSION
    scope_id: str
    artifact_id: str
    param: str = Field(description="Paper-level parameter name, e.g. context_length.")
    kind: ScopeKind
    lower: Optional[float] = None
    upper: Optional[float] = None
    values: Optional[list[Any]] = None
    unit: Optional[str] = None
    explicit: bool = Field(
        True, description="False when inferred only from what the evaluation covered."
    )
    evidence: list[TextEvidence]


class EvalPoint(_Record):
    """One configuration the paper actually evaluated."""

    schema_version: str = SCHEMA_VERSION
    eval_id: str
    artifact_id: str
    config: dict[str, Any] = Field(description="Paper-level parameter -> value.")
    evidence: list[TextEvidence]


class BindingKind(str, Enum):
    mechanism_entry = "mechanism_entry"
    parameter = "parameter"
    config_key = "config_key"


class Binding(_Record):
    """Maps a paper-level concept to a code location."""

    schema_version: str = SCHEMA_VERSION
    binding_id: str
    artifact_id: str
    paper_term: str
    kind: BindingKind
    code_symbol: str = Field(description="Variable, parameter, config key, or qualified function.")
    location: Optional[CodeLocation] = None
    certain: bool = True
    rationale: Optional[str] = None


# --------------------------------------------------------------------------- #
# Step 2 (code side, Wanting)
# --------------------------------------------------------------------------- #
class Outcome(str, Enum):
    mechanism = "mechanism"  # the paper's mechanism runs
    mechanism_variant = "mechanism_variant"  # a documented internal variant of it
    fallback = "fallback"  # silently runs a baseline or dense implementation
    reject = "reject"  # assert / raise
    env_dependent = "env_dependent"  # depends on installed packages, GPU model, versions
    state_dependent = "state_dependent"  # depends on global or cached state
    suspicious = "suspicious"  # e.g. a hard-coded constant that shadows a parameter


class Condition(_Record):
    expr: str = Field(description="Python boolean expression over code-level names.")
    params: list[str] = Field(default_factory=list, description="Code-level names it depends on.")
    path_prefix: list[str] = Field(
        default_factory=list,
        description="Enclosing branch conditions (already negated where needed), outermost first.",
    )


class Region(_Record):
    """One row of the region table: under `condition`, the code reaches `outcome`."""

    schema_version: str = SCHEMA_VERSION
    region_id: str
    artifact_id: str
    entry_point: str
    condition: Condition
    outcome: Outcome
    outcome_detail: Optional[str] = Field(None, description="e.g. 'returns flash_attn_func(...)'.")
    location: CodeLocation
    call_chain: list[str] = Field(default_factory=list, description="Entry -> ... -> function.")
    provenance: Provenance
    notes: Optional[str] = None


# --------------------------------------------------------------------------- #
# Limitations (both sides)
# --------------------------------------------------------------------------- #
class Origin(str, Enum):
    paper = "paper"
    code = "code"


class Level(str, Enum):
    L1 = "L1"  # visible in the paper's evaluation results
    L2 = "L2"  # paper-code gap
    L3 = "L3"  # hidden assumption (paper assumption x variant checklist)


class EffectType(str, Enum):
    reject = "reject"
    path_change = "path_change"
    resource = "resource"
    performance = "performance"
    accuracy = "accuracy"
    state = "state"
    other = "other"


class Limitation(_Record):
    """A condition -> effect statement, from either side."""

    schema_version: str = SCHEMA_VERSION
    limitation_id: str
    artifact_id: str
    origin: Origin
    level: Optional[Level] = Field(None, description="Set by the paper side for L1/L3; L2 is set in step 4.")
    condition_text: str
    condition: Optional[Condition] = None
    effect_type: EffectType
    effect_text: str
    paper_evidence: list[TextEvidence] = Field(default_factory=list)
    code_evidence: list[CodeLocation] = Field(default_factory=list)
    region_ids: list[str] = Field(default_factory=list)
    provenance: Provenance
    notes: Optional[str] = None
    swarm_category: Optional[SwarmCategory] = None
    swarm_provenance: Optional[dict[str, Any]] = None


# --------------------------------------------------------------------------- #
# Step 3 (mutual verification)
# --------------------------------------------------------------------------- #
class Direction(str, Enum):
    paper_to_code = "paper_to_code"  # 3a, Zhaopeng
    code_to_paper = "code_to_paper"  # 3b, Wanting


class MatchResult(str, Enum):
    found = "found"  # the other side states / implements it with the same boundary
    boundary_mismatch = "boundary_mismatch"
    weaker = "weaker"  # documented, but weaker than the code behaviour ("tested with" vs "requires")
    not_found = "not_found"
    contradicted = "contradicted"


class ScopeStatus(str, Enum):
    in_scope = "in_scope"
    scope_edge = "scope_edge"  # touches an explicit assumption of the paper
    out_of_scope = "out_of_scope"
    unknown = "unknown"


class Verification(_Record):
    schema_version: str = SCHEMA_VERSION
    verification_id: str
    limitation_id: str
    direction: Direction
    result: MatchResult
    documented_in: list[DocSource] = Field(default_factory=list)
    matching_evidence: list[TextEvidence] = Field(default_factory=list)
    matching_code: list[CodeLocation] = Field(default_factory=list)
    scope_status: ScopeStatus = ScopeStatus.unknown
    evaluated_in_paper: Optional[bool] = Field(None, description="Does the region contain an EvalPoint?")
    verifier: str = Field(description="'human:<name>' or 'llm:<model>'.")
    rationale: Optional[str] = None


# --------------------------------------------------------------------------- #
# Step 4 (integration, Wanting)
# --------------------------------------------------------------------------- #
class FindingCategory(str, Enum):
    """v0.2.0. Documentation rule: only the paper (incl. appendix), the README and docstrings of public
    functions count as stated; code comments (TODO/FIXME included) and version-only notes do not."""

    # code side (from 3b)
    undisclosed = "undisclosed"  # code has it, nothing a user reads states it  <- core finding
    contradicts_docs = "contradicts_docs"  # a doc states the opposite of what the code does
    stated_differently = "stated_differently"  # a doc states it, with another boundary or a weaker form
    docs_only = "docs_only"  # README / public docstring states it, the paper does not
    paper_stated = "paper_stated"  # the paper states it with the same boundary as the code
    # paper side (from 3a)
    impl_deviates = "impl_deviates"  # the paper describes it, the code implements it differently
    not_implemented = "not_implemented"  # the paper describes it, the code has nothing for it
    paper_hypothesis = "paper_hypothesis"  # a proposed limitation grounded in paper evidence


class ReviewStatus(str, Enum):
    unreviewed = "unreviewed"
    worth_testing = "worth_testing"  # real and worth a test
    real_but_minor = "real_but_minor"  # real, but not worth a test (env detail, internal invariant, ...)
    wrong = "wrong"  # misread code or not a limitation


class Finding(_Record):
    schema_version: str = SCHEMA_VERSION
    finding_id: str
    artifact_id: str
    origin: Literal["v1", "swarm"] = "v1"
    category: FindingCategory
    level: Level
    limitation_ids: list[str]
    verification_ids: list[str] = Field(default_factory=list)
    scope_status: ScopeStatus
    evaluated_in_paper: Optional[bool] = None
    effect_type: EffectType
    summary: str
    witness_hint: Optional[dict[str, Any]] = Field(
        None, description="Concrete values satisfying scope and region condition, for step 5."
    )
    confidence: Confidence
    priority: int = Field(2, ge=1, le=3, description="1 = highest.")
    rationale: Optional[str] = None
    review: ReviewStatus = ReviewStatus.unreviewed
    review_note: Optional[str] = Field(None, description="Who reviewed (human:<name> / llm:<model>) and why.")


# --------------------------------------------------------------------------- #
# Steps 5-6 (Shanghao)
# --------------------------------------------------------------------------- #
class WitnessType(str, Enum):
    input_value = "input_value"
    event_sequence = "event_sequence"


class OracleType(str, Enum):
    exception = "exception"
    path_hook = "path_hook"
    differential = "differential"
    metamorphic = "metamorphic"
    resource = "resource"


class ExecEnv(str, Enum):
    cpu = "cpu"
    cpu_mock = "cpu_mock"
    simulator = "simulator"
    gpu = "gpu"
    none = "none"


class ExecResult(str, Enum):
    confirmed = "confirmed"
    refuted = "refuted"
    test_error = "test_error"
    not_run = "not_run"


class TestCase(_Record):
    __test__ = False  # keep pytest from collecting this class

    schema_version: str = SCHEMA_VERSION
    test_id: str
    finding_id: str
    witness_type: WitnessType
    inputs: list[dict[str, Any]]
    oracle_type: OracleType
    oracle_spec: str
    executable_on: ExecEnv
    file: Optional[str] = None
    result: ExecResult = ExecResult.not_run
    result_notes: Optional[str] = None


ALL_MODELS: dict[str, type[_Record]] = {
    "artifact": Artifact,
    "claim": Claim,
    "scope_item": ScopeItem,
    "eval_point": EvalPoint,
    "binding": Binding,
    "region": Region,
    "limitation": Limitation,
    "verification": Verification,
    "finding": Finding,
    "test_case": TestCase,
}
