---
type: Run Report
run: 2026-09-05-doc2query
classification: informed
date: 2026-09-05
---

# W-110's gate — questions instead of prose, four arms. **Ambiguous; handed to Arpit**

🔴 **The bar is met at `recall@1` and not at `recall@3`, `@5` or `@10`, and the
bar never said which `k`.** This run does **not** adjudicate that, per
CLAUDE.md: *"If a result lands between 'clearly passes' and 'clearly fails',
write it up as ambiguous and hand it to Arpit. Do not adjudicate it, and do not
restate the threshold in looser words."* No `VERDICT.md` is filed.

**What is not ambiguous: enrichment never cost a query, at any `k`, in any
arm.** Every movement was upward.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the 50 goldens and their relevance sets | pre-existing; sets by two mutually blind sessions, κ = 0.960 | — |
| 🟢 **the 98 questions (the `real` arm)** | **a separate agent session with a fresh context**, 2026-09-05 | **the 10 corpus documents. Nothing else** — no queries, no goldens, no relevance sets, no report |
| the `placebo` arm | `tools/quality-controls/placebo.py`, seeded, deterministic | the real arm's word counts only |
| 🔴 the feature, the harness and this report | Claude Code, this session | everything, including the judgments |

⚠ **The blind author here saw LESS than W-109's**: it was given the corpus and
**not** the questions, because doc2query enrichment is authored per *document*.
It was instructed in writing not to open any grading, query or evidence file.
**Compliance is asserted by that agent and was not mechanically verified.**

The run is `informed` because the harness and the analysis are this session's.
**Not a generalisation estimate.**

## The corpus

`fux-playground` re-derived from its ten committed documents — the same corpus
as [`2026-09-05-expand`](../2026-09-05-expand/report.md) and
[`2026-09-05-vector-gate`](../2026-09-05-vector-gate/report.md). Absolute
numbers here are **not comparable** with any run measured on the enriched
playground, whose enrichment was never committed and is gone.

## Arms

| arm | `.fux/enrich/` holds |
|---|---|
| `none` | nothing |
| `placebo` | content-free matched-length text — ADR-RS decision 15's control |
| `real` | the blind author's **98 questions**, all of them |
| `filtered` | the same, minus the **2** `fux enrich --check` refused (doc2query−−) |

## The numbers — `recall@k` over the 43 goldens declared `complete`

| arm | `recall@1` | `recall@3` | `recall@5` | `recall@10` | `hit@1` |
|---|---|---|---|---|---|
| `none` | 0.4341 | 0.8256 | 0.9186 | 0.9884 | 0.6047 |
| **`placebo`** | **0.4341** | **0.8256** | **0.9186** | **0.9884** | **0.6047** |
| `real` | **0.5698** | 0.8798 | 0.9535 | **1.0000** | **0.7674** |
| `filtered` | 0.5698 | 0.8798 | 0.9535 | 1.0000 | 0.7674 |

**Paired, against `none`:**

| metric | `placebo` | `real` | `filtered` |
|---|---|---|---|
| `recall@1` | 0 up / 0 down | **7 up / 0 down · net +7** | 7 / 0 · net +7 |
| `recall@3` | 0 / 0 | 3 / 0 · net +3 | 3 / 0 · net +3 |
| `recall@5` | 0 / 0 | 2 / 0 · net +2 | 2 / 0 · net +2 |
| `recall@10` | 0 / 0 | 1 / 0 · net +1 | 1 / 0 · net +1 |

The seven at `recall@1`: `q005 q007 q012 q013 q018 q028 q044`.

## 🔴 Why this is ambiguous, precisely

W-110's definition of done says:

> Gate filed: the `none` / `placebo` / `real` arms from
> `2026-08-28-placebo-and-seal` re-graded on `recall@k`; **blind** author;
> per-query rows; **net ≥ 6**.

**It does not fix `k`.** At `k = 1` the result is **net +7** and clears it. At
every larger `k` it does not — and the reason is arithmetic rather than
disagreement: `recall@10` is already `0.9884` without enrichment, so there is
almost nothing left to move. **The effect is real and it is concentrated at the
top of the ranking**, which is where a caller with one slot actually reads.

**Choosing the `k` after seeing the numbers is exactly the move a
pre-registration exists to prevent**, so this session does not choose one.

## ✅ The placebo is a perfect null, at every `k`

**0 discordant queries, and every aggregate identical to `none` to four
decimal places.** That is the strongest form this control can take: matched
length, matched file count, matched frontmatter, one shared vocabulary pool —
and no movement whatsoever.

It says the `real` arm's gain is **the content of the questions**, not the fact
that ten more files were indexed or that ten documents got longer.

## ⚠ The doc2query−− filter changed nothing measurable

`fux enrich --check` refused **2 of 98** questions across 2 of 10 files
(`evidence/check-output.txt`), and removing them moved **no** recall number at
any `k`. Two queries' top-5 *ordering* differed (`q002`, `q045`); their recall
did not.

**So the filter's value is unproven by this run**, and the honest statement is
that it did not hurt. Two refusals out of 98 is too small a treatment to see —
the 2026-08-24 lesson, applied to itself: *always report the fraction of the
population a treatment actually touched.* Here it is **2 %**.

## Reproduce

```bash
E=work/regression/2026-09-05-doc2query/evidence
# four copies of the corpus; write the blind questions into `real`, then
# `python tools/quality-controls/placebo.py <real>/.fux/enrich <placebo>/.fux/enrich`
python $E/enrich_bench.py <scratch-dir> <path-to>/fux/src \
    ~/my_programs/fux-playground/goldens/queries.jsonl /tmp/rows.csv
```

## Evidence

- `evidence/per-query.{csv,jsonl}` — **172 rows**, one per query per arm:
  `recall@{1,3,5,10}`, `hit@1` and the top-5 for each.
- `evidence/blind-questions.jsonl` — all 98 questions, as written.
- `evidence/check-output.txt` — the doc2query−− filter's refusals.
- `evidence/enrich_bench.py`, `evidence/summary.txt`.

## Nothing is claimed at 10 000 documents

Ten documents, 43 graded queries, one corpus state, one machine.
