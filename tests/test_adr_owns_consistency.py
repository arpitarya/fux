"""Each record's `owns:` frontmatter key must agree with the register, exactly.

`docs/adr/README.md`'s ownership table is the single source of truth for who
owns what — but every record *also* declares its own claim, written by whoever
authored that record, at a different time than the table. Nothing stopped the
two from drifting apart until this test: three records were found claiming a
component the table gives to someone else (ADR-DOTFUX over-claimed `config.py`,
ADR-URL-INGEST and ADR-INDEX-LIFECYCLE both over-claimed a path already
reassigned elsewhere).

**The claim is machine-readable now, so the check is total.** It used to be a
prose bullet — `- **Owns:** \\`src/fux/query/\\` — \\`ask\\` is the base path; …` —
which forced this test to guess which backticked path was a claim and which was
context, and to special-case the conditional `Owns (on acceptance):` form. The
claim is an inline list in frontmatter (`owns: [src/fux/query]`), so:

1. every path a record claims must be given to that record by the table, **and**
2. every row of the table must appear in its owner's `owns:` list.

The second direction is new and is the one that catches a component silently
re-homed in the table while its record still believes it owns it.

**There is no conditional claim.** A record that does not own a component today
declares `owns: []`, whatever its status. The old `Owns (on acceptance)` form
let a record assert a claim the table did not honour and call the disagreement
intentional, which is indistinguishable from drift.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adr_lib import owner_of, ownership_table, register_names  # noqa: E402
from fux import frontmatter as fm  # noqa: E402


def declared_owns() -> dict[str, list[str]]:
    """ADR-NAME -> the `src/`/`tools/` paths its frontmatter claims."""
    result: dict[str, list[str]] = {}
    for name, path in register_names().items():
        if not path.exists():
            continue  # test_register_links_match_each_record_state's job
        meta = fm.parse(path.read_text(encoding="utf-8")).meta
        claims = meta.get("owns")
        if not isinstance(claims, list):
            continue  # test_adr_frontmatter.py's job
        result[name] = [str(c).strip("`").rstrip("/") for c in claims]
    return result


def test_every_declared_claim_is_granted_by_the_register() -> None:
    table = ownership_table()
    bad = []
    for name, claims in sorted(declared_owns().items()):
        for path in claims:
            owner = owner_of(path, table)
            if owner != name:
                bad.append(
                    f"{name} declares `owns: [… {path} …]`, but the register's "
                    f"ownership table gives it to {owner!r}"
                )
    assert not bad, (
        "\n".join(bad)
        + "\n\nEither fix the record's `owns:` key to match the register, or fix "
        "the register to match it — they must agree, and this test does not "
        "decide which one is wrong."
    )


def test_every_register_row_is_declared_by_its_owner() -> None:
    """The direction that catches a component re-homed in the table alone."""
    declared = declared_owns()
    missing = []
    for component, owner in sorted(ownership_table().items()):
        if not owner.startswith("ADR-"):
            continue  # a `W-nn` placeholder owner has no record to declare it
        if owner not in declared:
            continue  # test_every_owner_resolves is what catches an unknown name
        if component not in declared[owner]:
            missing.append(
                f"the register gives `{component}` to {owner}, and {owner}'s "
                f"`owns:` does not list it"
            )
    assert not missing, "\n".join(missing)


def test_no_path_is_claimed_by_two_records() -> None:
    claimants: dict[str, set[str]] = {}
    for name, claims in declared_owns().items():
        for path in claims:
            claimants.setdefault(path, set()).add(name)
    dupes = {p: names for p, names in claimants.items() if len(names) > 1}
    assert not dupes, "\n".join(
        f"{p} is claimed by more than one record's `owns:` key: {', '.join(sorted(names))}"
        for p, names in sorted(dupes.items())
    )
