"""
test_real_tester.py — Phase 6 verification.

Same discipline as test_state.py / test_planner.py / test_full_loop.py:
prove the real, load-bearing behavior programmatically, not just eyeball
one console run. Specifically proves the roadmap's literal Phase 6 "done
when": generated code genuinely fails a SPECIFIC criterion, the Tester
names that criterion precisely (not "something failed"), and it does so
via REAL execution (a real subprocess, a real exit code, real captured
output) — not an LLM's opinion and not the Phase 4 stub.

Deliberately uses call_llm()'s `mock_response` injection (same mechanism
test_planner.py already uses for the Planner) rather than a live Groq
call: the thing Phase 6 needs to prove is that the SANDBOX genuinely
differentiates pass/fail from real execution, which is true whether the
test_code string came from a live LLM or a fixture — a live call adds
Phase 5's own reliability variance (rate limits, occasional invalid JSON)
without adding anything to what THIS phase is responsible for proving.

Run:
    python3 test_real_tester.py
"""

import json
import os

from agents import CoderOutputError, TesterOutputError, _strip_code_fence, run_coder, run_tester_real
from state import AcceptanceCriterion, CodeArtifact, Spec

REQUIREMENT = "Write an add(a, b) function; reject negative inputs."

SPEC = Spec(
    run_id="test-real-tester",
    requirement=REQUIREMENT,
    acceptance_criteria=[
        AcceptanceCriterion(id="AC1", text="add(2, 3) == 5"),
        AcceptanceCriterion(id="AC2", text="add(-1, 2) raises ValueError"),
        AcceptanceCriterion(id="AC3", text="add() terminates promptly (no infinite loop)"),
    ],
)

# Deliberately-incomplete implementation: handles AC1, does NOT reject
# negative inputs (so AC2 must genuinely fail), has nothing to do with an
# infinite loop itself (AC3's test below manufactures one on purpose, to
# prove the sandbox's timeout kills it rather than hanging the suite).
CODE_ARTIFACT = CodeArtifact(
    filename="solution.py",
    content="def add(a, b):\n    return a + b\n",
    task_id="T1",
)

TESTER_MOCK_RESPONSE = """{
  "tests": [
    {
      "criterion_id": "AC1",
      "test_code": "from solution import add\\nassert add(2, 3) == 5\\n"
    },
    {
      "criterion_id": "AC2",
      "test_code": "from solution import add\\ntry:\\n    add(-1, 2)\\nexcept ValueError:\\n    pass\\nelse:\\n    raise AssertionError('expected ValueError for negative input, none was raised')\\n"
    },
    {
      "criterion_id": "AC3",
      "test_code": "while True:\\n    pass\\n"
    }
  ]
}"""


def check(label: str, fn):
    try:
        fn()
        print(f"[ OK ] {label}")
    except AssertionError as e:
        print(f"[FAIL] {label}: {e}")
        raise


def real_execution_differentiates_pass_and_genuine_failure():
    os.environ["SDLC_USE_MOCK"] = "1"  # never touch Groq for this test
    os.environ["SDLC_TEST_TIMEOUT_SECONDS"] = "2"  # keep the AC3 timeout case fast

    results = run_tester_real(
        "test-real-tester", SPEC, [CODE_ARTIFACT], mock_response=TESTER_MOCK_RESPONSE
    )
    by_id = {r.criterion_id: r for r in results}

    assert len(results) == 3, f"expected one PerCriterionResult per criterion, got {len(results)}"

    # AC1: genuinely correct code, genuinely passes.
    assert by_id["AC1"].passed is True, f"AC1 should have passed (real exit 0): {by_id['AC1'].detail}"

    # AC2: genuinely missing behavior -> genuine failure, named precisely
    # (not "something failed") via the real AssertionError text captured
    # from real stderr.
    assert by_id["AC2"].passed is False, "AC2 should have failed — add() never rejects negative input"
    assert "ValueError" in by_id["AC2"].detail or "negative" in by_id["AC2"].detail, (
        f"AC2's detail should name the specific reason it failed, got: {by_id['AC2'].detail!r}"
    )

    # AC3: an infinite loop must be killed by the sandbox's timeout, not
    # hang this test suite or crash the Tester — proves the timeout safety
    # net is real, not just reasoned-through.
    assert by_id["AC3"].passed is False, "AC3's infinite loop must be caught as a failure, not hang or pass"
    assert "timeout" in by_id["AC3"].detail.lower() or "timed out" in by_id["AC3"].detail.lower(), (
        f"AC3's detail should say it was killed by the timeout, got: {by_id['AC3'].detail!r}"
    )


check(
    "real sandboxed execution differentiates a genuine pass, a genuine failure "
    "(named precisely), and a timeout-killed infinite loop",
    real_execution_differentiates_pass_and_genuine_failure,
)


def no_code_artifacts_fails_every_criterion_without_calling_the_llm():
    # Same honest, non-LLM rule the Phase 4 stub applies — proven here so
    # a future change to run_tester_real() can't quietly start calling the
    # Tester LLM (and burning a real API call) for a Coder failure that
    # already produced zero artifacts.
    results = run_tester_real("test-no-code", SPEC, [])
    assert len(results) == 3
    assert all(not r.passed for r in results)
    assert all("no code artifacts" in r.detail.lower() for r in results)


check(
    "zero code artifacts fails every criterion honestly, without generating tests for nothing",
    no_code_artifacts_fails_every_criterion_without_calling_the_llm,
)


# ---------------------------------------------------------------------------
# Stress test: exotic generated-code failure shapes, exercised directly
# against sandbox.py (below the Tester-LLM layer) so each shape is isolated
# — a real Groq call could ALSO produce any of these, but proving the
# sandbox handles them doesn't require paying for that variance. This is
# the "hardest phase" edge-case coverage flagged as thin in
# PHASE_6_PROGRESS_AND_DECISIONS.md — not exhaustive, but the three shapes
# most likely to actually occur from free-tier LLM output: a bad import, a
# syntax error, and a crash partway through doing real work.
# ---------------------------------------------------------------------------

import sandbox  # noqa: E402  (kept near its first use, matching this file's existing import style)


def exotic_failure_shapes_are_caught_cleanly_not_hung_or_crashed():
    # Shape 1: import error — references a module that doesn't exist.
    # Common when an LLM hallucinates a third-party dependency.
    outcome = sandbox.run_sandboxed(
        {"test_import_error.py": "import totally_fake_module_xyz_123\n"},
        entry_file="test_import_error.py",
    )
    assert outcome.returncode != 0, "a missing import must be a real failure, not silently pass"
    assert not outcome.timed_out
    assert "ModuleNotFoundError" in outcome.stderr or "ImportError" in outcome.stderr, (
        f"expected a real import error in stderr, got: {outcome.stderr!r}"
    )

    # Shape 2: syntax error — the LLM produced text that isn't valid Python
    # at all. The interpreter itself must reject it cleanly, not hang the
    # sandbox trying to run something that can't even parse.
    outcome = sandbox.run_sandboxed(
        {"test_syntax_error.py": "def broken(:\n    pass\n"},
        entry_file="test_syntax_error.py",
    )
    assert outcome.returncode != 0, "invalid syntax must be a real failure"
    assert not outcome.timed_out
    assert "SyntaxError" in outcome.stderr, f"expected SyntaxError in stderr, got: {outcome.stderr!r}"

    # Shape 3: partial output before an uncaught crash — proves BOTH
    # streams are captured independently and neither is lost: the prints
    # that happened before the crash should still be in stdout, and the
    # traceback should still be in stderr, so a human reading
    # PerCriterionResult.detail sees what actually happened, not just
    # "it crashed."
    outcome = sandbox.run_sandboxed(
        {
            "test_partial_crash.py": (
                "print('step 1 ok')\nprint('step 2 ok')\nraise RuntimeError('boom at step 3')\n"
            )
        },
        entry_file="test_partial_crash.py",
    )
    assert outcome.returncode != 0
    assert not outcome.timed_out
    assert "step 1 ok" in outcome.stdout and "step 2 ok" in outcome.stdout, (
        f"partial stdout before the crash must not be lost, got: {outcome.stdout!r}"
    )
    assert "RuntimeError" in outcome.stderr and "boom at step 3" in outcome.stderr, (
        f"the real traceback must be captured, got: {outcome.stderr!r}"
    )


check(
    "an import error, a syntax error, and a partial-output-then-crash are each "
    "caught cleanly with real diagnostic detail, none hangs or crashes the sandbox itself",
    exotic_failure_shapes_are_caught_cleanly_not_hung_or_crashed,
)


# ---------------------------------------------------------------------------
# Windows fallback path: this dev environment is Linux, and the real
# target machine is Windows, where resource.setrlimit doesn't exist (see
# sandbox.py's module docstring). This can't be verified on an actual
# Windows interpreter from here, but the CODE PATH Windows takes — skip
# the POSIX preexec_fn entirely, rely on the timeout alone — CAN be
# exercised for real by forcing sandbox._is_posix() to report False, which
# is exactly the branch condition Windows would hit. This proves that
# branch runs correctly end to end (still differentiates a real pass from
# a real failure), not just that it's syntactically present.
# ---------------------------------------------------------------------------


def windows_fallback_branch_still_differentiates_pass_and_fail():
    original_is_posix = sandbox._is_posix
    sandbox._is_posix = lambda: False  # simulate the Windows branch condition
    try:
        passing = sandbox.run_sandboxed(
            {"test_pass.py": "assert 1 + 1 == 2\n"}, entry_file="test_pass.py"
        )
        failing = sandbox.run_sandboxed(
            {"test_fail.py": "assert 1 + 1 == 3, 'math is broken'\n"}, entry_file="test_fail.py"
        )
    finally:
        sandbox._is_posix = original_is_posix  # never leak the patch to other tests

    assert passing.returncode == 0 and not passing.timed_out, (
        "a genuinely passing test must still pass with rlimits skipped (Windows-like path)"
    )
    assert failing.returncode != 0 and "math is broken" in failing.stderr, (
        f"a genuinely failing test must still fail with a real reason, got: {failing.stderr!r}"
    )


check(
    "the non-POSIX (Windows) fallback branch — rlimits skipped, timeout-only — "
    "still correctly differentiates a real pass from a real failure",
    windows_fallback_branch_still_differentiates_pass_and_fail,
)

# ---------------------------------------------------------------------------
# Regression test for a REAL bug found on a live Groq run (see
# PHASE_6_PROGRESS_AND_DECISIONS.md): a model can return structurally
# valid JSON whose string content is still broken Python, because it
# double-escaped newlines (JSON containing a literal backslash-backslash-n
# instead of backslash-n). That passes json.loads() and Pydantic
# validation cleanly — the bug can ONLY be caught by actually trying to
# parse the resulting string as Python. These checks build that exact
# bug on purpose (via json.dumps of a string that ALREADY contains a
# literal backslash+n, which forces json.dumps to escape the backslash a
# second time — precisely reproducing what a double-escaping model
# produces on the wire) and confirm both run_coder() and run_tester_real()
# catch it BEFORE ever reaching the sandbox, with a specific, actionable
# error rather than a generic import-time SyntaxError discovered five
# criteria too late.
# ---------------------------------------------------------------------------

# This is a Python string that ALREADY contains literal backslash+n
# characters (not real newlines) — exactly what a double-escaping model's
# decoded JSON produces. json.dumps() below will then escape each of
# those literal backslashes AGAIN, producing raw JSON text with two
# backslashes before every 'n' — the exact bug signature seen live.
_DOUBLE_ESCAPED_CONTENT = "class Broken:\\n    def __init__(self):\\n        pass\\n"


def run_coder_rejects_double_escaped_newlines_before_the_sandbox():
    bad_mock_response = json.dumps(
        {"artifacts": [{"filename": "broken.py", "content": _DOUBLE_ESCAPED_CONTENT, "task_id": "T1"}]}
    )
    try:
        run_coder("test-double-escape", SPEC, mock_response=bad_mock_response)
    except CoderOutputError as e:
        assert "not valid Python" in str(e), f"expected a specific syntax-error message, got: {e}"
        assert "double-escaped" in str(e) or "backslash" in str(e), (
            f"expected the error to name the likely cause, got: {e}"
        )
        return
    raise AssertionError("expected run_coder() to reject double-escaped-newline content as CoderOutputError")


check(
    "run_coder() catches double-escaped-newline content itself, before ever handing "
    "broken code to the Tester/sandbox",
    run_coder_rejects_double_escaped_newlines_before_the_sandbox,
)


def run_tester_real_rejects_its_own_double_escaped_test_code():
    bad_tester_response = json.dumps(
        {
            "tests": [
                {"criterion_id": "AC1", "test_code": _DOUBLE_ESCAPED_CONTENT},
                {"criterion_id": "AC2", "test_code": "assert True\n"},
                {"criterion_id": "AC3", "test_code": "assert True\n"},
            ]
        }
    )
    try:
        run_tester_real(
            "test-double-escape", SPEC, [CODE_ARTIFACT], mock_response=bad_tester_response
        )
    except TesterOutputError as e:
        assert "not valid Python" in str(e), f"expected a specific syntax-error message, got: {e}"
        assert "Tester's own generated test" in str(e) or "not necessarily in the code under test" in str(e), (
            f"expected the error to correctly attribute the defect to the Tester's own "
            f"generated test, not the code under test: {e}"
        )
        return
    raise AssertionError(
        "expected run_tester_real() to reject its own double-escaped test_code as TesterOutputError"
    )


check(
    "run_tester_real() catches a double-escaped test script it generated itself, and "
    "correctly attributes the defect to the Tester, not the code under test",
    run_tester_real_rejects_its_own_double_escaped_test_code,
)

# ---------------------------------------------------------------------------
# Defensive fence-stripping: since Coder/Tester no longer get Groq's
# response_format=json_object structural nudge (see llm_client.py's
# _ROLES_WITHOUT_JSON_MODE — dropped after it caused opaque, undebuggable
# rejections on large code payloads), a stray ```json fence despite the
# prompt's explicit "no markdown code fences" instruction is more likely.
# Confirms run_coder() still works when the model wraps its JSON anyway.
# ---------------------------------------------------------------------------


def run_coder_tolerates_a_stray_markdown_fence():
    payload = json.dumps({"artifacts": [{"filename": "ok.py", "content": "x = 1\n", "task_id": "T1"}]})
    fenced = f"```json\n{payload}\n```"
    artifacts = run_coder("test-fence", SPEC, mock_response=fenced)
    assert len(artifacts) == 1 and artifacts[0].filename == "ok.py", (
        "run_coder() should tolerate a fenced response exactly like an unfenced one"
    )


check(
    "run_coder() strips a stray ```json fence instead of failing on it",
    run_coder_tolerates_a_stray_markdown_fence,
)


def strip_code_fence_is_a_no_op_on_already_clean_json():
    clean = '{"a": 1}'
    assert _strip_code_fence(clean) == clean, "must not alter unfenced input at all"


check(
    "_strip_code_fence() is a no-op on already-clean JSON (no regression risk to existing fixtures)",
    strip_code_fence_is_a_no_op_on_already_clean_json,
)

print("\nAll Phase 6 real-Tester checks passed.")
