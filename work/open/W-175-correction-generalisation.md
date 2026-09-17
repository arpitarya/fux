---
type: Handoff
name: W-175
description: "The one claim W-162 shipped unmeasured: that a human correction helps phrasings OTHER than its own. It is the whole reason option (b) beat the editorial pin, it was pre-registered in the compare doc before the build, and the build did not do it. N corrections from real failures on an ungraded corpus, M blind paraphrases each, top-3 before/after, both directions."
item: W-175
filed: 2026-09-14
ball: agent
---

✅ **2026-09-15: the 2026-09-30 Codex gate is VOID — Codex is available now and
delivered the golden question sets.** ⚠ **Those are not the paraphrases.** A
paraphrase is written against a *correction*, blind, and no correction has been
filed yet.

✅ **W-192 CLOSED the same day and this item is 🟢.** Two of the three things
*"Agent work now"* asks for are done:

- **The pre-registration is frozen** —
  [`work/regression/2026-09-15-correction-generalisation/PRE-REGISTRATION.md`](../regression/2026-09-15-correction-generalisation/PRE-REGISTRATION.md),
  quoting the compare doc's §6 rather than restating it, with decision 19's
  floor computed for N = 12 / M = 5 and the tilt check stated as a conjunction.
- **The Codex prompt is written** —
  [`prompt-codex-paraphrases.md`](../regression/2026-09-15-correction-generalisation/prompt-codex-paraphrases.md),
  with the blindness clause **in the prompt** rather than assumed.
- **The arm order is RULED: (iii) first, then (ii), then (i).** (iii) has no
  upstream *and* is the only arm whose corpus the measurer never graded, which
  is the compare doc's own condition. (i) is last because twelve real failures
  are accrued, not scheduled.

**What is left here is the harness**, which is agent work and never waited on
any of this.

## ✅ THE HARNESS IS BUILT (2026-09-16) — and it refuses to run without paraphrases

[`tools/quality-controls/correction_generalisation.py`](../../tools/quality-controls/correction_generalisation.py).

Per correction: measure every paraphrase **before**, file the correction's **own**
question with `fux correct`, re-ingest, measure **again**. One row per paraphrase
per arm, with `before`/`after`, and the paired counts printed. **It applies no
bar** — that is [the pre-registration](../regression/2026-09-15-correction-generalisation/PRE-REGISTRATION.md)'s.

🔴 **It files the correction's OWN question and never a paraphrase.** Filing a
paraphrase would measure whether a question helps itself, which is the thing
document expansion was *not* chosen for.

🔴 **It takes the paraphrases as a FILE and exits 1 without one.** It may author
neither input: the corrections must come from real failures on a corpus the
measurer did not grade, and the paraphrases must be written **blind by Codex** —
a paraphrase written by anyone who has seen the correction is the correction's
own wording in disguise, and a leaked one produces a filed number shaped exactly
like a clean one.

**Regression headroom is measured in the BASELINE arm** ([SR-RS](../../records/0133_predictions.md)
22f), and `--no-fetch` is used on the re-ingest so the run cannot depend on a
network (W-177 made the bare verb networked).

**So: everything an agent may do here is done.** What is left is Arpit running
[the Codex prompt](../regression/2026-09-15-correction-generalisation/prompt-codex-paraphrases.md),
arm (iii) first.

---

# W-175 — does a correction generalise, or does it only fix its own phrasing?

**Model: Opus for the design, Codex for the paraphrases** — the paraphrases
must be written by somebody who has not seen which corrections were filed, and
that is the whole instrument.

**Filed 2026-09-14 on shipping [W-162](../../archive/open/W-162-fux-correct.md).**
`fux correct` is built, tested and in use. **The claim that made it the accepted
design is not measured.**

## ✅ RULED 2026-09-14 (Arpit) — three arms, all of them

| arm | source of the corrections | who writes the paraphrases | when |
|---|---|---|---|
| **(i) dogfood** | Arpit runs fux on his own repositories and files `fux correct` as he hits a wrong answer | Codex, blind | corrections accrue from now; paraphrases **2026-09-30** |
| **(ii) fux's own tree** | golden-style questions over `records/` + `work/` + `docs/`; Arpit spot-checks the misses and files the corrections | Codex, blind | questions now; paraphrases **2026-09-30** |
| **(iii) Codex end-to-end** | Codex authors the failures *and* the paraphrases on a corpus no Claude session graded | Codex | **2026-09-30**, when Codex is available |

**Sizes accepted:** N = 12 corrections per arm, M = 5 blind paraphrases each —
60 pairs per arm, well past the SR-RS d19 floor if the effect is real.
**Blind means:** the paraphraser sees the *question* only — never the
correction, never the document.

**Agent work now:** freeze the pre-registration into
`work/regression/<date>-correction-generalisation/`, build the harness (file N
corrections → re-ingest → M paraphrases before/after → per-query rows), write
the Codex prompt Arpit will run. **Ball: 🟣 2026-09-30** for every measured
number; 🟢 for the harness.

## What is unmeasured, precisely

[The compare doc](../compare/fux-correct.compare.md) §1 chose **(b) human
document expansion** over **(a) an editorial pin** on one argument:

> (a) **yes, but brittle** — one phrasing fixed, the next still wrong.
> (b) **best fit** — generalises across phrasings.

**Everything else in W-162 stands on tests.** The verb writes, the marker
survives, `--check` reports, the pin applies and suspends, both readers agree —
all asserted. **Generalisation is the one property a test cannot assert**, and
it is the only one that decides which of (a) and (b) fux should have built.

⚠ **`--pin` is not a fallback that makes this moot.** A pin fixes exactly one
phrasing, which is what (b) was chosen to avoid. If (b) does not generalise,
then fux built the more complicated of two options for a benefit it does not
have, and the compare doc's own reopen trigger fires.

## The pre-registration already exists, and it is not this file

[The compare doc](../compare/fux-correct.compare.md) §6 states the design, and
it was written **before** the build:

> pre-registered on golden: for N corrections, M held-out paraphrases per
> correction, written blind by Codex; measure top-3 retrieval of the corrected
> document on the paraphrases, before vs after / **keep** if the paraphrase gain
> clears the SR-RS d19 floor **and** no golden answerable question loses its
> top-1 (the tilt check) / **remove** → human lines stop being indexed into
> `ctx`, they stay as eval rows, and exact-question `--pin` becomes the default
> effect

**Freeze it into a run directory before the first number** and cite the compare
doc as the origin, rather than restating the bar in looser words.

## Why the paraphrases are not agent work

Three of its inputs are not mine to produce:

1. 🔴 **The corrections must come from real failures on a corpus the measurer
   did not grade** (the compare doc says so). Inventing corrections against a
   corpus I can read is fitting the instrument to the answer.
2. 🔴 **The paraphrases must be written blind, by Codex.** A paraphrase written
   by whoever wrote the correction is the same author twice.
3. **The evidence rule is W-156 (ruled 2026-09-14, archived)'s.** This
   measures a retrieval delta on one corpus, which is the exact case W-156 is
   open about.

## What an agent could do without a ruling

- **Freeze the pre-registration file** into `work/regression/<date>-correction-generalisation/`,
  quoting §6 and naming the SR-RS d19 floor for the N it will actually run.
- **Build the harness**: file N corrections, re-ingest, run M paraphrases per
  correction before and after, emit per-query rows.
- **Nothing else.** The corrections and the paraphrases are the two things it
  may not author.

## The keep/remove call this settles

| outcome | what changes |
|---|---|
| **keep** | nothing. SR-ENRICH decision 19 stands as written |
| **remove** | human lines **stop being indexed into `ctx`** — they share the field with model lines, so there is no per-author weight to turn down — `--pin` becomes the default effect, and the eval rows stay. SR-ENRICH decision 19 is rewritten and the compare doc's verdict flips to (a) |
| **ambiguous** | Arpit's, per-query rows filed |

## Records this will touch

SR-ENRICH (decision 19's keep/remove) · the compare doc's verdict block ·
a `VERDICT.md` beside the evidence.
