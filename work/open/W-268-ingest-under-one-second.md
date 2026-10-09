---
type: Handoff
name: W-268
description: "Arpit's ask (2026-10-10): `fux ingest` of 10 000 documents in under one second, any language. Research done in Cowork the same night; the proposal is work/proposals/ingest-under-one-second.md. Arpit picks a shape — (a) incremental Python first, then a Rust core (recommended), (b) Rust now, (c) incremental only — and the chosen steps are filed as build items."
item: W-268
filed: 2026-10-10
ball: arpit
---

# W-268 — ingest under one second

**Arpit, 2026-10-10 (Cowork), closing W-267:** *"No boundaries, no limitations.
If programming language is a boundary, find another programming language in
which it can be done in a faster way. But do some research. I would love to
bring it under one second."*

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
