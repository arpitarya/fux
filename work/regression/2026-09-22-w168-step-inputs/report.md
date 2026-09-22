---
type: Report
description: "W-168's eight remaining steps, each checked against the input its own pre-registration would need, plus the headroom any ranking change has on this corpus. Four steps are input-blocked, one is foreclosed by a ruling, and every step faces a bar requiring 58-78% of all remaining failures fixed with zero regressions. No feature was built and none should be until the corpus moves."
run: 2026-09-22-w168-step-inputs
item: W-168
filed: 2026-09-22
classification: informed
---

# W-168 — what each remaining step is actually waiting on

**This run builds no feature, rules on no threshold and files no verdict.** It
applies W-168's own rule — *golden question(s) → pre-registration → build* — to
**all eight remaining steps at once**, because three separate sessions have now
each discovered one step's missing input the expensive way, one step at a time.

## 1 · The pool any ranking change can win

Computed from W-213's 2 992 captured rows, **answerable questions only**, with
the required net taken from `resolution.smallest_detectable` rather than copied:

| rung | set-1 pool → min_fix | set-2 pool → min_fix | set-3 pool → min_fix |
|---|---:|---:|---:|
| `rung-seed` | 7 → **7** | 14 → **10** | 12 → **8** |
| `rung-00100` | 11 → **9** | 15 → **9** | 17 → **9** |
| `rung-00500` | 10 → **8** | 20 → **10** | 17 → **9** |
| **`rung-01000`** | **9 → 7** | **21 → 11** | **17 → 9** |
| `rung-10000` | 12 → **8** | 23 → **11** | 18 → **10** |

🔴 **To produce a verdict, ONE ranking step must fix 7 to 11 of the 7 to 23
questions still failing — 58 % to 78 % of every remaining failure — with ZERO
regressions, in all three sets.**

⚠ **`min_fix` is a ceiling on optimism, not a prediction.** With `b` wins and
`c` losses the discordant count is `b + c` and the net is `b − c`, so the quoted
number is reachable **only** when nothing regresses. **No measured ranking
change in this repository has managed that**: W-205 part 2 family (a) came
closest at `+1 / +3 / +4` with 0 regressions, and returned INCONCLUSIVE.

🔴 **The corpus is close to saturated.** `hit@5` on answerable questions is
101–106 of 113 (set-1), 89–98 of 112 (set-2), 95–101 of 113 (set-3). **A feature
that fixes three real failures is a real improvement and returns
INCONCLUSIVE here.** That is the B1 finding — *"the null was determined by the
corpus"* — arriving before the arms run instead of after.

## 2 · Per step, the input its pre-registration would need

| step | idea | the input | measured | state |
|---|---|---|---|---|
| **1** | anchor-text field | a document findable **only** via a linker's wording | **1 anchor-distinctive term corpus-wide, and it is a filename** | 🔴 **blocked** — [the census](../2026-09-22-anchor-input-census/report.md) |
| **2** | identifier field | id-queries with headroom | **3–4 of 33, below the floor of 6** | 🔴 **stopped 2026-09-18**, already recorded |
| **3** | supersession-aware ranking | a superseded/successor pair | present — **and the mechanism is ruled out** | 🔴 **foreclosed**, see §3 |
| **4** | corpus-mined expansion | `Term (ABBR)`, glossary lines, `aliases:` | **0 / 1 (a false positive) / 3 on one document** | 🔴 **blocked** |
| **5** | RM3 | under-specified questions with a known answer | **no `23c` tag exists for it** | ⚠ unlabelled |
| **6** | SDM proximity in refer | phrase-sensitive questions | **no `23c` tag exists for it** | ⚠ unlabelled |
| **7** | community MMR | multi-facet questions, after the graph is in `ask` | **no `23c` tag exists for it** | ⚠ unlabelled |
| **8** | git authority prior | **a corpus with history** | the ladder is synthetic and rebuilt at one stamp | 🔴 **blocked by the proposal's own words** |
| **9** | intent → doc-type prior | intent-labelled questions | 🟢 **present and abundant** — see §4 | 🟡 the *doc-type* half is undeclared |
| **10** | section units | long-document questions; **its own compare doc first** | not started | ⚠ a plane change, its own major |

**Step 4's input, measured over all 28 seed documents:** `Term (ABBR)` pairs
**0**; glossary `term — definition` lines **1**, and it matches the word
*"copy"*; `aliases:` declarations **3**, all on `02-sensor-thresholds.yaml`
(`"Nagpur DC"`, `"Guwahati DC"`, `"Coimbatore DC"`). **Three alias pairs on one
document cannot produce seven flips.**

⚠ **set-3's `vocabulary_gap: 25` is real and is NOT step 4's input.** Those
questions are colloquial paraphrase — *"why did the old lorry pack up"* →
`a06-reefer-RF-117-retired.md` — which no `Term (ABBR)` miner reaches. **It is
the same collision as `link_dependent`:** a d23c tag that reads as a step's
input and is a different thing. Two of these in one corpus is a pattern.

## 3 · Step 3 is foreclosed by a ruling, not by data

The corpus **has** superseded/successor pairs. The mechanism is what is gone.

**[VERDICT-W143](../2026-09-12-priors-and-tables/VERDICT-W143.md), 2026-09-12**,
on Arpit's own pre-registered question — *does ANY single global value clear a
`0 broken` bar?* — answered **NO**, and the shape is the whole story:

| | current-seeking | history-seeking |
|---|---:|---:|
| shipped default | 11–12 / 13 | 8–9 / 13 |
| **any value that demotes** | **13 / 13** | **5 / 13, down to 0 / 13** |

> **Arpit, 2026-09-11:** *"`P-SUPERSEDE` did not fail because `0.5` was wrong…
> every broken query had the superseded document as its correct answer.
> **Supersession belongs to the query's intent, not to the document.**"*

`superseded_weight` was **removed** on 2026-09-13 (W-151) and `superseded` is a
tie-break now, reached only where rounded scores are equal.

🔴 **So step 3's lexical half is not unbuilt — it is un-built, deliberately, by
a ruling on a measurement.** Re-introducing it under a new name would walk back
that ruling, which no session does. Its two other halves are out of reach for
other reasons: the **walk** is W-161's graph-composed `ask`, explicitly *"out of
scope"* in W-168; the **anchor inheritance** reads step 1's fold, which §2 has
just measured as having nothing to inherit.

## 4 · Where the ruling points instead — and it has its input

W-143's sentence is a **redirection**, not only a refusal: *supersession belongs
to the query's intent*. And the intent labels exist:

| tag | set-2 | set-3 |
|---|---:|---:|
| `superseded:current_seeking` / `superseded_pair:current` | 20 | 30 |
| `superseded:history_seeking` / `superseded_pair:history` | 6 | 11 |
| `recency:newer_correct` | 9 | — |
| `recency:older_correct` | 12 | 18 |

plus `tools/quality-controls/priors-probes.jsonl`, the **13 current-seeking and
13 history-seeking** probes W-143 itself ran, whose truth is read off the
corpus's own `supersedes:` and `archived=true` declarations and which need **no
answer key at all**.

⚠ **That is an observation about where the evidence points, NOT a design and NOT
a licence to build one.** W-168 step 9 as written is *intent → **doc-type**,
declared per source*, which is a different mechanism from *intent → supersession
handling*, and the golden corpus declares no doc types. **Whether the two become
one step is a scoping decision, and it is not this run's.**

## 5 · What follows

🔴 **W-168 cannot proceed step-by-step against this corpus, and the blocker is
one deliverable rather than eight.** The next generation of golden data has to
be authored to *create headroom and supply each step's input*, or every step
repeats §1's arithmetic.

**What generation 2 owes W-168**, measured rather than guessed:

1. **Harder questions.** `hit@5` at 81–94 % leaves 7–23 winnable questions per
   set. **Questions that today's engine fails** are the only thing that makes
   any of steps 3–10 decidable.
2. **Anchor-only vocabulary** — a house nickname or acronym for a page that the
   page never uses about itself, plus a hub linked by many documents in
   unrelated words, plus questions phrased in the linker's words.
3. **`Term (ABBR)` and glossary lines**, with questions that use one form while
   the answering document spells out the other.
4. **Identifiers of the failing shape**, already specified on W-168 step 2.
5. **A `23c` tag per step, named for the step** — `link_dependent` and
   `vocabulary_gap` are both real tags that read as a step's input and are not
   it. **A tag whose meaning a later session can misread is worse than none**,
   because d23c exists precisely so coverage need not be re-derived.
6. **A corpus with real git history**, or step 8 stays a proposal — *"never
   ships unmeasured"*, the proposal's own words.

## Not a paired run, and no per-query rows

🔴 **No query was run and no arm was compared.** §1's figures are a
**re-reading of W-213's filed rows**, not a new measurement, so there are no new
per-query rows ([SR-RS](../../../records/0133_predictions.md) decision 15) and
no headroom to disclose per direction (decision 22) — **this run IS a headroom
disclosure**, computed before the arms it is about.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the seed corpus and the ladder | Codex | — |
| sets 2 and 3, and their `23c` tags | Claude | the seed |
| the two instruments, this report | **Claude Code (this session)** | the corpus, the retired questions and their expected values, W-213's rows |

**`informed`.** Every figure is a property of the corpus or a re-reading of an
already-`informed` run. **No claim about ranking quality is made.**

## Reproduce

```console
$ .venv/bin/python tools/quality-controls/ranking_headroom.py \
    --rows work/regression/2026-09-22-band-operating-point/evidence/per-query.jsonl
$ .venv/bin/python tools/quality-controls/ref_edge_census.py \
    --corpora ~/my_programs/fux-lab/arms/runs/w213-head
```

**Evidence:** [`evidence/headroom.json`](evidence/headroom.json) ·
[`evidence/headroom.txt`](evidence/headroom.txt) ·
[`evidence/step-inputs.txt`](evidence/step-inputs.txt).
