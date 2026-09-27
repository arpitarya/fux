#!/usr/bin/env python3
"""Stamp and check each Standing Record's `content_sha`.

**What it is for.** A record is amended in place (Law zero), so "which version
of SR-X was this written against?" has no answer from the file alone. The
`content_sha` gives one: quote it beside a citation and a later reader can tell
whether the record has moved since.

**What it covers, exactly.** The whole file — frontmatter and body — with the
`content_sha:` line itself removed, on LF endings, UTF-8, SHA-256, full hex. A
hash cannot cover itself, and hashing only the body would let `owns`, `status`
or `laws` change without moving it, which are precisely the changes a reader
cares about.

**Deterministic, as L3 requires:** same bytes in, same digest out, no clock and
no path in the input.

⚠ **It tells you THAT a record moved, never what moved** — `git diff` does that.
Its value is outside git: a vendored copy, an agent policy file, or a doc that
pins the version of the rule it was written against.

Usage::

    python scripts/sr-hash.py                     # check every record: exit 1 and name every stale one
    python scripts/sr-hash.py --write 0109 0126   # stamp only the records you changed
    python scripts/sr-hash.py --write --all       # stamp every record — only on a tree nobody else is editing

🔴 **A bare `--write` is refused**, for the reason `sr-owns.py` refuses one
([SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md) decision 13a).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
KEY = "content_sha"

_LINE = re.compile(rf"^{KEY}:.*\n?", re.M)


def records() -> list[Path]:
    return sorted(RECORDS.glob("[0-9][0-9][0-9][0-9]_*.md"))


def digest(text: str) -> str:
    """SHA-256 of the record with its own `content_sha:` line removed."""
    return hashlib.sha256(_LINE.sub("", text.replace("\r\n", "\n")).encode("utf-8")).hexdigest()


def stamped(text: str) -> str:
    """`text` with a correct `content_sha:` line, added after `timestamp:` if absent."""
    body = _LINE.sub("", text.replace("\r\n", "\n"))
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    m = re.search(r"^timestamp:.*\n", body, re.M)
    if not m:
        raise SystemExit("a record with no `timestamp:` key — fix the frontmatter first")
    return body[: m.end()] + f"{KEY}: {sha}\n" + body[m.end() :]


def current(text: str) -> str | None:
    m = re.search(rf"^{KEY}:\s*([0-9a-f]{{64}})\s*$", text, re.M)
    return m.group(1) if m else None


#: Why a bare `--write` is refused. Stated here, printed on refusal.
_REFUSAL = (
    "refusing a repo-wide --write: name the records you changed "
    "(e.g. `0109` or records/0109_index-record.md), or pass --all when no other "
    "session shares this tree. A repo-wide stamp re-stamps ANOTHER session's "
    "in-progress records and silently satisfies the gate meant to make them "
    "re-read them (SR-WORK-OWNERSHIP decision 13a; work/LESSONS.md 2026-09-21)."
)


def select(every: list[Path], names: list[str]) -> list[Path]:
    """The records `names` picks out of `every` — a 4-digit number, a file
    name, or a path. An unknown name is an error, never a silent no-op."""
    picked = []
    for name in names:
        stem = Path(name).name
        hits = [p for p in every if p.name == stem or p.name.startswith(f"{stem}_")]
        if len(hits) != 1:
            raise SystemExit(f"{name!r} names {len(hits)} records; name exactly one")
        picked.append(hits[0])
    return sorted(set(picked))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="recompute and stamp the named records")
    ap.add_argument("--all", action="store_true", help="with --write: every record (a tree nobody else is editing)")
    ap.add_argument("records", nargs="*", help="record numbers, names or paths to act on")
    args = ap.parse_args()
    if args.write and not args.records and not args.all:
        print(_REFUSAL, file=sys.stderr)
        return 2
    chosen = select(records(), args.records) if args.records else records()

    stale = []
    for path in chosen:
        text = path.read_text(encoding="utf-8")
        want = digest(text)
        if current(text) == want:
            continue
        if args.write:
            path.write_text(stamped(text), encoding="utf-8")
            print(f"{path.name}: stamped {want[:12]}…")
        else:
            stale.append(path.name)
    if stale:
        print(f"STALE ({len(stale)}): {', '.join(stale)}")
        print("run `python scripts/sr-hash.py --write <record…>`")
        return 1
    if not args.write:
        print(f"{len(records())} records: every content_sha is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
