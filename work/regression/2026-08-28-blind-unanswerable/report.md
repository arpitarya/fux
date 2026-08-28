---
type: Run Report
run: 2026-08-28-blind-unanswerable
classification: blind
date: 2026-08-28
---

# The `unanswerable` class, authored blind — and what it found

**Two controls ran for the first time.** ADR-RS decision 15 has carried
*"BUILT IS NOT PROVEN — none of the three controls has yet been used in a run
that adjudicates anything"* since 2026-08-27. This is the run that uses one.

## Authorship — classification `blind`

Required from 2026-08-25 (CLAUDE.md §Conformance runs), ADR-RS decision 13.
Per artifact, naming the author and what evaluation material they could reach:

| artifact | author | could reach |
|---|---|---|
| the 20 `unanswerable` queries | a fresh session, no other context | the ten corpus documents and [`BLIND-AUTHOR-BRIEF.md`](../../../tools/quality-controls/BLIND-AUTHOR-BRIEF.md) — **nothing else** |
| the ground-truth answerability ruling | a second fresh session | the ten corpus documents and the 20 queries — **no engine output, and told not to run `fux`** |
| the 50-query relevance annotation | a third fresh session | the ten corpus documents and a **stripped** query list (`id` + `q` only) — no `doc`, no `max_rank`, no `known_failure`, no scores |
| this report and the per-query harness | Claude Code (informed) | everything |

⚠ **The orchestrating session is informed and did not author evaluation
material.** It wrote the harness and this report; every judgment in the run
came from a session that had seen no scores. The `known_failure` field was
stripped from the annotator's copy precisely because its text *describes
ranking behaviour*, which is score-derived.

🔴 **The brief's own author was not blind** — that limitation is
[stated in the brief itself](../../../tools/quality-controls/BLIND-AUTHOR-BRIEF.md)
and is unchanged by this run. The mitigation is publication, not trust.

## Finding 1 — the engine did not abstain once, on 20 of 20

**Ground truth: 0 of 20 answerable.** A second blind session read the corpus
and ruled every one unanswerable, none at low confidence.

**The engine reported `answerable: true` on 20 of 20.**

| band reported | count |
|---|---:|
| `grounded` | 6 |
| `partial` | 13 |
| `weak` | 1 |

**Agreement with ground truth: 0 of 20.**

⚠ **This is not a near-miss set gone wrong — it is the set working exactly as
the brief specified.** The brief asked for questions *close to* what the corpus
covers. The three the ground-truth session called out as the sharpest:

- **u001** — *"names of all four Calder Group regions"*. The corpus says
  **"four regions"** and never names them. Perfect vocabulary overlap, absent
  fact. Reported **`grounded`**.
- **u005** — north-south ingress. Named in ADR-0007 **only inside a rejected
  alternative**; "Calder Gateway" is east-west despite its name.
- **u010** — the on-call **stipend**. The rota's *Compensation and limits*
  section covers time off and rotation caps. No money anywhere.

**Separation does not catch it:** 17 of 20 sat at or above the `0.1` floor
(median `0.448`, max `0.828`). This reproduces the decoy control's 1-of-15 at
far greater severity, and it is the same mechanism ADR-CONFIDENCE already
carries as a named, untaken decision: `coverage` and `missing` are
**corpus-wide**, so a question whose terms exist *somewhere* reads as
answerable even when no document answers it. `doc_coverage` is the signal that
would speak to this — median `0.468` here — and **its gate is off by the
2026-08-28 measurement.**

⚠ **This run does not reopen that ruling and does not propose a threshold.**
R10 is unmeasured; picking a floor from these 20 numbers would be fitting a
threshold to the set that exposed it. **It is filed as evidence, not as a
verdict on R10.**

## Finding 2 — the goldens' relevance sets are NOT complete

**A blind annotator read the corpus and the 50 questions and judged which
documents genuinely answer each:**

| relevant documents | questions |
|---:|---:|
| 1 | 25 |
| 2 | 22 |
| 3 | 3 |

**25 of 50 questions have more than one genuinely relevant document.** The
committed goldens assert **exactly one** for all 50.

🔴 **This reverses the conclusion the field-count audit implied.**
`relevance_audit.py` established that the schema holds one scalar `doc` per
query, and the inference drawn from that on 2026-08-28 was *"recall@k over this
set IS hit@k."* **That inference was about the file's shape, and it does not
survive contact with the documents.** The audit said so in its own output —
*"completeness is a human judgment about documents, and no count can substitute
for it"* — and this is that judgment.

**So `recall@k` ≠ `hit@k` on this corpus.** For half the set, a run reporting
`hit@k` is measuring "did the one asserted document come back" while a
genuinely relevant second document ranking first would score as a miss.

Three questions (`q032`, `q046`, `q050`) were annotated at low confidence and
are flagged rather than counted as settled.

## What this run does NOT establish

- **It does not adjudicate R10.** No threshold is proposed, moved, or implied.
- **It does not rule on ADR-CONFIDENCE's `doc_coverage` gate**, which was ruled
  off on measured evidence the same day. A different set is not a re-judgement.
- **It does not make the annotation authoritative.** One blind annotator is one
  opinion; a second would be the way to test it. What it does establish is that
  the one-document assumption **cannot be assumed** — a single competent blind
  reader disagreed with it on half the set.
- **No delta is claimed against anything**, so the resolution floor does not
  apply — this is a single-arm observation, not a paired comparison.

## Evidence

- [`evidence/per-query.csv`](evidence/per-query.csv) — **one row per query**,
  mandatory since 2026-08-28: ground truth, engine verdict, band, separation,
  the floor it was judged under, coverage, doc_coverage, result count.
- [`evidence/unanswerable.jsonl`](evidence/unanswerable.jsonl) — the blind set.
- [`evidence/ground_truth.jsonl`](evidence/ground_truth.jsonl) — the independent ruling, with reasons.
- [`evidence/relevance_annotation.jsonl`](evidence/relevance_annotation.jsonl) — the blind 50-query annotation.

## Reproduce

```bash
# the engine's verdict on the blind set (the playground must be indexed)
cd ~/my_programs/fux-playground
while read -r line; do
  q=$(python3 -c 'import json,sys;print(json.loads(sys.argv[1])["query"])' "$line")
  .venv/bin/python -m fux.cli ask "$q" --json --band --top 5 \
    | python3 -c 'import json,sys;c=json.load(sys.stdin).get("confidence",{});print(c.get("answerable"),c.get("band"),c.get("separation"))'
done < ~/my_programs/fux/work/regression/2026-08-28-blind-unanswerable/evidence/unanswerable.jsonl
```
