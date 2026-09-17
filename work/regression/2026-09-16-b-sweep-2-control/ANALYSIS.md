---
type: Analysis
name: b-sweep-2-control-analysis
description: "Why the control was built the way it was, what it proves, and the frozen-rule defect that stops the sweep from being run."
---

# Why it is built this way, and why the sweep still cannot run

## The design choice that makes it a control rather than a tie

The obvious `verbose` family is *two documents, same occurrences, one three
times longer*. It does not work: as `b → 0` the length penalty vanishes and the
two scores **converge**, so the family reports a tie broken by whatever the
ordering happens to be. **A tie is not a regression anybody can read**, and a
control whose failure mode is a coin flip is not a control.

**Giving the rival one more occurrence (7 against 6) fixes it.** Now the two
arms disagree about something real:

- at `b = 0.75`, length normalisation outweighs one extra hit → **concise wins**;
- at `b = 0`, nothing pays for length → **7 > 6, verbose wins**.

So the family flips, at a value, and the flip is the measurement.

## What it proves, and what it does not

✅ **Proves:** the arm set now has a control with regression headroom, and it is
demonstrated rather than argued — 30/30 → 0/30, `p = 0.0000` on 30 discordant
pairs, at a value inside the sweep's own mechanism.

🔴 **Proves something sharper:** `b = 0` and `b = 0.15` are **indistinguishable**
on every instrument the arm set had yesterday. `main` +30, `content` +30,
`dump`/`inverse`/`placebo` unchanged — at both. **The only thing that separates
them is `verbose`.** Arpit's condition was not procedural caution; the blind spot
was real and one value wide.

❌ **Does not prove** that any value should ship. No threshold is frozen, the
descending rule is not applied, and the corpus is synthetic.

## 🔴 The rule defect, and why it is not mine to fix

The frozen rule requires a value that **nets positive on `dump`, `content` and
`main`, each individually**. `dump` is at **30/30 at the baseline** and can
never net positive.

**`dump` is described as a family and functions as a control.** Its own
generator comment says the prose document is *"correct in BOTH arms"* and that
(b) collapsing the dump's length *"must not change that"* — which is a control's
definition, word for word. It was grouped with `content` and `main` because all
three are *table* families, and the rule inherited the grouping.

**Two readings, and they give opposite verdicts:**

| reading | result |
|---|---|
| strict — *net > 0 on all three* | **no value can ever clear**, at any `b`, forever. W-144 closes as a measured negative on a technicality |
| *positive where there is headroom, non-negative everywhere* | **`b = 0.15` clears**: `main` +30, `content` +30, `dump` +0, all three controls holding |

**I am not choosing between them.** A pre-registered threshold may never move
([SR-RS](../../../records/0133_predictions.md) decision 10b), and a runner who
reinterprets a rule after seeing which reading passes is moving it with extra
steps. The question is in the inbox with this evidence attached.

⚠ **It would have been cheaper to catch before the 2026-09-15 sweep**, and it
was not, because that sweep's `dump` column read `+0` everywhere and `+0` looks
like *nothing happened* rather than like *this family cannot report*. **A
saturated family and an inert lever produce the same number**, which is the same
confusion `inverse` and `placebo` caused and the reason this run exists.

## Cost

Seconds. The scoring is in-process arithmetic over a generated corpus — no
subprocess per query, which is why a probe like this is worth running before
anything expensive.
