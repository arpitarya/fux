---
type: Report
run: 2026-09-16-golden-rung-00100
item: W-136
classification: informed
description: "Phase 5 on rung-00100: both question sets run through `fux ask` and `fux answer`, 249 questions, 498 calls. What fux answered, ranked and declined — and NOT whether any of it is right. Set 2 declines at 41.9% against set 1's 28.8%, which is authorship visible in the instrument, not a quality claim."
filed: 2026-09-16
---

# REPORT — phase 5, `rung-00100`, both sets

**Ruled by nothing. This is NOT A PAIRED RUN** — one engine, one configuration,
one pass, no arms — so [SR-RS](../../../records/0133_predictions.md) decision
22's paired headroom does not apply, and a fabricated version of it would be
worse than none. What is disclosed instead is below: declines, the band
distribution, empty ranked lists, and the slowest results.

It is a **prediction run**: it records what fux did and files **no score**.

⚠ **`classification: informed`, and it is the stricter of the two labels rather
than the accurate one** — this run files no number to classify at all. It is
labelled that way because **it feeds a scored run**: prompt 6 scores these
hand-offs, and **set 2 is `informed` by construction**, its author and its runner
being one model family. A `surface capture` label here would be defensible and
would leave a later reader one step from treating set-2 scores as blind.

🔴 **Whether any answer is correct is not in this file, and could not be.** There
is no answer key anywhere and none reached this session by any route
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). **Correct /
incorrect appears for the first time in
[prompt 6](../../golden/prompts/6-codex-score.md)'s output, from Codex**, against
a key Arpit pastes there.

**What Arpit gives Codex** — the two self-contained hand-offs:

- [`evidence/handoff-set-1.jsonl`](evidence/handoff-set-1.jsonl) — 125 lines
- [`evidence/handoff-set-2.jsonl`](evidence/handoff-set-2.jsonl) — 124 lines

## The run

| | |
|---|---|
| rung | `rung-00100` — 100 documents |
| engine | `fux 2.0.1`, commit `e71f27c6` |
| index | 🔴 **the rung's own; NOT re-ingested** — the version matches the stamp and only the commit differs |
| corpus check | **100/100 documents hashed against the manifest, 0 mismatches**; `seed_drift` NONE |
| calls | 249 questions × 2 = **498** |

🔴 **`[bm25f] b` changed from `0.75` to `0.15` earlier today**
([W-144](../2026-09-16-b-sweep-2/VERDICT.md)). It is applied at query time, so no
re-ingest was needed — **and it moves every score and every ranked order here.
No number in this report may be compared with any golden number filed before
2026-09-16.**

---

## Per set, never pooled

🔴 **The gap between the sets is the measurement.** Set 1 is Codex-authored, set
2 is Claude-authored; a mean across both erases exactly what two authors were
commissioned to expose.

| | **set 1** (Codex) | **set 2** (Claude, `informed`) |
|---|---:|---:|
| questions | 125 | 124 |
| `grounded` | **52** | 32 |
| `partial` | 37 | 40 |
| `weak` | 36 | **52** |
| **declined** (`answerable: false`) | **36 — 28.8 %** | **52 — 41.9 %** |
| empty ranked list | **0** | **0** |
| no citation | **0** | **0** |
| `ask` p50 / max | 71 / 78 ms | 72 / 94 ms |
| `answer` p50 / max | 88 / 106 ms | 88 / 111 ms |
| slowest question | `s1-037`, 177 ms | `s2-008`, 183 ms |

⚠ **Every set 2 number above carries `informed` permanently** — its author and
its runner are the same model family
([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md)).

## 🔴 Finding 1 — the two sets elicit different confidence, and that is authorship

**Set 2 is declined on 41.9 % of its questions against set 1's 28.8 %**, and the
band distributions are close to mirrored: set 1 skews `grounded` (52 of 125), set
2 skews `weak` (52 of 124).

🔴 **This is NOT a statement that either set is better, harder, or more
correct.** It cannot be — nothing here was scored. What it says is that **two
authors writing over the same 20 seed documents produced question sets the engine
responds to differently**, which is precisely the bias two sets were commissioned
to make visible instead of invisible.

⚠ **The scored numbers are where this becomes a finding or a nothing.** If set 2's
extra declines land on questions whose answers exist, that is a recall problem; if
they land on unanswerables, it is abstention working. **Only prompt 6 can tell
those apart**, and this report may not guess.

## 🔴 Finding 2 — `weak` and `declined` coincide EXACTLY, on both sets

**Set 1: 36 `weak`, 36 declined, 36 both. Set 2: 52, 52, 52.** Not correlated —
**identical**, in all 249 questions.

That is [SR-CONFIDENCE](../../../records/0141_confidence.md)'s gate behaving as
Arpit ruled it on 2026-09-14 (*does `weak` imply `answerable: false`* → yes), now
observed on a 249-question corpus rather than argued. **It is a fact about the
band, not about the answers.**

⚠ **It also means the two columns above carry one number, not two**, and a reader
comparing them would be comparing a thing with itself. Stated so nobody counts it
twice.

## What looked wrong

**Nothing.** No empty ranked list, no uncited answer, no failed call, no timeout,
and no question that returned nothing on either verb. Latency is flat: p50 within
1 ms across the two sets on both verbs.

⚠ **"Nothing looked wrong" is a statement about the RUN, not about the answers.**
A confidently wrong answer looks exactly like a confidently right one from here.

## What this run does NOT say

- 🔴 **Whether fux answered anything correctly.** Prompt 6's, from Codex.
- 🔴 **Whether a decline was right.** A decline is not a wrong answer, and this
  report may not call it one.
- **Anything about another rung.** One rung, named above.
- **Anything comparable to a pre-2026-09-16 golden number**, because `b` moved.

## Next

**Arpit gives the two hand-off files to Codex with
[prompt 6](../../golden/prompts/6-codex-score.md) and pastes each key there
himself.** Scoring is a chat he attends; no Claude session takes part.
