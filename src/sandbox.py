"""
sandbox.py — Phase 6: subprocess execution engine for the real Tester.

Scope discipline (per EVALUATION_AND_ROADMAP.md's Phase 6 section): this
file's ONLY job is "run this one Python file in a temp directory, with a
timeout and best-effort resource limits, and hand back exactly what
happened" — stdout, stderr, exit code, whether it timed out. It knows
nothing about acceptance criteria, Specs, or PerCriterionResult; agents.py
turns this file's SandboxResult into that shape. Same separation
persistence.py already established in Phase 2 (a small file that does one
mechanical thing, with the reasoning-heavy code living elsewhere).

THREAT MODEL, stated explicitly because the roadmap asks for exactly this
("talk through what 'safe enough' means... you want to be able to explain
the tradeoff, not just have code that happens to run"):

This sandboxes arbitrary-but-not-adversarial code — output from a free-tier
LLM that is trying (and sometimes failing) to solve the given spec, not a
hostile actor deliberately trying to escape confinement. It is NOT
multi-tenant-service-grade isolation (no container, no VM, no seccomp
filter, no network namespace). What it DOES defend against, which is the
realistic failure mode here, is: an infinite loop (killed by `timeout`),
runaway memory allocation (killed by RLIMIT_AS, where available), and a
runaway CPU-bound loop that isn't literally infinite but still shouldn't
eat the whole time budget (RLIMIT_CPU). A subprocess (not a thread, not an
in-process exec()) is the one property that IS treated as non-negotiable —
generated code crashing the interpreter, monkey-patching, or aborting
uncleanly must never take down the Tester or the rest of the pipeline with
it. That's the actual bar, not "unbreakable."

CROSS-PLATFORM NOTE: `resource.setrlimit` is POSIX-only — it does not
exist on Windows, and this project's actual target machine is Windows
(confirmed: the workspace lives under a Windows OneDrive path). Rather
than pretend otherwise, this module checks `_is_posix()` and skips
the memory/CPU rlimits entirely on Windows, falling back to the
`subprocess.run(timeout=...)` wall-clock kill as the sole safety net there.
This is a real, explainable gap, not an oversight — see
PHASE_6_PROGRESS_AND_DECISIONS.md for the full writeup. It's also exactly
the kind of "legitimate resource-constrained design decision" the roadmap
says is worth being able to explain in a viva, not something to hide.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Defaults, overridable via env vars — same env-var-driven-config pattern
# PROJECT_BRIEF.md already commits to for model ids and Phase 5's retry
# budget, rather than hardcoding numbers here.
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("SDLC_TEST_TIMEOUT_SECONDS", "5"))
DEFAULT_MEMORY_LIMIT_MB = int(os.environ.get("SDLC_TEST_MEMORY_LIMIT_MB", "256"))

# Cap how much of stdout/stderr we keep — a generated test that prints in a
# loop before timing out shouldn't blow up PerCriterionResult.detail or the
# eventual traceability report with megabytes of text.
_MAX_CAPTURED_CHARS = 4000


@dataclass
class SandboxResult:
    """Everything agents.py needs to turn one execution into a
    PerCriterionResult: pass/fail is `returncode == 0 and not timed_out`,
    left for the caller to decide (this module doesn't know what a
    "criterion" is), and `stdout`/`stderr` are already truncated so callers
    can use them directly as PerCriterionResult.detail without re-checking
    length themselves.
    """

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


def _truncate(text: str) -> str:
    if len(text) <= _MAX_CAPTURED_CHARS:
        return text
    return text[:_MAX_CAPTURED_CHARS] + f"\n...[truncated, {len(text)} chars total]"


def _is_posix() -> bool:
    """Split out as its own function (rather than inlining
    `os.name == "posix"` at the call site) so tests can monkeypatch
    `sandbox._is_posix` to exercise the non-POSIX branch deterministically
    — flipping the real `os.name` attribute would affect the whole
    process (tempfile, pathlib, etc. all consult it), a much bigger blast
    radius than this one `if` needs. See test_real_tester.py's
    Windows-fallback check, which patches this function, not `os.name`
    itself, to prove the fallback branch actually runs correctly.
    """
    return os.name == "posix"


def _posix_preexec(memory_limit_mb: int, timeout_seconds: float):
    """Returns a preexec_fn that applies RLIMIT_AS (address-space/memory)
    and RLIMIT_CPU (CPU seconds) in the CHILD process, right after fork and
    before exec. Only ever called when `_is_posix()` — see module
    docstring. Runs in the child, so a failure here (e.g. a limit this
    platform's kernel won't accept) becomes a normal OSError surfaced as a
    nonzero exit / caught by the subprocess machinery, not a crash of the
    Tester itself.

    BUG FOUND AND FIXED (via test_real_tester.py's own manufactured
    infinite-loop check, which caught this on a real run — see
    PHASE_6_PROGRESS_AND_DECISIONS.md): RLIMIT_CPU used to be set to the
    SAME duration as the wall-clock `subprocess.run(timeout=...)`, using
    the module-level default rather than the actual `timeout_seconds` this
    call was given. That made the two kill mechanisms race — for a
    CPU-bound infinite loop, whichever one the kernel got to first won,
    non-deterministically. When RLIMIT_CPU won, the process was SIGKILL'd
    (returncode -9) microseconds before `subprocess.run` would have raised
    `TimeoutExpired`, so `run_sandboxed()` reported a bare "nonzero exit
    code -9" instead of the clearer "killed after exceeding Ns timeout"
    message — same underlying safety property (the loop WAS stopped), but
    a nondeterministic reason string depending on kernel scheduling.

    Fix: RLIMIT_CPU is now `timeout_seconds` (the ACTUAL value this call
    was given, not the module default) PLUS a 2-second buffer. RLIMIT_CPU
    is meant to be a backstop for the rare case where the wall-clock kill
    somehow doesn't land (e.g. the child ignores/blocks the signal
    subprocess.run sends) — giving it a buffer makes the wall-clock
    timeout deterministically win under normal conditions, and RLIMIT_CPU
    only fires as the actual last resort it was meant to be.
    """

    def _apply():
        import resource

        mem_bytes = memory_limit_mb * 1024 * 1024
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (ValueError, OSError):
            # Some platforms (notably macOS) restrict or ignore RLIMIT_AS.
            # Best-effort: the timeout below still bounds runaway CPU-bound
            # loops regardless of whether the memory limit took effect.
            pass
        try:
            cpu_seconds = max(1, int(timeout_seconds) + 2)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        except (ValueError, OSError):
            pass

    return _apply


def run_sandboxed(
    code_files: dict[str, str],
    entry_file: str,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
) -> SandboxResult:
    """Write every (filename -> content) pair in `code_files` into a fresh
    temp directory, then run `entry_file` (must be a key in `code_files`)
    as `python <entry_file>` with cwd set to that directory, so imports
    between the generated files (`import solution` from a test file, say)
    resolve naturally without any path hacking.

    Isolation properties, explicitly:
      - A FRESH temp directory per call — no state leaks between criteria
        or between Coder retry attempts.
      - A subprocess, not an in-process exec/eval — a segfault, an
        os._exit(), or a genuinely broken interpreter state in generated
        code cannot touch the Tester's own process.
      - `subprocess.run(timeout=...)` — cross-platform, kills the process
        tree on timeout via Python's own machinery. This is the ONLY
        safety net on Windows (see module docstring).
      - On POSIX only: RLIMIT_AS + RLIMIT_CPU via preexec_fn, as a second,
        stronger line of defense against runaway memory/CPU specifically
        (a fork-bomb-shaped or memory-leaking generated "test" is stopped
        before the wall-clock timeout would even fire).

    Never raises for "the generated code failed" — that's an ordinary
    nonzero returncode, not a sandbox failure. It DOES let a real
    filesystem-level error (e.g. can't create the temp dir at all) raise,
    since that's an environment problem this function can't paper over.
    """
    if entry_file not in code_files:
        raise ValueError(f"entry_file {entry_file!r} is not among the provided code_files")

    with tempfile.TemporaryDirectory(prefix="sdlc_sandbox_") as tmpdir:
        tmp_path = Path(tmpdir)
        for filename, content in code_files.items():
            # BUG #5: same Windows-default-encoding issue as
            # persistence.py/report.py -- LLM-generated source (Coder's
            # code, Tester's test scripts) can contain non-ASCII
            # punctuation and must be written as UTF-8 explicitly, not the
            # OS locale default.
            (tmp_path / filename).write_text(content, encoding="utf-8")

        kwargs: dict = {}
        if _is_posix():
            kwargs["preexec_fn"] = _posix_preexec(memory_limit_mb, timeout_seconds)
        # else: Windows — no rlimits available; timeout below is the sole
        # backstop. Documented as a real, known limitation, not silently
        # patched over with something that only looks cross-platform.

        # BUG #5 continued: capture_output+text=True decodes the CHILD
        # process's stdout/stderr using the OS locale default too (cp1252 on
        # Windows), which can raise UnicodeDecodeError if the generated code
        # prints non-ASCII -- and separately, the child Python interpreter
        # itself defaults to that same locale encoding for ITS stdout/stderr,
        # so a generated script that prints non-ASCII could crash with its
        # own UnicodeEncodeError before this function even gets a chance to
        # decode anything. Fixed on both sides: encoding="utf-8" here, and
        # PYTHONIOENCODING=utf-8 forced into the child's environment so the
        # generated code's own stdout/stderr streams are UTF-8 too.
        sandbox_env = dict(os.environ)
        sandbox_env["PYTHONIOENCODING"] = "utf-8"

        try:
            proc = subprocess.run(
                [sys.executable, entry_file],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                env=sandbox_env,
                **kwargs,
            )
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout or b"").decode(errors="replace")
            stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr or b"").decode(errors="replace")
            return SandboxResult(
                returncode=-1,
                stdout=_truncate(stdout),
                stderr=_truncate(
                    stderr + f"\n[sandbox] killed after exceeding {timeout_seconds}s timeout "
                    "(likely an infinite loop or unbounded blocking call)."
                ),
                timed_out=True,
            )

        return SandboxResult(
            returncode=proc.returncode,
            stdout=_truncate(proc.stdout),
            stderr=_truncate(proc.stderr),
            timed_out=False,
        )
