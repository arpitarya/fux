# M1-rerun — pruning criterion at matched retention

*Produced by `tools/pruning-eval/run2.py`. Definitions frozen in
`tools/pruning-eval/PRE-REGISTRATION-v2.md`, committed before this ran.*

**Gate metric: recall@20** of the candidate set — the set the
refer plane would fetch and re-score. Everything else is diagnostic.

**Δ is signed**: positive = worse than arm 5 (no pruning), in points.

## rfc

- 8,872 documents · 2000 queries (abstract 703 · heading 1297)
- distinct terms per document: median **967** · p90 1,850 · p99 3,236 · max 28,461
- 9,875,331 document-level postings · budget floor 8 · Rule C δ=3
- 8872 RFCs, manifest-pinned; long technical prose

**Arm 5 (no pruning) — the ceiling:** recall@20 **0.935** · recall@10 0.906 · recall@50 0.962 · MRR 0.767

### 6% retention

| arm | rules | actual ret. | Δ ret (pts) | recall@20 | Δ (pts) | abstract recall@20 | heading recall@20 | docs pruned | lost |
|---|---|---|---|---|---|---|---|---|---|
| 1 KL only | — | 5.90% | -0.10 | 0.661 | +27.45 | 0.627 | 0.679 | 100.0% | 60 |
| 2 impact only | B | 5.90% | -0.10 | 0.435 | +50.00 | 0.489 | 0.406 | 100.0% | 60 |
| 3 A + B | A+B | 5.90% | -0.10 | 0.273 | +66.25 | 0.209 | 0.308 | 100.0% | 60 |
| 4 A + B + C | A+B+C | 6.04% | +0.04 | 0.281 | +65.40 | 0.208 | 0.322 | 100.0% | 60 |

### 15% retention

| arm | rules | actual ret. | Δ ret (pts) | recall@20 | Δ (pts) | abstract recall@20 | heading recall@20 | docs pruned | lost |
|---|---|---|---|---|---|---|---|---|---|
| 1 KL only | — | 14.89% | -0.11 | 0.775 | +16.05 | 0.755 | 0.786 | 100.0% | 60 |
| 2 impact only | B | 14.89% | -0.11 | 0.568 | +36.75 | 0.615 | 0.543 | 100.0% | 60 |
| 3 A + B | A+B | 14.89% | -0.11 | 0.403 | +53.30 | 0.340 | 0.436 | 100.0% | 60 |
| 4 A + B + C | A+B+C | 14.99% | -0.01 | 0.416 | +51.90 | 0.354 | 0.450 | 100.0% | 60 |

### 30% retention

| arm | rules | actual ret. | Δ ret (pts) | recall@20 | Δ (pts) | abstract recall@20 | heading recall@20 | docs pruned | lost |
|---|---|---|---|---|---|---|---|---|---|
| 1 KL only | — | 30.12% | +0.12 | 0.849 | +8.65 | 0.859 | 0.843 | 100.0% | 60 |
| 2 impact only | B | 30.12% | +0.12 | 0.704 | +23.20 | 0.774 | 0.665 | 100.0% | 60 |
| 3 A + B | A+B | 30.12% | +0.12 | 0.554 | +38.15 | 0.521 | 0.572 | 100.0% | 60 |
| 4 A + B + C | A+B+C | 29.99% | -0.01 | 0.561 | +37.45 | 0.531 | 0.577 | 100.0% | 60 |

## Gate readout (pre-registered)

PASS iff, at **6 % retention** on the gating corpus, the best arm is
within **2 pts** of arm 5 on **recall@20**, measured on the
**abstract-derived** slice (heading-derived queries flatter Rule A).

| corpus | rung | best arm | abstract recall@20 | ceiling | Δ (pts) |
|---|---|---|---|---|---|
| rfc | 6% | 1 KL only | 0.627 | 0.986 | +35.85 |
| rfc | 15% | 1 KL only | 0.755 | 0.986 | +23.04 |
| rfc | 30% | 1 KL only | 0.859 | 0.986 | +12.66 |

*The call belongs in ADR-0018, reviewed by a human. This table states
the inputs; it does not adjudicate.*
