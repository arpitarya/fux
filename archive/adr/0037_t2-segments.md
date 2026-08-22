---
type: Retired ADR
name: ADR-T2-SEGMENTS
title: "ADR-T2-SEGMENTS (0037) — RETIRED: moved to work/proposals/t2-segments.md"
description: "This record was removed from docs/adr/ on 2026-08-22 by Arpit's instruction. Its content is not duplicated here — it lives at work/proposals/t2-segments.md. Number 0037 is retired and never reused."
status: superseded
timestamp: 2026-08-22T00:00:00Z
---

# ADR-T2-SEGMENTS (0037) — retired, not superseded by another record

**This is a tombstone, deliberately not a copy.** Keeping the full text here as
well as in the proposal would create two versions of one document, and they
would drift.

- **What it was:** the record that **T2 is not built**, decided by measurement
  ([R9](../../work/regression/2026-08-22-r9-t2-at-10k/VERDICT.md), 12.46 ms
  against a 150 ms bar), `accepted` on 2026-08-22.
- **What happened:** Arpit ruled the same day that it should not be a record —
  *"move the document to proposals and remove the ADR completely."*
- **Where the content is now:**
  [`work/proposals/t2-segments.md`](../../work/proposals/t2-segments.md).
- **Number `0037` is retired and never reused.** A future ADR takes the next
  free number and does not reclaim this one.
- **Nothing measured changed, and no code moved.** T2 was never built; there is
  no `tpack`, no BIC codec and no `tier` knob in `src/`.

⚠ **Two frozen files still cite this record by its old name and path** —
`tools/t2-eval/PRE-REGISTRATION.md` and R9's `VERDICT.md`. **Neither may be
edited**, so those references are stale by design. That is the cost of moving a
decision after its instrument and its verdict were frozen around it, and it is
recorded rather than repaired.
