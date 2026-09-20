"""
test_report.py — Phase 7 verification.

Per the roadmap's Phase 7 "done when": someone reading one generated
report should follow requirement -> criterion -> task -> code -> test ->
verdict UNAIDED. This test builds a small fixture with two criteria — one
that made it all the way through DONE, and one deliberately left with a
gap (no matching task) — and asserts the rendered markdown actually
contains every link in the chain for the complete criterion, and clearly
marks the gap for the incomplete one rather than silently dropping it.

Run:
    python3 test_report.py
"""

from report import generate_traceability_report
from state import (
    AcceptanceCriterion,
    CodeArtifact,
    PerCriterionResult,
    ReviewVerdict,
    Spec,
    TaskItem,
)

SPEC = Spec(
    run_id="report-fixture",
    requirement="Write a function that reverses a string.",
    acceptance_criteria=[
        AcceptanceCriterion(id="AC1", text="reverse('abc') == 'cba'"),
        AcceptanceCriterion(id="AC2", text="reverse('') == ''"),
    ],
    tasks=[TaskItem(id="T1", description="Implement reverse()", addresses_criteria=["AC1"])],
    # NOTE: AC2 deliberately has no task addressing it, to prove the
    # report shows that gap instead of hiding it.
)

ARTIFACTS = [CodeArtifact(filename="solution.py", content="def reverse(s):\n    return s[::-1]\n", task_id="T1")]

TEST_RESULTS = [
    PerCriterionResult(criterion_id="AC1", passed=True, detail="PASS (real sandboxed execution, exit 0)."),
    # AC2 never reached the Tester in this fixture (simulating a run that
    # failed before every criterion got tested).
]

VERDICTS = [
    ReviewVerdict(criterion_id="AC1", approved=True, justification="Test result shows AC1 passed."),
]


def check(label: str, fn):
    try:
        fn()
        print(f"[ OK ] {label}")
    except AssertionError as e:
        print(f"[FAIL] {label}: {e}")
        raise


def report_follows_the_full_chain_for_a_complete_criterion():
    md = generate_traceability_report(SPEC, ARTIFACTS, TEST_RESULTS, VERDICTS, final_status="failed")

    ac1_section = md.split("## AC2")[0]  # everything before AC2's section
    assert "## AC1: reverse('abc') == 'cba'" in ac1_section
    assert "`T1` — Implement reverse()" in ac1_section
    assert "def reverse(s):" in ac1_section
    assert "**PASS**" in ac1_section
    assert "**APPROVED**" in ac1_section


check(
    "AC1's section shows requirement -> task -> code -> test -> verdict, unaided",
    report_follows_the_full_chain_for_a_complete_criterion,
)


def report_shows_gaps_instead_of_hiding_them():
    md = generate_traceability_report(SPEC, ARTIFACTS, TEST_RESULTS, VERDICTS, final_status="failed")

    ac2_section = md.split("## AC2")[1]
    assert "(none — no task in the spec named this criterion)" in ac2_section
    # BUG #6 fix (see report.py + persistence.py): the report used to say
    # "no code artifact was linked to this criterion's task(s)" here even
    # when real code existed elsewhere in the run, which reads as "nothing
    # was built" when the actual situation is "nothing was PLANNED for
    # this criterion" -- a materially different, more useful statement.
    # AC2 has no addressing task at all (see SPEC's note above), so it
    # must NOT fall back to showing ARTIFACTS (that fallback is reserved
    # for a criterion that DOES have a task but whose code's task_id
    # didn't match it) -- this assertion is what proves that distinction.
    assert "(none — no task in the spec named this criterion, so no code was written for it)" in ac2_section
    assert "def reverse(s):" not in ac2_section, (
        "AC2 has no task at all -- it must not fall back to showing AC1's unrelated code"
    )
    assert "(none — this criterion was never reached by the Tester)" in ac2_section
    assert "(none — this criterion was never reached by the Reviewer)" in ac2_section


check(
    "AC2's incomplete chain is shown explicitly as gaps, not silently dropped",
    report_shows_gaps_instead_of_hiding_them,
)


# ---------------------------------------------------------------------------
# A real FAILED-run report, generated from an actual graph run (not a hand-
# built fixture) — closes the gap PHASE_7_PROGRESS_AND_DECISIONS.md flagged:
# "no FAILED-run report has actually been read, only reasoned through and
# unit-tested via fixture." This uses the same persistent-forced-failure
# hook test_full_loop.py's third case already relies on (force every
# attempt to fail AC1, hit max_test_review_retries), then runs it through
# save_report() for real and reads the actual file back.
# ---------------------------------------------------------------------------

from langgraph.types import Command  # noqa: E402

from graph import build_graph  # noqa: E402
from report import save_report  # noqa: E402
from state import RunStatus, new_run_state  # noqa: E402


def a_real_failed_run_produces_a_report_that_names_where_the_chain_broke():
    graph = build_graph()
    run_id = "test-report-failed-run"
    config = {"configurable": {"thread_id": run_id}}
    initial_state = {
        **new_run_state(run_id),
        "requirement": "Write a function that reverses a string.",
        "force_tester_fail_criteria": ["AC1"],
        "force_tester_fail_attempts": 999,  # forces failure on every attempt
    }

    result = graph.invoke(initial_state, config)
    assert "__interrupt__" in result
    result = graph.invoke(Command(resume=True), config)

    assert result["status"] == RunStatus.FAILED, "this run is designed to hit the retry cap"
    assert result["spec"] is not None, "the spec itself was still approved — only the loop failed"

    report_path = save_report(
        result["spec"],
        result["code_artifacts"],
        result["test_results"],
        result["review_verdicts"],
        final_status=result["status"].value,
        retries=result["retries"],
    )
    markdown = report_path.read_text(encoding="utf-8")

    assert "**Final status:** failed" in markdown
    # This run is designed to hit max_test_review_retries (5, raised from
    # 3 — see state.py's RetryCounters docstring) — the report must say so
    # explicitly, not just leave it to a console log someone has to have
    # kept. See PHASE_7_PROGRESS_AND_DECISIONS.md's "Live-mode report
    # generated" finding for the real run that showed why this matters: a
    # report with no retry count can't be told apart from a first-try
    # clean pass.
    assert "**Retries spent:** spec_approval=0/3, test_review=5/5" in markdown, (
        f"expected the retry tally in the report header, got:\n{markdown[:400]}"
    )
    # AC1 was forced to fail on every attempt — the report must show the
    # REAL forced-failure detail text, not a vague "something failed", and
    # must show AC2 (which never had a chance to fail) as genuinely passing
    # — proving the report distinguishes the two, not a blanket "failed".
    assert "## AC1:" in markdown and "## AC2:" in markdown
    ac1_section = markdown.split("## AC2")[0]
    ac2_section = markdown.split("## AC2")[1]
    assert "**FAIL**" in ac1_section, f"AC1 must show as FAIL:\n{ac1_section}"
    assert "**PASS**" in ac2_section, f"AC2 must show as PASS (never forced to fail):\n{ac2_section}"
    print(f"  (real FAILED report written to {report_path} — read it yourself to double-check)")


check(
    "a real FAILED run's report clearly shows which criterion broke the chain "
    "and which one didn't, not a blanket failure",
    a_real_failed_run_produces_a_report_that_names_where_the_chain_broke,
)

def a_consolidated_files_code_still_shows_up_even_with_a_task_id_mismatch():
    # BUG #6's actual live scenario: a task DOES address the criterion,
    # but the Coder's single consolidated file's task_id doesn't happen to
    # match it (the direct consequence of run_coder()'s own prompt saying
    # "prefer ONE consolidated file... even if multiple tasks address
    # it" -- see persistence.save_code_artifacts()'s docstring). The
    # report must still show the actual code, not silently claim none
    # exists, since a real passing test result is sitting right there
    # proving the code does the job.
    spec = Spec(
        run_id="bug6-fallback",
        requirement="Write a ShoppingCart class.",
        acceptance_criteria=[AcceptanceCriterion(id="AC1", text="add_item stores an item.")],
        tasks=[TaskItem(id="T2", description="Implement add_item", addresses_criteria=["AC1"])],
    )
    # Deliberately mismatched: the artifact claims task_id="T1", but the
    # spec's only task addressing AC1 is "T2" -- exactly what a
    # consolidated-file Coder response looks like when it tags the file
    # with a different task than the one this criterion cares about.
    artifacts = [
        CodeArtifact(
            filename="cart.py",
            content="class ShoppingCart:\n    def add_item(self, name, price, qty):\n        pass\n",
            task_id="T1",
        )
    ]
    test_results = [
        PerCriterionResult(criterion_id="AC1", passed=True, detail="PASS (real sandboxed execution, exit 0)."),
    ]
    verdicts = [ReviewVerdict(criterion_id="AC1", approved=True, justification="add_item test passed.")]

    md = generate_traceability_report(spec, artifacts, test_results, verdicts, final_status="done")

    assert "class ShoppingCart:" in md, (
        "the code exists and its test passed -- the report must show it, "
        "not claim '(none — no code artifact was linked)' the way the live "
        "bug did on a genuine DONE run"
    )
    assert "no code artifact's task_id matched" in md, (
        "the fallback should be labeled as a fallback, not presented as a normal exact match"
    )


check(
    "a criterion whose task exists but whose code's task_id doesn't match still shows the real code (BUG #6)",
    a_consolidated_files_code_still_shows_up_even_with_a_task_id_mismatch,
)


print("\nAll Phase 7 report checks passed.")
