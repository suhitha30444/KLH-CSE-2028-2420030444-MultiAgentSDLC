# A Spec-Driven, Multi-Agent Framework for Automating the Software Development Lifecycle on Free-Tier LLM Infrastructure

**Hamsini Kapilavai**
Department of Computer Science and Engineering, KL University, Bowrampet
*Rough draft (bullet outline), September 2026. Not final prose; to be expanded into full sections later.*

---

## Abstract (bullet notes)

- A system where four AI agents (Planner, Coder, Tester, Reviewer) work together to turn a plain-English requirement into tested, working code.
- Runs on LangGraph, so agents can loop back to each other instead of just running in a straight line.
- Built entirely on free-tier tools: Groq's free API, two sizes of open model, no paid infrastructure.
- Two decisions make it reliable rather than just a demo:
  - Every agent outputs structured JSON, checked with Pydantic, instead of relying on native "tool calling," which the free models handled poorly.
  - Retries carry information forward. When the Coder fails, the next attempt is told what went wrong instead of just repeating the same prompt.
- Code is actually run and tested in a sandboxed subprocess, not self-graded by the model.
- Every run produces a traceability report: requirement, criteria, code, test result, review verdict.
- Reports live, non-mocked results, including six real bugs found only because the system was run for real, and how each was fixed, ending in a genuine `DONE` on a fairly complex test case.
- Closes with limitations and remaining work.

---

## 1. Introduction (bullet notes)

- LLMs are good at writing one function or file at a time, but real software development is a loop: plan, build, test, review, fix, repeat.
- Question this project asks: can a small team of role-specialized AI agents carry out that loop end to end, on a real (small) requirement, using only free tools, and leave behind something a human can check afterward?
- Originally scoped as seven agents (requirement analysis, planning, frontend, backend, review, testing, docs) on Docker with Llama 3.x. Deliberately narrowed to four agents (Planner, Coder, Tester, Reviewer) and a lighter subprocess sandbox instead of Docker. More agents don't add capability if they aren't doing meaningfully different work, and Docker was solving for a threat model (untrusted multi-tenant code) this project doesn't have.
- Not claiming a new model or algorithm. Built entirely from existing tools: LangGraph, Pydantic, Groq-hosted open models.
- The actual contribution: an honest account of what breaks when this kind of pipeline is run for real, not mocked, against a rate-limited free API, and the specific fixes that made it recoverable rather than silently wrong.

---

## 2. Related Work

**Source quality check.** Ten papers were originally collected for this project. Only four hold up as citable academic sources: Sami et al., Khanzadeh (AgentMesh), Rasheed et al. (CodePori), and Wang et al. Five others (short pieces credited to Wasif/Tunkel, Khan/Kallinteris, Nasir/Kallinteris, Khan/Daviglus, and Sajid/Maya) have been dropped and are not cited. They share signs that don't belong in genuine research: near-identical reference lists citing unrelated fields (HR analytics, genomics, biomedical retrieval) under a software-engineering paper, in places reusing the same reference list verbatim across different listed authors; vague numeric claims ("35% increase in development speed," "40% fewer coding errors") with no stated methodology, dataset, or system behind them; and no named system, architecture diagram, or code in any of the five. There's no answer to "how was this measured," so they don't belong in a report that will be scrutinized. A seventh paper, Baldwa et al. ("XCognitive SwarmNet"), is kept but flagged: it is a Research Square preprint, not peer-reviewed, and its results (98.1% accuracy, gains across every metric) read as unusually tidy. It is cited as related work, not as validated ground truth.

**The four legitimate sources, and what each is used for:**

- Sami, Awan, Rasheed, Saari, Systä & Abrahamsson (2024), "Experimenting with Multi-Agent Software Development: Towards a Unified Platform" (arXiv:2406.05381), Tampere/Jyväskylä. An active academic group, properly structured, with real experiments. Similar goal — LLM agents turning requirements into user stories, UML, code, and tests — but built on paid models (GPT-3.5/4/Llama3) with a broader deliverable set. Establishes that this general direction is legitimate, active research rather than something this project needs to outdo.

- Khanzadeh (2025), "AgentMesh: A Cooperative Multi-Agent Generative AI Framework for Software Development Automation" (arXiv:2507.19902). The closest architectural match. Same four-role shape: Planner, Coder, Debugger/Tester, Reviewer, in a sequential LangGraph-style pipeline. This means the four-agent shape itself is not the novel part of this project; AgentMesh got there first. But AgentMesh's own paper states its Reviewer does not structurally gate anything — its report is used mainly to flag things for human inspection rather than feed back into a retry loop. This project's Reviewer does what AgentMesh's explicitly does not: it structurally blocks completion (`tests_passed AND all_approved`, §4) and forces capped, evidence-based retries. See the novelty statement below.

- Rasheed, Waseem, Kemell, Ahmad, Sami, Saari, Rasku & Abrahamsson (2026), "CodePori: Large-Scale System for Autonomous Software Development Using Multi-Agent Technology" (arXiv:2402.01411), same Tampere group, a 118-participant empirical study. Argues against benchmark-only evaluation ("binary pass-or-fail... limited insight into practical applicability") in favor of practitioner-facing evaluation, which matches the approach behind the live-run bug reporting in §5. Used here mainly as a foil on scope (see below).

- Wang, Xu, Chen, Bi, Gu & Zheng (2025), "An Empirical Study of Agent Developer Practices in AI Agent Frameworks" (arXiv:2512.01939). A large empirical study: 1,575 GitHub agent projects, 8,710+ developer discussions, and a four-category taxonomy of agent-framework failures across the SDLC. Taken directly from the paper's own text (p.2): Logic failures (task termination, infinite-loop prevention) account for 25.6%; Tool failures (integration, permission, API) for 14%; Performance failures (context retention, memory management) for 25%; Version failures (framework/dependency incompatibility) for over 23%. A different pair of figures, 21.63%/25.61%, circulates in secondary discussion of this paper; those do not match the source text and should not be used — the figures above were checked directly against the PDF and are the ones to cite. This taxonomy is used in §4 to justify specific design choices, not just as background.

**Candidate replacement papers, not yet reviewed.** Five additional arXiv papers were identified as stronger replacements for the five excluded above. They have not yet been obtained or read in full, so the relevance notes below are provisional pending review of the actual text:
- "LLM-Based Multi-Agent Systems for Software Engineering: Literature Review, Vision and the Road Ahead" (arXiv:2404.04834) — general foundation; reportedly discusses the free-tier/open-weight-model gap this project's approach sits in.
- "AgentBalance: Backbone-then-Topology Design for Cost-Effective Multi-Agent Systems under Budget Constraints" (arXiv:2512.11426) — budget-constrained multi-agent design, relevant to the free-tier framing.
- "Human-In-the-Loop Software Development Agents" (arXiv:2411.12924) — relevant to the Phase 3 human-approval-gate design (§4).
- "MapCoder-Lite: Distilling Multi-Agent Coding into a Single Small LLM" (arXiv:2509.17489) — small/distilled-model reliability, relevant to the `gpt-oss-20b` worker-tier choice.
- "When Should AI Review Precede Human Approval of Agent-Generated Code?" (arXiv:2603.13870) — relevant to the Reviewer-verdict vs. human-approval-gate distinction this project's design makes.

**A note on scope, not novelty.** Baldwa et al.'s XCognitive SwarmNet (caveated above) sits at the opposite end of the spectrum from this project: a heavy cognitive-swarm framework with collective memory, an explainability layer, digital-twin simulation, and governance, benchmarked against six systems. This project trades that sophistication for being buildable and runnable on zero budget, with auditability coming from a traceability report rather than a dedicated explainability layer.

### Novelty statement (grounded in the four legitimate sources only)

1. **Core contribution: a Reviewer that is load-bearing, not advisory, and a demonstration of what that costs and buys.** AgentMesh, the closest prior system, built the same four-role shape and left its Reviewer's output advisory. This project's Phase 5 live run shows what happens when the Reviewer's verdict is instead structurally load-bearing: a real, reasoning-capable Reviewer, shown stub (unverified) test evidence, correctly refused to approve any criterion, and the run terminated `FAILED` cleanly, with no false `DONE`, because completion required `tests_passed AND all_approved` rather than a plausible-sounding verdict. None of the four legitimate papers, including AgentMesh, test this specific condition: what a gated, evidence-aware Reviewer does when the evidence it is given is provably unverified.
2. **Design decisions justified against measured failure data, not instinct.** Wang et al.'s taxonomy (above) shows task-termination/looping failures and version/dependency failures are among the largest documented categories of real agent-framework failure. This project's independent per-loop retry caps (§4) and environment-variable-driven model IDs (which absorbed the Groq Llama→gpt-oss deprecation with a one-line config change, §3) are direct, purpose-built answers to those two categories, not just engineering instinct.
3. **CodePori as a foil on scope.** CodePori pursued large-scale, broad-autonomy generation with a 118-participant study, and even there participants still had to manually fix things — installing libraries, fixing paths, loading models — despite a six-agent system built on a stronger paid model. That is evidence, from serious academic work, that "large-scale, fully autonomous, zero human touch" does not yet hold up, which reframes this project's narrower, spec-gated, evidence-verified four-agent design as a deliberate trade-off rather than a limitation it is stuck with.
4. **A gap none of the four legitimate papers cover:** free-tier, rate-limited deployment on small open-weight models (`gpt-oss-20b`/`120b`) instead of GPT-4/Claude-class models. If the pending literature-review paper (2404.04834) turns out to flag this gap once reviewed, it strengthens this point further, but it stands on the four verified sources alone in the meantime.

---

## 3. System Architecture (bullet notes)

- LangGraph state graph: four agent nodes plus one human-approval "interrupt" node.
- Flow: Planner, then human approval or rejection, then Coder, Tester, Reviewer, with two loop-back paths:
  - Spec loop: human rejects, control returns to the Planner.
  - Test/review loop: a failing test or a rejected review sends control back to the Coder.
- Each loop has its own retry counter, so one bad loop can't consume the other's budget.
- Groq rate-limit backoff is handled separately again; a 429 response is not a quality failure, so it doesn't count against either retry budget.

**Agent roles and model sizing:**

| Agent | Job | Model | Why |
|---|---|---|---|
| Planner | Requirement to spec and acceptance criteria | Larger model (`gpt-oss-120b`) | Needs real judgment to break down a vague ask |
| Coder | Spec/task to code | Smaller model (`gpt-oss-20b`) | High-volume, more mechanical |
| Tester | Criterion to runnable test script | Smaller model (`gpt-oss-20b`) | Same as Coder |
| Reviewer | Code and test results to a verdict per criterion | Larger model (`gpt-oss-120b`) | Needs judgment again |

- Both model sizes are hosted on Groq only, to avoid managing separate free-tier rate limits across providers.
- Model names are read from `.env`, not hardcoded. This paid off when Groq deprecated the original Llama 3.1/3.3 models (August 16, 2026) and switching over took only a configuration change.

**State schema:**
- One shared Pydantic-based state object (`SDLCState`): `Spec`, `TaskItem`, `CodeArtifact`, `PerCriterionResult`, `ReviewVerdict`, `RetryCounters`.
- Acceptance criteria are objects with a stable ID (`AC1`, `AC2`, ...) assigned by the code itself, not by the LLM, avoiding a class of bugs where criteria get reordered and references stop lining up.
- The schema already has unused fields (`backlog`, `sprint_number`, `completed_increments`) reserved for a future Agile mode. The intent is that switching from a one-pass "waterfall" run to an iterative "Agile" mode later should mean changing the graph's wiring, not rewriting the data model.

---

## 4. Key Design Decisions (bullet notes)

- **Structured JSON over native tool-calling.** Every agent replies with a specific JSON shape, checked by Pydantic. This mattered more for reliability than which model size was used — the small/free models were considerably worse at directly "calling a tool" than at producing valid JSON when told exactly what shape to use.
- **Human approval gate.** After the Planner proposes a spec, the graph pauses and a human must approve or reject before any code is written. This is non-negotiable: the human decides what gets built, the pipeline automates how.
- **Retry budgets, and, more importantly, informed retries rather than blind resamples.** Justified against Wang et al.'s failure taxonomy (§2): task-termination/looping failures are the single largest documented category, at 25.6%, of real agent-framework failures, so a hard per-loop retry cap is a direct answer to the largest empirically known failure mode, not just a safety instinct.
  - Every loop has a hard retry cap. `test_review_retries` was raised from 3 to 5 after real runs showed 3 wasn't enough to give the Coder's actual logic a fair shot.
  - A larger fix followed from noticing that every retry across the project had been a blind resample: same prompt, no information about what went wrong last time. Fixed in two rounds:
    - Round 1: the Coder's own validation errors are fed back into the next attempt's prompt.
    - Round 2: extended to Reviewer rejections too. The next Coder prompt now includes which criterion failed, the real test detail, and the Reviewer's specific objection.
  - Deliberately not extended to Tester-side errors, since a broken test script is not something the Coder can fix, and feeding it back would just add noise.
- **Real sandboxed testing rather than self-graded pass/fail.** The Tester writes one runnable script per acceptance criterion, executed in a subprocess with a timeout and, on POSIX, CPU/memory limits. No Docker: the actual risk here is unpredictable LLM-written code, not an untrusted third party, so a lighter sandbox was judged sufficient.
- **A traceability report on every run.** A Markdown report per run: requirement, each criterion, task, code, test result, review verdict, retry count. Generated for both `DONE` and `FAILED` runs, since a failed run's report is just as useful for understanding what happened.

---

## 5. Evaluation: what happened on live runs (bullet notes)

- Not a benchmark score. This is a plain account of what happened running the system for real against the live Groq API, not mocked responses.

**Early result, and an instructive failure:**
- `is_prime` (3 criteria): reached `DONE` cleanly on an early live run.
- `ShoppingCart` (5 criteria), while the Tester was still a stub rather than real execution: the real Reviewer correctly refused to approve any criterion, because it could tell the "test results" weren't real evidence. The run ended `FAILED` at the retry cap, but cleanly, with no crash and correct retry counting. This is treated as a good sign rather than a bug — the Reviewer was not rubber-stamping.

**The ShoppingCart case: six real bugs found and fixed on the way to a genuine `DONE`:**

1. **Sandbox timing race.** The CPU limit and timeout were set to the same duration, so the CPU limit sometimes killed the process first with a confusing "-9" error instead of a clean timeout message. Fix: gave the CPU limit a two-second buffer above the timeout. Matches the "Logic / task termination" failure category from the Wang et al. study (§2).
2. **Double-escaped newlines.** The Coder's JSON was technically valid, but the Python inside it was broken because newlines were escaped twice. Fix: added a `compile()`-based syntax check immediately after validation, plus explicit anti-double-escaping instructions in the prompt.
3. **Groq rejecting large payloads.** Groq's structured-JSON mode silently rejected large code responses with no explanation. Fix: turned off structured-JSON mode for the Coder and Tester specifically (the largest payloads), and added a fallback to strip stray Markdown code fences. A "version/compatibility" style issue, in the same family as the earlier Llama-to-gpt-oss deprecation (§2).
4. **Blind retries.** Retries were resending the identical prompt with no feedback, so a systematic mistake like #2 simply repeated. Fix: the two-round feedback mechanism described in §4.
5. **Reasoning-model token starvation.** Groq's `gpt-oss` models spend tokens "thinking" before answering; the default token budget (1024) was often fully consumed by that reasoning, leaving an empty or cut-off JSON response. Fix: raised the token budget to 8000, forced `reasoning_format="hidden"`, and set low reasoning effort for the Coder and Tester roles specifically. A "performance / context and resource" style issue (§2).
6. **Windows Unicode crash.** Immediately after the fixes above, `ShoppingCart` (now 7 criteria) finally reached a real `DONE`: 7/7 passed in the sandbox, and the Reviewer approved. It then crashed one line later while saving the result, because the Planner's text contained a non-breaking hyphen character that Windows' default file-writing encoding (cp1252) couldn't handle. Fix: forced UTF-8 encoding on every file write and read, and on the sandbox's subprocess output.

- End state: with all six fixed, the 7-criterion `ShoppingCart` requirement completed end-to-end live: real code, real sandboxed tests, real Reviewer approval, no crash.
- None of these six bugs would have appeared under mocked testing; they only surfaced because the system was run against the real provider and the real target OS.

**Build status against the project's own roadmap:**

| Phase | What | Status |
|---|---|---|
| 0–7 | Tool setup, schemas, Planner, approval gate, full mock loop, real Groq calls, real sandboxed testing, traceability report | Done |
| 8 | SQLite persistence | Not built (planned) |
| 9 | Flask/live-progress UI | Not built (planned) |
| 10 | Agile/backlog wrapper | Not built (stretch goal) |

---

## 6. Limitations (bullet notes)

- Windows resource limits (CPU/memory) only partly apply. On Windows, only the timeout works, not the full resource-limit backstop. Reasoned through in code but not verified at the syscall level on a live Windows machine.
- The retry-feedback fix (§4) only covers Coder-side mistakes. A broken Tester-generated script still causes a blind resample, by design.
- No live Groq rate limit (429) has actually been hit, so the backoff logic is untested against a real throttling event.
- Persistence is limited to flat files (`specs/`, `reports/`); no database yet (Phase 8).
- No live UI yet, only console output and generated reports (Phase 9).
- The Agile mode is a schema-level plan, not a built or tested feature (Phase 10).
- Small sample: only two example requirements tried so far (`is_prime`, `ShoppingCart`), with one genuine `DONE` on the harder case. These are illustrative case studies, not a statistically solid reliability estimate.

---

## 7. Future Work (bullet notes)

- Run more live cases, including one complex enough to genuinely exhaust the 5-retry budget on real code-quality grounds, to obtain a live `FAILED` report with a real retry history now that the six known bugs are fixed.
- Phase 8: SQLite persistence, so past runs can be reopened without re-running.
- Phase 9: Flask with live progress (SSE), so all four agents' status is visible as it happens.
- Phase 10 (stretch): an Agile/backlog wrapper, conceptually related to the pending Agile-focused papers identified for the candidate replacement set (§2).

---

## 8. Conclusion (bullet notes)

- Two decisions mattered most for reliability: structured, validated JSON output instead of native tool-calling, and retries that carry forward real feedback instead of blindly resampling.
- Running real code for real, on the real target OS, is what surfaced six genuine bugs a mocked test would not have found, and fixing all six is what took a complex requirement from repeated failure to an actual, verified `DONE`.
- The central claim is not "four cooperating agents"; AgentMesh built that shape first. The claim is that making the Reviewer's verdict structurally load-bearing rather than advisory changes what the system does under unverified evidence: it refuses to report `DONE` instead of guessing, and this is demonstrated with a real run rather than only argued for.
- The remaining gaps (database, live UI, Agile mode) are scoped and deliberately deferred. They do not change the core result: a small, free-tier, role-specialized agent team with a load-bearing Reviewer, feedback-informed retries, and an auditable report per run can automate a real, defensible slice of the SDLC.

---

## References

**Cited (verified, legitimate sources):**

1. Sami, M. A., Awan, M. W., Rasheed, Z., Saari, M., Systä, K., & Abrahamsson, P. (2024). *Experimenting with Multi-Agent Software Development: Towards a Unified Platform.* arXiv:2406.05381.
2. Khanzadeh, S. (2025). *AgentMesh: A Cooperative Multi-Agent Generative AI Framework for Software Development Automation.* arXiv:2507.19902.
3. Rasheed, Z., Waseem, M., Kemell, K.-K., Ahmad, A., Sami, M. A., Saari, M., Rasku, J., & Abrahamsson, P. (2026). *CodePori: Large-Scale System for Autonomous Software Development Using Multi-Agent Technology.* arXiv:2402.01411.
4. Wang, Y., Xu, X., Chen, J., Bi, T., Gu, W., & Zheng, Z. (2025). *An Empirical Study of Agent Developer Practices in AI Agent Frameworks.* arXiv:2512.01939.
5. Baldwa, A., Upadhyay, D., Bhatt, P., Bhatt, P., Bacanin, N., Djuric Jovicic, M., & Nikolic, B. (2026). *Explainable Multi-Agent AI Systems for Intelligent Software Engineering and Business Automation.* Research Square preprint (not peer-reviewed; cite as related work, not validated ground truth), DOI:10.21203/rs.3.rs-10527656/v1.

**Excluded, not to be cited** (padded/duplicated reference lists citing unrelated fields, unsourced numeric claims, no named system or architecture): Wasif & Tunkel (2025); Khan & Kallinteris (2025, "Autonomous Multi-Agent LLMs in Agile Development"); Nasir & Kallinteris (2025); Khan & Daviglus (2025); Sajid & Maya (2023).

**Candidate replacements, pending review** (freely available on arXiv, no institutional access required):
6. *LLM-Based Multi-Agent Systems for Software Engineering: Literature Review, Vision and the Road Ahead.* arXiv:2404.04834. Also published in ACM TOSEM; that version is paywalled, the arXiv version is free and equivalent.
7. *AgentBalance: Backbone-then-Topology Design for Cost-Effective Multi-Agent Systems under Budget Constraints.* arXiv:2512.11426.
8. *Human-In-the-Loop Software Development Agents.* arXiv:2411.12924.
9. *MapCoder-Lite: Distilling Multi-Agent Coding into a Single Small LLM.* arXiv:2509.17489.
10. *When Should AI Review Precede Human Approval of Agent-Generated Code?* arXiv:2603.13870.

**Tools and internal sources:**
- LangGraph documentation: `https://langchain-ai.github.io/langgraph/`
- Pydantic documentation: `https://docs.pydantic.dev/`
- Groq API documentation: `https://console.groq.com/docs`
- This project's own internal logs: `PROJECT_BRIEF.md`, `EVALUATION_AND_ROADMAP.md`, `PHASE_0_1` through `PHASE_7_PROGRESS_AND_DECISIONS.md`, `BUGFIX_CODER_RETRY_FEEDBACK.md`, `BUGFIX_4_REASONING_MODEL_TOKEN_STARVATION.md`, `BUGFIX_5_WINDOWS_UNICODE_ENCODING.md`.

---

*Rough bullet-point outline, not final prose. Next step: expand each section into full paragraphs once structure and citations are locked in.*
