"""
test_full_loop.py — Phase 4 verification.

Same discipline as test_state.py (Phase 1), test_planner.py (Phase 2), and
test_approval_gate.py (Phase 3): prove the failure/loop cases
programmatically, not just the happy path. Resumes are driven with
Command(resume=...) directly — no real input().

Per EVALUATION_AND_ROADMAP.md's Phase 4 "done when": a forced stub failure
must demonstrably send control back to the Coder, the run must terminate
FAILED once max_test_review_retries hits, and it must terminate DONE when
all criteria stub-pass. All three are checked below, not just the last one.

Run:
    python3 test_full_loop.py
"""

from langgraph.types import Command

from graph import build_graph
from state import RunStatus, new_run_state

REQUIREMENT = "Write a function that reverses a string."


def check(label: str, fn):
    try:
        fn()
        print(f"[ OK ] {label}")
    except AssertionError as e:
        print(f"[FAIL] {label}: {e}")
        raise


def _start_run(graph, run_id: str, **extra_state):
    config = {"configurable": {"thread_id": run_id}}
    initial_state = {**new_run_state(run_id), "requirement": REQUIREMENT, **extra_state}
    result = graph.invoke(initial_state, config)
    return result, config


def clean_run_reaches_done_on_first_attempt():
    graph = build_graph()
    result, config = _start_run(graph, "test-clean-first-attempt")

    assert "__interrupt__" in result, "expected graph to pause for approval"
    result = graph.invoke(Command(resume=True), config)

    assert "__interrupt__" not in result
    assert result["status"] == RunStatus.DONE
    assert result["retries"].test_review_retries == 0, "no forced failure was set — should pass on the first attempt"
    assert len(result["code_artifacts"]) >= 1
    assert len(result["test_results"]) == len(result["spec"].acceptance_criteria)
    assert all(r.passed for r in result["test_results"])
    assert len(result["review_verdicts"]) == len(result["spec"].acceptance_criteria)
    assert all(v.approved for v in result["review_verdicts"])


check(
    "a clean run (no forced failures) reaches DONE on the Coder's first attempt",
    clean_run_reaches_done_on_first_attempt,
)


def forced_failure_sends_control_back_to_coder_then_recovers():
    graph = build_graph()
    result, config = _start_run(
        graph,
        "test-forced-failure-recovers",
        force_tester_fail_criteria=["AC1"],
        force_tester_fail_attempts=1,
    )

    assert "__interrupt__" in result
    result = graph.invoke(Command(resume=True), config)

    assert "__interrupt__" not in result, "graph should not pause again after approval"
    assert result["status"] == RunStatus.DONE, (
        "expected the run to recover and reach DONE once the forced "
        "failure stopped applying on the Coder's second attempt"
    )
    assert result["retries"].test_review_retries == 1, (
        "expected EXACTLY one test/review retry — proves the forced AC1 "
        "failure actually routed back to the Coder, not zero (never "
        "failed) and not more than one (looped past the point it should "
        "have recovered)"
    )
    # The final test results must show a clean pass — this is the SECOND
    # attempt's results (Coder/Tester/Reviewer results aren't accumulated
    # across attempts, the latest attempt's results are what's in state).
    assert all(r.passed for r in result["test_results"])


check(
    "a forced single-criterion failure sends control back to the Coder, then recovers to DONE",
    forced_failure_sends_control_back_to_coder_then_recovers,
)


def persistent_failure_stops_at_max_retries_without_looping_forever():
    graph = build_graph()
    result, config = _start_run(
        graph,
        "test-persistent-failure-hits-cap",
        force_tester_fail_criteria=["AC1"],
        force_tester_fail_attempts=999,  # forces failure on every attempt
    )

    assert "__interrupt__" in result
    result = graph.invoke(Command(resume=True), config)

    max_retries = result["retries"].max_test_review_retries
    assert max_retries == 5, "test assumes RetryCounters' default of 5 — update this test if that default changes"

    assert "__interrupt__" not in result, "graph should have stopped, not paused again"
    assert result["status"] == RunStatus.FAILED
    assert result["retries"].test_review_retries == max_retries, (
        f"expected the loop to stop at exactly {max_retries} retries, "
        f"got {result['retries'].test_review_retries}"
    )
    # The spec itself was still approved and should still be persistable —
    # only the code/test/review loop failed, not the approval.
    assert result["spec"] is not None


check(
    "a criterion that keeps failing stops the run FAILED at max_test_review_retries, not an infinite loop",
    persistent_failure_stops_at_max_retries_without_looping_forever,
)


print("\nAll Phase 4 full-loop checks passed.")
