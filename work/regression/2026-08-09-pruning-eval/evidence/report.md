# M1 — pruning-quality gate (P1): measured results

*Produced by `tools/pruning-eval/run.py`. Definitions are frozen in
`tools/pruning-eval/PRE-REGISTRATION.md`, committed before this ran.*

**Delta is signed**: positive = the pruned arm is *worse* than baseline,
in percentage points of absolute hit@5.

## acme — **gating corpus**

- 877 documents · 885 chunks · 55/55 queries scored
- gold labels: `committed-pairs` — realistic generated repo; committed human-authored pairs
- rare-term slice: 19 queries
- distinct terms per document: median **32** · p90 81 · p99 156 · max 407 · mean 41.95
  *(top-k is a no-op for every document below k — compare against the paper's ~10⁴-word document assumption)*

| arm | hit@5 | Δ hit@5 (pts) | P@10 | MRR | rare hit@5 | Δ rare (pts) |
|---|---|---|---|---|---|---|
| baseline | 0.873 | — | 0.0891 | 0.672 | 0.789 | — |
| k=inf pruned | 0.873 | +0.00 | 0.0891 | 0.672 | 0.789 | +0.00 |
| k=inf diag | 0.873 | +0.00 | 0.0891 | 0.672 | 0.789 | +0.00 |
| k=128 pruned | 0.873 | +0.00 | 0.0891 | 0.672 | 0.789 | +0.00 |
| k=128 diag | 0.873 | +0.00 | 0.0891 | 0.672 | 0.789 | +0.00 |
| k=64 pruned | 0.782 | +9.09 | 0.0818 | 0.642 | 0.737 | +5.26 |
| k=64 diag | 0.818 | +5.45 | 0.0818 | 0.651 | 0.737 | +5.26 |

**Prune coverage** — a corpus few documents are pruned in cannot test P1.

| k | documents pruned | postings kept | vs baseline |
|---|---|---|---|
| inf | 0 / 877 (0.0%) | 37,987 | 1.000× |
| 128 | 22 / 877 (2.5%) | 36,633 | 0.964× |
| 64 | 155 / 877 (17.7%) | 32,290 | 0.850× |

**POST-HOC diagnostic — queries whose gold document was actually
pruned.** Declared post-hoc: this slice is *not* part of the
pre-registered verdict. It exists because an aggregate delta of zero
on a corpus of short documents says nothing about pruning.

| k | queries in slice | baseline hit@5 | pruned hit@5 | Δ (pts) |
|---|---|---|---|---|
| inf | 0 | — | — | **slice empty — nothing measured** |
| 128 | 5 | 1.000 | 1.000 | +0.00 |
| 64 | 42 | 0.952 | 0.857 | +9.52 |

**Failure catalogue (k=inf):** none — no top-5 hit lost.

**Failure catalogue (k=128):** none — no top-5 hit lost.

**Failure catalogue (k=64)** — 5 lost top-5 hit(s):

| query | gold | base→pruned rank | cause | attribution | pruned-out terms |
|---|---|---|---|---|---|
| Are raw card numbers stored, and if so for how long? | `docs/adr/0002-tokenize-pan-at-the-edge.md` | 2→6 | term-pruned | shifted-statistics | are, numbers, so, for |
| What incident caused the move to client-supplied idempote… | `docs/postmortems/2025-09-03-double-charge.md` | 2→60 | term-pruned | missing-postings | the, move, to, keys |
| What is the maximum window over which a failed webhook is… | `docs/api/webhooks.md` | 5→88 | term-pruned | missing-postings | window, over, which, a, webhook, it |
| What technology keeps information after the power goes off? | `docs/notes/durable-storage.md` | 4→6 | score-compressed | shifted-statistics | — |
| Which incident drove the decision to store amounts in int… | `docs/postmortems/2025-04-10-fractional-cent-drift.md` | 4→80 | term-pruned | missing-postings | the, store, units |

## orbit — **gating corpus**

- 892 documents · 900 chunks · 53/53 queries scored
- gold labels: `committed-pairs` — realistic generated repo; committed human-authored pairs
- rare-term slice: 18 queries
- distinct terms per document: median **36** · p90 89 · p99 150 · max 432 · mean 42.63
  *(top-k is a no-op for every document below k — compare against the paper's ~10⁴-word document assumption)*

| arm | hit@5 | Δ hit@5 (pts) | P@10 | MRR | rare hit@5 | Δ rare (pts) |
|---|---|---|---|---|---|---|
| baseline | 0.887 | — | 0.0925 | 0.751 | 0.778 | — |
| k=inf pruned | 0.887 | +0.00 | 0.0925 | 0.751 | 0.778 | +0.00 |
| k=inf diag | 0.887 | +0.00 | 0.0925 | 0.751 | 0.778 | +0.00 |
| k=128 pruned | 0.887 | +0.00 | 0.0925 | 0.751 | 0.778 | +0.00 |
| k=128 diag | 0.887 | +0.00 | 0.0925 | 0.751 | 0.778 | +0.00 |
| k=64 pruned | 0.887 | +0.00 | 0.0906 | 0.757 | 0.778 | +0.00 |
| k=64 diag | 0.868 | +1.89 | 0.0925 | 0.744 | 0.722 | +5.56 |

**Prune coverage** — a corpus few documents are pruned in cannot test P1.

| k | documents pruned | postings kept | vs baseline |
|---|---|---|---|
| inf | 0 / 892 (0.0%) | 39,316 | 1.000× |
| 128 | 14 / 892 (1.6%) | 38,101 | 0.969× |
| 64 | 120 / 892 (13.5%) | 33,813 | 0.860× |

**POST-HOC diagnostic — queries whose gold document was actually
pruned.** Declared post-hoc: this slice is *not* part of the
pre-registered verdict. It exists because an aggregate delta of zero
on a corpus of short documents says nothing about pruning.

| k | queries in slice | baseline hit@5 | pruned hit@5 | Δ (pts) |
|---|---|---|---|---|
| inf | 0 | — | — | **slice empty — nothing measured** |
| 128 | 2 | 1.000 | 1.000 | +0.00 |
| 64 | 37 | 0.946 | 0.946 | +0.00 |

**Failure catalogue (k=inf):** none — no top-5 hit lost.

**Failure catalogue (k=128):** none — no top-5 hit lost.

**Failure catalogue (k=64):** none — no top-5 hit lost.

## synth — **gating corpus**

- 100,000 documents · 116,756 chunks · 200/200 queries scored
- gold labels: `baseline-top1` — 100000 generated documents; no human relevance judgments — gold is the baseline arm's top-1 (fidelity)
- rare-term slice: 67 queries
- distinct terms per document: median **46** · p90 62 · p99 67 · max 72 · mean 47.84
  *(top-k is a no-op for every document below k — compare against the paper's ~10⁴-word document assumption)*

| arm | hit@5 | Δ hit@5 (pts) | P@10 | MRR | rare hit@5 | Δ rare (pts) |
|---|---|---|---|---|---|---|
| baseline | 1.000 | — | 0.1000 | 1.000 | 1.000 | — |
| k=inf pruned | 1.000 | +0.00 | 0.1000 | 1.000 | 1.000 | +0.00 |
| k=inf diag | 1.000 | +0.00 | 0.1000 | 1.000 | 1.000 | +0.00 |
| k=128 pruned | 1.000 | +0.00 | 0.1000 | 1.000 | 1.000 | +0.00 |
| k=128 diag | 1.000 | +0.00 | 0.1000 | 1.000 | 1.000 | +0.00 |
| k=64 pruned | 0.980 | +2.00 | 0.0985 | 0.921 | 1.000 | +0.00 |
| k=64 diag | 0.980 | +2.00 | 0.0985 | 0.928 | 1.000 | +0.00 |

**Prune coverage** — a corpus few documents are pruned in cannot test P1.

| k | documents pruned | postings kept | vs baseline |
|---|---|---|---|
| inf | 0 / 100,000 (0.0%) | 5,131,715 | 1.000× |
| 128 | 0 / 100,000 (0.0%) | 5,131,715 | 1.000× |
| 64 | 4,554 / 100,000 (4.6%) | 5,113,822 | 0.997× |

**POST-HOC diagnostic — queries whose gold document was actually
pruned.** Declared post-hoc: this slice is *not* part of the
pre-registered verdict. It exists because an aggregate delta of zero
on a corpus of short documents says nothing about pruning.

| k | queries in slice | baseline hit@5 | pruned hit@5 | Δ (pts) |
|---|---|---|---|---|
| inf | 0 | — | — | **slice empty — nothing measured** |
| 128 | 0 | — | — | **slice empty — nothing measured** |
| 64 | 27 | 1.000 | 0.889 | +11.11 |

**Failure catalogue (k=inf):** none — no top-5 hit lost.

**Failure catalogue (k=128):** none — no top-5 hit lost.

**Failure catalogue (k=64)** — 4 lost top-5 hit(s):

| query | gold | base→pruned rank | cause | attribution | pruned-out terms |
|---|---|---|---|---|---|
| every worker the shard service | `docs/doc-025420.md` | 1→172 | term-pruned | missing-postings | service |
| idempotency payments shard | `docs/doc-077530.md` | 1→26 | term-pruned | missing-postings | payments |
| retry across every pipeline the | `docs/doc-043026.md` | 1→6 | score-compressed | missing-postings | — |
| service the payments service validates | `docs/doc-060583.md` | 1→— | term-pruned | missing-postings | payments |

**Secondary (easy-by-construction) known-item eval** — sanity only:

| arm | hit@5 | MRR |
|---|---|---|
| baseline | 0.250 | 0.250 |
| k=inf pruned | 0.250 | 0.250 |
| k=128 pruned | 0.250 | 0.250 |
| k=64 pruned | 0.250 | 0.250 |

## Verdict inputs — the pre-registered rule

PASS iff, at **k=128**, the `pruned` arm's hit@5 delta is ≤ 2 pts on
**each** gating corpus and no corpus is worse than 3 pts.

| gating corpus | k=128 Δ hit@5 (pts) | k=64 Δ hit@5 (pts) | ≤2 | ≤3 |
|---|---|---|---|---|
| acme | +0.00 | +9.09 | yes | yes |
| orbit | +0.00 | +0.00 | yes | yes |
| synth | +0.00 | +2.00 | yes | yes |

*The call itself belongs in ADR-0017, reviewed by a human. This table
states the inputs; it does not adjudicate an ambiguous result.*
