---
type: Evidence
description: "W-221: RM3's lexical first pass vs the graph-boosted top 10 `ask` shows, on rung-01000 / set-2-u. The documents mostly agree; the feedback terms RM3 learns from them agree on only half the questions. Ambiguous under W-221's two outcomes, so it goes to Arpit."
run: 2026-09-23-rm3
item: W-221
filed: 2026-09-25
---

# First-pass check: lexical vs graph-boosted top 10

🔴 **No key and no score was read.** This compares two rankings with each other,
never with a relevance judgment. Script: [`first_pass_check.py`](first_pass_check.py).
Per-question rows: [`first-pass-check.jsonl`](first-pass-check.jsonl).

## What ran

- **Where:** the `rm3-0.0` arm copy of `rung-01000` (root `17fe414e…`, `ask_boost = true`), all 125 `set-2-u` questions, of which 92 are tagged `rm3_underspecified`.
- **Engine:** the working tree at `02d5f133`. The arm's `tune.toml` pins `anchor = 0.0`, so the step-1 default change does not apply.
- **Reproduction check:** the recomputed boosted top 10 equals the arm's captured `ranked` list on **125 of 125** questions.
- **The lexical list is RM3's actual input.** It is `trace_out["window"][:10]`, the same un-expanded lexical call that `run_query`'s `rm3_weight > 0` branch makes.

## 1 · The ten documents

| | all 125 | tagged 92 |
|---|---:|---:|
| identical list | 26 | 21 |
| same set, reordered | 26 | 21 |
| **different membership** | **73** | **50** |
| rank 1 the same | 124 | 92 |
| documents shared, median | 9 of 10 | 9 of 10 |
| documents shared, distribution | 10: 52 · 9: 40 · 8: 24 · 7: 6 · 6: 2 · 5: 1 | 10: 42 · 9: 24 · 8: 19 · 7: 5 · 6: 2 |

- **Every lexical document that the boost displaces sits at lexical rank 6–10.** The counts by rank are 6: 14 · 7: 18 · 8: 18 · 9: 28 · 10: 41, for 119 displacements in total.
- The top-5 set is the same on 97 of 125 questions.
- **The typical swap:** the boost drops generic neighbours (`ext/sibling/*-postmortem.md`, `*-decision.md`) and brings in linked `seed/` documents.

## 2 · The ten feedback terms, which is what RM3 actually uses

Both top-10 lists were fed to `rm3.feedback_terms`. The boosted ten carry their **lexical** scores, because that is the only score `P(q|d)` is defined on.

| terms shared (of 10) | all 125 | tagged 92 |
|---|---:|---:|
| 10 | 62 | 47 |
| 9 | 28 | 19 |
| 8 | 14 | 9 |
| 7 | 14 | 12 |
| 6 | 5 | 4 |
| 4 | 2 | 1 |

- **The same ten terms on 62 questions.** At most one term differs on 90 of 125. **Two to six terms differ on 35, and 26 of those are tagged.**
- Every question with identical or reordered documents has the identical term set. Every term change comes from the 73 questions whose document membership differs.

## Worked examples

- **`s2u-037`, tagged, 6 of 10 documents shared.** The lexical ranks 6–9 are four `ext/sibling/*-postmortem.md` files. The boosted list replaces them with `seed/18-reefer-RF-120-asset-file.md`, `seed/02-sensor-thresholds.yaml`, `seed/08-driver-hours-and-safety-policy.md` and `seed/01-sop-temperature-excursion.md`.
- **`s2u-077`, untagged, 5 of 10 shared.** The lexical ranks 6–10 are five sibling postmortems. The boosted list replaces them with five `seed/` documents. This is the only question with 5 in common.
- **`s2u-076`, untagged, 9 of 10 shared.** This is the one rank-1 swap: `22-cold-chain-document-map.md` rises above `a05-induction-checklist-2020.txt`.

## Reading, and why this is not called either way

W-221 names two outcomes. **This result matches neither cleanly.**

- **The case for "largely the same":**
  - Rank 1 is the same on every tagged question.
  - The median overlap is 9 of 10.
  - Every difference is in the bottom half of the list, where `P(q|d)` gives a document the least weight.
- **The case for "meaningfully different":**
  - 73 of 125 questions have a different feedback **set**.
  - On 35 questions, 26 of them tagged, RM3 would learn 2 to 6 different expansion terms of its ten.
  - The swapped-in documents are exactly the linked `seed/` documents the boost exists to surface.

**Whether a re-run against the boosted list would move the FAIL is not knowable from this capture.** Drift broke at every weight. Different terms on about a quarter of the questions could change that or could leave it where it is. Per W-221 §Hazards, the ambiguity goes to Arpit.
