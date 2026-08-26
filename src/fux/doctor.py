"""`fux doctor` — install/environment health check.

Checks today: python version, repo root found, `.fux/` writable, and the two
layout assertions from ADR-DOTFUX — the committed index is not git-ignored, and
nothing undeclared sits at the top level of `.fux/`.

The index check exists because the failure it catches is silent: a `.fux/*`
line in any `.gitignore` up the tree, or a consumer-edited `.fux/.gitignore`,
drops the committed index out of git with no error anywhere. Doctor stays
offline — it never touches the fetcher or the network.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import find_root
from .store import fuxdir

PY_MIN = (3, 11)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    level: str = "error"  # "error" fails the command; "warn" only reports


def run(start: Path | None = None) -> list[Check]:
    checks = [_python_version(), *_repo_root(start)]
    return checks


def _background_runner(root: Path) -> Check:
    """The deferred re-index, reported and never repaired (W-66 Phase 4).

    ADR-MAINTENANCE decision 1c: `post-commit` spawns a detached process that
    exits, so without this the whole maintenance path is invisible — a runner
    that died leaves the dirty list intact and says nothing at all. Four
    questions, one line: is one live and which pid, how many documents are
    pending, is the lock held or stale, and did the last run fail.

    **Read-only, and that is the decision rather than an omission.** A stale
    lock is *named* along with the command that clears it; this never clears
    it. Clearing a lock whose owner is actually alive puts two runners inside
    `.fux/index/` at once, which is the single failure the lock exists to
    prevent — decision 1c's veto 7. The logic lives in `maintain/runner.py`
    (ADR-MAINTENANCE's component); this function only renders it.

    A **warning**, never an error: a pending re-index means the index is late,
    which is the deferring hook working as designed, not a broken repo.
    """
    from .maintain import runner

    state = runner.status(root)
    pending = state["pending"]
    last = state["last_run"] or {}

    if state["lock"] == "stale":
        return Check(
            "background runner",
            False,
            f"a lock is held by pid {state['pid']}, which is not running - a re-index was "
            f"killed. {pending} changed path(s) pending. Run `fux ingest --stop` to clear it, "
            f"or delete {state['lock_path']}",
            level="warn",
        )
    if state["running"]:
        return Check(
            "background runner",
            True,
            f"running (pid {state['pid']}), {pending} changed path(s) pending",
            level="warn",
        )
    if last.get("outcome") == "failed":
        return Check(
            "background runner",
            False,
            f"the last background re-index FAILED ({last.get('error', 'no detail recorded')}). "
            f"{pending} changed path(s) pending - run `fux ingest` to see the error",
            level="warn",
        )
    if pending:
        return Check(
            "background runner",
            True,
            f"idle, {pending} changed path(s) pending - run `fux ingest` to catch up",
            level="warn",
        )
    return Check("background runner", True, "idle, nothing pending", level="warn")


def _python_version() -> Check:
    ok = sys.version_info[:2] >= PY_MIN
    have = f"{sys.version_info.major}.{sys.version_info.minor}"
    return Check(
        "python version",
        ok,
        f"{have} (need >= {'.'.join(map(str, PY_MIN))})" if not ok else f"{have}, fux {__version__}",
    )


def _repo_root(start: Path | None) -> list[Check]:
    root = find_root(start)
    if root is None:
        return [Check("repo root", False, "no fux.toml or .git found above the current directory")]
    checks = [Check("repo root", True, str(root))]
    fux_dir = root / ".fux"
    try:
        fux_dir.mkdir(exist_ok=True)
        probe = fux_dir / ".doctor-probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        checks.append(Check(".fux/ writable", True, str(fux_dir)))
    except OSError as exc:
        checks.append(Check(".fux/ writable", False, str(exc)))
    checks.extend(_layout(root))
    return checks


def _layout(root: Path) -> list[Check]:
    """ADR-DOTFUX: the index must not be ignored; `.fux/` holds only declared entries."""
    checks: list[Check] = []
    ignored = _is_git_ignored(root, root / fuxdir.FUX_DIR / "index")
    if ignored is None:
        checks.append(Check("index not gitignored", True, "skipped (not a git checkout)"))
    else:
        checks.append(
            Check(
                "index not gitignored",
                not ignored,
                ".fux/index is committed, not derived - remove the ignore rule "
                "(a `.fux/*` blanket is the usual cause)"
                if ignored
                else "the committed index is tracked",
            )
        )

    fux_dir = root / fuxdir.FUX_DIR
    extras = sorted(p.name for p in fux_dir.iterdir() if p.name not in fuxdir.DECLARED) if fux_dir.is_dir() else []
    checks.append(
        Check(
            ".fux/ layout declared",
            not extras,
            f"undeclared entries: {', '.join(extras)} - see .fux/README.md and ADR-DOTFUX"
            if extras
            else "every entry is declared",
            level="warn",
        )
    )
    checks.append(_accelerator(root))
    checks.append(_background_runner(root))
    checks.append(_url_health(root))
    return checks


def _url_health(root: Path) -> Check:
    """The `url:` half of the corpus, reported (W-82 §3.1).

    Doctor had **no URL check at all**, which is the defect: a URL that has
    failed every fetch for a month looked exactly like one fetched a minute ago.
    [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision 4 keeps the
    prior record on a failed fetch — correct, because a flaky network must never
    present as a deletion — and the cost of that rule is that **a permanently
    dead URL lives in the index forever**. This makes the cost visible.

    **Report, never auto-delete**, and **never fetch**: doctor stays offline
    (this module's contract), so every number here comes from the committed
    index and a gitignored counter file. It says what the last networked run
    saw; it does not go looking.

    A **warning**, never an error. A stale or failing URL means the index is
    behind, which is a fact about the world rather than a broken install, and
    reporting it as a failure would train people to ignore a red doctor —
    the same reasoning `_accelerator` records.
    """
    from .maintain import urlstate

    try:
        from .store import reader

        indexed = [doc_id[4:] for doc_id in reader.read_index(root) if doc_id.startswith("url:")]
    except Exception:
        # An unreadable or absent index is another check's business, not this
        # one's. Reporting "cannot tell" beats a traceback on a health command.
        return Check("url sources", True, "skipped (no readable index)", level="warn")

    summary = urlstate.summarize(urlstate.read(root), indexed)
    if not summary.has_urls:
        return Check("url sources", True, "none indexed", level="warn")

    parts = [f"{summary.indexed} url: record(s)"]
    if summary.run_seq == 0:
        parts.append("no networked run recorded yet - run `fux update`")
    else:
        parts.append(f"{summary.confirmed_last_run} confirmed by the last run")
    if summary.never_confirmed:
        parts.append(f"{summary.never_confirmed} never re-fetched since first ingest")
    if summary.failing:
        parts.append(f"{summary.failing} failing")
    detail = ", ".join(parts)
    if summary.failing_urls:
        # Named, not just counted: a count tells you something is wrong and a
        # name tells you which line of `.fux/sources/urls` to go and look at.
        listed = ", ".join(summary.failing_urls[:5])
        more = f" (+{len(summary.failing_urls) - 5} more)" if len(summary.failing_urls) > 5 else ""
        detail += (
            f" - failed {urlstate.FAILING_STREAK}+ runs in a row: {listed}{more}. "
            "fux never deletes a URL record; remove the line from .fux/sources/urls yourself"
        )
    return Check("url sources", not summary.failing_urls, detail, level="warn")


def _accelerator(root: Path) -> Check:
    """The derived accelerator: present, fresh, and genuinely not committed.

    A **warning**, never an error. The accelerator is disposable by design —
    `ask` answers correctly from the scan without it — so a missing or stale
    one costs speed, not correctness. Reporting it as a failure would train
    people to ignore a red doctor.
    """
    from .derive import format as derive_fmt
    from .derive.accel import is_fresh

    directory = derive_fmt.runtime_dir(root)
    if not (directory / derive_fmt.STATS_NAME).exists():
        return Check(
            "accelerator",
            True,
            "not built - `ask` uses the reference scan; run `fux build` for the fast path",
            level="warn",
        )

    tracked = _is_git_tracked(root, directory)
    if tracked:
        return Check(
            "accelerator",
            False,
            ".fux/runtime/ is TRACKED by git - it is a derived plane and must not be "
            "committed; check .fux/.gitignore lists `runtime/` (ADR-DOTFUX)",
            level="warn",
        )

    if not is_fresh(root):
        return Check(
            "accelerator",
            True,
            "stale (the committed index changed since it was built) - `ask` falls back "
            "to the scan; run `fux build`",
            level="warn",
        )
    return Check("accelerator", True, f"fresh, derived, untracked ({directory})", level="warn")


def _is_git_tracked(root: Path, path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(path)],
            cwd=root,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _is_git_ignored(root: Path, path: Path) -> bool | None:
    """True/False from `git check-ignore`, or None when git can't answer."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", str(path)],
            cwd=root,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None  # 128: not a repository, or any other git failure


def cmd_doctor(args) -> int:
    checks = run()
    exit_code = 0 if all(c.ok for c in checks if c.level == "error") else 1

    if getattr(args, "json", False):
        # W-66 Phase 4 / ADR-CLI, 2026-08-22: `doctor` had no machine-readable
        # form, and a status an agent cannot parse is not a status for this
        # product's actual audience. The runner block is lifted out beside the
        # checks rather than left as prose inside `detail`, because a caller
        # asking "is a re-index pending" should not have to parse a sentence.
        import json as json_mod

        from .config import find_root

        root = find_root()
        payload = {
            "ok": exit_code == 0,
            "version": __version__,
            "checks": [
                {"name": c.name, "ok": c.ok, "level": c.level, "detail": c.detail} for c in checks
            ],
        }
        if root is not None:
            from .maintain import runner

            payload["runner"] = runner.status(root)
        print(json_mod.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    for check in checks:
        # ASCII only — Windows' default console codepage (cp1252/"charmap")
        # can't encode U+2714/U+2717 and the process crashes on print()
        # rather than degrading; caught by CI's windows runners.
        mark = "OK" if check.ok else ("WARN" if check.level == "warn" else "FAIL")
        print(f"[{mark}] {check.name}: {check.detail}")
    return exit_code
