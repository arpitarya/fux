"""Ownership is a table, not a judgement call — and this test is its twin.

`docs/adr/README.md` carries the ownership table: which decision record owns
which component of `src/` and `tools/`. This test fails when the table and the
tree disagree, so a module cannot be added without someone deciding which
record it belongs to.

**Edit both in the same change.** The table and this file drift silently
otherwise, which is the failure mode the check exists to prevent.

A component with no decision yet is claimed by an open work item (`W-nn`)
instead of an ADR name. That id is resolved against `work/OPEN-WORK.md`, so a
`W-nn` that closes without rehoming its component fails this test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from adr_lib import ADR_DIR, RECORD_DIRS, ROOT, open_work_ids, ownership_table, register_names

# Roots whose components must every one be claimed.
CLAIMED_ROOTS = (ROOT / "src" / "fux", ROOT / "tools")

# Not components: caches, dotdirs, and the test trees of the tools themselves.
_IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache", "tests", "pruning"}


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------
# parsing


def records_on_disk() -> set[Path]:
    found: set[Path] = set()
    for d in RECORD_DIRS:
        found |= set(d.glob("[0-9][0-9][0-9][0-9]_*.md"))
    return found


# --------------------------------------------------------------------------
# the components that must be claimed


def components() -> set[str]:
    found: set[str] = set()
    for root in CLAIMED_ROOTS:
        if not root.exists():  # pragma: no cover - tree not built yet
            continue
        for child in sorted(root.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                if child.name in _IGNORED_DIR_NAMES:
                    continue
                found.add(_rel(child))
            elif child.suffix == ".py":
                found.add(_rel(child))
    return found


# --------------------------------------------------------------------------
# the checks


def test_every_component_is_claimed_by_a_record() -> None:
    table = ownership_table()
    unclaimed = sorted(components() - set(table))
    assert not unclaimed, (
        "these components are claimed by no ADR and by no open work item:\n  "
        + "\n  ".join(unclaimed)
        + "\n\nAdd a row to the ownership table in docs/adr/README.md (and keep "
        "this test in the same change)."
    )


def test_every_ownership_row_points_at_something_real() -> None:
    missing = sorted(c for c in ownership_table() if not (ROOT / c).exists())
    assert not missing, (
        "the ownership table claims components that do not exist:\n  " + "\n  ".join(missing)
    )


def test_every_owner_resolves() -> None:
    names, ids = register_names(), open_work_ids()
    bad = []
    for component, owner in sorted(ownership_table().items()):
        if owner.startswith("ADR-"):
            if owner not in names:
                bad.append(f"{component}: {owner} is not in the ADR register")
        elif re.fullmatch(r"W-\d{2}", owner):
            if owner not in ids:
                bad.append(
                    f"{component}: {owner} is not an open item in work/OPEN-WORK.md — "
                    "the item closed without rehoming this component"
                )
        else:
            bad.append(f"{component}: {owner!r} is neither an ADR name nor a W-nn id")
    assert not bad, "\n".join(bad)


def test_register_covers_every_record_on_disk() -> None:
    listed = {p.resolve() for p in register_names().values()}
    on_disk = {p.resolve() for p in records_on_disk()}
    missing = sorted(_rel(p) for p in on_disk - listed)
    phantom = sorted(str(p) for p in listed - on_disk)
    assert not missing and not phantom, (
        f"records on disk but not in the register: {missing}\n"
        f"records in the register but not on disk: {phantom}"
    )


def test_register_links_match_each_record_state() -> None:
    """A record's directory is its state — the register must point at the real one."""
    wrong = []
    for name, path in sorted(register_names().items()):
        if not path.exists():
            wrong.append(f"{name}: register points at {path}, which does not exist")
    assert not wrong, "\n".join(wrong)


def test_record_numbers_are_unique_within_a_directory() -> None:
    """Numbers are ordinals scoped to a directory and a generation.

    They restart when a record set is replaced, so `0001` may exist in more
    than one directory at once — nothing identifies a record by number. What
    must never happen is two records sharing a number in the SAME directory.
    """
    for d in RECORD_DIRS:
        seen: dict[str, str] = {}
        for path in sorted(d.glob("[0-9][0-9][0-9][0-9]_*.md")):
            num = path.name[:4]
            assert num not in seen, (
                f"{_rel(d)}: {path.name} and {seen[num]} both claim number {num}"
            )
            seen[num] = path.name


@pytest.mark.parametrize("name", sorted(register_names()))
def test_record_declares_its_own_name(name: str) -> None:
    """The register and the record must agree on the record's name.

    The record states it once, in frontmatter. It used to state it twice — a
    `name:` key and a `- **Name:**` bullet, written by hand at different times
    — and this test compared the register to the bullet, which is the copy that
    could drift from the key without anything noticing.
    """
    path = register_names()[name]
    m = re.search(r"^name:\s*(ADR-[A-Z0-9-]+)\s*$", path.read_text(encoding="utf-8"), re.M)
    assert m, f"{path.name} has no `name:` in its frontmatter — records are cited by name"
    assert m.group(1) == name, f"{path.name} declares {m.group(1)}, register says {name}"


def test_records_do_not_restate_the_laws() -> None:
    """A record that restates a cross-cutting principle is a bug (ADR-LAWS)."""
    handles = [
        "stdlib-only runtime",
        "no model in the maintenance path",
        # L8, added with the law on 2026-08-27. It caught a real paraphrase the
        # same day: ADR-QUALITY decision 11 was written as "bound by L8 —
        # hashed, bounded, local, off every committed and networked path", which
        # is the drift this test exists to stop. Cite the number, not the words.
        "hashed, bounded, and local",
    ]
    offenders = []
    for path in sorted(records_on_disk()):
        if path.name.endswith("_laws.md"):
            continue
        text = path.read_text(encoding="utf-8")
        for handle in handles:
            if handle in text:
                offenders.append(f"{path.name}: restates a law verbatim ({handle!r})")
    assert not offenders, (
        "\n".join(offenders)
        + "\n\nCite ADR-LAWS and the law number instead; the laws have one home."
    )


def test_mermaid_diagrams_carry_a_collapsed_ascii_twin() -> None:
    """§1's diagram is a Mermaid block plus a hand-paired ASCII twin.

    The twin is mandatory (a renderer is not always available) and collapsed
    (§1 is capped at one screen). Both halves are cheap to enforce and easy to
    forget, which is exactly what a check is for.

    ⚠ **This check used to read EVERY ```text fence as an ASCII twin, and that
    was wrong.** A record legitimately uses ```text for captured example output
    — `0048_fuxignore.md` has one twin and three output blocks — so the old
    rule reported three violations against a record that was correctly written,
    and the only way to "fix" it was to stop using ```text for examples.
    **Found 2026-08-27 by running the gate for the first time in a session that
    could run it**; the record was right and the test was not.

    The rule now PAIRS them positionally, which is what *"hand-paired twin"*
    always meant: for each Mermaid block, the **next** ```text fence after it is
    its twin, and that one must be collapsed. Fences that are not the next one
    after a diagram are examples, and none of this applies to them.
    """
    problems = []
    for path in sorted(records_on_disk()) + [ADR_DIR / "TEMPLATE.md"]:
        text = path.read_text(encoding="utf-8")
        if "```mermaid" not in text:
            continue
        for diagram in re.finditer(r"```mermaid\n.*?\n```", text, re.S):
            twin = re.search(r"```text\n.*?\n```", text[diagram.end():], re.S)
            if twin is None:
                problems.append(f"{path.name}: has a Mermaid block but no ASCII twin")
                continue
            start = diagram.end() + twin.start()
            end = diagram.end() + twin.end()
            before, after = text[:start], text[end:]
            open_tag = before.rfind("<details>")
            inside = open_tag != -1 and open_tag > before.rfind("</details>")
            if not (inside and after.lstrip().startswith("</details>")):
                problems.append(
                    f"{path.name}: the ASCII twin is not wrapped in a <details> block"
                )
            elif "\n\n```text" not in text[open_tag:end]:
                problems.append(
                    f"{path.name}: needs a blank line after </summary>, or the fence will not render"
                )
    assert not problems, "\n".join(problems)


def test_charts_name_the_source_of_their_numbers() -> None:
    """A chart's numbers are measured or computed, and the record says which.

    §1's Charts section is optional — most records should have none. When one
    is present, every number in it has to be traceable, or the chart is a
    drawing rather than evidence. The cheap enforceable form of that rule is a
    `source:` line inside the ASCII twin.
    """
    problems = []
    for path in sorted(records_on_disk()):
        text = path.read_text(encoding="utf-8")
        if "### Charts" not in text:
            continue
        charts = text.split("### Charts", 1)[1].split("\n## ", 1)[0]
        if "source:" not in charts:
            problems.append(
                f"{path.name}: has a Charts section with no 'source:' line — "
                "say which run or which constants the numbers come from"
            )
    assert not problems, "\n".join(problems)


# --------------------------------------------------------------------------
# describes — the second, additive relation (ADR-OWNERSHIP)


def test_every_described_component_also_has_an_owner() -> None:
    """Veto condition 1. `describes` must never become a way to avoid deciding
    an owner — a component with no owner fails whatever describes it."""
    from adr_lib import describes_table

    owners = ownership_table()
    owned = set(owners)
    orphans = [
        c
        for c in describes_table()
        if c not in owned and not any(c.startswith(p + "/") for p in owned)
    ]
    assert not orphans, (
        f"described but unowned: {sorted(orphans)} — `describes` is additive, "
        "never a substitute for `owns`"
    )


def test_no_record_describes_what_it_already_owns() -> None:
    """Veto condition 2. The row would be noise, and noise in a hand-maintained
    table is how the table stops being trusted."""
    from adr_lib import describes_table, owner_of

    owners = ownership_table()
    redundant = [
        f"{component} -> {record}"
        for component, records in describes_table().items()
        for record in records
        if owner_of(component, owners) == record
    ]
    assert not redundant, f"already owned, so the describes row is noise: {redundant}"


def test_every_describing_record_is_a_real_record() -> None:
    """A typo here is invisible: the gate would demand a record that cannot be
    resolved, and `owning_records` skips unresolvable owners by design."""
    from adr_lib import describes_table

    known = set(register_names())
    unknown = sorted(
        {r for records in describes_table().values() for r in records} - known
    )
    assert not unknown, f"describes names records that are not in the register: {unknown}"


def test_every_describes_row_states_a_reason() -> None:
    """Veto condition 4. A bare pair is unauditable — a later reader cannot tell
    a real relation from a defensive one."""
    import re as _re

    from adr_lib import REGISTER

    body = REGISTER.read_text(encoding="utf-8")
    body = body.split("<!-- DESCRIBES-TABLE-START -->", 1)[1]
    body = body.split("<!-- DESCRIBES-TABLE-END -->", 1)[0]
    thin = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0].lower() == "component":
            continue
        assert len(cells) >= 3, f"a describes row needs a reason cell: {line}"
        if len(cells[2]) < 40:
            thin.append(cells[0])
    assert not thin, f"describes rows with no real reason given: {thin}"


def test_the_describes_table_is_parsed_not_hard_coded() -> None:
    """The markers are the contract between the register and both tests.

    If they vanish, `describes_table()` raises rather than silently returning
    an empty relation — which would turn the widened gate back off with every
    test still green (veto condition 3, in its quietest form).
    """
    from adr_lib import REGISTER

    text = REGISTER.read_text(encoding="utf-8")
    assert "<!-- DESCRIBES-TABLE-START -->" in text
    assert "<!-- DESCRIBES-TABLE-END -->" in text


def test_the_freshness_gate_actually_consults_describers() -> None:
    """⚠ Veto condition 3, made mechanical.

    The widening is one line in `owning_records`. Deleting it leaves every
    other test in this suite green while the gate silently narrows back to
    owner-only — so assert the behaviour, not the line.
    """
    import test_adr_freshness as freshness

    table = ownership_table()
    touched = freshness.owning_records(["src/fux/query/__init__.py"], table)
    assert "ADR-ASK" in touched, "the owner must still be demanded"
    assert "ADR-CONFIDENCE" in touched, "a describer must be demanded too"
    assert "ADR-OUTPUT" in touched
