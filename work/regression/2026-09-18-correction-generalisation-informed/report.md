---
type: Report
run: 2026-09-18-correction-generalisation-informed
item: W-175
classification: informed
description: "Arm (ii)'s corpus, Claude as the author of BOTH the corrections and the paraphrases, on Arpit's instruction. 12 corrections, 60 paraphrases, top-3 before/after: 0 discordant, net 0. Rank@20 shows the mechanism moved every correction's OWN question (12/12 up) and 3 of 60 paraphrases. NOT the pre-registration's blind arm; rules on nothing."
filed: 2026-09-18
engine_commit: 7259bab7
---

# REPORT — does a correction generalise? (informed, Claude-authored)

🔴 **Read the first line before the numbers.** This run is **`informed`** twice
over: the corrections and the paraphrases were both written by the session that
measured them, and the corpus is fux's own tree. **It is not the arm the
[pre-registration](../2026-09-15-correction-generalisation/PRE-REGISTRATION.md)
froze** — that arm's paraphrases are Codex's and blind — **so it files no
`VERDICT.md` and settles nothing about keep/remove.** It exists because Arpit
asked for it (*"you go ahead and generate a set of questions and answers, and
then try to test it out"*) and it is filed as what it is.

## The question

`fux correct` writes a human question line onto the document that answers it,
into the `ctx` field. The compare doc chose it over an editorial pin on one
claim: it **generalises to phrasings other than its own**. Does it?

## The number, in the frozen endpoint

**Top-3 retrieval of the corrected document, on each paraphrase, before vs
after the correction is filed and re-ingested.** 12 corrections × 5
paraphrases = 60 pairs, arm (ii)'s corpus (96 documents: `records/` + `docs/`).

```
 arm     n  before  after  better  worse  discordant    net
  ii    60      20     20       0      0           0     +0

headroom (SR-RS 22b/22f), measured in the BASELINE arm:
  improvement   40/60    regression   20/60
```

- **0 discordant.** Not one paraphrase crossed the top-3 line in either
  direction. Under the frozen table that is the *impossible* row — no net can
  clear α at 0 flips — which reads as a measured null, not an inconclusive.
- **Both headroom directions are non-zero** (40 could improve, 20 could
  regress), so SR-RS 22d does not fire: the null is not a ceiling artefact.

## What the graded view adds — the mechanism is alive and does not transfer

The binary endpoint hides where the target moved. Rank of the corrected
document at `--top 20`, before → after:

| | improved | worsened | unchanged |
|---|---:|---:|---:|
| **the correction's OWN question** (12) | **12** | 0 | 0 |
| **the paraphrases** (60) | **3** | 0 | **57** |

Own-question moves: `None→18`, `20→5`, `8→4`, `None→5`, `None→2`, `None→11`,
`15→9`, `5→1`, `12→7`, `19→3`, `14→4`, `5→1`. **Every correction lifted its own
phrasing, four of twelve into the top 3.** The three paraphrase moves were
`None→12`, `10→9` and `3→1` — two of them on CG-04, whose paraphrases happen to
share *stale* / *re-download* vocabulary with the correction line.

**Reading:** a `ctx` line at weight 1.0 behaves like a pin with a weak weight.
It helps exactly the words it contains. A paraphrase gains only where it shares
tokens with the correction that the document body lacks — which is the
mechanism working as built, and it is claim **(a)** from the compare doc: *"one
phrasing fixed, the next still wrong."*

## Two things this run cannot say, and one it can

- **It cannot rule keep/remove.** The blindness condition is unmet. A blind
  Codex paraphraser may write closer paraphrases than these — the ones here were
  written to differ in vocabulary, which is the definition of the test but also
  the hardest case for lexical transfer. **The Codex arm is still the one that
  decides.**
- **It cannot run the tilt check** — that needs golden questions and a key.
- **It can say the mechanism's ceiling is low at `ctx = 1.0`:** even the
  correction's own question reaches top-3 only 4 times in 12 on a 96-document
  corpus. Whatever the blind arm finds about transfer, **a correction that
  cannot fix its own phrasing 8 times in 12 is a separate finding**, and it is
  a weight question before it is a generalisation question.

## Authorship

| artifact | author | could reach |
|---|---|---|
| candidate questions (45) | Claude, this session | the corpus (it is fux's own records) |
| the 12 corrections (= the 12 real misses chosen) | Claude, this session | the before-scores, by construction — a miss was the selection rule |
| the 60 paraphrases | Claude, this session | the correction text, the target document's name; **not** the document bodies (unread in this session), **not** any per-paraphrase score before writing |
| the harness | `tools/quality-controls/correction_generalisation.py`, unchanged | — |
| the analysis | Claude, this session | everything above |

**`informed`**, and never compared with a blind run or used to state a delta.

## Side observations, not claims

- **29 of 45 intent-phrased questions over fux's own records missed the top
  3** (hit@3 = 36 %) on the baseline. Claude-authored, so informed — but a
  64 % miss rate on a 96-document corpus of the project's own decision records is
  worth a line in W-168's ledger.
- `--why` on a miss shows the top three matching on `does, tool, refuse, call,
  network, own` — function-word-heavy overlap winning over the record that
  answers. The analyzer's stopword coverage is thin for question-shaped input.

## Reproduce

`evidence/repro.sh` — builds everything under `$TMPDIR`, never inside the repo,
and never touches `work/`. Engine `7259bab7`, `fux 3.0.0-alpha.1`, Python 3.12,
Linux (the Cowork bridge VM).
