# docs/conformance/ — the test-evidence & analysis home

Every fux-lab conformance run files its **full report + diagnosis + raw evidence**
here, so fixes are made from measured evidence, not memory. Binding: CLAUDE.md
§ "Conformance runs".

## Why this exists

fux-lab is a scratch harness — it commits nothing and is discarded. The durable
record of *what the engine actually did at scale, and what to fix* belongs in the
versioned repo. This directory is that record.

## Structure — one folder per run

```
docs/conformance/
  README.md                         this file (the convention + index)
  <date>-<run>/                     e.g. 2026-07-22-scaling-1k-5k-10k/
    report.md                       the suite's own report(s) / comparison
    <tier>.md                       per-tier reports when a run spans tiers
    ANALYSIS.md                     diagnosis → concrete fux improvements
    evidence/                       raw fux why --json, --debug=trace, doctor
```

## The flow (run → file → fix)

1. Run the suite in `fux-lab/<tier>` (`./setup.sh && ./run.sh`).
2. File the report(s) + an `ANALYSIS.md` + `evidence/` here, in one folder per run.
3. `ANALYSIS.md` names the specific fux changes worth making, with repro commands.
4. Findings that warrant an engine change **graduate** to `docs/proposals/` and,
   when accepted, an ADR — this directory stays the evidence backing them.

Measurements, not narratives. Every number carries its repro command. An
unresolved cause is stated as unresolved.

## Runs

| Run | Version | Scope | Headline |
|---|---|---|---|
| [2026-07-22-scaling-1k-5k-10k](2026-07-22-scaling-1k-5k-10k/ANALYSIS.md) | 0.23.0 | 1k→5k→10k scaling | Hybrid gap closes as lexical collapses; zero-overlap 0/14; latency linear from the start. Two failure mechanisms measured. |
| [2026-07-22-acme-payments](2026-07-22-acme-payments/ANALYSIS.md) | 0.23.0 | ~1k realistic repo (A-vs-B discriminator) | **Settles A vs B → B:** hybrid collapse is a corpus artifact (hit@5 .182→.855, parity with lexical). Three new real findings: staleness 9/12 inversions, zero-overlap dense rescue 0/6, honest-decline 0/4 on well-formed unanswerables. |
| [2026-07-23-min-confidence-calibration](2026-07-23-min-confidence-calibration/ANALYSIS.md) | 0.25.0-dev (editable, phase 6) | acme 55 answerable + 4 unanswerable + gibberish + fixture-21 + synthetic 1k/5k/10k | **No `min_confidence` value clears all 5 gates** — decline-4/4 needs floor ≥0.25, zero-false-decline needs floor ≤0.087, empty interval. Shipped permissive (0.0); follow-up filed (floor an absolute signal, not the pool-relative sentence score). |
| [2026-07-23-supersession-recovery](2026-07-23-supersession-recovery/ANALYSIS.md) | 0.25.0-dev (editable, phase 6) | acme's 12 stale-vs-current pairs, DoD 8 before/after | **Partial recovery, measured exactly:** 5/12 pairs carry a machine-readable marker, only 3/9 original `find`-inversions do; at the `answer` level 1 fully corrected, 1 de-cited (retrieval-limited), 1 already correct, 6 unmarked/unreachable. `find` ranking confirmed byte-identical (annotation only). |
