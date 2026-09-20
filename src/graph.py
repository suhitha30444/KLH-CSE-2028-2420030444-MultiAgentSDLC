"""
graph.py — Phase 3: the human approval gate (SDD review gate).
             Phase 4: extends the SAME StateGraph with Coder, stub Tester,
             and Reviewer nodes, plus the test/review retry loop.
             Phase 6: tester_node now calls the REAL sandboxed Tester
             (agents.run_tester_real) for production runs; the Phase 4
             stub (agents.run_tester_stub) survives only as the
             deliberate-override test/demo hook — see tester_node below.

Scope discipline (per EVALUATION_AND_ROADMAP.md): Phase 3 built the
Planner + human-approval loop. Phase 4 extends this same compiled graph —
per the roadmap's own instruction ("this is the first phase that extends
graph.py's existing StateGraph rather than building a new one") — with
coder -> tester -> reviewer, routing any unsatisfied criterion back to the
Coder, capped by retries.test_review_retries / max_test_review_retries
(a counter SEPARATE from spec_approval_retries — see state.py's
RetryCounters docstring for why those two are never conflated). Phase 6
adds one more edge shape at the SAME layer: a real Tester can also fail to
produce something usable (TesterOutputError, e.g. malformed test-generation
JSON) exactly like the Coder/Reviewer already can, so it shares the same
retry-back-to-Coder handling rather than inventing new plumbing.

Uses LangGraph's interrupt()/Command(resume=...) pattern, checked against
langgraph==1.2.11 (the version this project has been built and verified
against in every phase so far).

Run directly for a demo / smoke test:
    python3 graph.py
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from agents import (
    CoderOutputError,
    PlannerOutputError,
    ReviewerOutputError,
    TesterOutputError,
    run_coder,
    run_planner,
    run_reviewer,
    run_tester_real,
    run_tester_stub,
)
from state import RunStatus, SDLCState


class ApprovalGraphState(SDLCState):
    """SDLCState plus the graph-layer fields Phase 1's shared schema
    doesn't need to know about.

    DECISION: extending SDLCState here via TypedDict inheritance, rather
    than adding these to state.py itself. state.py is Phase 1's file,
    already "done and verified" — these fields are only needed within
    this graph, so they belong at the graph layer.

      - requirement: str — the raw plain-English ask (Phase 3). Needed for
        the Planner-retry loop within this graph.

      - force_tester_fail_criteria / force_tester_fail_attempts (Phase 4,
        testing/demo hooks only, read defensively via `.get()` with
        defaults in tester_node so a production caller that never sets
        them behaves exactly as if this class didn't declare them):
        criterion ids the stub Tester should fail, and for how many of the
        Coder's first N attempts. This is what lets a demo/test show a
        real recovery (fail once, loop back to the Coder, pass on retry)
        instead of failing forever or never failing at all. Phase 6:
        tester_node uses these two fields to decide whether to run the
        real sandboxed Tester or the Phase 4 stub — see tester_node's
        docstring for why a real Tester can never honestly honor a forced
        failure.

        CORRECTNESS NOTE: these two started out deliberately NOT declared
        as TypedDict fields, on the theory that "testing-only" fields
        shouldn't look like part of the production schema. That was wrong
        in a way that broke the feature outright: LangGraph's StateGraph
        only creates a state "channel" for keys present in the schema's
        type annotations — an extra key handed to `.invoke()` that isn't
        declared here is silently dropped before any node ever sees it,
        not an error, just quietly ignored. Caught by graph.py's own demo
        block asserting `test_review_retries == 1` and getting 0 instead.
        Declaring them (with no default value required — a caller that
        omits them from the initial dict is unaffected, same as before)
        is the fix; they're still not meant to be used outside tests/demos,
        that discipline just isn't enforceable through omission from this
        class.
    """

    requirement: str
    force_tester_fail_criteria: list[str]
    force_tester_fail_attempts: int

    # coder_feedback: a human-readable description of why the LAST attempt
    # that reached this point in the pipeline didn't work, or "" once a
    # Coder attempt both succeeds AND its feedback has been consumed.
    # Populated from two different sources, both read by coder_node and
    # passed into run_coder(..., previous_error=...) so a retry actually
    # tells the LLM what to fix instead of resending the identical prompt
    # and hoping a systematic mistake doesn't repeat:
    #   - coder_node itself, on a CoderOutputError (str(exc) — invalid
    #     JSON or a syntax error such as double-escaped newlines).
    #   - reviewer_node, when tests_passed/all_approved isn't fully true —
    #     a per-criterion summary of which acceptance criteria failed
    #     their test or were rejected by the Reviewer, and why. Without
    #     this, every "loop back to the Coder because a criterion isn't
    #     satisfied yet" retry was ALSO a blind resample (same root gap
    #     as the CoderOutputError case, just triggered from a different
    #     node) — the Coder never learned which criterion was wrong or
    #     what the Tester/Reviewer actually said about it.
    # Declared here (not left to an undeclared dict key) for the same
    # reason force_tester_fail_criteria/_attempts are declared above:
    # LangGraph only creates a state channel for keys present in this
    # TypedDict's annotations, so an undeclared key would be silently
    # dropped rather than threaded across nodes. Read defensively via
    # `.get()` in coder_node so callers that never set it (e.g. main.py's
    # initial_state) are unaffected.
    coder_feedback: str


def planner_node(state: ApprovalGraphState) -> dict:
    """Run the Planner. On a PlannerOutputError (malformed LLM JSON), retry
    automatically rather than surfacing a stack trace or bothering the human
    with an invalid spec to review.

    DECISION: PlannerOutputError retries share the SAME counter
    (retries.spec_approval_retries) as human rejections, rather than a
    fourth separate counter — see Phase 3's decisions log for the full
    rationale.
    """
    try:
        spec = run_planner(state["run_id"], state["requirement"])
    except PlannerOutputError as exc:
        retries = state["retries"]
        retries.spec_approval_retries += 1
        print(
            f"[planner] Planner output failed validation "
            f"(attempt {retries.spec_approval_retries}/"
            f"{retries.max_spec_approval_retries}): {exc}"
        )
        if retries.spec_approval_retries >= retries.max_spec_approval_retries:
            return {"retries": retries, "status": RunStatus.FAILED, "spec": None}
        return {"retries": retries, "status": RunStatus.IN_PROGRESS, "spec": None}

    return {"spec": spec, "status": RunStatus.IN_PROGRESS}


def route_after_planner(state: ApprovalGraphState) -> str:
    if state["status"] == RunStatus.FAILED:
        return "max_retries_exceeded"
    if state["spec"] is None:
        # Planner errored but hasn't hit the cap yet — try again.
        return "retry_planner"
    return "await_approval"


def approval_node(state: ApprovalGraphState) -> dict:
    """Pause the graph and hand the human everything they need to judge the
    spec: the plain-English requirement plus every acceptance criterion.

    The actual y/n prompt happens OUTSIDE this node, in the caller
    (main.py) — interrupt() can't block on input() itself, it just pauses
    graph execution and hands `.invoke()`'s caller the payload below.
    """
    spec = state["spec"]
    approved: bool = interrupt(
        {
            "run_id": spec.run_id,
            "requirement": spec.requirement,
            "acceptance_criteria": spec.acceptance_criteria_text,
        }
    )

    if approved:
        return {"status": RunStatus.DONE}

    retries = state["retries"]
    retries.spec_approval_retries += 1
    if retries.spec_approval_retries >= retries.max_spec_approval_retries:
        return {"retries": retries, "status": RunStatus.FAILED}
    return {"retries": retries, "status": RunStatus.IN_PROGRESS}


def route_after_approval(state: ApprovalGraphState) -> str:
    if state["status"] == RunStatus.DONE:
        return "approved"
    if state["status"] == RunStatus.FAILED:
        return "max_retries_exceeded"
    return "retry_planner"


# ---------------------------------------------------------------------------
# Phase 4: Coder -> stub Tester -> Reviewer, with the test/review retry loop
# Phase 6: tester_node now runs the REAL sandboxed Tester by default
# ---------------------------------------------------------------------------
#
# DECISION: status is decided INSIDE coder_node / reviewer_node (same
# pattern Phase 3 already established in planner_node / approval_node),
# and the route_after_* functions are pure "read status, pick an edge
# label" mappers with no side effects of their own. Keeping all retry-cap
# arithmetic inside the node that owns it, rather than in the routing
# function, is what Phase 3 already proved works cleanly with LangGraph's
# conditional edges. tester_node follows the same shape now that it can
# fail too (Phase 6).


def coder_node(state: ApprovalGraphState) -> dict:
    """Run the Coder against the approved spec. On a CoderOutputError
    (malformed LLM JSON / zero artifacts), retry automatically, sharing
    retries.test_review_retries with failed-test/rejected-review retries —
    both are "the Coder hasn't produced something usable yet" from the
    run's point of view, same reasoning Phase 3 used for its own counter
    reuse decision.

    Bug fix: retries now carry `coder_feedback` forward into the next
    attempt's prompt (via run_coder(..., previous_error=...)) instead of
    resending the identical prompt every time. Previously every retry was
    a blind resample with zero information about the prior failure, which
    let a systematic mistake (e.g. the model double-escaping newlines in
    its JSON string) repeat across the entire retry budget — exactly what
    happened on a live run: 4 straight invalid-JSON failures, then the
    same double-escaped-newline syntax error on the 5th and final attempt,
    never once told what it had gotten wrong. `coder_feedback` is also
    populated by reviewer_node with per-criterion failure detail, so a
    retry triggered by a failed test or a rejected review is no longer
    blind either — see ApprovalGraphState's docstring.
    """
    spec = state["spec"]
    previous_error = state.get("coder_feedback") or None
    try:
        artifacts = run_coder(state["run_id"], spec, previous_error=previous_error)
    except CoderOutputError as exc:
        retries = state["retries"]
        retries.test_review_retries += 1
        print(
            f"[coder] Coder output failed validation "
            f"(attempt {retries.test_review_retries}/"
            f"{retries.max_test_review_retries}): {exc}"
        )
        if retries.test_review_retries >= retries.max_test_review_retries:
            return {
                "retries": retries,
                "status": RunStatus.FAILED,
                "code_artifacts": [],
                "coder_feedback": str(exc),
            }
        return {
            "retries": retries,
            "status": RunStatus.IN_PROGRESS,
            "code_artifacts": [],
            "coder_feedback": str(exc),
        }

    print(f"[coder] produced {len(artifacts)} artifact(s): {[a.filename for a in artifacts]}")
    return {"code_artifacts": artifacts, "status": RunStatus.IN_PROGRESS, "coder_feedback": ""}


def route_after_coder(state: ApprovalGraphState) -> str:
    if state["status"] == RunStatus.FAILED:
        return "max_retries_exceeded"
    if not state["code_artifacts"]:
        # Coder errored but hasn't hit the cap yet.
        return "retry_coder"
    return "run_tests"


def tester_node(state: ApprovalGraphState) -> dict:
    """Phase 6: run the REAL sandboxed Tester (agents.run_tester_real) by
    default — the worker LLM writes one test script per acceptance
    criterion, and each is genuinely executed in sandbox.py's subprocess
    sandbox, so passed/failed comes from a real exit code, not a guess.

    EXCEPTION, test/demo path only: if the graph state explicitly carries
    force_tester_fail_criteria/force_tester_fail_attempts (see
    ApprovalGraphState's docstring), this node uses the Phase 4 stub
    (agents.run_tester_stub) instead. This is intentional, not a
    leftover — a real Tester decides pass/fail by actually running the
    code, so it CANNOT honestly be told in advance which criterion to
    fail; forcing a failure to prove the retry loop's wiring only makes
    sense against the stub, which exists for exactly that purpose and
    says so in its own docstring. Production callers (main.py) never set
    these fields, so they always take the real path.

    On TesterOutputError (the Tester LLM's test-generation output itself
    couldn't be trusted — invalid JSON, missing criterion, etc.), retries
    exactly like coder_node/reviewer_node: shares
    retries.test_review_retries and loops back to the Coder once under
    the cap, same "hasn't produced something usable yet" category Phase 4
    established.
    """
    spec = state["spec"]
    retries = state["retries"]
    force_criteria = state.get("force_tester_fail_criteria") or []
    force_attempts = state.get("force_tester_fail_attempts", 0)

    if force_criteria or force_attempts:
        apply_force = force_criteria if retries.test_review_retries < force_attempts else []
        results = run_tester_stub(spec, state["code_artifacts"], force_fail_criteria=apply_force)
        passed = sum(1 for r in results if r.passed)
        print(f"[tester] (stub, forced — test/demo path) {passed}/{len(results)} criteria passed")
        return {"test_results": results, "status": RunStatus.IN_PROGRESS}

    try:
        results = run_tester_real(state["run_id"], spec, state["code_artifacts"])
    except TesterOutputError as exc:
        retries.test_review_retries += 1
        print(
            f"[tester] Tester output failed validation "
            f"(attempt {retries.test_review_retries}/"
            f"{retries.max_test_review_retries}): {exc}"
        )
        if retries.test_review_retries >= retries.max_test_review_retries:
            return {"retries": retries, "status": RunStatus.FAILED, "test_results": []}
        return {"retries": retries, "status": RunStatus.IN_PROGRESS, "test_results": []}

    passed = sum(1 for r in results if r.passed)
    print(f"[tester] {passed}/{len(results)} criteria passed (real sandboxed execution)")
    return {"test_results": results, "status": RunStatus.IN_PROGRESS}


def route_after_tester(state: ApprovalGraphState) -> str:
    """Phase 6: mirrors route_after_coder's shape. A TesterOutputError
    leaves test_results empty without having hit the cap yet (see
    tester_node above) — that's the same "errored, not yet capped, try
    again" signal route_after_coder already uses for code_artifacts.
    """
    if state["status"] == RunStatus.FAILED:
        return "max_retries_exceeded"
    if not state["test_results"]:
        return "retry_coder"
    return "run_review"


def reviewer_node(state: ApprovalGraphState) -> dict:
    """Run the Reviewer against the Tester's results. A run only reaches
    DONE when EVERY criterion both passed its test AND was approved by the
    Reviewer — see run_reviewer()'s docstring in agents.py for the
    reasoning, now backed by Phase 6's real test evidence instead of
    Phase 4's canned stub results.

    On ReviewerOutputError, or on any unsatisfied criterion, increments
    retries.test_review_retries and either loops back to the Coder or
    ends the run FAILED once the cap is hit — never loops forever.

    Bug fix: on an unsatisfied criterion (not a ReviewerOutputError — that
    branch is the Reviewer's own JSON problem, not something the Coder can
    act on), also builds `coder_feedback`: a per-criterion summary of the
    real test failure detail and/or the Reviewer's rejection reason, so
    the next Coder attempt is told exactly what to fix instead of blindly
    resampling the same (broken) logic again.
    """
    spec = state["spec"]
    test_results = state["test_results"]

    try:
        verdicts = run_reviewer(state["run_id"], spec, test_results)
    except ReviewerOutputError as exc:
        retries = state["retries"]
        retries.test_review_retries += 1
        print(
            f"[reviewer] Reviewer output failed validation "
            f"(attempt {retries.test_review_retries}/"
            f"{retries.max_test_review_retries}): {exc}"
        )
        if retries.test_review_retries >= retries.max_test_review_retries:
            return {"retries": retries, "status": RunStatus.FAILED, "review_verdicts": []}
        return {"retries": retries, "status": RunStatus.IN_PROGRESS, "review_verdicts": []}

    tests_passed = all(r.passed for r in test_results)
    all_approved = all(v.approved for v in verdicts)

    if tests_passed and all_approved:
        print("[reviewer] all criteria passed and approved — DONE")
        return {"review_verdicts": verdicts, "status": RunStatus.DONE}

    failing = sorted(
        {r.criterion_id for r in test_results if not r.passed}
        | {v.criterion_id for v in verdicts if not v.approved}
    )

    # Bug fix: tell the Coder WHICH criteria failed and WHY, instead of
    # silently looping back with no information (the same "blind resample"
    # gap coder_node's own CoderOutputError feedback closes — see
    # ApprovalGraphState's coder_feedback docstring). Built from the real
    # per-criterion test detail (sandboxed exit code / stderr) and the
    # Reviewer's own justification, not a guess.
    criteria_by_id = {c.id: c.text for c in spec.acceptance_criteria}
    results_by_id = {r.criterion_id: r for r in test_results}
    verdicts_by_id = {v.criterion_id: v for v in verdicts}
    feedback_lines = []
    for cid in failing:
        crit_text = criteria_by_id.get(cid, "(unknown criterion)")
        detail_parts = []
        result = results_by_id.get(cid)
        if result is not None and not result.passed:
            detail_parts.append(f"test FAILED: {result.detail[:400]}")
        verdict = verdicts_by_id.get(cid)
        if verdict is not None and not verdict.approved:
            detail_parts.append(f"reviewer rejected: {verdict.justification[:400]}")
        feedback_lines.append(f"  - {cid} ({crit_text}) — " + "; ".join(detail_parts))
    coder_feedback = (
        "Your previous submission did not satisfy every acceptance "
        "criterion. Fix EXACTLY these problems without breaking the "
        "criteria that already pass:\n" + "\n".join(feedback_lines)
    )

    retries = state["retries"]
    retries.test_review_retries += 1
    print(
        f"[reviewer] not satisfied yet ({failing}); "
        f"retry {retries.test_review_retries}/{retries.max_test_review_retries}"
    )
    if retries.test_review_retries >= retries.max_test_review_retries:
        return {
            "review_verdicts": verdicts,
            "retries": retries,
            "status": RunStatus.FAILED,
            "coder_feedback": coder_feedback,
        }
    return {
        "review_verdicts": verdicts,
        "retries": retries,
        "status": RunStatus.IN_PROGRESS,
        "coder_feedback": coder_feedback,
    }


def route_after_reviewer(state: ApprovalGraphState) -> str:
    if state["status"] == RunStatus.DONE:
        return "approved"
    if state["status"] == RunStatus.FAILED:
        return "max_retries_exceeded"
    return "retry_coder"


def build_graph():
    """Compile the graph: Planner -> human approval -> Coder -> (real)
    Tester -> Reviewer -> (loop back to Coder | done | failed).

    DECISION: MemorySaver (in-memory checkpointer) — unchanged from Phase 3,
    same known limitation (no durable checkpoint across a process restart;
    see Phase 3's decisions log).
    """
    builder = StateGraph(ApprovalGraphState)

    builder.add_node("planner", planner_node)
    builder.add_node("approval", approval_node)
    builder.add_node("coder", coder_node)
    builder.add_node("tester", tester_node)
    builder.add_node("reviewer", reviewer_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "await_approval": "approval",
            "retry_planner": "planner",
            "max_retries_exceeded": END,
        },
    )
    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            # CHANGED from Phase 3: an approved spec now proceeds into the
            # Coder/Tester/Reviewer loop instead of ending the run at END.
            "approved": "coder",
            "retry_planner": "planner",
            "max_retries_exceeded": END,
        },
    )
    builder.add_conditional_edges(
        "coder",
        route_after_coder,
        {
            "run_tests": "tester",
            "retry_coder": "coder",
            "max_retries_exceeded": END,
        },
    )
    # CHANGED (Phase 6): tester -> reviewer was an unconditional edge in
    # Phase 4 (the stub Tester could never fail to produce a result). Now
    # that the real Tester can raise TesterOutputError, this needs the
    # same three-way conditional shape as coder's edges.
    builder.add_conditional_edges(
        "tester",
        route_after_tester,
        {
            "run_review": "reviewer",
            "retry_coder": "coder",
            "max_retries_exceeded": END,
        },
    )
    builder.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "approved": END,
            "retry_coder": "coder",
            "max_retries_exceeded": END,
        },
    )

    # LangGraph checkpoints state via msgpack and, as of 1.2.11, warns on
    # every unregistered custom type it has to serialize — registering
    # state.py's types explicitly avoids the noise and a future hard break.
    # CodeArtifact / PerCriterionResult / ReviewVerdict added here in
    # Phase 4 for the same reason Spec/RetryCounters/RunStatus were
    # registered in Phase 3 — they're now checkpointed too. Phase 6 adds
    # no new checkpointed types (sandbox.SandboxResult never enters
    # SDLCState — it's consumed and turned into a PerCriterionResult
    # entirely inside run_tester_real(), so the graph layer never sees it).
    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("state", "Spec"),
            ("state", "RetryCounters"),
            ("state", "RunStatus"),
            ("state", "CodeArtifact"),
            ("state", "PerCriterionResult"),
            ("state", "ReviewVerdict"),
        ]
    )
    checkpointer = MemorySaver(serde=serde)
    return builder.compile(checkpointer=checkpointer)


def _print_run_summary(result: dict) -> None:
    """Shared by this file's demo block and main.py: a human-readable trace
    of one run — the informal preview of what Phase 7's traceability report
    formalizes into requirement -> criterion -> task -> code -> test ->
    verdict.
    """
    spec = result.get("spec")
    if spec is not None:
        print(f"\nRequirement: {spec.requirement}")
        print("Acceptance criteria:")
        for c in spec.acceptance_criteria:
            print(f"  {c.id}: {c.text}")

    artifacts = result.get("code_artifacts") or []
    if artifacts:
        print("\nCode artifacts:")
        for a in artifacts:
            print(f"  {a.filename} (task {a.task_id})")

    test_results = result.get("test_results") or []
    if test_results:
        print("\nTest results:")
        for r in test_results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.criterion_id}: {r.detail}")

    verdicts = result.get("review_verdicts") or []
    if verdicts:
        print("\nReview verdicts:")
        for v in verdicts:
            mark = "APPROVED" if v.approved else "REJECTED"
            print(f"  [{mark}] {v.criterion_id}: {v.justification}")

    retries = result.get("retries")
    if retries is not None:
        print(
            f"\nRetries spent: spec_approval={retries.spec_approval_retries}/"
            f"{retries.max_spec_approval_retries}, "
            f"test_review={retries.test_review_retries}/"
            f"{retries.max_test_review_retries}"
        )


if __name__ == "__main__":
    # Demo / smoke test, independent of main.py: runs the FULL pipeline,
    # deliberately forcing AC1 to fail on the Coder's first attempt so the
    # retry loop is actually exercised and visible — not just a happy path
    # that never proves the loop works, per the roadmap's Phase 4 "done
    # when": a forced stub failure must demonstrably send control back to
    # the Coder, and the run must still reach DONE once all criteria
    # stub-pass. This demo intentionally still exercises the STUB Tester
    # (via force_tester_fail_criteria/attempts below) — see tester_node's
    # docstring for why the forced-failure demo can only ever run against
    # the stub, never the real sandboxed Tester. test_real_tester.py is
    # where Phase 6's REAL Tester gets its own dedicated proof.
    from state import new_run_state

    graph = build_graph()
    run_id = "phase4-demo-run"
    config = {"configurable": {"thread_id": run_id}}
    initial_state = {
        **new_run_state(run_id),
        "requirement": "Write a function that reverses a string.",
        "force_tester_fail_criteria": ["AC1"],
        "force_tester_fail_attempts": 1,
    }

    print("=" * 70)
    print("DEMO: forcing AC1 to fail on the first attempt, on purpose (stub Tester)")
    print("=" * 70)

    result = graph.invoke(initial_state, config)
    assert "__interrupt__" in result, "expected the graph to pause for approval"
    payload = result["__interrupt__"][0].value
    print("\n[demo] Paused for approval. Payload the human would see:")
    print(f"  requirement: {payload['requirement']}")
    print(f"  acceptance_criteria: {payload['acceptance_criteria']}")

    result = graph.invoke(Command(resume=True), config)

    assert result["status"] == RunStatus.DONE, f"expected DONE, got {result['status']}"
    assert result["retries"].test_review_retries == 1, (
        "expected exactly one test/review retry (the forced AC1 failure "
        "recovering on the Coder's second attempt)"
    )

    _print_run_summary(result)
    print(
        "\n[demo] DONE. The forced AC1 failure on attempt 1 sent control "
        "back to the Coder, and attempt 2 passed cleanly — the retry loop "
        "is proven, not assumed."
    )
