"""
llm_client.py — Phase 2: mock-mode call_llm(). Phase 4 adds Coder/Reviewer
default mock responses below (Phase 4's Tester was a rule-based stub with
no LLM behind it at all). Phase 5 adds the real Groq branch and its own
rate-limit backoff (see call_llm()'s docstring and _call_groq_real() below)
— mock mode's behavior is unchanged. Phase 6 adds the Tester as a REAL
caller of this function for the first time — see _MODEL_ENV_BY_ROLE and
_DEFAULT_MOCK_RESPONSES["tester"] below — since the real sandboxed Tester
(agents.py's run_tester_real) needs the LLM to generate per-criterion test
code before anything can be executed.

Every agent calls this one function regardless of what's behind it. The
point of introducing this file in Phase 2, even though it only had a mock
mode then, is that agents.py never needs to change its calling convention
now that Phase 5 flips the mode: only the inside of call_llm() changes.

Mode is controlled by SDLC_USE_MOCK (default "1" — mock). This mirrors the
env-var pattern PROJECT_BRIEF.md already commits to for model IDs
(SDLC_ORCHESTRATOR_MODEL / SDLC_WORKER_MODEL) — config lives in the
environment, not hardcoded in agent code.
"""

from __future__ import annotations

import os
import random
import time

from groq import APIConnectionError, APITimeoutError, Groq, GroqError, RateLimitError


class LLMCallError(Exception):
    """Raised when the call itself can't happen — GROQ_API_KEY/model env var
    missing, an unrecoverable Groq error, or the rate-limit retry budget
    below exhausted. NOT for a response that comes back but fails
    JSON/schema validation — that's the calling agent's job to catch on the
    text this function returns, not this function's job to pre-judge.
    """


# Generic canned replies, keyed by agent_role, for ad-hoc manual testing
# without passing an explicit mock_response. Real test coverage (Phase 2's,
# Phase 4's, and Phase 6's "done when") uses explicit fixtures in
# test_planner.py / test_full_loop.py / test_real_tester.py instead of
# these — these defaults exist so `call_llm("planner", prompt)` returns
# *something* sane if you're poking at this interactively.
#
# DECISION (Phase 4): the "coder" and "reviewer" defaults below are keyed
# to the SAME canned "planner" requirement (reverse a string, AC1/AC2, T1)
# so that running the whole pipeline with no explicit mock_response
# anywhere still produces a coherent end-to-end trace, not three agents
# each hallucinating an unrelated task. Like the "planner" default, these
# ignore the actual prompt content (mock mode doesn't read it) — see the
# call_llm() docstring below for why that's expected, not a bug, until
# Phase 5.
#
# DECISION (Phase 6): the "tester" default below is ALSO wired to the same
# reverse-string scenario, and — unlike the coder/reviewer defaults, which
# can afford to be static text mock mode never inspects — its two test
# scripts are genuinely correct, runnable Python against the "coder"
# default's actual solution.py, because run_tester_real() really executes
# whatever call_llm() returns in a sandbox. A static/lazy default here
# would either always "pass" (defeating the point of proving real
# execution) or crash the demo pipeline in mock mode for a reason that has
# nothing to do with the code under test.
_DEFAULT_MOCK_RESPONSES: dict[str, str] = {
    "planner": """{
  "requirement": "Write a function that reverses a string.",
  "acceptance_criteria": [
    {"text": "reverse('abc') == 'cba'"},
    {"text": "reverse('') == ''"}
  ],
  "tasks": [
    {"id": "T1", "description": "Implement reverse()", "addresses_criteria": [0, 1]}
  ]
}""",
    "coder": """{
  "artifacts": [
    {
      "filename": "solution.py",
      "content": "def reverse(s):\\n    return s[::-1]\\n",
      "task_id": "T1"
    }
  ]
}""",
    "tester": """{
  "tests": [
    {
      "criterion_id": "AC1",
      "test_code": "from solution import reverse\\nassert reverse('abc') == 'cba'\\n"
    },
    {
      "criterion_id": "AC2",
      "test_code": "from solution import reverse\\nassert reverse('') == ''\\n"
    }
  ]
}""",
    "reviewer": """{
  "verdicts": [
    {
      "criterion_id": "AC1",
      "approved": true,
      "justification": "Test result shows AC1 passed: reverse('abc') == 'cba' as required."
    },
    {
      "criterion_id": "AC2",
      "approved": true,
      "justification": "Test result shows AC2 passed: reverse('') == '' as required."
    }
  ]
}""",
}


# --- Phase 5: real-mode config ---------------------------------------------

# PROJECT_BRIEF.md's mixed-model decision: Planner and Reviewer need strong
# reasoning, so they use the bigger orchestrator model; Coder does
# high-volume, mechanical work, so it uses the smaller/faster worker model.
# Phase 6: the Tester's job (write a small, mechanical test script per
# criterion) is the same "high-volume, mechanical" shape as the Coder's,
# so it shares the worker model rather than getting a third tier — keeps
# the free-tier rate-limit story simple (two pools, not three) and matches
# PROJECT_BRIEF.md's own framing of what needs the bigger model and what
# doesn't.
_MODEL_ENV_BY_ROLE: dict[str, str] = {
    "planner": "SDLC_ORCHESTRATOR_MODEL",
    "reviewer": "SDLC_ORCHESTRATOR_MODEL",
    "coder": "SDLC_WORKER_MODEL",
    "tester": "SDLC_WORKER_MODEL",
}

# DECISION (found live, see PHASE_6_PROGRESS_AND_DECISIONS.md): Groq's
# response_format={"type": "json_object"} does more than check basic JSON
# syntax — it runs the model's own output through a stricter internal
# schema/structure validator, and on a real live run that validator
# rejected the Coder's response TWICE in a row with `failed_generation`
# EMPTY both times, giving zero visibility into what the model actually
# produced. Coder and Tester are the two roles whose JSON payloads embed
# large, multi-line CODE as string values (Planner/Reviewer's payloads are
# short criteria/verdict text) — exactly the shape most likely to trip a
# stricter structured-output validator. Rather than keep paying for a
# feature that was actively destroying the one thing needed to debug a
# failure (the raw bad response), json_object mode is now skipped for
# these two roles specifically; our own parsing (json.loads + Pydantic +
# agents.py's _python_syntax_error() static check) is the actual
# correctness backstop, and it produces a real, inspectable error instead
# of an opaque 400. Planner/Reviewer keep json_object mode — their
# payloads are short and haven't shown this failure mode.
_ROLES_WITHOUT_JSON_MODE: frozenset[str] = frozenset({"coder", "tester"})

# DECISION: this retry budget is read from its OWN env vars and is
# deliberately separate from RetryCounters.spec_approval_retries /
# test_review_retries in state.py. Those two count semantically meaningful
# failures (a rejected spec, a failing test/review) that a human and the
# Phase 7 traceability report care about. Getting rate-limited by Groq's
# free tier and retrying half a second later is not a failure of the
# Planner/Coder/Reviewer/Tester's output — it's infrastructure throttling,
# orthogonal to whether the eventual response was any good — see
# PROJECT_BRIEF.md's "Retry caps everywhere" decision and
# EVALUATION_AND_ROADMAP.md's Phase 5 section, which both call this out as
# a distinct concern. It must not eat into those budgets or show up in a
# run's traceability history as if the agent got something wrong.
_MAX_RATE_LIMIT_RETRIES = int(os.environ.get("SDLC_GROQ_MAX_RATE_LIMIT_RETRIES", "5"))
_BACKOFF_BASE_SECONDS = float(os.environ.get("SDLC_GROQ_BACKOFF_BASE_SECONDS", "2"))

# BUG #4 (found live on a real ShoppingCart run: 5/5 Coder attempts all
# failed with json.JSONDecodeError -- 4x "Expecting value: line 1 column 1
# (char 0)" and 1x "Unterminated string starting at ... char 55"): neither
# max_tokens/max_completion_tokens NOR reasoning_format was ever being
# sent to Groq. openai/gpt-oss-20b / openai/gpt-oss-120b (this project's
# SDLC_WORKER_MODEL / SDLC_ORCHESTRATOR_MODEL) are REASONING models --
# per Groq's own docs (console.groq.com/docs/reasoning), before emitting a
# single character of the actual answer they spend completion tokens on
# internal chain-of-thought, and Groq's default max_completion_tokens is
# only 1024. Two failure shapes follow directly from that, both of which
# match what was observed live:
#   - reasoning alone burns through the whole 1024-token budget before any
#     JSON is emitted -> `message.content` comes back "" with
#     finish_reason="length" -> json.loads("") -> "Expecting value: line 1
#     column 1 (char 0)" (4 of the 5 attempts).
#   - reasoning finishes with tokens to spare, content generation starts,
#     but the SAME shared budget runs out partway through the JSON string
#     -> a truncated response -> "Unterminated string" wherever the cutoff
#     landed (the 5th attempt).
# Also: reasoning_format defaults to "raw" (reasoning inlined into
# `content` via <think>...</think>), which would ALSO break json.loads at
# char 0 even with a large enough budget, since content wouldn't start
# with "{". Fix, applied to every role uniformly:
#   - max_completion_tokens raised well above the 1024 default (generous
#     enough for reasoning + a full multi-method Python class + JSON
#     overhead), via SDLC_GROQ_MAX_COMPLETION_TOKENS.
#   - reasoning_format="hidden" always -- guarantees `content` is ONLY the
#     final answer (reasoning still happens and still costs tokens, but
#     never leaks into the JSON we're about to parse). Groq's docs note
#     "parsed"/"hidden" are required for JSON mode anyway (planner/
#     reviewer), so this is a no-op there and a fix for coder/tester.
#   - reasoning_effort="low" for the WORKER roles specifically (coder,
#     tester -- see _ROLES_WITHOUT_JSON_MODE just above: same "mechanical,
#     high-volume" tier PROJECT_BRIEF.md already assigns them). Less
#     reasoning per call means more of the shared token budget is left for
#     the actual code/test output, which is the thing that was starving.
#     Planner/Reviewer are left at the provider default -- their payloads
#     are short criteria/verdict text, not full source files, so they
#     were not the ones observed hitting this failure live, and they
#     benefit more from unrestricted reasoning quality than coder/tester
#     do for "write this mechanical test script" work.
_MAX_COMPLETION_TOKENS = int(os.environ.get("SDLC_GROQ_MAX_COMPLETION_TOKENS", "8000"))
_WORKER_REASONING_EFFORT = os.environ.get("SDLC_GROQ_WORKER_REASONING_EFFORT", "low")

# Lazily constructed so mock-mode runs (including the existing test suite,
# test_planner.py / test_approval_gate.py / test_full_loop.py) never need
# GROQ_API_KEY set at all — building a real Groq() client is a cost only
# real mode should pay.
#
# DECISION: constructed with max_retries=0. The groq SDK ships its own
# built-in retry behavior (DEFAULT_MAX_RETRIES = 2, confirmed by reading
# venv/Lib/site-packages/groq/_constants.py) that would otherwise retry
# silently *underneath* the loop in _call_groq_real() below — two
# overlapping, differently-tuned retry mechanisms, one of them invisible
# from this file. That's the same category of surprise Phase 4's decision
# log flagged about LangGraph silently dropping undeclared state keys:
# correct-looking code whose actual retry/backoff behavior you could not
# explain from reading this file alone. Disabling the SDK's own retries and
# doing 100% of the backoff logic explicitly here means the whole retry
# story lives in one place you can point to.
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise LLMCallError(
                "SDLC_USE_MOCK=0 but GROQ_API_KEY is not set in the "
                "environment (.env). Real mode needs a Groq API key."
            )
        _client = Groq(api_key=api_key, max_retries=0)
    return _client


def _call_groq_real(agent_role: str, prompt: str) -> str:
    """The Phase 5 real branch. Retries ONLY on the transient, "try again
    shortly" errors — RateLimitError (429) and connection/timeout errors —
    with exponential backoff and jitter. Anything else (bad API key, unknown
    model, malformed request) is a real problem, not a rate limit, and is
    left to raise on the first attempt rather than being silently retried
    into looking like a hang.

    response_format={"type": "json_object"} is passed for planner/reviewer
    to push the model into valid-JSON output structurally, on top of (not
    instead of) the prompt's own instructions. It is DELIBERATELY OMITTED
    for coder/tester — see _ROLES_WITHOUT_JSON_MODE's comment above for
    the live failure that motivated this split.

    max_completion_tokens/reasoning_format="hidden" (and reasoning_effort
    for coder/tester) are always passed now — see BUG #4's comment on
    _MAX_COMPLETION_TOKENS above. Without them, gpt-oss's hidden
    chain-of-thought can (and on a live run, did) consume the entire
    default 1024-token budget before any JSON was emitted, or leak
    <think> tags into `content` — either way json.loads() downstream got
    nothing usable.
    """
    model_env = _MODEL_ENV_BY_ROLE.get(agent_role)
    if model_env is None:
        raise LLMCallError(f"No model configured for agent_role={agent_role!r}.")
    model = os.environ.get(model_env)
    if not model:
        raise LLMCallError(f"{model_env} is not set in the environment (.env).")

    client = _get_client()

    create_kwargs: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        # See BUG #4's comment on _MAX_COMPLETION_TOKENS above: without
        # these two, a reasoning model can (and on a live run, did) burn
        # its entire completion budget on hidden chain-of-thought and/or
        # leak <think> tags into content, leaving nothing (or something
        # unparseable) for json.loads() to work with.
        "max_completion_tokens": _MAX_COMPLETION_TOKENS,
        "reasoning_format": "hidden",
    }
    if agent_role not in _ROLES_WITHOUT_JSON_MODE:
        create_kwargs["response_format"] = {"type": "json_object"}
    else:
        # Worker tier (coder/tester): bias toward leaving more of the
        # shared token budget for actual output rather than reasoning --
        # see BUG #4's comment above.
        create_kwargs["reasoning_effort"] = _WORKER_REASONING_EFFORT

    last_error: Exception | None = None
    last_reason = ""
    for attempt in range(_MAX_RATE_LIMIT_RETRIES + 1):
        try:
            response = client.chat.completions.create(**create_kwargs)
            return response.choices[0].message.content or ""
        except RateLimitError as e:
            last_error, last_reason = e, "rate limited"
        except (APIConnectionError, APITimeoutError) as e:
            # APITimeoutError is a subclass of APIConnectionError in the
            # groq SDK, so this branch also catches plain timeouts — listed
            # separately here anyway so the reason string stays accurate.
            last_error, last_reason = e, "connection error"
        except GroqError as e:
            # Everything else Groq can raise (BadRequestError, e.g. the
            # response_format=json_object validator rejecting a generation
            # with "json_validate_failed" — the free-tier invalid-JSON
            # unreliability the roadmap warned about, just surfacing as a
            # rejected request instead of malformed-but-parseable text;
            # AuthenticationError; NotFoundError on a bad model id; etc.).
            # Deliberately NOT retried here — blindly resampling would mask
            # a real prompt/config problem. Raised immediately as
            # LLMCallError instead: agents.py's run_planner/run_coder/
            # run_reviewer/run_tester_real catch LLMCallError and convert it
            # into their own *OutputError, which the ALREADY-BUILT
            # test_review_retries / spec_approval_retries loop resamples
            # through — so a retry still happens, at the layer already
            # designed for "the LLM hasn't produced something usable yet"
            # (Phase 4 decision #1), not duplicated here.
            raise LLMCallError(
                f"Groq call for agent_role={agent_role!r} failed (not a "
                f"rate-limit/connection issue, not retried here): {e}"
            ) from e

        if attempt < _MAX_RATE_LIMIT_RETRIES:
            # Exponential backoff (base * 2**attempt) with +/-50% jitter, so
            # that if the Planner/Coder/Tester/Reviewer all get rate-limited
            # in the same run, their retries don't all wake up and hit Groq
            # again at the exact same instant.
            delay = _BACKOFF_BASE_SECONDS * (2**attempt) * random.uniform(0.5, 1.5)
            time.sleep(delay)

    raise LLMCallError(
        f"Groq call for agent_role={agent_role!r} failed after "
        f"{_MAX_RATE_LIMIT_RETRIES} retries ({last_reason} each time): {last_error}"
    )


def call_llm(
    agent_role: str,
    prompt: str,
    *,
    mock_response: str | None = None,
) -> str:
    """
    Send `prompt` as `agent_role` ("planner", "coder", "tester", "reviewer")
    and return the raw text response.

    Mock mode (SDLC_USE_MOCK != "0", the default):
      - if `mock_response` is given, return it verbatim — this is how
        test_planner.py / test_full_loop.py / test_real_tester.py inject
        varied/deliberately-broken fixtures without this file needing to
        know about any of them.
      - otherwise, return a generic canned reply for `agent_role`, or "{}"
        if that role has no default yet.

    Real mode (SDLC_USE_MOCK == "0"):
      - makes an actual Groq chat-completion call using
        SDLC_ORCHESTRATOR_MODEL (planner/reviewer) or SDLC_WORKER_MODEL
        (coder/tester), with response_format json_object (planner/reviewer
        only), reasoning_format="hidden" (always), max_completion_tokens
        (SDLC_GROQ_MAX_COMPLETION_TOKENS, default 8000 — see BUG #4's
        comment in this file for why the 1024 provider default silently
        starved reasoning models of any room to actually answer),
        reasoning_effort (coder/tester only, SDLC_GROQ_WORKER_REASONING_EFFORT,
        default "low"), and exponential-backoff retry
        (SDLC_GROQ_MAX_RATE_LIMIT_RETRIES, default 5;
        SDLC_GROQ_BACKOFF_BASE_SECONDS, default 2) around rate-limit and
        connection errors specifically. `mock_response` is ignored in real
        mode — it exists to inject fixtures into mock mode, not to
        override a real call.
      - raises LLMCallError if GROQ_API_KEY / the role's model env var is
        missing, or if the retry budget above is exhausted.

    `prompt` is unused in mock mode (the mock doesn't read it) but is what
    real mode actually sends — the signature didn't need to change between
    the two, which was the point of introducing this file in Phase 2.
    """
    use_mock = os.environ.get("SDLC_USE_MOCK", "1") != "0"

    if not use_mock:
        return _call_groq_real(agent_role, prompt)

    if mock_response is not None:
        return mock_response

    return _DEFAULT_MOCK_RESPONSES.get(agent_role, "{}")
