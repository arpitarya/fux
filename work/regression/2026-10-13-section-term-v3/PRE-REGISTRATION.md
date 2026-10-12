---
type: Pre-registration
description: "The frozen bar for W-278: the section term's third form (the best section scored as a short document on the document yardstick, combined by max) at section_weight = 1.0, on set-7-claude (generation 6) under law L13 with its defaults — gates G0/G1/G3/G4, G5 descriptive, slice = step10_section questions missing hit@1 at baseline (>= 15), C1 by SR-RS d19, C2 by L13's default margin, C3 net > 0, the four guardrails. Decided arm sw-1.0; sw-0.5 reported only. Frozen before the generation-6 ladder exists and before any arm."
run: 2026-10-13-section-term-v3
item: W-278
filed: 2026-10-13
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — the section term's third form at λ = 1.0, on `set-7-claude` (W-278)

## What is being asked

**Does scoring a long document's best section as if it were its own short
document, and letting the document keep the better of the two, put long
documents whose answer sits under one heading at rank 1, without breaking more
than the margin elsewhere?** Both earlier forms failed on drift (W-236, W-269),
and W-270's re-test stopped on its slice floor. Arm diffs showed why: both
forms scored on a *section* average length, so a long document's gain was a
length artefact (17 of 21 and 19 of 24 rank-1 changes brought in a long
document). The third form removes that yardstick
([SR-SECTIONS](../../../records/0161_sections.md) decision 5, amended
2026-10-13). This run decides **one** value, named here, on a set no mechanism
has been decided on.

## The bar: **L13, defaults**

[Law L13](../../../records/0015_LAW-13-the-standing-bar.md), the standing bar.
This run fills in only the parameters and loosens nothing.

| L13 row | this run |
|---|---|
| **G · gates** | **G0** byte identity at `0.0` against the pre-section engine · **G1** the size bar at `rung-10000` · **G3** sectionless documents unmoved at every λ · **G4** no section contribution exceeds its section scored as a document (construction, no key). **G5** is descriptive: it is written before any score and is never read by the decider. Below |
| **slice** | the `step10_section` questions that **miss `hit@1` at baseline**: the key's tag, read from the scorer's counts ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)), never from a per-row tag |
| **slice floor** | the baseline pool's `miss@1` **≥ 15**, or the run STOPS before any arm is read. `reorderable@1` is reported beside it |
| **endpoint** | **`hit@1`**: the step's claim is that the right long document reaches rank 1, not that it enters the top five |
| **C1 · helps** | the slice's paired `hit@1` net at `sw-1.0` clears [SR-RS](../../../records/0133_predictions.md) decision 19 at the observed flips, by [`verdict.py`](../../../tools/quality-controls/verdict.py)'s `rule`, never by hand |
| **C2 · collateral** | on every question outside the slice, `hit@1` losses − wins **≤ `max(2, ⌊0.03 × (165 − slice)⌋)`**, L13 decision 3's default, computed by the decider from the slice size |
| **C3 · net positive** | whole-set `hit@1` net at `sw-1.0` **> 0** |
| **guardrails** | L13 decision 3's defaults: `hit@5` total falls by **≤ 1** · `section@1` (the scorer's `evidence_quoted`) total by **≤ 2** · `grounded` band count by **≤ 2** · median `ask` rises by **≤ 100 ms**, standalone at `rung-10000`, three runs per arm |
| **arms** | baseline **`sw-0.0`** · **decided arm `sw-1.0`** · `sw-0.5` captured and **reported only**. No arm above 1.0: the record refuses one |
| **data** | **`set-7-claude`** (165 questions, generation 6) on a copy of generation 6's `rung-01000`: a fresh set, as L13 decision 5 requires |
| **outcome** | L13 decision 4's table, computed by [`evidence/decide.py`](evidence/decide.py) |

**Why `sw-1.0`, and only that.** It is the form Arpit ruled (*"score a long
doc's best section as if it were its own short doc, and let the doc take the
better of the two (no bonus on top)"*, W-278). It is named before any number
on this set exists. `sw-0.5` is Callan's (1994) interpolation, reported so a
reader can see whether half the move behaves differently; **a reported arm
that would also pass is a lead for a new run, never a default** (L13
decision 4).

### Reading the slice from counts

W-270's rule, unchanged
([its pre-registration](../2026-10-11-section-retest-set-6/PRE-REGISTRATION.md)
§Reading the slice from counts). A slice question misses at baseline, so it
cannot lose; its net is its wins `s`, and C1 is `rule(s, 0)`. `s` is read from
counts as a range. **One outcome across the range is the outcome; more than
one is INCONCLUSIVE, handed to Arpit.** That only tightens, which L13
decision 6 permits.

⚠ **A dry run of this decider on W-270's own scores, relabelled** (`sw-2.0` →
`sw-1.0`, `sw-4.0` → `sw-0.5`), in a scratch tree: **STOP — the slice is 11,
below 15**, W-270's own result. With the floor lowered to 5 in a scratch copy
only, the table ran to *FAIL: drift* at a margin of 2. It decides nothing
(L13 decision 5); it shows the code path runs.

## The mechanism and the engine

[SR-SECTIONS](../../../records/0161_sections.md) decision 5, the third form,
with the own-match rule Arpit ruled on 2026-10-13 (*own-match only*), and
decision 7's amended scan. `b` stays `0.15`. **Held for every arm:** the
engine, the index root, the copy's `tune.toml` apart from `section_weight`,
the corpus and the questions.

⚠ **The build exists before this bar, by W-278's order.** L13 decision 4
freezes the decider *before any build code exists*. W-278's definition of done,
ruled by Arpit on 2026-10-11, puts the record (DoD 1), the latency fix (DoD 2)
and the build (DoD 3) before the bar (DoD 4). The build was tested only on the
unit fixtures and timed on generation 5's `rung-10000` with a released set's
question text. **No arm was captured or scored on any set.** What the freeze
protects is the **data**: this file, the decider and the gate scripts are
committed **before the generation-6 ladder is built and before any arm is
captured**, and no session has scored anything on `set-7-claude`. Stated so a
reader can weigh it.

## Procedure — DoD 5

1. **The ladder, generation 6**, rebuilt from `work/golden/seed/` alone by
   [`work/golden/README.md`](../../golden/README.md) phase 4, generation 5's
   driver, in a session whose context holds no `set-7-claude` question (A23).
   `rung-00100` is built at the seed's own size, generation 5's ruling applied
   again. Its own run directory files it.
2. **The base:** a `cp -a` of generation 6's `rung-01000` to
   `fux-lab/arms/runs/s7-base/rung-01000`; `fux doctor --fix` with the pinned
   engine (every key it writes is recorded); `fux.toml [index] section_records
   = true`; `fux ingest --full`.
3. **The arms:** `fux-lab/arms/runs/s7/sw-<λ>/rung-01000` for λ ∈ {0.0, 0.5,
   1.0}, each a `cp -a` of the base; `diff -r` shows only the `section_weight`
   line.
4. **G0's before-copy:** a `cp -a` of the same generation-6 `rung-01000` to
   `fux-lab/arms/runs/s7-pre/rung-01000`, `fux ingest --full` with the
   pre-section engine (`main` at `dca6aaa4`, in its own worktree and venv).
5. **Capture:** `tools/quality-controls/golden_run.py --rung rung-01000
   --tree <copy> --sets 7-claude --arm sw-<λ> --engine-commit <pinned> --fux
   <pinned>` per arm, unchanged; and once on the before-copy with
   `--engine-commit dca6aaa4 --fux <main's fux>`.
6. **Gates**, before any score: `g0.py` on the two `0.0` captures, `g3.py`
   over the three arms, `g4.py` on the `sw-1.0` copy, W-236's `g1.py` on a
   `--full` copy of generation 6's **`rung-10000`** ingested by the pinned
   engine. **G5:** `g5.py` over the three captures.
7. **Latency**, standalone, after every capture: `latency.py` on `sw-0.0` and
   `sw-1.0` copies of generation 6's `rung-10000` (the G1 copy, twice, with
   only `section_weight` changed).
8. **Score:** 🔴 Arpit, `just golden-score work/regression/2026-10-13-section-term-v3`,
   in his own shell. **Decide:** a session that did **not** capture runs
   `evidence/decide.py`, or Arpit does.

**Smoke runs before the freeze, deciding nothing:** `g4.py` on a scratch copy
of gen-5 `rung-10000` at `sw-1.0` with five `set-6-claude` questions, **PASS**
(24 817 sectioned candidates, 12 199 sections named, 0 failures); `g5.py` on
W-270's own captures relabelled, which reproduces its diagnostic: 21 rank-1
changes at `sw-2.0`, **17 incoming long**.

## Gates — each a STOP, never a verdict

**G0 — byte identity at `0.0`.** [`evidence/g0.py`](evidence/g0.py): every
hand-off and prediction row of the `sw-0.0` arm equals the pre-section
engine's, except `ask_ms`, `answer_ms`, `arm`, `engine_commit` and
`repo_head`.

**G1 — the size bar at `rung-10000`.** W-236's
[`g1.py`](../2026-10-10-section-records/evidence/g1.py), unchanged: section ÷
document plane **≤ 2.0**; total **≤ 55 000 000 B**; largest file
**≤ 1 048 576 B**; totality misses and `nsec` disagreements **0**. The third
form changes no committed byte, so this checks generation 6's data.

**G3 — sectionless documents unmoved.** [`evidence/g3.py`](evidence/g3.py),
W-270's gate with the treatments `sw-1.0` and `sw-0.5`.

**G4 — no contribution exceeds its section scored as a document.**
[`evidence/g4.py`](evidence/g4.py), on the `sw-1.0` copy with the pinned
engine: for every question and every sectioned candidate, the engine's
`(section, contribution)` against an independent re-derivation from the
committed lines. Bound, max form at λ 1, nothing missed, the right section.
Any failure stops the run.

**G5 — descriptive, not a gate.** [`evidence/g5.py`](evidence/g5.py): per
arm, how many rank-1 changes there are and how long the incoming and outgoing
documents are. It is written before any score, so a length-driven arm is
visible before anyone reads a number. It has no threshold and the decider
never reads it.

`decide.py` reads `evidence/g0/g0.json`, `evidence/g1.json`,
`evidence/g3/g3.json`, `evidence/g4/g4.json` and refuses to read a score
unless all four say PASS.

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | generation 6's long documents move from rank 2–10 to rank 1 on their one-heading questions, against short competitors that beat them on length alone; few incumbent rank-1 hits move | the section, scored as the note it is, is the right unit for a long document; a ship case for 1.0 |
| **hurts** | a long document whose one section matches about as well as a short document overtakes it on a tie-break or on the parent's title | the max form still credits length in a way the yardstick does not show; G5 should show it first |
| **does nothing** | the slice barely moves | the max form is too weak at `b = 0.15`: the section's own score rarely beats the short competitor's. FAIL: no gain, and step 10 closes on three mechanisms |

## After the verdict (W-278 DoD 6)

- **PASS** → W-273 phase 2 ships `section_weight = 1.0`, with the `_format`
  bump and a *Breaking* CHANGELOG line.
- **FAIL** → step 10 closes as measured on three mechanisms; SR-SECTIONS stays
  `proposed` with every FAIL on it, not archived.
- **INCONCLUSIVE** → Arpit rules (L13 decision 4).

## What this run may NOT do

1. **Move any number above** ([SR-RS](../../../records/0133_predictions.md) d10b).
2. **Decide `sw-0.5`**, or name any value but 1.0 a default.
3. **Sweep anything else**: not the section rule, not `b`, not the form of `G`,
   not the own-match rule.
4. **Be adjudicated by the session that captures the arms.**
5. **Proceed past a STOP** (G0, G1, G3, G4, the slice floor).
6. **Open, read or be handed an answer key**, or invoke `score.py` (L11).
7. **Edit or re-ingest a ladder rung in place**; every arm is a copy.
8. **Merge the build to `main`** before a PASS.

## Freeze — filled before the commit that freezes this file

| | |
|---|---|
| `set-7-claude.jsonl` sha256 | `94940840d8d31fce742b671ef5caeab5ee3af8ccc8d4c9245da0483c69c051fa` (165 lines) |
| `evidence/decide.py` sha256 | `971d46919dda2db1bc7228ad279c913e487bc214edefb82b527f3a032569b4ef` |
| `evidence/g0.py` sha256 | `049d18137e90b036acd303730c71e2230e9857602281ec3dda499a1b7e06daaa` |
| `evidence/g3.py` sha256 | `d21fbcaeae1d08d2be2b4a8ef60c7d125e3e903e0af63fdf63ef9dec8c5bfe1c` |
| `evidence/g4.py` sha256 | `14fff70e06e0a2d499a98ee6a0b3829dd27cc68e491a994a0890e308b649af8b` |
| `evidence/g5.py` sha256 | `618a54ccaee74ef9a768e867eec5adfa3757c8b01bdac1b08105f0d7a3b543cf` |
| `evidence/latency.py` sha256 | `a0f2cbdd9fa6bbbce52f69a61bf4cb7f31cd69bb52c186eb7ab0caf37e35f03d` |
| W-236's `evidence/g1.py` sha256 (G1, reused unchanged) | `000939d2680ae423115d569dbfdcd08d688717d4768841df48a8a33c70c2df71` |
| the mechanism | SR-SECTIONS decisions 5 and 7 at `08ef6293` |
| the engine | **`08ef6293`** (W-278 DoD 1–3) |
| the pre-section engine (G0) | `main` at **`dca6aaa4`** |
| the ladder | generation 6 **does not exist** at this file's freeze; DoD 5 step 1 builds it after this commit, and the report records each rung's head |
| scores on `set-7-claude` | **none exist**; no session has run an arm on it |
