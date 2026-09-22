---
type: OpenItem
id: W-211
title: "W-211 — the registry's tests follow the rules to their new home (SR-WORK-REGISTRY)"
description: "Arpit, 2026-09-22 (Cowork): DOC-REGISTRY.md became SR-WORK-REGISTRY (0067) — rules AND table; the work/ file is retired. test_doc_registry.py still reads work/DOC-REGISTRY.md (now missing) and must read §3 of the record; the gate-unreachable pin in test_sr_ownership.py lacks the new record. Ratified, not built; two red tests until it lands."
status: open
lane: agent
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: agent
ruled: 2026-09-22
---

# W-211 — the registry's tests follow the rules to their new home

**Model: Sonnet** — two edits under `tests/`, both mechanical, both named
below; nothing to design.

## ✅ BUILT AND CLOSED 2026-09-22 (Claude Code, Opus)

**Both edits landed, all five DoD items met, and the whole unit suite is green
for the first time since the registry moved** — 5 354 passed.

1. `tests/test_doc_registry.py` reads **§3 of the record**, bounded by the next
   `## ` heading so §1's and §2's tables are never read as rows, with line
   numbers kept whole-file so a failure names a line somebody can jump to.
   `_resolve` anchors on `records/`. The docstring says what the file does
   **not** check, per decision 11.
2. `tests/test_sr_ownership.py` — `SR-WORK-REGISTRY` is in the pin, beside
   SR-WORK-DOCS, with the reason it belongs there.
3. `tests/test_no_work_item_is_lost.py` — checked; two comments, no read. **No
   change**, as the item predicted.

🔴 **One thing the item did not predict, and it needed a sixth test.** A missing
*file* fails loudly; a renamed *section* fails **silently** — `rows()` returns
`[]` and every remaining check passes against an empty list. The old test was
safe from this by accident, because its input was a path. So
`test_the_table_was_actually_found` is now the **first** test in the file and
asserts the parse found more than twenty rows. ⚠ **This is the class the repo
calls a vacuous pass**, and moving a test's input from a file to a section of a
file is exactly the change that introduces it.

⚠ **Measured, not assumed:** 57 rows parse out of §3 and all 9 live `work/*.md`
resolve into them, so the inverse check is doing work rather than comparing two
empty sets.

**Also corrected in the record:** two Consequences bullets that spoke in the
future tense (*"it must read §3"*, *"until it lands"*) and one Reference line
(*"once W-211 lands"*) now say what is true.

---

## ✅ RULED 2026-09-22 (Arpit, Cowork) — ratified, not built

**The rulings:** *"convert DOC-REGISTRY.md into a law sr"* — offered a Law
(L12) or a WORK record, he chose the WORK record; then *"move everything in
DOC-REGISTRY into 0067_WORK-registry.md"*. The Cowork session wrote
[SR-WORK-REGISTRY](../../records/0067_WORK-registry.md) with the rules in §2
**and the whole table in §3**, retired `work/DOC-REGISTRY.md`, repointed every
live link and SR-WORK-DOCS decision 11, moved `tests/test_doc_registry.py` to
the new record in the ownership table, and regenerated the stamps. **It did
not touch `tests/`** — that is this item.

## Why the tree is red right now

Two tests, both in `tests/`:

1. `tests/test_doc_registry.py` opens `work/DOC-REGISTRY.md`, which no longer
   exists — every test in the file errors on the missing path.
2. `tests/test_sr_ownership.py::test_the_set_of_gate_unreachable_records_is_exactly_this`
   pins the set of records no `src/` change can reach. SR-WORK-REGISTRY owns
   one test and no code, exactly like SR-WORK-DOCS and SR-WORK-GOVERNANCE, so
   it belongs in the pin and is not in it:

```text
newly unreachable: ['SR-WORK-REGISTRY']
newly reachable:   []
```

(2026-09-22, from the Cowork bridge shell; the other doc/record suites pass.)

## Definition of done

1. `tests/test_doc_registry.py` reads the table from
   `records/0067_WORK-registry.md` — the rows between the `## §3 — The
   registry` heading and the next `## ` heading — instead of
   `work/DOC-REGISTRY.md`. Link targets in the rows are now relative to
   `records/`, so *every target exists* resolves from there. The
   *every live `work/` document has a row* check keeps its meaning; the
   registry itself is no longer under `work/` and needs no row (record
   decision 8). The module docstring points at decisions 5, 6, 7 and 8 and
   says, as decision 11 does, what the file does **not** check.
2. `tests/test_sr_ownership.py` — add `"SR-WORK-REGISTRY"` to
   `_UNREACHABLE_BY_THE_GATE`, next to `SR-WORK-DOCS`, with the two-line
   comment the neighbours carry: it owns `tests/test_doc_registry.py` and no
   code, and its subject — what a registry row owes — is unreachable from
   `src/` by construction.
3. `tests/test_no_work_item_is_lost.py` names `DOC-REGISTRY` in two comments
   only (checked 2026-09-22) — no change unless a read is found.
4. Both suites green, whole — `uv run pytest -q tests` and `tests_e2e`.
5. Bump the `tests/test_doc_registry.py` and `tests/test_sr_ownership.py` rows
   in SR-WORK-REGISTRY §3 and re-stamp (`python scripts/sr-hash.py --write`);
   `test_sr_ownership.py`'s trigger is *the ownership table changes — same
   change, always*, and it did.

## Out of scope

- Any change to what `test_doc_registry.py` checks beyond where it reads
  from. Decision 11 of the record says what it enforces and what it does not;
  this item moves the source and makes the docstring true, not the test
  stricter.
- The notes-column size question the record names in Consequences. That is a
  ruling, not a test.

## Key files

- `tests/test_doc_registry.py` (the path it reads, `REGISTRY = WORK / "DOC-REGISTRY.md"`, and the docstring)
- `tests/test_sr_ownership.py` (the pin, ~line 429)
- [`records/0067_WORK-registry.md`](../../records/0067_WORK-registry.md) — the rules the tests now serve
