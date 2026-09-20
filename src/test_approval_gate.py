"""
test_approval_gate.py — Phase 3 verification.

Same discipline as test_state.py (Phase 1) and test_planner.py (Phase 2):
prove the failure/loop cases programmatically, not just the happy path.
Resumes are driven with Command(resume=...) directly — no real input() —
so this runs unattended and deterministically.

Run:
    python3 test_approval_gate.py
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


def _start_run(graph, run_id: str):
    config = {"configurable": {"thread_id": run_id}}
    initial_state = {**new_run_state(run_id), "requirement": REQUIREMENT}
    result = graph.invoke(initial_state, config)
    return result, config


def immediate_approval_reaches_done():
    graph = build_graph()
    result, config = _start_run(graph, "test-approve-immediately")

    assert "__interrupt__" in result, "expected graph to pause for approval"
    payload = result["__interrupt__"][0].value
    assert payload["requirement"] == REQUIREMENT
    assert len(payload["acceptance_criteria"]) >= 1

    result = graph.invoke(Command(resume=True), config)
    assert "__interrupt__" not in result
    assert result["status"] == RunStatus.DONE
    assert result["spec"] is not None
    assert result["retries"].spec_approval_retries == 0


check("immediate approval reaches DONE with a spec, no retries spent", immediate_approval_reaches_done)


def reject_once_then_approve_loops_back_to_planner():
    graph = build_graph()
    result, config = _start_run(graph, "test-reject-then-approve")

    first_spec = result["__interrupt__"][0].value

    # Reject -> should loop back through the Planner and interrupt again,
    # not just re-ask about the same spec.
    result = graph.invoke(Command(resume=False), config)
    assert "__interrupt__" in result, "expected a second approval pause after looping back to Planner"
    assert result["retries"].spec_approval_retries == 1

    second_spec = result["__interrupt__"][0].value
    assert second_spec["run_id"] == first_spec["run_id"]  # same run, new Planner attempt

    # Approve the second attempt.
    result = graph.invoke(Command(resume=True), config)
    assert "__interrupt__" not in result
    assert result["status"] == RunStatus.DONE
    assert result["retries"].spec_approval_retries == 1


check(
    "rejecting once loops back to the Planner, approving the retry completes the run",
    reject_once_then_approve_loops_back_to_planner,
)


def repeated_rejection_stops_at_max_retries():
    graph = build_graph()
    result, config = _start_run(graph, "test-max-retries-exceeded")

    max_retries = result["retries"].max_spec_approval_retries
    assert max_retries == 3, "test assumes RetryCounters' default of 3 — update this test if that default changes"

    for _ in range(max_retries):
        result = graph.invoke(Command(resume=False), config)

    assert "__interrupt__" not in result, "graph should have stopped, not paused for another approval"
    assert result["status"] == RunStatus.FAILED
    assert result["retries"].spec_approval_retries == max_retries


check(
    "rejecting max_spec_approval_retries times in a row ends the run FAILED, not looping forever",
    repeated_rejection_stops_at_max_retries,
)


print("\nAll Phase 3 approval-gate checks passed.")
