---
type: Report
run: 2026-09-20-golden-ladder-outputs
item: W-204
classification: informed
description: "W-204 phase A: 3 984 fux calls — 249 questions × 2 verbs × 8 rungs — at one frozen engine, producing one RUNG-NNNNN.md per rung. It files NO score. Surface claims only, per set, never pooled."
filed: 2026-09-20
---

# W-204 phase A — every rung's outputs, at one frozen engine

🔴 **This run files no score and states nothing about correctness.** It records
what `fux ask` ranked, what `fux answer` returned and cited, and where the
confidence band declined. *Correct* and *incorrect* are W-204 phase D's, after
Arpit opens the key, and no Claude session can supply them
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). **No answer reached
this session by any route, a paste included**, and nothing at either spelling of
the sealed-key directory was opened, listed, globbed, stat'd, hashed or counted.

Everything below is permitted by
[the frozen pre-registration](PRE-REGISTRATION.md) §8, and nothing else is
claimed.

## What ran

| | |
|---|---|
| engine commit | `538f34978141a54b28b78b7ea76d36969cf63aa0` — frozen before the first call |
| engine version | `fux 3.0.0-alpha.1` |
| index format | `fux.index.v4`, read from each rung's shard header |
| `[bm25f] b` | **`0.15`** — set by this run; see §Two forced repairs |
| rungs | all eight, `rung-seed` … `rung-10000`, 18 820 documents |
| questions | set 1 **125** (Codex) · set 2 **124** (Claude) |
| calls | 249 × 2 verbs × 8 rungs = **3 984** |
| reader | Python only |

**The frozen-engine invariant holds, checked rather than asserted.** This run
files one rung per commit, so `HEAD` moved eleven times while the engine did
not:

```
$ git diff --stat 538f3497..<last rung commit> -- src node .fux/tune.toml
(empty)
```

Every hand-off row carries `engine_commit` (the frozen sha) **and** `repo_head`
(the commit that call actually ran at), so the claim is checkable from the
evidence and not only from this sentence.

## Two forced repairs, both declared in advance

Neither was discovered mid-run; both are in the pre-registration, §4 and §5,
committed before the first call.

1. 🔴 **Every rung's `fux.toml` carried `meta = "hashed"`, and HEAD refuses it by
   name** after W-194. `fux doctor` in `rung-seed` returned
   `[FAIL] fux.toml loads: [sources.url] meta is not a fux.toml key`. **No rung
   could be read at all** until the line went. `fux.toml` is untracked in each
   rung's git repository and the key governed URL record display; every rung is
   a directory corpus with no URLs.
2. 🔴 **Every rung's `.fux/tune.toml` held `b = 0.75`**, written by `fux setup`
   on 2026-09-12 and untouched since — **W-144's upgrade trap, observed in the
   wild**: `fux setup` writes `b` out in full, so a repository set up before the
   2026-09-16 ruling keeps the old value and does not move. This run set all
   eight to HEAD's measured default `0.15`. `b` is applied at query time, so the
   change reached no index byte.

**Corpus verified before and after both repairs**, to prove no document moved:

| check | before | after |
|---|---|---|
| `ladder_check.py`, all four checks incl. `seed_drift` | PASS | PASS |
| documents hashed against `.sha256` | 18 820, 0 mismatched, 0 missing | 18 820, 0 mismatched, 0 missing |
| `rungs.verify()` per rung | — | clean, all eight |

## The re-ingest, filed as a step and not hidden

The rungs' shards were `fux.index.v3` and HEAD writes `v4`, so **no committed
rung index was readable by the frozen engine.** Each rung was re-ingested once.

⚠ **`--no-fetch` alone is refused**, which the pre-registration did not
anticipate. The engine's own error names the remedy — *"there is no in-place
migration: run `fux ingest --full`"* — so the command is
`fux ingest --full --no-fetch`. `--full` is safe here for the reason the same
error gives: it refuses rather than strands `url:` records, and no rung holds
one. All eight `work/golden/ladder/rung-NNNNN.index` stamps were re-written with
the new engine, commit and `index_root_sha256`; **every root hash moved**, which
is the expected consequence of a format bump and was stated in advance.

## Set 1 — Codex-authored · `informed`

| rung | n | grounded | partial | weak | `answerable: false` | empty ranked | uncited answers | ask p50 | ask p95 | answer p50 | answer p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `rung-seed` | 125 | 60 | 48 | 17 | **17 (13.6 %)** | 0 | 0 | 66.0 | 67.5 | 84.4 | 87.9 |
| `rung-00100` | 125 | 61 | 37 | 27 | **27 (21.6 %)** | 0 | 0 | 70.5 | 72.8 | 88.4 | 93.1 |
| `rung-00200` | 125 | 65 | 37 | 23 | **23 (18.4 %)** | 0 | 0 | 74.6 | 76.9 | 91.1 | 95.5 |
| `rung-00500` | 125 | 67 | 37 | 21 | **21 (16.8 %)** | 0 | 0 | 87.6 | 100.1 | 103.9 | 136.1 |
| `rung-01000` | 125 | 67 | 37 | 21 | **21 (16.8 %)** | 0 | 0 | 100.0 | 114.7 | 116.6 | 131.2 |
| `rung-02000` | 125 | 64 | 37 | 24 | **24 (19.2 %)** | 0 | 0 | 126.6 | 141.4 | 144.7 | 164.5 |
| `rung-05000` | 125 | 64 | 37 | 24 | **24 (19.2 %)** | 0 | 0 | 193.7 | 232.5 | 207.8 | 248.3 |
| `rung-10000` | 125 | 64 | 37 | 24 | **24 (19.2 %)** | 0 | 0 | 322.0 | 392.0 | 335.7 | 404.7 |

## Set 2 — Claude-authored · `informed` permanently

| rung | n | grounded | partial | weak | `answerable: false` | empty ranked | uncited answers | ask p50 | ask p95 | answer p50 | answer p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `rung-seed` | 124 | 42 | 55 | 27 | **27 (21.8 %)** | 0 | 0 | 66.8 | 68.1 | 85.5 | 88.9 |
| `rung-00100` | 124 | 44 | 40 | 40 | **40 (32.3 %)** | 0 | 0 | 70.4 | 72.6 | 88.2 | 92.3 |
| `rung-00200` | 124 | 46 | 40 | 38 | **38 (30.6 %)** | 0 | 0 | 74.6 | 77.2 | 91.8 | 96.2 |
| `rung-00500` | 124 | 46 | 40 | 38 | **38 (30.6 %)** | 0 | 0 | 85.8 | 99.1 | 104.4 | 113.5 |
| `rung-01000` | 124 | 42 | 40 | 42 | **42 (33.9 %)** | 0 | 0 | 96.7 | 108.0 | 113.9 | 126.0 |
| `rung-02000` | 124 | 42 | 40 | 42 | **42 (33.9 %)** | 0 | 0 | 116.4 | 131.3 | 131.8 | 146.2 |
| `rung-05000` | 124 | 41 | 40 | 43 | **43 (34.7 %)** | 0 | 0 | 180.1 | 213.1 | 193.7 | 229.2 |
| `rung-10000` | 124 | 40 | 40 | 44 | **44 (35.5 %)** | 0 | 0 | 292.0 | 359.9 | 304.4 | 369.9 |

🔴 **The two tables are never combined.** Their authors differ and the gap
between them is the measurement; a figure spanning both erases exactly what two
authors were commissioned to expose.

## Four things that did not happen, across 3 984 calls

| | count |
|---|---|
| empty ranked lists | **0 of 3 984** |
| answers with no citation | **0 of 1 992** |
| `fux answer` returning `null` | **0 of 1 992** |
| freshness verdicts other than `current` | **0 of 1 992** |
| failed calls or unparseable JSON | **0** |

⚠ **That is a statement about the RUN, not about the answers.** A confidently
wrong answer is indistinguishable from a confidently right one from here, and
saying so is the whole reason this report has no correctness column.

## The decline signal is the band flag, not a null answer

🔴 **`fux answer` returned text on every one of the 1 992 calls**, including all
**443** whose band said `answerable: false`. So *"fux declined"* in this run
means **the confidence band declared the question unanswerable**, not that the
answer verb returned nothing. The two are reported as separate columns above and
are never folded into one *"declined"* number, because on this corpus they have
different values — 443 and 0.

## Findings

Three, all of them surface-level. Each is stated as observed on one corpus at
one engine, and none of them rules anything —
[`ANALYSIS.md`](ANALYSIS.md) carries what follows from them.

1. 🔴 **`band: weak` and `answerable: false` coincide exactly — 3 984 of 3 984
   rows, both sets, all eight rungs, no exception.** The 2026-09-16 `rung-00100`
   run found this on 249 rows; it now holds across a 500× corpus range, a
   different `b`, a different index format and a different engine. **The band
   column and the decline column carry one number**, so a reader comparing them
   compares a thing with itself.
2. 🔴 **After `rung-00100`, every band transition is `grounded ↔ weak`. 43 of 43.
   Not one question enters or leaves `partial` across a 100× corpus growth.**
   The `partial` set is byte-identical at all seven rungs from 100 documents up —
   the same 37 questions in set 1, the same 40 in set 2. `partial` only ever lost
   members, and only on the single step from 20 to 100 documents (17 → `grounded`,
   9 → `weak`); **nothing ever entered it at any point in the ladder.**
3. ⚠ **Set 2 declines more than set 1 at every single rung**, by 7.7 to 17.1
   percentage points, and the gap is widest at the top of the ladder. Same
   corpus, same engine, same day, different authors. 🔴 **This is not a claim
   that either set is better, harder or more correct** — nothing was scored. Only
   a key separates *"set 2 asks more unanswerable questions"* from *"fux recalls
   worse on set 2's phrasing"*, and this report does not guess.

## Latency — descriptive, and not a benchmark

`ask` p50 runs **66 ms at 20 documents to 322 ms at 10 000**; `answer` tracks it
about 15–20 ms above. ⚠ **No claim here may be cited against
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md).** There are no arms
to interleave, nothing was pinned, and this machine is shared
([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12) — the run
was announced in the session and ran between 2026-09-20's other work.

## What may not be compared with this

🔴 **No number in this run may be compared with any golden number filed before
today.** The engine, the index format and the ranker have all moved, and the
`b` this run used is one it had to set itself. In particular the 2026-09-16
`rung-00100` run is **not** a baseline for the `rung-00100` rows here — see
`ANALYSIS.md` §1 for why that run's own `b` is in doubt.

## Evidence

Per rung, under [`evidence/<rung>/`](evidence/):

| file | what |
|---|---|
| `predictions-set-N.jsonl` | `{id, ranked[], answerable, band}` |
| `handoff-set-N.jsonl` | the above plus `question`, `answer_text`, `citations`, `freshness`, `source`, `rung`, `engine_commit`, `repo_head`, `ask_ms`, `answer_ms` — self-contained, and what Arpit carries to a scorer |
| `RUNG-NNNNN.md` | the human-readable twin, **generated** from the two hand-offs by [`tools/quality-controls/rung_outputs.py`](../../../tools/quality-controls/rung_outputs.py) |

🔴 **The `.md` is never written by hand.** It is derived from the same bytes
phase D will score, so the eight readable documents cannot drift from the rows —
the failure mode where a summary and its evidence disagree and only the summary
is ever read.

## Reproduce

```bash
cd ~/my_programs/fux-lab/corpora/golden/<RUNG>
/Users/arpitarya/my_programs/fux/.venv/bin/fux ask    "<question>" --json --band --top 10
/Users/arpitarya/my_programs/fux/.venv/bin/fux answer "<question>" --json
```

engine `538f3497`, `b = 0.15`, the rung re-ingested once with
`fux ingest --full --no-fetch`. The whole pass:

```bash
python tools/quality-controls/golden_run.py --rung <RUNG> \
    --evidence work/regression/2026-09-20-golden-ladder-outputs/evidence/<RUNG> \
    --engine-commit 538f34978141a54b28b78b7ea76d36969cf63aa0
python tools/quality-controls/rung_outputs.py --rung <RUNG> \
    --evidence work/regression/2026-09-20-golden-ladder-outputs/evidence/<RUNG>
```

## Authorship

| artifact | author | what they could reach |
|---|---|---|
| **set 1 questions** | Codex | none of this run |
| **set 2 questions** | Claude | **queries** — same model family as the runner, permanently `informed` |
| **the corpus** (`work/golden/seed/`, the `ext/` filler) | Codex (seed) · Claude (ladder growth, blind) | seed authored without the questions; ladder built by a session that had not read `questions/` |
| **index configuration, retriever and ranker settings** | Claude | 🔴 **queries** — `[bm25f] b = 0.15` was ruled on 2026-09-16 by a Claude session that had read the released question text, and this run applied it |
| **the run** | Claude (this session) | **queries** (ids and text), **no judgments**, **no prior scores**, **no key** |
| **this analysis** | Claude (this session) | the same |
| **the key** | Arpit and Codex | 🔴 **unreached by this session, by any route** |

**`classification: informed`**, for three independent reasons, any one of which
is sufficient:

- **Set 2 can never be blind** — author and runner are the same model family
  ([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md)).
- **Set 1 is no longer blind either**, since the 2026-09-17 L11 breach
  ([W-196](../../../archive/open/W-196-l11-breach-2026-09-17.md)) put both keys
  into a Cowork Claude session.
- **The ranker this run used was tuned by a session that had read the
  questions**, and **this pass feeds a scored run**.

⚠ **An informed number is not an "upper bound"** — that claims a bounded
magnitude a leak does not have. It is **not a generalisation estimate**
([SR-RS](../../../records/0133_predictions.md) decisions 11–13).

**Headroom is not disclosed and is not missing: this is NOT a paired run.**
SR-RS decision 22 governs a paired run — two arms, an endpoint, a direction.
This one has a single arm, no endpoint and no comparison, so there is no
direction to disclose headroom in and a number invented for one would be worse
than its absence. **W-204 phase B is the paired run**, and its own
pre-registration carries the disclosure in both directions.
