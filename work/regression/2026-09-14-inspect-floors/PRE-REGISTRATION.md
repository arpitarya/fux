---
type: Pre-registration
description: "What a fux inspect floor has to do before it may carry a flag. 🔴 READ THE FIRST SECTION: this FILE is a restatement written after the numbers, and its commit also carries the implementation. The RULE it restates is older and is in git at two named commits, both of which predate every number in this run. The file is not the frozen artifact and may not be cited as one."
run: 2026-09-14-inspect-floors
item: W-169
filed: 2026-09-14
---

# Pre-registration — what a floor has to do

## 🔴 First: what this file is, and what it is not

**It is not a frozen-ahead-of-the-numbers artifact, and an earlier draft of
this run claimed it was.** That claim was wrong in both of its parts and is
corrected here rather than quietly dropped, because a false provenance claim
about a threshold is worse than no claim at all — it is the exact failure the
pre-registration discipline exists to prevent, wearing the discipline's own
clothes.

| the claim that was made | the fact |
|---|---|
| *"committed **alone** at `34306eb5`"* | **`34306eb5` carries 28 files**, including all five modules of `src/fux/inspect/`, both test files and SR-INSPECT. `git commit` with no pathspec commits the whole index, and the index already held the implementation |
| *"ahead of the first number"* | **This file was written after** the seven rungs and `planted-bad` had been measured, and after the three bounds had been set in `checks.py` |

**What IS checkable, and it is the thing that matters.** The rule this run was
judged against was written down before the verb existed, by two documents whose
commits anyone can read:

| where the rule is stated | commit | date | what it already said |
|---|---|---|---|
| [`work/proposals/fux-inspect.md`](../../proposals/fux-inspect.md) §3 | **`df257ad5`** | **2026-09-13** | floors are *"**provisional and say so** … measured later on golden, **never tuned to this repo**. A wall of red on an unmeasured floor is how a tool gets ignored."* A clean prior commit: the proposal was filed a day before this work began |
| the same file §5b, and [`W-169`](../../../archive/open/W-169-fux-inspect.md) DoD 5 | **`91255adb`** | **2026-09-14** | *"a floor separates the planted-bad corpus from every golden rung"* / *"a floor that flags a healthy rung is **dropped to descriptive** — the number prints, the flag does not."* ⚠ **Weaker provenance, stated as weaker:** both were written by the previous session and sat **uncommitted** in the working tree; their first commit is this session's own. What makes it checkable anyway is that `91255adb` **contains no `fux inspect`** — the verb did not exist in it, so no number could have informed the words |

**So the honest summary: the criterion predates the numbers; this file does
not.** Everything below is a restatement of §3, §5b and DoD 5, kept here so a
reader has the rule in one place beside the evidence it judged.

## The rule, quoted from the two documents that state it

> Their floors are **provisional and say so** — the same status
> `SEPARATION_FLOOR` carries — measured later on golden, **never tuned to this
> repo**. A wall of red on an unmeasured floor is how a tool gets ignored.
> — [`work/proposals/fux-inspect.md`](../../proposals/fux-inspect.md) §3

> a floor separates the planted-bad corpus from every golden rung / **a floor
> that flags a healthy rung is dropped to *descriptive*** — the number prints,
> the flag does not.
> — same file, §5b

> Three checks — findable share, boilerplate share, near-duplicate share — with
> floors measured on the golden ladder and marked provisional; **a floor that
> flags a healthy rung drops to descriptive.**
> — [`W-169`](../../../archive/open/W-169-fux-inspect.md) DoD 5

## The procedure that follows from it

1. **Measure the three shares on every golden rung available** — 100, 200, 500,
   1 000, 2 000, 5 000, 10 000 — plus a **planted-bad** corpus built to be bad
   in all three ways and the **planted-lenses** corpus the e2e suite uses.
2. A bound is admissible **iff** it flags **no** golden rung **and** flags a
   corpus that is bad in that bound's own dimension.
3. **A number with no admissible bound ships as `descriptive`.** It still
   prints; it carries no flag. This is the rule passing, not the run failing.
4. **Every bound that ships is marked `provisional`** and prints that word.
5. **This repository's own numbers are reported and are not an input to any
   bound** — *never tuned to this repo* is the explicit instruction.

⚠ **Step 2 means a bound is chosen with the rung numbers in hand, by design.**
That is the criterion's own shape and not a leak: the criterion constrains the
bound rather than predicting it. What it forbids is the reverse — loosening the
criterion so that a preferred bound becomes admissible — and
[`VERDICT.md`](VERDICT.md) records that this did not happen, because the one
number that could not clear it went descriptive instead.

## What this run may NOT do

- **Move the rule.** If no bound is admissible for a number, that number goes
  descriptive; the rule does not loosen to admit one.
- **Read any evaluation material.** The three shares are properties of an
  index. This run reads each rung's `docs/` and nothing else — not
  `queries.jsonl`, not `judged.jsonl`, not `key.jsonl`.
- **Rule on ranking.** `fux inspect` changes no ranking and this run states no
  delta between arms.
