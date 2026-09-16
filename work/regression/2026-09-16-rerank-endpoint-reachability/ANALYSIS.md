---
type: Analysis
name: rerank-endpoint-reachability-analysis
description: "What the numbers decide about the next pre-registration's scope, the assumption the run corrected before it was frozen, and the definition of regression headroom the VOID run got backwards."
---

# What this decides, and the assumption it corrected first

## The three decisions it hands to the next pre-registration

1. **The `ask` path is re-run, with the citing document excluded.** 18.3 %
   baseline, 22 / 98 headroom. It can move in both directions, which is the
   thing decision 22b requires and the VOID run lacked.
2. **The `answer` path is NOT re-run.** 0 of 120 on both candidate criteria.
   An arm on a zero-headroom endpoint is `INCONCLUSIVE` before it starts, and
   running one anyway would spend ~2 000 subprocesses to file a foregone
   conclusion.
3. **W-108's two-mechanism separation stays undelivered, and the reason is now
   measured.** It is a property of *this contest set*, not of the refer plane —
   and the next instrument for it must produce queries that are **not lifted
   verbatim from a corpus document**, which is a different generator, not a
   flag on this one.

## 🔴 The assumption this run corrected before it was frozen

The first explanation for `answer`'s 4-hits-in-538 was **crowding**: the citing
document takes every slot, so post-filtering cannot help and the path is
unfixable.

**Measured, it is false.** Over 30 contests:

| | |
|---|---|
| passages per answer | min 5, max 35, **mean 19.4** |
| citing document present | **30 / 30** |
| citing document the **only** document | **0 / 30** |
| target document present | **8 / 30** (27 %) |

There is always something else to promote, and the target is reached about a
quarter of the time. **The path fails for a different reason** — the target is
almost never the *best* non-source passage, and on the occasions it is, the line
range does not overlap the decision the author pointed at.

**Had the pre-registration been written on the first explanation**, it would
have said *"`answer` is unfixable because the source monopolises the candidate
set"* — a sentence that is wrong, in a frozen document, justifying the right
scope decision for the wrong reason. That is the cost of freezing a rationale
nobody checked.

## The definition the VOID run got backwards

It defined **regression headroom** as *right in both arms*. That is
**post-hoc**: it reports what **survived** an arm rather than what was **at
risk** going in, and it reads generously in exactly the case that matters — when
an arm is breaking things, the count shrinks, so the endpoint looks like it had
less to lose than it did.

**Right in the BASELINE arm** is the quantity that means something, and it is
knowable before any treatment runs — which is why it can be measured *here*, in
a run with no arms at all. `rerank_reachability.py` reports it that way, and the
next pre-registration freezes that definition.

## What made the VOID run's screens pass

Worth restating, because it is the transferable part and it is now measured
twice. Both circularity screens passed — **0.4141** passage-level, **0.5273**
document-level — with the contamination present the whole time.

**A screen scores the candidates it is handed.** It compares the truth against
rivals from a list; it never asks *what else is in the corpus*. The citing
document was never on the list. 🔴 **This run is what asking that question looks
like**, and the answer was 87.5 %.

## Cost

~5 minutes and 240 subprocesses, against the ~2 000 a second VOID run would
have cost.
