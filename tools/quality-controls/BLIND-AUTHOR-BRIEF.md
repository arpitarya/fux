---
type: Brief
name: BLIND-AUTHOR-BRIEF
description: "The exact, auditable instructions given to whoever authors the `unanswerable` class. Committed so the brief itself can be checked for leaks, because it was written by a session that had read everything the author must not see."
timestamp: 2026-08-28T00:00:00Z
---

# The blind author's brief — `unanswerable`

**Ruled by Arpit 2026-08-28:** a fresh session, given the corpus and nothing
else, with **this prompt committed so anyone can audit what the author was
told.**

## ⚠ Read this part first: why the brief is in the repository

[ADR-RS](../../docs/adr/0036_predictions.md) decision 11 defines **blind** as
authored with no access to the evaluation queries, the judgments, prior
per-query scores, or any derived report of them. A fresh session given only the
corpus satisfies that literally.

🔴 **But the prompt is a leak channel, and the prompt's author is not blind.**
This file was written by a session that had read the goldens, the decoys, the
`known_failure` list and four runs of per-query scores. A single steer —
*"avoid topics like X"*, *"make them hard"*, *"here is an example"* — would
launder that knowledge into a slot whose only value is that it was not there.

**So the mitigation is not trust, it is publication.** The brief is committed,
it is short enough to read in full, and **the check is that it contains no
corpus topic, no example question, and no difficulty steer.** If a later reader
finds one, the class it produced is `informed` and must be relabelled.

⚠ **This does not make the class blind by fiat.** It makes the claim
**checkable**, which is the same thing `seal.py` buys and the same limit it
has.

## What the author may see

| may see | must NOT see |
|---|---|
| the ten corpus documents, in full | `goldens/queries.jsonl` — any of it |
| the fux CLI and its output shapes | `tools/quality-controls/decoys.jsonl` |
| this brief | any run report, verdict, or per-query score |
| | the `known_failure` list, or which queries are sealed |

**Reading the corpus is required, not merely allowed.** A question that is
unanswerable *and* implausible for the domain tests nothing — a system declines
it for the wrong reason. Plausibility can only come from knowing the subject
matter, and the corpus is not evaluation material.

## The task, stated without steering

> Read the ten documents in this corpus. Write **20 questions that a person
> working in this domain would plausibly ask, and that these ten documents
> cannot answer.**
>
> A question qualifies only if **nothing in the corpus answers it** — not
> partially, not by inference from two documents together. If you find yourself
> reasoning *"well, document 4 sort of implies it"*, it does not qualify.
>
> Aim for questions that sit **close to what the corpus does cover** rather than
> far from it. A question about an unrelated industry is trivially unanswerable
> and tests nothing.
>
> Output one JSON object per line:
>
>     {"id": "u001", "query": "<the question>", "expect_empty": true}
>
> `id` runs `u001`..`u020`. Do not add fields. Do not explain your choices in
> the file — a rationale is a judgment about the corpus, and judgments are what
> this class must not carry.

## ⚠ The three things this brief deliberately does not say

Each was considered and left out, and the reason matters more than the omission:

1. **No example question.** One example fixes the register, the length and the
   flavour of all twenty, and the example would come from a session that had
   read the decoys.
2. **No difficulty target.** *"Make them hard"* and *"make them realistic"* both
   shape the difficulty distribution, which is **exactly what an informed author
   fits** even with no correct answer to fit to. This is the claim the
   `quality-controls` README got wrong until 2026-08-28.
3. **No topic list, positive or negative.** *"Avoid X"* leaks the goldens as
   surely as *"cover X"* would.

## Validating what comes back

🔴 **CORRECTED 2026-08-28, on the first run of this brief. The loop below is
CIRCULAR — do not use it as written.**

It grades a submitted question by the engine's own `answerable`, so a `DROP`
was defined to mean *"the corpus answers it, so the question is defective."*
**But `answerable` is the claim under test.** When the first blind set ran, the
engine returned `answerable: true` on **20 of 20** — and a second blind session
reading the corpus confirmed all 20 were genuinely unanswerable. Followed as
written, this loop would have discarded a perfect set as 100 % defective and
recorded the engine's failure as the author's.

**The rule it violates is the one this whole directory exists for: a control
may never be adjudicated by the system it controls.**

**What to do instead — ground truth first, engine second:**

1. **A second session, blind to the engine's output, reads the corpus and rules
   each question answerable or not.** It must be told not to run `fux`. That
   ruling is the ground truth, and the drop count comes from *it*.
2. **Then** run the engine and record its verdict per question **beside** the
   ground truth, as two columns. Disagreement is a finding about the engine,
   not a defect in the set.
3. Both columns go in the run's `evidence/per-query.csv` (mandatory since
   2026-08-28). Worked example:
   [`2026-08-28-blind-unanswerable`](../../work/regression/2026-08-28-blind-unanswerable/report.md).

<details>
<summary>The original loop, kept for the record — it is what ran, and what the correction is against</summary>

**A submitted question is not a decoy until the corpus is checked.** Run each
through the engine; a question the corpus actually answers is a defect in the
set, not in the engine:

```bash
while read -r line; do
  q=$(python3 -c 'import json,sys;print(json.loads(sys.argv[1])["query"])' "$line")
  fux ask "$q" --json --band | python3 -c '
import json,sys
p=json.load(sys.stdin); c=p.get("confidence",{})
print(("KEEP " if not c.get("answerable", True) else "DROP "), c.get("band"), "|", len(p.get("results",[])), "results")'
done < unanswerable.jsonl
```

⚠ **`DROP` is not a judgment on the author.** It means the corpus answers it, so
it belongs in the goldens rather than here. **Record how many were dropped** —
a set that needed heavy pruning was authored against a misread of the corpus,
and the count is the only signal of that anyone will ever have.

</details>

**Recording the drop count is still required** — it is still the only signal
that a set was authored against a misread of the corpus. What changed is
**who decides a drop**: the blind ground-truth reader, never the engine.

## Where it lands, and what it must not become

- The file goes to `<playground>/goldens/unanswerable.jsonl`, **separate from
  `queries.jsonl`**, so the two authorships never merge into one file whose
  provenance nobody can reconstruct.
- ⚠ **It is scored INSIDE the gate** ([ADR-QUALITY](../../docs/adr/0044_quality-contract.md)
  decision 5), with an `answerable-only` slice reported beside it. That is what
  makes it different from the decoys, which are a diagnostic control and are
  never scored.
- **It may not be grown by an informed author later.** Adding to it is
  re-authoring it, and the whole set inherits the least-blind contributor.
