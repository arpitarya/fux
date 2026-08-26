---
type: Verdict
name: P-SUPERSEDE
title: "P-SUPERSEDE — does `superseded_weight` earn its place once the declaration it needs exists?"
verdict: FAIL
prediction: P-SUPERSEDE
pre_registration: work/regression/2026-08-25-supersession-and-reranker-default/evidence/PRE-REGISTRATION.md
status: final
timestamp: 2026-08-25T00:00:00Z
---

# P-SUPERSEDE — FAIL, and the failure is informative

## The bar, frozen before the number

> **WORKS** — some arm reaches **≥ 1 fixed and 0 broken** against **A1**.

## The ruling

| arm vs A1 | fixed | broken |
|---|---|---|
| `superseded_weight = 0.5` | `q015`, `q049` | `q022`, `q033` |
| `superseded_weight = 0.25` | `q015`, `q049` | `q004`, `q022`, `q033`, `q046` |

**Neither arm reaches 0 broken. FAIL.**

**`superseded_weight` stays at its default of `1.0` — neutral.**

## FAIL is the successful outcome here, and this is why

**The prior is not inert — it fires, for the first time since it shipped.** A1,
the control, moved **nothing**: the frontmatter edit alone fixes 0 and breaks 0.
So every movement is the demotion, and the demotion **fixes `q015`** — the exact
query the mechanism was designed for, the one whose failure motivated a
cross-encoder.

**And it fails anyway, because every query it breaks has the superseded
document as its correct answer**: *"can I start new work against helix mesh"*,
*"why keep a superseded record"*, *"why did we adopt a service mesh in the first
place"*, *"how do we stop a slow dependency taking down checkout"*.

**The diagnosis, and it is the transferable part:**

> **Supersession is a property of the QUERY'S INTENT, not of the DOCUMENT.**
> A superseded document is fully relevant to *what did we used to do*, *why*,
> and *may I still use it* — and wrong for exactly one intent, *what is true
> now*. A per-document multiplier is the wrong shape for the problem, because
> the problem is not about the document.

`q015` contains the word **"current"**. The four broken queries do not. **The
signal was in the query the whole time.**

## What this does NOT say

- **Not that supersession is worthless.** It says a *global demotion* is.
- **Not a magnitude claim.** ±2 on 50 queries is below ADR-RS decision 14's
  resolution floor and must be read as **no detected change in size**. What
  this establishes is **mechanical**: the prior reaches the ranking, and its
  breakages are systematic rather than noisy — all four share one cause.
- **Not generalisable.** Ten documents, one corpus, `informed` authorship.

## What it points at

Query-intent classification — *"what is current"* vs *"what did we used to
think"* — as a different question against the same corpus, rather than a weight
on the document. **Unbuilt, unruled, and now with measured evidence behind it.**
