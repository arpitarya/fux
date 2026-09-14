"""`LEVERS` and SR-INSPECT decision 12's table are one list, held equal here.

**Why this gate exists.** Every lever is a *recommendation to change what is
indexed or how it ranks* — a stopword, an `.fuxignore` line, an `archived=`
stamp, a decoder. A report that recommended a knob the records do not describe
would be fux telling its own consumer to do something nobody decided, and the
two copies of the list could disagree while both looked correct: exactly the
restatement [SR-LAW-0](../records/0002_LAW-0-authority.md) forbids.

**The code is the fact and the record is the claim**, in that direction: the
report prints `lenses.LEVERS`, so a mismatch means the record is describing a
report nobody gets.
"""

from __future__ import annotations

import re
from pathlib import Path

from fux.inspect.lenses import LEVERS

RECORD = Path(__file__).resolve().parents[1] / "records" / "0156_inspect.md"

#: The table is INDENTED — it sits inside numbered decision 12 — so every
#: pattern here matches on the stripped line. A pattern anchored at column 0
#: would find nothing and every assertion below would pass on an empty dict,
#: which `test_the_record_carries_the_table_at_all` is here to refuse.
_ROW = re.compile(r"^\|\s*([a-z][a-z \-]+?)\s*\|\s*(.+?)\s*\|$")


def _record_table() -> dict[str, str]:
    """The finding -> lever table under decision 12, and only that table."""
    out: dict[str, str] = {}
    inside = False
    for raw in RECORD.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "| finding | lever |":
            inside = True
            continue
        if inside:
            if not line.startswith("|"):
                break
            if set(line) <= set("|- "):
                continue
            match = _ROW.match(line)
            if match:
                out[match.group(1)] = match.group(2)
    return out


def test_the_record_carries_the_table_at_all() -> None:
    """A collector that matches nothing is a test that always passes."""
    assert len(_record_table()) >= 8, _record_table()


def test_every_finding_the_report_can_print_is_in_the_record() -> None:
    table = _record_table()
    missing = sorted(set(LEVERS) - set(table))
    assert not missing, (
        f"SR-INSPECT decision 12 does not list: {missing}\n\n"
        "`lenses.LEVERS` is what the report prints. A finding the record does "
        "not carry is a recommendation with no decision behind it."
    )


def test_the_record_names_no_finding_the_report_cannot_print() -> None:
    table = _record_table()
    extra = sorted(set(table) - set(LEVERS))
    assert not extra, (
        f"SR-INSPECT decision 12 lists findings `fux inspect` never prints: {extra}"
    )


def test_the_lever_text_is_the_same_text() -> None:
    """Byte-equal, unlike the verb tables.

    ⚠ **This one IS held equal on purpose, and the two cases are not in
    tension.** `.fux/README.md`'s verb table and SR-CLI's are written for
    different readers and say the same thing in different words. A lever is
    not prose: it is the literal string a consumer will act on, and *"use
    `.fuxignore`"* versus *"mark it `archived=`"* are different instructions.
    """
    table = _record_table()
    for finding, lever in sorted(LEVERS.items()):
        assert table[finding] == lever, (
            f"the lever for `{finding}` differs:\n"
            f"  code:   {lever}\n"
            f"  record: {table[finding]}"
        )
