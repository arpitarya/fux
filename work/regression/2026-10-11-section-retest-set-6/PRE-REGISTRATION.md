---
type: Pre-registration
description: "The frozen bar for W-270: the gain-only section term at section_weight = 2.0, re-tested on a fresh set (set-6-claude, generation 5) under law L13 with its defaults — gates G0/G1/G3, slice = step10_section questions missing hit@1 at baseline (>= 15), C1 by SR-RS d19, C2 collateral <= 2, C3 net > 0, the four guardrails. Decided arm sw-2.0; sw-4.0 reported only. Engine b4d961cd (W-273 phase 1). Frozen before the generation-5 ladder exists and before any arm."
run: 2026-10-11-section-retest-set-6
item: W-270
filed: 2026-10-11
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — the gain-only section term at λ = 2.0, on `set-6-claude` (W-270)

## What is being asked

**Does the gain-only section term at `section_weight = 2.0` put long
documents whose answer sits under one heading at rank 1 on a question set its
family has not tuned against, without breaking more than the margin
elsewhere?** On `set-5-claude`, W-269 measured `hit@1` 12 wins and 5 losses at
2.0 (net +7) and failed its own zero-loss bar
([verdict](../2026-10-10-section-gain-only/VERDICT.md), which stands). Three
things kept that from being a ship case: 2.0 was the best of four weights chosen
after the score; the set had been read by two mechanisms; and the gain had
costs elsewhere. This run removes the first two. It decides **one** value,
named here, on a set no mechanism has been decided on.

## The bar: **L13, defaults**

[Law L13](../../../records/0015_LAW-13-the-standing-bar.md) — the standing bar,
Arpit's ruling 2026-10-10 (*"go with the proposed bar … create it as a law
SR"*). This run fills in only the parameters. It loosens nothing; the one
parameter it states explicitly (C2's margin) is L13's own default for this
set's size.

| L13 row | this run |
|---|---|
| **G · gates** | **G0** byte identity at `0.0` against the pre-section engine · **G1** the size bar at `rung-10000` · **G3** sectionless documents unmoved at every λ. Below |
| **slice** | the `step10_section` questions that **miss `hit@1` at baseline**: the key's tag, read from the scorer's counts ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)), never from a per-row tag |
| **slice floor** | the baseline pool's `miss@1` **≥ 15**, or the run STOPS before any arm is read. `reorderable@1` is reported beside it |
| **endpoint** | **`hit@1`**: the step's claim is that the right long document reaches rank 1, not that it enters the top five |
| **C1 · helps** | the slice's paired `hit@1` net at `sw-2.0` clears [SR-RS](../../../records/0133_predictions.md) decision 19 at the observed flips, by [`verdict.py`](../../../tools/quality-controls/verdict.py)'s `rule`, never by hand |
| **C2 · collateral** | on every question outside the slice, `hit@1` losses − wins **≤ 2** |
| **C3 · net positive** | whole-set `hit@1` net at `sw-2.0` **> 0** |
| **guardrails** | L13 decision 3's defaults: `hit@5` total falls by **≤ 1** · `section@1` (the scorer's `evidence_quoted`) total by **≤ 2** · `grounded` band count by **≤ 2** · median `ask` rises by **≤ 100 ms**, standalone at `rung-10000`, three runs per arm |
| **arms** | baseline **`sw-0.0`** · **decided arm `sw-2.0`** · `sw-4.0` captured and **reported only** |
| **data** | **`set-6-claude`** (110 questions, generation 5) on a copy of generation 5's `rung-01000`, `ingest --full`: a fresh set, as L13 decision 5 requires |
| **outcome** | L13 decision 4's table, computed by [`evidence/decide.py`](evidence/decide.py) |

**Why `sw-2.0`, and only that.** It is the value W-269 measured the gain at,
and the value Arpit asked about (*"shouldn't we go with two point zero?"*). It
is named before any number on this set exists. `sw-4.0` is one doubling above,
reported so a reader can see whether the effect is still rising; **a reported
arm that would also pass is a lead for a new run, never a default** (L13
decision 4).

### Reading the slice from counts — and what the counts cannot say

The score rows carry no tag, by L11. The decider sees, per arm, the whole-set
per-row `hit@1` flips (wins `W`, losses `Lo`) and the `step10_section` pool's
`miss@1`.

- A slice question misses at baseline, so it **cannot lose**: the slice net is
  its wins `s`, and C1 is `rule(s, 0)`. Every loss in the set is therefore
  outside the slice, and C2's quantity is `Lo − (W − s)`.
- The pool's `miss@1` falls by `s − l`, where `l` counts tagged questions that
  hit at baseline and lose. **`l` is not in the counts**: it lies in
  `0 … min(Lo, tagged baseline hits)`. So `s` is a range.
- 🔴 **The rule:** the decider evaluates L13's table at **every** `s` the
  counts allow. One outcome across the range is the outcome. More than one is
  **INCONCLUSIVE, handed to Arpit with the range**. This never passes a value a
  single guess would fail; it only sends the ambiguous case to the hand that
  L13 already sends ambiguity to. It is a tightening, which L13 decision 6
  permits without a ruling.
- ⚠ **Read on W-269's own scores (relabelled), it gives *INCONCLUSIVE —
  undetermined (FAIL: drift / INCONCLUSIVE)***: `s ∈ {10, 11, 12}`, C2's
  collateral 3 · 4 · 5. A dry run of the frozen decider, before this file was
  frozen, against a set this run does not decide on. It decides nothing (L13
  decision 1); it shows the rule does what this section says.

## The mechanism and the engine

[SR-SECTIONS](../../../records/0161_sections.md) decision 5, the gain-only
term, as built at W-269 (`03fbf782`), plus W-273 phase 1's decision 2
amendment (no section records for `.csv`, `.json`, `.jsonl`): **engine
`b4d961cd`**. Against `03fbf782`, `src/`, `node/` and `tools/` differ in three
files only, and the ladder holds none of those formats, so on this corpus the
two builds write the same index
([W-273's gates](../2026-10-11-section-formats-gates/report.md)). `b` stays
`0.15`. **Held for every arm:** the engine, the index root, the copy's
`tune.toml` apart from `section_weight`, the corpus and the questions.

⚠ **The build exists before this bar, by design.** L13 decision 4 freezes the
decider *before any build code exists*. This is a re-test of a mechanism
already built and already measured once (W-269), on fresh data, and Arpit
ordered the work that way on 2026-10-10 (W-271's rulings: W-273 phase 1 hands
W-270 the engine to pin). What the freeze protects here is the **data**: this
file, the decider and the three gate scripts are committed **before the
generation-5 ladder is built and before any arm is captured**, and no session
has scored anything on `set-6-claude`. Stated so a reader can weigh it, not
hidden.

## Procedure — DoD 4 and 5

1. **The ladder, generation 5** (DoD 4): rebuilt from `work/golden/seed/`
   alone by [`work/golden/README.md`](../../golden/README.md) phase 4, the
   2026-10-05 driver adapted for generation 5, in a session whose context holds
   no `set-6-claude` question (A23). Its own run directory files it.
2. **The base:** a `cp -a` of generation 5's `rung-01000` to
   `fux-lab/arms/runs/s6-base/rung-01000`; `fux doctor --fix` with `b4d961cd`
   (every key it writes is recorded); `fux ingest --full`.
3. **The arms:** `fux-lab/arms/runs/s6/sw-<λ>/rung-01000` for λ ∈ {0.0, 2.0,
   4.0}, each a `cp -a` of the base; `diff -r` shows only the `section_weight`
   line.
4. **G0's before-capture:** a `cp -a` of the same generation-5 `rung-01000`
   to `fux-lab/arms/runs/s6-pre/rung-01000`, `fux ingest --full` with the
   pre-section engine (`main` at `dca6aaa4`, in its own worktree and venv).
5. **Capture:** `tools/quality-controls/golden_run.py --rung rung-01000
   --tree <copy> --sets 6-claude --arm sw-<λ> --engine-commit b4d961cd --fux
   <pinned>` per arm, unchanged; and once on the before-copy with
   `--engine-commit dca6aaa4 --fux <main's fux>`.
6. **Gates**, before any score: `g0.py` on the two `sw-0.0`-weight captures,
   `g3.py` over the three arms, and W-236's `g1.py` on a `--full` copy of
   generation 5's **`rung-10000`** ingested by `b4d961cd`.
7. **Latency**, standalone, after every capture: `latency.py` on
   `sw-0.0` and `sw-2.0` copies of generation 5's `rung-10000` (the G1 copy,
   twice, with only `section_weight` changed).
8. **Score:** 🔴 Arpit, `just golden-score work/regression/2026-10-11-section-retest-set-6`,
   in his own shell. **Decide:** a session that did **not** capture runs
   `evidence/decide.py`, or Arpit does.

## Gates — each a STOP, never a verdict

**G0 — byte identity at `0.0`.** [`evidence/g0.py`](evidence/g0.py): every
hand-off and prediction row of the `sw-0.0` arm equals the pre-section
engine's, except `ask_ms`, `answer_ms`, `arm`, `engine_commit` and
`repo_head`. One differing row stops the run.

**G1 — the size bar at `rung-10000`.** W-236's
[`g1.py`](../2026-10-10-section-records/evidence/g1.py), unchanged, on a
`--full` copy of generation 5's `rung-10000` ingested by `b4d961cd`: section ÷
document plane **≤ 2.0**; total **≤ 55 000 000 B**; largest file
**≤ 1 048 576 B**; totality misses and `nsec` disagreements **0**. Generation 5
adds six long documents, so the numbers move from W-269's; the bars do not.

**G3 — sectionless documents unmoved.** [`evidence/g3.py`](evidence/g3.py),
W-269's gate with the treatments `sw-2.0` and `sw-4.0`: every sectionless
document's section term is `{id: null, contribution: 0.0}` and its BM25F term
contributions equal `sw-0.0`'s, over `ask --why --top 1000` × 110 questions.

`decide.py` reads `evidence/g0/g0.json`, `evidence/g1.json`,
`evidence/g3/g3.json` and refuses to read a score unless all three say PASS.

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | the six long documents' one-heading answers move from rank 2–10 to rank 1; few incumbent rank-1 hits move | W-269's +7 survived selection; a ship case for 2.0 |
| **hurts** | a long document with one dense, off-topic section overtakes a right short one | concentration in a section is not relevance at `b = 0.15`; W-269's 5 losses were the mechanism, not noise |
| **does nothing** | the slice barely moves at 2.0 | W-269's gain was selected on set 5. FAIL: no gain, and the step closes on two sets |

## After the verdict (ruled with W-271, Arpit 2026-10-10)

- **PASS** → W-273 phase 2 ships `section_weight = 2.0`, with the
  `_format` bump and a *Breaking* CHANGELOG line.
- **FAIL** → step 10 closes as measured on two sets; SR-SECTIONS stays
  `proposed` with both FAILs on it, not archived.
- **INCONCLUSIVE** → Arpit rules (L13 decision 4).

## What this run may NOT do

1. **Move any number above** ([SR-RS](../../../records/0133_predictions.md) d10b).
2. **Decide `sw-4.0`**, or name any value but 2.0 a default.
3. **Sweep anything else**: not the section rule, not `b`, not the form of `G`.
4. **Be adjudicated by the session that captures the arms.**
5. **Proceed past a STOP** (G0, G1, G3, the slice floor).
6. **Open, read or be handed an answer key**, or invoke `score.py` (L11).
7. **Edit or re-ingest a ladder rung in place**; every arm is a copy.
8. **Merge the build to `main`** before a PASS.

## Freeze — filled before the commit that freezes this file

| | |
|---|---|
| `set-6-claude.jsonl` sha256 | `878c26ac236e1c028aed5311042e57aab00aaf9cfba8e819986a2e3ee5cb563f` (110 lines) |
| `evidence/decide.py` sha256 | `7dd5a04c5bd8ad54ba16918852f6dc30df12643968f621a267c092d85916de35` |
| `evidence/g0.py` sha256 | `5f60e82cd203c09bb16cf94b41d9e3a4a1920231fc0b9b25f0a4e374fc5f3b94` |
| `evidence/g3.py` sha256 | `051d224ff813167dfee9b3a63416b5104e3a5cb496e1e3097f9c842b6591ffaa` |
| `evidence/latency.py` sha256 | `ff3f64f0d1b0c893b81cd831aefb874cf64d42fb37c72554dec901df76537e1f` |
| W-236's `evidence/g1.py` sha256 (G1, reused unchanged) | `000939d2680ae423115d569dbfdcd08d688717d4768841df48a8a33c70c2df71` |
| the mechanism | SR-SECTIONS decision 5 at `113ae3b4`; decision 2 as amended at `b4d961cd` |
| the engine | **`b4d961cd`** (W-273 phase 1) |
| the pre-section engine (G0) | `main` at **`dca6aaa4`** |
| the ladder | generation 5 **does not exist** at this file's freeze; DoD 4 builds it after this commit, and the report records each rung's head |
| scores on `set-6-claude` | **none exist**; no session has run an arm on it |
