#!/usr/bin/env python3
"""Keep work/MACHINE.md's disk budget — law L14 (SR-LAW-14).

    disk-budget.py pre     PreToolUse: ask before an action that could grow the
                           project into a GB nobody approved
    disk-budget.py post    PostToolUse: record a yes; say so when the project
                           has grown past what was approved
    disk-budget.py fresh   measure now and print usage against the ceiling;
                           exit 1 when past it (the veto check)

**The number lives in `work/MACHINE.md`'s `budget` row and nowhere else**
(decision 1). What counts (decision 2): the repository — its `.git` and every
worktree under it — plus every git worktree outside it. Under the budget nothing
is asked; past it, one yes approves exactly one more GB, and an Agent call or a
new worktree asks from 90 % of the approved ceiling (decision 3). Back under the
budget, the approvals are forgotten. A measurement is reused for 60 seconds.

Never blocks on its own failure: an error here prints nothing and exits 0, so a
broken hook degrades to the Cowork rule (measure by hand) rather than to a wall.
Stdlib only.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MACHINE = ROOT / "work" / "MACHINE.md"
USAGE = ROOT / ".claude" / ".disk-usage"
STATE = ROOT / ".claude" / ".disk-nudged"
REUSE_S = 60
GB = 1024 * 1024  # in KiB, what `du -sk` reports
SPAWNS = {"Agent", "Task", "EnterWorktree"}
#: Tools that can grow the disk. Reads and searches never ask.
GROWS = SPAWNS | {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"}


def budget_gb(text: str | None = None) -> int:
    text = MACHINE.read_text(encoding="utf-8") if text is None else text
    m = re.search(r"^\|\s*budget\s*\|\s*(\d+)\s*GB\b", text, re.M)
    if not m:
        raise ValueError("work/MACHINE.md has no `| budget | <n> GB` row")
    return int(m.group(1))


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _roots() -> list[Path]:
    """The repository, plus every worktree that lives outside it."""
    out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    roots = [ROOT]
    for line in out.splitlines():
        if line.startswith("worktree "):
            p = Path(line[9:]).resolve()
            if p != ROOT.resolve() and ROOT.resolve() not in p.parents and p.is_dir():
                roots.append(p)
    return roots


def usage_kb(fresh: bool = False) -> int:
    cached = _load(USAGE)
    if not fresh and time.time() - cached.get("at", 0) < REUSE_S:
        return int(cached["kb"])
    total = 0
    for root in _roots():
        out = subprocess.run(["du", "-sk", str(root)], capture_output=True, text=True).stdout
        total += int(out.split()[0]) if out.split() else 0
    _save(USAGE, {"at": time.time(), "kb": total})
    return total


def ceiling_gb(budget: int, used_kb: int) -> int:
    """The approved ceiling — reset to the budget once usage is back under it."""
    state = _load(STATE)
    if used_kb < budget * GB:
        if state:
            _save(STATE, {})
        return budget
    return max(budget, int(state.get("approved_gb", budget)))


def _gb(kb: int) -> str:
    return f"{kb / GB:.1f} GB"


def pre(event: dict) -> dict | None:
    tool = event.get("tool_name", "")
    if tool not in GROWS:
        return None
    budget = budget_gb()
    used = usage_kb()
    ceiling = ceiling_gb(budget, used)
    spawn = tool in SPAWNS or (tool == "Bash" and "worktree add" in str(event.get("tool_input", {}).get("command", "")))
    threshold = ceiling * GB * (0.9 if spawn else 1.0)
    if used < threshold:
        return None
    state = _load(STATE)
    state.update(pending_gb=ceiling + 1, pending_id=event.get("tool_use_id"))
    _save(STATE, state)
    why = "a new agent or worktree asks from 90 % of the ceiling" if spawn else "the next growth is unapproved"
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"Disk budget (L14, work/MACHINE.md): the project uses {_gb(used)} of {ceiling} GB "
            f"approved (budget {budget} GB); {why}. Yes approves exactly one more GB "
            f"(ceiling → {ceiling + 1} GB)."),
    }}


def post(event: dict) -> dict | None:
    state = _load(STATE)
    if state.get("pending_gb") and state.get("pending_id") == event.get("tool_use_id"):
        state["approved_gb"] = state.pop("pending_gb")
        state.pop("pending_id", None)
        _save(STATE, state)
    if event.get("tool_name", "") not in GROWS:
        return None
    budget = budget_gb()
    used = usage_kb()
    ceiling = ceiling_gb(budget, used)
    if used <= ceiling * GB:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": (
            f"⚠ Disk budget (L14): the project has grown to {_gb(used)}, past the {ceiling} GB "
            "approved. The next growing action asks Arpit for one more GB."),
    }}


def fresh() -> int:
    budget = budget_gb()
    used = usage_kb(fresh=True)
    ceiling = ceiling_gb(budget, used)
    print(f"disk: {_gb(used)} used · budget {budget} GB · approved ceiling {ceiling} GB")
    return 0 if used <= ceiling * GB else 1


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "fresh":
        return fresh()
    if cmd not in ("pre", "post"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        event = json.loads(sys.stdin.read() or "{}")
        out = pre(event) if cmd == "pre" else post(event)
    except Exception:  # never a wall on the hook's own failure
        return 0
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
