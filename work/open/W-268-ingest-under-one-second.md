---
type: Handoff
name: W-268
description: "Arpit's ask (2026-10-10): `fux ingest` of 10 000 documents in under one second, any language. Research done in Cowork the same night; the proposal is work/proposals/ingest-under-one-second.md. Arpit picks a shape — (a) incremental Python first, then a Rust core (recommended), (b) Rust now, (c) incremental only — and the chosen steps are filed as build items."
item: W-268
filed: 2026-10-10
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-26
updated_by: "Cowork (Opus 5.5)"
ball: cowork
---

# W-268 — ingest under one second

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Find where the 4.9 seconds go and what could remove them | a proposal and a side-by-side comparison | ✅ 2026-10-10 |
| 2 | Arpit picks the order — Python incremental first, then Rust (recommended), Rust now, or incremental only | the build order | ✅ ruled 2026-10-25 — **S1**: incremental Python first, then the Rust core |
| 3 | Arpit picks what happens on a machine with no pre-built Rust package — fall back to Python (recommended) or fail | no consumer ever installs Rust | ✅ ruled 2026-10-25 — **P1**: the Python engine is the fallback and the reference |
| 4 | Measure start-up, the runtime build and file reading on the Mac | the three unknowns, measured before any code | ⏳ |
| 5 | File the chosen build steps as their own items | work that can start | ⏸ replaced — Arpit's 2026-10-26 direction (Rust only, Python's ingest replaced) moved the build plan to [W-305](W-305-rust-ingest-core.md); this item waits on its rulings |

**⚠ 2026-10-26 — build plan superseded; ruled the same day (W-305): F1 → straight to Rust, F3 = P1 confirmed.** Arpit (Cowork): *"Python will be replaced by Rust. The whole ingest part … would be only in Rust."* That reverses F1 = S1 and F3 = P1 below. The new design and its forks R1–R8 are [W-305](W-305-rust-ingest-core.md) / [`rust-ingest-core.md`](../proposals/rust-ingest-core.md). This item keeps the goal and the clock (G1–G3); step 4's measurement becomes W-305's step 0.

**Arpit, 2026-10-10 (Cowork), closing W-267:** *"No boundaries, no limitations.
If programming language is a boundary, find another programming language in
which it can be done in a faster way. But do some research. I would love to
bring it under one second."*

**Arpit, 2026-10-25 (Cowork docket):** *"S1 · Incremental, then Rust (Recommended)"*
and *"P1 · Python fallback (Recommended)"* — F1 = S1, F3 = P1; F2 = Rust + PyO3 with
abi3 wheels stands from 2026-10-10. Next (Cowork): file the chosen steps as W-items —
step 0 first (Sonnet, measure on the Mac), each with its bar named before it runs —
mark the proposal `graduated`, archive this item (DoD 3).

**Status 2026-10-10: research DONE — 🔴 Arpit picks a shape.** The proposal is
[`ingest-under-one-second.md`](../proposals/ingest-under-one-second.md). In one
paragraph: at no change, all 4.90 s is spent re-doing work for documents that
did not change, and committed records do not depend on corpus-wide df, so an
**incremental ingest in Python (shape A)** can reach the no-change and
one-file cases; a **full** ingest under one second needs **native code (shape
B, Rust behind PyO3)**, parallel by shard and deterministic. Step 0 measures
three unknowns on the Mac first: start-up + import, the accelerator build, and
the per-file read cost.

**Compare doc (2026-10-10):** [`ingest-under-one-second.compare.md`](../compare/ingest-under-one-second.compare.md). **Arpit's direction, 2026-10-10:** *"We can build it in Rust. The only catch here is I don't want consumer to install Rust."* — so F2 is Rust + PyO3 with pre-compiled abi3 wheels; no consumer installs a toolchain.

**The questions for Arpit:** **F1** the order — S1 incremental Python first, then the Rust core (**recommended**) · S2 Rust now · S3 incremental only. **F3** a machine with no wheel — P1 the Python engine as fallback and reference (**recommended**) · P2 wheels only, install fails · P3 an sdist (needs Rust there — excluded by his condition).

**Model:** **Cowork** (research, rule 37a). The build items it files name their
own models.

**Records it will update:** none itself (research). The build steps will name
SR-INGEST, SR-MAINTENANCE, SR-LAW-2 (a crate set, if B), SR-LAW-4 (the parallel
determinism test, if B) and SR-WORK-RELEASE (platform wheels, if B).

## Definition of done

1. The proposal filed with its sources — **done 2026-10-10**.
2. 🔴 Arpit picks F1 and F3 on the compare doc (F2 = Rust, his direction 2026-10-10).
3. The chosen steps filed as W-items (step 0 first, Sonnet), each with its bar
   named before it runs; the proposal marked `graduated`; this item archived.
