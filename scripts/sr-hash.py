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

    python scripts/sr-hash.py            # check: exit 1 and name every stale record
    python scripts/sr-hash.py --write    # recompute and stamp every record
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="recompute and stamp every record")
    args = ap.parse_args()

    stale = []
    for path in records():
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
        print("run `python scripts/sr-hash.py --write`")
        return 1
    if not args.write:
        print(f"{len(records())} records: every content_sha is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
