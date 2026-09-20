"""
test_planner.py — Phase 2 verification.

Same discipline as Phase 1's test_state.py: prove the happy path AND prove
specific failure modes are actually caught, not just "it ran once and
looked fine." Per EVALUATION_AND_ROADMAP.md's Phase 2 "done when": three
isolated Planner runs produce three valid, persisted spec files, and at
least one deliberately-broken mock response gets caught with a clear error.
This file does that with 2 valid + 3 deliberately-broken fixtures — a
little past the minimum, because there are three distinct ways a Planner
response can be broken (bad JSON, a schema violation, a bad cross-reference)
and each deserves its own proof, not just "some malformed input, somehow
rejected."

Run:
    cd src
    python3 test_planner.py
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from agents import PlannerOutputError, run_planner
from persistence import save_spec


def check(label: str, fn):
    try:
        fn()
        print(f"[ OK ] {label}")
    except AssertionError as e:
        print(f"[FAIL] {label}: {e}")
        raise


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_REVERSE_STRING = """{
  "requirement": "Write a function that reverses a string.",
  "acceptance_criteria": [
    {"text": "reverse('abc') == 'cba'"},
    {"text": "reverse('') == ''"}
  ],
  "tasks": [
    {"id": "T1", "description": "Implement reverse()", "addresses_criteria": [0, 1]}
  ]
}"""

VALID_IS_PRIME = """{
  "requirement": "Write a function that checks if a number is prime.",
  "acceptance_criteria": [
    {"text": "is_prime(2) == True"},
    {"text": "is_prime(4) == False"},
    {"text": "is_prime(1) == False"}
  ],
  "tasks": [
    {"id": "T1", "description": "Implement is_prime()", "addresses_criteria": [0, 1, 2]},
    {"id": "T2", "description": "Add input-validation for negative numbers", "addresses_criteria": []}
  ]
}"""

# Broken mode 1: not valid JSON at all (truncated / malformed syntax).
BROKEN_NOT_JSON = """{
  "requirement": "Write a function that sums a list.",
  "acceptance_criteria": [
    {"text": "sum_list([1,2,3]) == 6"},
""" # deliberately unterminated

# Broken mode 2: valid JSON, but violates the schema (zero acceptance
# criteria — Spec.acceptance_criteria has min_length=1).
BROKEN_EMPTY_CRITERIA = """{
  "requirement": "Write a function that does something.",
  "acceptance_criteria": [],
  "tasks": []
}"""

# Broken mode 3: valid JSON, individually-valid criteria/tasks, but a task
# references a criterion index that doesn't exist (only 2 criteria, index 5
# doesn't exist). This is the failure mode specific to the index->id
# remapping run_planner() does itself, not caught by Pydantic at all.
BROKEN_BAD_INDEX = """{
  "requirement": "Write a function that multiplies two numbers.",
  "acceptance_criteria": [
    {"text": "multiply(2, 3) == 6"},
    {"text": "multiply(0, 5) == 0"}
  ],
  "tasks": [
    {"id": "T1", "description": "Implement multiply()", "addresses_criteria": [0, 5]}
  ]
}"""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def valid_response_produces_persisted_spec():
    tmp = Path(tempfile.mkdtemp())
    try:
        spec = run_planner("run-A", "unused", mock_response=VALID_REVERSE_STRING)
        assert spec.run_id == "run-A"
        assert [c.id for c in spec.acceptance_criteria] == ["AC1", "AC2"]
        assert spec.tasks[0].addresses_criteria == ["AC1", "AC2"]

        path = save_spec(spec, data_dir=tmp)
        assert path.exists()
        assert path.name == "spec_run-A.json"
        assert "reverse" in path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(tmp)


check("valid response -> validated Spec -> persisted spec_run-A.json", valid_response_produces_persisted_spec)


def second_valid_response_is_independent():
    tmp = Path(tempfile.mkdtemp())
    try:
        spec = run_planner("run-B", "unused", mock_response=VALID_IS_PRIME)
        assert spec.run_id == "run-B"
        assert len(spec.acceptance_criteria) == 3
        assert [c.id for c in spec.acceptance_criteria] == ["AC1", "AC2", "AC3"]
        # T2's addresses_criteria is legitimately empty (scaffolding task).
        assert spec.tasks[1].addresses_criteria == []

        path = save_spec(spec, data_dir=tmp)
        assert path.name == "spec_run-B.json"
    finally:
        shutil.rmtree(tmp)


check("second, differently-shaped valid response also persists correctly", second_valid_response_is_independent)


def not_json_is_rejected_with_raw_response_attached():
    try:
        run_planner("run-C", "unused", mock_response=BROKEN_NOT_JSON)
    except PlannerOutputError as e:
        assert "JSON" in str(e)
        assert e.raw_response == BROKEN_NOT_JSON
        return
    raise AssertionError("expected PlannerOutputError for non-JSON response")


check("malformed JSON is rejected, not silently swallowed", not_json_is_rejected_with_raw_response_attached)


def empty_criteria_is_rejected_by_schema():
    try:
        run_planner("run-D", "unused", mock_response=BROKEN_EMPTY_CRITERIA)
    except PlannerOutputError as e:
        assert e.errors, "expected structured Pydantic errors to be attached"
        assert e.errors[0]["type"] == "too_short"
        return
    raise AssertionError("expected PlannerOutputError for zero acceptance criteria")


check("zero acceptance criteria is rejected by the Spec schema (min_length=1)", empty_criteria_is_rejected_by_schema)


def out_of_range_criterion_index_is_rejected():
    try:
        run_planner("run-E", "unused", mock_response=BROKEN_BAD_INDEX)
    except PlannerOutputError as e:
        assert "index" in str(e)
        assert "5" in str(e)
        return
    raise AssertionError("expected PlannerOutputError for out-of-range criterion index")


check(
    "task referencing a criterion index that doesn't exist is rejected "
    "(not caught by Pydantic — this is run_planner()'s own check)",
    out_of_range_criterion_index_is_rejected,
)


def three_valid_runs_persist_three_distinct_files():
    tmp = Path(tempfile.mkdtemp())
    try:
        for i, (rid, resp) in enumerate(
            [("run-1", VALID_REVERSE_STRING), ("run-2", VALID_IS_PRIME), ("run-3", VALID_REVERSE_STRING)]
        ):
            spec = run_planner(rid, "unused", mock_response=resp)
            save_spec(spec, data_dir=tmp)
        files = sorted(p.name for p in tmp.glob("spec_*.json"))
        assert files == ["spec_run-1.json", "spec_run-2.json", "spec_run-3.json"], files
    finally:
        shutil.rmtree(tmp)


check(
    "three isolated Planner runs produce three distinct persisted spec files "
    "(Phase 2's literal 'done when')",
    three_valid_runs_persist_three_distinct_files,
)


print("\nAll Phase 2 Planner checks passed.")
