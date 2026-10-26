#!/usr/bin/env python3
"""Disk budget — the repository's disk-budget law (L9 in codelaw, L14 in fux and
sheetpane; the record that owns this hook says which).

The budget lives in one place, work/MACHINE.md §Disk budget's `budget` row.
What counts is the whole project: the repo (its .git and every worktree under
it), every worktree outside it, and a CARGO_TARGET_DIR outside it.

    pre     PreToolUse   — an action that would grow the project into an
                           unapproved GB raises a permission prompt
    post    PostToolUse  — a yes approves exactly one GB; says so the moment
                           the project has grown past what was approved
    prompt  UserPromptSubmit — shows the usage from 80 % of the budget
    fresh   by hand      — measures now and prints; exit 1 past the ceiling

Hook input is JSON on stdin. A measurement is reused for 60 seconds.
"""
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".claude" / ".disk-usage"
NUDGED = ROOT / ".claude" / ".disk-nudged"
MACHINE = ROOT / "work" / "MACHINE.md"
CACHE_S = 60

# Decision 3: a new sub-agent or worktree asks from 90 % of the ceiling.
NEW_TOOLS = {"Agent", "Task", "EnterWorktree"}
GROWS = re.compile(
    r"\b(cargo|rustup|npm|npx|pnpm|yarn|bun|pip3?|uv|maturin|poetry|make|cmake"
    r"|docker|tar|unzip|curl|wget|python3? -m (pip|build|venv)"
    r"|git (worktree add|clone|fetch|pull|lfs))\b")
NEW_BASH = re.compile(r"\bgit worktree add\b")


def budget_gb():
    try:
        text = MACHINE.read_text(encoding="utf-8")
    except OSError:
        return 5.0
    m = re.search(r"^\|\s*budget\s*\|\s*([\d.]+)\s*GB", text, re.M)
    return float(m.group(1)) if m else 5.0


def load():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"ts": 0, "kb": 0, "approved_gb": 0, "pending": {}}


def save(st):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st), encoding="utf-8")
    os.replace(tmp, STATE)


def du_kb(path):
    r = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True)
    try:
        return int(r.stdout.split()[0])
    except (IndexError, ValueError):
        return 0


def inside(p):
    try:
        Path(p).resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def measure():
    """Decision 2: the repo, worktrees outside it, a target dir outside it."""
    kb = du_kb(ROOT)
    out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("worktree "):
            p = line[9:]
            if not inside(p) and Path(p).is_dir():
                kb += du_kb(p)
    target = os.environ.get("CARGO_TARGET_DIR")
    if target and Path(target).is_dir() and not inside(target):
        kb += du_kb(target)
    return kb


def usage(st, fresh=False):
    if fresh or time.time() - st.get("ts", 0) > CACHE_S:
        st["kb"], st["ts"] = measure(), time.time()
    gb = st["kb"] / 1024 / 1024
    budget = budget_gb()
    if gb < budget:
        # Back under the budget, the approvals are forgotten.
        st["approved_gb"] = 0
        NUDGED.unlink(missing_ok=True)
    return gb, budget, max(budget, st.get("approved_gb", 0))


def emit(event, **fields):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, **fields}}))


def growing(tool, inp):
    """'new' (a sub-agent or worktree), 'grow' (a build or install) or None."""
    if tool in NEW_TOOLS:
        return "new"
    if tool == "Bash":
        cmd = inp.get("command", "")
        if NEW_BASH.search(cmd):
            return "new"
        if GROWS.search(cmd):
            return "grow"
    return None


def pre(hook, st):
    kind = growing(hook.get("tool_name", ""), hook.get("tool_input") or {})
    if not kind:
        return
    gb, budget, ceiling = usage(st)
    threshold = ceiling * 0.9 if kind == "new" else ceiling
    if gb < threshold:
        return
    need = math.floor(gb) + 1 if gb >= ceiling else int(ceiling) + 1
    now = time.time()
    st["pending"] = {k: v for k, v in st.get("pending", {}).items() if now - v["ts"] < 3600}
    st["pending"][hook.get("tool_use_id", "")] = {"gb": need, "ts": now}
    emit("PreToolUse", permissionDecision="ask", permissionDecisionReason=(
        f"Disk budget: the project uses {gb:.1f} GB against a {budget:g} GB budget"
        f" (approved ceiling {ceiling:g} GB). Allowing this "
        f"{'new agent or worktree' if kind == 'new' else 'action'} approves one more GB,"
        f" up to {need} GB (work/MACHINE.md §Disk budget). Deny it to clean up instead."))


def post(hook, st):
    tool, inp = hook.get("tool_name", ""), hook.get("tool_input") or {}
    notes = []
    p = st.get("pending", {}).pop(hook.get("tool_use_id", ""), None)
    if p:
        st["approved_gb"] = max(st.get("approved_gb", 0), p["gb"])
        notes.append(f"Disk budget: the decider approved one more GB — the ceiling is now {p['gb']} GB.")
    if growing(tool, inp):
        gb, budget, ceiling = usage(st, fresh=True)
        if gb >= ceiling:
            mark = f"{ceiling:g}"
            if not NUDGED.exists() or NUDGED.read_text(encoding="utf-8") != mark:
                NUDGED.write_text(mark, encoding="utf-8")
                notes.append(f"Disk budget: the project has grown to {gb:.1f} GB, past the approved"
                             f" {ceiling:g} GB (budget {budget:g} GB). Stop growing it: the next"
                             " build, install, agent or worktree asks the decider first.")
    if notes:
        emit("PostToolUse", additionalContext=" ".join(notes))


def prompt(_hook, st):
    gb, budget, ceiling = usage(st)
    if gb >= budget * 0.8:
        print(f"<disk>Disk budget: {gb:.1f} GB used of a {budget:g} GB budget"
              f"{f' (approved to {ceiling:g} GB)' if ceiling > budget else ''}"
              " — work/MACHINE.md §Disk budget.</disk>")


def fresh(_hook, st):
    gb, budget, ceiling = usage(st, fresh=True)
    state = "under the budget" if gb < budget else (
        "inside the approved GB" if gb < ceiling else "PAST the approved ceiling")
    print(f"{gb:.2f} GB used · budget {budget:g} GB · approved ceiling {ceiling:g} GB · {state}")
    return 0 if gb < ceiling else 1


def main(argv):
    mode = argv[0] if argv else "fresh"
    hook = {}
    if mode not in ("fresh", "prompt") and not sys.stdin.isatty():
        try:
            hook = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            hook = {}
    fn = {"pre": pre, "post": post, "prompt": prompt, "fresh": fresh}.get(mode)
    if fn is None:
        print(f"usage: disk-budget.py pre|post|prompt|fresh (got {mode})", file=sys.stderr)
        return 2
    st = load()
    rc = fn(hook, st) or 0
    save(st)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
