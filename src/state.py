"""
state.py — Phase 1: SDD schemas, before any agent code.

Scope discipline (per EVALUATION_AND_ROADMAP.md Phase 1): this file defines
SHAPES ONLY. No LLM calls, no LangGraph wiring, no agent functions. That
comes in Phases 2-4. Coder/Tester/Reviewer get built AGAINST these shapes
from day one instead of retrofitted onto looser ones later.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, TypedDict

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 1. THE SPEC — the human-approved artifact (Phase 3 reviews exactly this)
# ---------------------------------------------------------------------------

class TaskItem(BaseModel):
    """One unit of implementation work the Planner breaks the requirement into.

    Consumed by: Coder (Phase 4) turns each TaskItem into a CodeArtifact.
    Consumed by: traceability report (Phase 7) as the "task" column between
    criterion and code.
    """

    id: str
    # DECISION: ids are short stable strings ("T1", "T2"...), not array indices.
    # Indices shift if you ever reorder tasks; a stable id is what the Phase 7
    # report and CodeArtifact.task_id below can safely reference.
    description: str

    addresses_criteria: list[str] = Field(default_factory=list)
    # Which AcceptanceCriterion ids (see Spec below) this task is meant to
    # satisfy. This is the literal thread Phase 7 walks:
    #   criterion -> task -> code -> test result -> review verdict.
    # DECISION: left optional (can be empty) rather than required-non-empty,
    # because the Planner may emit setup/scaffolding tasks that don't map to
    # any single criterion. Revisit once you see real Planner output.

    @field_validator("id", "description")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class AcceptanceCriterion(BaseModel):
    """A single, independently-checkable condition the final code must satisfy.

    DECISION: modeled as an object with a stable `id`, not a bare string, even
    though EVALUATION_AND_ROADMAP.md phrases the field as `acceptance_criteria:
    list[str]`. Reason: PerCriterionResult and ReviewVerdict both need a
    `criterion_id` to reference — if criteria were plain strings, that
    reference would have to be the string text itself (fragile — a
    one-character edit breaks every downstream link) or a positional index
    (fragile the moment criteria get reordered). `Spec.acceptance_criteria_text`
    below gives you the literal `list[str]` back for free if you need to match
    the roadmap's wording exactly (e.g. a human-readable printout in Phase 3).
    """

    id: str  # e.g. "AC1"
    text: str

    @field_validator("text")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class Spec(BaseModel):
    """The structured, persisted spec a human approves before code generation
    starts. Phase 2 writes this to disk as spec_<run_id>.json — this IS the
    project's spec.md-equivalent artifact. Phase 3's interrupt() node prints
    this object (requirement + acceptance criteria) and waits for y/n.
    """

    run_id: str
    requirement: str  # the raw plain-English ask, verbatim
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)
    # DECISION: min_length=1 enforced here on purpose. A spec with zero
    # acceptance criteria can't be tested or reviewed per-criterion at all —
    # better to reject it at the Planner's own validation step (Phase 2) than
    # let it silently flow through with empty lists later and no clear error
    # pointing at the actual cause.
    tasks: list[TaskItem] = Field(default_factory=list)

    @property
    def acceptance_criteria_text(self) -> list[str]:
        """Plain list[str] view, matching the roadmap doc's literal wording."""
        return [c.text for c in self.acceptance_criteria]


# ---------------------------------------------------------------------------
# 2. CODE OUTPUT
# ---------------------------------------------------------------------------

class CodeArtifact(BaseModel):
    """One generated file. Consumed by: Tester (Phase 6, sandboxed execution),
    Reviewer (Phase 7), and the traceability report (the "code" column).
    """

    filename: str
    content: str
    task_id: Optional[str] = None  # which TaskItem.id produced this file

    @field_validator("filename")
    @classmethod
    def _looks_like_a_filename(cls, v: str) -> str:
        if not v.strip() or "/" in v or "\\" in v:
            # DECISION: reject path separators outright rather than sanitizing
            # them. Phase 6 runs this content in a sandboxed subprocess — a
            # filename that's secretly a path (e.g. "../../evil.py") is worth
            # refusing at the schema boundary, not trusting the sandbox alone.
            raise ValueError(f"invalid filename: {v!r}")
        return v


# ---------------------------------------------------------------------------
# 3. TEST RESULTS
# ---------------------------------------------------------------------------

class PerCriterionResult(BaseModel):
    """Phase 6's real Tester produces ONE of these per acceptance criterion —
    never one blanket pass/fail for the whole run. This granularity is what
    lets the retry loop send control back to the Coder with a SPECIFIC
    reason ("AC2 failed: division by zero on empty input") instead of
    "something failed."
    """

    criterion_id: str  # must match an AcceptanceCriterion.id from the Spec
    passed: bool
    detail: str  # stdout/stderr/exception summary; human-readable reason

    @field_validator("detail")
    @classmethod
    def _detail_required_on_failure(cls, v: str, info) -> str:
        # DECISION: only enforced non-blank when passed=False. A passing
        # criterion can reasonably have terse detail ("OK"); a FAILING one
        # with blank detail is the exact "something failed" vagueness Phase 6
        # is explicitly trying to avoid.
        if info.data.get("passed") is False and not v.strip():
            raise ValueError("detail must explain the failure when passed=False")
        return v


# ---------------------------------------------------------------------------
# 4. REVIEW
# ---------------------------------------------------------------------------

class ReviewVerdict(BaseModel):
    """Reviewer's per-criterion judgment call. Phase 7 requires this to
    REFERENCE the actual PerCriterionResult, not just independently re-decide
    pass/fail — that linkage is enforced by convention (same criterion_id),
    not by this schema alone, since the schema can't see the Tester's output
    to cross-check it. Worth a runtime assertion in Phase 7: every
    ReviewVerdict.criterion_id should have a matching PerCriterionResult.
    """

    criterion_id: str
    approved: bool
    justification: str

    @field_validator("justification")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("justification must not be blank")
        return v


# ---------------------------------------------------------------------------
# 5. RETRY BOOKKEEPING
# ---------------------------------------------------------------------------

class RetryCounters(BaseModel):
    """Two SEPARATE counters, per EVALUATION_AND_ROADMAP.md's explicit
    instruction not to conflate them:

    - spec_approval_retries: a human rejects the spec in Phase 3's approval
      gate, looping back to the Planner.
    - test_review_retries: a failed test or a rejected review in Phases 4/6/7
      loops back to the Coder.

    A THIRD kind of retry (rate-limit backoff on Groq calls, Phase 5) does
    NOT belong here — it's transport-layer, lives in llm_client.py, and
    resets per-call rather than per-run. Mixing it in would let a string of
    rate-limit retries silently eat into the same budget as "the Coder keeps
    producing broken code," making `failed` runs ambiguous about which
    problem actually happened.

    DECISION (raised from 3 to 5 after real live-Groq evidence — see
    PHASE_6_PROGRESS_AND_DECISIONS.md): on a 5-7 acceptance-criterion
    requirement, real infrastructure/format hiccups (a Tester JSON gap, a
    Groq-side rejection) were observed consuming most or all of a 3-retry
    budget before the Coder's actual code got tested even once — not a
    correctness bug, just not enough attempts for a task of that size on
    free-tier models. 5 is a deliberate tradeoff: more attempts for
    complex requirements to actually get a fair shot, at the cost of more
    Groq calls (hence more free-tier quota) per FAILED run that was never
    going to succeed. Revisit if this number stops matching the
    complexity of requirements actually being run through this pipeline.
    """

    spec_approval_retries: int = 0
    max_spec_approval_retries: int = 3
    test_review_retries: int = 0
    max_test_review_retries: int = 5


# ---------------------------------------------------------------------------
# 6. AGILE-READINESS FIELDS — untouched, unused until Phase 10
# ---------------------------------------------------------------------------

class BacklogItem(BaseModel):
    """Per PROJECT_BRIEF.md: exists from Phase 1 onward so the eventual Agile
    migration (Phase 10) changes the graph's EDGES, not this data structure.
    Do not build logic against this yet.
    """

    id: str
    description: str
    done: bool = False


# ---------------------------------------------------------------------------
# 7. TOP-LEVEL GRAPH STATE
# ---------------------------------------------------------------------------

class RunStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class SDLCState(TypedDict):
    """The object LangGraph threads through every node, starting in Phase 4.

    DECISION: this top-level container is a TypedDict, not a Pydantic
    BaseModel, even though every field it holds IS a Pydantic model or a
    list of them. Reason: mirrors the Phase 0 toy graph exactly — nodes take
    the current state and return a partial dict, which LangGraph
    shallow-merges. LangGraph does support a Pydantic BaseModel as the
    top-level state schema too, but that pushes validation onto every node
    transition (a cost for a run with many nodes) and partial-update
    semantics get less predictable. Keeping the outer shape a plain
    TypedDict and pushing all the *validation* value into the nested
    Pydantic models gets the reliability benefit without that cost. Revisit
    this call in Phase 4 once the graph is actually wired — reasonable
    default, not a law.
    """

    run_id: str
    spec: Optional[Spec]
    code_artifacts: list[CodeArtifact]
    test_results: list[PerCriterionResult]
    review_verdicts: list[ReviewVerdict]
    retries: RetryCounters
    status: RunStatus

    # Agile-readiness fields (see BacklogItem above) — planned, untouched,
    # not read or written by any Phase 0-9 logic.
    backlog: list[BacklogItem]
    completed_increments: list[str]
    sprint_number: int


def new_run_state(run_id: str) -> SDLCState:
    """Build a fresh, empty SDLCState for a new run. This is the only helper
    in this file that "does" anything — everything else above is pure shape.
    main.py (from Phase 2 onward) will call this to seed a run.
    """
    return SDLCState(
        run_id=run_id,
        spec=None,
        code_artifacts=[],
        test_results=[],
        review_verdicts=[],
        retries=RetryCounters(),
        status=RunStatus.IN_PROGRESS,
        backlog=[],
        completed_increments=[],
        sprint_number=0,
    )
