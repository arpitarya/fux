---
type: Note
description: "W-257 DoD 3, stopped at a pre-registered STOP before any arm was scored. The full rung was authored (1,000 files, 5,620 questions; first-pass --check refused 837, reproduced line for line on the pinned engine). G0, G1, the archived gate and G3 pass. The placebo gate fails: placebo.py writes one word-matched line per file, the author's files have a median of 5 question lines, and the pre-registration says the run stops there and the gap goes to Arpit. A second issue goes with it: the author had no fux-enrich skill, so the questions are one per chunk and partly template-filled, unlike the pilot."
run: 2026-10-10-enriched-rung
item: W-257
filed: 2026-10-10
measured: "not yet: no arm captured, no question-set number exists"
---

# Gates before the arms: one STOP, four passes

✅ **The STOP was ruled the same day** (Arpit: *"go with the recommended
approach"*). See [AMENDMENT.md](AMENDMENT.md) and the capture in [report.md](report.md).

**No arm has been run against the question set.** No harness call, no
`score.py`, and no number on `set-5-claude` exists. That is why this is a note
and not a `report.md` (the per-run contract's half-empty directory still
holds). The frozen bar is [PRE-REGISTRATION.md](PRE-REGISTRATION.md), unchanged.

## What was handed in

The blind author's report, relayed by Arpit in chat on 2026-10-10. Read from
`~/my_programs/fux-lab/enrich-full-gen4/`:

| | |
|---|---:|
| documents planned · files written | 1,000 · 1,000 (all four scopes, `seed`, `seed/archive`, `ext`, `ext/archive`) |
| questions | **5,620**, one per chunk. Per file: min 1 · median 5 · max 26 |
| refused on the first pass ([`evidence/check-first-pass.txt`](evidence/check-first-pass.txt)) | **837 (14.9 %)**, in 357 files. One reason only: *"does not retrieve its document … wanted top 3"* |
| file stamps | `model: claude-opus-5-5` on all 1,000 · `skill: fux-enrich` on all 1,000 (the pilot's were `fux-enrich@1`) |
| wall clock · tokens (the author's report, not on disk) | ≈ 15.6 min (937 s) · ≈ 1.17 M subagent tokens over 11 authors + ≈ 110 k coordination |

## The engine and the arms built so far

- **Engine:** `a07f9329` (`fux 3.0.0-alpha.11`), a detached worktree with its
  own venv in the session scratchpad. `src/` last changed at `0fec04d1`
  (2026-10-09 19:38). The author ran 2026-10-10 00:30–00:46 through the fux
  repo's editable install, so **the author's engine and this one are the same
  source**.
- **Arms built:** `none`, `declared`, `unfiltered` under
  `~/my_programs/fux-lab/arms/runs/w257/`, each a `cp -a` of `rung-01000` at
  `e776146f`. `diff -r` (outside `.git/`) shows only `.fux/sources/dirs` between
  `none` and `declared`, and only `.fux/enrich/` between `declared` and
  `unfiltered`. `unfiltered/.fux/enrich/` is `diff -rq`-identical to the
  author's. Each was ingested `--full`.
- `filtered`, `placebo`, `cov-25` and `cov-50` are **not built**.

## The gates

| gate | result | evidence |
|---|---|---|
| **`archived` refusal** | **pass**: `--plan` with `enrich=true` beside `archived=true` plans all four scopes and 1,000 documents | [`evidence/plan-g-archived.txt`](evidence/plan-g-archived.txt) |
| **G0**, declaration is a no-op | **pass**: the committed `.fux/index/` of `declared` is byte-identical to `none`'s and to the rung's (sha256 of the concatenated shards `49ddce51…` for all three). Ingest reads enrichment by document sha and never consults the declaration (`ingest/run.py` `_enrichment_for`) | below |
| **G1**, every file valid | **pass**: `--check` on the ingested `unfiltered` names no malformed file, no sha mismatch and no PII hit | [`evidence/check-g1-ingested.txt`](evidence/check-g1-ingested.txt) |
| **G3**, the filter is visible | **pass**: 837 / 5,620 = **14.9 % ≥ 10 %** | `check-first-pass.txt` |
| **placebo line count** | 🔴 **STOP**: see below | — |
| G2, headroom | not read: it is read on the `none` arm's harness output, which does not exist | — |

**One reading to keep straight.** `--check` on the **ingested** `unfiltered`
refuses **761**, not 837. On an **un-ingested** copy with the same files (the
author's state), it refuses **837, the same lines exactly**
([`evidence/check-repro-uningested.txt`](evidence/check-repro-uningested.txt)).
So the first pass reproduces. The difference is index state: with `ctx`
zeroed, the enrichment still changes document frequencies and lengths. The
`filtered` arm is built from the author's first pass, as frozen. The 761 is a
G1 by-product and is never a second pass.

## 🔴 The STOP: the placebo cannot match line count

The pre-registration's `placebo` arm is *"matched file count, line count and
length, one shared pool"*, and *"if `placebo.py` cannot match line count on
question-shaped bodies, the run stops and the gap goes to Arpit. The control is
not loosened to fit."*

[`placebo.py`](../../../tools/quality-controls/placebo.py) matches **word
count** and writes the body as **one line**. The author's files carry a median
of 5 question lines (1–26). It also swaps its marker only for
`skill: fux-enrich@1`, and these files say `skill: fux-enrich`, so every placebo
would keep the real stamp. The frontmatter is stripped before indexing, so that
mislabels the file and changes no term. But it is a second defect in the same
control.

**The STOP blocks B-108 only.** B-109 (`filtered` vs `unfiltered`) and B-110
(`cov-c` vs `cov-100`) need no placebo. The pre-registration says *"the run
stops"*, though, and does not split it. So nothing runs until Arpit rules.

## The second issue: the author ran without the skill

The full-rung brief, like the pilot's, said *"Follow the fux-enrich skill
(.claude/skills/fux-enrich; if absent, `fux enrich --help`)"*. The pilot had the
skill (`fux-enrich@1`, 7.9 questions per document, hand-written). The full rung
did not, because it is not in `fux-lab`. So:

- **One question per chunk, by the author's own choice.** 5.6 per document
  overall, against the pilot's 7.9 and the pre-registration's framing of
  *"5–10"*.
- **Template-filled questions** on the near-identical `ext` documents: the
  authors read each file and filled fixed patterns with its values. Most
  `ext/adjacent` refusals are those patterns (*"Who owns the Month-end close
  checklist — <org>, which department … in_force from <date>?"*). Seed and the
  one-off documents were written by hand.
- `- ` bullets on every line. `is_question` strips them, `--check` reads them,
  and G1 passes.

The ruling was *"instructions unchanged"*, and the instructions were unchanged.
The environment was not. A B-108 verdict on these files measures **doc2query as
written without the skill**, which is not the shipped workflow. Whether that is
the measurement Arpit wants is his call, and nothing here adjudicates it
(pre-registration rule 6).

## Two incidents the author reported, recorded and not judged

1. The auto-mode classifier blocked one author's `cat` of two `ext/adjacent`
   files (*"PII Data Handling"*), and that author read them with the Read tool
   instead. The corpus is synthetic.
2. One author used `ext/sibling/00000-sop.md`, from another batch, as a template
   reference. It says no text from that file went into a question.

The author reports that no forbidden path was opened and that `corpora/golden/`
was not modified. **Nothing in the environment can prove its blindness**, the
same caveat as the pilot's.

## Repro

```bash
F=<worktree at a07f9329>/.venv/bin/fux; A=~/my_programs/fux-lab/arms/runs/w257
(cd $A/declared && $F enrich --plan)                    # archived gate
for a in none declared unfiltered; do (cd $A/$a && $F ingest --full); done
for a in none declared; do cat $A/$a/.fux/index/*.jsonl | shasum -a 256; done   # G0
(cd $A/unfiltered && $F enrich --check)                 # G1 (761: ingested state)
python3 -I tools/quality-controls/placebo.py $A/unfiltered/.fux/enrich /tmp/p  # one line per body
```
