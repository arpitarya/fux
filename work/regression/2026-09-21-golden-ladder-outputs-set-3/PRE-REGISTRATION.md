---
type: Pre-Registration
description: "W-204 phase A, re-run: every question of all THREE golden sets through `fux ask` and `fux answer` on the eight rungs rebuilt with set 3's documents, at one frozen HEAD. It files NO score and predicts NOTHING about correctness — its only claims are the surface ones, per set. The 2026-09-20 pass stays filed as the pre-set-3 baseline."
run: 2026-09-21-golden-ladder-outputs-set-3
item: W-204
status: frozen
filed: 2026-09-21
---

# PRE-REGISTRATION — W-204 phase A, re-run on the set-3 ladder

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b). A threshold or a
claim added to this document after the first row is filed is a moved threshold,
whatever it is called.

**This document cites
[the 2026-09-20 pre-registration](../2026-09-20-golden-ladder-outputs/PRE-REGISTRATION.md)
and does not edit it.** That document froze one engine sha, two question sets and
a ladder built from a twenty-document seed; **all three of those have moved**, so
this is a new id space rather than an amendment. W-204 §"Then" priced this
re-run in when it ruled set 3: *"the first phase A stays filed as the pre-set-3
baseline."*

---

## 1 · What changed since the baseline pass, and what did not

| | 2026-09-20 baseline | this run |
|---|---|---|
| question sets | 1 and 2 — **249** questions | 1, 2 and **3** — **374** questions |
| seed corpus | 20 documents | **28** — set 3's `16`–`22` and `archive/a06` |
| `ref` edges on the ladder | 🔴 **0 on all eight rungs** | **61 on `rung-seed`**, and every rung above it |
| rung sizes | seed 20 · 100 · … · 10 000 | seed **28** · 100 · … · 10 000 (the ext half is 8 shorter) |
| engine | `538f3497` | 🔴 **`7a88a1657a183157a1cd842e5d392d55f65823f2`** |
| what it claims | the four surface claims, per set | **unchanged** — the same four, now per set of three |

**What did NOT change, deliberately:** the two verbs and their flags, the
hand-off schema, the per-rung document's shape, the classification, and the rule
that no correctness column exists anywhere in this run.

## 2 · What this run is, and what it explicitly is NOT

**It is an output pass.** For every question in all three sets, on every rung, it
records **what `fux ask` ranked, what `fux answer` returned or declined, and what
it cited** — and stops there. The deliverable is one human-readable
`RUNG-NNNNN.md` per rung, derived mechanically from the machine hand-offs so the
two cannot disagree.

🔴 **It files no score, no accuracy and no verdict, because no Claude session
can.** No answer key reaches this session by any route, **a paste included**
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). A key **may** sit on
this machine, at the one address L11 decision 3 has permitted since 2026-09-18;
it is Arpit's, and it is closed to this session **on both spellings**, exactly as
decision 5 states. Nothing in this run opens, lists, globs, stats, hashes or
counts either of them, and every recursive search this run performs over `work/`
excludes `work/golden/`.

🔴 **There is no column for *correct*.** That column is born in W-204 phase D,
after Arpit opens the key, and nowhere earlier.

🔴 **Set 3 does not get a softer rule because Claude wrote it.** Its questions
were authored by a session that then left, under L11 decision 6's per-set
carve-out; **this session has never seen a set-3 answer** and does not become
entitled to one by having rebuilt the corpus the set was written against. Set 3
is as closed as sets 1 and 2 until prompt 9.

## 3 · The frozen engine

| | |
|---|---|
| engine commit | 🔴 **`7a88a1657a183157a1cd842e5d392d55f65823f2`** — frozen here, before any call |
| engine version | `fux 3.0.0-alpha.1` |
| index format written | **`fux.index.v4`**, analyzer `v2` |
| reader | Python only. The Node reader is not an arm of this run |

**Later commits in this run touch no engine byte, and that is checkable rather
than asserted:**

```bash
git diff --stat 7a88a1657a183157a1cd842e5d392d55f65823f2..HEAD -- src node   # must be empty
```

and the closing report states the result of running it.

🔴 **This run must finish before W-205 part 2 changes a line of
`src/fux/query/analyzer.py`.** Part 2 changes what the analyzer emits, which
changes the committed postings; a run straddling that change would file rows
from two engines under one header. The ordering is stated here so that a later
reader can see it was chosen before the numbers, not after.

## 4 · The eight rungs, three sets, two verbs

| rung | documents | of which seed |
|---|---:|---:|
| `rung-seed` | **28** | 28 |
| `rung-00100` | 100 | 28 |
| `rung-00200` | 200 | 28 |
| `rung-00500` | 500 | 28 |
| `rung-01000` | 1 000 | 28 |
| `rung-02000` | 2 000 | 28 |
| `rung-05000` | 5 000 | 28 |
| `rung-10000` | 10 000 | 28 |

**Three sets, kept apart at every step and never pooled** —
`set-1.jsonl` (**125**, Codex), `set-2.jsonl` (**124**, Claude),
`set-3.jsonl` (**125**, Claude). 🔴 **The gap between set 1 and the two
Claude-authored sets is the measurement**; a figure spanning them erases exactly
what two authors were commissioned to expose, and this run prints no such figure.

**Both verbs, per question, from inside the rung directory:**

```
fux ask    "<question>" --json --band --top 10
fux answer "<question>" --json
```

**374 questions × 2 verbs × 8 rungs = 5 984 calls.**

## 5 · Ranking configuration — declared, and checked per rung before the run

🔴 **`[bm25f] b = 0.15`**, HEAD's measured default
([SR-RANKING](../../../records/0111_ranking.md) decision 3), and
🔴 **`[bm25f] anchor = 0.0`**, which is off and stays off.

⚠ **Both are checked on every rung before the first call, and the check is the
lesson of the baseline pass rather than a formality.** The 2026-09-20 run found
`b = 0.75` in all eight rung `tune.toml` files — W-144's upgrade trap, written by
a `fux setup` from 2026-09-12 — and had to edit them mid-run. This run's rungs
were created by a `fux setup` at HEAD on 2026-09-21, so both values are HEAD's
own defaults with no edit; the report prints the eight files' `b` and `anchor`
lines as evidence rather than asserting it.

🔴 **`anchor` stays at `0.0` even though the ladder now has 61 `ref` edges.**
The anchor field is [W-168](../../open/W-168-search-improvements.md) step 1's and
its weight moves **only on a passing pre-registered run of its own**. This is an
output pass with one arm; turning a ranking feature on inside it would make every
row in it a measurement of an unratified default. The edges being there at last
is what **unblocks** that separate run — it is not permission to take it here.

## 6 · Corpus verification — the rebuild is a step of this run's evidence, not a hidden fix

The ladder was rebuilt on 2026-09-21 under
[prompt 4](../../golden/prompts/4-claude-corpus.md) and filed as its own run,
[`2026-09-21-ladder-set-3-rebuild`](../2026-09-21-ladder-set-3-rebuild/report.md).
Before the first call here:

- **`ladder_check.py`, all four checks including check 4 (`seed_drift`)**, on all
  eight rungs: must PASS. A drift stops this run.
- **Every document on disk hashed against its committed `.sha256`**, all eight
  rungs: 0 mismatched, 0 missing.
- 🔴 **`ref_edge_census.py` must exit 0 on all eight rungs.** The baseline pass
  ran on a ladder with **zero** `ref` edges and nobody noticed for weeks
  ([SR-RS](../../../records/0133_predictions.md) decision 23); this run states the
  census in its report whether or not anything downstream reads links.

## 7 · What this run may claim — the surface claims, per set

🔴 **These are the only claims this run is permitted to make**, each reported
**per set** and **per rung**, never pooled:

| # | surface claim | how it is computed |
|---|---|---|
| S1 | **decline rate** — how many questions `fux answer` declined | the answer JSON's payload being empty |
| S2 | **band distribution** — how the confidence band falls | the `band` field of `fux ask --band` |
| S3 | **empty ranked lists** — how many questions `fux ask` returned nothing for | `len(ranked) == 0` |
| S4 | **latency tail** — the slowest calls, per verb | wall-clock per call, reported as a tail, never as a benchmark |

**Two findings the baseline pass filed are re-examined here, and they are
observations, not predictions.** The pre-registration states them so that
agreement cannot later be presented as a confirmed hypothesis:

- `band: weak` ⇔ `answerable: false` held on 3 984 of 3 984 rows.
- The band's middle was **inert** — 43 of 43 transitions were `grounded ↔ weak`
  and `partial` gained a member at no rung.

⚠ **Whatever set 3 does to either is reported as a third set's behaviour, not as
a replication**, because set 3 did not exist when they were observed and its
documents changed the corpus they were observed on.

⚠ **S4 is descriptive and is NOT a benchmark measurement.** This machine is
shared ([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12),
and no latency claim here may be cited against
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)'s captures.

🔴 **What this run may NOT claim, exhaustively:** whether an answer is right or
wrong; `hit@k`, `recall@k`, `precision` or any keyed metric; a difficulty band; a
comparison against the 2026-09-20 rows as if the corpora were the same; a
comparison between the sets beyond reporting each separately; and any statement
about a version other than the frozen HEAD.

**Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22) does not
apply**: decision 22 governs a **paired** run, and this has one arm, no endpoint
and no direction.

## 8 · What is recorded, per set, never merged

| file | one line or section per question |
|---|---|
| `evidence/<rung>/predictions-set-N.jsonl` | `{id, ranked[], answerable, band}` |
| `evidence/<rung>/handoff-set-N.jsonl` | the above **plus** `question`, `answer_text`, `citations[{doc,lines}]`, `freshness`, `source`, `rung`, `engine_commit`, `repo_head` — self-contained, and **what Arpit gives a scorer** |
| `evidence/<rung>/RUNG-NNNNN.md` | the human-readable twin: set 1 in full, then set 2, then set 3, never interleaved |

🔴 **The `.md` is generated by `tools/quality-controls/rung_outputs.py`, never
written by hand.** Both it and `golden_run.py` were generalised from a hardcoded
`(1, 2)` to a `--sets` list in the change that landed set 3; **the default is
`1,2,3` and a named set with no file is refused rather than skipped**, because
*"this rung has no set-3 rows"* and *"set 3 was never asked"* are indistinguishable
in the evidence afterwards.

⚠ **One ambiguous id scores the wrong set.** The three hand-offs stay in separate
files at every step, and the generator now checks **every pair** of sets for a
colliding id, not just 1 against 2.

## 9 · Classification, and what is read

**`classification: informed`**, for three reasons of which any one suffices:

- **Sets 2 and 3 can never be blind** — author and runner are the same model
  family, permanently ([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md)).
- **Set 1 is no longer blind either**, since the 2026-09-17 L11 breach recorded in
  [W-196](../../../archive/open/W-196-l11-breach-2026-09-17.md).
- **This pass feeds a scored run** (phase D).

⚠ **A fourth reason applies to set 3 alone and is worth naming:** this session
rebuilt the corpus set 3 was written against, so it has read every seed document
the set's author read. That is *not* a key, and it is not a breach — but it is one
more reason the word `blind` may never be attached to a set-3 number.

**What this run reads:** `work/golden/seed/`, the three `questions/set-N.jsonl`
(**ids and text only**), `work/golden/ladder/`, `work/golden/README.md`,
`work/golden/prompts/`, and the eight rung directories under
`~/my_programs/fux-lab/corpora/golden/`. **Nothing else, and nothing at either
spelling of the sealed-key directory L11 decision 5 closes.**

## 10 · The reproduce command

```bash
cd ~/my_programs/fux-lab/corpora/golden/<RUNG>
/Users/arpitarya/my_programs/fux/.venv/bin/fux ask    "<question>" --json --band --top 10
/Users/arpitarya/my_programs/fux/.venv/bin/fux answer "<question>" --json
```

with the engine at `7a88a1657a183157a1cd842e5d392d55f65823f2`, `b = 0.15`, `anchor = 0.0`, and the rung as
the 2026-09-21 rebuild froze it. **A run whose numbers cannot be regenerated is
an anecdote.**
