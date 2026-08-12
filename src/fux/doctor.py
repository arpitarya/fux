"""`fux doctor` — install/environment health check.

Checks today: python version, repo root found, `.fux/` writable, and the two
layout assertions from ADR-0011 — the committed index is not git-ignored, and
nothing undeclared sits at the top level of `.fux/`.

The index check exists because the failure it catches is silent: a `.fux/*`
line in any `.gitignore` up the tree, or a consumer-edited `.fux/.gitignore`,
drops the committed index out of git with no error anywhere. Doctor stays
offline — it never touches the middleware or the network.
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
    """ADR-0011: the index must not be ignored; `.fux/` holds only declared entries."""
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
            f"undeclared entries: {', '.join(extras)} - see .fux/README.md and ADR-0011"
            if extras
            else "every entry is declared",
            level="warn",
        )
    )
    checks.append(_accelerator(root))
    return checks


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
            "committed; check .fux/.gitignore lists `runtime/` (ADR-0011)",
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
    for check in checks:
        # ASCII only — Windows' default console codepage (cp1252/"charmap")
        # can't encode U+2714/U+2717 and the process crashes on print()
        # rather than degrading; caught by CI's windows runners.
        mark = "OK" if check.ok else ("WARN" if check.level == "warn" else "FAIL")
        print(f"[{mark}] {check.name}: {check.detail}")
    return 0 if all(c.ok for c in checks if c.level == "error") else 1
