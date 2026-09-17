---
type: Handoff
name: W-166
description: "Three ways a carried-forward record silently keeps stale bytes, each with its remedy already named: a decoder change does not invalidate carried extraction (no decoder digest), a new extraction rule does not reach an unchanged document (no rule digest), and a `url:` record is never re-redacted until re-fetched although its bytes sit in `.fux/acquired/`. Promoted from BACKLOG B-009, B-010, B-011."
item: W-166
filed: 2026-09-14
ball: agent
---

# W-166 — carry-forward invalidation: two digests and one re-extraction

**Model: Opus for the reuse-key design (a digest that is too coarse re-ingests
every corpus on every release; too fine misses the case), Sonnet for the
build.**

**Promoted 2026-09-14 from [`BACKLOG.md`](../BACKLOG.md)** rows B-009, B-010,
B-011 (deleted there). Ratified-not-built.

## Context

Ingest reuses a document's extracted record when its source bytes are
unchanged. The reuse key already carries the PII ruleset digest and the
`[index]` digest ([SR-PII](../../records/0148_pii.md), [SR-INGEST](../../records/0106_ingest.md)
decision 15a) — the precedent. Two inputs that also change what extraction
produces are **not** in the key, and one class of record has its bytes on
disk and is never re-processed:

- **decoders** — a fix to a built-in or `.fux/decoders/` decoder reaches an
  unchanged document only on `--full` ([SR-DECODE](../../records/0139_decode.md)
  decision 11a: *"There is no decoder digest. Stated, not fixed."*).
- **extraction rules** — same for a change in `extract.py`
  ([SR-INGEST](../../records/0106_ingest.md) Consequences).
- **`url:` re-redaction** — a PII ruleset change re-redacts file records
  from disk but no `url:` record until its bytes are fetched again, `--full`
  included, although `.fux/acquired/` holds them ([SR-PII](../../records/0148_pii.md)
  the 🔴 before decision 18: *"the data needed is present and unused"*).

## Definition of done

1. **A decoder digest** in the reuse key: per *binding* — the built-in
   decoder's version constant, or the sha of the consumer's `.fux/decoders/`
   file — so only documents that used the changed decoder re-extract.
2. **An extraction-rule digest** — one constant in `extract.py`, bumped by
   hand when a rule changes, with a test that fails if `extract.py` changed
   and the constant did not (the `check-version-parity.py` pattern).
3. **`url:` records re-extract from `.fux/acquired/`** when the PII digest
   (or either digest above) moves and the blob is present; when it is not,
   the record is marked `stale-redaction` and `doctor` names it.
4. Determinism: all three are functions of committed bytes or source-tree
   content, never of time. Same sources → same key → same index (L3).
5. A release note: the first ingest after this lands re-extracts every
   document once (the B-203 pattern — accepted, stated).
6. Records: SR-DECODE 11a, SR-INGEST Consequences + 15a, SR-PII the 🔴 — each
   from *stated* to *fixed*; SR-INDEX-LIFECYCLE if the key's shape is stated
   there.

## Out of scope

- A consumer-side refresh path for the templates themselves (B-013, B-014) —
  a different problem (the *file* is stale, not the *record*).
- Term-hash collision detection on deltas (B-083).

## Where the work is

`src/fux/ingest/` (the reuse key and the carry-forward path),
[`src/fux/decode/`](../../src/fux/decode/), `src/fux/ingest/extract.py`,
the acquired plane ([SR-ACQUIRED](../../records/0145_acquired-plane.md)).

## Records this will touch

SR-DECODE · SR-INGEST · SR-PII · SR-INDEX-LIFECYCLE · SR-ACQUIRED.

## Verification, and the keep/remove call (gap check 2026-09-14)

Order: **design the key (Opus) → implement → test → measure the cost → call.**

- **Tests:** (a) a decoder edit re-extracts exactly the documents bound to
  it and no others; (b) an `extract.py` edit without the constant bump fails
  the parity test; (c) a PII ruleset change re-redacts a `url:` record from
  `.fux/acquired/` without a fetch, and marks one whose blob is absent;
  (d) determinism — two clean-clone ingests of the same tree give the same
  root hash (L3).
- **Measured, not assumed:** the one-off full re-extraction on the first
  ingest after landing, timed on this repo and on the largest golden rung and
  filed under `work/regression/` as a surface capture (exempt from
  blind/informed). Then a **no-op delta ingest** on an unchanged tree must
  re-extract **zero** documents — that is the keep test.
- **Keep** if the no-op delta re-extracts nothing and a decoder change
  touches only its bindings. **Remove or narrow** — the digest is too coarse
  — if a routine engine release re-extracts every corpus: then the decoder
  digest is scoped per built-in decoder version, not per package version, and
  the item is re-measured before it ships.
- **Release note** for the one-off; **no ranking measurement** — nothing
  here changes what an unchanged corpus scores.
