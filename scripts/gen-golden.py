#!/usr/bin/env python3
"""Render `CLAUDE.md` §Golden answer key from SR-WORK-GOLDEN.

**Why this exists, and why it is a second generator rather than a flag on
[`gen-laws.py`](gen-laws.py).** The laws generator renders **ten** blocks in a
fixed handle order and validates that every handle has exactly one home; this
renders **one** block from one named record. Folding them together would mean a
generator whose contract is *"sometimes a set, sometimes a singleton"*, and the
set half's validation — `LAW_ORDER`, the duplicate-handle check — is meaningless
here. **What the two genuinely share is the link rewrite, and that is imported
rather than copied.**

**Why a view exists at all.** [SR-LAW-0](../records/0002_LAW-0-authority.md)
decision 1 says every rule is stated in exactly one SR and every other artifact
links to it. Decision 5 is the exception: **a generated view is permitted, and
only while a test binds it.** SR-WORK-GOLDEN decision 3 is why this particular
rule earns one — Cowork reads `CLAUDE.md` and does not read `records/`, so a
link there would cover nothing Cowork reaches.
⚠ **Remove [`tests/test_claude_md_golden.py`](../tests/test_claude_md_golden.py)
and the block in `CLAUDE.md` violates decision 1.** The permission is the test,
not the generation.

## The contract

- `records/0066_WORK-golden.md` carries **exactly one** normative block::

      <!-- GOLDEN-TEXT:BEGIN -->
      🔴 **No Claude session opens …**
      <!-- GOLDEN-TEXT:END -->

- It is dropped between `CLAUDE.md`'s `<!-- GOLDEN:BEGIN … -->` /
  `<!-- GOLDEN:END -->` markers.
- **Link targets are rewritten, and that is the only transform** — the record
  lives in `records/`, `CLAUDE.md` at the repo root, so the same text needs two
  spellings of the same target.

Run `python scripts/gen-golden.py --write` after amending the record; run it with
`--check` (what CI and the test do) to prove the two agree.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"
RECORD = ROOT / "records" / "0066_WORK-golden.md"

SRC_BEGIN = "<!-- GOLDEN-TEXT:BEGIN -->"
SRC_END = "<!-- GOLDEN-TEXT:END -->"

BEGIN = "<!-- GOLDEN:BEGIN"
END = "<!-- GOLDEN:END -->"

#: The exact opening marker written into `CLAUDE.md`. It names the generator, so
#: a reader who edits the block by hand is told where the text actually lives
#: before the test tells them.
BEGIN_LINE = (
    "<!-- GOLDEN:BEGIN — GENERATED from records/0066_WORK-golden.md by "
    "scripts/gen-golden.py. Do not edit by hand: amend the record, then run "
    "`python scripts/gen-golden.py --write`. -->"
)


def _rewrite_links(text: str) -> str:
    """`gen-laws.py`'s rewrite, imported by path.

    `scripts/` is not a package and must not become one for two scripts, so this
    is the same `importlib` load `tests/test_claude_md_laws.py` already uses.
    **Importing beats copying**: a divergence between two link rewriters would
    be invisible until one of the two files grew a link shaped like the case the
    other handles differently.
    """
    spec = importlib.util.spec_from_file_location(
        "fux_gen_laws", Path(__file__).with_name("gen-laws.py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._rewrite_links(text)


def render() -> str:
    """The record's normative block, links rewritten for the repo root."""
    text = RECORD.read_text(encoding="utf-8")
    if text.count(SRC_BEGIN) != 1 or text.count(SRC_END) != 1:
        raise SystemExit(
            f"{RECORD.name}: expected exactly one {SRC_BEGIN}/{SRC_END} pair "
            f"(found {text.count(SRC_BEGIN)}/{text.count(SRC_END)})"
        )
    body = text.split(SRC_BEGIN, 1)[1].split(SRC_END, 1)[0].strip("\n")
    if not body:
        raise SystemExit(f"{RECORD.name}: the GOLDEN-TEXT block is empty")
    return _rewrite_links(body)


def committed_block() -> str:
    """What `CLAUDE.md` currently carries between the markers."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(
            "CLAUDE.md carries no GOLDEN:BEGIN/GOLDEN:END markers — §Golden "
            "answer key has not been migrated to the generated block "
            "(SR-WORK-GOLDEN decision 2)"
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
        fromfile="CLAUDE.md (committed)", tofile="records/0066_WORK-golden.md (the record)",
        lineterm="",
    )
    print("\n".join(diff), file=sys.stderr)
    print(
        "\nCLAUDE.md's golden-key block does not match SR-WORK-GOLDEN. The record "
        "is the source (SR-LAW-0 decision 1): fix the record, then run "
        "`python scripts/gen-golden.py --write`.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
