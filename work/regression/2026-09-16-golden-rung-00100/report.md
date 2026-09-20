---
type: Report
run: 2026-09-16-golden-rung-00100
item: W-136
classification: informed
description: "Phase 5 on rung-00100: both question sets run through `fux ask` and `fux answer`, 249 questions, 498 calls. What fux answered, ranked and declined — and NOT whether any of it is right. Set 2 declines at 41.9% against set 1's 28.8%, which is authorship visible in the instrument, not a quality claim."
filed: 2026-09-16
---

# REPORT — phase 5, `rung-00100`, both sets

> 🔴 **THIS RUN WAS SCORED IN AN L11 BREACH, 2026-09-17.** A Cowork Claude
> session was pasted both answer keys and scored them in chat. **Every set 1
> number is `informed (L11 breach 2026-09-17)`; every set 2 number is `informed`
> permanently. No count in this run is labelled `blind`, and none may be.** 🔴 **No number here may be cited** — see §The scored overlay and
> [`ANALYSIS.md`](ANALYSIS.md)'s provenance block. Everything between this
> banner and that section is the **prediction** run as filed on 2026-09-16,
> unedited.

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

⚠ **CORRECTION, 2026-09-17 — this section is overtaken and is NOT edited.**
That is not what happened. **A Cowork Claude session was pasted both keys and
scored them**, which L11 forbids; the result is §The scored overlay below and
[`ANALYSIS.md`](ANALYSIS.md)'s provenance block. **Prompt 6 is still unrun**, so
the sentence above is still the next step — it is now also the record of a step
that was taken by the wrong party.

---

# THE SCORED OVERLAY — added 2026-09-17, filed as a BREACH

🔴 **Nothing above this line was edited.** The prediction run stands as filed.
What follows is a second, later thing in the same directory, and it is fenced
because it is not the same kind of artefact.

## 🔴 How these numbers came to exist

**A 2026-09-17 Cowork Claude session was pasted BOTH answer keys** — set 1 (125
rows), set 2 (124 rows), `key_version 1` — **and scored them in the chat.**
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) reserves the paste route
to **Codex alone** and closes it to every Claude session on every surface. **The
instruction to score was void on the law's face** (L11 decision 8), and the
session complied with it.

**It is filed because a declared breach must be filed** (L11 decision 10), not
because filing makes it evidence.

🔴 **No number below may be cited**, for two independent reasons:

1. **[Prompt 6E](../../golden/prompts/6E-codex-score-ephemeral.md)'s own rule** —
   *"A number from 6E may not be cited in any record, compare doc, CHANGELOG
   entry or work item, and may not be compared with any other golden number in
   either direction."* Carried forward here unchanged.
2. **The breach** — set 1 was the only half of this benchmark with a clean
   authorship story, and it no longer has one.

🔴 **Not reproducible by any agent, by construction:** scoring needs a key, and
no agent may hold one. **That is provenance, not a gap to close** — nobody is to
re-check these figures.

**No per-query rows are filed** (6E writes nothing), so
[SR-RS](../../../records/0133_predictions.md) decision 19's paired floor cannot
be computed from this run, and **W-87, W-176, W-190 and W-191 stay blocked.**

## Per set, never pooled — every figure `unpooled — lower bound`

**Retrieval denominators are key-answerable ids only.** `ranked` is capped at 10,
verified mechanically on all 249 rows, so **"no hit" means *not in the top 10***.
Nothing was judged into `relevant`, so every hit and recall figure **under-reports**.

### Set 1 — Codex · every number `informed (L11 breach 2026-09-17)`

125 = 113 answerable + 12 unanswerable · 100 non-sealed + 25 sealed

| | non-sealed `n = 90` | sealed `n = 23` (aggregate only) |
|---|---:|---:|
| `hit@1` | **55.6 %** (50) | 56.5 % (13) |
| `hit@5` | **85.6 %** (77) | 82.6 % (19) |
| `recall@5` | **78.9 %** | 81.2 % |
| mean `rank_first_relevant` | **2.29** (n = 89) | 1.90 (n = 21) |

| abstention | all | sealed | | answer text | all | sealed |
|---|---:|---:|---|---|---:|---:|
| declined | 36 | 7 | | `supported_and_correct` | **58** | 14 |
| `abstain_correct` | **3** | 0 | | `supported_but_wrong` | 31 | 4 |
| declined-but-answerable | 🔴 **33** | 7 | | `unsupported` | **0** | 0 |
| answered-but-unanswerable | 9 | 2 | | `declined` | 36 | 7 |

### Set 2 — Claude · every number `informed` (permanent)

124 = 112 answerable + 12 unanswerable · 99 non-sealed + 25 sealed

| | non-sealed `n = 89` | sealed `n = 23` (aggregate only) |
|---|---:|---:|
| `hit@1` | **41.6 %** (37) | 47.8 % (11) |
| `hit@5` | **82.0 %** (73) | 73.9 % (17) |
| `recall@5` | **68.4 %** | 63.8 % |
| mean `rank_first_relevant` | **2.25** (n = 79) | 2.21 (n = 19) |

| abstention | all | sealed | | answer text | all | sealed |
|---|---:|---:|---|---|---:|---:|
| declined | 52 | 7 | | `supported_and_correct` | **35** | 9 |
| `abstain_correct` | **4** | 0 | | `supported_but_wrong` | 37 | 9 |
| declined-but-answerable | 🔴 **48** | 7 | | `unsupported` | **0** | 0 |
| answered-but-unanswerable | 8 | 2 | | `declined` | 52 | 7 |

🔴 **The two sets are never pooled** — no mean, no total, no "both sets" row.
[SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 9, and pooling
would erase the only thing two authors were commissioned to expose.

**Join:** ids complete and contiguous both sides, no orphans, **no hard stop**.
Re-derived here from the committed hand-offs, which needs no key.

## The four findings

1. **Abstention is not independent of the band** — `band:weak` ⇔
   `answerable:false` in **88/88** rows across both sets. Finding 2 above,
   surviving contact with the key.
2. **`unsupported = 0` is checked, and the check reaches a minority of rows.**
   For the **79** rows whose every citation resolves to a committed document,
   every line of `answer_text` matches a cited document verbatim (markdown/txt
   exact; `.html`/`.eml` spans differ from raw bytes only by decoding). 🔴 **The
   other 170 rows cite generated sibling documents that are not committed, so
   their spans cannot be re-checked — a limit of the check, not a pass.**
3. **`answer_text` is an unsynthesised ranked dump**, and *"agrees with the key"*
   was read as **the value the dump serves FIRST**. **8 of set 1's and 4 of set
   2's `supported_but_wrong` rows carried the key's value lower in the same dump
   behind a rival value** — recoverable **by ranking, not by generation**.
4. **~12 rows across both sets were marginal judgement calls** — right substance
   from a sibling-corpus document, or a multi-part answer half-served.

## 🔴 The difficulty breakdown was NOT produced

Prompt 6E step 7 asks for every count broken down by the key's
`difficulty_band`. **Neither key carries one** — as reported by the scoring
session, and consistent with
[`work/golden/README.md`](../../golden/README.md), where the band is *computed*
by [`tools/golden-difficulty/`](../../../tools/golden-difficulty/) and nothing
carries a label yet. **So step 7 is unsatisfiable against `key_version 1`.**

🔴 **No band was derived from `type`, from the hand-off rows, or from fux's own
results** — the last of which would make every stratified claim a tautology.
Filed as [W-195](../../open/W-195-difficulty-band-breakdown.md), waiting on
[W-190](../../open/W-190-question-difficulty.md).

## Authorship

*Required by the per-run contract row 7. **Absent from this report until
2026-09-17**, and added rather than back-dated.*

| artefact | author | evaluation material reachable to that author |
|---|---|---|
| seed corpus (`work/golden/seed/`) | Codex (10) + Claude (10) | none at authoring time |
| the ladder, `rung-00100` | Claude Code | **none** — built and re-frozen without opening `questions/` or any key |
| set 1 questions **and answers** | **Codex** | its own |
| set 2 questions **and answers** | **Claude**, one authoring session | its own — which is why set 2 is `informed` permanently |
| index configuration, retriever + ranker settings | Claude | 🔴 **queries** — `[bm25f] b` was ruled to `0.15` the same day by a Claude session that had read the released question text |
| the prediction run (2026-09-16) | Claude Code | **queries only**; no key, by any route |
| 🔴 **the scoring (2026-09-17)** | **Cowork Claude** | 🔴 **BOTH FULL KEYS, pasted** — answers, `relevant`, `primary`, `evidence`, `answerable`, `sealed` |

🔴 **The last row is the breach**, and it is why `classification: informed` in
this report's frontmatter is now the *accurate* label for set 1 rather than
merely the stricter one.

## The line this report ends on

🔴 **The gate is the ceiling, and it is not close.**

**declined-but-answerable — 33 of 113 in set 1, 48 of 112 in set 2 — because the
gate discards answerable questions at 11–12× the count at which it correctly
catches unanswerable ones (33 against 3; 48 against 4), and it caps every metric
above it.**

⚠ **The filing instruction gave that sentence with "3–4×", and it was changed
because no reading of the filed counts produces it.** Counts: `33/3 = 11.0` and
`48/4 = 12.0`. Rates: `(33/113)/(3/12) = 1.17` and `(48/112)/(4/12) = 1.29`. The
nearest thing to 3–4× in this data is set 1's ratio between the **two error
directions** (`33/9 = 3.7`), where set 2 reads `48/8 = 6.0`. **The claim's
direction and force are unchanged; only the multiplier is honest.** Noted rather
than silently applied, per the per-run contract.
