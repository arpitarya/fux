---
type: Report
run: 2026-09-21-golden-ladder-outputs-set-3
item: W-204
classification: informed
description: "W-204 phase A re-run: every question of all three golden sets through `fux ask` and `fux answer` on the eight rungs rebuilt with set 3's documents, at one frozen engine. 5 984 calls, 2 992 rows, no score. The authorship gap REPLICATES on an independently-authored third set, and the baseline's inert-middle-band finding is narrowed rather than confirmed."
filed: 2026-09-21
---

# REPORT — the whole ladder's outputs, three sets, one frozen engine

🔴 **No score, and no correctness column anywhere.** *Correct* is W-204 phase D's,
after Arpit opens the key. This run records **what fux did** and never what it
should have done.

**Frozen engine `7a88a165`**, `fux 3.0.0-alpha.1`, `fux.index.v4`, analyzer `v2`,
`b = 0.15`, `anchor = 0.0`. **5 984 calls — 374 questions × 2 verbs × 8 rungs.**
The frozen-engine invariant the pre-registration named was run and is empty:

```
$ git diff --stat 7a88a165..HEAD -- src node
(no output)
```

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen and
committed before the first call. **The 2026-09-20 pass stays filed as the
pre-set-3 baseline and is not edited**; its corpus no longer exists, so no number
here is differenced against it — where this report says *reproduces* it means the
same **property** held on a new corpus, a third set and a different ladder, never
that two numbers matched.

## What was verified before the first call

| check | result |
|---|---|
| `ladder_check.py`, all four checks incl. `seed_drift` | ✅ **PASS**, all eight rungs |
| every document hashed against its committed `.sha256` | ✅ **18 828 documents, 0 mismatched, 0 missing** |
| `ref_edge_census.py` | ✅ **exit 0** — 61 `ref` edges on every rung |
| `[bm25f] b` on all eight rungs | ✅ **0.15**, HEAD's measured default, **no edit needed** |
| `[bm25f] anchor` on all eight rungs | ✅ **0.0**, off and left off |
| `[sources.url] meta` in any rung's `fux.toml` | ✅ **absent on all eight** |

🔴 **Both of the 2026-09-20 pass's forced mid-run repairs were absent**, because
the rungs were created by a `fux setup` at HEAD on 2026-09-21 rather than on
2026-09-12. The pre-registration predicted this and said the check would be
printed rather than asserted; it is the table above.

## S1–S4, per set, per rung

| rung | set | author | n | declined | weak | partial | grounded | empty ranked | ask p50 | ask p95 | answer p50 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `rung-seed` | 1 | Codex | 125 | 0 | 25 | 43 | 57 | 0 | 69 | 71 | 87 |
| `rung-seed` | 2 | Claude | 124 | 0 | 28 | 45 | 51 | 0 | 69 | 74 | 89 |
| `rung-seed` | 3 | Claude | 125 | 0 | 28 | 50 | 47 | 0 | 69 | 70 | 90 |
| `rung-00100` | 1 | Codex | 125 | 0 | 33 | 35 | 57 | 0 | 73 | 75 | 91 |
| `rung-00100` | 2 | Claude | 124 | 0 | 38 | 38 | 48 | 0 | 72 | 76 | 91 |
| `rung-00100` | 3 | Claude | 125 | 0 | 33 | 40 | 52 | 0 | 73 | 78 | 94 |
| `rung-00200` | 1 | Codex | 125 | 0 | 27 | 35 | 63 | 0 | 77 | 82 | 96 |
| `rung-00200` | 2 | Claude | 124 | 0 | 34 | 38 | 52 | 0 | 77 | 79 | 96 |
| `rung-00200` | 3 | Claude | 125 | 0 | 31 | 40 | 54 | 0 | 76 | 80 | 96 |
| `rung-00500` | 1 | Codex | 125 | 0 | 27 | 35 | 63 | 0 | 89 | 96 | 108 |
| `rung-00500` | 2 | Claude | 124 | 0 | 36 | 38 | 50 | 0 | 86 | 90 | 105 |
| `rung-00500` | 3 | Claude | 125 | 0 | 37 | 40 | 48 | 0 | 85 | 90 | 105 |
| `rung-01000` | 1 | Codex | 125 | 0 | 29 | 35 | 61 | 0 | 100 | 106 | 117 |
| `rung-01000` | 2 | Claude | 124 | 0 | 36 | 38 | 50 | 0 | 98 | 105 | 116 |
| `rung-01000` | 3 | Claude | 125 | 0 | 37 | 40 | 48 | 0 | 98 | 106 | 117 |
| `rung-02000` | 1 | Codex | 125 | 0 | 32 | 35 | 58 | 0 | 129 | 150 | 147 |
| `rung-02000` | 2 | Claude | 124 | 0 | 39 | 38 | 47 | 0 | 127 | 152 | 146 |
| `rung-02000` | 3 | Claude | 125 | 0 | 41 | 39 | 45 | 0 | 119 | 133 | 137 |
| `rung-05000` | 1 | Codex | 125 | 0 | 31 | 35 | 59 | 0 | 195 | 236 | 214 |
| `rung-05000` | 2 | Claude | 124 | 0 | 39 | 38 | 47 | 0 | 183 | 219 | 199 |
| `rung-05000` | 3 | Claude | 125 | 0 | 42 | 38 | 45 | 0 | 185 | 223 | 200 |
| `rung-10000` | 1 | Codex | 125 | 0 | 32 | 35 | 58 | 0 | 327 | 396 | 343 |
| `rung-10000` | 2 | Claude | 124 | 0 | 41 | 38 | 45 | 0 | 298 | 366 | 312 |
| `rung-10000` | 3 | Claude | 125 | 0 | 42 | 38 | 45 | 0 | 296 | 363 | 309 |

⚠ **S4 latency is DESCRIPTIVE and is not a benchmark measurement.** One arm, no
interleaving, a shared machine. `ask` p50 goes **69 ms → 327 ms** across a 357×
corpus range and `answer` p50 **87 ms → 343 ms**; neither may be cited against
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)'s captures. ⚠ Two
long-running background builds were on this machine during earlier rungs and
**none during `rung-10000`**, which is the only rung whose latency anyone would
quote; said out loud because a loaded machine produces a clean, localised anomaly
that reads like a finding.

---

## 🔴 FINDING 1 — `band: weak` ⇔ `answerable: false`, 2 992 of 2 992

**Exactly coincident on every row**, all three sets, all eight rungs. The
2026-09-16 run saw this on 249 rows and the 2026-09-20 pass on 3 984; it now
holds on a **third, independently authored question set** and a **rebuilt
corpus**, at the same `b` but a different ladder.

**Band and decline carry one number.** Whether that is an invariant worth keeping
or a branch that never fires is
[SR-CONFIDENCE](../../../records/0141_confidence.md)'s, and a run with no key
cannot tell them apart.

## 🔴 FINDING 2 — the band's middle is NOT inert. It is one-way, and set 3 shows it.

**The 2026-09-20 pass reported the middle band inert** — *"43 of 43 transitions
are `grounded ↔ weak` from 100 documents up, and `partial` gains a member at no
point in the ladder."* **The second half survives. The first half does not.**

| set | `partial` across rungs 100 → 10 000 | membership identical? |
|---|---|---|
| 1 (Codex) | 35 · 35 · 35 · 35 · 35 · 35 · 35 | ✅ **yes, byte-identical** |
| 2 (Claude) | 38 · 38 · 38 · 38 · 38 · 38 · 38 | ✅ **yes, byte-identical** |
| **3 (Claude)** | **40 · 40 · 40 · 40 · 39 · 38 · 38** | 🔴 **no** |

Set 3 loses a member at `rung-01000 → rung-02000` and another at
`rung-02000 → rung-05000`. So **two transitions above `rung-seed` involve
`partial`**, where the baseline found zero of 43.

🔴 **The corrected statement is narrower and more useful than either the old
finding or its negation: the middle band is not inert, it DRAINS.** Across all
three sets and all seven transitions above the seed rung, `partial` **loses**
members and **gains none, ever** — 0 of 21 transitions adds one. A document
falling out of `partial` goes to `weak`; nothing arrives.

⚠ **Why sets 1 and 2 could not have shown this.** Their `partial` sets happened
to be stable over this corpus range; set 3 is the only set whose questions were
written against documents that *changed the corpus*, and it is the one that
moved. **A property observed on two sets was a property of two sets.** That is
the argument for a third set, measured rather than asserted.

**Still not a verdict.** Whether a one-way middle band is a well-behaved
invariant or a dead branch needs the key, and it is phase D's.

## 🔴 FINDING 3 — the authorship gap REPLICATES, and that is new

The 2026-09-20 pass found set 2 declining more than set 1 and could not say
whether that was *authorship* or *those 124 questions*. **A third set,
authored by a different session under a different brief, answers it.**

| rung | set 1 — **Codex** | set 2 — **Claude** | set 3 — **Claude** |
|---|---:|---:|---:|
| `rung-00100` | 26.4 % | 30.6 % | 26.4 % |
| `rung-01000` | 23.2 % | 29.0 % | 29.6 % |
| `rung-05000` | 24.8 % | 31.5 % | 33.6 % |
| **`rung-10000`** | **25.6 %** | **33.1 %** | **33.6 %** |

🔴 **At the top rung the two Claude-authored sets land within 0.5 points of each
other and 7.5 points above the Codex set.** Set 3 does not sit *between* set 1
and set 2 — it sits **on** set 2. Two authors made the gap visible; a third
author on one of the two sides makes it **replicable**, which is a different and
stronger thing.

⚠ **It is NOT a claim that either set is better, harder or fairer.** Only a key
separates *more genuinely unanswerable questions* from *phrasing this engine
retrieves worse*, and this run has no key. What it establishes is that the
difference tracks **who wrote the questions**, not which 124 questions they were.

⚠ **And it is a reason to keep set 1.** Every Claude-authored set is `informed`
permanently; the one externally-authored set is now also the only one that sits
apart on this measure.

## What looked fine, and what that does and does not mean

- **0 empty ranked lists** in 2 992 rows.
- **0 answers without a citation** in 2 992.
- **`freshness: current` on 2 992 of 2 992.**
- **0 failed calls**; **one** distinct `engine_commit` across every row.
- 🔴 **0 declines** — `fux answer` returned text on **every** call, including all
  **648** rows the band called unanswerable. **The decline signal is the band
  flag, not a null answer**, and the two stay separate columns.

⚠ **All of that is a statement about the RUN, not about the answers.** A run in
which nothing failed and every answer was cited is exactly what a run that is
confidently wrong also looks like.

## Headroom — why none is disclosed

🔴 **This is NOT a paired run.** One arm, one engine, no comparison and no
endpoint, so there is no direction in which headroom could be quoted.
[SR-RS](../../../records/0133_predictions.md) decision 22 governs a **paired**
run — two arms, an endpoint, a direction — and it does not reach this one.

⚠ **Stated rather than omitted**, because a missing headroom disclosure and an
inapplicable one look identical in a filed report, and only one of them is
honest. **W-204 phase B is the paired run**, and its own frozen pre-registration
carries the disclosure.

## Reproduce

```bash
cd ~/my_programs/fux-lab/corpora/golden/<RUNG>
/Users/arpitarya/my_programs/fux/.venv/bin/fux ask    "<question>" --json --band --top 10
/Users/arpitarya/my_programs/fux/.venv/bin/fux answer "<question>" --json
```

engine `7a88a165`, `b = 0.15`, `anchor = 0.0`, the ladder as the
[2026-09-21 rebuild](../2026-09-21-ladder-set-3-rebuild/report.md) froze it.

```bash
.venv/bin/python tools/quality-controls/golden_run.py --rung <RUNG> --sets 1,2,3 \
    --evidence work/regression/2026-09-21-golden-ladder-outputs-set-3/evidence/<RUNG> \
    --engine-commit 7a88a1657a183157a1cd842e5d392d55f65823f2
.venv/bin/python tools/quality-controls/rung_outputs.py --rung <RUNG> --sets 1,2,3 \
    --evidence work/regression/2026-09-21-golden-ladder-outputs-set-3/evidence/<RUNG>
```

## Authorship

| artifact | author | blind to the evaluation? |
|---|---|---|
| seed corpus, documents `01`–`15` + `a01`–`a05` | Codex | — |
| seed corpus, documents `16`–`22` + `a06` | **Claude** (set-3 authoring session) | no |
| `questions/set-1.jsonl` | **Codex** | blindness ended at the 2026-09-17 L11 breach (W-196) |
| `questions/set-2.jsonl` | **Claude** | never blind — author and runner are one model family |
| `questions/set-3.jsonl` | **Claude** | never blind, same reason |
| the ladder, all eight rungs | Claude Code, from `seed/` only | honour rule; nothing mechanical enforces it |
| this run | Claude Code | — |

**`classification: informed`**, on three independent grounds any one of which
suffices: sets 2 and 3 share an author with the runner; set 1 lost blindness in
2026-09-17's breach; and these rows feed a scored run.

⚠ **A fourth ground applies to set 3 alone:** this session rebuilt the corpus set
3 was written against, so it has read every seed document that set's author read.
That is not a key and not a breach — and it is one more reason the word `blind`
may never be attached to a set-3 number.

🔴 **No answer reached this session by any route, a paste included.** Nothing
here opened, listed, globbed, stat'd, hashed or counted either spelling of the
directory [L11](../../../records/0012_LAW-11-sealed-answer-key.md) decision 5
closes, and every recursive search over `work/` excluded `work/golden/`.
