---
type: Handoff
name: W-260
description: "Two W-256 measurements came back in the shape their frozen rules send to Arpit: §2's doc_coverage replay INCONCLUSIVE (the one candidate floor is not distinguishable from chance), and §8's ingest split a split result (an unchanged delta costs 10.4 s at rung-10000, but redact, not walk+parse, carries it). One line each; nothing waits on either."
item: W-260
filed: 2026-10-04
ball: arpit
---

# W-260 — two W-256 results that are Arpit's to rule

**Model:** none until he rules; the follow-up each answer licenses is named
below. **Records it would update:** [SR-CONFIDENCE](../../records/0141_confidence.md)
d12 (line 1), [SR-MAINTENANCE](../../records/0129_hooks.md) 1a-3 and B-002 (line 2).

Both came from W-256 (closed
2026-10-04), each under a pre-registration frozen alone before any number. Each
frozen rule says this shape of result **goes to Arpit, not to the runner**
(SR-RS d10b), so neither is decided here.

## 1 · `doc_coverage_floor` — INCONCLUSIVE ([run](../regression/2026-10-04-doc-coverage-replay/VERDICT.md))

- rung-01000, 374 stored rows, labels from the retired (open) sets; 36
  unanswerable, of which **21 reach the clause** (the 20-row headroom bar
  cleared by one); AUC 0.60.
- Only floor **0.80** meets the point criteria — catches 12 of 21 (57 %),
  demotes 61 correct answers against a rate-matched coin's 64.1 — but
  **p = 0.35** against the frozen 0.00625, and it fails set-1 and set-3.
- **Today:** `doc_coverage_floor` stays `0.0` (SR-CONFIDENCE d12's *off*);
  the record carries a pointer to the run and nothing else.
- **His options:** (a) *off stands* — record the run as the measured reason,
  close; (b) *re-measure on more unanswerables* — a set with ≥ 60 reachable
  ones (the next generation, or W-257's rung) before anything moves; (c)
  something else. **Recommended (a)**: 21 reachable rows cannot separate a
  0.57 catch rate from chance, and (b) waits on data that does not exist yet.

## 2 · The delta ingest — a split result ([run](../regression/2026-10-04-ingest-split/VERDICT.md))

- rung-10000, unchanged, 3 interleaved repeats, identical root sha: a delta
  costs a median **10.39 s** with zero documents re-extracted; full is 15.11 s
  (**1.45×**, not the 23× SR-INGEST used to cite — rewritten 2026-10-04).
- Walk + parse are only **24–30 %** of it; **`redact` carries ~57 % (5.9–6.0 s)**.
  W-239 measured `redact` at **0.97 s** on the same rung, so this copy's
  6 s is unexplained — the run's ANALYSIS guesses (post hoc, untested) at the
  `pii.toml` that `doctor --fix` wrote into the copy.
- **Today:** B-002 neither closes nor promotes; SR-MAINTENANCE 1a-3 is
  untouched.
- **His options:** (a) *explain `redact` first* — an agent item that finds why
  6 s vs 0.97 s (a diagnosis, Opus), then re-applies the frozen rule to a
  corrected number; (b) a redaction cache keyed on content sha (a build); (c)
  accept ~10 s as the delta floor at the design point and close B-002 as is.
  **Recommended (a)**: the number that decides is not yet understood, and a
  6× gap against W-239 on the same rung is more likely a setup difference
  than an engine fact.
