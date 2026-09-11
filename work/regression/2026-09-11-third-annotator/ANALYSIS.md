---
type: Analysis
run: 2026-09-11-third-annotator
---

# Analysis

1. **Apply:** in `fux-playground/goldens/queries.jsonl`, set `relevance` to `complete`
   for q020, q021, q027, q032, q039, q042, q050. `relevant` arrays unchanged.
   Repro: `python3 -c "import csv;r=list(csv.DictReader(open('evidence/per-query.csv')));print(sum(x['in_dispute']=='yes' and x['resolved']=='relevant' for x in r))"` → `10`.
2. **Consequence:** `recall@k`'s denominator grows from 43 to 50 queries. Any
   `recall@k` filed before this is not comparable with one computed after.
3. **Unresolved:** whether the sets are complete. Annotator 3 added 4 documents no one
   else did (report §Four documents). A completeness audit is a different run.
4. **Unresolved:** the brief annotators 1–2 received is not filed; this run used its own
   relevance definition.
