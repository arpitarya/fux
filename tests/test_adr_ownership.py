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

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
REGISTER = ADR_DIR / "README.md"
OPEN_WORK = ROOT / "work" / "OPEN-WORK.md"

# A record's directory is its state. `docs/adr/` is live; `work/adr/` is
# superseded-pending (still in force, replacement planned); `archive/adr/`
# is superseded and may not back a live claim, so it is NOT scanned here.
RECORD_DIRS = (ADR_DIR, ROOT / "work" / "adr")

# Roots whose components must every one be claimed.
CLAIMED_ROOTS = (ROOT / "src" / "fux", ROOT / "tools")

# Not components: caches, dotdirs, and the test trees of the tools themselves.
_IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache", "tests", "pruning"}


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------
# parsing


def _table_rows(text: str, start: str, end: str) -> list[list[str]]:
    body = text.split(start, 1)[1].split(end, 1)[0]
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() in {"component", "#"}:
            continue
        rows.append(cells)
    return rows


def ownership_table() -> dict[str, str]:
    rows = _table_rows(
        REGISTER.read_text(encoding="utf-8"),
        "<!-- OWNERSHIP-TABLE-START -->",
        "<!-- OWNERSHIP-TABLE-END -->",
    )
    table: dict[str, str] = {}
    for cells in rows:
        component = cells[0].strip("`").rstrip("/")
        owner = cells[1].strip().strip("*").strip("`")
        assert component not in table, f"{component} is claimed twice in the ownership table"
        table[component] = owner
    return table


def records_on_disk() -> set[Path]:
    found: set[Path] = set()
    for d in RECORD_DIRS:
        found |= set(d.glob("[0-9][0-9][0-9][0-9]_*.md"))
    return found


def register_names() -> dict[str, Path]:
    """ADR-NAME -> the record's file, from the register table.

    The link may point into `docs/adr/` or `work/adr/`; it is resolved
    relative to the register, so the table stays the single source of both
    a record's name and its current state.
    """
    text = REGISTER.read_text(encoding="utf-8")
    names: dict[str, Path] = {}
    pattern = r"\[(\d{4})\]\(([^)]*\d{4}_[^)]+\.md)\)\s*\|\s*\*\*(ADR-[A-Z0-9-]+)\*\*"
    for m in re.finditer(pattern, text):
        names[m.group(3)] = (ADR_DIR / m.group(2)).resolve()
    return names


def open_work_ids() -> set[str]:
    return set(re.findall(r"\bW-\d{2}\b", OPEN_WORK.read_text(encoding="utf-8")))


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
    """The register and the record must agree on the record's name."""
    path = register_names()[name]
    head = path.read_text(encoding="utf-8")[:2000]
    m = re.search(r"^- \*\*Name:\*\* `(ADR-[A-Z0-9-]+)`", head, re.M)
    assert m, f"{path.name} has no '- **Name:**' line — records are cited by name, not number"
    assert m.group(1) == name, f"{path.name} declares {m.group(1)}, register says {name}"


def test_records_do_not_restate_the_laws() -> None:
    """A record that restates a cross-cutting principle is a bug (ADR-LAWS)."""
    handles = ["stdlib-only runtime", "no model in the maintenance path"]
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
    """
    problems = []
    for path in sorted(records_on_disk()) + [ADR_DIR / "TEMPLATE.md"]:
        text = path.read_text(encoding="utf-8")
        if "```mermaid" not in text:
            continue
        if "```text" not in text:
            problems.append(f"{path.name}: has a Mermaid block but no ASCII twin")
            continue
        for m in re.finditer(r"```text\n.*?\n```", text, re.S):
            before = text[: m.start()]
            after = text[m.end() :]
            open_tag = before.rfind("<details>")
            close_before = before.rfind("</details>")
            inside = open_tag != -1 and open_tag > close_before
            if not (inside and after.lstrip().startswith("</details>")):
                problems.append(
                    f"{path.name}: the ASCII twin is not wrapped in a <details> block"
                )
            elif "\n\n```text" not in text[open_tag : m.end()]:
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
