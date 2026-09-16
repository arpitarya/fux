---
type: Regression Run
name: rerank-endpoint-reachability
description: "A precondition check, not an arm: at the shipped default, can the cited-decision contest set reach either verb path's endpoint? The `ask` repair works (18.3 %, headroom both ways); both `answer` line-range criteria are 0 of 120 and are INCONCLUSIVE by construction."
run: 2026-09-16-rerank-endpoint-reachability
item: W-154
classification: informed
status: complete
timestamp: 2026-09-16T00:00:00Z
---

# Can this contest set reach either endpoint at all?

**One configuration — the shipped default.** No arm, no comparison, no bar.
The question has nothing to do with `rerank_weight`: *given a contest, is the
endpoint reachable, and is it saturated?*

🔴 **Why it ran before the next pre-registration was written.**
[The 2026-09-15 Part B run](../2026-09-15-rerank-quality/VERDICT.md) was ruled
**VOID** — the queries are sentences lifted verbatim from a citing document, so
that document is a perfect proximity match and took rank 1. The verdict names
the repair (exclude the citing document) and says it needs its own
pre-registration. **Writing that pre-registration without measuring whether the
repaired endpoint can move would be fitting a threshold to a hope.**
[SR-RS](../../../records/0133_predictions.md) decision 22b makes zero headroom
`INCONCLUSIVE` by construction, and discovering that here costs 5 minutes
instead of ~2 000 subprocesses.

**Reproduce:**

```bash
.venv/bin/python tools/quality-controls/rerank_reachability.py \
  --contests work/regression/2026-09-15-rerank-quality/evidence/contests-screened.jsonl \
  --sample 120 --seed 154 \
  --rows-out evidence/per-contest-rows.jsonl --json-out evidence/summary.json
```

**120 of the 538 screened contests**, seeded and shuffled. The instrument writes
nothing — no `.fux/tune.toml`, no index — so it runs on the live tree by
construction rather than by care.

---

## The result

| criterion | path | hits | rate | regression / improvement headroom |
|---|---|---:|---:|---|
| `ask_target_at_1` | `ask` | 4 | **3.3 %** | 4 / 116 |
| `ask_source_at_1` | `ask` | 105 | **87.5 %** | — |
| **`ask_target_at_1_excl`** | `ask` | 22 | **18.3 %** | **22 / 98** |
| `answer_top_overlap` | `answer` | 0 | **0.0 %** | 🔴 **0 / 120** |
| **`answer_best_nonsource_overlap`** | `answer` | 0 | **0.0 %** | 🔴 **0 / 120** |

## 🔴 The contamination is bigger than the VOID verdict said

That verdict reported *"39 of the 52 **broken** contests (75 %)"* — a statement
about the contests an arm changed. Measured across **all** contests at baseline:

**The citing document takes rank 1 in 87.5 % of them, and the target takes rank
1 in 3.3 %.**

So it was never a defect concentrated in the flips. **It is the endpoint.** At
3.3 % the unrepaired `ask` criterion is nearly saturated at zero, which is its
own reason it could only ever move one way.

## The `ask` repair works

Excluding the citing document from the ranked list takes the baseline from
**3.3 % to 18.3 %**, with **22 contests right and 98 wrong** — headroom in both
directions, which is what decision 22b requires and what the VOID run did not
have.

## 🔴 Neither `answer` criterion can be measured on this contest set

**Zero hits in 120, on both.** Not a weak signal — **zero**, so regression
headroom is zero and any arm run on it is `INCONCLUSIVE` (22d) before it starts.

Two criteria were tried, and the second is the same repair the `ask` path got:

- **`answer_top_overlap`** — the VOID run's own criterion (4 hits in 538, and 0
  in this sample).
- **`answer_best_nonsource_overlap`** — drop every passage from the citing
  document, then ask whether the best remaining one overlaps the true decision.

⚠ **The obvious explanation is wrong, and it was measured rather than assumed.**
The first guess was that the citing document monopolises the passage set, making
post-filtering impossible. It does not: over 30 contests, answers carried **19.4
passages on average**, the citing document appeared in **30 of 30**, and it was
the **only** document in **0 of 30**. There is always something else to promote.
The target document is present in roughly **27 %** of answers — it is simply
almost never the *best* non-source passage, and when it is, the line range does
not overlap.

**So the `answer` path is out of scope for the re-run**, and
[W-108](../../../records/0133_predictions.md)'s two-mechanism separation stays
undelivered — **with a measured reason rather than a null**.

## What this does NOT establish

- **Nothing about `rerank_weight`.** One configuration ran. This says which
  endpoints *can* be measured, never what a measurement would find.
- **Nothing about the refer plane.** That `answer` cannot be scored on *this*
  contest set is a property of the contest set, not of the refer plane.
- **Nothing that transfers.** The corpus is fux's own tree — see §Authorship.

## Authorship

| what | who |
|---|---|
| the contest generator | this project's sessions (`cited_decision.py`) |
| the contest set | derived from this repository's own citations |
| this instrument | this session |
| the corpus | **fux's own tree** |

**`informed`**, and not marginally: the corpus is the repository these sessions
read constantly and the instrument's author is its reader.
[SR-RS](../../../records/0133_predictions.md) decisions 11–19a — an informed run
is **reclassified, not banned**: filed, cited, and never compared with a blind
run or used to state a delta against one.
