"""
Phase 1 verification — prove state.py's shapes behave as designed BEFORE any
agent code depends on them. Same "feed it good data, then feed it
deliberately broken data" discipline as the Phase 0 Pydantic exercise, now
applied to the real schemas.

Run:
    source venv/bin/activate
    python3 test_state.py
"""

from pydantic import ValidationError

from state import (
    AcceptanceCriterion,
    CodeArtifact,
    PerCriterionResult,
    ReviewVerdict,
    Spec,
    TaskItem,
    new_run_state,
)


def check(label: str, fn):
    try:
        fn()
        print(f"[ OK ] {label}")
    except AssertionError as e:
        print(f"[FAIL] {label}: {e}")
        raise


def valid_spec_builds():
    spec = Spec(
        run_id="run-001",
        requirement="Write a function that reverses a string.",
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", text="reverse('abc') == 'cba'"),
            AcceptanceCriterion(id="AC2", text="reverse('') == ''"),
        ],
        tasks=[
            TaskItem(id="T1", description="Implement reverse()", addresses_criteria=["AC1", "AC2"]),
        ],
    )
    assert spec.acceptance_criteria_text == ["reverse('abc') == 'cba'", "reverse('') == ''"]
    assert spec.tasks[0].addresses_criteria == ["AC1", "AC2"]
    dumped = spec.model_dump_json()
    reloaded = Spec.model_validate_json(dumped)
    assert reloaded == spec


check("valid Spec builds, and round-trips through JSON", valid_spec_builds)


def empty_criteria_rejected():
    try:
        Spec(run_id="run-002", requirement="Do something.", acceptance_criteria=[])
    except ValidationError as e:
        assert e.error_count() == 1
        assert e.errors()[0]["type"] == "too_short"
        return
    raise AssertionError("expected ValidationError for empty acceptance_criteria")


check("Spec with empty acceptance_criteria is rejected", empty_criteria_rejected)


def blank_fields_rejected():
    for factory, label in [
        (lambda: AcceptanceCriterion(id="AC1", text="   "), "AcceptanceCriterion.text"),
        (lambda: TaskItem(id="T1", description=""), "TaskItem.description"),
        (lambda: ReviewVerdict(criterion_id="AC1", approved=True, justification=""), "ReviewVerdict.justification"),
    ]:
        try:
            factory()
        except ValidationError:
            continue
        raise AssertionError(f"expected ValidationError for blank {label}")


check("blank required text fields are rejected", blank_fields_rejected)


def path_traversal_filename_rejected():
    try:
        CodeArtifact(filename="../../evil.py", content="print(1)")
    except ValidationError:
        return
    raise AssertionError("expected ValidationError for path-separator filename")


check("CodeArtifact rejects filenames containing path separators", path_traversal_filename_rejected)


def failing_result_requires_detail():
    PerCriterionResult(criterion_id="AC1", passed=True, detail="")
    try:
        PerCriterionResult(criterion_id="AC1", passed=False, detail="")
    except ValidationError:
        return
    raise AssertionError("expected ValidationError for failing result with blank detail")


check("PerCriterionResult forces an explanation when passed=False", failing_result_requires_detail)


def fresh_state_shape():
    state = new_run_state("run-003")
    assert state["run_id"] == "run-003"
    assert state["spec"] is None
    assert state["code_artifacts"] == []
    assert state["retries"].test_review_retries == 0
    assert state["retries"].max_test_review_retries == 5  # raised from 3 — see state.py's RetryCounters docstring
    assert state["backlog"] == []
    assert state["completed_increments"] == []
    assert state["sprint_number"] == 0
    assert state["status"].value == "in_progress"


check("new_run_state() produces correct defaults, Agile fields present but empty", fresh_state_shape)


print("\nAll Phase 1 schema checks passed.")