# Conformance run — `answer` confidence-floor calibration

**Date:** 2026-07-23 · **Run:** `min-confidence-calibration` · **Target:** v0.25.0
(handoff 0006 DoD 6, compare `answer-decline-floor.compare.md`)

**Headline:** **No `min_confidence` value clears all five gates.** The
unanswerable and answerable score distributions overlap with no separating
threshold. **Recommendation: ship permissive — `min_confidence = 0.0`
(disabled).**

---

## What was measured

- **The floor mechanism** in `src/fux/query/api.py::_run_answer`: after
  `build_answer()` selects sentences, `best_confidence = max(s.score for s in
  sentences)`; decline when `floor > 0.0 and best_confidence < floor`.
- **The value the floor actually compares** is the per-sentence `score` from
  `build_answer` — *not* the `find`/`ask` score. It had to be measured on the
  new build, because the old acme evidence predates the mechanism.

## Setup (and the deliberate deviation)

- **Editable local checkout**, not the pinned PyPI wheel: `uv pip install -e
  ~/my_programs/fux` into `fux-lab/acme/.venv`. Verified `fux 0.24.0` importing
  from `~/my_programs/fux/src/fux`. No PyPI release carries the floor yet.
- **Acme corpus regenerated** (`make_repo.py`, seed 20260722): 929 docs, 59 eval
  pairs, ingested to 885 chunks, hybrid engine live. The prior corpus dir was
  absent — regen was required, not reuse.
- **Mechanism proven before trusting numbers:** `min_confidence = 0.99` made a
  known-answerable query decline; `0.0` answered it.
- **Method:** a throwaway script (`evidence/dump_scores.py`) mirrors
  `_run_answer` exactly and dumps `best_confidence` for every eval question in
  one pass. Boundary values were then re-confirmed against the real CLI. **No
  file under `src/` was touched.**

## The five gates

| # | Gate | Exercises `answer`? | Result |
|---|------|--------------------|--------|
| 1 | Decline all 4 acme typed-unanswerable | **yes** | needs floor **>= 0.25** |
| 2 | Keep declining gibberish | yes | **satisfied at any floor** (empty pool) |
| 3 | Fixture 21-pair (`tests_e2e/eval`) | **no — `ask`** | no-op |
| 4 | Acme 55 answerable, no false decline | **yes** | needs floor **<= 0.087** |
| 5 | Synthetic 1k/5k/10k baselines | **no — `find`** | no-op |

Gates 1 and 4 are **mutually exclusive**: 0.25 <= floor <= 0.087 is empty.

### Why 2, 3, 5 are not constraints

- **#2 gibberish:** `best_confidence = null` — the candidate pool is empty, so it
  declines via the pre-existing zero-candidate early return at *any* floor,
  including 0.0. A floor can only make its decline more certain.
- **#3 fixture 21-pair:** `run_eval.py` queries with `ask`, never `answer`
  (line 81). `min_confidence` gates only `answer`. Unaffected by construction.
- **#5 synthetic tiers:** the regress harness scores retrieval with `find`
  (`_score_pairs`), and `make_corpus.py` plants only `overlap`/`zero-overlap`
  pairs — no `unanswerable`, no answer pairs — so `check_unanswerable_pairs` is
  empty there. The lone `answer` call is the gibberish probe, which declines at
  any floor. 5k/10k were not regenerated: the deterministic generator provably
  emits no answer pairs.

## The measured score distributions (the crux)

**Unanswerable — must decline (best_confidence):**

| best_confidence | question |
|---|---|
| **0.2488** | policy on cryptocurrency & stablecoin settlement |
| 0.1483 | uptime SLA % for the GraphQL API |
| 0.1081 | configure k8s HPA for the mobile app |
| 0.0958 | third-party vendor for SMS-OTP |

To decline **all 4**, floor must exceed **0.2488** -> floor >= 0.25.

**Answerable — must keep answering (lowest 8 of 55):**

| best_confidence | kind | question |
|---|---|---|
| 0.0869 | zero-overlap | what keeps information after power loss |
| 0.1363 | stale-vs-current | algorithm to verify a webhook signature |
| 0.1459 | zero-overlap | why nobody can quietly change the record |
| 0.1770 | factual | numeric form the ledger stores amounts in |
| 0.1815 | factual | how long Acme retains raw PANs |
| 0.1898 | why | why we tokenize card numbers at the edge |
| 0.1915 | zero-overlap | what we do when a message won't go through |
| 0.2000 | zero-overlap | how we stop strangers draining an account |

The lowest legitimate answer (0.0869) sits **below** the weakest fabrication
that must be caught, and 13 legitimate answers sit at or below the crypto
fabrication (0.2488). **The classes are interleaved, not separated.**

## Threshold sweep (`evidence/threshold-sweep.json`)

| floor | unanswerable declined /4 | gibberish /1 | answerable false-declines /55 |
|------:|:---:|:---:|:---:|
| 0.00 | 0 | 1 | **0** |
| 0.10 | 1 | 1 | 1 |
| 0.12 | 2 | 1 | 1 |
| 0.15 | 3 | 1 | 3 |
| 0.20 | 3 | 1 | 7 |
| 0.24 | 3 | 1 | 10 |
| **0.25** | **4** | 1 | **11** |
| 0.26 | 4 | 1 | 13 |
| 0.30 | 4 | 1 | 17 |
| 0.35 | 4 | 1 | 23 |

- **Only floor = 0.0 gives zero false declines** — and it catches 0/4
  unanswerable (the disabled/pre-0.25 behaviour).
- **The first non-zero floor (0.10) already false-declines a correct answer**
  while catching only 1/4 unanswerable.
- **4/4 unanswerable first happens at 0.25**, costing **11/55 (20%)** correct
  answers.

## CLI validation of the boundary

Confirms the script's numbers drive real CLI behaviour:

| floor | crypto unanswerable (bc 0.2488) | "numeric form ledger stores amounts" (bc 0.177) |
|---|---|---|
| 0.24 | **ANSWER** (fabricates) | **DECLINE** (false — a correct answer lost) |
| 0.25 | DECLINE (correct) | DECLINE (false — same correct answer lost) |

At **no** floor does the crypto fabrication decline while the legitimate
"numeric form" answer survives.

## Verdict

Per the compare doc's calibration rule and DoD 6: when no single value satisfies
1–5, **do not ship a default that declines a correct answer.** Ship the knob
with a **permissive default of 0.0** and document the trade-off curve above. Full
diagnosis and the reopen path in `ANALYSIS.md`.
