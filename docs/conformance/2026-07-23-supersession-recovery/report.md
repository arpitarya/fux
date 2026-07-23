# Conformance run — supersession recovery (handoff 0006 DoD 8)

**Date:** 2026-07-23 · **Run:** `supersession-recovery` · **Target:** v0.25.0
(handoff 0006 DoD 8, compare `supersession-handling.compare.md`)

**Headline:** Markers present on **5 of 12** stale docs (not "roughly a third").
Only **3 of the 9** original `find`-inversions carry a machine-readable marker.
At the **`answer`** level the fix **fully corrects 1** of those 9 and **de-cites
the retired doc in a 2nd**; the other 7 are either already answer-correct (1) or
unmarked and unreachable (6). **This is partial recovery — not a fix of all 9.**

---

## Setup

- **Editable local checkout** (`fux-lab/acme/.venv` → `~/my_programs/fux/src`),
  the same env from the confidence-floor run — reused, not rebuilt. Acme corpus
  as ingested (929 docs, 885 chunks, hybrid engine live).
- **Method:** the `find`/`ask --json` annotation and ranking were read from the
  real CLI. The `answer` before/after was measured with a script
  (`evidence/dump_supersession.py`) that mirrors `_run_answer` and compares
  `build_answer` on the raw retrieval pool (BEFORE — no preference) vs
  `prefer_current(pool)` (AFTER). CLI `answer --json` confirmed the after-state.
  **No file under `src/` was modified.**

## 1. Marker count — the real number

**5 of 12** stale docs carry machine-readable `status: superseded` +
`superseded_by:` frontmatter:

| pair | stale doc | superseded_by target | target == eval-current? | was a find-inversion? |
|---|---|---|---|---|
| 0 | adr/0006-settlement-window-t-plus-three | adr/0018-settlement-window-t-plus-two | ✅ | **yes** |
| 2 | adr/0001-acquirer-northwind | guides/architecture-overview | ✅ | no |
| 5 | guides/legacy-api-keys | guides/authentication | ✅ | **yes** |
| 9 | adr/0004-webhook-signing-sha1 | adr/0011-hmac-sha256-webhook-signing | ❌ (eval-current is api/webhooks) | no |
| 11 | adr/0010-realtime-reconciliation | adr/0016-reconcile-against-psp-feed-daily | ✅ | **yes** |

The other **7 of 12** (pairs 1,3,4,6,7,8,10) carry no marker — dated inline
prose or nothing. Deterministically unreachable (no model allowed).

## 2. `find` / `ask` annotation + ranking unchanged (accepted verdict)

For all 5 marked pairs, `find --json` carries `"superseded": true,
"superseded_by": "<doc>"` on the stale doc's result **wherever it appears**
(pairs 0,2,5,11; pair 9's stale is not in top-6, so not annotated there). **Rank
positions are byte-identical to the 2026-07-22 evidence** — annotation only, no
reorder, exactly as the compare-doc verdict requires:

| pair | stale rank now (was) | current rank now (was) | unchanged |
|---|---|---|---|
| 0 | 1 (1) | 2 (2) | ✅ |
| 2 | 4 (4) | 1 (1) | ✅ |
| 5 | 1 (1) | 5 (5) | ✅ |
| 9 | — (—) | 6 (6) | ✅ |
| 11 | 1 (1) | 2 (2) | ✅ |

Raw JSON in `evidence/find-json/`.

## 3–5. `answer` before/after — the actual behavior fix

`prefer_current` drops a superseded doc's chunks from the `answer` pool **only
when its resolved successor is also in the pool it retrieved**. Result for the 3
marked inversions:

| pair | before (`answer` lead / stale cited?) | after | verdict |
|---|---|---|---|
| **0** settlement | leads with **stale** 0006 (T+3) | leads with **current** 0018 (T+2); stale gone | **FULLY RESOLVED** |
| **5** auth | lead = unrelated 0007; stale cited (5th) | stale de-cited; **lead unchanged** (0007); current not promoted | **PARTIAL** |
| **11** reconciliation | already leads with **current** 0016; stale never cited | unchanged | **already correct** (find-only) |

Marked non-inversions: pair 2 (before led with stale northwind → after de-cited,
an improvement but not one of the 9); pair 9 (stale not retrieved; answer serves
a *different unmarked* stale doc, no effect).

The 6 unmarked inversions (1,4,6,7,8,10): `answer` before == after, unchanged —
the documented residual.

## Before / after summary

| metric | value |
|---|---|
| `find`-inversions (original run) | **9 of 12** |
| …carrying a machine-readable marker | **3 of 9** (pairs 0,5,11) |
| …fully corrected at `answer` (retired gone AND current leads) | **1** (pair 0) |
| …retired doc removed from citations but lead unchanged | **+1** (pair 5) |
| …already answer-correct before the fix (find-only) | 1 (pair 11) |
| …unmarked, deterministically unreachable | **6** |

**Net: 1 of 9 fully corrected, 1 more de-cited. Partial by design — only
frontmatter-marked pairs are reachable, and a marker fixes `answer` only when
retrieval also lands the successor in the pool.** Diagnosis in `ANALYSIS.md`.
