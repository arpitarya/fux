---
type: OpenItem
id: W-89
title: "W-89 — does L2 reach a query log?"
description: "A gap in the laws surfaced by W-87's research. L2 says content is never durable outside its source system; a record of what people ASKED is content-adjacent and privacy-adjacent, and no law names it. Filed rather than settled as a side effect of a metrics ruling."
status: ruled
lane: arpit
timestamp: 2026-08-27T00:00:00Z
---

# W-89 — does L2 reach a query log?

> ## ✅ RULED 2026-08-27 (Arpit) — shape 2: a new law, `L8`
>
> **L2 does not reach a query log. `L8` does.** The normative text is in
> [`CLAUDE.md`](../../CLAUDE.md) §Non-negotiable constraints; the handle and the
> reasoning are [ADR-LAWS](../../docs/adr/0001_laws.md) decision 8; both were
> edited in the same change, as ADR-LAWS decision 4 requires.
>
> **L8** · *What fux retains about use is hashed, bounded, and local.*
>
> **Why shape 2 and not shape 3** (leave it a product decision, which is what
> Arpit's first instinct — *"the log is built, and it's in gitignored files, so
> it's okay"* — amounts to): the guard would have been one decision inside
> [ADR-QUALITY](../../docs/adr/0044_quality-contract.md), and an ADR is designed
> to be superseded. Two facts made that too thin — a durable use record
> **already exists** in [`maintain/lastcited.py`](../../src/fux/maintain/lastcited.py),
> and [`ranking-tuning.md`](../proposals/ranking-tuning.md) §8 calls a per-repo
> query log *"an asset fux gets for free"*. The pull toward building one is
> documented and growing, which is OPEN-WORK rule 6's damage-that-accrues.
>
> **Why not shape 1** (L2 already covers it): L2 is written about the corpus. A
> query is not corpus content however precisely it describes one, and stretching
> a law to cover a case it does not name is the paraphrase-drift failure
> ADR-LAWS exists to stop.
>
> ⚠ **L8 landed green — it forbids nothing fux does today**, verified against the
> code before the text was written.
>
> ⚠ **Outstanding, hands only:** this file's `git mv` into `archive/open/` and its
> `archive/README.md` row. Filed in [`OPEN-WORK.md`](../OPEN-WORK.md) with the
> other stray-file `git` operations — no agent has a shell.
>
> Outcome recorded in [`IMPLEMENTATION.md`](../IMPLEMENTATION.md).

*Everything below is the question as it stood before the ruling, kept because
the reasoning that produced the call is worth keeping.*

**Model: Opus.** It is a question about the laws, and a wrong answer is not
catchable by any test.

**Filed 2026-08-27**, split out of [W-87](W-87-what-good-means.md) fork 6 in the
change that ruled it. [ADR-QUALITY](../../docs/adr/0044_quality-contract.md)
decision 11 declines a query log **and explicitly declines to settle this**.

## The question

**L2 says: content is never durable outside its source system.** It governs the
**corpus**. A query log is not corpus content — it is a record of what a person
asked, which is:

- **content-adjacent** — a sufficiently specific query reveals the document, and
  sometimes the sentence, without ever storing it;
- **privacy-adjacent** — in a corporation, *who asked what, when* is exactly the
  material an access review cares about, and L5 exists because ACL mismatch is a
  real leak;
- **not mentioned by any of L1–L7.**

**So the honest position today is: the laws do not say.** That is the finding.

## Why it is not settled by W-87

**A metrics document should not amend the laws as a side effect.**
[`work/compare/what-good-means.compare.md`](../compare/what-good-means.compare.md)
fork 6 says so in its own proposed verdict, and Arpit ruled it as written on
2026-08-27. Ruling *"no query log"* is a scope decision; ruling *"L2 does/does
not reach one"* is a change to the constitution and belongs in
[ADR-LAWS](../../docs/adr/0001_laws.md).

## What is blocked on Arpit

- [ ] **Does L2 reach a query log?** Three shapes the answer can take:
  1. **L2 already covers it** — queries are derived from content and inherit its
     protection. Cheapest to state; ⚠ stretches a law written about the corpus.
  2. **A new law (L8)** naming what fux may retain about *use* rather than about
     *content*. Honest; ⚠ CLAUDE.md §Non-negotiable constraints and ADR-LAWS'
     table both change, in the same commit.
  3. **Nothing changes** — no law reaches it, and the prohibition stays a
     product decision recorded in ADR-QUALITY. ⚠ Leaves the gap named but
     unguarded, which is a legitimate choice only if it is said out loud.

## Definition of done

- [ ] The question answered, in one of the three shapes above.
- [ ] If the answer changes a law: `CLAUDE.md` §Non-negotiable constraints **and**
      [ADR-LAWS](../../docs/adr/0001_laws.md)'s table edited in the **same
      commit** — CLAUDE.md is the only normative home and no record may restate
      a law.
- [ ] [ADR-QUALITY](../../docs/adr/0044_quality-contract.md) decision 11's
      pointer updated to name the answer instead of the open question.

## References

- [ADR-QUALITY](../../docs/adr/0044_quality-contract.md) — decision 11, which
  declines to settle this
- [ADR-LAWS](../../docs/adr/0001_laws.md) — where an answer would land
- [`work/compare/what-good-means.compare.md`](../compare/what-good-means.compare.md)
  — §4 fork 6, the research that surfaced the gap
- [W-87](W-87-what-good-means.md) — the parent item
