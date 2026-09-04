---
type: Run Report
run: 2026-09-05-answer-top3
classification: informed
date: 2026-09-05
---

# `fux answer` refers the top 3 — before and after, on the 43 graded queries

**W-108.** `cmd_answer` retrieved one document and handed it to `refer()`, so
`answer` inherited `recall@1` by construction. This is the paired measurement of
retrieving three instead, on the shipped defaults and with the reranker on.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the 50 goldens' questions | pre-existing (playground) | — |
| the relevance sets | **two blind sessions**, mutually blind, κ = 0.960 (2026-08-28) | corpus + stripped queries only |
| 🔴 the change being measured (W-108) | Claude Code, this session | **the queries, the relevance sets, and the [first-recall](../2026-08-28-first-recall/report.md) per-query rows** |
| the harness (`evidence/answer_bench.py`) | Claude Code, this session | everything |
| this report and `ANALYSIS.md` | Claude Code, this session | everything |

🔴 **`informed`, and the reason is the change's author, not the corpus.** W-108
was designed by a session that had read the graded queries and the run showing
`recall@1 = 0.5969`. **These numbers are not a generalisation estimate** and no
claim is made about any corpus but this one.

## The corpus is NOT the one the 2026-08-28 numbers were measured on

⚠ **`fux-playground`'s `.fux/index/` is empty and `.fux/sources/dirs` lists no
directory** — the corpus that W-87 Part B has been blocked on since 2026-08-27
(*Blocked on Arpit*, 9 days). `.fux/enrich/` is empty too.

So this run **re-derived** the index in two throwaway copies of the playground,
from the ten committed documents, with `docs` appended to the source list and
**no enrichment installed**. Both arms read the same re-derived index, byte for
byte.

**What that costs, stated plainly:** the absolute numbers below are **not
comparable** with `2026-08-28-first-recall`'s `0.5969`/`0.9535`, which were
measured on the enriched corpus. This is a **paired** before/after on one corpus
state, which is what the change needed; nothing here restores or replaces that
run. **The playground itself was not modified.**

## Arms

| arm | engine | `[ranking] rerank_weight` |
|---|---|---|
| `A0` | `main` @ `b512f41` (before W-108) | `0.0` — the shipped default |
| `B0` | W-108 | `0.0` — the shipped default |
| `A1` | `main` @ `b512f41` | `1.0` |
| `B1` | W-108 | `1.0` |

`A0 -> B0` is the change as it ships. `A1 -> B1` is the same change with the
reranker on — **the only configuration in which W-108's passage-proximity
multiplier fires at all** — and it is conflated with the reranker's own effect
on which documents are candidates, so it is read as post-hoc.

## The numbers — 43 of 50 queries (`relevance: complete`)

`hit` = the answer cited at least one relevant document. `recall` = the share of
a query's relevant set the answer's cited documents cover. `bytes` = mean
assembled bytes (`--audit`'s `budget.used`).

| arm | n | hit | recall | bytes | docs cited | grounded | partial | weak |
|---|---|---|---|---|---|---|---|---|
| `A0` | 43 | 0.6047 | 0.4341 | 2 517 | 1.00 | 22 | 21 | 0 |
| `B0` | 43 | **0.9070** | **0.8256** | 6 467 | 2.98 | 14 | 21 | **8** |
| `A1` | 43 | 0.6744 | 0.4922 | 2 486 | 1.00 | 22 | 21 | 0 |
| `B1` | 43 | **0.9070** | **0.8256** | 6 467 | 2.98 | 17 | 21 | **5** |

**Paired outcome, `A0 -> B0`: 13 queries fixed, 0 broken.**
`q005 q007 q012 q013 q015 q017 q018 q026 q035 q038 q043 q044 q049`.
Recall rose on 24 queries and **fell on none**.

**Paired outcome, `A1 -> B1` (post-hoc): 10 fixed, 0 broken.**
`q005 q007 q012 q017 q018 q035 q038 q043 q044 q049`. Recall rose on 21, fell on
none.

**Resolution.** 13 discordant, 13–0. Under the paired bar
([ADR-RS](../../../docs/adr/0036_predictions.md) decision 19) a net of 13 at 13
flips is far above the floor of 6; this is not a below-resolution result.

## The three costs, none of them hidden

**1. Assembled bytes rose on 43 of 43 queries** — mean 2 517 -> 6 467, median
delta +4 242, max +5 655, and 8 000 (the `[refer] budget`) is now reached. The
**bound** is unchanged and never exceeded. W-108's own hazard note asked to
assert *"the assembled bytes never exceed today's for the same query"*; that is
**false on 43 of 43 and false by design** — it conflated the bound with the
spend. An answer that reads three documents costs about 2.6× the context of one
that read one.

**2. `--band` demotes 8 of 43 from `grounded` to `weak`** (5 of 43 with the
reranker on): `q001 q002 q019 q024 q026 q030 q044 q048`. `answer` retrieved one
result, so `separation` was `1.0` on **every query it had ever answered** — an
artefact of the width, not a claim about the ranking. It is now real. No floor
moved and nothing gates on the band.

**3. The winning document changed on 18 of 43** (10 of 43 with the reranker
on). `ask` ranks documents; `answer` now runs a cross-document passage contest
over `ask`'s top three, so the two are allowed to disagree — and do. Every hit
change was an improvement, so on this corpus the disagreement never cost a
correct citation.

## The gate

> **No hand-graded golden that passed now fails.**

**Met, byte-for-byte.** `check.py` (which grades `ask` by *rank*) emits
**identical output** on both arms — `FAIL 13 · pass 28 · xfail 9` — and
`diff evidence/goldens-arm-A-main.txt evidence/goldens-arm-B-w108.txt` is empty.
⚠ Those 13 failures are the **un-enriched corpus's** baseline, present in both
arms; they are not a regression and W-108 did not cause them.

## Reproduce

```bash
# a worktree of the pre-W-108 engine
git worktree add /tmp/arm-main main

# two throwaway playgrounds; the second turns the reranker on
cp -R ~/my_programs/fux-playground /tmp/pg-rw0
cp -R ~/my_programs/fux-playground /tmp/pg-rw1
sed -i '' 's/^rerank_weight           = 0.0/rerank_weight           = 1.0/' /tmp/pg-rw1/.fux/tune.toml
for d in /tmp/pg-rw0 /tmp/pg-rw1; do
  printf 'docs\n' >> "$d/.fux/sources/dirs"          # the wiped source list
  (cd "$d" && PYTHONPATH=/tmp/arm-main/src python -m fux.cli ingest)
done

# 172 rows: 43 queries x 4 arms
uv run python work/regression/2026-09-05-answer-top3/evidence/answer_bench.py /tmp out.csv
```

## Evidence

- `evidence/per-query.csv` — **172 rows, one per query per arm**: cited
  documents, hit, recall, band, separation, support, assembled bytes, dropped.
- `evidence/answer_bench.py` — the harness, as run.
- `evidence/goldens-arm-A-main.txt` / `evidence/goldens-arm-B-w108.txt` —
  `check.py`'s full output per arm; byte-identical.
- `evidence/goldens-as-measured.jsonl` — the 50 goldens as they stood.

## Nothing is claimed at 10 000 documents

Ten documents, 43 queries, one corpus state, one machine. CLAUDE.md §Litmus:
this is measurement at the design point and below it, and no threshold, budget
or bound above 10 000 is stated, implied or owed.
