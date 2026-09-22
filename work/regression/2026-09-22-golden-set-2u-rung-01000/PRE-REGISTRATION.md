---
type: Pre-Registration
description: "A BASELINE CAPTURE of a NEW question set — generation 2's `set-2-u`, 125 Claude-authored questions — on one rung (`rung-01000`), one arm, one pinned engine. It is NOT a paired comparison, it files NO verdict about the engine, and it computes no correctness column because no answer key reaches this session."
run: 2026-09-22-golden-set-2u-rung-01000
item: W-215
status: frozen
filed: 2026-09-22
classification: informed
---

# PRE-REGISTRATION — `set-2-u` baseline capture, `rung-01000`

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b). A threshold or a
claim added to this document after the first row is filed is a moved threshold,
whatever it is called.

---

## 1 · 🔴 What this run IS, and what it explicitly is NOT

**It is a BASELINE CAPTURE of a new question set.** Generation 1's three sets
retired on 2026-09-22 and are **not part of this run**; they are not read, not
asked and not referenced as rows. `set-2-u` is generation 2's first set and has
never been run against anything.

🔴 **It is NOT a paired comparison.** One arm, one engine, one rung. There is no
baseline arm, no treatment arm, no endpoint and no direction — and therefore
**no delta, no net, no flip count and no verdict about the engine.** Nothing in
this directory may be cited as evidence that any engine behaviour improved,
regressed or held.

🔴 **There is no column for *correct*, and there cannot be.** No answer key
reaches this session by any route, **a paste included**
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). A key sits on this
machine at the one address L11 decision 3 has permitted since 2026-09-18; it is
Arpit's, the tree is **LOCKED** (`just golden-state` → `locked`, run before
anything else), and it is closed to this session **on both spellings**. Nothing
in this run opens, lists, globs, stats, hashes or counts either directory, and
every recursive search this run performs over `work/` excludes `work/golden/`.

**What it produces is one hand-off file that Arpit picks up**, plus the machine
predictions beside it and a descriptive report. Scoring is
[`tools/golden-score/score.py`](../../../tools/golden-score/score.py), started
by Arpit from his own shell. **This session does not invoke it.**

## 2 · The set

| | |
|---|---|
| file | `work/golden/questions/set-2-u.jsonl` |
| generation | **2** |
| author | **Claude** — the `u` suffix of L11 decision 14's `set-<gen>-<x\|u>` |
| questions | **125** |
| id namespace | `s2u-001` … `s2u-125` |
| fields read | `id` and `question` — **and nothing else**, which is all the file carries |

🔴 **Checked before the file is committed, and only its KEYS were read:** all
125 rows carry exactly `{"id", "question"}` and nothing else — no `answer`,
`answer_text`, `relevant`, `primary`, `answerable`, `evidence`, `difficulty` or
`sealed` field — and the 125 ids are unique and all in the `s2u-` namespace, so
they cannot collide with a retired set's. ⚠ **`wc -l` says 124**: the file has no
trailing newline. **The set is 125 questions**, and a run that trusted the line
count would have silently dropped the last one.

⚠ **The set is authored but not yet ratified.** [W-215](../../open/W-215-generation-2-corpus.md)
asks Arpit to authorise generation 2 and is open in the inbox at the moment this
document is frozen. **This run is the capture he asked for, and it settles
nothing about W-215's other five items.**

## 3 · The frozen engine — a clean worktree, because the live tree is dirty

| | |
|---|---|
| engine commit | 🔴 **`3f824de03a944a0d2e9cffb7a8ba09b439c17d02`** |
| engine version | **`fux 3.0.0-alpha.2`** |
| how it is pinned | a detached `git worktree` at that sha, with **its own venv**, outside the repository |
| reader | Python only. The Node reader is not an arm of this run |

🔴 **The live working tree carries an UNCOMMITTED change and this run does not
contain it.** `src/fux/query/confidence.py` and `node/src/query/confidence.mjs`
are modified in the repository right now — a concurrent session building
**W-214** (`weak` demoted from a refusal to a signal; `answerable` back to
`band != none`). The repository's own venv is an **editable** install pointing at
that dirty tree, so running from it would have filed 125 rows against an engine
with no nameable sha.

⚠ **Consequence, declared before any row exists:** every `answerable` value in
this run carries the **OLD, pre-W-214 semantics** — `band not in (none, weak)`,
verified in the pinned worktree at
[`src/fux/query/confidence.py:293`](../../../src/fux/query/confidence.py). When
W-214 lands, **this capture's `answerable` column describes a behaviour the
engine no longer has**, and any later comparison against it is comparing two
instruments. The `band` column is unaffected.

## 4 · 🔴 The rung is RE-INGESTED once, and this is why

**The rule** (prompt 5, phase 5): use the rung's own index and do not re-ingest,
*unless* the engine version **and** `engine_commit` both differ from
`work/golden/ladder/rung-01000.index`. **Both differ:**

| | `ladder/rung-01000.index` | this run |
|---|---|---|
| engine | `fux 3.0.0-alpha.1` | **`fux 3.0.0-alpha.2`** |
| engine_commit | `3c885386d1dd83ef40018f99047b5d308b3d9b78` | **`3f824de03a944a0d2e9cffb7a8ba09b439c17d02`** |

**And the mismatch is not cosmetic.** `git diff --stat 3c885386..3f824de0 -- src node`
touches `query/analyzer.py`, `ingest/extract.py` and `ingest/parse.py` — the
analyzer decides what the postings contain — and `fux doctor` at the pinned
engine already reports **`url sources: skipped (no readable index)`** and
**`register: skipped (no readable index)`** against the committed alpha.1 index.
Querying it with an alpha.2 analyzer would file 125 rows from two engines.

**So, declared in advance:**

1. `rungs.verify('rung-01000', …, documents_too=True)` against the frozen
   `ladder/rung-01000.sha256` — **before** the re-ingest. Already run at the time
   of freezing: **0 problems, 1 000 documents.**
2. `ladder_check.py`, all four checks including `seed_drift` — already run:
   **8 rungs, manifests consistent, nesting verified.**
3. **One** `fux ingest --full` in the rung, with the pinned engine, with
   `.fux/tune.toml` **unedited**.
4. `rungs.verify(...)` again — the documents must be byte-identical afterwards.
   **A re-ingest that moves a document byte stops this run.**
5. `work/golden/ladder/rung-01000.index` is updated to the new engine, commit and
   `index_root_sha256`; `rung-01000.coverage` is regenerated and **must match its
   declarations** (1 000 documents, 103 archived, 101 superseded, 1 000 carrying
   `mtime`). A coverage disagreement stops this run.

⚠ **The ladder becomes heterogeneous and the report says so.** Only
`rung-01000` is re-ingested; the other seven rungs keep their alpha.1 index
records. **Every golden number filed before today against `rung-01000` names an
index root that no longer exists.**

## 5 · Ranking configuration — declared, and checked before the first call

🔴 **`[bm25f] b = 0.15`** · 🔴 **`[bm25f] anchor = 0.0`** · 🔴
**`[confidence] separation_floor = 0.1`** — read from the rung's committed
`.fux/tune.toml` at the time of freezing and **not edited by this run**.
`anchor` stays off: W-168 step 1's weight moves only on its own passing
pre-registered run, and turning a ranking feature on inside a single-arm capture
would make every row here a measurement of an unratified default.

## 6 · The calls — both verbs, per question, from inside the rung directory

```
fux ask    "<question>" --json --band --why --top 10
fux answer "<question>" --json
```

**125 questions × 2 verbs × 1 rung = 250 calls.**

🔴 **`--why` is not optional and it is not for debugging**
([SR-WORK-QUALITY](../../../records/0056_WORK-quality.md) decision 13).
`derivation.gates` is the only place `reachable` and `in_window` exist, they are
discarded the moment the query returns, and a filed run cannot get them back —
W-204 phase D scored 11 716 rows and **could not compute the funnel at all**.
The hand-off records those five integers and **nothing else from the
derivation**.

## 7 · The metrics — descriptive only, with `k` named

🔴 **`k = 10` everywhere**, because `--top 10` is what the ranked list is
truncated to. There is no `k = 5` figure in this run and none may be derived
from it: a `recall@5` computed from a `k = 10` list is legal arithmetic and a
different measurement from one whose retrieval was capped at 5.

| # | claim | how it is computed | `k` |
|---|---|---|---|
| S1 | **decline rate** — how many questions `fux answer` declined | the answer JSON's payload being empty | n/a |
| S2 | **band distribution** — `grounded` / `partial` / `weak` / `none` | `confidence.band` from `ask --band` | n/a |
| S3 | **empty ranked lists** | `len(ranked) == 0` | **10** |
| S4 | **funnel-gate capture rate** — how many of 125 rows carry all five integers | `derivation.gates` present and a dict | n/a |
| S5 | **latency tail** — slowest calls per verb | wall clock per call | n/a |

⚠ **S5 is DESCRIPTIVE and is NOT a benchmark measurement.** This machine is
shared ([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12) and
the arms are not interleaved, so no latency figure here may be cited against
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)'s captures.

## 8 · 🔴 Headroom disclosure ([SR-RS](../../../records/0133_predictions.md) decision 22)

**Decision 22 governs a PAIRED run. This run has one arm, one endpoint-free
capture and no direction, so per-direction headroom — improvement (*not right in
both arms*) and regression (*not wrong in both arms*) — is UNDEFINED here, in
both directions.** It is disclosed as undefined rather than omitted, because 22b
forbids the word appearing bare and 22d forbids reading an absent number as a
null.

**What is disclosed instead, so a later paired run cannot invent its own pool:**

- The **structural ceiling** on any future paired comparison that uses this set
  at this rung is **125 questions**. That is an upper bound on a discordant
  count, not an estimate of one.
- The **usable** pool is smaller and this run cannot measure how much smaller,
  because the split between answerable and unanswerable questions lives in the
  key. 🔴 **The nearest measured prior is that the pool was 7–23 answerable
  questions per set per rung** on generation 1's three sets
  ([`2026-09-22-w168-step-inputs`](../2026-09-22-w168-step-inputs/report.md)),
  which is what put SR-RS decision 19's floor of 6 net flips out of reach of
  every step of W-168. ⚠ **That number is about RETIRED sets and is cited as
  context, never as a property of `set-2-u`.** Whether generation 2 carries a
  larger pool is exactly what W-215 was filed to change and **this run does not
  answer it**; the first thing that can is a score.
- Consequently **no verdict, PASS, FAIL, INCONCLUSIVE or VOID, is filed by this
  run**, and no `VERDICT.md` exists in this directory.

## 9 · Classification — 🔴 `informed`, permanently

**`classification: informed`**, and it is not a property of this session's care.
🔴 **The set's author and its runner are the same model family**, so `set-2-u`
can never be `blind` ([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md);
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) decision 14). **The word
*blind* does not appear as a description of this run anywhere in this
directory.**

⚠ **Independently sufficient, even if the first reason vanished:** every golden
number in this project is `informed` permanently from the first unlock
(2026-09-22), and the tree has been unlocked once.

## 10 · What this run may NOT claim, exhaustively

Whether any answer is right or wrong · `hit@k`, `recall@k`, `precision` or any
keyed metric · a difficulty band · an abstention-quality figure · a comparison
against any generation-1 number (those ids are retired and the corpus index has
moved) · a comparison between this rung and any other · any statement about an
engine other than `3f824de0` · anything about the uncommitted W-214 behaviour ·
and the word *blind*.

## 11 · Reproduce

```bash
git worktree add <tmp>/engine-pin 3f824de03a944a0d2e9cffb7a8ba09b439c17d02 --detach
cd <tmp>/engine-pin && uv venv .venv && uv pip install --python .venv/bin/python -e .
cd ~/my_programs/fux-lab/corpora/golden/rung-01000 && <tmp>/engine-pin/.venv/bin/fux ingest --full
cd ~/my_programs/fux
python3 tools/quality-controls/golden_run.py --rung rung-01000 --sets 2-u \
    --fux <tmp>/engine-pin/.venv/bin/fux \
    --engine-commit 3f824de03a944a0d2e9cffb7a8ba09b439c17d02 \
    --evidence work/regression/2026-09-22-golden-set-2u-rung-01000/evidence
```
