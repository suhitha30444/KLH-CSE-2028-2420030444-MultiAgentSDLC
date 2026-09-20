"""
main.py — Phase 3: entry point through Planner + human approval gate.
           Phase 4: the approved spec now continues through Coder ->
           Tester -> Reviewer instead of stopping at approval.
           Phase 6: that Tester is now the real sandboxed one by default.
           Phase 7: once a run reaches the code/test/review stage (i.e.
           the spec was approved), a traceability report is generated and
           persisted alongside the spec — see report.py.

Run:
    python3 main.py
    python3 main.py --requirement "Write a function that checks if a number is prime."
"""

from __future__ import annotations

import argparse
import sys
import uuid

# BUG #5, part 2 (see persistence.py's save_spec() for part 1 -- the file-
# write half of this same bug): every print() in this project ultimately
# goes through sys.stdout, whose encoding on Windows defaults to the same
# restrictive locale codepage (commonly cp1252) that crashed save_spec()
# on a literal U+2011 non-breaking hyphen. That crash happened to hit a
# FILE write first, but nothing stops the identical crash from hitting a
# console print() instead the next time an agent's LLM-generated text
# (a criterion, a Reviewer justification, a test failure detail) contains
# a character outside cp1252 -- which would kill the whole run mid-demo
# with no code artifact ever surviving to disk. Reconfigured here, once,
# at the very top of the entry point, with errors="replace" rather than
# the default "strict": worst case an unprintable character shows as "?"
# on screen, which is recoverable and still lets the run finish and
# persist its files -- a crash is not. `reconfigure()` is a no-op-safe
# TextIOWrapper method (Python 3.7+); wrapped in try/except because a
# redirected/piped stdout in some environments doesn't support it, and
# this must never be the reason the whole program fails to start.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Phase 5: load .env BEFORE any other project import, so SDLC_USE_MOCK,
# GROQ_API_KEY, and the model env vars are actually in os.environ by the
# time llm_client.call_llm() reads them. Nothing in the import chain below
# (graph -> agents -> llm_client) called load_dotenv() itself before this
# — every prior "real mode" test worked because test_groq_connection.py /
# test_call_llm_real.py each called load_dotenv() themselves; running the
# actual graph through main.py without this line silently stayed in mock
# mode regardless of SDLC_USE_MOCK=0 in .env.
from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Command

from graph import _print_run_summary, build_graph
from persistence import save_code_artifacts, save_spec
from report import save_report
from state import RunStatus, new_run_state

DEFAULT_REQUIREMENT = "Write a function that reverses a string."


def prompt_for_approval(payload: dict) -> bool:
    """Show the human what Phase 3's roadmap entry asks for — the
    requirement and every acceptance criterion — and wait for y/n."""
    print("\n" + "=" * 60)
    print("SPEC READY FOR APPROVAL")
    print("=" * 60)
    print(f"Requirement:\n  {payload['requirement']}\n")
    print("Acceptance criteria:")
    for i, criterion in enumerate(payload["acceptance_criteria"], start=1):
        print(f"  {i}. {criterion}")
    print("=" * 60)

    while True:
        answer = input("Approve this spec? [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


def run(requirement: str) -> None:
    run_id = uuid.uuid4().hex[:8]
    graph = build_graph()
    config = {"configurable": {"thread_id": run_id}}

    initial_state = {**new_run_state(run_id), "requirement": requirement}
    result = graph.invoke(initial_state, config)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        approved = prompt_for_approval(payload)
        if not approved:
            print("Rejected — looping back to the Planner...\n")
        result = graph.invoke(Command(resume=approved), config)

    # DECISION (unchanged from Phase 3): the spec is persisted the moment
    # it's approved, regardless of what happens afterward in the
    # Coder/Tester/Reviewer loop — approval and "does the generated code
    # actually satisfy it" are separate concerns. result["spec"] is only
    # ever non-None once a human has said yes to it (planner_node/
    # approval_node never set it otherwise), so this check alone is
    # enough to tell the two FAILED cases apart below (rejected at
    # approval vs. failed after approval).
    if result["spec"] is not None:
        spec_path = save_spec(result["spec"])
        print(f"\nSpec approved and persisted to: {spec_path}")

        # BUG #6: the actual generated code previously existed only in
        # memory for the run's duration -- report.py's inline embedding
        # depends on CodeArtifact.task_id matching a spec task exactly,
        # which silently fails for the Coder's own "prefer one consolidated
        # file" pattern (see persistence.save_code_artifacts()'s docstring
        # for the live run this was found on: DONE, 5/5 passed and
        # approved, and still nothing anyone could actually open and run).
        # Written unconditionally here -- independent of whether the
        # report's linking below succeeds -- so a real .py file always
        # exists on disk after any run that got as far as the Coder.
        code_dir = save_code_artifacts(run_id, result["code_artifacts"])
        if code_dir is not None:
            print(f"Generated code written to: {code_dir}")

        # Phase 7: generate the traceability report the moment the run
        # has reached (or attempted) the code/test/review stage, whether
        # it ends DONE or FAILED there — a FAILED run's report is exactly
        # where the chain-of-custody view is most useful (it shows WHICH
        # criterion never got satisfied and why, not just "it failed").
        report_path = save_report(
            result["spec"],
            result["code_artifacts"],
            result["test_results"],
            result["review_verdicts"],
            final_status=result["status"].value,
            retries=result["retries"],
        )
        print(f"Traceability report written to: {report_path}")

    if result["status"] == RunStatus.DONE:
        print("\nAll acceptance criteria PASSED (real sandboxed execution) and were approved by the Reviewer.")
        _print_run_summary(result)
    elif result["status"] == RunStatus.FAILED:
        if result["spec"] is None:
            retries = result["retries"]
            print(
                f"\nRun failed at spec approval: hit "
                f"{retries.spec_approval_retries}/{retries.max_spec_approval_retries} "
                f"rejections without approval. Nothing was persisted."
            )
        else:
            _print_run_summary(result)
            retries = result["retries"]
            print(
                f"\nRun failed: test_review_retries hit "
                f"{retries.test_review_retries}/{retries.max_test_review_retries} "
                f"without every criterion passing and being approved."
            )
    else:
        # Shouldn't happen — the graph only ends on DONE or FAILED — but
        # fail loudly rather than silently if it ever does.
        raise RuntimeError(f"graph ended in unexpected status: {result['status']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one requirement through the full SDLC pipeline.")
    parser.add_argument(
        "--requirement",
        default=DEFAULT_REQUIREMENT,
        help="Plain-English requirement to plan for.",
    )
    args = parser.parse_args()
    run(args.requirement)
