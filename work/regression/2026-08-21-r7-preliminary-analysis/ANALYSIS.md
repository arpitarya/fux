# ANALYSIS — 2026-08-21, R7 closed without a pre-registered measurement

## The diagnosis

**R7 was closed on Arpit's explicit call**, not adjudicated by a run: the
preliminary evidence (`report.md`) put the odds of a formal FAIL at roughly
70–80 %, and running the real pre-registered bench (~1–2 hours: pre-
registration, a fresh 100k-doc `fux-lab` environment, 30 re-ingest cycles) was
judged not worth spending against those odds. This file records *why* the
odds were judged that way, so the call is auditable even though no VERDICT.md
exists to cite.

**The number, and what it actually measures.** Extrapolating this repo's own
committed-index density (2.429× real git-pack compression, measured, not
assumed) linearly to 100 000 documents lands at **≈ 470 MB — about 1.97× over
the 250 MB budget.** That is real signal, not a guess.

**But it measures the wrong artifact, and that matters for what happens
next.** The 250 MB threshold was sized against `ADR-POSTINGS`'s designed
encoding (BIC postings, 4-bit impacts, MPH dictionary, front-coding) —
`docs/adr/0013_postings.md`, status **⏳ proposed, not built**. What actually
sits in `.fux/index/` today is plain JSON: a term hash is stored as a
**16-character hex string** (the ASCII rendering of an 8-byte binary hash) as
a dict key, inside standard JSON's quote/colon/comma/bracket overhead. That
alone is close to a 2× blow-up over a raw 8-byte binary key before any
docid-delta or impact-quantization saving is even considered — which is
roughly the size of the shortfall this analysis measured.

**This is the distinction that keeps R7 from reading as P1's pruning
failure.** P1 (2026-08-09) found pruning **fundamentally** could not preserve
recall — no encoding choice fixes a *lossy* selector missing relevant
documents. R7's preliminary shortfall, by contrast, tracks almost exactly
with a **known, closeable representation cost** (hex-string JSON keys instead
of packed binary) that the project's own design already planned to fix and
simply has not built yet. Closing R7 as "the wire format is dead" — the
consequence PRIORITY.md's P3 row states for a *measured* FAIL — would be an
overclaim this analysis does not support. **R7 is closed unmeasured, not
FAILED.**

## Specific changes this points to

1. **Do not treat this as triggering PRIORITY.md P3's "wire format is dead"
   consequence.** That consequence was written for a formal measurement
   against the real intended encoding; this was neither. `work/OPEN-WORK.md`
   and `work/PRIORITY.md` are updated to say "closed unmeasured, real
   shortfall found, root cause identified" — not FAIL.
   Repro: `git log --oneline -- work/OPEN-WORK.md work/PRIORITY.md` after this
   change.
2. **Building `ADR-POSTINGS`'s encoding is now better-motivated, not
   optional-someday.** The ~2× gap this analysis found is roughly the size a
   binary key (8 B) vs. hex-string key (16 B) swap alone would close, before
   BIC delta-coding or 4-bit impact quantization are even applied — i.e. the
   proposed design plausibly clears the gap by a comfortable margin once
   built, which is a materially different risk picture than "the architecture
   needs a redesign." Filed as the natural next step, not started here.
   Repro: none yet — this is a recommendation, not a measured claim about the
   unbuilt encoder.
3. **R7 stays formally unmeasured until the compact encoding exists.**
   A real pre-registered run against plain JSON would answer a question
   nobody is asking ("is the placeholder format small enough?" — it was never
   meant to be the shipped format). The honest gate is: build `ADR-POSTINGS`,
   *then* pre-register and measure R7 for real.
   Repro: `work/regression/2026-08-21-r7-preliminary-analysis/evidence/`
   reproduces every number in this file; there is no repro command for a
   measurement that has not happened.

## What is left unresolved, stated as unresolved

- **Corpus representativeness.** Both measurements ran against this repo's
  own 345-document index (real prose/code, not R7's synthetic corpus type).
  A different corpus (vocabulary richness, average length, cross-document
  term overlap) could shift the raw bytes/doc and the achievable compression
  ratio in either direction. The gap found (~2×) is large enough that this
  alone is unlikely to flip the conclusion, but it was not tested and is not
  claimed to have been.
- **Whether BIC/MPH actually closes the gap, once built.** §"Specific
  changes" above states this is *plausible*, not measured. That is exactly
  what a real, pre-registered R7 run — after the encoder exists — would
  settle.
