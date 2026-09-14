"""`.fux/README.md`'s verb table, SR-CLI §1's, and the parser must agree.

**[SR-DOTFUX](../records/0102_fux-directory.md)'s 2026-09-12 amendment** put a
verb table in the file `fux setup` writes into every consumer's repository, and
[SR-CLI](../records/0101_cli-surface.md) §1 has carried one since the surface
shipped. Two hand-maintained copies of one list, with nothing comparing them.

🔴 **They had already drifted when this test was written** (W-164 gate 2): the
`maintenance` group reads `hooks · tune · verify` in SR-CLI and
`hooks tune output verify` in the README. **`fux output` is a real verb** — it
is in `build_parser()` — so the record, which is the source of truth under L0,
was the copy that was wrong, in a table it explicitly *"promises to keep true"*.

## The third party is the parser, and it is the one that settles it

Comparing two documents to each other can only say *they disagree*; it cannot
say which is right, and a session that guessed would have half a chance of
teaching the code to match a stale record. **`build_parser()` is the fact.** So
every verb it defines must appear in both tables, and neither table may name a
verb the parser does not have.

## What is NOT checked

**The prose in the third column.** The two say the same thing in different
words on purpose — the README is written for a consumer looking at their own
`.fux/`, the record for whoever is deciding. Holding those byte-equal would be
the restatement L0 forbids wearing a test's clothes.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / ".fux" / "README.md"
RECORD = ROOT / "records" / "0101_cli-surface.md"

_GROUP_ROW = re.compile(r"^\|\s*\*{0,2}([a-z]+)\*{0,2}\s*\|\s*(`.+?`.*?)\s*\|")
_VERB = re.compile(r"`([a-z]+)`")


def _table(path: Path) -> dict[str, set[str]]:
    """`{group: {verbs}}` from the first verb table in `path`.

    A verb table is recognised by its header row, so a later table of flags or
    exit codes cannot be read as one.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    out: dict[str, set[str]] = {}
    inside = False
    for line in lines:
        if line.startswith("| group | verbs"):
            inside = True
            continue
        if inside:
            if not line.startswith("|"):
                break
            if set(line) <= set("|-: "):
                continue
            match = _GROUP_ROW.match(line)
            if match:
                out[match.group(1)] = set(_VERB.findall(match.group(2)))
    return out


def _parser_verbs() -> set[str]:
    from fux.cli import build_parser

    actions = [
        a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction)
    ]
    assert actions, "build_parser() defines no subcommands — the parser shape moved"
    return set(actions[0].choices)


def test_both_tables_were_actually_found():
    """A parser that matches nothing makes every test below vacuous."""
    for path in (README, RECORD):
        table = _table(path)
        assert len(table) >= 5, f"{path.name}: only {len(table)} group(s) parsed"
        assert sum(len(v) for v in table.values()) > 10, f"{path.name}: too few verbs parsed"


def test_every_shipped_verb_is_in_both_tables():
    """🔴 **The parser settles it.** A table is wrong; the code is the fact."""
    shipped = _parser_verbs()
    for path in (README, RECORD):
        listed = {v for verbs in _table(path).values() for v in verbs}
        missing = sorted(shipped - listed)
        assert not missing, (
            f"{path.relative_to(ROOT)} does not list: {missing}\n\n"
            "`build_parser()` defines these and this table does not mention them. "
            "A consumer reading it for what fux can do is reading a short list."
        )


def test_neither_table_names_a_verb_that_does_not_exist():
    """A table naming a removed verb is worse than one missing a new one."""
    shipped = _parser_verbs()
    for path in (README, RECORD):
        listed = {v for verbs in _table(path).values() for v in verbs}
        phantom = sorted(listed - shipped)
        assert not phantom, (
            f"{path.relative_to(ROOT)} names verbs the parser does not have: {phantom}"
        )


def test_the_two_tables_group_the_verbs_identically():
    """The grouping IS the mental model — SR-CLI §1's own words.

    A verb that moves group in one copy and not the other teaches two different
    mental models from one repository.
    """
    readme, record = _table(README), _table(RECORD)
    assert set(readme) == set(record), (
        f"different group sets: README has {sorted(set(readme) - set(record))}, "
        f"the record has {sorted(set(record) - set(readme))}"
    )
    differing = {
        group: (sorted(readme[group] - record[group]), sorted(record[group] - readme[group]))
        for group in readme
        if readme[group] != record[group]
    }
    assert not differing, (
        "these groups hold different verbs in the two tables "
        "(README-only, record-only):\n  "
        + "\n  ".join(f"{g}: {d}" for g, d in sorted(differing.items()))
        + "\n\nThe parser decides which copy is wrong — see `_parser_verbs`."
    )
