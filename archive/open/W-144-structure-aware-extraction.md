---
type: OpenItem
id: W-144
title: "W-144 — structure-aware extraction: does a table inflate `flen`?"
description: "MEASURED 2026-09-12 and the answer is yes: excluding table-row tokens from flen ranks better, hit@1 0/30 -> 30/30 at p = 0 with both controls holding, above a table share of ~0.29 that a third of the golden ladder exceeds. One synthetic corpus may not ship a ranking change, so what is left is Arpit accepting or overriding the compare doc."
status: open
lane: agent
timestamp: 2026-09-12T00:00:00Z
---

## ✅ CLOSED 2026-09-16 — `PASS` at `b = 0.15`, shipped

[Verdict](../regression/2026-09-16-b-sweep-2/VERDICT.md) · **`PASS`**.

| `b` | `content` | `main` | controls | clears? |
|---|---:|---:|---|---|
| 0.4 | +0 | +0 | all hold | no — neither benefit family moves |
| 0.3 | **+30** | +0 | all hold | no — `main` does not net positive |
| 0.2 | **+30** | +0 | all hold | no — same |
| **0.15** | **+30** | **+30** | **all four hold** | ✅ **yes** |

Both benefit families at `0.15`: `p = 0.0000` on 30 discordant pairs, against a
required net of **12**.

🔴 **Why `0.15` and not `0.3`.** The two benefit families cross at **different**
values — `content` (a rate card whose subject *is* its rows) between 0.4 and 0.3,
`main` (prose with a table appendix) between 0.2 and 0.15. **The rule requires
both.** A rule asking for *either* would have shipped `0.3` and left half the
mechanism unmeasured behind a passing verdict.

✅ **The controls' holding is a measurement, not a tautology** — `verbose` is
proven able to lose (30/30 → **0/30 at `b = 0`**), and without it `b = 0` and
`b = 0.15` are indistinguishable on every other instrument. ✅ **`dump` holds**,
which is the specific harm W-155 showed option (b) causing.

### Step 4, discharged

| | |
|---|---|
| **shipped** | `B = 0.15` in `src/fux/query/bm25f.py` **and** `node/src/query/bm25f.mjs`; `.fux/tune.toml` |
| **records** | SR-RANKING decision 3 — 🔴 **the first default here that is MEASURED rather than inherited** — plus SR-TUNING, SR-ASK, SR-NODE-SEARCH |
| **L3 / byte equality** | ✅ **22 144 comparisons, byte-identical in every mode**; Node parity test green, bundle rebuilds |
| **CHANGELOG** | a ranking block naming the value, the reason, and the upgrade trap |

🔴 **The upgrade trap, stated in the CHANGELOG because nothing else would catch
it:** `fux setup` writes `b` out in full, so **a repo set up before this keeps
`0.75` and will not move.** A fresh clone and a set-up repo now rank differently
until the line is changed or deleted.

⚠ **One synthetic corpus, `informed`.** 510 generated documents built so the
mechanism *can* move. It says a lower `b` ranks better **on documents shaped like
these**; fux's own docs tree is the reopen-trigger evidence and was not run.

⚠ **No fux test pinned `b`'s value**, so the suites passing is not evidence the
change is right. The differential is; the sweep is what says it is better.

---

## ✅ RULED 2026-09-16 (Arpit, Cowork) — `dump` is a CONTROL; the range and first-that-clears stand

**Ruling: this is a specification defect in the decision rule, not a threshold to
move.** `dump` was grouped with `content` and `main` because all three are
*table* families, and the rule inherited the grouping. **Its own generator says
the prose document is *"correct in BOTH arms"*, and that collapsing the dump's
length *"must not change that"*** — that is the definition of a control, and it
was written down before any number existed.

**`dump` moves to the control set.** The decision rule reads:

> the first descending value that **nets positive on `content` and `main`**,
> each individually, neither negative, with **every control holding** —
> `inverse`, `placebo`, `verbose` **and `dump`**.

**Unchanged from the 2026-09-15 ruling:** the range `b ∈ {0.4 → 0.3 → 0.2 →
0.15}`, **descending**, first-that-clears; the `verbose` control, its expected
direction and its floor; the SR-RS d19 pair-count floor; and steps 4–5 (ship on
clear, amend SR-TUNING and SR-RANKING in the same change, L3 check, two-reader
byte equality, CHANGELOG line — `fux setup` writes `b` out in full).

⚠ **Why this is not the moving-threshold failure**
([SR-RS](../../records/0133_predictions.md) decision 10b): the justification is
`dump`'s **role, quoted from its generator**, not the fact that it makes a value
clear. The reclassification would be correct if the sweep had never run.
**Re-freeze `PRE-REGISTRATION.md` with that reason written into it**, in a new
`work/regression/<date>-b-sweep-2/`, before the first number. The 2026-09-15
pre-registration is **superseded in place, not edited**.

⚠ **`dump` keeps its teeth.** W-155 showed option (b) drove it 30/30 → 0/30;
catching exactly that is a control's job here, and it holds 30/30 down to
`b = 0`. **If a value clears `content` and `main` while `dump` regresses, the run
FAILS.** Same bar.

⚠ **Reading (2) is the likely outcome, not the reason.** `b = 0.15` is a long
way from the literature's `0.75`; that is what the descending order and the
`verbose` control are for, and neither is optional.

**Agent work:** the 2026-09-15 order, with step 2's decision rule replaced by the
one above. **Step 1 is ✅ discharged** — `verbose` is built and proven
(30/30 across the ruled range, 0/30 at `b = 0`, `p = 0.0000`). Next is the
re-frozen pre-registration, then the run in `fux-lab`.

## 🔴 STEP 1 IS DONE, AND IT FOUND THAT THE RULE CANNOT BE SATISFIED (2026-09-16)

[The control probe](../regression/2026-09-16-b-sweep-2-control/report.md).

✅ **Your condition is discharged.** `verbose` exists, and it is proven to lose
rather than argued to be able to: two prose-only documents, a concise brief with
6 occurrences against a report **3× as long with 7**. It **holds 30/30 at every
value in the ruled range** `{0.4, 0.3, 0.2, 0.15}` and **breaks to 0/30 at
`b = 0`**, `p = 0.0000` on 30 discordant pairs.

⚠ **The extra occurrence is the design.** With equal `tf` the two documents
merely **tie** as `b → 0`, and a tie is not a regression anyone can read off a
hit count. At 7 against 6 the verbose document wins outright once length stops
being paid for, so the control fires as a flip.

🔴 **And it earned its keep in the same probe.** `b = 0` and `b = 0.15` are
**indistinguishable on every instrument the arm set had before it**: `main` +30,
`content` +30, `dump`/`inverse`/`placebo` unchanged — at both. The blind spot you
named was real, and it was exactly one value wide.

✅ **The crossovers replicate** on the new corpus (adding 30 terms moves every
probe term's `df`, now 2–12): `content` between 0.4 and 0.3, `main` between 0.2
and 0.15.

### 🔴 The question, and why the run has NOT started

**The ruled rule is unsatisfiable as written.** It asks for the first descending
value that

> nets positive on all three families — **`dump`**, `content` and `main`, each
> individually, none negative

**`dump` sits at 30/30 at the baseline.** Its correct answer is the prose
document, which already wins at `b = 0.75`, so it can **hold or break and never
net positive** — at any value, forever.

**`dump` is described as a family and behaves as a control.** Its own generator
says the prose document is *"correct in BOTH arms"* and that collapsing the
dump's length *"must not change that"*. It was grouped with `content` and `main`
because all three are *table* families, and the rule inherited the grouping.

| reading | what the sweep returns |
|---|---|
| **(1) strict** — net > 0 on all three | **no value clears, ever.** W-144 closes as a measured negative on a technicality |
| **(2) positive where there is headroom, non-negative everywhere** | **`b = 0.15` clears** — `main` +30, `content` +30, `dump` +0, all three controls holding |

🔴 **Not chosen here.** A pre-registered threshold may never move
([SR-RS](../../records/0133_predictions.md) decision 10b), and a runner picking
the reading after seeing which one passes is moving it with extra steps. **No
pre-registration is frozen and no sweep has run.**

⚠ **Worth knowing before you rule:** reading (2) makes `b = 0.15` the answer, and
`0.15` is a long way from the literature's `0.75` — which is the discomfort the
descending rule and the new control were both built for. Reading (1) throws away
a lever that demonstrably works on two of three benefit families.

⚠ **This would have been cheaper to catch before the 2026-09-15 sweep**, and was
not: `dump` read `+0` in every column, and **a saturated family and an inert
lever produce the same number**.

## ✅ RULED 2026-09-15 (Arpit, Cowork) — (b), a LOWER range, gated on a control that can lose

**Ruling: option (b)** of the three the verdict put up — pre-register a lower `b`
range — **with one condition**: the run does not start until the arm set carries a
control family with regression headroom. Both existing controls (`inverse`,
`placebo`) are saturated 30/30 in every arm, so *"nothing regresses"* on the
probe is consistent with safety and is not evidence of it.

**Not taken:** (a) the pre-registered fallback — it returns to option (b)-of-the-
compare-doc, which W-155 showed destroys `dump`, a defect lowering `b` does not
have; (c) stopping at `0.75` — the mechanism is confirmed and one-directional
and bites at table shares a third of the ladder has.

**Agent work, in order — a SEPARATE run, not a continuation of 2026-09-15-b-sweep:**

1. **Add a control family that can regress** — e.g. `verbose`: same subject as
   its rival at ~3× the prose, expected to LOSE at `b = 0.75` and to keep losing
   at every value tried. If a lower `b` stops penalising verbosity, this arm
   catches it. Name it, its expected direction and its floor in the
   pre-registration before any number exists.
2. **Pre-register the lower range, descending**, in
   `work/regression/<date>-b-sweep-2/PRE-REGISTRATION.md`: `b ∈ {0.4 → 0.3 → 0.2 → 0.15}`,
   families `dump` · `content` · `main` + `inverse` · `placebo` · **`verbose`**,
   rule *first value netting positive on `dump`, `content` and `main` with every
   control holding*, SR-RS d19 floor at the pair count actually run. The probe's
   crossovers (`content` 0.4→0.3, `main` 0.2→0.15) are the reason for the range,
   not the answer — first-that-clears still decides.
3. Run on the golden ladder (verdict) and on fux's own docs tree (reopen-trigger
   evidence only), in `fux-lab`.
4. If a value clears: ship it as the `tune.toml [bm25f]` default, amend SR-TUNING
   and SR-RANKING in the same change, L3 check, two-reader byte equality, and a
   CHANGELOG line — `fux setup` writes `b` out in full, so a new default diverges
   fresh clones from set-up repos.
5. If no value clears with `verbose` holding: **stop and re-inbox**, with the
   numbers. No second widening without a ruling.

⚠ **`0.15` is far from the literature's `0.75`.** That is why the descending rule
and the new control both exist; neither is optional.

## 🔴 THE SWEEP IS RUN, AND NO PRE-REGISTERED VALUE CLEARS (2026-09-15)

[Verdict](../regression/2026-09-15-b-sweep/VERDICT.md) · `FAIL`.

`b = 0.6`, `0.5` and `0.4` leave **all five families exactly where `0.75` does**
— 0 discordant pairs, everywhere. The pre-registration's fallback fires.

🔴 **But the lever is not inert.** A mechanism probe outside the arms
(SR-RS 22c) puts the crossovers **below the frozen floor**:

| family | flips between |
|---|---|
| `content` — the table IS the answer | **0.4 and 0.3** |
| `main` — prose with a table appendix | **0.2 and 0.15** |

🔴 **And option (d) does not have option (b)'s defect.** `dump` — the family
W-155 showed option (b) **destroyed** — holds **30/30 down to `b = 0`**.
Lowering `b` rescales every document's length together; excluding table tokens
rewrote one document's length by ~7×.

⚠ **Both controls are saturated** (30/30 in every arm), so *nothing regresses*
is consistent with safety and **is not evidence of it**.

**Three options, in the inbox** — take the pre-registered fallback, pre-register
a lower range, or stop at `0.75`. **Not taken here**: picking `0.15` because the
probe found it is the moving-threshold failure the descending rule exists to
prevent.


# W-144 — structure-aware extraction, graduated

**Model: Opus** — it is a ranking change gated on a pre-registered measurement,
and the call on whether a null is a null belongs to the model that can read the
measurement against its bar.

**Filed 2026-09-12 while reviewing `work/proposals/`**, not from new work. The
proposal
[`structure-aware-extraction.md`](../proposals/structure-aware-extraction.md)
says it *"graduates to a compare doc or an OPEN-WORK item when W-86's P4 lands
(OOXML)"*. **P4 landed** — `src/fux/decode/docx.py`, `pptx.py` and `xlsx.py`
all ship — and the proposal sat parked, so the trigger fired and nothing moved.

## The claim, and what it is not

**The claim:** tables, code fences and lists should be **fields in
`extract.py`, not policy in decoders**. Its strongest concrete suspicion is
that **table cells inflate `flen`**, so BM25F's length normalisation makes a
table-heavy document read as denser than it is, and it ranks lower than it
should for a term that appears in its prose.

⚠ **[SR-TABULAR](../../records/0150_tabular.md) did NOT answer this.** It
decided how a tabular document is *chunked* — one passage per row, bounded by
`max_table_rows` — which is a **retrieval** decision about passages. The
proposal's subject is **ranking**: what a table contributes to a document's
field lengths. Both can be right; neither implies the other.

⚠ **The boundary is the load-bearing half of the proposal**, and it survives
unchanged: in decoders, every consumer-owned decoder re-implements ranking
policy in code fux cannot test or version; in `extract.py`, one implementation
and every format inherits it free.

## Definition of done

1. **Measure first, on golden data.** Does a table-heavy document's `flen`
   differ enough from its prose to move a ranking? A pre-registration under
   [SR-RS](../../records/0133_predictions.md) naming the metric, the arms and
   the bar, frozen before the first number.
2. **A null closes this item**, and closing it that way is a success — the
   proposal's own text says a ranking change here needs a verdict and never an
   argument.
3. If it is not null: a compare doc for the field design, then an
   SR-EXTRACTED / SR-RANKING amendment, then the change.

🔴 **Blocked on [W-136](W-136-golden-benchmark.md)** — the corpus this must be
measured on is the golden ladder in fux-lab ([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)),
and the proposal asks for a verdict at 10 000 documents, which is the ceiling
and therefore the right size.

## Unblocked 2026-09-12 — table-heavy documents are in the ladder

The golden ladder carries rate cards, notification matrices, grace tables and
preventive-maintenance schedules — markdown tables inside otherwise short
documents, which is the exact shape this item asks about. Five rungs are frozen
with committed indexes, so `flen` can be read per document without ingesting
anything.

## ✅ MEASURED 2026-09-12 — the mechanism is real; the quality question is not answered

[The run](../regression/2026-09-12-priors-and-tables/report.md) §3.

- **Headroom is large**: 31–35 % of documents carry a table share ≥ 10 %; the
  most table-heavy document's length normaliser would fall **58 %**; `avg_wlen`
  at rung 1 000 moves 151.5 → 133.8.
- **It moves ranking**: 16 of 124 top-1 results change at `rung-01000`, 82 of 124
  top-10 lists.
- **In the predicted direction**: **41 of 44** top-1 changes across three rungs
  promote a *more* table-heavy document; **1** goes the other way.
- 🔴 **The key-free quality endpoint saturates.** A `df == 1` prose term scores
  12/12 in **both** arms at every dilution up to 16 terms — its idf is
  unreachable by length normalisation. **Inconclusive (22d), not a null.**

🔴 **THIS ITEM DOES NOT CLOSE.** Its definition of done says *"a null closes this
item"*. **This is not a null.** The mechanism is confirmed and one-directional,
and whether the new order is *better* is unadjudicated.

**The cheapest way to finish it, and it is already paid for:** the 16 top-1
movers at `rung-01000` are named in
[`evidence/tables-rung-01000-ranking.jsonl`](../regression/2026-09-12-priors-and-tables/evidence/). Once Codex scores
the ladder (W-136 phase 5) those ids can be read off directly — **no new run and
no new corpus**. Only if 16 is too few to clear the floor does this need a
purpose-built graded set.

## Ball, 2026-09-12 — 🟢, and deliberately not 🟡

The cheapest way to finish this waits on W-136 phase 5 (grade the 16 named
top-1 movers, no new run). **That is not the same as being blocked**, and
balling it 🟡 would hide runnable work from an agent, which picks from 🟢 only.

**The unblocked path:** build a graded set over table-heavy documents and answer
*"is the new order better"* without waiting for anybody. It costs more than
reading 16 ids off phase 5; it is available today.

---

## ✅ ANSWERED 2026-09-12 — and what remains is one ruling, not one task

[VERDICT-W144](../regression/2026-09-12-reaim-and-instruments/VERDICT-W144.md) ·
[the run](../regression/2026-09-12-reaim-and-instruments/report.md) §2.

**The endpoint that saturated is fixed by one change: probe terms at `df` 4-23
instead of `df == 1`.** A `df == 1` term's idf is unreachable by length
normalisation, which is why the 2026-09-12 probe scored 12/12 in both arms at
every dilution.

| family | n | hit@1 shipped | hit@1 no-table | p |
|---|---:|---:|---:|---:|
| **main** | 30 | **0 / 30** | **30 / 30** | **0.0000** |
| `inverse` (roles swapped) | 30 | 30 / 30 | 30 / 30 | — |
| `placebo` (no table) | 30 | 30 / 30 | 30 / 30 | — |

**Both pre-declared controls hold.** Verification gate passes on 330/330
documents. Ground truth is **prose density** — the subject says the term 6 times
in ~400 prose tokens, the rival 3 times in ~400 — which is the annotator's
judgement, not the feature under test.

### The threshold is the transferable result, not the 30-0

| nominal table share | ≤ 0.26 | **0.29** | ≥ 0.33 |
|---|---|---|---|
| shipped wins | ✅ 30/30 | 🔴 **0/30** | 🔴 0/30 |

**The ladder's median table share among table-bearing documents is 0.344**, and
31 % of `rung-01000` carries a share ≥ 10 %. **The defect bites at shares real
documents actually have.**

⚠ The transition is a cliff because all 30 probes are built identically. A real
corpus gives a gradient; the cliff **locates** the threshold.

## ✅ Step 1 done 2026-09-15 — the sweep is frozen

[`work/regression/2026-09-15-b-sweep/PRE-REGISTRATION.md`](../regression/2026-09-15-b-sweep/PRE-REGISTRATION.md),
committed before any number. **Steps 2–4 are the run**, and it is `fux-lab`'s:
golden is local-only (W-148 row 1, Arpit 2026-09-14).

**One thing the pre-registration adds that the ruling did not spell out —
DESCENDING ORDER IS PART OF THE DECISION RULE.** *"Ship the first value that
nets positive on all three"* is ambiguous about which order they are tried in,
and it matters: `b = 0.4` is a long way from the literature's `0.75`, so **a
sweep that reported *the best value* would pick the extreme whenever the curve
is flat.** First-that-clears, descending, makes the shipped value the smallest
departure that works.

⚠ **And one consequence worth knowing before the run, not after:** `b` is a
`[bm25f]` key and `fux setup` writes its value out in full — so a new default
**diverges a fresh clone from any repo that has run setup**. That belongs in
the CHANGELOG, and it is not a reason to skip the change.

## ✅ RULED 2026-09-14 (Arpit) — (d), lower `b`, measured first

The compare doc's verdict block carries the ruling. **Agent work, in order:**

1. Pre-register the sweep in `work/regression/<date>-b-sweep/PRE-REGISTRATION.md`:
   `b ∈ {0.75, 0.6, 0.5, 0.4}`, families `dump` · `content` · `main` + `inverse` ·
   `placebo`, decision rule *first value netting positive on all three with
   controls holding*, SR-RS d19 floor at the pair count actually run.
2. Run it on the golden ladder (verdict) and on fux's own docs tree
   (reopen-trigger evidence only).
3. Ship the winning `b` as the `tune.toml [bm25f]` default, amend
   [SR-TUNING](../../records/0135_tuning.md) and
   [SR-RANKING](../../records/0111_ranking.md) in the same change, L3 check,
   two-reader byte equality.
4. If no value wins: (b) + idf guard, its own pre-registration, same bar.
   **(c) is out for 3.0.**

## What was left before the ruling — kept because the argument binds

**This item's clause 2 — *"a null closes this item"* — is not reached.** Clause 3
applies: *a compare doc for the field design, then an SR amendment, then the
change.*

**The compare doc is filed:**
[`work/compare/table-tokens-in-flen.compare.md`](../compare/table-tokens-in-flen.compare.md),
status `proposed`, recommending **(b) exclude table-row tokens from `flen[body]`
only**, with a reopen-trigger.

🔴 **No session may implement it first.** `CLAUDE.md` §Conformance runs: *never
ship a ranking/behaviour change off a single synthetic corpus*, and this is one.

**The gap in the recommendation, stated because it is the thing to press on:**
every probe's table is an **appendix**. There is no probe where the table *is*
the answer — a rate card whose subject is its rows. Option (b) makes such a
document shorter than it reads and gives its rare cell terms more idf leverage.
**Not measured.**

**If (b) is accepted**, the work is small and mostly done: `split_body`'s rule
moves from `tools/quality-controls/table_flen.py` into `ingest/extract.py` (it
already agrees with the committed index on 330/330 and 994/994 documents), then
[SR-EXTRACTED](../../records/0115_extracted-mode.md) is amended in the same
change, then an L3 determinism check, then the re-measurement the
reopen-trigger names.

## 2026-09-13 — the option list gained a fourth, and the gap gained an item

**Arpit, 2026-09-13**, on being told the measured defect: *"this could happen in
the real world — document A could be longer and document B smaller, and one gets
penalised, right?"* **Yes, and that is what length normalisation is FOR.** The
question is only whether the extra length is **verbosity** — the same subject at
greater length — or **scope**, material of another kind. `b` is BM25's dial
between those two readings.

- **[The compare doc](../compare/table-tokens-in-flen.compare.md) gained option
  (d): lower `b`.** It was missing the textbook lever — one key, no schema
  change, and **no structural claim about what a table is**. Its cost is that it
  is global and blunt, and that no run in this project has ever moved `b`
  (`k1`/`b` have no instrument with headroom).
- 🔴 **W-155 RAN on 2026-09-13 and the answer is YES**
  ([verdict](../regression/2026-09-13-table-is-the-answer/VERDICT.md)). It was
  *"the only outstanding test whose result could move the call from (b) to (c)
  or (d)"*, and it moved it.
  - **`dump` 30/30 → 0/30**: when the query term is a **row label** in a
    document that says nothing about it, excluding table cells promotes that
    document **above the prose that answers**.
  - **`content` 0/30 → 30/30**: when the table genuinely IS the answer, (b)
    **fixes** it. Both controls hold.
  - **So (b) is right for two document shapes and wrong for a third, and `flen`
    cannot tell them apart** — the effect is decided by *where the term sits*,
    not by whether the table is an appendix.
  - ⚠ **The YES is the weak kind, declared in the pre-registration before the
    run** — the probe author was looking for the harm. **The arithmetic under it
    is not weak**: (b) cuts the dump's length ~7× while leaving its `tf`.
  - **This item still does not close.** The ruling — accept (b) anyway, move to
    (c), move to (d), or wait for W-156 — is Arpit's, and the measurement is
    now in front of him instead of missing.
- 🔴 **W-156 (ruled 2026-09-14, archived)** carries the reason this
  cannot ship on the evidence it has: **SR-WORK-ENVIRONMENTS puts every
  measurement on golden data, golden is one synthetic corpus, and the
  single-corpus rule therefore cannot be satisfied by any ranking change.**
  That is a conflict between two of Arpit's rulings, not a gap in this item.

⚠ **This item is still one ruling — accept or override — and it is still his.**
Neither new item decides it.
