---
type: Pre-Registration
description: "Frozen before any number: what the golden ladder's phase-4 run measures, on which rungs, with which metrics and which k."
item: W-136
run: 2026-09-12-golden-ladder
classification: informed
engine: fux-engine 2.0.0-alpha.7
engine_sha: 676e973
filed: 2026-09-12
---

# Pre-registration — golden ladder phase 4, rungs seed → 1 000

**Committed before any query was asked and before any question was read.**
The ladder was built and frozen first; the questions were opened only after
this file and the five rung manifests were committed. That order is the whole
of what makes the rungs blind, and it is checkable from `git log`.

---

## 1. What this run is, and what it is not

**It is:** the plumbing run for the sealed golden benchmark. It produces, per
rung, one ranked prediction and one prose answer for each of the 124 released
questions, so that Codex can score them in phase 5 without Claude ever seeing
an answer.

**It is NOT a measurement anyone may cite a delta from.** Every number that
comes out of it is `informed` by construction, for the reason
[W-145](../../open/W-145-codex-regenerates-the-key.md) records: the answer key
in use was authored by Claude as a stopgap when Codex's quota ran out mid
phase 1, and the same model family grew the corpus and runs the engine. A leak
is detectable after the fact; correlated priors between the question-writer and
the corpus-writer are not.

**Binding consequence, fixed here and not revisable after the numbers exist:**

- 🔴 **No delta may be stated** — not rung-to-rung, not against any other run,
  not "better than", not "unchanged". Per-rung absolute scores may be reported.
- 🔴 **No verdict may be filed against any prediction** (R1–R7 or otherwise).
  This run adjudicates nothing.
- 🔴 **The run may not be compared with a blind run**, in either direction.

When Codex regenerates the key under W-145, the *same frozen ladder* can be
re-run and that run may be blind. That is why the per-query rows below are
recorded now: they are what makes the later comparison possible at all.

---

## 2. Arms

**One arm.** Engine `fux-engine 2.0.0-alpha.7` at repo sha `676e973`, stock
configuration, each rung's own committed index, no re-ingest, no tuning
override, no flag that changes ranking.

There is deliberately **no second arm**. A paired comparison against a
Claude-authored key would produce exactly the delta §1 forbids, and building
one would be the more expensive way of learning nothing.

---

## 3. Rungs

| rung | documents | frozen manifest |
|---|---:|---|
| `rung-seed` | 20 | `work/golden/ladder/rung-seed.sha256` |
| `rung-00100` | 100 | `work/golden/ladder/rung-00100.sha256` |
| `rung-00200` | 200 | `work/golden/ladder/rung-00200.sha256` |
| `rung-00500` | 500 | `work/golden/ladder/rung-00500.sha256` |
| `rung-01000` | 1 000 | `work/golden/ladder/rung-01000.sha256` |

`rung-02000`, `rung-05000` and `rung-10000` are **not built**. Arpit capped this
session at 1 000 documents. Nothing here claims anything about a rung that does
not exist, and no threshold below is written against one.

Every rung is verified against its manifest immediately before it is queried.
A rung whose documents do not hash to its manifest is not run; it is reported
as not run.

---

## 4. The command, fixed

Per question, from inside the rung directory, in this order:

```
fux ask "<question>" --json --band --top 10
fux answer "<question>" --json          # the prose answer and its citation
```

- `--top 10` fixes **k = 10** for every ranked list. Metrics below name their
  own k and never exceed it.
- `--band` produces the confidence block, which is what `answerable` is read
  from. Nothing else decides abstention.
- No `-q` fusion, no `--expand`, no `--fast`, no `--no-tune`. Stock.
- A question is asked **exactly once per rung**. No retry on a poor-looking
  result, which is the step that would turn this into an informed *search*.

---

## 5. What is recorded, per question per rung

`evidence/<rung>/predictions.jsonl` — the phase-5 input, one line per question:

```json
{"id": "...", "ranked": ["seed/01-….md", …], "answerable": true, "band": "…"}
```

`evidence/<rung>/answers.jsonl` — the prose answer for human and agent review:

```json
{"id": "...", "question": "...", "answer": "...", "citations": [...],
 "band": "...", "answerable": true, "ranked": [...], "ms": 0}
```

🔴 **Per-query rows are recorded for every question on every rung** — CLAUDE.md
§Conformance runs, and ADR-RS decision 15. A summary count is not enough and
never was: the discordant count, `b`, `c` and every test anyone runs later are
derivable from per-query rows and from nothing else.

---

## 6. Metrics Codex computes in phase 5 — defined here, before the numbers

| metric | definition | k |
|---|---|---:|
| `hit@1` | the top-ranked path is in the key's `relevant` for that id | 1 |
| `hit@5` | any of the top 5 paths is in `relevant` | 5 |
| `recall@5` | \|top-5 ∩ `relevant`\| / \|`relevant`\| | 5 |
| `rank_first_relevant` | 1-based rank of the first path in `relevant`; `null` if none in top 10 | 10 |
| `abstained` | the run reported `answerable: false` | — |
| `abstain_correct` | `abstained` equals the key's `answerable == false` | — |

- An `unanswerable` id scores `hit@1 = hit@5 = recall@5 = 0` by definition and
  is judged **only** on `abstain_correct`. It is never counted as a miss in the
  answerable slices.
- **Sealed ids are reported in aggregate only**, per rung, per metric. The key
  in use marks all 124 ids `sealed: false`, so in this run the aggregate and
  the per-query set are the same population; that is recorded, not hidden.

---

## 7. Headroom disclosure (ADR-RS decision 22)

This is a **single-arm** run, so there is no paired endpoint to disclose
headroom for, and §1 forbids the delta that would need one.

What is disclosed instead, per rung, computed from the per-query rows:

- **improvement headroom** — the number of ids not already `hit@1` correct;
- **regression headroom** — the number of ids currently `hit@1` correct;
- both labelled **unproven**, because this run carries no feature-off/on arm
  and no generator `--selftest` establishing separability (decision 22c).

⚠ **Unproven is disclosed, not voided.** It is not zero and it does not trigger
22d. It is stated so that the later blind re-run on this same frozen ladder has
a recorded starting point that nobody had to reconstruct.

---

## 8. What would make this run invalid

Written down now so it cannot be decided afterwards. If any of these is true,
the run is reported as invalid rather than scored:

1. A rung's documents do not match its frozen manifest.
2. The engine version differs from `rung-NNNNN.index` and the rung was re-ingested
   without that being stated in the report.
3. Any question or answer from `work/golden/golden-answer/` appears in a Claude
   session's context at any point.
4. A question is asked more than once on the same rung, or asked with any flag
   not listed in §4.
5. The ladder is rebuilt, regenerated or added to after this file is committed.

---

## Reference

- Process and phase contract: [`work/golden/README.md`](../../golden/README.md)
- The item: [W-136](../../open/W-136-golden-benchmark.md)
- Why every number here is `informed`: [W-145](../../open/W-145-codex-regenerates-the-key.md)
- Classification, per-query rows, headroom: [ADR-RS](../../../docs/adr/0133_predictions.md)
  decisions 11–15, 22, 23
- The ceiling this run respects: [`CLAUDE.md`](../../../CLAUDE.md) §Litmus — 10 000
  documents, and this run stops at 1 000 on Arpit's instruction.
