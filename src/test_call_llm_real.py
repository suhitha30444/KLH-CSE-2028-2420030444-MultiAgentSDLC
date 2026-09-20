"""
test_call_llm_real.py — Phase 5: exercises call_llm() itself in real mode,
not just a raw Groq call the way test_groq_connection.py does. That script
proves Groq is reachable and the prompts produce valid JSON; this one
proves llm_client.py's new _call_groq_real() branch actually works —
model-by-role selection, response_format, the retry/backoff loop — since
it's the same function agents.py calls.

Sets SDLC_USE_MOCK=0 for THIS PROCESS ONLY (os.environ, not your .env
file), so .env can stay at SDLC_USE_MOCK=1 for every other script and the
existing test suite.

Run:
    python test_call_llm_real.py            # tests all three agents
    python test_call_llm_real.py planner     # just one
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
load_dotenv()

os.environ["SDLC_USE_MOCK"] = "0"  # in-process override only

from agents import _build_coder_prompt, _build_prompt, _build_reviewer_prompt
from llm_client import LLMCallError, call_llm
from state import AcceptanceCriterion, PerCriterionResult, Spec, TaskItem

SAMPLE_REQUIREMENT = "Write a function that reverses a string."

SAMPLE_SPEC = Spec(
    run_id="test-run",
    requirement=SAMPLE_REQUIREMENT,
    acceptance_criteria=[
        AcceptanceCriterion(id="AC1", text="reverse('abc') == 'cba'"),
        AcceptanceCriterion(id="AC2", text="reverse('') == ''"),
    ],
    tasks=[
        TaskItem(id="T1", description="Implement reverse()", addresses_criteria=["AC1", "AC2"]),
    ],
)

SAMPLE_TEST_RESULTS = [
    PerCriterionResult(criterion_id="AC1", passed=True, detail="[stub] passed"),
    PerCriterionResult(criterion_id="AC2", passed=True, detail="[stub] passed"),
]

PROMPTS = {
    "planner": lambda: _build_prompt(SAMPLE_REQUIREMENT),
    "coder": lambda: _build_coder_prompt(SAMPLE_SPEC),
    "reviewer": lambda: _build_reviewer_prompt(SAMPLE_SPEC, SAMPLE_TEST_RESULTS),
}


def run(agent_role: str) -> None:
    print(f"\n=== call_llm({agent_role!r}, ...) — real mode ===")
    try:
        raw = call_llm(agent_role, PROMPTS[agent_role]())
    except LLMCallError as e:
        print(f"LLMCallError: {e}")
        return
    print(raw)


if __name__ == "__main__":
    targets = sys.argv[1:] or list(PROMPTS.keys())
    for name in targets:
        if name not in PROMPTS:
            print(f"Unknown agent {name!r}; choices are {list(PROMPTS.keys())}")
            continue
        run(name)
