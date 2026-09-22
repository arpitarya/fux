---
type: Verdict
run: 2026-09-22-golden-final-score
description: "W-204 phase D — the one score. 11 716 per-query rows joined to the key with ZERO join errors, across v1.0.0 · v2.0.1 · HEAD on eight rungs and three question sets. Retrieval improves monotonically across the three engines and every one of the nine paired comparisons clears SR-RS decision 19's floor. The abstention layer is the opposite story: HEAD withholds on 818 of 2 992 and the key says 747 of those were answerable."
classification: informed
filed: 2026-09-22
---

# FINAL-SCORE — v1.0.0 · v2.0.1 · HEAD, scored against the key

🔴 **Every number in this document is `informed`, permanently.**
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) decision 14: Arpit ran
`just golden-unlock` on 2026-09-22 at 11:41 and a Claude session scored from the
key. There is no arm here whose runner's model family had not seen the answers,
and locking again does not create one. **Do not cite any of this as a blind
measurement**, and do not compare it with a number from before the unlock as if
the labels matched.

## The one table

**hit@5, per set, eight rungs each.** Sets are **never pooled** — three columns,
three instruments, read down not across.

| set | questions × rungs | **v1.0.0** | **v2.0.1** | **HEAD** |
|---|---:|---:|---:|---:|
| set-1 (Codex) | 1 000 | 699 · 69.9 % | 723 · 72.3 % | **833 · 83.3 %** |
| set-2 (Claude) | 992 | 608 · 61.3 % | 634 · 63.9 % | **744 · 75.0 %** |
| set-3 (Claude) | 1 000 | 625 · 62.5 % | 672 · 67.2 % | **771 · 77.1 %** |

**The paired comparisons, per set** — [SR-RS](../../../records/0133_predictions.md)
decision 19's floor is a net of **6 flips**, and it is applied per set, never to a
pooled total:

| set | v1 → v2 | v2 → HEAD | v1 → HEAD |
|---|---|---|---|
| set-1 | +79 / −55 = **+24** | +114 / −4 = **+110** | +163 / −29 = **+134** |
| set-2 | +76 / −50 = **+26** | +125 / −15 = **+110** | +173 / −37 = **+136** |
| set-3 | +85 / −38 = **+47** | +127 / −28 = **+99** | +163 / −17 = **+146** |

🔴 **Nine of nine clear the floor, in the same direction, on three independently
authored sets.** That is as close to unambiguous as this benchmark can produce.
The weakest comparison (v1 → v2 on set-1, net +24) clears by four times.

## What actually improved, and it is not uniform

**hit@5 by rung**, summed within an arm across its three sets (1 000 + 992 +
1 000 = 2 992 questions per arm, 374 per rung):

| rung | v1 | v2 | HEAD | HEAD − v1 |
|---|---:|---:|---:|---:|
| `rung-seed` | 284 | **308** | 306 | +22 |
| `rung-00100` | 256 | 275 | **296** | +40 |
| `rung-00200` | 245 | 264 | **300** | +55 |
| `rung-00500` | 235 | 246 | **294** | +59 |
| `rung-01000` | 229 | 238 | **292** | +63 |
| `rung-02000` | 232 | 234 | **288** | +56 |
| `rung-05000` | 225 | 232 | **286** | +61 |
| `rung-10000` | 226 | 232 | **286** | +60 |

🔴 **The gap is a function of corpus size, and that is the result worth keeping.**
v1 loses **30 hits** from `rung-00100` to `rung-10000` and v2 loses **43**; HEAD
loses **10**. The three engines are closest on the smallest corpus and furthest
apart on the largest. **What improved between v1 and HEAD is resistance to
distraction**, not raw matching — which is exactly what an index-and-refer design
is supposed to buy and the first time this project has measured it.

⚠ **`rung-seed` is the one rung where HEAD is not first** (306 against v2's 308,
a net of 2 — well under the floor, so *not distinguishable*). Named because it is
the only inversion in the table and a reader will find it; it is not a finding.

## 🔴 The abstention layer is the bad news, and it is worse than "unmeasured"

| | v1.0.0 | v2.0.1 | HEAD |
|---|---|---|---|
| carries a `band` | **no** — the field did not exist | yes | yes |
| ever says `answerable: false` | no | 🔴 **no — 2 992 of 2 992 are `true`** | yes, 818 |
| abstentions the key agrees with | — | — | **71** |
| abstentions the key contradicts | — | — | **747** |

🔴 **v2's confidence band never abstains.** It emits `weak` on 975 rows and
`answerable: true` on **all 2 992**. The band is present and is not connected to
a decision — so the abstention layer is **HEAD-only in practice**, and there is
no cross-arm comparison to make. ⚠ **That is an absence, not a regression**, and
no row here may be read as *"HEAD abstains worse than v2"*.

🔴 **HEAD abstains on 818 of 2 992 (27.3 %), and the key says 747 of those 818
— 91.3 % — were answerable.** Stated as the two numbers that actually decide
whether an abstention layer is worth having, per set (each set carries **12
unanswerable questions**, so 96 rows across eight rungs):

| | set-1 | set-2 | set-3 |
|---|---:|---:|---:|
| **caught** — unanswerable it withheld on | 31/96 · **32.3 %** | 20/96 · **20.8 %** | 20/96 · **20.8 %** |
| **cost** — answerable it withheld on | 205/904 · **22.7 %** | 271/896 · **30.2 %** | 271/904 · **30.0 %** |
| **precision** — abstentions that were right | 31/236 · **13.1 %** | 20/291 · **6.9 %** | 20/291 · **6.9 %** |

🔴 **It catches at most a third of what it is for and withholds a quarter to a
third of what it could have answered.** On set-2 and set-3, **fourteen answerable
questions are sacrificed for every unanswerable one caught.** The band is not
mis-tuned at the margin; at this operating point it costs far more than it saves.

⚠ **Stable across the ladder, which rules out one explanation.** On set-1 it
withholds 25–33 per rung from `rung-seed` to `rung-10000` and catches 3–5 — the
rates barely move across a 357× corpus range, so this is **where the threshold
sits**, not a corpus-size effect that a bigger index would fix.

**Read the two halves together and the picture is sharp:** HEAD ranks the right
documents into the top 5 more often than either predecessor at every corpus size,
and then declines to answer a quarter of the time, almost always wrongly. **The
retrieval is the strong part of this engine and the abstention is the weak
part**, and that is the opposite of where the last year of work went.

⚠ **`answered_unanswerable` is 288 in every arm** — 96 per set, identical across
v1, v2 and HEAD. Every engine returns text for the same 96 planted-unanswerable
questions per set. The answer layer does not decline on them at all, in any
version; only the band does, and it declines on the wrong ones.

## What this run does NOT say

- **No answer-text verdict.** `correct · partial · wrong · declined` with the
  evidence quote as the criterion is a **judgement**, and nothing here made one.
  `evidence_quoted` (v1 1 019 · v2 1 494 · HEAD 1 696) is a **normalised
  substring test** reported under its own name — an answer can quote the right
  sentence and be wrong, or paraphrase correctly and match nothing.
- **No difficulty bands.** Phase D step 2's `d <= 1 / 2 / >= 3` thresholds freeze
  the moment a number is filed by band (SR-RS decision 10b). **Nothing is filed
  by band here, so nothing is frozen.**
- **No pooling.** Step 6 writes a key byte and stays Arpit's.
- **Nothing about L1's dependency amendment.** All three arms carry no runtime
  dependency ([ARMS.md](../2026-09-21-golden-three-engines/evidence/ARMS.md)).
- ⚠ **The interpreters differ** — v1 and v2 on CPython 3.11.15, HEAD on 3.14.3 —
  because a released wheel's `Requires-Python` is part of what was released.
  Recorded in ARMS.md, not equalised, and not priced here.

## The controls held

- **Zero join errors across 11 716 rows.** Every hand-off row has a key line and
  every key line has a row, in all 94 arm × rung × set buckets. A partial join is
  how a partial score comes to look like a whole one; this one is complete.
- **The null control is exact.** `null-a` and `null-b` — the same arm run twice
  on the same rung — score **identically** (140 / 235 / 257 / 236 on
  hit@1/5/10/primary). The harness adds no variance of its own.
- **The output carries no answer.** ids, ranks, booleans and counts; the
  allow-list was checked against the emitted field set and is clean.

## Evidence

- [`evidence/per-query.jsonl`](evidence/per-query.jsonl) — 11 716 rows
- [`evidence/aggregate.json`](evidence/aggregate.json) — 94 buckets
- [`report.md`](report.md) · [`ANALYSIS.md`](ANALYSIS.md)
- the scorer: [`tools/golden-score/score.py`](../../../tools/golden-score/score.py),
  driven by [`tools/quality-controls/phase_d.py`](../../../tools/quality-controls/phase_d.py)
- the arms: [`2026-09-21-golden-three-engines`](../2026-09-21-golden-three-engines/evidence/ARMS.md)
