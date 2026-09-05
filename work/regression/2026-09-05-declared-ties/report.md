---
type: Run Report
run: 2026-09-05-declared-ties
classification: informed
date: 2026-09-05
---

# W-111 — the declared tie-break: correct, differential-green, and **unexercised by any corpus here**

The tie-break now reads `superseded -> recency -> priority -> id` instead of a
document's name alone. **Its measured effect on both available corpora is
zero**, and that is the finding rather than a disappointment: it means the
change is safe, and it means nothing here demonstrates the benefit either.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the change, the harness and this report | Claude Code, this session | everything |
| the playground query set | `tools/differential/queryset.py`, seeded, generated from the corpus's own vocabulary | no goldens involved |
| the 10 000-document query set | `fux-benchmark`'s `pairs.jsonl`, pre-existing | — |

**No blind option existed and none is claimed** — the measured quantity is *how
often does fux tie*, which no judgment can contaminate.

## What was measured

| corpus | queries | top-5 rows | rows marked `tie` | queries whose top-5 **order** differs from the old `id`-only key |
|---|---|---|---|---|
| `fux-playground` re-derived, 10 docs, **generated** queries | 668 | 2 450 | **0** (0.00 %) | **0** |
| `fux-benchmark` `t10000`, **10 000 docs**, 240 `pairs.jsonl` | 240 | 1 200 | **3** (0.25 %) | **0** |

## 🔴 Why zero, and why that is a fact about the CORPORA

The 4.38 % figure this change was motivated by comes from
[`2026-08-25-rank-flip-susceptibility`](../2026-08-25-rank-flip-susceptibility/ANALYSIS.md)
— **297 generated queries over a 495-document corpus that does not exist on
this machine.** Neither corpus available here reproduces that population, and
both are inert for a second, structural reason:

- **`fux-playground`**: all ten documents share **one** `mtime` (one commit) and
  **none** is superseded. Both signals are constant, so every tie falls through
  to `id`.
- **`t10000`**: it is **not a git repository**, so `git_commit_times` returns
  nothing and **all 10 000 documents have no `mtime` at all**. 40 documents are
  superseded, and none of the three ties involved one.

**So the ordering is correct and the demonstration is missing.** The unit tests
prove each signal in the ratified order separates equals
(`tests/query/test_ties_and_filters.py`, one test per signal plus the
precedence between them); **no corpus here shows it changing a real answer.**

⚠ **The three ties at 10 000 documents each marked exactly ONE row of five** —
so each is a row tied with the *sixth* document, off the page. That is the flag
doing precisely what it was built for, and it is the only thing in this run
that a caller would have seen.

## The differential law

`tools/differential/run.py --full --skipping both` on the playground:

```
queries: 3164   tops: [1, 5, 20, 50]   modes: off, on
comparisons: 101248
DIFFERENTIAL GREEN — 101248 comparisons, byte-identical in every mode
```

**101 248 comparisons**, far past W-111's `240+`. Both paths reach `rank()`
with the same record dicts and the new key reads only fields both generators
already carry (`superseded`, `mtime`, `loc`).

⚠ **A 10 000-document differential run was started and had not finished when
this was filed.** It is not required — the playground run satisfies the bar
several hundred times over — and it is named here rather than quietly omitted.

## `find`'s three filters

Not graded: they are **precision controls**, not ranking changes, and there is
no relevance question to grade. Covered by
`tests/query/test_ties_and_filters.py` and `tests_e2e/test_verbs.py`, including
the two cases that are judgement rather than plumbing — a `url:` document is
**kept** by `--phrase` offline, and `--phrase` drops stopwords because the
index's analyzer does.

## Reproduce

```bash
E=work/regression/2026-09-05-declared-ties/evidence
python $E/tie_rate.py <corpus> <path-to>/fux/src generated /tmp/rows.csv <path-to>/fux/tools/differential
python $E/tie_rate.py <corpus> <path-to>/fux/src <queries.jsonl> /tmp/rows.csv
python tools/differential/run.py --root <corpus> --full --skipping both
```

## Evidence

- `evidence/per-query-playground.{csv,jsonl}` — 668 rows.
- `evidence/per-query-t10000.{csv,jsonl}` — 240 rows.
- `evidence/differential-playground.txt` — the full run.
- `evidence/tie_rate.py` — the harness. It derives the old `id`-only order by
  **re-sorting the declared results**, patching no engine code.

## Nothing is claimed at 10 000 documents

The larger corpus **is** 10 000 documents — the design point exactly. No
threshold, budget or bound above it is stated or implied.
