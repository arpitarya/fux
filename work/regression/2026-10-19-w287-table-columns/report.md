---
type: Run Report
run: 2026-10-19-w287-table-columns
item: W-287
date: 2026-10-19
classification: informed
status: decided — FAIL (guardrail)
---

# 2026-10-19 — W-287 stage B: tables by row and by column — **FAIL (guardrail)**

**Decided 2026-10-19 by Arpit's run of the frozen decider: [VERDICT.md](VERDICT.md).** 59 slice wins, 0 losses on both endpoints, no collateral — and `answer` p95 on the 20 000-row sheet 1.74× against a 1.2× limit. `table_column_weight` stays `0.0`.

**Run class: `informed`.** One session wrote the engine, the corpus, the
questions, the capture and the bar ([PRE-REGISTRATION.md](PRE-REGISTRATION.md)
§Classification). **No endpoint has been computed by anyone.** The decider is
frozen and is run by a hand that did not capture
([SR-RS](../../../records/0133_predictions.md) decision 6) — Arpit, from his own
shell:

```bash
cd ~/my_programs/fux/work/regression/2026-10-19-w287-table-columns/evidence
python3 decide.py --questions ../questions.jsonl --captures captures \
    --g0 g0.json --latency latency.json > decision.json
```

**Surface:** Darwin arm64 · Python 3.14.3 (`.venv`) · Node 22 · the working
tree on `896382fb`, uncommitted. Latency is this surface's and is not
comparable to Linux figures elsewhere.

## Authorship — SR-RS decision 13

| artifact | author | could reach, at the time |
|---|---|---|
| the engine (stages A–C) | Claude Code (Opus 5.5), this session | the design; no query of this set (it did not exist yet) |
| `corpus.py`, `questions.jsonl` (answers included) | Claude Code, this session | the engine it had just built — **queries and judgments both** |
| `capture.py`, `g0.py`, `latency.py`, `decide.py`, the pre-registration | Claude Code, this session | everything above; **no prior score on this set — none exists** |
| the captures, G0, G1, latency | Claude Code, this session | the questions' text and the arms' raw output; **no endpoint**, because the capture computes none |
| the verdict | **Arpit**, running `decide.py` | everything; he did not build the arms |

One author for engine, data and instrument: **`informed`**, permanently. The
burden the rule places on this report: the queries and the judgments were
reachable by the engine's author, so this run supplies no generalisation claim —
only whether the mechanism moves the data built to let it.

## Headroom — SR-RS decision 22, per endpoint and per direction

Computed by `decide.py` from the baseline arm's per-query rows, never by this
hand (SR-RS decision 24e: the pool is the baseline's own misses):

- **improvement** headroom, per endpoint (`hit1`, `cell1`): the slice questions
  `tc-0.0` misses — `gates.slice_floor.winnable` in `decision.json`; below
  **15** on either endpoint the run STOPS before any arm is read.
- **regression** headroom: the questions `tc-0.0` already answers — `counts`
  per arm in `decision.json`, and C2/C3 read the losses from it.

By construction (T3), every F1, F3 and F4 question — 71 of the 83 — carries a
decoy row that out-counts its answer row on the query's own terms at baseline;
`corpus.py` re-checks every count on the final rows. That is a construction
claim, not a measured pool, and the decider's number is the one that counts.

## What was captured

| | |
|---|---|
| corpus | `evidence/corpus.py`, seed 287 — 25 documents, regenerated twice byte-identical; built at `~/my_programs/fux-lab/w287-tables/base/repo` (kept) |
| questions | 102 — F1 40 · F2 12 · F3 16 · F4 15 · P 19; slice 83 — `questions.jsonl` at the run root (a question set is not evidence rows, SR-RS d21b) |
| arms | `tc-0.0` (baseline), `tc-1.0` (decided), `tc-1.0-noB3`, `-noB4`, `-noB5`, `-B2` (reported) |
| per arm | each question's `answer --json --band` passages (up to 10: document, ordinal, locator, table, row, cells, `columns_matched`, text, score), the band, and `ask --top 10` — `evidence/captures/<arm>.jsonl` |
| engine | `src/fux/` digest `d942320c…` (re-frozen after STOP 1, and again for the one-table-module refactor — the pre-registration's two notes) |

## Gates — run by the capturing hand, as the pre-registration says

| gate | result |
|---|---|
| **G1** every arm's committed index byte-identical | **PASS** — one digest, `145ceb896368f4a9…`, across all six arms |
| **G0** key off = the engine without row metadata | **PASS** on the re-capture — 0 of 102 differ, 0 tie reorders (`evidence/g0.json`) |
| slice floor (≥ 15 winnable per endpoint) | **computed by the decider**, from the baseline arm — not by this hand |

### 🔴 STOP 1 — the first capture failed G0, and it was a build defect

**2 of 102 questions** (`w287-075`, `w287-079`) cited a different member of an
exact-score tie group with the key **off**. `rescore` and `assemble` broke ties
on the *displayed* locator, and C3 had changed that string for a spreadsheet row
(`#p12` → `#Incidents!R13`). Every score and the score order were identical; only
which tied row the budget seated moved. **Fixed:** ties break on the positional
`order_key` in both runtimes ([SR-REFER](../../../records/0127_refer-plane.md)
decision 28a), pinned by
`tests/refer/test_table_columns.py::test_c3_a_sheet_locator_moves_no_order_among_tied_rows`.
The stopped capture is kept unscored in `evidence/stop-1/`; the bar, the data and
every frozen script are unchanged; only the engine digest moved.
**That is the gate doing its job**: without G0 the defect would have shipped as a
presentation change that silently reorders tied rows.

## Latency

`evidence/latency.json` — run standalone after both captures and the gates, with
nothing else of this run in flight; the load average before and after is in the
file. Read by the decider; not interpreted here.

## The seven captures ([SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md))

| # | capture | where |
|---|---|---|
| 1 | the engine | `src/fux/` digest in the pre-registration's STOP 1 note; `captures/meta.json` names the import path and version |
| 2 | the corpus | `corpus.py` + `corpus-sha256.txt` in the lab env (hashed in the freeze) |
| 3 | the questions | `evidence/questions.jsonl` (hashed) |
| 4 | the config | each arm's `.fux/tune.toml` differs from the base in `table_column_weight` alone (`capture.py::_set_weight`) |
| 5 | per-query rows | `captures/<arm>.jsonl`; the decider writes `per_query` (SR-RS 19a) |
| 6 | the surface | above |
| 7 | the instrument | `capture.py`, `g0.py`, `latency.py`, `decide.py`, all hashed before any arm |

## What happens next

1. Arpit runs `decide.py` (above) and files `VERDICT.md` from `decision.json`.
2. PASS ships `table_column_weight = 1.0` as the template value; FAIL keeps
   `0.0` with a FAILED banner on SR-REFER decision 28; INCONCLUSIVE is his.
3. **Engine re-frozen 2:** stage A was refactored to ONE table module mid-run
   (Arpit's 19:45 correction). The re-capture is identical to the one it
   replaced, field for field — so the per-decoder capture is kept in
   `evidence/superseded-engine-2/` only as the proof of that. W-288 moves
   `_table.py` to `ext/table.py` next; its byte-identity gate, applied to these
   25 documents, keeps this capture valid across that move too.
