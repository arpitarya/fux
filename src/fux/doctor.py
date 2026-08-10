"""`fux doctor` — install/environment health check.

M0 scope: three checks (python version, repo root found, `.fux/` writable).
Grows per-plane checks (config, corpus, consistency) as those planes land.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import find_root

PY_MIN = (3, 11)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


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
    return checks


def cmd_doctor(args) -> int:
    checks = run()
    for check in checks:
        mark = "✔" if check.ok else "✗"
        print(f"{mark} {check.name}: {check.detail}")
    return 0 if all(c.ok for c in checks) else 1
