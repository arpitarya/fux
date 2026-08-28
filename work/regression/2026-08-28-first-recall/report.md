---
type: Run Report
run: 2026-08-28-first-recall
classification: informed
date: 2026-08-28
---

# `recall@k` is computed for the first time

**[ADR-QUALITY](../../../docs/adr/0044_quality-contract.md) decision 2 made
`recall@k` the headline on 2026-08-27 and its own consequences said it could not
be computed** — *"it needs known-relevant sets per query."* Those sets now exist,
authored blind and twice, and decision 12 gave them a schema. This is the first
number under the contract.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the relevance sets | **two blind sessions**, mutually blind, agreeing at κ = 0.960 | corpus + stripped queries only |
| the goldens' questions | pre-existing | — |
| 🔴 **the installed corpus enrichment** | an agent, 2026-08-24 | **the queries** — all ten files are the contaminated set |
| the harness, migration and this report | Claude Code | everything |

🔴 **The run is `informed`, and the reason is the corpus, not the judgments.**
All ten enrichment files installed in the playground are the arm whose author
**had read these queries** — the `+9` arm. **So the absolute recall numbers
below are measured on a corpus fitted to the very questions being asked**, and
they are **not a generalisation estimate.** They are the metric working, on the
corpus as it stands.

⚠ **No delta is claimed against anything**, so the resolution floor does not
apply. This is a single-arm measurement.

## The number

**`recall@k` over the 43 of 50 queries declared `complete`** (decision 12 rule
b: the covered fraction is reported *with* the number, never the number alone).
Reported as a curve against context bytes, per decision 2.

| k | `recall@k` | mean context bytes |
|---:|---:|---:|
| 1 | **0.5969** | 2,988 |
| 3 | **0.8566** | 9,079 |
| 5 | **0.9535** | 15,135 |
| 10 | **0.9884** | 27,048 |

**The 7 excluded queries are the two annotators' exact-set disagreements.** They
carry `relevance: partial` — a real claim that *these* documents are relevant,
with no assertion that the list is exhaustive — and recall over a
partially-declared set is a fraction with an unknown denominator.

## Why this is not just `hit@k` with a new name

**Of the 43, nineteen have more than one relevant document.** That is the whole
reason the metric changed:

| slice | `recall@5` | n |
|---|---:|---:|
| single-document | 0.9583 | 24 |
| **multi-document** | **0.9474** | 19 |

For the 24 single-document queries `recall@k` **is** `hit@k` and always was. For
the other 19 it is a genuinely different quantity — it asks what fraction of the
relevant set came back, and a run that returned one of three relevant documents
scores `0.33` here and `1.0` under `hit@k`.

## Back-compatibility, verified rather than assumed

Decision 12 rule d says the new fields are optional and nothing historical
breaks. **Checked on the real harnesses after the swap:**

- `fux-playground/check.py` — **41 pass · 9 xfail**, unchanged.
- `tools/differential/playground_grade.py` — **41/0/9 in both modes**,
  `accelerator == scan` still holding.

**No `hit@k` number moved.** The goldens gained two fields and lost nothing.

## What this run does NOT establish

- 🔴 **It is not a generalisation estimate.** The corpus enrichment was fitted
  to these queries. A clean absolute number needs an uncontaminated corpus.
- **It compares nothing.** One arm, no delta, no verdict on any prediction.
- **It does not validate the relevance sets.** Two blind readers agreeing at
  κ = 0.96 is strong evidence about this corpus; κ measures agreement, never
  correctness, and both could share a blind spot.
- **It says nothing above 10 000 documents** — ten documents, fifty queries.
- **The 7 `partial` queries are not adjudicated**, and an agent should not be
  the one to adjudicate them.

## Evidence

- [`evidence/per-query.csv`](evidence/per-query.csv) — **one row per query**:
  the relevance-set size and `recall@` 1/3/5/10. Every number above is
  derivable from it.
- [`evidence/goldens-as-measured.jsonl`](evidence/goldens-as-measured.jsonl) —
  the migrated goldens exactly as measured, so the run is reproducible even if
  the playground's copy moves on.

## Reproduce

```bash
# the schema gate, then the number
python3 tools/quality/goldens.py ~/my_programs/fux-playground/goldens/queries.jsonl

# hit@k must be UNCHANGED by the migration -- 41 pass / 9 xfail
cd ~/my_programs/fux-playground && .venv/bin/python check.py --top 5
```
