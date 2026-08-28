---
type: Analysis
name: 2026-08-28-benchmark-contested-analysis
description: "How the contested suite was built, why each design choice was forced, what each finding does and does not license, and the two defects this run found in its own instrument."
---

# Analysis — the contested-answer suite, and what it found

## 1. Why the marker suite had to be replaced, in one paragraph

A term planted in exactly one document has `df = 1`. It is the easiest retrieval
problem BM25 has, it is already rank 1, and **no ranking change can move it up
or break it**. In McNemar's terms `pb` and `pc` are structurally zero, so the
discordant count is fixed by the corpus before either engine runs. The
2026-08-28 benchmark sized that set correctly at `N = 240` and still could not
detect anything. **A power table says how many queries; it never says whether
the queries are hard.** This run reproduces the saturation on a fresh corpus —
`hit@5` 120/120 in both arms — which confirms the diagnosis rather than assuming
it.

## 2. The design, and the confound each choice removes

The contest must be decided by **one** property. Everything else has to be equal,
or the target wins for a reason that is not the property under test.

| choice | the confound it removes |
|---|---|
| Every candidate carries each query term **exactly once** | tf. A candidate carrying it twice wins on term evidence before the ranker runs. |
| Two planted sentences of **identical shape and word count** in every candidate | length normalisation. The target must not be shorter. |
| **Fixed** section count, sentence count and sentence length across a cluster | body-length noise between candidates. |
| Cluster members get **unrelated document numbers** from the seeded stream | path tie-breaking. Near-identical candidates are exactly where an engine ordering ties by path scores 0 % or 100 % and the number measures `sorted()`. |
| `--selftest` **asserts** all of the above and halts | the assumption itself. This is the difference between an instrument and a hope. |

**The proximity design specifically.** Target: `The a b procedure applies here.`
plus `The <common> <common> procedure applies here.` Distractor: `The a <common>
procedure applies here.` plus `The b <common> procedure applies here.` Same
sentence count, same word count, same per-term frequency. **The only difference
is whether `a` and `b` share a sentence.** A bag-of-words ranker has nothing to
prefer the target on — confirmed empirically: both bag-of-words arms landed at
21.7 % against a 25 % chance level.

## 3. Why `path` and not `heading` is the version discriminator

Read from source before the run:

- `1.0.0` commits **two** tf fields: `body` 1.0, `heading` 3.0.
- `HEAD` commits **five**: `body` 1.0, `heading` 3.0, `title` 2.0, `path` 1.5, `ctx` 1.0.

So a heading contest is decided by a field **both arms already have, at the same
weight** — which is why it was pre-registered as a control rather than an
endpoint. `path` is the field one arm has and the other does not, and unlike the
ranking priors it is **structural**: there is no knob that ships it off. An
instrument-wiring check before the run confirmed the asymmetry is real — arm A
could not retrieve a filename-only marker at all; arm B ranked it 1.

## 4. What the three results license

**C1 (null, 94 queries of headroom).** Licenses: *on shipped defaults, `HEAD`
does not separate these clusters any better than `1.0.0`.* Does **not** license
*the engines retrieve equally well* — a null with headroom is a stronger
statement than a null without one, and still not equality. The mechanism was
named in advance (`rerank_weight = 0.0`), so this is a confirmation, not a
post-hoc rescue of a disappointing number.

**C2 (b = 94, c = 0).** Licenses: *the proximity machinery does the job it was
built for on a corpus designed to let it.* Does **not** license lowering or
raising any default. `c = 0` is a property of the generator: every planted
target **is** the co-occurrence, so the document that should win *without*
co-occurrence does not exist in this corpus and cannot be broken. `P-SUPERSEDE`
is the standing precedent for what happens when that limit is ignored, and the
hand-graded playground is what caught it.

🔴 **A citation defect found on the way, worth fixing at the source.**
[`VERDICT.md` for P-SUPERSEDE](../2026-08-25-supersession-and-reranker-default/VERDICT.md)
records `superseded_weight = 0.5` as fixing **two** queries (`q015`, `q049`) and
breaking two (`q022`, `q033`). **`work/OPEN-WORK.md` and the v1-vs-HEAD
presentation both say it "fixed one query and broke two."** The verdict is the
primary evidence and the derived documents are wrong. The ruling is unaffected —
the bar was *0 broken*, and two breaks fail it either way — but a load-bearing
claim quoted at the wrong magnitude in two places is the same class of defect as
an ADR whose amendment contradicts itself.

⚠ **And the magnitude of C2 is inflated by construction.** The reranker's value
on **hand-graded** text is on record and small: `28 → 32`, **+4 fixed, 0
broken**, itself `informed` and below the resolution floor. This suite rewards
exactly what the reranker does, so `94/120` establishes that the machinery
**functions** — never that it is worth 78 points. **The hand-graded `+4` remains
the better estimate of real value**, for precisely the reason the hand-graded
supersession result outranked the generated one.

**C3 (b = 60, c = 0).** Licenses: *`HEAD` can retrieve a document by a token
that appears only in its filename; `1.0.0` cannot.* Does **not** license *`HEAD`
ranks better*. The contest is decided by a field arm A does not have, which is
close to tautological, and reporting it as a ranking win would flatter B on a
question nobody asked.

## 5. Two defects this run found in its own instrument

🔴 **The `heading` control saturated.** It was built to be able to fail and
could not: 100 % in both arms, **zero headroom**. It returned the predicted null
for the wrong reason, so it did not discharge its purpose, and C1 and C3
therefore rest on the generator's assertions rather than on a live control.
Verdict downgraded to **Inconclusive**. The fix is a control with headroom by
construction — for instance a heading contest where the distractors are *also*
heading-matched so the contest is genuinely close. **The headroom column is what
caught this**, which is the strongest available argument that the column belongs
in every future run.

⚠ **The cross-seed "null control" is weaker than its name.** Query ids are
positional, so pairing arm A on seed 12 against arm A on seed 13 compares
*different questions* and its discordant count is not a determinism check. The
determinism check is the **same-corpus repeat** (380/380 substantive rows
identical), and that is what C5 was ruled on. The cross-seed comparison is
reported descriptively only — rates 21.7 % vs 20.0 % on proximity, 0 % vs 0 % on
path, 100 % vs 100 % on heading. **The previous run's B9 has the same
weakness**, and its "0 discordant of 240" across two seeds should be read as a
rate check rather than as evidence of determinism.

## 6. What this changes for the next run

1. **Every paired run declares headroom beside power.** Two of this run's four
   suites could not detect anything at any sample size, and the table said so
   before a p-value was quoted.
2. **A control must be checked for headroom too.** A control with none is
   decoration.
3. **`rerank_weight` shipping off was already on record**
   ([2026-08-25](../2026-08-25-supersession-and-reranker-default/report.md);
   `P-RERANK-DEFAULT` was withdrawn as mis-framed). This run adds a
   headroom-asserted measurement and the *pattern*, and must not be cited as
   discovering the default.
4. **Shipped-default version comparisons are close to exhausted as ranking
   questions.** Every ranking prior `HEAD` added is off at the default, so on
   ranking priors B-core *is* A. The open questions are (a) do the priors help
   on a **hand-graded** corpus, and (b) should any default move — and (b) is
   Arpit's call, not a benchmark's.
5. **A `blind` run still does not exist.** This run is `informed` for the same
   structural reason as the last one, and W-96 is what fixes it.
