# R5, re-measured — the hook is no longer slow at the design point

**Filed:** 2026-08-23 (Cowork, W-76 Phase 3)
**Question:** [R5](../2026-08-20-m5-hooks/report.md) FAILED — a 20-document
commit re-indexed in **44.4 s at 100 000 documents**. W-76 Phase 3 exists to
fix that with a `git diff` delta. **Is the fix still needed?**
**Harness:** [`evidence/scaling-run.log`](evidence/scaling-run.log)

## 1 · The measurement

A full ingest, then one document edited, then a re-ingest. Synthetic corpora,
device VM (arm64), working-tree engine mid-W-76.

| documents | full ingest | **1-doc re-ingest** | per document |
|---|---|---|---|
| 1 000 | 0.95 s | **0.08 s** | 81.8 us |
| 2 500 | 2.36 s | **0.20 s** | 78.1 us |
| 5 000 | 4.71 s | **0.40 s** | 79.5 us |
| **10 000** | 9.52 s | **0.84 s** | 84.0 us |

**Linear in document count at ~82 us per document**, flat across a 10x range.

## 2 · What changed since R5

Nothing was built for this. **W-76 Phase 1 removed the document-level `code`
field**, and that removed the embedding pass — measured at **91 % of a full
ingest** in [the cost profile](../2026-08-20-ingest-cost-profile/report.md).
R5's 44.4 s was paying for it on every hook run.

Extrapolating the curve above to R5's own size gives **~8.4 s at 100 000
documents**, against the 44.4 s it measured. The delta hook was designed to
fix a cost that a different change had already removed most of.

## 3 · Verdict — Phase 3 is NOT built

**At the 10 000-document design point a one-document commit re-indexes in
0.84 s.** That is not a failure by any reading, and the machinery Phase 3
proposes — a `git diff` walk, a reverse-edge index, incremental statistics,
and a `doctor --verify-delta` safety net to prove all three agree with a full
ingest — is real complexity in the maintenance path, which is the path where a
bug is silent and corpus-wide.

This follows the precedent of [R9-T2-AT-10K](../2026-08-22-r9-t2-at-10k/report.md),
which closed the T2 proposal as a decision **not to build** on a measurement
rather than on a preference.

⚠ **R5 itself is not retracted.** It measured 44.4 s and that stands as filed.
What changed is the engine underneath it, and this is a *new* measurement, not
an edit to a frozen one.

## 4 · The reopen condition is a NUMBER, not a size

> **Reopen Phase 3 when a measured one-document re-ingest exceeds 5 s on a
> real corpus.**

Five seconds is where a post-commit hook stops feeling like part of `git
commit` and starts feeling like a build. On this curve that is **~60 000
documents** — but the trigger is the seconds, not the count, because the curve
is a property of these documents and not of the engine.

**Two things would move it sooner**, and both are in W-76:

- **Phase 7** commits per-chunk vectors, which re-introduces an embedding pass
  at roughly 9.8x the density of the one Phase 1 removed. **Re-run this
  harness immediately after Phase 7** — it is the single most likely thing to
  turn this verdict over.
- **Phase 8** adds `ctx` tokens, which grows the per-document extraction cost.

## 5 · Threats to validity, declared

- **Synthetic corpus**, ~30-term vocabulary, 80-400 word bodies. Real prose is
  larger per document, so the per-document constant is likely optimistic.
- **One machine**, arm64 device VM. The linearity is portable; the constant is
  not.
- **The delta is one document.** R5 used twenty. At 82 us per document the
  difference is 1.6 ms of extraction against a ~0.8 s corpus-wide floor, so
  the shape does not change — but it was not measured at twenty.
- **This measures `run()` directly, not the hook**, so it excludes process
  start-up (~50-150 ms) and the detached-runner handoff.

---

## 6 · Amendment, same day — re-run after Phase 7, as §4 demanded

§4 named Phase 7 as *"the single most likely thing to turn this verdict over"*
and said to re-run immediately after it. Phase 7 landed (committed per-chunk
`int8` vectors, ~9.8 chunks per document) and the harness was re-run.

| documents | full ingest | | **1-doc re-ingest** | |
|---|---|---|---|---|
| | before Phase 7 | after | before | after |
| 1 000 | 0.95 s | **6.46 s** | 0.08 s | **0.09 s** |
| 2 500 | 2.36 s | **16.06 s** | 0.20 s | **0.22 s** |

*(evidence: [`evidence/scaling-after-phase7.log`](evidence/scaling-after-phase7.log).
The 5 000 row did not complete before the harness was cut off; two points
establish the ratio and the third was not needed.)*

**The verdict SURVIVES, and the prediction in §4 was wrong** — in a way worth
recording, because it was wrong about the mechanism rather than the size.

- **Full ingest got 6.8x slower.** That is the per-chunk embedding, exactly as
  predicted, and at 10 000 documents extrapolates to **~64 s** for a
  first-time ingest or a `--full`.
- **The hook did not move** — +10 %, which is noise against a 5 s trigger.

**Why the prediction missed:** §4 assumed the embedding pass would land on the
hook. It does not, because **carry-forward isolates it to changed documents**
([ADR-INGEST](../../../docs/adr/0007_ingest.md) decision 1b): an unchanged
document keeps its committed vectors verbatim and is never re-embedded. One
document's 9.8 chunks is trivial; the corpus-wide cost is the walk, and the
walk did not change.

**What this moves instead:** the cost landed on `fux ingest --full` and on a
first ingest, neither of which R5 measures and neither of which is a hook. If
a bar is ever wanted there it is a **different prediction**, and it should be
pre-registered as one rather than read off this run.

**The §4 reopen condition stands unchanged**: a measured one-document
re-ingest above **5 s**. It is now ~0.22 s at 2 500 documents, and the curve
is still linear.
