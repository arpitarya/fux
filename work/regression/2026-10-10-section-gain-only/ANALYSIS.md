---
type: Analysis
description: "What W-269's FAIL (drift) settles and what it leaves: the gain-only term removed W-236's short-document credit (G3) and improved the step10_section pool, but lost 2–5 baseline rank-1 hits at every λ. No change follows on main; the next step, if any, is Arpit's."
run: 2026-10-10-section-gain-only
item: W-269
filed: 2026-10-10
---

# Analysis — section records, gain-only, after the verdict

## 1 · What the run settled

- **W-236's diagnosis was right.** G3 shows that no sectionless document's
  term moves at any λ (0 failures, 4 × 1 481 comparisons), and the pool no
  longer gets worse: misses go 23 → 23 · 21 · 19 · 13, where W-236's went
  23 → 26 · 26 · 28 · 28. The short-document credit was what turned W-236's
  pool the wrong way.
- **That is not enough under the frozen bar.** Clause 2 allows zero new rank-1
  misses, and every λ has some: `s5c-009` and `s5c-060` from `0.25` up, plus
  `s5c-073` and `s5c-075` from `0.5` up, plus `s5c-024` at `2.0`
  ([`evidence/decision.json`](evidence/decision.json)). The losses grow
  slowly (2 → 5) while the wins grow fast (2 → 12). The table is still the
  ruling ([VERDICT](VERDICT.md)).

Repro, read-only, no key:

```bash
python3 work/regression/2026-10-10-section-gain-only/evidence/decide.py   # Arpit's run; writes decision.json + per-query.jsonl
python3 work/regression/2026-10-10-section-gain-only/evidence/describe.py # what moved, never whether it improved
```

## 2 · Specific changes

**None on `main`.** `section_weight` never reached it, and the bar's *On FAIL*
clause gives the branch (`claude/gracious-galileo-aqrg8b`) to Arpit. Recorded:
SR-SECTIONS §1 and decision 5, `compare/section-units`, the register row,
IMPLEMENTATION's prediction row.

If Arpit ever reopens the step, these are the candidate questions. Each would
need **its own pre-registration on a set this family has not tuned against**,
never a re-read of these 90:

| candidate | what it would test | why it is not a re-read |
|---|---|---|
| a clause-2 bar that admits losses below the d19 floor | whether +10 pool / −5 drift is acceptable | the bar is a ruling, and SR-RS d10b forbids moving this one |
| a gain cap (`G ≤ c · S_doc`) | whether the losses come from a few large gains | a new form; the frozen one may not be swept (§What this run may NOT do, 3) |
| `b` raised above 0.5 | the compare doc's own reopen trigger | a separate ruling that the item explicitly left untouched |

## 3 · Unresolved

- **Which documents took rank 1 on the five lost questions** is not examined.
  Whether they are long documents with one dense off-topic section (the bar's
  *hurts* row) is the obvious guess, and it is unverified. Reading it needs the
  hand-offs' `ranked` lists against document lengths, which needs no key:

  ```bash
  python3 - <<'PY'
  import json
  ev = "work/regression/2026-10-10-section-gain-only/evidence"
  ids = {"s5c-009", "s5c-024", "s5c-060", "s5c-073", "s5c-075"}
  for arm in ("sw-0.0", "sw-2.0"):
      for r in map(json.loads, open(f"{ev}/{arm}/rung-01000/handoff-set-5-claude.jsonl")):
          if r["id"] in ids:
              print(arm, r["id"], r["ranked"][:3])
  PY
  ```
- ⚠ `informed`, one Claude-authored set of 90, and the second mechanism on it.
