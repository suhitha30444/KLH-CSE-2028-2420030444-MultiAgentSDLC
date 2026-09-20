"""
report.py — Phase 7: the traceability report generator (the payoff).

Scope discipline (per EVALUATION_AND_ROADMAP.md's Phase 7 section, which
explicitly says "a function producing markdown is enough"): this file is
ONE function that takes the finished pieces of a run — Spec,
CodeArtifacts, PerCriterionResults, ReviewVerdicts — and renders the
literal chain the roadmap's "impressive core" item #3 asks for:

    requirement -> acceptance criterion -> task -> code -> test result
    -> review verdict

for one real run, "readable without narration" — i.e. someone who wasn't
in the room should be able to follow it unaided. No new agent, no new
graph node, no LLM call of its own: everything it needs is already sitting
in SDLCState by the time a run reaches DONE or FAILED (see main.py, which
calls this after graph.invoke() returns).
"""

from __future__ import annotations

from pathlib import Path

from state import CodeArtifact, PerCriterionResult, RetryCounters, ReviewVerdict, Spec

_MAX_CODE_CHARS_IN_REPORT = 1500  # keep one artifact's listing from swamping the report


def _truncate_code(content: str) -> str:
    if len(content) <= _MAX_CODE_CHARS_IN_REPORT:
        return content
    return content[:_MAX_CODE_CHARS_IN_REPORT] + f"\n# ...[truncated, {len(content)} chars total]"


def generate_traceability_report(
    spec: Spec,
    code_artifacts: list[CodeArtifact],
    test_results: list[PerCriterionResult],
    review_verdicts: list[ReviewVerdict],
    *,
    final_status: str,
    retries: RetryCounters | None = None,
) -> str:
    """Render one run as markdown, one section per acceptance criterion,
    each section walking the FULL chain for that criterion specifically —
    not one global code dump and one global test summary side by side,
    which would leave the reader to do the criterion-to-code matching
    themselves (exactly the "chain of custody" gap the roadmap's Phase 7
    "Using Claude" tip warns about: "would someone reading it understand
    the chain... without you narrating").

    DECISION: tasks/code/tests/verdicts are matched to each criterion by
    id (TaskItem.addresses_criteria, CodeArtifact.task_id,
    PerCriterionResult.criterion_id, ReviewVerdict.criterion_id) — the
    exact link state.py's docstrings describe each of those fields as
    existing for. A criterion with no matching task, code, test result,
    or verdict yet (e.g. the run failed before reaching that stage) is
    rendered as "(none)" rather than silently omitted — a reader should
    see WHERE the chain broke, not just the parts that happened to exist.

    `retries` is optional (kept that way so existing callers/tests that
    don't have a RetryCounters handy — e.g. report-only unit tests that
    build a fixture without a full graph run — don't need to change) but
    SHOULD be passed for any real run. Without it, the report shows only
    the FINAL attempt's results, which can understate what actually
    happened: a run that failed once, hit a live Groq JSON error once,
    then recovered on a third attempt renders identically to one that
    passed cleanly on the first try unless the retry count is shown
    alongside it. See PHASE_7_PROGRESS_AND_DECISIONS.md's "Live-mode
    report generated, one known limitation surfaced by it" for the real
    run that exposed this gap.
    """
    lines: list[str] = []
    lines.append(f"# Traceability Report — run `{spec.run_id}`")
    lines.append("")
    lines.append(f"**Final status:** {final_status}")
    lines.append("")
    if retries is not None:
        lines.append(
            f"**Retries spent:** spec_approval={retries.spec_approval_retries}/"
            f"{retries.max_spec_approval_retries}, "
            f"test_review={retries.test_review_retries}/"
            f"{retries.max_test_review_retries}"
        )
        if retries.test_review_retries > 0:
            lines.append(
                f"*({retries.test_review_retries} Coder/Tester/Reviewer attempt(s) "
                "were rejected before this final one — see the criteria below for "
                "the ACCEPTED attempt only; earlier attempts' specific failures "
                "aren't retained by this report, only their count.)*"
            )
        lines.append("")
    lines.append(f"**Requirement:** {spec.requirement}")
    lines.append("")
    lines.append(
        "Each section below follows ONE acceptance criterion end to end: "
        "the task(s) meant to satisfy it, the code that resulted, the real "
        "test executed against it, and the Reviewer's verdict."
    )
    lines.append("")

    test_by_id = {r.criterion_id: r for r in test_results}
    verdict_by_id = {v.criterion_id: v for v in review_verdicts}

    for criterion in spec.acceptance_criteria:
        lines.append(f"## {criterion.id}: {criterion.text}")
        lines.append("")

        tasks = [t for t in spec.tasks if criterion.id in t.addresses_criteria]
        lines.append("**Task(s):**")
        if tasks:
            for t in tasks:
                lines.append(f"- `{t.id}` — {t.description}")
        else:
            lines.append("- (none — no task in the spec named this criterion)")
        lines.append("")

        task_ids = {t.id for t in tasks}
        artifacts = [a for a in code_artifacts if a.task_id in task_ids]
        fell_back = False
        # Only fall back when this criterion genuinely HAS a task meant to
        # address it (`tasks` non-empty) but the strict task_id match still
        # came up empty -- that's the Coder-consolidated-one-file case this
        # bug fix targets. A criterion with NO task at all is a different,
        # real gap (nothing was ever planned to address it) and should
        # keep saying so, not get an arbitrary pile of unrelated code.
        if not artifacts and code_artifacts and tasks:
            # BUG #6 (found live: a run reached DONE, 5/5 criteria passed
            # and approved, and the report STILL showed "(none — no code
            # artifact was linked)" for every single criterion). Root
            # cause: CodeArtifact.task_id can only hold ONE task id, but
            # run_coder()'s own prompt tells the Coder to "prefer ONE
            # consolidated file... even if multiple tasks address it" --
            # so the moment the Coder does exactly that, every task EXCEPT
            # the one task_id it happened to pick comes up with zero
            # matching artifacts, even though the code plainly exists and
            # plainly satisfies the criterion (the real sandboxed test
            # result right below proves it). Rather than keep reporting a
            # true statement ("no artifact's task_id matched") that reads
            # as a false one ("no code exists for this"), fall back to
            # showing every artifact from the run when the strict
            # per-task match comes up empty but code was produced at all --
            # labeled as a fallback so the distinction isn't hidden.
            artifacts = code_artifacts
            fell_back = True
        lines.append("**Code:**")
        if artifacts:
            if fell_back:
                lines.append(
                    "*(no code artifact's task_id matched this criterion's "
                    "task(s) exactly — showing every file the Coder "
                    "produced this run, since the test result below "
                    "confirms which one actually satisfies it)*"
                )
                lines.append("")
            for a in artifacts:
                lines.append(f"`{a.filename}`:")
                lines.append("```python")
                lines.append(_truncate_code(a.content))
                lines.append("```")
        elif not tasks:
            lines.append("- (none — no task in the spec named this criterion, so no code was written for it)")
        else:
            lines.append("- (none — the Coder produced no code artifacts at all this run)")
        lines.append("")

        result = test_by_id.get(criterion.id)
        lines.append("**Test result:**")
        if result is not None:
            mark = "PASS" if result.passed else "FAIL"
            lines.append(f"- **{mark}** — {result.detail}")
        else:
            lines.append("- (none — this criterion was never reached by the Tester)")
        lines.append("")

        verdict = verdict_by_id.get(criterion.id)
        lines.append("**Review verdict:**")
        if verdict is not None:
            mark = "APPROVED" if verdict.approved else "REJECTED"
            lines.append(f"- **{mark}** — {verdict.justification}")
        else:
            lines.append("- (none — this criterion was never reached by the Reviewer)")
        lines.append("")

    return "\n".join(lines)


def save_report(
    spec: Spec,
    code_artifacts: list[CodeArtifact],
    test_results: list[PerCriterionResult],
    review_verdicts: list[ReviewVerdict],
    *,
    final_status: str,
    retries: RetryCounters | None = None,
    reports_dir: str | Path = "reports",
) -> Path:
    """Render and write the report to <reports_dir>/report_<run_id>.md,
    mirroring persistence.py's save_spec() shape (same data_dir-creation
    pattern, same <thing>_<run_id> naming) rather than inventing a new
    convention for the second file type this project persists to disk.
    """
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"report_{spec.run_id}.md"
    markdown = generate_traceability_report(
        spec,
        code_artifacts,
        test_results,
        review_verdicts,
        final_status=final_status,
        retries=retries,
    )
    # BUG #5: same Windows-default-encoding crash as persistence.py -- see
    # its comment. The report embeds the same LLM-generated criteria text
    # (and code/test details), so it is equally exposed to non-ASCII
    # punctuation the model may have produced.
    path.write_text(markdown + "\n", encoding="utf-8")
    return path
