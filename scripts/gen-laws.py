#!/usr/bin/env python3
"""Render `CLAUDE.md` §Non-negotiable constraints from the nine Law records.

**Why this exists.** [ADR-LAW-0](../docs/adr/0002_LAW-0-authority.md) decision 1
says every rule is *stated* in exactly one ADR and every other artifact links to
it. `CLAUDE.md` is the file every session reads first, so dropping the law text
out of it would cost agents their first read of the constitution — and keeping a
hand-written copy is the restatement decision 1 forbids.

Decision 5 is the way out: **a generated view is permitted, and only while a
test binds it.** This script is the generator;
[`tests/test_claude_md_laws.py`](../tests/test_claude_md_laws.py) is the bind.
⚠ **Remove that test and the block in `CLAUDE.md` violates decision 1** — the
permission is the test, not the generation.

## The contract

- Each `docs/adr/*_LAW-*.md` record carries **exactly one** normative block::

      <!-- LAW-TEXT:BEGIN L3 -->
      - **L3** · **Deterministic — no model in the maintenance path.** ...
      <!-- LAW-TEXT:END L3 -->

- The nine blocks are concatenated in `L0 … L9` order between `CLAUDE.md`'s
  `<!-- LAWS:BEGIN … -->` / `<!-- LAWS:END -->` markers.
- **Link targets are rewritten, and that is the only transform.** A record lives
  at `docs/adr/`, `CLAUDE.md` at the repo root, so the same law text needs two
  spellings of the same target. Rewriting deterministically here is what lets
  both files carry working links without either becoming the source.

Run `python scripts/gen-laws.py --write` after amending a law; run it with
`--check` (what CI and the test do) to prove the two agree.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
CLAUDE_MD = ROOT / "CLAUDE.md"

#: The nine handles, in the order the block renders them. L0 first because it is
#: the law that governs the others; L9 last because it is the newest.
LAW_ORDER = tuple(f"L{i}" for i in range(10))

BEGIN = "<!-- LAWS:BEGIN"
END = "<!-- LAWS:END -->"

#: The exact opening marker written into `CLAUDE.md`. It names the generator, so
#: a reader who edits the block by hand is told where the text actually lives
#: before the test tells them.
BEGIN_LINE = (
    "<!-- LAWS:BEGIN — GENERATED from docs/adr/*_LAW-*.md by "
    "scripts/gen-laws.py. Do not edit by hand: amend the record, then run "
    "`python scripts/gen-laws.py --write`. -->"
)

_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")


def _rewrite_target(target: str) -> str:
    """One link target, from `docs/adr/`-relative to repo-root-relative.

    Four cases and no others, because a fifth would be a guess:

    - absolute or in-page (`http…`, `mailto:`, `#frag`) — unchanged
    - `../../x` — the record reaching the repo root, so the prefix is dropped
    - `../x` — the record reaching `docs/`, so `docs/` replaces the `../`
    - anything else — a sibling record, so `docs/adr/` is prepended
    """
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return target
    if target.startswith("../../"):
        return target[len("../../") :]
    if target.startswith("../"):
        return "docs/" + target[len("../") :]
    return "docs/adr/" + target


def _rewrite_links(text: str) -> str:
    return _LINK_RE.sub(lambda m: "](" + _rewrite_target(m.group(1)) + ")", text)


def law_records() -> dict[str, Path]:
    """`{handle: path}` for every `*_LAW-*.md` record, keyed by its marker."""
    found: dict[str, Path] = {}
    for path in sorted(ADR_DIR.glob("*_LAW-*.md")):
        text = path.read_text(encoding="utf-8")
        handles = re.findall(r"<!-- LAW-TEXT:BEGIN (L\d) -->", text)
        if not handles:
            raise SystemExit(f"{path.name}: no <!-- LAW-TEXT:BEGIN Ln --> marker")
        if len(handles) > 1:
            raise SystemExit(f"{path.name}: {len(handles)} LAW-TEXT blocks, expected 1")
        handle = handles[0]
        if handle in found:
            raise SystemExit(f"{handle} declared by both {found[handle].name} and {path.name}")
        found[handle] = path
    return found


def law_text(path: Path, handle: str) -> str:
    """One record's normative block, links rewritten for the repo root."""
    text = path.read_text(encoding="utf-8")
    begin = f"<!-- LAW-TEXT:BEGIN {handle} -->"
    end = f"<!-- LAW-TEXT:END {handle} -->"
    try:
        body = text.split(begin, 1)[1].split(end, 1)[0]
    except IndexError:
        raise SystemExit(f"{path.name}: unterminated LAW-TEXT block for {handle}") from None
    body = body.strip("\n")
    if not body.startswith(f"- **{handle}** ·"):
        raise SystemExit(
            f"{path.name}: {handle}'s block must open `- **{handle}** ·` (got {body[:40]!r})"
        )
    return _rewrite_links(body)


def render() -> str:
    """The generated block body — what sits between the markers, no markers."""
    records = law_records()
    missing = [h for h in LAW_ORDER if h not in records]
    if missing:
        raise SystemExit(f"no record declares {', '.join(missing)}")
        # An extra handle is impossible: LAW_ORDER is the closed set and a
        # record declaring L10 would fail `_ORDER` lookup below, loudly.
    extra = [h for h in records if h not in LAW_ORDER]
    if extra:
        raise SystemExit(f"unknown law handle(s) {extra} — add them to LAW_ORDER first")
    return "\n".join(law_text(records[h], h) for h in LAW_ORDER)


def committed_block() -> str:
    """What `CLAUDE.md` currently carries between the markers."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(
            "CLAUDE.md carries no LAWS:BEGIN/LAWS:END markers — §Non-negotiable "
            "constraints has not been migrated to the generated block (W-122 phase 4)"
        )
    after = text.split(BEGIN, 1)[1]
    # The marker line runs to the end of the comment; skip it, then take
    # everything up to END.
    after = after.split("-->", 1)[1]
    return after.split(END, 1)[0].strip("\n")


def write() -> bool:
    """Replace the block in place. Returns True when bytes changed."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    head = text.split(BEGIN, 1)[0]
    tail = text.split(END, 1)[1]
    new = head + BEGIN_LINE + "\n\n" + render() + "\n\n" + END + tail
    if new == text:
        return False
    CLAUDE_MD.write_text(new, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if CLAUDE.md is stale")
    parser.add_argument("--write", action="store_true", help="regenerate CLAUDE.md's block")
    args = parser.parse_args(argv)

    expected = render()
    if args.write:
        changed = write()
        print("CLAUDE.md: regenerated" if changed else "CLAUDE.md: already current")
        return 0

    actual = committed_block()
    if actual == expected:
        if not args.check:
            print(expected)
        return 0
    if not args.check:
        print(expected)
        return 0
    diff = difflib.unified_diff(
        actual.splitlines(), expected.splitlines(),
        fromfile="CLAUDE.md (committed)", tofile="docs/adr/*_LAW-*.md (records)",
        lineterm="",
    )
    print("\n".join(diff), file=sys.stderr)
    print(
        "\nCLAUDE.md's law block does not match the records. The records are the "
        "source (ADR-LAW-0 decision 1): fix the record, then run "
        "`python scripts/gen-laws.py --write`.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
