# Fux conformance run — env `acme` — 2026-07-22

Version under test: **fux 0.23.0** (installed from PyPI into this environment's own venv).

Corpus: `/home/claude/lab/acme/corpus` · 929 documents · **15 failure(s)** across 57 checks.

## Results

| Area | Check | Status | Detail |
|---|---|---|---|
| environment | fux under test | ✅ PASS | fux 0.23.0 · binary `/home/claude/lab/acme/.venv/bin/fux` |
| ingest | cold ingest | ✅ PASS | exit 0 · 1.0s |
| determinism | double-ingest byte-identical | ✅ PASS | state 8c4b70da839b0fc2→8c4b70da839b0fc2 · lock b703e9ef4b642241→b703e9ef4b642241 |
| determinism | --check clean after ingest | ✅ PASS | cache is fresh (877 sources tracked) |
| determinism | DRIFT: modified source | ✅ PASS | strict exit 2 (want 2) · DRIFT  docs/adr/0001-acquirer-northwind.md  (sha mismatch — re-ingest) |
| determinism | DRIFT: new/untracked source | ✅ PASS | strict exit 2 (want 2) · DRIFT  docs/indexing/_regress-newfile.md  (new — not in fux.lock) |
| determinism | DRIFT: deleted source | ✅ PASS | strict exit 2 (want 2) · DRIFT  docs/adr/0001-acquirer-northwind.md  (missing — source deleted; cache orphan) |
| determinism | drift reasons distinguishable | ✅ PASS | three distinct reasons |
| surface | `fux ask` runs | ✅ PASS | exit 0 · cold 0.354s · warm 0.351s |
| surface | `fux find` runs | ✅ PASS | exit 0 · cold 0.346s · warm 0.352s |
| surface | `fux answer` runs | ✅ PASS | exit 0 · cold 0.480s · warm 0.465s |
| surface | `fux explain` runs | ✅ PASS | exit 0 · cold 0.334s · warm 0.326s |
| surface | `fux graph` runs | ✅ PASS | exit 0 · cold 0.311s · warm 0.322s |
| surface | `fux cat` runs | ✅ PASS | exit 0 · cold 0.095s · warm 0.093s |
| determinism | fresh clone answers from committed state | ✅ PASS | state plane answered (top docs/adr/0002-tokenize-pan-at-the-edge.md) |
| determinism | fresh clone top-1 parity | ✅ PASS | index top docs/adr/0002-tokenize-pan-at-the-edge.md · state top docs/adr/0002-tokenize-pan-at-the-edge.md |
| determinism | fresh clone byte-identical (index vs state) | ℹ️ INFO | lower-rank scores differ — state plane is quantized (codes/sigs); top-1 stable, tail re-ranked |
| determinism | --lexical-only stable across runs | ✅ PASS | identical |
| correctness | citations resolve to real files | ✅ PASS | 5 sources checked |
| honest-decline | find declines on unanswerable | ✅ PASS | exit 0 · 0 results (want 0) |
| honest-decline | ask declines on unanswerable | ✅ PASS | exit 0 · 0 results (want 0) |
| honest-decline | answer does not fabricate | ✅ PASS | exit 0 · answer=null · 0 sources (want 0/none) |
| size | .fux/state | ℹ️ INFO | 0.24 MB · 256 B/doc |
| size | .fux/index | ℹ️ INFO | 1.83 MB · 1970 B/doc |
| size | .fux/cache | ℹ️ INFO | 0.81 MB · 877 B/doc |
| size | fux.lock | ℹ️ INFO | 0.20 MB · 220 B/doc |
| quality | eval (lexical-only, all n=55) | ℹ️ INFO | hit@1 0.527 · hit@5 0.873 · MRR 0.669 |
| quality | eval (lexical-only, cross-doc n=6) | ℹ️ INFO | hit@1 0.5 · hit@5 1.0 · MRR 0.708 |
| quality | eval (lexical-only, factual n=12) | ℹ️ INFO | hit@1 0.417 · hit@5 1.0 · MRR 0.649 |
| quality | eval (lexical-only, how-to n=8) | ℹ️ INFO | hit@1 1.0 · hit@5 1.0 · MRR 1.0 |
| quality | eval (lexical-only, stale-vs-current n=12) | ℹ️ INFO | hit@1 0.25 · hit@5 0.833 · MRR 0.5 |
| quality | eval (lexical-only, why n=11) | ℹ️ INFO | hit@1 0.909 · hit@5 1.0 · MRR 0.955 |
| quality | eval (lexical-only, zero-overlap n=6) | ℹ️ INFO | hit@1 0.0 · hit@5 0.167 · MRR 0.042 |
| quality | eval (hybrid, all n=55) | ℹ️ INFO | hit@1 0.491 · hit@5 0.855 · MRR 0.659 |
| quality | eval (hybrid, cross-doc n=6) | ℹ️ INFO | hit@1 0.5 · hit@5 0.833 · MRR 0.667 |
| quality | eval (hybrid, factual n=12) | ℹ️ INFO | hit@1 0.333 · hit@5 1.0 · MRR 0.628 |
| quality | eval (hybrid, how-to n=8) | ℹ️ INFO | hit@1 0.875 · hit@5 1.0 · MRR 0.938 |
| quality | eval (hybrid, stale-vs-current n=12) | ℹ️ INFO | hit@1 0.167 · hit@5 0.833 · MRR 0.475 |
| quality | eval (hybrid, why n=11) | ℹ️ INFO | hit@1 0.909 · hit@5 1.0 · MRR 0.955 |
| quality | eval (hybrid, zero-overlap n=6) | ℹ️ INFO | hit@1 0.167 · hit@5 0.167 · MRR 0.167 |
| quality | zero-overlap dense rescue (hybrid) | ❌ FAIL | rescued 1/6 into top-5 (hit@5 0.167, MRR 0.167) |
| quality | staleness: current-doc reachable (n=12, hybrid, top-5) | ℹ️ INFO | current doc in top-5 for 10/12 pairs |
| staleness | inversion — What is the card settlement window today? | ❌ FAIL | superseded `docs/adr/0006-settlement-window-t-plus-three.md` (rank 1) outranked current `docs/adr/0018-settlement-window-t-plus-two.md` (rank 2) |
| staleness | inversion — How long is an idempotency key valid? | ❌ FAIL | superseded `docs/guides/legacy-idempotency-notes.md` (rank 1) outranked current `docs/guides/idempotency-keys.md` (rank 2) |
| staleness | inversion — What is the current API rate limit per key? | ❌ FAIL | superseded `docs/api/legacy-rate-limits.md` (rank 1) outranked current `docs/api/rate-limits.md` (rank 2) |
| staleness | inversion — How does the API authenticate requests today? | ❌ FAIL | superseded `docs/guides/legacy-api-keys.md` (rank 1) outranked current `docs/guides/authentication.md` (rank 5) |
| staleness | inversion — How many days after a charge can a refund still be i | ❌ FAIL | superseded `docs/guides/legacy-refund-policy.md` (rank 1) outranked current `docs/api/refunds.md` (rank 2) |
| staleness | inversion — Are raw card numbers stored, and if so for how long? | ❌ FAIL | superseded `docs/guides/legacy-card-storage.md` (rank 1) outranked current `docs/adr/0002-tokenize-pan-at-the-edge.md` (rank 6) |
| staleness | inversion — How many days do we have to respond to a chargeback  | ❌ FAIL | superseded `docs/runbooks/legacy-dispute-7day.md` (rank 1) outranked current `docs/runbooks/chargeback-dispute-response.md` (rank 2) |
| staleness | inversion — For how long does Acme retry a failed webhook before | ❌ FAIL | superseded `docs/api/legacy-webhooks-v1.md` (rank 1) outranked current `docs/api/webhooks.md` (rank 2) |
| staleness | inversion — Does reconciliation run in real time or as a daily b | ❌ FAIL | superseded `docs/adr/0010-realtime-reconciliation.md` (rank 1) outranked current `docs/adr/0016-reconcile-against-psp-feed-daily.md` (rank 2) |
| honest-decline | typed unanswerable questions decline (n=4) | ❌ FAIL | 0/4 declined cleanly via `answer`; `find` returned candidates for 4/4 |
| honest-decline | fabrication — What is Acme's policy on cryptocurrency and stableco | ❌ FAIL | answer="A rounding bug in the proration engine paid out fractional  · 5 sources (want a clean decline) |
| honest-decline | fabrication — How do I configure the Kubernetes horizontal pod aut | ❌ FAIL | answer='Retries frequently cross process and even device boundaries · 1 sources (want a clean decline) |
| honest-decline | fabrication — What is the uptime SLA percentage for Acme's GraphQL | ❌ FAIL | answer="acme-payments is five services around an append-only ledger · 5 sources (want a clean decline) |
| honest-decline | fabrication — Which third-party vendor supplies our SMS one-time-p | ❌ FAIL | answer='Two designs were on the table — the server hashes the reque · 4 sources (want a clean decline) |
| baseline | comparison | ℹ️ INFO | no baseline yet — this run establishes one (--accept-baseline) |

## Metrics (baseline candidates)

```json
{
  "eval_hybrid": {
    "MRR": 0.659,
    "hit@1": 0.491,
    "hit@5": 0.855
  },
  "eval_hybrid_cross-doc": {
    "MRR": 0.667,
    "hit@1": 0.5,
    "hit@5": 0.833
  },
  "eval_hybrid_factual": {
    "MRR": 0.628,
    "hit@1": 0.333,
    "hit@5": 1.0
  },
  "eval_hybrid_how-to": {
    "MRR": 0.938,
    "hit@1": 0.875,
    "hit@5": 1.0
  },
  "eval_hybrid_stale-vs-current": {
    "MRR": 0.475,
    "hit@1": 0.167,
    "hit@5": 0.833
  },
  "eval_hybrid_why": {
    "MRR": 0.955,
    "hit@1": 0.909,
    "hit@5": 1.0
  },
  "eval_hybrid_zero-overlap": {
    "MRR": 0.167,
    "hit@1": 0.167,
    "hit@5": 0.167
  },
  "eval_lexical-only": {
    "MRR": 0.669,
    "hit@1": 0.527,
    "hit@5": 0.873
  },
  "eval_lexical-only_cross-doc": {
    "MRR": 0.708,
    "hit@1": 0.5,
    "hit@5": 1.0
  },
  "eval_lexical-only_factual": {
    "MRR": 0.649,
    "hit@1": 0.417,
    "hit@5": 1.0
  },
  "eval_lexical-only_how-to": {
    "MRR": 1.0,
    "hit@1": 1.0,
    "hit@5": 1.0
  },
  "eval_lexical-only_stale-vs-current": {
    "MRR": 0.5,
    "hit@1": 0.25,
    "hit@5": 0.833
  },
  "eval_lexical-only_why": {
    "MRR": 0.955,
    "hit@1": 0.909,
    "hit@5": 1.0
  },
  "eval_lexical-only_zero-overlap": {
    "MRR": 0.042,
    "hit@1": 0.0,
    "hit@5": 0.167
  },
  "fux_version": "fux 0.23.0",
  "ingest_seconds": 1.02,
  "latency_answer_cold_seconds": 0.48,
  "latency_answer_warm_seconds": 0.465,
  "latency_ask_cold_seconds": 0.354,
  "latency_ask_warm_seconds": 0.351,
  "latency_cat_cold_seconds": 0.095,
  "latency_cat_warm_seconds": 0.093,
  "latency_explain_cold_seconds": 0.334,
  "latency_explain_warm_seconds": 0.326,
  "latency_find_cold_seconds": 0.346,
  "latency_find_warm_seconds": 0.352,
  "latency_graph_cold_seconds": 0.311,
  "latency_graph_warm_seconds": 0.322,
  "lock_hash": "b703e9ef4b642241",
  "reingest_seconds": 0.88,
  "size_cache_bytes": 814975,
  "size_index_bytes": 1830480,
  "size_lock_bytes": 204603,
  "size_state_bytes": 237366,
  "staleness_current_in_top5": 10,
  "staleness_inversions": 9,
  "staleness_pairs": 12,
  "state_hash": "8c4b70da839b0fc2",
  "unanswerable_fabricated": 4,
  "unanswerable_find_nonempty": 4,
  "unanswerable_pairs": 4,
  "zero_overlap_rescued": 1,
  "zero_overlap_total": 6
}
```

## Findings — candidate engine changes

*Each finding below is written to graduate into the fux repo's own lifecycle: paste into `docs/proposals/` or attach to an ADR reopen-trigger.*

1. **zero-overlap dense rescue (hybrid)** — rescued 1/6 into top-5 (hit@5 0.167, MRR 0.167)
  repro: `fux find '<zero-overlap question>' --json  # hybrid mode`
2. **inversion — What is the card settlement window today?** — superseded `docs/adr/0006-settlement-window-t-plus-three.md` (rank 1) outranked current `docs/adr/0018-settlement-window-t-plus-two.md` (rank 2)
  repro: `fux find "What is the card settlement window today?" --json --top 10`
3. **inversion — How long is an idempotency key valid?** — superseded `docs/guides/legacy-idempotency-notes.md` (rank 1) outranked current `docs/guides/idempotency-keys.md` (rank 2)
  repro: `fux find "How long is an idempotency key valid?" --json --top 10`
4. **inversion — What is the current API rate limit per key?** — superseded `docs/api/legacy-rate-limits.md` (rank 1) outranked current `docs/api/rate-limits.md` (rank 2)
  repro: `fux find "What is the current API rate limit per key?" --json --top 10`
5. **inversion — How does the API authenticate requests today?** — superseded `docs/guides/legacy-api-keys.md` (rank 1) outranked current `docs/guides/authentication.md` (rank 5)
  repro: `fux find "How does the API authenticate requests today?" --json --top 10`
6. **inversion — How many days after a charge can a refund still be i** — superseded `docs/guides/legacy-refund-policy.md` (rank 1) outranked current `docs/api/refunds.md` (rank 2)
  repro: `fux find "How many days after a charge can a refund still be issued?" --json --top 10`
7. **inversion — Are raw card numbers stored, and if so for how long?** — superseded `docs/guides/legacy-card-storage.md` (rank 1) outranked current `docs/adr/0002-tokenize-pan-at-the-edge.md` (rank 6)
  repro: `fux find "Are raw card numbers stored, and if so for how long?" --json --top 10`
8. **inversion — How many days do we have to respond to a chargeback ** — superseded `docs/runbooks/legacy-dispute-7day.md` (rank 1) outranked current `docs/runbooks/chargeback-dispute-response.md` (rank 2)
  repro: `fux find "How many days do we have to respond to a chargeback dispute?" --json --top 10`
9. **inversion — For how long does Acme retry a failed webhook before** — superseded `docs/api/legacy-webhooks-v1.md` (rank 1) outranked current `docs/api/webhooks.md` (rank 2)
  repro: `fux find "For how long does Acme retry a failed webhook before giving up?" --json --top 10`
10. **inversion — Does reconciliation run in real time or as a daily b** — superseded `docs/adr/0010-realtime-reconciliation.md` (rank 1) outranked current `docs/adr/0016-reconcile-against-psp-feed-daily.md` (rank 2)
  repro: `fux find "Does reconciliation run in real time or as a daily batch?" --json --top 10`
11. **typed unanswerable questions decline (n=4)** — 0/4 declined cleanly via `answer`; `find` returned candidates for 4/4
  repro: `fux answer '<unanswerable q>' --json`
12. **fabrication — What is Acme's policy on cryptocurrency and stableco** — answer="A rounding bug in the proration engine paid out fractional  · 5 sources (want a clean decline)
  repro: `fux answer "What is Acme's policy on cryptocurrency and stablecoin settlement?" --json`
13. **fabrication — How do I configure the Kubernetes horizontal pod aut** — answer='Retries frequently cross process and even device boundaries · 1 sources (want a clean decline)
  repro: `fux answer "How do I configure the Kubernetes horizontal pod autoscaler for the mobile app?" --json`
14. **fabrication — What is the uptime SLA percentage for Acme's GraphQL** — answer="acme-payments is five services around an append-only ledger · 5 sources (want a clean decline)
  repro: `fux answer "What is the uptime SLA percentage for Acme's GraphQL API?" --json`
15. **fabrication — Which third-party vendor supplies our SMS one-time-p** — answer='Two designs were on the table — the server hashes the reque · 4 sources (want a clean decline)
  repro: `fux answer "Which third-party vendor supplies our SMS one-time-password delivery?" --json`

## Reproduce

```bash
cd acme && ./setup.sh && ./run.sh
```
