# Review 2 — Progress Report

**Team:** Kapilavai Hamsini (2420030398), Suhitha Chalasani (2420030444),
Sri Raaga Tangirala (2420030472)
**Supervisor:** Dr. K. Swanthana
**Date:** 2026-09-18

## Since Review 1

Review 1 covered the initial abstract and project setup. Since then, the
project's scope was deliberately corrected and narrowed, and the core
pipeline (Phases 0–7 of the SDD-integrated roadmap) was built, tested, and
verified against live Groq calls.

### Scope correction

The original abstract described seven agents (Requirement Analysis,
Planning, Frontend, Backend, Code Review, Testing, Documentation) on Llama
3.x with Docker sandboxing. This was reviewed and narrowed to **four
agents** — Planner, Coder, Tester, Reviewer — on Groq's `openai/gpt-oss-120b`
/ `openai/gpt-oss-20b` (Llama 3.x was deprecated by Groq on 16 Aug 2026),
with **subprocess-based sandboxing** instead of Docker — a deliberate,
explainable tradeoff for the project's actual threat model (arbitrary-but-
not-adversarial LLM output, not a multi-tenant service). Full reasoning:
`docs/phase-logs/PHASE_0_1_PROGRESS_AND_DECISIONS.md`.

### What was built (Phases 0–7)

| Phase | Deliverable | Status |
|---|---|---|
| 0 | LangGraph/Pydantic/Groq tool literacy | Done |
| 1 | SDD schemas (`state.py`) | Done |
| 2 | Planner, mocked, with spec persistence | Done |
| 3 | Human approval gate | Done |
| 4 | Coder, stub Tester, Reviewer, full mock loop with retries | Done |
| 5 | Real Groq calls + rate-limit handling | Done |
| 6 | Real sandboxed, per-criterion Tester | Done |
| 7 | Reviewer + traceability report | Done |

**Per the roadmap: "End of Phase 7 = a complete, demoable, genuinely
spec-driven project."** That milestone is reached.

### Five real bugs found and fixed via live testing

Live Groq runs against a multi-criterion `ShoppingCart` requirement
surfaced five genuine, distinct bugs — each diagnosed from a real
traceback or a real bad output, not anticipated in advance:

1. **Sandbox timeout race** — `RLIMIT_CPU` and the wall-clock timeout could
   race, producing an unclear `SIGKILL` instead of a clean timeout message.
2. **Double-escaped-newline JSON** — structurally valid JSON containing
   syntactically broken Python, now caught by a static `compile()` check
   before execution.
3. **Groq `json_object` mode rejecting large code payloads** with no
   diagnostic — worked around by disabling strict JSON mode for the
   Coder/Tester roles specifically.
4. **Reasoning-model token starvation** — `gpt-oss` models spend completion
   tokens on hidden chain-of-thought before answering; the default 1024-token
   cap left nothing for the actual JSON output. Fixed by raising
   `max_completion_tokens` to 8000 and forcing `reasoning_format="hidden"`.
5. **Windows default-encoding crash** — LLM-generated Unicode punctuation
   (e.g. a non-breaking hyphen) crashed `write_text()` under Windows'
   default `cp1252` locale. Fixed by forcing UTF-8 encoding on every file
   write and subprocess I/O boundary.

Full writeups: `docs/phase-logs/PHASE_6_PROGRESS_AND_DECISIONS.md` and the
three `BUGFIX_*.md` files.

### A structural fix: retries stopped being blind resamples

Coder retries originally repeated the exact same prompt after a failure,
with no information about what went wrong — for a model with a systematic
bias (e.g. double-escaping newlines), that just reproduced the same mistake.
Both the Coder's own validation errors and Reviewer-triggered retries now
carry the specific prior failure (which criterion, which test detail, which
justification) into the next attempt's prompt. See
`docs/phase-logs/BUGFIX_CODER_RETRY_FEEDBACK.md`.

### Result

After all five fixes, a live run against the `ShoppingCart` requirement
reached a genuine **`DONE`** — 7/7 acceptance criteria passed in the real
sandbox and approved by the Reviewer — the first time this project reached
that state end-to-end on real Groq calls, not mocked output.

## Known gaps going into the next phase

- No SQLite persistence yet (Phase 8, optional polish) — run history exists
  only as flat files in `results/`.
- No live progress UI (Phase 9, optional polish) — Flask is the planned
  choice, nothing built yet.
- Agile/sprint wrapper (Phase 10) not started — explicit stretch goal; the
  state schema already reserves the fields it will need.
- Windows-specific `resource`-module limits are reasoned through and
  guarded in code but not independently verified on a Windows interpreter
  (only the timeout applies there; POSIX gets the additional memory/CPU
  limits).
- No traceability report has yet been captured from a live run that ends
  `FAILED` at the retry cap — only a live `DONE` report exists so far.

## Next steps

1. Capture one live `FAILED`-at-cap report to confirm the retry-count
   reporting (added in Phase 7) reads correctly end to end on real output.
2. Optionally implement Phase 8 (SQLite) and/or Phase 9 (Flask/SSE) if time
   allows before the final review — neither is required for the "genuinely
   spec-driven project" bar the roadmap sets.
