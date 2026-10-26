#!/usr/bin/env python3
"""NOW ledger — SR-WORK-NOW decisions 2-5: work/NOW.md holds only what is live.

    start  SessionStart      add this session's row; close dead sessions
    show   UserPromptSubmit  heartbeat; close dead sessions
    sync   PostToolUse       heartbeat; list worktrees this session created,
                             drop path rows whose path is gone
    stop   Stop              ask once for an empty `working on` cell
    end    SessionEnd        clean or queue what the session left
                             (SR-WORK-CLEANUP), then remove its rows

A session is dead with no heartbeat for 6 hours; a row with no heartbeat at
all (a Cowork session's) once it started more than 6 hours ago. Hook input is
JSON on stdin; `show </dev/null` by hand closes dead sessions.
"""
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW_MD = ROOT / "work" / "NOW.md"
TMP = ROOT / "work" / ".NOW.md.tmp"
LOCK = ROOT / ".claude" / ".now.lock"
SESSIONS = ROOT / ".claude" / ".sessions"
NUDGED = ROOT / ".claude" / ".now-nudged"
OPEN_WORK = ROOT / "work" / "OPEN-WORK.md"
DEAD_S = 6 * 3600
LOCK_S = 30
# Rows whose `where` is a path on this host: dropped once the path is gone.
PATH_KINDS = {"worktree", "files", "folder", "dir", "clone", "build"}

FLIGHT_HEAD = "| session | surface | started | working on |"
RES_HEAD = "| kind | where | host | session | created |"


# ---------------------------------------------------------------- NOW.md I/O

class Locked:
    """mkdir mutex on .claude/.now.lock; reclaimed after 30 seconds."""

    def __enter__(self):
        for _ in range(100):
            try:
                LOCK.mkdir()
                return self
            except FileExistsError:
                try:
                    if time.time() - LOCK.stat().st_mtime > LOCK_S:
                        LOCK.rmdir()
                        continue
                except OSError:
                    continue
                time.sleep(0.1)
        return self  # never wedge a session on its own ledger

    def __exit__(self, *_):
        try:
            LOCK.rmdir()
        except OSError:
            pass


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def read_now():
    """(prose_before_tables, flight_rows, resource_rows) — rows as cell lists."""
    text = NOW_MD.read_text(encoding="utf-8")
    head, _, _ = text.partition("## In flight")
    flight, res, section = [], [], None
    for line in text.splitlines():
        if line.startswith("## In flight"):
            section = flight
        elif line.startswith("## Resources"):
            section = res
        elif section is not None and line.startswith("|") and not line.startswith("|---"):
            c = cells(line)
            if c[0] in ("session", "kind"):
                continue
            section.append(c)
    return head.rstrip() + "\n", flight, res


def renderer():
    """lockmaster's NOW.md renderer (`lockmaster.now`) when it is importable —
    installed, or this repository's own src/ — so NOW.md always equals
    `lockmaster status --now` (SR-ARCHITECTURE decision 14, W-07)."""
    for extra in (None, ROOT / "src"):
        if extra is not None:
            if not (extra / "lockmaster" / "now.py").is_file():
                continue
            sys.path.insert(0, str(extra))
        try:
            from lockmaster import now
            return now
        except ImportError:
            continue
    return None


def write_now(head, flight, res):
    mod = renderer()
    if mod is not None:
        text = mod.format_now(head, flight, mod.normalise(res, ROOT))
    else:
        # The same shape lockmaster.now writes, for a repo without lockmaster.
        def table(header, rows, n):
            out = [header, "|" + "---|" * n]
            out += ["| " + " | ".join((r + [""] * n)[:n]) + " |" for r in rows]
            return "\n".join(out)

        res = [r for r in res if not (r[0] in PATH_KINDS and (p := where_path(r[1])) is not None
                                      and not p.exists())]
        text = (f"{head}\n## In flight\n\n{table(FLIGHT_HEAD, flight, 4)}\n\n"
                f"## Resources this session created\n\n{table(RES_HEAD, res, 5)}\n")
    TMP.write_text(text, encoding="utf-8")
    os.replace(TMP, NOW_MD)


# ---------------------------------------------------------------- sessions

def beat_file(sid):
    return SESSIONS / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', sid)}.json"


def beat(sid, **extra):
    SESSIONS.mkdir(parents=True, exist_ok=True)
    f = beat_file(sid)
    try:
        st = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {"started": time.time(), "worktrees": worktree_paths()}
    st.update(extra, beat=time.time())
    f.write_text(json.dumps(st), encoding="utf-8")
    return st


def worktree_paths():
    out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    paths = [l[9:] for l in out.splitlines() if l.startswith("worktree ")]
    return [p for p in paths if os.path.realpath(p) != os.path.realpath(ROOT)]


def started_epoch(cell):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(cell.strip("` "), fmt).timestamp()
        except ValueError:
            pass
    return None


def dead(row):
    sid = row[0].strip("`")
    f = beat_file(sid)
    if f.exists():
        try:
            return time.time() - json.loads(f.read_text(encoding="utf-8"))["beat"] > DEAD_S
        except (OSError, ValueError, KeyError):
            return True
    t = started_epoch(row[2]) if len(row) > 2 else None
    return t is not None and time.time() - t > DEAD_S


def where_path(cell):
    m = re.search(r"`([^`]+)`", cell)
    if not m:
        return None
    p = Path(m.group(1).rstrip("/"))
    return p if p.is_absolute() else ROOT / p


# ---------------------------------------------------------------- cleanup

def cleanup_module():
    spec = importlib.util.spec_from_file_location(
        "worktree_cleanup", Path(__file__).with_name("worktree-cleanup.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def next_id():
    seen = [0]
    for d in (ROOT / "work" / "open", ROOT / "archive" / "open"):
        seen += [int(m.group(1)) for f in d.glob("W-*.md")
                 if (m := re.match(r"W-(\d+)", f.name))]
    for f in (OPEN_WORK, ROOT / "work" / "BACKLOG.md"):
        try:
            seen += [int(x) for x in re.findall(r"\bW-(\d+)\b", f.read_text(encoding="utf-8"))]
        except OSError:
            pass
    return max(seen) + 1


def file_item(ball, lane, title, body, sid):
    """One item file + one OPEN-WORK row (and, for red, an inbox row), in the
    queue's own row style; the `### build (N)` count moves with the row."""
    n = next_id()
    wid, slug = f"W-{n:02d}", "session-cleanup"
    today = date.today().isoformat()
    by = "now-ledger.py (Claude Code)"
    path = ROOT / "work" / "open" / f"{wid}-{slug}.md"
    path.write_text(
        f"---\ntype: Handoff\nname: {wid}\ndescription: \"{title}\"\nitem: {wid}\n"
        f"filed: {today}\nfiled_by: \"{by}\"\n"
        f"updated: {today}\nupdated_by: \"{by}\"\nball: {'arpit' if ball == '🔴' else lane}\n---\n\n"
        f"# {wid} — {title}\n\n## At a glance\n\n| what | state |\n|---|---|\n"
        f"| {title} | ⏳ |\n\nFiled at the end of session `{sid}`.\n\n{body}\n\n## Record affected\n\n"
        f"No SR affected — the rule is SR-WORK-CLEANUP.\n",
        encoding="utf-8")
    text = OPEN_WORK.read_text(encoding="utf-8")
    bullets = re.search(r"^- (🔴|🟣|🟡|🟢)", text, re.M) is not None
    row = (f"- {ball} **{wid}** · `{lane}` — {title}." if bullets else f"{ball} **{wid}** `{lane}` {title}.") + \
          f" Filed by {by}. [detail](open/{wid}-{slug}.md)"

    def bump(m):
        return f"{m.group(1)} ({int(m.group(2) or 0) + 1})\n\n{row}\n\n"
    text = re.sub(r"^(### (?:\S+ )?build)(?: \((\d+)\))?\n\n", bump, text, count=1, flags=re.M)
    if ball == "🔴":
        head = re.search(r"^## Blocked on [^\n]*\n\n(\| what[^\n]*)\n", text, re.M)
        aged = head is not None and "| age |" in head.group(1)
        inbox = (f"| 🔴 **{wid}** — keep or drop each worktree in [the item](open/{wid}-{slug}.md):"
                 f" removing it would lose data (SR-WORK-CLEANUP decision 3) | {today} |"
                 + (" 0 d |" if aged else "") + "\n"
                 f"| ↳ **blocks:** nothing else in the queue | |" + (" |" if aged else "") + "\n")
        text = re.sub(r"(^## Blocked on [^\n]*\n\n\| what[^\n]*\n\|---[^\n]*\n)",
                      lambda m: m.group(1) + inbox, text, count=1, flags=re.M)
        text = re.sub(r"\n\*Empty since[^\n]*\n", "\n", text, count=1)
    OPEN_WORK.write_text(text, encoding="utf-8")
    return wid


def close_session(sid, res):
    """SR-WORK-NOW decision 4: clean or queue what `sid` left; return the
    resource rows that are not its."""
    mine = [r for r in res if len(r) > 3 and r[3].strip("`") == sid]
    keep = [r for r in res if r not in mine]
    trees, other = [], []
    for r in mine:
        p = where_path(r[1])
        if r[0] in PATH_KINDS and p is not None and not p.exists():
            continue
        (trees if r[0] == "worktree" and p is not None else other).append(r)
    red = []
    if trees:
        try:
            _, red = cleanup_module().sweep([str(where_path(r[1])) for r in trees], apply=True)
        except Exception as e:  # noqa: BLE001 — a failed check is red, the safe side
            red = [(str(where_path(r[1])), [f"cleanup failed: {e}"]) for r in trees]
    if red:
        lines = "\n".join(f"- `{p}` — " + "; ".join(why) for p, why in red)
        file_item("🔴", "arpit", f"Worktrees left by session {sid} would lose data if removed",
                  "These worktrees were left untouched. Rule per worktree: **keep** (merge it or"
                  " commit the files; the next cleanup removes it) or **drop** (only then may an"
                  " agent force the removal and delete the unmerged branch).\n\n" + lines, sid)
    if other:
        lines = "\n".join("- " + " · ".join(r) for r in other)
        file_item("🟢", "agent", f"Clean up what session {sid} left",
                  "Clean each only if nothing is lost; otherwise turn this item red and put it"
                  " to the decider (SR-WORK-CLEANUP decision 7).\n\n" + lines, sid)
    beat_file(sid).unlink(missing_ok=True)
    return keep


def reap(flight, res, me=None):
    """Close every dead session but `me`."""
    for row in [r for r in flight if r[0].strip("`") != me and dead(r)]:
        res = close_session(row[0].strip("`"), res)
        flight.remove(row)
    return flight, res


# ---------------------------------------------------------------- modes

def start(sid, _hook):
    beat(sid)
    with Locked():
        head, flight, res = read_now()
        flight, res = reap(flight, res, sid)
        if not any(r[0].strip("`") == sid for r in flight):
            flight.append([sid, "Claude Code", datetime.now().strftime("%Y-%m-%d %H:%M"), ""])
        write_now(head, flight, res)


def show(sid, _hook):
    if sid:
        beat(sid)
    with Locked():
        head, flight, res = read_now()
        n = (len(flight), len(res))
        flight, res = reap(flight, res, sid)
        if (len(flight), len(res)) != n:
            write_now(head, flight, res)


def sync(sid, _hook):
    st = beat(sid)
    host = socket.gethostname().split(".")[0]
    with Locked():
        head, flight, res = read_now()
        before = [list(r) for r in res]
        listed = {os.path.realpath(str(p)) for r in res if (p := where_path(r[1]))}
        for p in worktree_paths():
            if p not in st.get("worktrees", []) and os.path.realpath(p) not in listed:
                res.append(["worktree", f"`{p}`", host, sid, date.today().isoformat()])
        res = [r for r in res if not (r[0] in PATH_KINDS and (p := where_path(r[1])) is not None
                                      and not p.exists())]
        if res != before:
            write_now(head, flight, res)


def stop(sid, _hook):
    _, flight, _ = read_now()
    row = next((r for r in flight if r[0].strip("`") == sid), None)
    if not row or (len(row) > 3 and row[3]):
        return
    seen = NUDGED.read_text(encoding="utf-8").split() if NUDGED.exists() else []
    if sid in seen:
        return
    NUDGED.write_text(" ".join(seen + [sid]), encoding="utf-8")
    print(json.dumps({"decision": "block", "reason":
          f"work/NOW.md: this session's row ({sid}) has an empty `working on` cell."
          " Fill it with what you are doing (the W-id when there is one), then stop"
          " (SR-WORK-NOW decision 2)."}))


def end(sid, _hook):
    with Locked():
        head, flight, res = read_now()
        res = close_session(sid, res)
        flight = [r for r in flight if r[0].strip("`") != sid]
        flight, res = reap(flight, res, sid)
        write_now(head, flight, res)


def main(argv):
    if not NOW_MD.is_file():
        return 0  # a repository without the work system has no NOW to keep (W-09)
    mode = argv[0] if argv else "show"
    fn = {"start": start, "show": show, "sync": sync, "stop": stop, "end": end}.get(mode)
    if fn is None:
        print(f"usage: now-ledger.py start|show|sync|stop|end (got {mode})", file=sys.stderr)
        return 2
    hook = {}
    if not sys.stdin.isatty():
        try:
            hook = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            hook = {}
    sid = hook.get("session_id") or os.environ.get("CLAUDE_SESSION_ID", "")
    if not sid and mode != "show":
        return 0
    fn(sid, hook)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
