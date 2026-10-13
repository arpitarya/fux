---
type: Report
run: 2026-10-11-ladder-gen5-rebuild
item: W-270
classification: surface capture
description: "The golden ladder rebuilt from scratch on generation 5's 118-document seed (W-272's seeds 89-112) — W-270 DoD 4. All eight rungs froze with every coverage count equal to its declaration, at engine 9ab19fc6 (src identical to b4d961cd). rung-00100 is 118 documents, the seed alone, by Arpit's ruling. The ext stream is a byte-identical subset of generation 4's. The generation-4 rungs were moved to golden-gen4/, not deleted."
filed: 2026-10-11
---

# REPORT — the golden ladder, rebuilt for generation 5

**Not a paired run.** It has no arms, no judged queries and no threshold, and
no question was asked of a rung. It is [phase 4](../../golden/README.md) of the
golden process, run because W-272 added seeds 89–112, and it is
[W-270](../../open/W-270-section-retest-set-6.md)'s DoD 4. **A surface capture:
no verdict, no per-query rows.** It ran **after** W-270's bar was frozen and
committed alone (`9ab19fc6`), as L13 and W-270 require.

## Authorship

🔴 **The honour declaration ([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) A23).**
One Claude Code session (Opus 5.5) did the whole run. **Its context has never
held a `set-6-claude` question.** Under `work/golden/` it read `seed/` and
`seed-dates.tsv` (through the builder and the name-leak search), the seed text
of 89–112 by `grep` for the name-leak search, `ladder/` and `README.md`. It
hashed `questions/set-6-claude.jsonl` for W-270's freeze table and counted its
lines, and opened no value in it. It touched neither spelling of the sealed-key
directory ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)).

⚠ **The ordering rule was not kept**, as on every rebuild since 2026-09-21:
`set-6-claude.jsonl` was committed (`17f79e1b`) before this build. The honour
rule is what protects this phase. Nothing in the generator, its seed or the
builder reads a question.

| artifact | author | could reach |
|---|---|---|
| `seed/` 89–112, `set-6-claude` | the designated prompt-14 chat (W-272) | its own questions |
| `build_golden_rung.py`, `make_golden_ext.py` (unmodified in fux-lab) | earlier sessions | none |
| [`evidence/build_from_worktree.py`](evidence/build_from_worktree.py) (gen 4's, body unchanged), [`evidence/make_golden_ext_gen4.py`](evidence/make_golden_ext_gen4.py) (copied unchanged), [`evidence/new_seed_name_leaks.py`](evidence/new_seed_name_leaks.py) (range changed to 89–112) | this session | none |

## What the check found

Before the build, `tests/test_golden_ladder_seed.py` failed **8 of 8**: every
rung lacked seeds 89–112.

## What was done

- **From scratch.** The gen-4 rungs were moved to
  `fux-lab/corpora/golden-gen4/` first. Corpora are kept (Arpit, 2026-09-12).
- **From a clean worktree at `9ab19fc6`** (branch `claude/gracious-galileo-aqrg8b`,
  W-270's bar commit). Its `src/` and `node/` equal `b4d961cd`, the engine W-270
  pins, so each rung's committed index is `fux.index.v8` with a section plane.
  ⚠ `main`'s engine (v7) reads these rungs only after `ingest --full`, which
  every arm does on its copy anyway.
- 🔴 **`rung-00100` is 118 documents** — the seed alone, no generated document.
  The seed (112 + 6 archived) is larger than the rung's headline size, so the
  builder refused `--count 100` (`ext_n = −18`). **Arpit ruled 2026-10-11:
  *keep it at 118 docs*** (offered: drop it · keep it at 118 · leave it stale).
  It is built with `--count 118` and is byte-for-byte `rung-seed`'s content
  (same index root).

| rung | docs | seed | ext | archived | superseded | mtime | build | index root |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| rung-seed | 118 | 118 | 0 | 6 | 12 | 118 | 28 s | `8166f9ce1944…` |
| rung-00100 | 118 | 118 | 0 | 6 | 12 | 118 | 24 s | `8166f9ce1944…` |
| rung-00200 | 200 | 118 | 82 | 14 | 20 | 200 | 39 s | `a78a3762ee93…` |
| rung-00500 | 500 | 118 | 382 | 44 | 50 | 500 | 90 s | `eccc591f3e11…` |
| rung-01000 | 1 000 | 118 | 882 | 94 | 100 | 1 000 | 174 s | `f8129a90de5e…` |
| rung-02000 | 2 000 | 118 | 1 882 | 194 | 200 | 2 000 | 315 s | `1f5684758bf2…` |
| rung-05000 | 5 000 | 118 | 4 882 | 494 | 500 | 5 000 | 509 s | `b3d92989d6c0…` |
| rung-10000 | 10 000 | 118 | 9 882 | 994 | 1 000 | 10 000 | 608 s | `48ee8c0b8b71…` |

- **On every rung, every declared count equals the indexed count**
  ([`build.log`](evidence/build.log)).
- **Superseded now exceeds archived** (gen 4: archived one above). Seeds
  107–112 are superseded by 89–94 and sit in `seed/`, not `seed/archive/`, as
  authored; that adds 6 superseded and no archived.
- **History (T11) unchanged:** 12 documents, 34 commits, 9 authors.
- **Validation:**
  - `tests/test_golden_ladder_seed.py`: **10 passed** (8 failed before).
  - `tools/differential/ladder_check.py`: *8 rungs, manifests consistent and nesting verified*.
  - `ref_edge_census.py`: **82 `ref` edges on every rung**, unchanged from gen 4; supersedes edges match the table.
  - **Determinism:** every ext line of the gen-5 manifests at `rung-00200`,
    `rung-01000` and `rung-10000` occurs, byte-identical, in gen 4's — 24 fewer
    per rung, 0 new.

## Name-leak search (seeds 89–112 against `rung-10000/ext/`)

[`evidence/new_seed_name_leaks.out`](evidence/new_seed_name_leaks.out): 414
tokens first appear in seeds 89–112, and 41 of them also occur in ext. **None
is a fact leak**, but these are retrieval hazards, the gen-4 pattern again:

- **Three first-name-plus-surname collisions with different people:** seeds'
  *Girish Pande*, *Sameer Joshi*, *Kavya Sharma* against ext's *Girish Pai*
  (649 documents), *Tanmay Joshi* (669), *Kavya Reddy* (618).
- **Six places** the generator's companies already use as sites, in 228–275
  ext documents each: Hubballi, Indore, Surat, Rajahmundry, Visakhapatnam,
  Chhatrapati Sambhajinagar.

The rest are dates and common words. A question naming one of these places
competes with a few hundred generated documents, which is the hard-negative
pressure the ladder exists to apply, not a defect.
