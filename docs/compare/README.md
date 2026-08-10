# Compare docs — every fork's debate, verdict first

One doc per genuine fork in the v0.30 design. **The verdict block sits at the
top of every doc** — status, the call, confidence, and the reopen-trigger —
so a reader (human or agent) gets the decision without the debate, and the
debate without archaeology. v0.26-era compare docs are archived at
[`archive/v0.26-docs/compare/`](../../archive/v0.26-docs/compare/).

| doc | fork | verdict | status |
|-----|------|---------|--------|
| [index-format](index-format.compare.md) | tiered JSONL vs MST+BIC wire vs pure scan vs SQLite | **tiered JSONL (T0/T1/T2), git as the Merkle tree** — benches B1–B6 | ✅ accepted (2026-08-09) |
| [storage-architecture](storage-architecture.compare.md) | index-and-refer vs snapshot substrate vs full-copy | **index-and-refer** (size amended by ADR-0003: full postings) | ✅ accepted (council 2026-08-09) |
| [wire-format](wire-format.compare.md) | one format vs wire/runtime split; codec choice | split; BIC wire — **superseded for the committed plane by index-format; survives inside tier T2** | ⚠ superseded |
| [keyspace-unification](keyspace-unification.compare.md) | six planes vs one MST keyspace vs wavelet self-index | one MST keyspace — **superseded: git itself now provides the Merkle tree (index-format)** | ⚠ superseded |
| [meta-privacy](meta-privacy.compare.md) | plain vs hashed-default vs hashed-only meta | **hashed-by-default for external sources** | ✅ accepted (council) |
| [cache-policy](cache-policy.compare.md) | LRU vs ARC | **ARC** | ✅ accepted |
| [ingest-mode-naming](ingest-mode-naming.compare.md) | "extracted" vs "enriched" vs "advanced" for the AI tier | **enriched** (proposed) | ⏳ awaiting Arpit |
| [pruning-criterion](pruning-criterion.compare.md) | KL vs impact vs term-centric vs combined; the gate metric | prediction **falsified** by the re-run (ADR-0003); pruning removed from the design — full postings | ❌ closed (M8 experiment only) |

Convention: `> **Verdict:**` blockquote first, then Context → Options →
Matrix → Consequences → References → Reopen-trigger. Docs here are compact;
if one outgrows a screen, split it into a *For humans* summary section and a
*For AI agents* decision-data section (per OPEN-WORK convention).
