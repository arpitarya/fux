---
type: Handoff
name: W-234
description: "Arpit's ruling 2026-09-28: the laws are reordered and renumbered densely. L13 (retired SR archived) becomes L1. L7 becomes Python >= 3.12. A new Node >= 22 law sits right after it as L8. Retired handles L5/L9 are reused. Old handles map through a dated table in SR-LAWS; live docs are repointed and frozen history is left as written."
item: W-234
filed: 2026-09-28
ball: agent
---

> **ARCHIVED 2026-09-28 — built as ruled.** Live successors: SR-LAWS decision 2a, SR-LAW-8, `tests/test_law_handles.py`.

# W-234 — the laws, reordered and renumbered

**Model: Opus** (every law citation in the repo, generated blocks, hooks, skills, packaging).

## ✅ RULED 2026-09-28 (Arpit, Cowork)

*"law 13 … renumber it to law 1, renumber rest of them, then law 7 which says
python 311, change it to Python 312 and create a new law for node similar to
Python … just after Python, renumber all the laws."* Then, via three questions:
- **History: mapping table.**
- **Node ≥ 22.**
- **Python 3.12 breaks in the next release.**

### The new table (L0 unchanged; record files reordered to match)

| new | law | was | record file (new) |
|---|---|---|---|
| **L0** | SRs are the only source of truth; Law records outrank | L0 | `0002_LAW-0-authority.md` |
| **L1** | A retired SR is archived, never deleted | **L13** | `0003_LAW-1-retired-records-archived.md` |
| **L2** | `$0`, FOSS-only | L1 | `0004_LAW-2-zero-cost.md` |
| **L3** | Content is never durable outside its source | L2 | `0005_LAW-3-content-never-durable.md` |
| **L4** | Deterministic: no model in the maintenance path | L3 | `0006_LAW-4-deterministic.md` |
| **L5** | Offline by default | L4 | `0007_LAW-5-offline-by-default.md` |
| **L6** | Say "index", not "db" | L6 | `0008_LAW-6-say-index.md` |
| **L7** | **Python ≥ 3.12** (was ≥ 3.11) | L7 | `0009_LAW-7-python-312.md` |
| **L8** | **NEW: Node ≥ 22**, the Node twin of L7 | — | `0010_LAW-8-node-22.md` |
| **L9** | A use record is never committed | L8 | `0011_LAW-9-use-record.md` |
| **L10** | The consumer is served build output | L10 | `0012_LAW-10-bundled-output.md` |
| **L11** | The golden answer key is Arpit's custody | L11 | `0013_LAW-11-sealed-answer-key.md` |
| **L12** | Every value lives in a config file | L12 | `0014_LAW-12-values-live-in-config.md` |

Unchanged handles: **L0, L6, L7, L10, L11, L12**. L11 especially keeps its
number: hooks, guards and CLAUDE.md cite it everywhere.

### Rulings this carries

1. **Retired handles are reused.** L5 and L9 now name live laws. This
   **overrides** SR-LAWS's *"the handle is never reused"* for L5/L9, and that
   sentence is amended. The archived SR-LAW-5 (hashed meta) and the retired L9
   (environments, now SR-WORK-ENVIRONMENTS) are named in the mapping table as
   the *pre-2026-09-28* meanings.
2. **History: a mapping table.** SR-LAWS carries **"Handles before 2026-09-28 → now"**:
   - L1→L2, L2→L3, L3→L4, L4→L5, L8→L9, L13→L1;
   - old L5 = retired hashed meta (archived);
   - old L9 = retired environments law.
   Every **live** doc, record, test, hook, skill, steering file, template and
   code comment is repointed in **one change**. **`archive/` and past WORKLOG
   entries are left as written** (SR-WORK-ARCHIVE d11; WORKLOG append-only).
   They are read by date through the table.
3. **L7: Python ≥ 3.12**, breaking in the next release:
   - `requires-python = ">=3.12"`;
   - the CI matrix drops 3.11;
   - CHANGELOG under **Breaking**.
   The law text states what 3.12 permits beyond `tomllib` (L7's old reason).
4. **L8 (new): Node ≥ 22.** This is the Node read plane's floor, the way L7 is
   Python's:
   - `node/package.json` `engines.node = ">=22"`;
   - the published bundle's engines;
   - CI;
   - CHANGELOG under **Breaking**.
   Rationale in the record: Node 20 is past end-of-life (April 2026, as far as
   Arpit's session knew; **verify before writing the record**), and 22 is the
   oldest LTS still supported. Note: L12 values-in-config does not apply to a
   version floor, which is a law, not a tunable.

## Definition of done (one change)

- **Records:**
  - rename and renumber the files per the table;
  - update each record's `id`/handle and frontmatter;
  - SR-LAWS: the new table, the mapping table, the retired-handle amendment;
  - records/README: the register rows and the `0001–0050` range note.
- **Write SR-LAW-8 (Node).** Amend **SR-LAW-7** to 3.12.
- **Repoint every live citation.** Do a scripted **simultaneous** substitution
  (L3→L4 and L4→L5 in one pass, never chained), scoped to live trees only,
  **excluding `archive/` and existing WORKLOG entries**. Then do a hand review
  of every hit: prose like "L3 cache" or "rung L4" is not a law.
- **Regenerate** the CLAUDE.md laws block (`scripts/gen-laws.py --write`) and
  the golden block. `test_claude_md_laws.py` green.
- **Skills, steering, `.claude/rules`, hooks, agents files:**
  - repoint the law handles;
  - `guard-*.sh` messages cite L11 (unchanged), but check them anyway.
- **Packaging:** `pyproject.toml`, `node/package.json`, the CI matrix,
  CHANGELOG under Breaking.
- **Test:** add a check that every `L<n>` handle cited in a live doc exists in
  SR-LAWS's current table. It catches stale handles after a renumber.
- Both suites whole, green. Archive W-234.

## Traps

- **L3 is the most cited law.** A chained replace (L3→L4 then L4→L5) turns
  every deterministic citation into "offline". Substitute simultaneously.
- **Golden-tree guard:** repointing is a repo-wide text edit. Never walk
  `work/golden/` (L11). Use explicit roots with `--exclude-dir=golden`, and no
  heredocs quoting commands (W-230).
- Archived files that link into `records/0003…0014` will now point at renamed
  files. Archive links are never repaired (SR-WORK-ARCHIVE d11), and that is
  accepted.
