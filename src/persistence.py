"""
persistence.py — Phase 2: writing a validated Spec to disk.

A persisted spec goes in specs/ — the folder that already exists in the
real repo for exactly this purpose (confirmed against the actual workspace
2026-09-16; earlier drafts of this file assumed a /data folder that turned
out not to exist — see claude/PHASE_2_PROGRESS_AND_DECISIONS.md).
"""

from __future__ import annotations

from pathlib import Path

from state import CodeArtifact, Spec


def save_spec(spec: Spec, data_dir: str | Path = "specs") -> Path:
    """Write `spec` to <data_dir>/spec_<run_id>.json (pretty-printed) and
    return the path written. Creates data_dir if it doesn't exist yet
    (though in the real repo, specs/ already exists).

    Only ever called with an already-validated Spec — run_planner() in
    agents.py raises PlannerOutputError before a bad one gets this far, so
    this function doesn't re-validate anything; it just serializes.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"spec_{spec.run_id}.json"
    # BUG #5 (found live: a Planner-generated acceptance criterion used a
    # Unicode non-breaking hyphen, U+2011 '\u2011', which crashed
    # Path.write_text() on Windows with UnicodeEncodeError -- Windows'
    # write_text() defaults to the OS locale encoding (often cp1252), not
    # UTF-8 like Linux/macOS. LLM output routinely contains non-ASCII
    # punctuation (en/em dashes, smart quotes, non-breaking hyphens), so an
    # explicit encoding is required here, not optional.
    path.write_text(spec.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def save_code_artifacts(
    run_id: str,
    code_artifacts: list[CodeArtifact],
    data_dir: str | Path = "code",
) -> Path | None:
    """BUG #6 (found live: a run reached DONE with 5/5 criteria passed and
    approved, but there was no way to actually show anyone the resulting
    code -- it only ever existed in memory for the duration of the run.
    report.py's traceability report tries to embed it inline, but that
    depends on CodeArtifact.task_id exactly matching a task in the spec,
    which silently fails whenever the Coder does exactly what its own
    prompt asks for -- "prefer ONE consolidated file... even if multiple
    tasks address it" -- since one artifact can only carry ONE task_id.
    The live report from this exact run showed "(none — no code artifact
    was linked)" for every single criterion despite the code genuinely
    existing and genuinely passing every test.

    This writes every CodeArtifact's actual content to
    <data_dir>/<run_id>/<filename> so there is always a real, openable,
    runnable file on disk after a run -- independent of whether the
    report's per-criterion linking succeeds. Returns the directory written
    to, or None if there were no code artifacts to save (e.g. a run that
    failed before the Coder ever produced anything).
    """
    if not code_artifacts:
        return None
    run_dir = Path(data_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for artifact in code_artifacts:
        # Same Windows cp1252-default crash as save_spec() above -- explicit
        # UTF-8 required, not optional, for the same reason.
        (run_dir / artifact.filename).write_text(artifact.content, encoding="utf-8")
    return run_dir
