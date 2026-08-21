"""Shared parsing for the ADR register — the single place both the ownership
twin (test_adr_ownership.py) and the freshness gate (test_adr_freshness.py)
read the register from, so they can never disagree about who owns what.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
REGISTER = ADR_DIR / "README.md"
OPEN_WORK = ROOT / "work" / "OPEN-WORK.md"
OPEN_DIR = ROOT / "work" / "open"

# A record's directory is its state. `docs/adr/` is live; `work/adr/` is
# superseded-pending (still in force, replacement planned); `archive/adr/` is
# superseded and may not back a live claim, so it is not scanned here.
RECORD_DIRS = (ADR_DIR, ROOT / "work" / "adr")


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
    """component -> owner (an `ADR-NAME` or a `W-nn` id), from the register."""
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


def owned_paths(table: dict[str, str] | None = None) -> list[str]:
    """Component paths, longest first (most specific wins on a prefix match)."""
    return sorted((table or ownership_table()), key=len, reverse=True)


def owner_of(changed: str, table: dict[str, str] | None = None) -> str | None:
    """The owner (`ADR-NAME` or `W-nn`) of `changed`, by longest-prefix match."""
    table = table or ownership_table()
    for p in owned_paths(table):
        if changed == p or changed.startswith(p + "/"):
            return table[p]
    return None


def register_names() -> dict[str, Path]:
    """ADR-NAME -> the record's file, from the register's record-listing table.

    The link may point into `docs/adr/` or `work/adr/`; it is resolved
    relative to the register, so the table stays the single source of both a
    record's name and its current state.
    """
    text = REGISTER.read_text(encoding="utf-8")
    names: dict[str, Path] = {}
    pattern = r"\[(\d{4})\]\(([^)]*\d{4}_[^)]+\.md)\)\s*\|\s*\*\*(ADR-[A-Z0-9-]+)\*\*"
    for m in re.finditer(pattern, text):
        names[m.group(3)] = (ADR_DIR / m.group(2)).resolve()
    return names


def open_work_ids() -> set[str]:
    return set(re.findall(r"\bW-\d{2}\b", OPEN_WORK.read_text(encoding="utf-8")))


def record_path_for(owner: str) -> Path | None:
    """The file that IS `owner`'s record — an ADR's own file, or a `W-nn`
    item's detail file under `work/open/`. `None` when it cannot be resolved
    (an unknown owner — test_adr_ownership.py's test_every_owner_resolves is
    what catches that; this function just declines to guess).
    """
    if owner.startswith("ADR-"):
        return register_names().get(owner)
    if re.fullmatch(r"W-\d{2}", owner):
        matches = sorted(OPEN_DIR.glob(f"{owner}-*.md"))
        return matches[0] if matches else None
    return None
