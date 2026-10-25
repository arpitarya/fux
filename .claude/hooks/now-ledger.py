#!/usr/bin/env python3
"""Keep `work/NOW.md` as only what is live — SR-WORK-NOW.

    now-ledger.py start   SessionStart: add this session's row; close dead ones
    now-ledger.py show    UserPromptSubmit: heartbeat; name the other live sessions
    now-ledger.py sync    PostToolUse (Bash, Agent, worktree): list worktrees this
                          session created; drop path rows whose path is gone
    now-ledger.py stop    Stop: ask once for an empty `working on` cell
    now-ledger.py end     SessionEnd: clean or queue what the session left, then
                          remove every row of it

One row per live session under `## In flight` (decision 2); what it creates
under `## Resources this session created` until it is cleaned (decision 3). At
the end a worktree is removed when nothing in it can be lost and is otherwise
filed red for Arpit; any other resource becomes a 🟢 agent cleanup item
(decision 4, SR-WORK-CLEANUP). A session with no heartbeat for 6 hours — or a
Cowork row started more than 6 hours ago — is closed the same way at the next
session's start (decision 5).

Never blocks on its own failure: an error prints nothing and exits 0.
Stdlib only.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import re
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW_MD = ROOT / "work" / "NOW.md"
QUEUE = ROOT / "work" / "OPEN-WORK.md"
SESSIONS = ROOT / ".claude" / ".sessions"
LOCK = ROOT / ".claude" / ".now.lock"
NUDGED = ROOT / ".claude" / ".now-nudged"
DEAD_AFTER_S = 6 * 3600
LOCK_STALE_S = 30
FLIGHT = "## In flight"
RESOURCES = "## Resources this session created"
SURFACE = "Claude Code"


def _cleanup_module():
    spec = importlib.util.spec_from_file_location("worktree_cleanup", Path(__file__).with_name("worktree-cleanup.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # a dataclass resolves its module here
    spec.loader.exec_module(mod)
    return mod


def _stamp(t: float | None = None) -> str:
    return dt.datetime.fromtimestamp(t or time.time(), dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def _parse_stamp(s: str) -> float | None:
    try:
        return dt.datetime.strptime(s.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp()
    except ValueError:
        return None


# ── NOW.md as two tables ─────────────────────────────────────────────────────

def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def read_tables(text: str) -> tuple[list[str], dict[str, tuple[int, int]]]:
    """The file's lines and, per heading, the [start, end) range of its body rows."""
    lines = text.split("\n")
    spans: dict[str, tuple[int, int]] = {}
    for heading in (FLIGHT, RESOURCES):
        h = next(i for i, line in enumerate(lines) if line.strip() == heading)
        sep = next(i for i in range(h, len(lines)) if lines[i].startswith("|---"))
        end = sep + 1
        while end < len(lines) and lines[end].startswith("|"):
            end += 1
        spans[heading] = (sep + 1, end)
    return lines, spans


def rows(text: str, heading: str) -> list[list[str]]:
    lines, spans = read_tables(text)
    a, b = spans[heading]
    return [_cells(line) for line in lines[a:b]]


def set_rows(text: str, heading: str, new: list[list[str]]) -> str:
    lines, spans = read_tables(text)
    a, b = spans[heading]
    return "\n".join(lines[:a] + [_row(r) for r in new] + lines[b:])


class _Locked:
    """`.claude/.now.lock/` as a mutex; reclaimed after 30 seconds (SR-WORK-CLEANUP d10)."""

    def __enter__(self):
        deadline = time.time() + 10
        while True:
            try:
                LOCK.mkdir(parents=True)
                return self
            except FileExistsError:
                try:
                    if time.time() - LOCK.stat().st_mtime > LOCK_STALE_S:
                        LOCK.rmdir()
                        continue
                except OSError:
                    pass
                if time.time() > deadline:
                    raise TimeoutError("work/NOW.md is locked")
                time.sleep(0.1)

    def __exit__(self, *exc):
        try:
            LOCK.rmdir()
        except OSError:
            pass


# ── session state ────────────────────────────────────────────────────────────

def _sid(event: dict) -> str:
    return (event.get("session_id") or os.environ.get("CLAUDE_SESSION_ID") or str(os.getppid()))[:8]


def _state_path(sid: str) -> Path:
    return SESSIONS / f"{sid}.json"


def _state(sid: str) -> dict:
    try:
        return json.loads(_state_path(sid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(sid: str, data: dict) -> None:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    _state_path(sid).write_text(json.dumps(data), encoding="utf-8")


def _beat(sid: str) -> dict:
    data = _state(sid)
    data["beat"] = time.time()
    _save_state(sid, data)
    return data


def _worktree_paths() -> set[str]:
    return {str(w.path) for w in _cleanup_module().worktrees(ROOT)}


# ── filing what a session left ───────────────────────────────────────────────

def _next_id() -> int:
    seen = [0]
    for folder in (ROOT / "work" / "open", ROOT / "archive" / "open"):
        seen += [int(m.group(1)) for p in folder.glob("W-*.md") if (m := re.match(r"W-(\d+)", p.name))]
    seen += [int(n) for n in re.findall(r"\*\*W-(\d+)\*\*", QUEUE.read_text(encoding="utf-8"))]
    return max(seen) + 1


def file_item(sid: str, red: list[str], other: list[str]) -> str:
    """One work item for what session `sid` left: 🔴 arpit when anything would be
    lost (with an inbox row), else 🟢 agent. Returns its id."""
    n = _next_id()
    wid = f"W-{n}"
    name = f"{wid}-cleanup-session-{sid}.md"
    today = dt.date.today().isoformat()
    ball, dot = ("arpit", "🔴") if red else ("agent", "🟢")
    body = [f"- 🔴 worktree — {r}" for r in red] + [f"- 🟢 {o}" for o in other]
    (ROOT / "work" / "open" / name).write_text(
        "---\n"
        "type: Handoff\n"
        f"name: {wid}\n"
        f'description: "Session {sid} ended and left {len(red) + len(other)} resource(s) uncleaned '
        f'(SR-WORK-NOW decision 4, SR-WORK-CLEANUP)."\n'
        f"item: {wid}\nfiled: {today}\n"
        'filed_by: "now-ledger.py (SessionEnd)"\n'
        f"updated: {today}\n"
        'updated_by: "now-ledger.py (SessionEnd)"\n'
        f"ball: {ball}\n"
        "---\n\n"
        f"# {wid} — clean up what session {sid} left\n\n"
        + "\n".join(body) + "\n\n"
        + ("**Arpit rules per red worktree** (SR-WORK-CLEANUP decision 3): **keep** — merge it or "
           "commit the files, and the next cleanup removes it — or **drop**, and only then may an "
           "agent use `--force` or `-D`.\n" if red else
           "Clean each one only if nothing in it would be lost; otherwise turn this item red "
           "(SR-WORK-CLEANUP decision 7).\n"),
        encoding="utf-8",
    )
    text = QUEUE.read_text(encoding="utf-8")
    lane = (f"- {dot} **{wid}** · `{ball}` — session {sid} left {len(red) + len(other)} uncleaned "
            f"resource(s); {'Arpit rules keep or drop per worktree' if red else 'clean if nothing is lost'}. "
            f"Filed by now-ledger.py. [detail](open/{name})")
    text = text.replace("### fux build\n\n", f"### fux build\n\n{lane}\n", 1)
    header = "| what he decides | filed | age |\n|---|---|---|\n"
    if red and header in text:
        inbox = (f"| 🔴 **{wid}** — rule keep or drop for {len(red)} worktree(s) session {sid} left. "
                 f"[the item](open/{name}) | {today} | 0d |\n| ↳ **blocks:** nothing else in the queue | | |\n")
        text = text.replace(header, header + inbox, 1)
    QUEUE.write_text(text, encoding="utf-8")
    return wid


def end_session(sid: str, text: str) -> str:
    """Clean or queue session `sid`'s resources; return NOW.md without its rows."""
    mine = [r for r in rows(text, RESOURCES) if len(r) >= 4 and r[3] == sid]
    red, other = [], []
    worktrees = [Path(r[1]) for r in mine if r[0] == "worktree"]
    if worktrees:
        wc = _cleanup_module()
        for wt in wc.verdicts(ROOT, set(worktrees)):
            err = wc.clean(wt, ROOT) if wt.safe else "; ".join(wt.reasons)
            if err:
                red.append(f"`{wt.path}` — {err}")
    other = [f"{r[0]} `{r[1]}` on {r[2]}" for r in mine if r[0] != "worktree"]
    if red or other:
        file_item(sid, red, other)
    text = set_rows(text, FLIGHT, [r for r in rows(text, FLIGHT) if r[0] != sid])
    text = set_rows(text, RESOURCES, [r for r in rows(text, RESOURCES) if len(r) < 4 or r[3] != sid])
    try:
        _state_path(sid).unlink()
    except OSError:
        pass
    return text


def _dead(row: list[str]) -> bool:
    sid, surface, started = row[0], row[1], row[2]
    beat = _state(sid).get("beat")
    if surface == SURFACE and beat:
        return time.time() - beat > DEAD_AFTER_S
    t = _parse_stamp(started)
    return t is not None and time.time() - t > DEAD_AFTER_S


# ── the five events ──────────────────────────────────────────────────────────

def start(event: dict) -> str | None:
    sid = _sid(event)
    _save_state(sid, {"beat": time.time(), "baseline": sorted(_worktree_paths())})
    with _Locked():
        text = NOW_MD.read_text(encoding="utf-8")
        for row in rows(text, FLIGHT):
            if row[0] != sid and _dead(row):
                text = end_session(row[0], text)
        flight = rows(text, FLIGHT)
        if not any(r[0] == sid for r in flight):
            text = set_rows(text, FLIGHT, flight + [[sid, SURFACE, _stamp(), ""]])
        NOW_MD.write_text(text, encoding="utf-8")
    return None


def show(event: dict) -> str | None:
    sid = _sid(event)
    _beat(sid)
    others = [r for r in rows(NOW_MD.read_text(encoding="utf-8"), FLIGHT) if r[0] != sid]
    if not others:
        return None
    named = "; ".join(f"{r[0]} ({r[1]}, since {r[2]}): {r[3] or '—'}" for r in others)
    return f"NOW.md — other live session(s) on this tree: {named}. Never edit their rows (SR-WORK-NOW decision 2)."


def sync(event: dict) -> str | None:
    sid = _sid(event)
    state = _beat(sid)
    with _Locked():
        text = NOW_MD.read_text(encoding="utf-8")
        res = rows(text, RESOURCES)
        known = {r[1] for r in res if len(r) > 1}
        baseline = set(state.get("baseline", []))
        new = sorted(_worktree_paths() - baseline - known)
        res = [r for r in res if not (len(r) > 1 and r[1].startswith("/") and not Path(r[1]).exists())]
        res += [["worktree", p, socket.gethostname(), sid, _stamp()] for p in new]
        updated = set_rows(text, RESOURCES, res)
        if updated != text:
            NOW_MD.write_text(updated, encoding="utf-8")
    return None


def stop(event: dict) -> dict | None:
    sid = _sid(event)
    mine = [r for r in rows(NOW_MD.read_text(encoding="utf-8"), FLIGHT) if r[0] == sid]
    if not mine or mine[0][3]:
        return None
    nudged = set(NUDGED.read_text(encoding="utf-8").split()) if NUDGED.exists() else set()
    if sid in nudged:
        return None
    NUDGED.write_text(" ".join(sorted(nudged | {sid})), encoding="utf-8")
    return {"decision": "block", "reason": (
        f"work/NOW.md: session {sid}'s `working on` cell is empty. Write one line — what this "
        "session is doing, with its W-id — in your own row (SR-WORK-NOW decision 2). Asked once.")}


def end(event: dict) -> str | None:
    sid = _sid(event)
    with _Locked():
        text = NOW_MD.read_text(encoding="utf-8")
        NOW_MD.write_text(end_session(sid, text), encoding="utf-8")
    return None


def main(argv: list[str]) -> int:
    handlers = {"start": start, "show": show, "sync": sync, "stop": stop, "end": end}
    if not argv or argv[0] not in handlers:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        out = handlers[argv[0]](json.loads(raw or "{}"))
    except Exception:  # never a wall on the hook's own failure
        return 0
    if isinstance(out, dict):
        print(json.dumps(out))
    elif out:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
