"""Every `fux doctor` row has a register entry, and every entry names a live row.

**[SR-DOCTOR](../records/0152_doctor.md)'s register is §2's table**, and it is a
hand-maintained list of what a command produces. Nothing compared them, so a row
added in code and not registered was invisible to review, and a registered row
whose check was renamed or deleted went on reading as authority.

## The code is the fact, in both directions

A row that exists and is unregistered is an undocumented surface. A row that is
registered and does not exist is worse: the record says `fux doctor` reports
something it does not, which is a promise a reader cannot check without running
the command and counting.

## Why the names are read by RUNNING doctor, not by parsing `doctor.py`

The item's wording was *"enumerate the `Check` producers in `doctor.py`"*. A
static scan finds the `Check(...)` constructor calls — and the row's **name** is
frequently a literal inside a branch, several per function, with more than one
function returning rows conditionally. Running the command on an empty directory
produces exactly the set a user sees, which is the set the register is about.

⚠ **The cost of that choice, stated:** a row that only appears under a condition
this fixture does not create would go unchecked. `_daemon` is the live example —
it returns `None` unless a daemon is configured — so it is listed in
`CONDITIONAL` below by name, which is the narrow, visible form of the exemption.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from fux import doctor

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "records" / "0152_doctor.md"

#: Rows a bare directory cannot produce, each with the condition it needs.
#:
#: ⚠ **By name, never by pattern.** A regex exemption would quietly grow to
#: cover rows nobody meant to exempt, which is how a gate stops gating.
CONDITIONAL = {
    "url daemon": "`_daemon` returns None unless a refresh daemon is configured",
}


def _live_rows() -> set[str]:
    """Every row name `fux doctor` produces on a bare git checkout."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        return {c.name for c in doctor.run(root)}


def _registered_rows() -> set[str]:
    """Every row name the record's register names, from its first table column.

    A register cell may hold several names for one shared implementation —
    ``tune.toml current` · `output.toml current`` — so every backticked name in
    the cell counts, not just the first.
    """
    out: set[str] = set()
    for line in RECORD.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cell = line.strip().strip("|").split("|", 1)[0]
        out |= set(re.findall(r"`+([^`]+)`+", cell))
    return {name.strip("` ") for name in out if name.strip("` ")}


def test_the_two_sets_were_actually_found():
    """A collector that matches nothing is a test that always passes."""
    assert len(_live_rows()) > 20, f"only {len(_live_rows())} live rows — doctor.run moved"
    assert len(_registered_rows()) > 20, "the register table was not parsed — its shape moved"


def test_every_live_row_is_registered():
    """A row in code and not in the register is an undocumented surface."""
    unregistered = sorted(_live_rows() - _registered_rows())
    assert not unregistered, (
        "these `fux doctor` rows have no entry in SR-DOCTOR's register:\n  "
        + "\n  ".join(unregistered)
        + "\n\nAdd a row to the register naming what it fires on, its level, and "
        "the record that decided it — in the same change that adds the check."
    )


def test_every_registered_row_still_exists():
    """A register naming a row that is gone is a promise nobody can check."""
    live = _live_rows()
    phantom = sorted(name for name in _registered_rows() - live if name not in CONDITIONAL)
    assert not phantom, (
        "SR-DOCTOR's register names rows `fux doctor` does not produce:\n  "
        + "\n  ".join(phantom)
        + "\n\nIf the check was renamed, rename the register row. If it was removed, "
        "delete the row and say in the record what replaced it. If it fires only "
        "under a condition this test's bare fixture cannot create, add it to "
        "`CONDITIONAL` BY NAME with that condition."
    )


def test_every_conditional_exemption_is_still_registered():
    """An exemption for a row nobody registers any more is dead weight.

    It also hides the opposite defect: a name in `CONDITIONAL` that the register
    dropped would make `test_every_registered_row_still_exists` pass by
    exempting something it is no longer asked about.
    """
    stale = sorted(set(CONDITIONAL) - _registered_rows())
    assert not stale, f"exempted but no longer in the register: {stale}"
