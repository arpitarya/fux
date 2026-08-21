"""Each record's own `**Owns:**` line must agree with the register.

`docs/adr/README.md`'s ownership table is the single source of truth for who
owns what — but every record *also* carries its own `**Owns:**` line (or
`**Owns (on acceptance):**` / `**Owns (on build):**` for a claim that only
becomes real once the record's status changes), written by whoever authored
that record, by hand, at a different time than the table. Nothing stopped the
two from drifting apart until this test: three records were found claiming a
component the table gives to someone else (ADR-DOTFUX over-claimed
`config.py`, ADR-URL-INGEST and ADR-INDEX-LIFECYCLE both over-claimed a path
already reassigned elsewhere) — this is what PRIORITY.md's P1 calls
"overlapping `Owns:`".

**Only unqualified `Owns:` lines are active claims.** `Owns (on acceptance):`
and `Owns (on build):` are deliberately conditional — the record is not
accepted or not built yet, so the table correctly does not (yet) point at it,
and that is not a drift to report.

**A bullet that starts with prose ("no module", "nothing yet", "nothing in
`src/`") claims nothing right now**, even if it mentions a path later while
explaining where that path actually lives. Only a bullet whose value starts
immediately with a backtick path is an active claim, and only the paths
before its first em-dash count — text after the dash is context (what moved
where, what a sibling record owns), not part of the claim.
"""

from __future__ import annotations

import re

from adr_lib import owner_of, ownership_table, register_names

_OWNS_LINE = re.compile(r"^- \*\*Owns(\s*\([^)]*\))?:\*\*\s*(.*)$")
_PATH = re.compile(r"`((?:src|tools)/[^`]+)`")


def _owns_bullet(text: str) -> tuple[bool, str] | None:
    """(qualified, the bullet's full value text) for a record's Owns line."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _OWNS_LINE.match(line)
        if not m:
            continue
        qualified = m.group(1) is not None
        chunk = [m.group(2)]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not lines[j].lstrip().startswith("- **"):
            chunk.append(lines[j].strip())
            j += 1
        return qualified, " ".join(chunk)
    return None


def _active_claims(bullet: str) -> list[str]:
    bullet = bullet.strip()
    if not bullet.startswith("`"):
        return []
    head = bullet.split("—", 1)[0]
    return [p.rstrip("/") for p in _PATH.findall(head)]


def active_owns() -> dict[str, list[str]]:
    """ADR-NAME -> the `src/`/`tools/` paths it actively claims right now."""
    result: dict[str, list[str]] = {}
    for name, path in register_names().items():
        if not path.exists():
            continue  # test_register_links_match_each_record_state's job
        parsed = _owns_bullet(path.read_text(encoding="utf-8"))
        if parsed is None:
            continue  # no Owns line at all — a template/malformed record, not this test's job
        qualified, bullet = parsed
        if qualified:
            continue
        claims = _active_claims(bullet)
        if claims:
            result[name] = claims
    return result


def test_owns_line_is_a_subset_of_the_register() -> None:
    table = ownership_table()
    bad = []
    for name, claims in sorted(active_owns().items()):
        for path in claims:
            owner = owner_of(path, table)
            if owner != name:
                bad.append(
                    f"{name}'s Owns: line claims `{path}`, but the register's "
                    f"ownership table gives it to {owner!r}"
                )
    assert not bad, (
        "\n".join(bad)
        + "\n\nEither fix the Owns: line to match the register, or fix the "
        "register to match the Owns: line — they must agree, and this test "
        "does not decide which one is wrong."
    )


def test_no_path_is_claimed_by_two_records_owns_lines() -> None:
    claimants: dict[str, set[str]] = {}
    for name, claims in active_owns().items():
        for path in claims:
            claimants.setdefault(path, set()).add(name)
    dupes = {p: names for p, names in claimants.items() if len(names) > 1}
    assert not dupes, "\n".join(
        f"{p} is claimed by more than one record's Owns: line: {', '.join(sorted(names))}"
        for p, names in sorted(dupes.items())
    )
