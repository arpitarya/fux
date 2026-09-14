---
type: Pre-registration
description: "What a fux inspect floor has to do before it may carry a flag, written down before the first number. Taken verbatim from work/proposals/fux-inspect.md §3 and §5b and work/open/W-169-fux-inspect.md DoD 5, both of which predate this run."
run: 2026-09-14-inspect-floors
item: W-169
filed: 2026-09-14
---

# Pre-registration — what a floor has to do

**This restates nothing new.** The rule was written by Arpit's proposal on
2026-09-13 and by the item on 2026-09-14, both **before any number existed**,
and it is reproduced here so the verdict has a frozen file to read rather than
a document that could be edited afterwards.

## The rule, from the two documents that state it

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
> — [`W-169`](../../open/W-169-fux-inspect.md) DoD 5

## What that makes this run's procedure, stated before it ran

1. **Measure the three shares on every golden rung available** — 100, 200, 500,
   1 000, 2 000, 5 000, 10 000 — plus a **planted-bad** corpus built to be bad
   in all three ways and the **planted-lenses** corpus the e2e suite uses.
2. A bound is admissible **iff** it flags **no** golden rung **and** flags a
   corpus that is bad in that bound's own dimension.
3. **A number with no admissible bound ships as `descriptive`.** It still
   prints; it carries no flag. This is a pass of the rule, not a failure of the
   run.
4. **Every bound that ships is marked `provisional`** and prints that word.
5. **This repository's own numbers are reported and are not an input to any
   bound** — *never tuned to this repo* is the explicit instruction.

## What this run may NOT do

- **Move the rule.** If no bound is admissible for a number, that number goes
  descriptive; the rule does not loosen to admit one.
- **Read any evaluation material.** The three shares are properties of an
  index. This run reads each rung's `docs/` and nothing else — not
  `queries.jsonl`, not `judged.jsonl`, not `key.jsonl`.
- **Rule on ranking.** `fux inspect` changes no ranking and this run states no
  delta between arms.
