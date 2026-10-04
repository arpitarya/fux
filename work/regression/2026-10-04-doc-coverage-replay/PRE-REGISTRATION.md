---
type: Pre-registration
name: PRE-REG-DOC-COVERAGE
description: "W-256 section 2 - frozen before the replay: does any doc_coverage_floor on a fixed grid catch at least 50 percent of the unanswerable questions while demoting fewer correct answers than a coin at the same withhold rate, over the W-213 captures at rung-01000 (3 retired sets, 374 rows)? PASS moves doc_coverage_floor in tune.toml; FAIL or INCONCLUSIVE leaves SR-CONFIDENCE d12's off standing with a measured reason."
run: 2026-10-04-doc-coverage-replay
item: W-256
frozen: 2026-10-04
---

# W-256 section 2 - abstention gate 2 (`doc_coverage`), replayed on stored fields

**Frozen 2026-10-04, before the replay script produced a number.** The run
directory holds this file and nothing else until the measurement lands. It is
`informed` permanently (section 8), a replay with no new engine call.

## 1 - The question, and what waits on it

[SR-CONFIDENCE](../../../records/0141_confidence.md) decision 12 ships
`doc_coverage_floor = 0.0` (the clause **off**) *"because the two populations
overlap"* - measured in 2026-08 on the retired playground's 50 goldens and 15
decoys, an instrument [SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md)
retired, and the record itself says turning the gate on *"needs a new
measurement on a golden rung in `fux-lab`"*. This is that measurement, on data
already in hand. It is gate 2 of B-261's eight; W-251 section 4 item 11
(*`separation` stays the label's quantity; this is the next lever*) waits on the
number.

## 2 - The bar (verbatim from W-256 section 2; it may not move)

> A floor must catch **at least 50 %** of unanswerables while demoting **fewer
> correct answers than a coin at the same withhold rate.**

This is the W-213 criterion that removed gate 1
([W-213 report](../2026-09-22-band-operating-point/report.md), Result 2). PASS
-> `doc_coverage_floor` moves in `.fux/tune.toml` (L12) and SR-CONFIDENCE
decision 12 is amended; FAIL / INCONCLUSIVE -> filed, decision 12's *off*
stands with a measured reason. **Then** gates 4 and 3 (the ruled u017 pair)
become replayable on `answer_text` the same way - **a successor item, not this
one.**

## 3 - The data, and how every label is known

**Captures:** `work/regression/2026-09-22-band-operating-point/evidence/rung-01000/capture-set-{1,2,3}.jsonl`
- 125 + 124 + 125 = **374 rows**, each a stored `ask --json --band --why` /
`answer --json` result carrying the whole `confidence` block
(`coverage`, `doc_coverage`, `doc_coverage_floor`, `separation`,
`separation_floor`, `support`, `missing`, `verified`, `failed`, `band`,
`answerable`) plus `answer_text`, `ranked` and `id`. Captured at engine
`7d41fdab` (W-213), `doc_coverage_floor = 0.0` on every row (the script checks
this and files any exception as a problem).

**The rows themselves do not say which question is unanswerable, and the item's
sentence *"already carry ... 36 unanswerables / 340 answerable"* is wrong in
one number.** A capture row has no label field; its own `confidence.answerable`
is the *engine's* output and, since W-214 (`weak` stopped being a refusal), is
true on essentially every row. The label is joined by `id` from
`work/golden/retired/set-N/expected.jsonl`:

| | set-1 | set-2 | set-3 | total |
|---|---:|---:|---:|---:|
| capture rows at rung-01000 | 125 | 124 | 125 | **374** |
| key `answerable == false` (**unanswerable**) | 12 | 12 | 12 | **36** |
| key `answerable == true` | 113 | 112 | 113 | **338** |

So the item's **340** is **338** (374 - 36). The 36 is right. Capture ids and
key ids match one-for-one in all three sets (checked by id only, no answer
content read). The W-213 report's "96 key-unanswerable per set" is 12 x 8
rungs, not a per-set count at this rung.

**L11, checked and satisfied.** `work/golden/retired/` holds the sets that
retired on 2026-09-22 under [L11](../../../records/0013_LAW-11-sealed-answer-key.md)
decision 14; [`work/golden/README.md`](../../golden/README.md) (section "All
three sets RETIRED on 2026-09-22") and each `retired/set-N/README.md` state that
they are *"open regression data any session may read in any state"* and that no
number measured on them is evidence about the engine's quality. **The sealed
answers directory is not read and not needed**, and the replay script's only
path under `work/golden/` is `retired/` (as `band_sweep.py`'s).

## 4 - Definitions (all fixed now)

- **Population:** the 374 rows of rung-01000, three sets **pooled**. Rungs
  other than rung-01000 are not used: eight rungs of the same question are
  eight correlated observations, which is why W-213 adjudicated at one rung and
  this does the same.
- **Unanswerable:** the retired key's `answerable == false`.
- **Correct:** a key-answerable question whose `answer_text` quotes a key
  evidence quote - **`evidence_quoted`**, the named proxy of
  [`band_sweep.py`](../../../tools/quality-controls/band_sweep.py) and
  `tools/golden-score/score.py` (`score_one`, imported not restated). ⚠ A
  proxy, not a judgement: a substring test under-detects correct answers; its
  bias on *this* comparison has no declared direction (it shrinks both the
  correct count and the coin's expectation), and the run says so rather than
  claiming one.
- **Band at a floor `f`:** the engine's **own** band rule, by constructing
  `fux.query.confidence.Confidence` from the stored fields with
  `doc_coverage_floor = f` and the stored `separation_floor` (the shipped
  0.10) - reconstructed, never reimplemented, exactly as W-213's replay did.
  **Self-check:** at `f = 0.0` the reconstructed band must equal the stored
  `band` on every row; any disagreement is a problem and the run is void.
- **Demoted (= withheld) at `f`:** the band at `f` differs from the band at
  `0.0`. Since W-214 a demotion is `grounded`/`weak` -> `partial`, a published
  signal and not a refusal; this measurement treats it as abstention gate 2
  of B-261 means it (a row the gate would hold back), and says that is the
  reading.
- **Reachable unanswerable:** an unanswerable whose band at `0.0` is `weak` or
  `grounded`. Rows already `partial` (via `missing` / stale) or `none` (no
  support) are not reachable by this clause and are not "caught" by it.
- **Catch rate at `f`:** (reachable unanswerables demoted) / (reachable
  unanswerables).
- **Withhold rate at `f`:** (rows demoted) / 374.
- **Demoted-correct at `f`:** correct rows demoted.
- **Coin at the same rate:** a coin that demotes each row independently with
  probability equal to the withhold rate. Its expected demoted-correct is
  `(correct rows) x (withhold rate)`; the tail probability of observing as few
  as the actual demoted-correct is the **exact lower-tail binomial**
  `P(X <= k)`, `X ~ Binomial(correct rows, withhold rate)`.
- **AUC:** `P(doc_coverage of a random unanswerable < that of a random
  answerable)`, ties counted half - reported over all rows and over the rows
  reaching the clause. It is **reported, not decisive**: a floor needs the
  distribution's tail, not its centre.

## 5 - The candidate floors: a fixed grid, stated now

**`f` in {0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00}** - eight floors,
0.10 apart, covering the range the 2026-08 measurement saw (goldens' minimum
0.401, median 0.882; the one decoy 0.710) and ending at `1.0`, which the record
reads as *structural* (every term the corpus has, the cited document has too).
No floor is added, dropped or re-spaced after a number exists. Because eight
floors are tried, the per-floor significance level is **Bonferroni
0.05 / 8 = 0.00625**.

## 6 - PASS / FAIL / INCONCLUSIVE

A floor **passes** iff **all three** hold:

1. **catch rate >= 0.50** (pooled), AND **demoted-correct < the coin's
   expectation** (pooled) - the bar of section 2, point estimates;
2. **exact lower-tail p <= 0.00625** (pooled) - the coin comparison is
   distinguishable from chance, not a draw;
3. **(1) holds in each of the three sets separately** - W-213's standard,
   that a floor which clears pooled but fails a set it was not fitted to is not
   a floor.

Then:

- **PASS** - at least one grid floor passes. The **lowest** passing floor is
  the reported one (the smallest departure from *off* that works, SR-RS
  decision 18's descending logic); the rest are listed. The ruling on moving
  `doc_coverage_floor` and amending decision 12 is Arpit's to ratify; the
  run supplies the number.
- **FAIL** - no grid floor meets the point criteria of (1) pooled. Decision 12's
  *off* stands with this measured reason.
- **INCONCLUSIVE** - any of: (a) fewer than **20** reachable unanswerables
  pooled (a 50 % catch would be under 10 rows - no headroom to be right or wrong
  with, [SR-RS](../../../records/0133_predictions.md) decision 22d's rule that a
  null measured where nothing can move is not a null); or (b) some floor meets
  (1) pooled but no floor meets (2) and (3) together - the direction is right
  and not distinguishable from chance, or it does not hold set by set. (b) is
  filed with the floor named, **never promoted to PASS by a looser alpha**, and
  goes to Arpit.

Headroom is reported per direction, never bare ([SR-RS](../../../records/0133_predictions.md)
22b): improvement headroom = reachable unanswerables (what a floor could still
catch); regression headroom = correct rows currently `grounded`/`weak` (what a
floor could still cost). Decision 19's paired floor is **not applicable** - this
is not a paired comparison of two arms but a gate against a rate-matched coin -
and the exact-binomial discipline is the same one `verdict.py` applies, with the
family correction above. A result between clearly passing and clearly failing is
written up as AMBIGUOUS and handed to Arpit, not adjudicated by the runner
(decision 10b).

## 7 - The instrument

[`tools/quality-controls/doc_coverage_replay.py`](../../../tools/quality-controls/doc_coverage_replay.py)
(written for this run, frozen with it). It imports `band_sweep.py`'s loader,
retired-key path and scorer (one copy of each), reconstructs the engine's
`Confidence` per floor, writes `evidence/per-query.jsonl` (one row per question
per floor: `id`, `arm`, `doc_coverage`, both bands, the two labels),
`evidence/result.json` and prints the table. **Run once, with the command in its
docstring.**

⚠ **Replay of stored fields only.** `doc_coverage` is read from the capture and
never recomputed from a newer index: a different index would be a different
run called by the same name (the item's hazard). The rows describe the
engine at `7d41fdab`; if the engine's `doc_coverage` definition has changed
since, **that does not change what this measures** (the stored value), but the
report says it and a PASS ruling would owe a re-check on the live engine
before `tune.toml` moves.

## 8 - Classification, authorship, what this cannot show

**`informed`, permanently**, three ways over: the sets are retired and open
(L11 decision 14); sets 2 and 3 were authored by the model family that
built and tunes the engine; the proxy and this document are the same family's.
Retiring changes what the data is *for*, not what it has seen.

| artifact | author | could reach |
|---|---|---|
| set-1 questions and key | Codex (Arpit, 2026-09-15) | retired, open |
| set-2, set-3 | Claude, from `work/golden/seed/` | retired, open |
| the captures | W-213, this repository's tooling | the retired key, to score |
| this document, the script and the run | Claude Code, one session family | the retired sets; **not** the sealed answers directory |

It cannot show: a floor's behaviour on any corpus other than the lab's
generated rung-01000 (one corpus, three question sets); ground truth beyond the
`evidence_quoted` proxy; that a PASS generalises (detectability is not
generalisation, SR-RS decision 19's last bullet); or anything about gates 3, 4
and the other five.

## 9 - What would make this pre-registration wrong

- A capture row whose `doc_coverage_floor` is not `0.0`, or a replay that
  disagrees with the stored band at `0.0` - the instrument is wrong, not the
  engine, and the run is void.
- Capture and key ids that do not join one-for-one (counted at freeze: they do).
- `Confidence` changing its constructor between this freeze and the run - the
  run then reports it and does not patch the script silently.
