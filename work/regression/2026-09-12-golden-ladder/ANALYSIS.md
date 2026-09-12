---
type: Analysis
description: "What the golden-ladder run diagnoses, turned into specific improvements with a repro command each, and what it leaves unresolved."
run: 2026-09-12-golden-ladder
item: W-136
classification: informed
filed: 2026-09-12
---

# Analysis — golden ladder, rungs seed → 1 000

**Read [`report.md`](report.md) first.** Everything below is diagnosis; the
measurements are there.

⚠ **Every item here is derived from ranked lists and corpus structure, not from
the answer key.** That is deliberate: it is what lets this analysis say
something while [W-145](../../open/W-145-codex-regenerates-the-key.md) is open.
**No item states a delta, and no item is a verdict.**

Repro commands run from `~/my_programs/fux-lab/corpora/golden/<rung>/` with
`~/my_programs/fux/.venv/bin/fux` on the path.

---

## 1. The abstention decision does not move, and the band does

**What was seen.** 0 of 124 questions reported `answerable: false`, on all five
rungs, while the key contains 12 unanswerable questions. The band *does* move —
39 of 124 land in `weak` at rung 1 000 — so the confidence machinery is
producing a signal. Nothing converts that signal into a refusal.

**Repro:**

```bash
cd ~/my_programs/fux-lab/corpora/golden/rung-01000
fux ask "acknowledging a tessaline alarm — what does that NOT do?" \
  --json --band --top 10 | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["confidence"])'
# {'band': 'weak', 'answerable': True, 'separation': 0.0,
#  'separation_floor': 0.1, 'coverage': 1.0, 'support': 10, ...}
```

That is question `g004`, and it is the shape of the whole finding in one line:
**`separation` is 0.0 against a floor of 0.1** — the ten results are
indistinguishable from each other — the band correctly reports `weak`, and
`answerable` is `true` anyway.

**Improvement, specific.** Decide — in a record, not in code first — whether
`weak` is intended to imply `answerable: false`, or whether abstention has a
separate gate that is currently unreachable on this corpus. The band table in
[`report.md`](report.md) §4.1 is the input to that decision.

⚠ **This is the third recorded occurrence of the same finding.** The open
blocker carries an abstention re-run at 20/20 with 0 flips, run twice. Under
CLAUDE.md §"Two strikes → a gate", a failure class the WORKLOG records twice
becomes a mechanical check in the change that records the second occurrence —
and this is past two. **That gate is owed, and it is not written.** It is not
written *here* because what the gate should assert is the very thing the record
has not decided; writing a check against an undecided contract is how W-83
happened. The decision is named in §5 as the one thing that blocks it.

---

## 2. `superseded_weight` is landing at about a coin flip

**What was seen.** Across ranked lists where both halves of a declared
supersession pair appear, the retired half is above its successor in 51–58 % of
them, on every rung ([`report.md`](report.md) §4.2). The index carries the
`superseded` flag on all four retired seed documents, so the input is present
and the prior is being applied to something.

**Repro** — the clearest single pair:

```bash
cd ~/my_programs/fux-lab/corpora/golden/rung-seed
fux ask "what is the diesel surcharge percentage" --json --top 10 \
  | python3 -c 'import json,sys
for i,r in enumerate(json.load(sys.stdin)["results"],1): print(i, r["loc"], round(r["score"],3))'
# 1 seed/07-rate-card-and-surcharges.md  6.257   <- RETIRED
# 2 seed/12-rate-card-2026-h2.md         6.145   <- supersedes: 07
```

The retired card is first by 0.112 of a score point, and the document that
declares `supersedes:` on it is second.

⚠ **`fux answer` does not inherit the inversion, and that matters.** On the same
question it returns `seed/12-rate-card-2026-h2.md:L28-L32` — *"6.25% when HSD
exceeds Rs. 92/litre"*, the current rule — with the retired card's passage
second. Passage re-scoring on the fetched bytes puts it right where document
ranking did not.

So the finding is narrower and more precise than "supersession is broken":
**the document plane inverts and the passage plane recovers.** Which endpoint a
caller reads decides whether the inversion is visible at all — `fux find` and
`fux ask`'s ranked list expose it, `fux answer` here did not. Any sweep of
`superseded_weight` must therefore name its endpoint before it runs, or it will
measure two different things and average them.

**Improvement, specific.** This is the corpus [W-143](../../open/W-143-four-no-op-priors.md)
was blocked for. The open blocker says the four-priors remeasure **cannot run**
because the playground declares no `supersedes:` on any branch of its history,
and names *"build a purpose-made corpus"* as option (b). **That corpus now
exists and is frozen**: 145 co-ranked pairs at `rung-seed`, 4 declared seed
pairs plus 98 declared `ext/` pairs at rung 1 000, all confirmed in the built
index rather than in the source files.

So W-143's remeasure is runnable on `rung-seed` and `rung-00100` — a sweep of
`superseded_weight` against the inversion count, which is a **key-free**
endpoint and therefore **not** contaminated by W-145. That is the one
measurement this ladder can produce today that nobody has to caveat.

⚠ **It still needs its own pre-registration**, written before the sweep. This
analysis does not authorise a threshold.

---

## 3. Thirty questions have no seed document in their top 5 at rung 1 000

**What was seen.** `hit@5 ≤ 94/124` at rung 1 000, by structure, before anyone
scores anything ([`report.md`](report.md) §5). The ids:

```
g005 g013 g014 g019 g021 g032 g036 g038 g041 g042 g044 g050 g054 g056
g058 g060 g066 g078 g083 g084 g102 g103 g106 g107 g110 g111 g120 g122
g123 g124
```

**Repro:**

```bash
cd ~/my_programs/fux/work/regression/2026-09-12-golden-ladder
awk -F'\t' '$2=="rung-01000"' evidence/per-question.tsv \
  | awk -F'\t' '$5 !~ /^seed\// && $6 !~ /^seed\// && $7 !~ /^seed\// \
                && $8 !~ /^seed\// && $9 !~ /^seed\// {print $1}'
```

**Diagnosis, honest about its limit.** The `ext/sibling/` documents reuse the
seed documents' headings and document types with a different company and every
number changed — that is what they are *for*, and the `heading` negative
control row in [`work/golden/README.md`](../../golden/README.md) declares them
as exactly that. So a distractor outranking the answer is the control working,
**and** a possible ranking defect, and this run cannot tell those two apart.

**What would tell them apart, specifically:** re-run these thirty ids on
`rung-01000` with `ext/` excluded from `.fux/sources/dirs` in a scratch copy. An
id that finds its answer with the distractors removed is a ranking failure; an
id that does not was never going to be answered and the distractors are
incidental. **That is a separate run with its own pre-registration**, not a
number to add to this one.

---

## 4. `rung-seed` saturates and must not be used as a discriminating rung

**What was seen.** At `rung-seed` every top-1 is trivially a `seed/` path —
there is nothing else in the corpus — so the improvement direction has **zero
headroom** and is Inconclusive there per ADR-RS decision 22d, not "no detected
change".

**Improvement, specific.** Any future run that wants a ranking endpoint should
start at `rung-00100`. `rung-seed` remains useful for exactly one thing: the
supersession-inversion endpoint in §2, which has its largest co-ranked
population there (145) precisely *because* nothing else competes.

This is the same saturation that made the 2026-08-28 `heading` control "pass"
while testing nothing. Recording it here so the next session does not rediscover
it at the cost of a run.

---

## 5. Unresolved, stated as unresolved

1. **Whether `weak` should imply `answerable: false`.** Undecided in any record.
   Until it is, the abstention gate §1 owes cannot be written against anything.
   **This is the single decision that unblocks the most here.**
2. **Whether the thirty ids in §3 are ranking failures or the negative control
   working.** Not decidable from this run; §3 names the run that would decide it.
3. **What `superseded_weight` value, if any, clears the inversion count.** Not
   swept here. W-143's job, with its own pre-registration.
4. **Everything the key would answer** — `hit@1`, `hit@5`, `recall@5`,
   `rank_first_relevant`, `abstain_correct`. Codex's, in phase 5, and `informed`
   until W-145 closes.
5. **Rungs 2 000, 5 000 and 10 000 are not built.** Nothing here extrapolates to
   them, and the 2026-08-22 ceiling forbids anything above 10 000 entirely.

---

## 6. What changed in this session's own tooling

A defect in the corpus generator is recorded because it is the kind that passes
every check that exists: some supersession **superseders silently dropped their
`supersedes:` frontmatter**, because the template that rendered them emits no
frontmatter at all. The target-existence check could not see it — every
remaining target still existed, so the manifest, the coverage file and the index
all agreed with each other and with nothing true.

`make_golden_ext.py --check` now counts **pairs**, not targets: every retired
document must have exactly one superseder, and no target may be claimed twice.
That is the check that catches it, and it is the reason §2's inversion counts
can be trusted to be counting what they say.

---

## Reference

- The run: [`report.md`](report.md) · [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md)
- The answers: [`ANSWERS-FOR-REVIEW.md`](ANSWERS-FOR-REVIEW.md)
- The corpus this unblocks: [W-143](../../open/W-143-four-no-op-priors.md)
- Headroom, saturation, test-data coverage:
  [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 22, 23
