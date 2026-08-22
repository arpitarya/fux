"""Every filed verdict has a register row — ADR-RS veto 4, and its acceptance gate.

[ADR-RS](../docs/adr/0036_predictions.md) decision 3 says the prediction table
in `work/IMPLEMENTATION.md` **claims to be complete**. Nothing verified that
claim, and it was already false once: **R9** ran on 2026-08-22, passed, and was
cited in six documents while having no row. Nothing was wrong with the
measurement — what was missing was anything positioned to notice.

## The direction is the whole design

**Every filed verdict has a row. NOT every row has a verdict.**

Getting that backwards breaks the queue rather than protecting it: a **RETIRED**
id (R7, R8) has no verdict and never will, and a row that is registered but
unmeasured is the normal state of a live prediction. Only the other direction is
a defect — a measurement that happened and went unregistered.

## Two registers, one rule

Verdicts come in two flavours and both are checked here:

- the **`R` series** — the paper's architectural claims, `## Predictions`;
- **feature gates** — pre-registered and frozen exactly the same way, but not
  claims the paper makes, `## Feature gates`. `W44-SIGNAL` is the first.

A verdict whose id is in neither fails. That is what keeps "every measurement is
accounted for" true without an id having to be smuggled into the `R` series to
satisfy a checker.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fux import frontmatter as fm  # noqa: E402

REGRESSION = ROOT / "work" / "regression"
IMPLEMENTATION = ROOT / "work" / "IMPLEMENTATION.md"

#: The registers, by the heading that opens each one.
REGISTER_HEADINGS = ("## Predictions", "## Feature gates")

#: A plausible floor for how many verdicts exist. The check that silently finds
#: nothing is the failure mode this file exists to prevent, one level up — so it
#: asserts the walk worked before asserting anything about what it found.
MIN_VERDICTS = 5


def verdict_files() -> list[Path]:
    if not REGRESSION.is_dir():  # pragma: no cover - tree not built yet
        return []
    return sorted(
        p / "VERDICT.md"
        for p in REGRESSION.iterdir()
        if p.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-", p.name) and (p / "VERDICT.md").is_file()
    )


def _section(text: str, heading: str) -> str:
    """The body under `heading`, up to the next `## ` heading."""
    start = text.find(heading)
    if start < 0:
        return ""
    rest = text[start + len(heading) :]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def registered_ids() -> set[str]:
    """Every id with a row in either register.

    Reads the **first cell** of each table row, so an id merely *mentioned* in
    another row's prose is not mistaken for a registration — the difference
    between "R7 is named in R8's row" and "R7 has a row".
    """
    text = IMPLEMENTATION.read_text(encoding="utf-8")
    ids: set[str] = set()
    for heading in REGISTER_HEADINGS:
        for line in _section(text, heading).splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            first = line.split("|")[1].strip().strip("*` ")
            if first and first.lower() not in {"id", "---"} and not set(first) <= {"-", ":"}:
                ids.add(first)
    return ids


def verdict_prediction_id(path: Path) -> str:
    """The `prediction:` frontmatter key — never a grep for `R[0-9]`.

    Ids appear in prose all over this repo; the frontmatter is the only place
    a verdict *declares* what it ruled on.
    """
    return str(fm.parse(path.read_text(encoding="utf-8")).meta.get("prediction", "")).strip()


def test_the_walk_actually_found_verdicts() -> None:
    """A checker that passes because it found nothing is not a checker."""
    found = verdict_files()
    assert len(found) >= MIN_VERDICTS, (
        f"only {len(found)} VERDICT.md files found under {REGRESSION} — expected at least "
        f"{MIN_VERDICTS}. Either the walk is broken or the evidence store moved; both make "
        "every other assertion in this file vacuous."
    )


def test_the_registers_were_parsed() -> None:
    """Same guard, for the other half of the comparison."""
    ids = registered_ids()
    assert len(ids) >= MIN_VERDICTS, (
        f"parsed only {len(ids)} ids from {IMPLEMENTATION.name}'s registers ({sorted(ids)}). "
        f"Expected the tables under {list(REGISTER_HEADINGS)}; if a heading was renamed, "
        "rename it here in the same change."
    )


@pytest.mark.parametrize("path", verdict_files(), ids=lambda p: p.parent.name)
def test_every_filed_verdict_has_a_register_row(path: Path) -> None:
    """The check that would have caught R9."""
    pid = verdict_prediction_id(path)
    assert pid, f"{path.parent.name}/VERDICT.md declares no `prediction:` id"
    assert pid in registered_ids(), (
        f"{path.parent.name}/VERDICT.md rules on {pid!r}, which has no row in "
        f"{IMPLEMENTATION.name}'s registers.\n\n"
        f"A measurement that ran and was never registered is exactly the R9 failure: the "
        f"register claims to be complete (ADR-RS decision 3) and quietly is not.\n\n"
        f"Add a row under '## Predictions' (an `R` id) or '## Feature gates' (a feature gate)."
    )


def test_a_registered_id_needs_no_verdict() -> None:
    """The direction guard, asserted against a live fixture rather than a comment.

    R7 and R8 are **RETIRED** — registered, never measured, and no verdict will
    ever exist for them. If someone inverts this check to "every row has a
    verdict", this test fails and says why.
    """
    ruled = {verdict_prediction_id(p) for p in verdict_files()}
    retired = {"R7", "R8"} & registered_ids()
    assert retired, "expected R7/R8 to be registered as retired ids — has the register moved?"
    assert not (retired & ruled), (
        f"{sorted(retired & ruled)} has both a retired registration and a verdict — "
        "either the id was reused (ADR-RS forbids it) or this fixture is stale."
    )


def test_a_verdict_with_no_row_would_fail(tmp_path) -> None:
    """Asserted by construction, because the check that never fails is the one
    nobody notices is broken.

    This is the box that would have caught R9, exercised directly: an id that is
    not in either register must not be reported as registered.
    """
    assert "R-NONEXISTENT-42" not in registered_ids()
    fake = tmp_path / "VERDICT.md"
    fake.write_text(
        "---\ntype: Verdict\nname: FAKE\nverdict: PASS\nprediction: R-NONEXISTENT-42\n"
        "pre_registration: tools/nowhere/PRE-REGISTRATION.md\n---\n\nbody\n",
        encoding="utf-8",
    )
    assert verdict_prediction_id(fake) == "R-NONEXISTENT-42"
    assert verdict_prediction_id(fake) not in registered_ids(), (
        "an unregistered id must not resolve as registered — if this passes, the "
        "real check above cannot fail either"
    )


def test_prose_mentions_do_not_count_as_registration() -> None:
    """R8's row names R7, and R7's row names neither — only first cells register.

    Without this, a checker could be satisfied by an id appearing anywhere in
    the table's prose, which is how a register drifts into looking complete
    while a row is genuinely missing.
    """
    text = IMPLEMENTATION.read_text(encoding="utf-8")
    section = _section(text, "## Predictions")
    assert "R7" in section, "fixture stale: R7 should be registered"
    # A token that appears only inside prose, never as a first cell.
    assert "hook-at-scale" in section, "fixture stale: expected R5's prose to cite the fork"
    assert "hook-at-scale" not in registered_ids()
