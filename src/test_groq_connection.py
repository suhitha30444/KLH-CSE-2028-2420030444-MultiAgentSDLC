"""
test_groq_connection.py — Phase 5, step 1: standalone one-call test script.

Sends ONE real Groq API call per agent's *actual* prompt (imported straight
from agents.py's _build_prompt / _build_coder_prompt / _build_reviewer_prompt,
so this exercises the exact text the real graph will send in Phase 5 — not
a synthetic "say OK" ping) and prints the raw response plus whether it
parses as the JSON shape each agent expects.

This deliberately does NOT go through call_llm() — call_llm()'s real-mode
branch is what Phase 5 builds next, informed by what this script tells us
(e.g. whether the smaller worker model needs prompt tightening to stay
valid JSON). Keep SDLC_USE_MOCK=1 in .env until this script is reliable
for all three agents.

Run it directly from your own terminal (needs your machine's normal
internet — Claude's own tool access can't reach api.groq.com to run this
for you):

    python test_groq_connection.py            # tests all three agents
    python test_groq_connection.py planner     # just one
"""
from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from groq import Groq

from agents import _build_prompt, _build_coder_prompt, _build_reviewer_prompt
from state import AcceptanceCriterion, PerCriterionResult, Spec, TaskItem

API_KEY = os.environ.get("GROQ_API_KEY", "")
ORCH_MODEL = os.environ.get("SDLC_ORCHESTRATOR_MODEL", "openai/gpt-oss-120b")
WORKER_MODEL = os.environ.get("SDLC_WORKER_MODEL", "openai/gpt-oss-20b")

if not API_KEY:
    print("GROQ_API_KEY is not set in .env — nothing to test.")
    sys.exit(1)

client = Groq(api_key=API_KEY)

# Same canonical example already used everywhere else in this project
# (llm_client.py's default mocks, test_full_loop.py) so results are
# comparable against the mock-mode traces you already have.
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


def call(agent_role: str, model: str, prompt: str) -> None:
    print(f"\n=== {agent_role} ({model}) ===")
    print(f"--- prompt sent ({len(prompt)} chars) ---")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print(f"CALL FAILED: {type(e).__name__}: {e}")
        return

    raw = resp.choices[0].message.content
    print(f"--- raw response ---\n{raw}")

    try:
        parsed = json.loads(raw)
        print(f"--- JSON parse: OK, keys={list(parsed.keys())} ---")
    except json.JSONDecodeError as e:
        print(f"--- JSON parse: FAILED: {e} ---")
        print(
            "This is the failure mode the roadmap flags as most likely on "
            "the free-tier model — if it happens, paste this raw response "
            "plus the prompt above back to Claude to iterate the prompt. "
            "Don't loosen the schema to accept it."
        )


AGENTS = {
    "planner": lambda: call("planner", ORCH_MODEL, _build_prompt(SAMPLE_REQUIREMENT)),
    "coder": lambda: call("coder", WORKER_MODEL, _build_coder_prompt(SAMPLE_SPEC)),
    "reviewer": lambda: call(
        "reviewer", ORCH_MODEL, _build_reviewer_prompt(SAMPLE_SPEC, SAMPLE_TEST_RESULTS)
    ),
}

if __name__ == "__main__":
    targets = sys.argv[1:] or list(AGENTS.keys())
    for name in targets:
        if name not in AGENTS:
            print(f"Unknown agent {name!r}; choices are {list(AGENTS.keys())}")
            continue
        AGENTS[name]()
