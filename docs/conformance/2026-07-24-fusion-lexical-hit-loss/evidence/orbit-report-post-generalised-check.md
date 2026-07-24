# Fux conformance run — env `orbit` — 2026-07-24

Version under test: **fux 0.26.0** (installed from PyPI into this environment's own venv).

Corpus: `/Users/arpitarya/my_programs/fux-lab/orbit/corpus` · 944 documents · **9 failure(s)** across 79 checks.

## Results

| Area | Check | Status | Detail |
|---|---|---|---|
| environment | fux under test | ✅ PASS | fux 0.26.0 · binary `/Users/arpitarya/my_programs/fux-lab/orbit/.venv/bin/fux` |
| ingest | cold ingest | ✅ PASS | exit 0 · 0.5s |
| determinism | double-ingest byte-identical | ✅ PASS | state db9f8ddfe38825bc→db9f8ddfe38825bc · lock 30209b0b9d8d5cc6→30209b0b9d8d5cc6 |
| determinism | --check clean after ingest | ✅ PASS | cache is fresh (892 sources tracked) |
| determinism | DRIFT: modified source | ✅ PASS | strict exit 2 (want 2) · DRIFT  docs/adr/0001-carrier-cologne.md  (sha mismatch — re-ingest) |
| determinism | DRIFT: new/untracked source | ✅ PASS | strict exit 2 (want 2) · DRIFT  docs/indexing/_regress-newfile.md  (new — not in fux.lock) |
| determinism | DRIFT: deleted source | ✅ PASS | strict exit 2 (want 2) · DRIFT  docs/adr/0001-carrier-cologne.md  (missing — source deleted; cache orphan) |
| determinism | drift reasons distinguishable | ✅ PASS | three distinct reasons |
| surface | `fux ask` runs | ✅ PASS | exit 0 · cold 0.121s · warm 0.129s |
| surface | `fux find` runs | ✅ PASS | exit 0 · cold 0.121s · warm 0.118s |
| surface | `fux answer` runs | ✅ PASS | exit 0 · cold 0.129s · warm 0.125s |
| surface | `fux explain` runs | ✅ PASS | exit 0 · cold 0.107s · warm 0.107s |
| surface | `fux graph` runs | ✅ PASS | exit 0 · cold 0.104s · warm 0.105s |
| surface | `fux cat` runs | ✅ PASS | exit 0 · cold 0.036s · warm 0.036s |
| determinism | fresh clone answers from committed state | ✅ PASS | state plane answered (top docs/adr/0002-goods-to-person-amrs.md) |
| determinism | fresh clone top-1 parity | ✅ PASS | index top docs/adr/0002-goods-to-person-amrs.md · state top docs/adr/0002-goods-to-person-amrs.md |
| determinism | fresh clone byte-identical (index vs state) | ℹ️ INFO | lower-rank scores differ — state plane is quantized (codes/sigs); top-1 stable, tail re-ranked |
| determinism | --lexical-only stable across runs | ✅ PASS | identical |
| correctness | citations resolve to real files | ✅ PASS | 2 sources checked |
| honest-decline | find declines on unanswerable | ✅ PASS | exit 0 · 0 results (want 0) |
| honest-decline | ask declines on unanswerable | ✅ PASS | exit 0 · 0 results (want 0) |
| honest-decline | answer does not fabricate | ✅ PASS | exit 0 · answer=null · 0 sources (want 0/none) |
| size | .fux/state | ℹ️ INFO | 0.25 MB · 265 B/doc |
| size | .fux/index | ℹ️ INFO | 1.83 MB · 1940 B/doc |
| size | .fux/cache | ℹ️ INFO | 0.80 MB · 848 B/doc |
| size | fux.lock | ℹ️ INFO | 0.20 MB · 213 B/doc |
| quality | eval (lexical-only, all n=53) | ℹ️ INFO | hit@1 0.642 · hit@5 0.887 · MRR 0.744 |
| quality | eval (lexical-only, cross-doc n=4) | ℹ️ INFO | hit@1 0.5 · hit@5 1.0 · MRR 0.688 |
| quality | eval (lexical-only, factual n=17) | ℹ️ INFO | hit@1 0.647 · hit@5 0.941 · MRR 0.775 |
| quality | eval (lexical-only, how-to n=6) | ℹ️ INFO | hit@1 1.0 · hit@5 1.0 · MRR 1.0 |
| quality | eval (lexical-only, stale-vs-current n=12) | ℹ️ INFO | hit@1 0.583 · hit@5 0.917 · MRR 0.736 |
| quality | eval (lexical-only, why n=8) | ℹ️ INFO | hit@1 0.875 · hit@5 1.0 · MRR 0.938 |
| quality | eval (lexical-only, zero-overlap n=6) | ℹ️ INFO | hit@1 0.167 · hit@5 0.333 · MRR 0.2 |
| quality | eval (hybrid, all n=53) | ℹ️ INFO | hit@1 0.698 · hit@5 0.887 · MRR 0.783 |
| quality | eval (hybrid, cross-doc n=4) | ℹ️ INFO | hit@1 0.75 · hit@5 1.0 · MRR 0.833 |
| quality | eval (hybrid, factual n=17) | ℹ️ INFO | hit@1 0.647 · hit@5 0.941 · MRR 0.784 |
| quality | eval (hybrid, how-to n=6) | ℹ️ INFO | hit@1 1.0 · hit@5 1.0 · MRR 1.0 |
| quality | eval (hybrid, stale-vs-current n=12) | ℹ️ INFO | hit@1 0.667 · hit@5 0.917 · MRR 0.792 |
| quality | eval (hybrid, why n=8) | ℹ️ INFO | hit@1 0.875 · hit@5 1.0 · MRR 0.917 |
| quality | eval (hybrid, zero-overlap n=6) | ℹ️ INFO | hit@1 0.333 · hit@5 0.333 · MRR 0.333 |
| quality | zero-overlap CLEAN dense rescue (hybrid vs lexical) | ❌ FAIL | clean rescues 1/6 (lexical missed → hybrid found); 2/6 in hybrid top-5 overall (hit@5 0.333, MRR 0.333) · rescued: How is the best-fitting shipping box picked for  |
| quality | hybrid vs lexical top-5 trade (all kinds) | ℹ️ INFO | lost 2, gained 2 (net +0); accepted behaviour, see compare/hybrid-losing-lexical-hits · lost: [factual] lex1→out What causes an inbound ASN to be rej; [zero-overlap] lex5→out How is inventory accuracy verified w |
| quality | staleness: current-doc reachable (n=12, hybrid, top-5) | ℹ️ INFO | current doc in top-5 for 11/12 pairs |
| staleness | inversion — At what pick-face fill level does replenishment trig | ❌ FAIL | superseded `docs/runbooks/legacy-replenishment-10pct.md` (rank 1) outranked current `docs/guides/replenishment.md` (rank 2) |
| staleness | inversion — How many days does a customer have to start a return | ❌ FAIL | superseded `docs/guides/legacy-returns-30day.md` (rank 1) outranked current `docs/guides/returns.md` (rank 2) |
| staleness | inversion — What time does the final carrier manifest close? | ❌ FAIL | superseded `docs/runbooks/legacy-manifest-cutoff-1600.md` (rank 1) outranked current `docs/guides/carrier-cutoffs.md` (rank 2) |
| honest-decline | typed unanswerable questions decline (n=4) | ❌ FAIL | 0/4 declined cleanly via `answer`; `find` returned candidates for 4/4 |
| honest-decline | fabrication — What is orbit's policy on paying warehouse staff in  | ❌ FAIL | answer="Dock doors were nailed one-per-carrier, so a late carrier's · 5 sources (want a clean decline) |
| honest-decline | fabrication — What is the uptime SLA percentage for the autonomous | ❌ FAIL | answer="Movable racks are carried by a fleet of AMRs to a small num · 3 sources (want a clean decline) |
| honest-decline | fabrication — How do I configure the GraphQL subscription API for  | ❌ FAIL | answer='The endpoint operates on the dock within the inbound subsys · 5 sources (want a clean decline) |
| honest-decline | fabrication — Which vendor supplies the on-site staff cafeteria ca | ❌ FAIL | answer="Track order completion at the putwall, where every zone's s · 4 sources (want a clean decline) |
| baseline | ingest_seconds | ✅ PASS | 0.49 → 0.51 (+4.1%, tolerance ±15%) |
| baseline | reingest_seconds | ✅ PASS | 0.31 → 0.31 (+0.0%, tolerance ±15%) |
| baseline | latency_ask_cold_seconds | ✅ PASS | 0.127 → 0.121 (-4.7%, tolerance ±15%) |
| baseline | latency_ask_warm_seconds | ✅ PASS | 0.137 → 0.129 (-5.8%, tolerance ±15%) |
| baseline | latency_find_cold_seconds | ✅ PASS | 0.129 → 0.121 (-6.2%, tolerance ±15%) |
| baseline | latency_find_warm_seconds | ✅ PASS | 0.121 → 0.118 (-2.5%, tolerance ±15%) |
| baseline | latency_answer_cold_seconds | ✅ PASS | 0.128 → 0.129 (+0.8%, tolerance ±15%) |
| baseline | latency_answer_warm_seconds | ✅ PASS | 0.131 → 0.125 (-4.6%, tolerance ±15%) |
| baseline | latency_explain_cold_seconds | ✅ PASS | 0.11 → 0.107 (-2.7%, tolerance ±15%) |
| baseline | latency_explain_warm_seconds | ✅ PASS | 0.108 → 0.107 (-0.9%, tolerance ±15%) |
| baseline | latency_graph_cold_seconds | ✅ PASS | 0.108 → 0.104 (-3.7%, tolerance ±15%) |
| baseline | latency_graph_warm_seconds | ✅ PASS | 0.108 → 0.105 (-2.8%, tolerance ±15%) |
| baseline | latency_cat_cold_seconds | ✅ PASS | 0.035 → 0.036 (+2.9%, tolerance ±15%) |
| baseline | latency_cat_warm_seconds | ✅ PASS | 0.034 → 0.036 (+5.9%, tolerance ±15%) |
| baseline | size_state_bytes | ✅ PASS | 249936 → 249936 (+0.0%, tolerance ±15%) |
| baseline | size_index_bytes | ✅ PASS | 1831383 → 1831383 (+0.0%, tolerance ±15%) |
| baseline | size_cache_bytes | ✅ PASS | 800335 → 800335 (+0.0%, tolerance ±15%) |
| baseline | size_lock_bytes | ✅ PASS | 201243 → 201243 (+0.0%, tolerance ±15%) |
| baseline | zero_overlap_rescued | ✅ PASS | 1 → 1 (+0.0%, tolerance ±15%) |
| baseline | zero_overlap_in_top5 | ✅ PASS | 2 → 2 (+0.0%, tolerance ±15%) |
| baseline | zero_overlap_demoted | ✅ PASS | 1 → 1 (+0.0%, tolerance ±15%) |
| baseline | zero_overlap_total | ✅ PASS | 6 → 6 (+0.0%, tolerance ±15%) |
| baseline | staleness_pairs | ✅ PASS | 12 → 12 (+0.0%, tolerance ±15%) |
| baseline | staleness_current_in_top5 | ✅ PASS | 11 → 11 (+0.0%, tolerance ±15%) |
| baseline | staleness_inversions | ✅ PASS | 3 → 3 (+0.0%, tolerance ±15%) |
| baseline | unanswerable_pairs | ✅ PASS | 4 → 4 (+0.0%, tolerance ±15%) |
| baseline | unanswerable_fabricated | ✅ PASS | 4 → 4 (+0.0%, tolerance ±15%) |
| baseline | unanswerable_find_nonempty | ✅ PASS | 4 → 4 (+0.0%, tolerance ±15%) |

## Metrics (baseline candidates)

```json
{
  "eval_hybrid": {
    "MRR": 0.783,
    "hit@1": 0.698,
    "hit@5": 0.887
  },
  "eval_hybrid_cross-doc": {
    "MRR": 0.833,
    "hit@1": 0.75,
    "hit@5": 1.0
  },
  "eval_hybrid_factual": {
    "MRR": 0.784,
    "hit@1": 0.647,
    "hit@5": 0.941
  },
  "eval_hybrid_how-to": {
    "MRR": 1.0,
    "hit@1": 1.0,
    "hit@5": 1.0
  },
  "eval_hybrid_stale-vs-current": {
    "MRR": 0.792,
    "hit@1": 0.667,
    "hit@5": 0.917
  },
  "eval_hybrid_why": {
    "MRR": 0.917,
    "hit@1": 0.875,
    "hit@5": 1.0
  },
  "eval_hybrid_zero-overlap": {
    "MRR": 0.333,
    "hit@1": 0.333,
    "hit@5": 0.333
  },
  "eval_lexical-only": {
    "MRR": 0.744,
    "hit@1": 0.642,
    "hit@5": 0.887
  },
  "eval_lexical-only_cross-doc": {
    "MRR": 0.688,
    "hit@1": 0.5,
    "hit@5": 1.0
  },
  "eval_lexical-only_factual": {
    "MRR": 0.775,
    "hit@1": 0.647,
    "hit@5": 0.941
  },
  "eval_lexical-only_how-to": {
    "MRR": 1.0,
    "hit@1": 1.0,
    "hit@5": 1.0
  },
  "eval_lexical-only_stale-vs-current": {
    "MRR": 0.736,
    "hit@1": 0.583,
    "hit@5": 0.917
  },
  "eval_lexical-only_why": {
    "MRR": 0.938,
    "hit@1": 0.875,
    "hit@5": 1.0
  },
  "eval_lexical-only_zero-overlap": {
    "MRR": 0.2,
    "hit@1": 0.167,
    "hit@5": 0.333
  },
  "fux_version": "fux 0.26.0",
  "hybrid_gained_over_lexical": 2,
  "hybrid_lost_lexical_top5": 2,
  "ingest_seconds": 0.51,
  "latency_answer_cold_seconds": 0.129,
  "latency_answer_warm_seconds": 0.125,
  "latency_ask_cold_seconds": 0.121,
  "latency_ask_warm_seconds": 0.129,
  "latency_cat_cold_seconds": 0.036,
  "latency_cat_warm_seconds": 0.036,
  "latency_explain_cold_seconds": 0.107,
  "latency_explain_warm_seconds": 0.107,
  "latency_find_cold_seconds": 0.121,
  "latency_find_warm_seconds": 0.118,
  "latency_graph_cold_seconds": 0.104,
  "latency_graph_warm_seconds": 0.105,
  "lock_hash": "30209b0b9d8d5cc6",
  "reingest_seconds": 0.31,
  "size_cache_bytes": 800335,
  "size_index_bytes": 1831383,
  "size_lock_bytes": 201243,
  "size_state_bytes": 249936,
  "staleness_current_in_top5": 11,
  "staleness_inversions": 3,
  "staleness_pairs": 12,
  "state_hash": "db9f8ddfe38825bc",
  "unanswerable_fabricated": 4,
  "unanswerable_find_nonempty": 4,
  "unanswerable_pairs": 4,
  "zero_overlap_demoted": 1,
  "zero_overlap_in_top5": 2,
  "zero_overlap_rescued": 1,
  "zero_overlap_total": 6
}
```

## Findings — candidate engine changes

*Each finding below is written to graduate into the fux repo's own lifecycle: paste into `docs/proposals/` or attach to an ADR reopen-trigger.*

1. **zero-overlap CLEAN dense rescue (hybrid vs lexical)** — clean rescues 1/6 (lexical missed → hybrid found); 2/6 in hybrid top-5 overall (hit@5 0.333, MRR 0.333) · rescued: How is the best-fitting shipping box picked for 
  repro: `fux find '<zero-overlap question>' --json  # vs --lexical-only`
2. **inversion — At what pick-face fill level does replenishment trig** — superseded `docs/runbooks/legacy-replenishment-10pct.md` (rank 1) outranked current `docs/guides/replenishment.md` (rank 2)
  repro: `fux find "At what pick-face fill level does replenishment trigger now?" --json --top 10`
3. **inversion — How many days does a customer have to start a return** — superseded `docs/guides/legacy-returns-30day.md` (rank 1) outranked current `docs/guides/returns.md` (rank 2)
  repro: `fux find "How many days does a customer have to start a return?" --json --top 10`
4. **inversion — What time does the final carrier manifest close?** — superseded `docs/runbooks/legacy-manifest-cutoff-1600.md` (rank 1) outranked current `docs/guides/carrier-cutoffs.md` (rank 2)
  repro: `fux find "What time does the final carrier manifest close?" --json --top 10`
5. **typed unanswerable questions decline (n=4)** — 0/4 declined cleanly via `answer`; `find` returned candidates for 4/4
  repro: `fux answer '<unanswerable q>' --json`
6. **fabrication — What is orbit's policy on paying warehouse staff in ** — answer="Dock doors were nailed one-per-carrier, so a late carrier's · 5 sources (want a clean decline)
  repro: `fux answer "What is orbit's policy on paying warehouse staff in cryptocurrency?" --json`
7. **fabrication — What is the uptime SLA percentage for the autonomous** — answer="Movable racks are carried by a fleet of AMRs to a small num · 3 sources (want a clean decline)
  repro: `fux answer "What is the uptime SLA percentage for the autonomous drone last-mile delivery fleet?" --json`
8. **fabrication — How do I configure the GraphQL subscription API for ** — answer='The endpoint operates on the dock within the inbound subsys · 5 sources (want a clean decline)
  repro: `fux answer "How do I configure the GraphQL subscription API for the customer mobile app?" --json`
9. **fabrication — Which vendor supplies the on-site staff cafeteria ca** — answer="Track order completion at the putwall, where every zone's s · 4 sources (want a clean decline)
  repro: `fux answer "Which vendor supplies the on-site staff cafeteria catering?" --json`

## Reproduce

```bash
cd orbit && ./setup.sh && ./run.sh
```
