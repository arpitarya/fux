---
type: Report
description: "W-257 pilot - a blind Claude session enriched gen-4 rung-01000's seed/ scope (94 documents, enrich=true) in fux-lab: 745 questions written; fux enrich --check refused 237 on the first pass (31.8 percent), every one for 'does not retrieve its document', and passed only 17 of 94 documents clean. Surface capture, no verdict; token cost and wall clock are in the author's report, which Arpit holds."
run: 2026-10-09-enrich-pilot-gen4
item: W-257
classification: blind
filed: 2026-10-10
---

# Report: the enrichment pilot — first-pass `--check` refusal

**This is a surface capture, not a measurement against a bar.** No
pre-registration is owed for the pilot (W-257's ruling: it measures cost and
refusal, not doc2query). Not a paired run, so headroom does not apply.

## What ran (read from the environment, 2026-10-10)

- **Where:** `~/my_programs/fux-lab/enrich-pilot-gen4/`, a lab environment whose
  `repo/` is a copy of gen-4 `rung-01000` (git HEAD `e776146f`, the rung's).
  The only tracked change is `.fux/sources/dirs`: `seed  enrich=true`.
  `corpora/golden/` is untouched.
- **When:** 2026-10-09, by file times: environment 13:03, ingest 13:04, the 94
  enrichment files 13:05:54–13:08:26, `plan.txt`/`check.txt` 13:08.
- **Author:** one session, every file stamped `model: claude-opus-5-5`,
  `skill: fux-enrich@1`. It was launched by Arpit with W-257's blind prompt.
  ⚠ Its blindness rests on that launch; nothing in the environment can prove it.
- **Scope:** `seed` (**94 documents, 817 chunks**). ⚠ **The prompt asked for a
  40–60-document folder.** The rung's `dirs` declares only `seed` and `ext`
  (plus two archive lines), so no 40–60 folder existed. The author took the
  smaller live scope.

## The numbers ([`evidence/check.txt`](evidence/check.txt), [`evidence/plan.txt`](evidence/plan.txt))

| | |
|---|---:|
| documents planned · enrichment files written | 94 · 94 |
| questions written | **745** (7.9 per document) |
| questions refused by `fux enrich --check` (first pass, none rewritten) | **237 — 31.8 %** |
| documents with no refused question · with ≥ 1 | **17 · 77** |
| refusal reasons | **one**: *"does not retrieve its document (absent from the ranking, wanted top 3)"* |
| wall clock · token cost | **not in the environment**: they are in the author's report |

## Authorship

| artifact | author | could reach |
|---|---|---|
| the 745 questions | the blind pilot session (Opus 5.5), 2026-10-09 | the rung copy's own documents, by its prompt; no questions/, key or evidence path |
| this capture | Claude Code, 2026-10-10, a different session | `results/` and the enrichment files' counts and stamps; it rewrote nothing |
