---
type: Proposal
title: The measurement plan — the twenty-one `unmeasured` rows that can be measured now, as eight pre-registrations
description: "The 2026-10-03 backlog audit sorted every `unmeasured` row by what it waits on. Twenty-one wait on nothing but a frozen pre-registration on data that exists (lab rungs, the retired sets, a filed capture). This file is the plan — rung, endpoint, instrument, bar — per theme, so each becomes a W-item by copying a section. Twelve rows stay blocked on data that does not exist, and the file says which."
status: proposed
timestamp: 2026-10-03T00:00:00Z
---

# The measurement plan, October 2026

**Graduation trigger — per section, not for the file:** a section graduates
into a `W-nn` when the data it names is in hand **and** a ranking or design
decision is waiting on its number (SR-WORK-BACKLOG decision 2: only a
measurement closes an `unmeasured`). Sections 1 and 2 can graduate the day
W-240's gen-4 rung is scored; sections 3, 5, 6 and 8 need no key at all and can
graduate now; sections 4 and 7 wait on Arpit's hands or tokens (W-251 §3
#23–24).

**Why a plan and not twenty-one items.** The queue's length is a signal
(SR-WORK-OPEN-QUEUE rule 3). Twenty-one 🟢 rows that each say *pre-register,
capture, score* would drown the seven items that are real work. One file that
says exactly how each would be measured costs nothing to keep and lets any
session pick one up with the design already written.

**Every section inherits the rules:** SR-RS d10a (file the run), d10b (a
pre-registered threshold never moves), d11–d19 (`blind`/`informed`, the paired
floor — a net of 6 flips), SR-WORK-TESTDATA (the feature's input must exist in
the data), L9 (never `fux-playground`), L11 (no agent reads a key; Arpit runs
`just golden-score`). Every number on an agent-authored set is `informed`.

---

## 1 · Ranking constants — B-089, B-090, B-107, B-091

**Rows:** `title`/`path`/`ctx` field weights carried *"from nothing"*
([SR-RANKING](../../records/0111_ranking.md) d3); `expand_weight = 0.2`
*"ratified and unmeasured"* ([SR-TUNE](../../records/0135_tuning.md) d12); PPR's
`iterations = 3`, `laziness = 0.5` ([SR-GRAPH](../../records/0126_graph.md)
Consequences); the `docidx` tie-break in 4.38 % of queries
([SR-RERANK](../../records/0138_rerank.md) veto 5).

**Design — the W-168 capture template** ([`2026-09-28-intent-prior`](../regression/2026-09-28-intent-prior/)
is the worked example): five arms per key, everything else held; `hit@1` on
`set-4-claude` at rung-01000 (gen-4 when scored); pre-registration frozen and
committed alone; Arpit runs `just golden-score`; a session that did **not**
capture runs the frozen `decide.py`. **Bar:** SR-RS d19 — net ≥ 6 at the
observed discordant count, zero rank-1 losses on untagged questions.
**Caveat, stated before the run:** the winnable pool is 7–31 questions
([`2026-09-22-w168-step-inputs`](../regression/2026-09-22-w168-step-inputs/)),
so INCONCLUSIVE is the likely outcome and a *filed* INCONCLUSIVE closes the row
as honestly as a PASS. Fallback: the constructed-family design of the `b`-sweep
(`tools/quality-controls/w144_graded.py`) with ≥ 2 controls that can lose.
**B-107 needs no run:** recount exact top-5 ties over the filed 2026-09-27
capture rows; *did a tie decide a golden?* needs his score.
**B-091:** the endpoint is rank-1 moves of `fux explain`/`ask_boost` on the
link-bearing questions (sets 3/4 carry `ref` edges, 82 per rung).

## 2 · Confidence and abstention — B-113 (+B-130), B-114, B-261's gates

✅ **Graduated 2026-10-04 → W-256 §2** (W-251 §4); B-114 was ruled, not measured (`cost` B-266).

**Rows:** the `doc_coverage` gate is off because *"the two populations
overlap"* ([SR-CONFIDENCE](../../records/0141_confidence.md) d12); the fusion
floor on the RRF scale (W-109 ⚠); the eight unmeasured gates of
[`abstention-gates`](../compare/abstention-gates.compare.md).

**Design — one measurement, then one ruling.** On rung-01000, join the W-213
hand-off rows (they already carry `doc_coverage`) for the **retired sets 1–3**
(36 unanswerables, 340 answerable, answers open) plus set-4's ~12
unanswerables. **Endpoint:** separation (AUC) between the two `doc_coverage`
distributions; for each candidate floor the (withheld-correct, caught-unanswerable)
pair against d19. **Bar, pre-registered:** a floor must catch ≥ 50 % of
unanswerables while demoting fewer correct answers than a coin at the same
withhold rate — the W-213 criterion that removed gate 1. Then W-251 §3 #11 (does
`separation` stay the quantity) and the next gate's item follow the number.

## 3 · Corpus shape — B-095, B-096, B-115, B-116 (B-122 blocked)

**Rows:** the type filter as a ranking change ([SR-TYPES](../../records/0128_types-list.md));
`max_phrases = 32` post-hoc ([SR-EXTRACTED](../../records/0115_extracted-mode.md) d9);
heading emission for `pdf`/`rtf`/`csv`/`jsonl` ([SR-DECODE](../../records/0139_decode.md)
d15); `toml`/`yaml`/`ini` emit no title (d11a).

**Design — probe sets, no key.** Thirty deterministic probes per format or
setting on rung-01000, in the [`2026-09-12-priors-and-tables`](../regression/2026-09-12-priors-and-tables/)
style; `hit@1` before/after; headroom proven under SR-RS 22c(b). B-095/B-096
add paired `hit@5` on the retired sets at d19. **Bar:** ≥ 24/30 probes reached,
or a pre-registered null that is filed. B-122 (how often `!` re-inclusion is
used) stays **blocked**: it needs consumer repos that do not exist.

## 4 · Fetch and daemon, real network — B-092, B-093, B-101, B-102, B-103, B-124

✅ **Graduated 2026-10-04:** the lab-side half → W-256 §4; his-hands half → [W-258](../open/W-258-live-network-captures.md). B-092 was ruled (`cost` B-265); B-093 stays blocked on B-268.

**Lab-side, now:** B-103 — a daemon start → sweep → stop e2e on
`windows-latest` with the 2026-08-27 positive control (term absent before,
present after); B-124 on loopback — journalled answers, server taken down,
`as-ingested` share against `doctor`'s quarter veto.
**His hands (W-251 §3 #24):** B-101 (`MAX_PARALLEL` against real session-gated
sources in signed-in Chrome), B-102 (a real rate limit), B-093 (a real usage
trace — also waits on #14, the query log), B-124's live half. B-092 is a note,
not a measurement (#8).

## 5 · Refer, tabular, cascade — B-117, B-119, B-121, B-127, B-262 (ex-B-044), B-120

**Design.** Re-run `tools/refer-bench` (the R4 harness, 100 ms mock source) at
`ANSWER_TOP = 3` — the registered bound's premise was `k = 10` — cold p95
against 3 s; re-register (B-119). Same rung: top-1 vs top-3 cited-document
recall on the retired sets, `evidence_quoted` beside it (B-127). Toggle header
scoring in `_rescore` and count citation changes (B-117). Deterministic byte
count on synthetic 1k/5k/20k-row sheets (B-121). **Cascade (B-262):** stage-1
`recall@k` above ~0.98 on golden tables is the gate
([SR-CHUNKING](../../records/0151_chunking.md) §What is NOT done); it needs the
tabular seed documents **no SR-WORK-TESTDATA row yet names** (checked 2026-10-04:
T1–T14 name none; a T15 is the prerequisite) — so this half graduates with the
seed generation that carries them. B-120 then
goes to Arpit as cascade-vs-constant **with numbers**.

## 6 · Node arm parity — B-125 → W-252

Promoted; the plan is the item.

## 7 · Enrichment — B-108, B-109, B-110, B-245

✅ **Graduated 2026-10-04 → [W-257](../open/W-257-enriched-rung.md)**, with the blind-author protocol this section missed (SR-RS d11).

**All blocked on one deliverable:** an enriched rung — model-generated
questions over rung-01000 with `enrich=true` declared. The cost is tokens and
it is his (W-251 §3 #23). When it exists: doc2query's bar re-registered naming
`k` (B-108), the `--check` filter on enough questions to be visible (B-109),
the tilt at 25/50/100 % coverage (B-110). B-245 (the vector plane) reopens only
when this ceiling **and** a rank-contract corpus both exist.

## 8 · Ingest cost — B-098

✅ **Graduated 2026-10-04 → W-256 §8**, which rules B-002 on the number.

Re-run `evidence/phase_times.py` with `full=True` against a delta on an
unchanged rung-10000; endpoint = the ratio, three repeats, identical sha. W-239
timed full ingest only (73.5 → 12.8 s) and the delta split was never re-read.

## Blocked rows, stated so nobody re-derives them

B-093, B-101, B-102 (real network, his machine) · B-105 (a real cross-encoder in
tooling) · B-108–B-110 (an enriched rung) · B-112 (human adjudication of 5–10 %
of judged scores) · B-122 (consumer repos) · B-135 (a Copilot observation on his
IDE) · B-245 (both conditions).

## Rulings, not measurements

B-092, B-100, B-114, B-120, B-128, B-137 were ruled 2026-10-04 (W-251 §4) — a
number was either in hand or could not settle them; B-099 stays Arpit's (§3 #9).
