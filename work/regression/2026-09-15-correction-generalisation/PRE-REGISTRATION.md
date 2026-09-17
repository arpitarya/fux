---
type: Pre-Registration
name: correction-generalisation
description: "Frozen before any correction is filed: does a `fux correct` line help phrasings OTHER than its own? N = 12 corrections per arm, M = 5 blind paraphrases each, top-3 before/after, the SR-RS d19 floor computed for this design, and the tilt check. Origin is the compare doc, written before the build."
status: frozen
item: W-175
timestamp: 2026-09-15T00:00:00Z
---

# Pre-registration — does a correction generalise?

🔴 **Frozen 2026-09-15, before a single correction exists.** [SR-RS](../../../records/0133_predictions.md)
decision 10b: a pre-registered threshold may never move. Nothing below is
revisable once the first number is measured; an ambiguous result goes to Arpit.

**Legally half-empty** — [`README`](../README.md) §Per-run contract: a directory
holding a frozen pre-registration and **no report** owes nothing else. There is
no report here and there may not be one for weeks: two of the three arms need
corrections that do not exist yet.

## The origin, quoted rather than restated

**This bar is [the compare doc](../../compare/fux-correct.compare.md)'s §6**,
written **before** `fux correct` was built — which is what makes it a
pre-registration rather than a rationalisation:

> **generalisation** (the reason (b) beat (a)) — pre-registered on golden: for N
> corrections, M held-out paraphrases per correction, written blind by Codex;
> measure top-3 retrieval of the corrected document on the paraphrases, before
> vs after / **keep if** paraphrase retrieval gain clears the SR-RS d19 floor,
> **and** no golden answerable question loses its top-1 (the tilt check) /
> **remove if** it fails → human lines are no longer indexed into `ctx` (they
> share the field with model lines, so there is no per-author weight to turn
> down); they stay as eval rows, and exact-question `--pin` becomes the default
> effect

**What this file adds is only arithmetic and procedure**, never a looser bar.

## The claim under test

`fux correct` writes a human-authored question onto the document that answers
it. [The compare doc](../../compare/fux-correct.compare.md) §1 chose that over
an editorial pin on **one** argument:

> (a) **yes, but brittle** — one phrasing fixed, the next still wrong.
> (b) **best fit** — generalises across phrasings.

**Every other property of `fux correct` rests on a test.** The verb writes, the
marker survives regeneration, `--check` reports, the pin applies and suspends,
both readers agree. **Generalisation is the one a test cannot assert**, and it
is the only one that decides which of (a) and (b) fux should have built.

⚠ **`--pin` is not a fallback that makes this moot.** A pin fixes exactly one
phrasing, which is what (b) was chosen to avoid.

## Design — frozen

| | value | why this and not another |
|---|---|---|
| **N** — corrections per arm | **12** | accepted by Arpit 2026-09-14 |
| **M** — held-out paraphrases per correction | **5** | accepted the same day |
| pairs per arm | **60** | N × M |
| endpoint | **top-3 retrieval of the corrected document**, on the paraphrase, before vs after the correction is filed and re-ingested | the compare doc's words |
| comparison | **paired** — the same paraphrase under both arms | only flips carry information (d19) |
| arms | **three, measured and reported separately** — never pooled | different corpora and different authors; pooling would hide which one moved |

## The bar, computed for this design

**Paired, so the test is McNemar's exact binomial on the discordant
paraphrases** — [SR-RS](../../../records/0133_predictions.md) decision 19.
**The bar tracks the FLIPS, never the 60.**

| paraphrases that flip | net needed at α = 0.05 |
|---:|---:|
| 2 · 4 | **impossible** |
| 6 | **6** |
| 8 – 12 | **8** |
| 15 | **9** |
| 20 | **10** |
| 30 | **12** |
| 50 | **16** |

🔴 **A net of 6 is the floor of all floors, and nets of 1–5 cannot clear α at
ANY discordant count.** So:

- **KEEP** requires a net ≥ the row for the observed discordant count **and**
  the tilt check passing.
- **A net of 5 or less is a measured negative**, whatever the flip count, and
  needs no further arithmetic.
- **`verdict.py`** (`tools/quality-controls/`) computes the exact p — the bar is
  not compared by hand, after three tools independently reached for the floor of
  all floors as if it were the bar.

## The tilt check — a second, absolute gate

**No golden answerable question may lose its top-1.** Stated as a conjunction in
the compare doc, and it is **not** traded off against the net: a mechanism that
fixes 12 corrections by reordering the rest of the corpus is a regression with a
good anecdote.

⚠ **It is measured on whichever question set is scored at the time**, and every
set 2 number is `informed` permanently ([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md)).
🔴 **No Claude session reads a golden answer to run it** — law
[L11](../../../records/0012_LAW-11-sealed-answer-key.md). The tilt check is
therefore run where the scoring is: it is Codex's, in a chat Arpit attends.

## The three arms, and their order — RULED HERE

Arpit accepted all three on 2026-09-14. **W-192 owes the order, and it is:**

| # | arm | corrections from | paraphrases by | upstream |
|---|---|---|---|---|
| **1st** | **(iii) Codex end-to-end** | Codex authors the failures on a corpus no Claude session graded | Codex, blind | 🟢 **none** |
| **2nd** | **(ii) fux's own tree** | golden-style questions over `records/`, `work/`, `docs/`; Arpit spot-checks the misses and files the corrections | Codex, blind | the questions (agent work), then Arpit |
| **3rd** | **(i) dogfood** | Arpit running fux on his own repositories, filing `fux correct` as he hits a wrong answer | Codex, blind | **elapsed time** — twelve real failures |

🔴 **(iii) goes first because it has no upstream, and because it is the only arm
whose corpus the measurer never graded** — which is the compare doc's own
condition (*"corrections must come from real failures on a corpus the measurer
did not grade"*). (i) is last not because it matters least — it matters **most**,
being the only arm made of real use — but because twelve real failures are
accrued, not scheduled.

⚠ **An arm that returns fewer than 12 corrections is reported at the N it
actually ran**, with the bar recomputed for the observed flips. It is **not**
topped up with invented failures, and it is not pooled with another arm to reach
12.

## What an agent may and may not author

| | who |
|---|---|
| the harness, the per-query rows, this file | **an agent** |
| the **corrections** | never the measurer — real failures only |
| the **paraphrases** | **Codex, blind**, from the question alone |
| the **verdict**, if ambiguous | **Arpit** |

🔴 **A paraphrase written by anyone who has seen the correction is the
correction's own wording in disguise**, and the whole claim under test is that a
correction helps phrasings *other* than its own.

## What is filed when a number exists

Per [`README`](../README.md) §Per-run contract: `report.md` (with
`classification:`), `ANALYSIS.md`, `evidence/` with **one row per paraphrase per
arm**, a `VERDICT.md` ruling on this file, and a row in the index.

⚠ **`classification` will be `informed` for arm (ii)** — fux's own tree is a
corpus this project's sessions read constantly. Arms (i) and (iii) may be
`blind` if nothing else disqualifies them; the [authorship
table](../../../records/0133_predictions.md) decides, not this file.

## What this settles

| outcome | what changes |
|---|---|
| **keep** | nothing. [SR-ENRICH](../../../records/0137_enrich.md) decision 19 stands as written |
| **remove** | human lines **stop being indexed into `ctx`**, `--pin` becomes the default effect, the eval rows stay, SR-ENRICH decision 19 is rewritten and the compare doc's verdict flips to (a) |
| **ambiguous** | Arpit's, per-query rows filed |
