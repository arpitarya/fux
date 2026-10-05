---
type: Report
run: 2026-10-05-ladder-gen4-rebuild
item: W-240
classification: surface capture
description: "The golden ladder rebuilt from scratch on generation 4's 94-document seed (prompt 12's section documents 63–82, prompt 13's planted misfits 83–88). All eight rungs froze with every coverage count equal to its declaration, at engine ba1c0e44 (3.0.0-alpha.11). rung-00100 now holds only 6 ext documents, which forced two driver changes, both filed. The generation-3 rungs were moved to golden-gen3/, not deleted. W-228's families lens then found all 3 planted misfits on all eight rungs and flagged none of the 3 controls."
filed: 2026-10-05
---

# REPORT — the golden ladder, rebuilt for generation 4

**Not a paired run.** It has no arms, no judged queries and no threshold, and
no question was asked of a rung. It is [phase 4](../../golden/README.md) of the
golden process, run because generation 4 added seeds 63–88. It then re-runs
W-228's `families` lens against the committed answer list
[`planted-misfits.tsv`](../../golden/planted-misfits.tsv). That list describes
document shape and is not an L11 key. **This is a surface capture. It files no
verdict and has no per-query rows.**

## Authorship

🔴 **The honour declaration ([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) A23).**
One Claude Code session (Opus 5.5, worktree `worktree-agent-a0e9471b763f1c99c`)
did the whole run. Its context has never held a question of any set. Under
`work/golden/` it read only these:
- `seed/` (with `seed/archive/`), `seed-dates.tsv` and `seed-history*`, through the builder;
- the seed text of 63–88, for the name-leak search;
- `planted-misfits.tsv`, `ladder/` and `README.md`;
- one prompt file: it read the header of `prompts/13-…`, then deleted the file.

It did not open, list, grep, hash or stat `questions/`. It touched neither
spelling of the sealed-key directory ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)).

⚠ **The ordering rule was not kept**, as on every rebuild since 2026-09-21.
`questions/set-5-claude.jsonl` was committed (`1c99b136`) before this build, so
the honour rule is all that protects this phase. Nothing in the generator, its
seed or the builder reads a question. Both driver changes below are committed,
so anyone can re-derive the bytes.

| artifact | author | could reach |
|---|---|---|
| `seed/` 63–82, `set-5-claude` | the designated prompt-12 chat | its own questions |
| `seed/` 83–88, `planted-misfits.tsv` | the designated prompt-13 chat | no questions (prompt 13 wrote none) |
| `build_golden_rung.py`, `make_golden_ext.py` (both unmodified in fux-lab) | earlier sessions | none |
| [`evidence/build_from_worktree.py`](evidence/build_from_worktree.py), [`evidence/make_golden_ext_gen4.py`](evidence/make_golden_ext_gen4.py), [`evidence/families_check.sh`](evidence/families_check.sh), [`evidence/check_planted.py`](evidence/check_planted.py), [`evidence/new_seed_name_leaks.py`](evidence/new_seed_name_leaks.py) | this session | none |

## What the check found

Before the build, `tests/test_golden_ladder_seed.py` failed **8 of 8**: every
rung lacked seeds 63–88. `ladder_check.py` passed, because the eight manifests
agreed with each other. The 68 older seeds were unchanged.

## What was done

- **From scratch, the 2026-09-27 way.** The gen-3 rungs were moved to
  `fux-lab/corpora/golden-gen3/` before the builder's `rmtree` could reach them.
  No process held them open. Corpora are kept (Arpit, 2026-09-12).
- **From a clean worktree at `ba1c0e44`.** That is main's `a9090e1f`
  (3.0.0-alpha.11) plus the prompt-13 deletion. Its engine source is identical
  to `a9090e1f`. The worktree held no uncommitted change while the rungs were built.
- **Two attempts failed before the clean build, both at `rung-00100`.** Each
  failure left the rung unfrozen, and each led to a driver change. The full
  diagnosis is in [ANALYSIS](ANALYSIS.md) §1.
  1. `configured source not found: 'ext/archive'`. The 6 ext documents include
     no archived one.
  2. `supersedes: targets not in the rung: a19, a20`. The authored hard
     negatives a05 and a06 supersede a19 and a20, which sort last.

  The clean build ran all eight rungs in one pass
  ([`build.log`](evidence/build.log)).

| rung | docs | seed | ext | archived | superseded | mtime | build | index root |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| rung-seed | 94 | 94 | 0 | 6 | 6 | 94 | 25 s | `6c830596fa03…` |
| rung-00100 | 100 | 94 | 6 | 7 | 7 | 100 | 24 s | `c7938af2021c…` |
| rung-00200 | 200 | 94 | 106 | 17 | 16 | 200 | 44 s | `af2fdf859365…` |
| rung-00500 | 500 | 94 | 406 | 47 | 46 | 500 | 106 s | `af538d6f921d…` |
| rung-01000 | 1 000 | 94 | 906 | 97 | 96 | 1 000 | 184 s | `5038b32b398d…` |
| rung-02000 | 2 000 | 94 | 1 906 | 197 | 196 | 2 000 | 471 s | `f3c2bbae824f…` |
| rung-05000 | 5 000 | 94 | 4 906 | 497 | 496 | 5 000 | 654 s | `4041a8cda756…` |
| rung-10000 | 10 000 | 94 | 9 906 | 997 | 996 | 10 000 | 695 s | `842145ea168c…` |

- Engine `fux 3.0.0-alpha.11` at commit `ba1c0e44`. **On every rung, every
  declared count equals the indexed count.**
- **From rung-00200 up, archived is one more than superseded.** These rungs cut
  the generated stream after a slot-5 retired document and before its slot-6
  successor. So each holds one archived document that nothing supersedes. Both
  counts match their declarations. See ANALYSIS §2.
- **History (T11) is unchanged on every rung:** 12 documents, 34 commits,
  9 authors. Generation 4 adds no history.
- **Validation:**
  - `tests/test_golden_ladder_seed.py`: 10 passed (8 failed before).
  - `tools/differential/ladder_check.py`: *8 rungs, manifests consistent and
    nesting verified*, exit 0.
  - `ref_edge_census.py --corpora fux-lab/corpora/golden`: **82 `ref` edges on
    every rung**, unchanged. Supersedes edges match the table.

## The `families` lens against the planted misfits (W-228 DoD 11)

The script was [`evidence/families_check.sh`](evidence/families_check.sh). It
ran on scratch copies of all eight rungs, and the kept rungs were not touched.
It ran `fux inspect --json --top 1000` twice per rung, and the two `families`
sections were byte-equal on all eight. The thresholds were the template's:
`skeleton_jaccard 0.60`, `core_share 0.80`, `misfit_floor 0.20` (provisional).
Per-rung output: [`planted-check.out`](evidence/planted-check.out). Lens output:
[`families-rung-seed.json`](evidence/families-rung-seed.json),
[`families-rung-01000.json`](evidence/families-rung-01000.json) and
[`families-rung-10000.json`](evidence/families-rung-10000.json).

| rung | families | misfits | `misfit_share` | flagged | planted found | controls flagged | unplanted |
|---|---:|---:|---:|---|---:|---:|---:|
| rung-seed | 8 | 3 | 10.7 % | no | **3 / 3** | **0 / 3** | 0 |
| rung-00100 | 10 | 3 | 9.4 % | no | **3 / 3** | **0 / 3** | 0 |
| rung-00200 | 22 | 4 | 3.3 % | no | **3 / 3** | **0 / 3** | 1 |
| rung-00500 | 23 | 4 | 1.0 % | no | **3 / 3** | **0 / 3** | 1 |
| rung-01000 | 23 | 17 | 1.9 % | no | **3 / 3** | **0 / 3** | 14 |
| rung-02000 | 23 | 32 | 1.7 % | no | **3 / 3** | **0 / 3** | 29 |
| rung-05000 | 23 | 75 | 1.6 % | no | **3 / 3** | **0 / 3** | 72 |
| rung-10000 | 23 | 146 | 1.5 % | no | **3 / 3** | **0 / 3** | 143 |

- **The lens finds each misfit with the right heading.** The mapping-study
  family has 7 members and the lane-qualification family has 6, and every new
  document joined its family. TMS-45 lacks `5. Requalification`, TMS-46 lacks
  `2. Probe grid`, and LQ-54 lacks `4. Conditions`. The three controls are
  members, and none is listed as a misfit.
- **Two corrections are noted here rather than silently applied:**
  - The first pass scored 0/3. The TSV names a heading bare
    (`Requalification`), while the document numbers it (`5. Requalification`).
    `check_planted.py` now drops a leading section number before comparing.
  - The second pass scored 0/3 from rung-02000 up. `inspect` cuts its named
    lists at `[report] top` (20), and the counts beside them are never cut. The
    planted misfits were counted but not listed. `--top 1000` lists them all.
- **The unplanted misfits are one generator accident, plus one real gap.**
  - The real gap is `seed/archive/a01-…-rev2.md`, which lacks
    `4. Immediate containment`. The 2026-09-28 run found it too.
  - From rung-01000 up, every other unplanted misfit is a generated
    `quarantine` or `marrowbeck-excursion-sop` document. It lacks only
    `Temperature Excursion Response SOP`, which the template family uses as its
    H1. ANALYSIS §3 explains why this returned when the 2026-09-28 lens change
    had removed it.
- **`misfit_floor` stays PROVISIONAL in the code.** This run changes no
  threshold and no lens. The proposal is in ANALYSIS §4.

## Name-leak search (seeds 63–88 against `rung-10000/ext/`)

[`evidence/new_seed_name_leaks.out`](evidence/new_seed_name_leaks.out) lists 288
tokens that first appear in seeds 63–88, and 31 of them also occur in ext. None
is a fact leak, but four places and two first names are retrieval hazards:
- **Siliguri** (seeds 76, 78, 82: *Siliguri depot*) and **Raipur** (seed 86:
  the LQ-54 lane). The generator's own companies already have a
  *Siliguri site* and a *Raipur site*, in 50+ ext documents each.
- **Imran** (seed 63, *Imran Shaikh*) and **Vikram** (seed 67, *Vikram
  Thakur*). Ext has *Imran Sheikh* and *Vikram Sethi*, who are different people.

Analysis §5 covers the full list.

The diagnosis, the hazards and the proposal are in [ANALYSIS.md](ANALYSIS.md).
