---
type: Handoff
name: W-256
description: "The three sections of the October measurement plan that need no golden key and no human hands, promoted together on 2026-10-04 (W-251 §4): §8 the delta/full ingest split (rules B-002 on the number), §2 the doc_coverage replay over the W-213 rows (abstention gate 2, then SR-CONFIDENCE d12), §4 lab-side — Windows daemon e2e, loopback 429, loopback as-ingested. Every number informed. Ratified, NOT run."
item: W-256
filed: 2026-10-04
ball: agent
---

# W-256 — the no-key measurements

**✅ CLOSED 2026-10-04 — three runs filed; one PASS, two handed to Arpit as their frozen rules require** (Claude Code; a Sonnet subagent pre-registered — frozen alone at `a935d511` — and ran, Opus 5.5 reviewed):
- **§2 `doc_coverage` replay — INCONCLUSIVE.** 374 rows, 21 reachable unanswerables (the item's 340 answerable was 338); floor 0.80 alone meets the point criteria, p = 0.35 against 0.00625, consistent in one set of three. `doc_coverage_floor` stays 0.0; SR-CONFIDENCE d12 carries a pointer. → W-260 §1.
- **§8 ingest split — a split result.** Delta median 10.39 s at rung-10000, full 15.11 s (1.45×; SR-INGEST's 23× rewritten); walk+parse 24–30 %, `redact` ~57 % — 6 s against W-239's 0.97 s, unexplained. B-002 neither closes nor promotes. → W-260 §2. W-239's `phase_times.py` could not give this split (its walk read 0 s); `ingest_split.py` names every gap.
- **§4 loopback — PASS.** B-102 14/14 (3, 3, 4, 1 requests; backoff 1.01/2.01/4.01 s; `rate_limited[host]` = 8; doctor names the host — two script defects fixed in-run and disclosed, all attempts kept); B-124 13/13 (current while up; `as-ingested` with `fetched_sha == indexed_sha` once down; the quarter veto silent at 20 %, warning at 33 %). SR-ACQUIRED now says the instrument was exercised on loopback, and its journal path is corrected (`provenance.jsonl`). **B-103 (Windows daemon e2e) excluded**: it needs a `windows-latest` CI run, and `main` carries an unpushed local commit that reds CI until W-240.

**Model:** Claude Code, **Sonnet** — each section is a pre-registration written
in the plan plus a script in `tools/`; the bars are stated before any number
exists. **Ratified 2026-10-04 by delegation ([W-251](../../work/open/W-251-backlog-audit-rulings.md)
§4), not run.** Three sections of
[`measurement-plan-2026-10`](../../work/proposals/measurement-plan-2026-10.md) graduate
here because each now has **a decision waiting on its number** (the plan's own
trigger); the rest of the plan stays parked.

**Every section inherits:** SR-RS d10a (file the run), d10b (a pre-registered
threshold never moves), d11–d19 (`blind`/`informed`; the paired floor), L9
(never `fux-playground`), L11 (no agent reads a key — none is needed here; the
retired sets are open and every number on them is `informed`).

## §8 — the delta/full ingest split (B-098 → rules B-002)

- **Why now:** SR-MAINTENANCE 1a-3 says the dirty list *"alone buys no speedup"*
  and option D (incremental corpus-wide passes) is *"deferred to its own item"*;
  the only number behind that is the 23× split SR-INGEST §1 still cites, which
  *"no longer describes the pipeline"*. W-239 timed full ingest only (73.5 →
  12.8 s at rung-10000; extract is 6.5 s of it).
- **Run:** `evidence/phase_times.py` with `full=True` against a delta on an
  unchanged rung-10000, three repeats, identical root sha; endpoint = per-phase
  split (walk/sha, parse, extract, edges, write) and the full/delta ratio.
- **The decision it rules, pre-registered:** if the delta run's non-extract
  phases total **< 5 s at rung-10000**, B-002 closes — the dirty list stays
  advisory (`maintain/dirty.py`'s docstring is true), SR-MAINTENANCE 1a-3 cites
  the run, and option D is *not needed at the design point*. If they total ≥ 5 s
  and walk+parse dominate, a runtime parse cache keyed on content sha
  (`.fux/runtime/parsed/`, pure in (sha, header, digests) like `_reusable`)
  becomes its own item (M–L, Opus). Either outcome rewrites SR-INGEST §1's 23×.

## §2 — `doc_coverage` over the W-213 rows (B-113; abstention gate 2 of B-261)

- **Data in hand:** the W-213 captures — 2 992 rows, 3 retired sets × 8 rungs
  (`work/regression/2026-09-22-band-operating-point/evidence/rung-*/capture-set-*.jsonl`)
  — already carry `confidence.{coverage,doc_coverage,separation,missing,failed,band}`;
  36 unanswerables / 340 answerable, answers open.
- **Run:** a replay script in `tools/quality-controls/` over those rows at
  rung-01000: AUC between the two `doc_coverage` distributions; for each
  candidate floor, the (withheld-correct, caught-unanswerable) pair.
- **Bar, pre-registered (the W-213 criterion that removed gate 1):** a floor
  must catch ≥ 50 % of unanswerables while demoting fewer correct answers than a
  coin at the same withhold rate. PASS → `doc_coverage_floor` moves in
  `tune.toml` (L12) and SR-CONFIDENCE d12 is amended; FAIL/INCONCLUSIVE → filed,
  d12's *off* stands with a measured reason. **Then** gates 4 and 3 (the ruled
  u017 pair) are replayable on `answer_text` the same way — a successor item,
  not this one. W-251 §4 #11 (`separation` stays the label's quantity; this
  is the next lever) is what waits on the number.

## §4 lab-side — the loopback halves

- **B-103:** a daemon start → sweep → stop e2e on `windows-latest`, with the
  2026-08-27 positive control (term absent before, present after).
  SR-MAINTENANCE 9c-i's *"macOS only"* sentence then reads *"verified on macOS
  and Windows"* or names the difference.
- **B-102 loopback:** a local server emitting 429 exercises `is_rate_limited` →
  `RATE_LIMIT_RETRIES`/`RATE_LIMIT_BACKOFF_BASE` and `url-state.json
  rate_limited[host]`; `fux doctor` names the host. The *real-network* half is
  [W-258](../../work/open/W-258-live-network-captures.md).
- **B-124 loopback:** a `url:` corpus with `keep=true`; `fux answer --journal`
  N times; the server taken down; `as-ingested` share against `doctor`'s
  quarter veto, and the taken-down document reports `as-ingested` with
  `match=True`. The live half is W-258.

## Definition of done

1. Three runs filed under `work/regression/`, each with PRE-REGISTRATION
   (frozen and committed alone, before the number), raw evidence, report and
   VERDICT, labelled `informed`.
2. The record sentence each run decides, rewritten in the same change and
   restamped: SR-MAINTENANCE 1a-3 and SR-INGEST §1 (§8); SR-CONFIDENCE d12
   (§2); SR-MAINTENANCE 9c-i (§4); SR-ACQUIRED Consequences' *"never had data
   to run against"* (§4).
3. `BACKLOG.md`: B-002 closed or promoted on §8's number; B-261's row names
   gate 2 as measured and the next gate; the plan's §2/§4/§8 marked
   *graduated → W-256*.
4. Both suites whole; a WORKLOG entry.

## Out of scope

- Anything needing a key (plan §1), his hands (§4 live — W-258) or his tokens
  (§7 — W-257).
- Building the parse cache or moving any floor before its number exists.

## Hazards

- ⚠ The W-213 rows were captured at a given index version; replaying
  `doc_coverage` from stored fields is legal only because the field is in the
  rows — do not recompute it from a newer index and call it the same run.
- ⚠ Windows CI minutes are the W-243 budget; run §4's e2e once, not per push.
