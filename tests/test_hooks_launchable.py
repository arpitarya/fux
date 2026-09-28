"""Every hook `.claude/settings.json` registers can be LAUNCHED — `100755` in git.

[W-230](../archive/open/W-230-l11-breach-2026-09-28.md), ruled by Arpit on
2026-09-28. ``guard-golden-traversal.sh`` was committed ``100644`` by W-223 and
stayed that way for three days. Claude Code launches a hook by path; a file
that is not executable fails to launch, that failure is non-blocking, and the
command runs. Two walks over ``work/`` ran live (W-227, W-230) while every
offline replay — which fed the hook to ``bash`` — denied them.

🔴 **The mode git carries is the one that decides**, because it is what every
checkout gets; the working-tree bit is asserted too on posix, because a live
session launches the file on disk. This is the two-strikes gate
(SR-WORK-SESSION decision 13), and it needs neither bash nor jq, so it never
skips.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"
PREFIX = "$CLAUDE_PROJECT_DIR/"


def _registered() -> list[str]:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    out: set[str] = set()
    for groups in settings.get("hooks", {}).values():
        for group in groups:
            for hook in group["hooks"]:
                if hook.get("type") != "command":
                    continue
                cmd = hook["command"].split()[0]
                assert cmd.startswith(PREFIX), f"hook `{cmd}` is not launched from the project dir"
                out.add(cmd[len(PREFIX):])
    return sorted(out)


def _tracked_hooks() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--", ".claude/hooks"], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.split()
    return sorted(p for p in out if p.endswith(".sh"))


def _git_mode(rel: str) -> str:
    entry = subprocess.run(
        ["git", "ls-files", "-s", "--", rel], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.split()
    return entry[0] if entry else "untracked"


def test_settings_registers_hooks():
    assert _registered(), "no hook is registered — this gate would pass vacuously"


@pytest.mark.parametrize("rel", sorted(set(_registered()) | set(_tracked_hooks())))
def test_the_hook_is_committed_executable(rel):
    """Registered or not: `just golden-unlock` deregisters three guards, and
    `just golden-lock` must bring back files that can run."""
    assert (ROOT / rel).is_file(), f"`{rel}` is registered but missing — a hook that cannot launch is skipped"
    mode = _git_mode(rel)
    assert mode == "100755", (
        f"`{rel}` is committed as {mode}, not 100755. Claude Code launches a hook "
        "by path; a non-executable one fails to launch and the tool call PROCEEDS. "
        "Fix: chmod +x and `git update-index --chmod=+x`."
    )
    if os.name != "nt":
        assert (ROOT / rel).stat().st_mode & 0o111, f"`{rel}` is not executable on disk"
