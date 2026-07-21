---
type: Handoff Prompt
title: Claude Code prompt — Engine v2 (bundled model + RRF hybrid)
description: Paste-ready prompt executing handoff 0003.
status: implemented
adrs: [../adr/0006-bundled-model.md, ../adr/0007-rrf-hybrid-fusion.md]
blocked_by: 0001-query-cli-v1-handoff.md
timestamp: 2026-07-21T00:00:00Z
---

# Claude Code prompt — Hybrid engine v2

Paste below into Claude Code at the repo root. **Precondition: handoff 0001
implemented and archived; both suites green.** (0002 is independent — either order.)

---

Build **Engine v2** — the bundled ≤10 MB static-embedding model, pure-stdlib
inference, and RRF hybrid retrieval — executing the committed spec exactly.

**Explore first:** read `CLAUDE.md` (binding), then
`docs/handoff/0003-hybrid-engine-v2-handoff.md` (the spec), then
`docs/compare/packaged-model.compare.md` (the no-numpy resolution and the
candidate-only-ranking math — implement exactly that) and the v2/RRF sections +
resolved sub-decisions of `docs/compare/query-engine.compare.md`. Inspect the
implemented `src/fux/index/` and `src/fux/query/` from 0001.

**Plan milestones — eval first, model second, fusion last:**
M1 eval harness (`tests_e2e/eval/`, committed Q→passage pairs, hit@1/hit@5/MRR,
baseline numbers for lexical v1 recorded); M2 distillation pipeline in
`tools/distill/` (dev-only deps; ≤10 MB asserted; reproducible recipe; license
check); M3 stdlib inference (`src/fux/embed/` — bundle loader, tokenizer,
mean-pool, int8 dot products; unit tests against reference vectors exported by the
distill script); M4 ingest-time chunk-vector cache (manifest-invalidated,
deterministic); M5 RRF fusion over BM25F candidates + `--explain` extension +
`--lexical-only`; M6 eval gate — hybrid must beat lexical on hit@5 and MRR, numbers
into ADR; M7 packaging (bundle in wheel, lazy load, wheel-size check) + goldens
updated deliberately.

**Hard rules:** zero runtime deps — the `fux.embed` package imports stdlib only
(add a test asserting it); no numpy, no downloads at runtime; dense scoring runs
over the BM25F candidate pool only (never the full corpus); pinned model artifact
with sha recorded; `--lexical-only` must remain byte-identical to v1 behavior;
determinism across platforms (int8 math only — no float accumulation ordering
surprises: sum in int32, scale once).

**Verify:** both suites + eval gate green; `fux ask` latency on the fixture corpus
remains interactive (<100 ms warm); model-missing path degrades cleanly to lexical;
wheel builds ≤15 MB with the bundle.

**Track as you go:** update `docs/implementation.md` (Phase 3 table) at every
milestone completion; keep "Now working on" current; eval numbers land in both the
tracker notes and the ADR.

**Close out (per CLAUDE.md):** ADRs 0006 + 0007 (with eval numbers and the distill
recipe); archive this pair `status: implemented`; update fux-plan/README/
DOC-REGISTRY/worklog/model-handoff-interview + CLAUDE.md scope line; bump minor.

Show the milestone plan (with the eval-first ordering) before writing code.
