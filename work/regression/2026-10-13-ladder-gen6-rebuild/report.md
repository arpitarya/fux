---
type: Report
run: 2026-10-13-ladder-gen6-rebuild
item: W-278
classification: surface capture
description: "The golden ladder rebuilt from scratch on generation 6's 188-document seed (W-277's seeds 113–182) — W-278 DoD 5 step 1. All eight rungs froze with every coverage count equal to its declaration, at a clean worktree of 2ac82d3b (src identical to 08ef6293). rung-00100 is 188 documents, the seed alone, by generation 5's ruling applied again. rung-10000 took 12 h: its commits are gpg-signed and signing blocked. The generation-5 rungs were moved to golden-gen5/, not deleted."
filed: 2026-10-13
---

# REPORT — the golden ladder, rebuilt for generation 6

**Not a paired run.** No arms, no judged queries, no threshold; no question
was asked of a rung. It is [phase 4](../../golden/README.md) of the golden
process and [W-278](../../open/W-278-section-term-v3.md)'s DoD 5 step 1. **A
surface capture: no verdict, no per-query rows.** It ran **after** W-278's bar
was frozen and committed alone (`2ac82d3b`).

## Authorship

🔴 **The honour declaration ([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) A23).**
One Claude Code session (Opus 5.5) did the whole run. **Its context has never
held a `set-7-claude` question.** Under `work/golden/` it read `seed/` and
`seed-dates.tsv` (through the builder and the name-leak search), `ladder/` and
`README.md`. It hashed `questions/set-7-claude.jsonl` for W-278's freeze table
and counted its lines, and opened no value in it. It touched neither spelling
of the sealed-key directory ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)).

| artifact | author | could reach |
|---|---|---|
| `seed/` 113–182, `set-7-claude` | the designated prompt-15 chat (W-277) | its own questions |
| `build_golden_rung.py`, `make_golden_ext.py` (unmodified in fux-lab) | earlier sessions | none |
| [`evidence/build_from_worktree.py`](evidence/build_from_worktree.py) (gen 5's, body unchanged), [`evidence/make_golden_ext_gen4.py`](evidence/make_golden_ext_gen4.py) (copied unchanged), [`evidence/new_seed_name_leaks.py`](evidence/new_seed_name_leaks.py) (range 113–182) | this session | none |

## What was done

- **From scratch.** The gen-5 rungs were moved to `fux-lab/corpora/golden-gen5/`.
  Corpora are kept (Arpit, 2026-09-12).
- **From a clean worktree at `2ac82d3b`**, its own venv (Python 3.14). A first
  attempt with the shell's `python3` (3.9, no `tomllib`) failed on `rung-seed`
  and was discarded before any rung froze.
- 🔴 **`rung-00100` is 188 documents**, the seed alone: generation 5's ruling
  (*keep it at the seed's size*) applied again.

| rung | docs | archived | superseded | mtime | build | index root |
|---|---:|---:|---:|---:|---:|---|
| rung-seed | 188 | 6 | 20 | 188 | 34 s | `b027fd5e73bf…` |
| rung-00100 | 188 | 6 | 20 | 188 | 35 s | `b027fd5e73bf…` |
| rung-00200 | 200 | 8 | 22 | 200 | 34 s | |
| rung-00500 | 500 | 37 | 51 | 500 | 92 s | |
| rung-01000 | 1 000 | 87 | 101 | 1 000 | 168 s | `b726d2294a51…` |
| rung-02000 | 2 000 | 187 | 201 | 2 000 | 296 s | |
| rung-05000 | 5 000 | 487 | 501 | 5 000 | 508 s | |
| rung-10000 | 10 000 | 987 | 1 001 | 10 000 | **43 690 s** | `31fb07827657…` |

- **Every declared count equals the indexed count** ([`build.log`](evidence/build.log)); roots for every rung are in `work/golden/ladder/rung-*.index`.
- ⚠ **rung-10000 took 12 h.** The builder's per-date commits inherit
  `commit.gpgsign = true`; signing blocked from 01:16 until 13:23 (11 s of CPU
  in that time). The rung is correct — it froze with every count matching —
  but the next build should not sign: [W-281](../../open/W-281-capture-harness-speed.md).
- **Validation:** `tests/test_golden_ladder_seed.py` **10 passed** (8 failed
  before); `tools/differential/ladder_check.py`: *8 rungs, manifests consistent
  and nesting verified*.

## Name-leak search (seeds 113–182 against `rung-10000/ext/`)

[`evidence/new_seed_name_leaks.out`](evidence/new_seed_name_leaks.out): 610
tokens first appear in seeds 113–182, 49 also in ext. **No fact leak.**
Retrieval hazards only: first names *Devika, Pallavi, Ritika, Sneha*, the
surname *Sethi*, and the places *Jalandhar* and *Ludhiana*; the rest are dates
and common words.
