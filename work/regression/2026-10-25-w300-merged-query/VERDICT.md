---
type: Verdict
name: W-300-MERGED-QUERY
description: "W-300 under L13 (defaults): the merged query (scope = all) against the repository alone, on the W-299 fixture package pinned beside a 6-document consumer — every gate byte-identical, slice hit@1 16 wins / 0 losses, nothing outside the slice moved. The table reads PASS; filed INCONCLUSIVE → Arpit, as the pre-registration fixed before any number. Arpit ruled PASS 2026-10-25: ship, scope stays all; the right test is W-303."
verdict: PASS
verdict_by_table: PASS
filed_as: "INCONCLUSIVE → Arpit, by the pre-registration's own rule (SR-RS d6; no golden G; section@1 and latency unmeasurable)"
ruled_by: "Arpit, 2026-10-25 (Cowork) — declared PASS: ship it, `scope` stays `all`; how to test it the right way is W-303"
prediction: W-300-MERGED-QUERY
pre_registration: work/regression/2026-10-25-w300-merged-query/PRE-REGISTRATION.md
run: 2026-10-25-w300-merged-query
item: W-300
filed: 2026-10-25
classification: informed
---

# VERDICT — W-300, the merged query

**Ruling: PASS — Arpit, 2026-10-25 (Cowork).** *"Yeah, declare it as pass, but
add a research item or add a testing item, how to test it this in the right
way. For now, go ahead and ship it."* And, on the default: *"keep scope as
all."* The three gaps below stand as written; the test that closes them —
a large real package beside a real repository, questions not written by
Claude, the repository's own rank-1 answers counted — is
[W-303](../../open/W-303-merged-query-right-test.md). **This section is the
ruling; everything under it is the run as filed, unchanged.**

**As filed by the run: INCONCLUSIVE → Arpit.** L13 decision 4's table, read on the numbers,
gives **PASS**; the pre-registration (frozen in commit `dbec142c` before any
number, sha256 `628f15655c83cfdabc293cb5805ae81a18ca0ae4d33a0e0fa1760f908ec6fffd`)
ruled in advance that a PASS from this run is filed INCONCLUSIVE, because:

1. **SR-RS decision 6** — the session that built W-300 wrote the questions,
   captured the arms and computed the reading. It may not adjudicate its own
   measurement.
2. **G over golden rows** (L13 decision 2) was not run — no golden corpus is
   reachable from this session, and the scorer is Arpit's (L11). G0a–c stand in.
3. **Two guardrails are unmeasurable here** — `section@1` (no answer key for
   this set) and `ask` latency on `rung-10000` (no package-bearing rung).

| row | result |
|---|---|
| G0a no pin, vs pre-W-300 (`9688d479`) | 0 / 30 differ |
| G0b pinned, `scope=repo`, vs pre-W-300 | 0 / 30 differ |
| G0c this repository's own index | 0 / 30 differ |
| G-Node (ids, package, order; score at round 9) | 0 / 30 differ |
| slice floor | 16 ≥ 15 |
| C1 slice `hit@1` | `b=16 c=0 discordant=16 net=16 p=0.0000 (net needed 10, alpha=0.05) -> B` |
| C2 outside the slice | 0 wins, 0 losses (margin 2) |
| C3 whole set | +16 |
| GR `hit@5` | 14 → 30 |
| GR `grounded` | 8 → 13 |

**What Arpit is asked to rule:** whether this run, with the three gaps above,
is enough to ship `scope = all` as the default — or which of them a further run
must close first (an independently authored question set over a real package; a
golden G0 by the scorer; a latency capture on a package-bearing rung).

**What it does not do:** speak for a package larger than its consumer, or for any
golden set. The evidence is `evidence/rows.jsonl`, `evidence/gates.json` and
`evidence/summary.json`; the voided first run is `evidence/run1-void/`.
