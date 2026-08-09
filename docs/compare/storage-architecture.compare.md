---
type: Compare Doc
title: Storage Architecture
description: Index-and-refer vs committed-snapshot substrate vs full-copy store — the fork the whole v0.30 rebuild rests on.
status: accepted
timestamp: 2026-08-09T00:00:00Z
---

# Storage architecture — Comparison

> **Verdict: Index-and-refer.** Git carries only a small deterministic
> index (pruned term stats, codes, edges, ledger); every byte of content
> stays in the system that owns it; answers rank from the index, fetch only
> the cited docs live (ARC-cached), and re-score on fetched bytes.
> **Status:** ✅ accepted — council debate 2026-08-09 (Arpit ratified in
> session) · **Confidence:** high on direction, gated on P1
> **Reopen when:** P1 (pruning quality) fails at k=128; or an enterprise
> design partner rejects any committed index even hashed; or live-fetch
> auth friction measurably kills adoption (DA's attack #3).
>
> **⚠ P1 was measured 2026-08-09 and is INCONCLUSIVE — this verdict now
> stands on an untested premise.** The reopen-trigger has **not** fired:
> P1 did not fail. But it did not pass either — top-128 pruning reached
> 0–2.5 % of documents on the three eval corpora (whose documents hold
> 32–46 distinct terms against the size model's ~2 000), so the run could
> not test the claim. At k=64, the only setting where pruning bit, acme lost
> 9.09 pts. **Annotated, not reopened**; the verdict holds pending the
> long-document re-run (W-13). See
> [ADR-0017](../adr/0017-pruning-eval-gate.md).
>
> **⚠ SIZE AMENDMENT (2026-08-09, [ADR-0018](../adr/0018-pruning-criterion-rerun.md)).**
> The re-run measured P1 properly and it **FAILED**: no pruning criterion came
> within 2 points of the unpruned index at any retention rung (best: −35.9 pts
> at 6 %, −12.7 pts at 30 %). **Index-and-refer is not what failed** — ranking
> from a committed index and fetching content from source systems is untouched.
> What failed is the claim that the index can be made ~16× smaller *by
> discarding postings*. This is therefore an **amendment, not a reopen**:
>
> - the committed index is **0.6–1.5 GB** at 10⁶ documents, not 220–290 MB;
> - **partial clone** and **external-shards-only committing** stop being
>   optional levers and become mandatory;
> - the paper's §5 size model must be re-derived at a retention that holds
>   quality, or at no pruning.
>
> Whether the architecture is still worth building at that footprint is Arpit's
> call, not the measurement's.

## Context

At the 1M-doc design point a full-copy store costs 250–450 GB (extrapolated
from the measured 10.8 KB/doc at 100k, archived ADR-0011) and duplicates
content whose owners (git dirs, Confluence, SharePoint) keep evolving it —
recreating the drift disease Fux exists to cure. The paper
([`../paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md))
formalizes the alternative.

## Options

- **A — Index-and-refer** *(verdict)*: committed index ~220–290 MB @1M;
  content fetched from sources at answer time; freshness is a read-time
  contract (SWR + read repair); per-source `snapshot` opt-out for air-gap/
  audit docs.
- **B — Committed-snapshot substrate** (the withdrawn FuxDB v0.1 paper):
  machine-made snapshots of external sources committed; ~450 MB state +
  packs; strong offline story, weak freshness story, ACL-copy problem in
  full.
- **C — Full-copy store** (v0.26 trajectory): all text in the local db;
  simplest queries; dead at scale (size, clone, second-truth drift).

## Matrix

| criterion (weight) | A refer | B snapshot | C full-copy |
|---|---|---|---|
| committed footprint @1M (H) | **~250 MB** | ~450 MB + packs | n/a (450 GB local) |
| freshness of answers (H) | **automatic** (fetch = current) | verify-then-repair | stale by default |
| second-source-of-truth risk (H) | **none** | real (snapshots drift) | maximal |
| offline / air-gap (M) | git sources full; external degrades | **full** | full |
| ACL containment (H) | leak surface = meta only (→ hashed) | full content copied across ACLs | full copy |
| demo cold-start (M) | 1.5–3 s first ask | instant | instant |
| build cost (M) | adapters + fetch layer | packs + staleness machinery | already sunk |

## Consequences

Sources become the only owners of content; the ledger + fresh-sha citation
becomes the trust mechanism; the network enters an opt-in fenced query path
(the one law exception, default off). Council conditions: hashed meta
default ([meta-privacy](meta-privacy.compare.md)), adapter cap
(git + HTTP + Confluence; [MCP proposal](../proposals/mcp-adapters.md)),
P1 gate before build, v0.26 untouched in `archive/` until dogfood.
DA minority report (preserved): the postings-by-term fix on v0.26 shipped
felt value in a week and was not done first.

## References

Paper §1–§3 and its [1,2,12,13] · federated-search frame (Callan) ·
RFC 5861 · Dynamo read repair · council transcript in WORKLOG 2026-08-09.

## Reopen-trigger

See verdict block. First measurement that can fire it: M1 (P1 numbers).
