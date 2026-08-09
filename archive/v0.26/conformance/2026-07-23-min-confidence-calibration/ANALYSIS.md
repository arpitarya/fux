# ANALYSIS — `answer` confidence-floor calibration

**Diagnosis:** the confidence floor is a *sound mechanism* pointed at a signal
that does not separate the two populations it must separate. On the acme corpus,
**no `min_confidence` value simultaneously declines the 4 typed-unanswerables and
preserves the 55 answerable pairs.** The requirement is a floor in the empty
interval `[0.25, 0.087]`.

## The recommendation (concrete)

**Ship `min_confidence = 0.0` (disabled) as the default.** Keep the knob;
document the trade-off curve. This is exactly the outcome the compare doc names:

> "If no single value satisfies 1–5, that is itself the finding: report the best
> achievable trade-off with the measured cost, and **do not ship a default that
> declines correct answers.**" — `answer-decline-floor.compare.md`, §"The
> calibration rule".

And handoff 0006 DoD 6 / Open Question M4: *"ship permissive-with-measurement …
let the evidence pick the follow-up."* The evidence is now in hand and it says
0.0.

## Why no value works — root cause

1. **The score is uncalibrated and near-uniform for a small corpus.** The
   per-sentence `score` is `passage_norm × (overlap+0.05) × (0.5+0.5·centrality)`,
   optionally scaled by `qsim`. `passage_norm` is normalised to the *best passage
   in that query's own pool*, so it is relative-within-query, not comparable
   across queries. Two different questions' "0.20"s mean different things.

2. **The fabrication signature is weak absolute score — but so are legitimate
   terse answers.** The compare doc's Option-A thesis ("weak top score is the
   fabrication signature") holds for the crypto case (0.2488) but collapses
   against real answers that are *also* weak: a one-line factual answer
   ("amounts are stored as int64 minor units", bc 0.177) or a zero-overlap
   paraphrase answer (bc 0.087) score no higher than an off-topic fabrication.

3. **`zero-overlap` and `stale-vs-current` answerables are the worst hit.**
   These are precisely the classes the *rest* of phase 6 exists to help (FuxVec
   rescue, supersession). A floor high enough to catch fabrications guts them:
   at 0.25, 3 of the 4 lowest false-declines are zero-overlap/stale answers.

4. **The single strongest fabrication (crypto, 0.2488) is the ceiling.** It out-
   scores 13 genuine answers. The compare doc already anticipated this exact
   defeat: *"a single strong but wrong match … defeats both [floor and margin] …
   a real, permanent limit of extractive retrieval without a model."*

## Specific fux improvements (each with a repro)

These are the paths that could actually close the gap; none is a calibration
tweak, so none belongs in this v0.25.0 change.

- **F1 — Calibrate the sentence score to be cross-query comparable.** The floor
  can only work against an *absolute* signal. Candidate: expose the raw
  (un-normalised-by-pool) passage BM25F score and/or the raw top dense cosine as
  a second, comparable confidence, and floor on *that* (ADR 0010's 0.23–0.26
  dense-noise band is a real absolute anchor; the current sentence score is not).
  Repro: `evidence/dump_scores.py` already isolates the value — add the raw
  dense cosine per question and re-sweep; if the dense cosine separates the
  classes where the sentence score does not, that is the floor's true home.

- **F2 — Floor on the dense plane, not the fused sentence score.** ADR 0010
  measured a 0.23–0.26 *dense noise band* on binary FuxVec. A floor on top dense
  cosine (question vs best passage) is anchored to a measured physical quantity,
  not a formula output. Needs the dense cosine surfaced at answer time.
  Reopen-trigger for a dense-floor compare doc.

- **F3 — This is the margin check's reopen-trigger, and it does NOT fire.**
  Option B (runner-up margin) was deferred pending "a fabrication whose top score
  clears the calibrated floor". There is no calibrated floor, so the trigger is
  moot: margin cannot rescue a case where the *floor itself* has no valid value.
  Record: margin stays deferred; the real follow-up is F1/F2 (an absolute,
  calibrated signal), not B.

- **F4 — Accept the documented limit.** Per the compare doc, a strong-but-wrong
  single match is a permanent limit of model-free extractive QA. The honest
  product statement is "answer declines only when the corpus has near-zero
  lexical overlap; a fluent out-of-scope question sharing incidental vocabulary
  can still be answered — verify citations." Ship that as the guarantee, not an
  implied never-fabricate.

## What this run does NOT claim

- It does not claim the mechanism is buggy. `min_confidence` behaves exactly as
  specified; the CLI matched the script at every boundary tested. The defect is
  calibration headroom, not code.
- It does not claim a larger/real corpus would behave identically. The score is
  pool-relative; a 10⁵–10⁶-doc corpus may spread the distributions differently.
  That is an argument for F1 (make the signal absolute), not for guessing a
  number now. **Do not ship a ranking/behaviour default off this one synthetic
  corpus** (CLAUDE.md conformance law) — which is itself a second reason 0.0 is
  the correct default today.

## Gate-by-gate result

| Gate | Verdict | Evidence |
|---|---|---|
| #1 decline 4/4 unanswerable | needs floor >= 0.25 | `evidence/acme-unanswerable.json` |
| #2 gibberish still declines | ✅ any floor (empty pool) | `evidence/gibberish.json` |
| #3 fixture 21-pair | ✅ no-op (`ask`, not `answer`) | README.txt |
| #4 acme 55 answerable, 0 false decline | needs floor <= 0.087 | `evidence/acme-answerable-55.json` |
| #5 synthetic 1k/5k/10k | ✅ no-op (`find`; no answer pairs) | README.txt |

**#1 and #4 have no common solution. Ship 0.0.**

## References

- `docs/compare/answer-decline-floor.compare.md` — the calibration rule (load-
  bearing) and the deferred margin check (Option B).
- `docs/adr/0010-fuxvec-binary-dense-search.md` — the 0.23–0.26 dense noise band
  (the absolute anchor F1/F2 should use instead of the pool-relative score).
- `docs/conformance/2026-07-22-acme-payments/` — the original 0/4 fabrication
  measurement this run calibrates the fix for.
- Rajpurkar et al., *Know What You Don't Know* (ACL 2018) — abstention as a
  first-class metric; the precision/recall trade-off measured here is the
  answerable-vs-unanswerable frontier that paper formalises.
