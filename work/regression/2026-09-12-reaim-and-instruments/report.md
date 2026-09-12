---
type: Report
description: "Three items that had no instrument now have one each. W-142's distractor control is retired — its endpoint sits at the corpus base rate under every setting of both fields. W-144's counterfactual ranks better above a table share of ~0.29. W-115's fence-aware grammar ranks better; its key-depth cap shows no detected ranking effect."
items: W-142, W-144, W-115
run: 2026-09-12-reaim-and-instruments
classification: informed
engine: fux-engine 2.0.0-alpha.7
pre_registration: work/regression/2026-09-12-reaim-and-instruments/PRE-REGISTRATION.md
filed: 2026-09-12
---

# Three instruments, three answers

**The instruments and their bars were committed before the first number** —
`aff3c82`, and `git log` proves the ordering. That is the habit
[the priors run](../2026-09-12-priors-and-tables/ANALYSIS.md) §7 named as owed
and could not claim for itself.

**Every endpoint is key-free.** No arm reads the sealed answer key, so none of
these results waits on [W-145](../../open/W-145-codex-regenerates-the-key.md).

---

## Authorship

| artifact | author | could reach the queries? | could reach the answers? |
|---|---|---|---|
| `body_control.py`, `w144_graded.py`, `w115_instrument.py`, `verdict.py` | Claude, this session | — | — |
| the W-144 and W-115 corpora and their probes | Claude, this session | wrote them | wrote them — truth is mechanical from the generator's declarations |
| the golden ladder (W-142's corpus) | Claude, 2026-09-12, built blind | no | no |
| the 124 released questions | Codex/Claude stopgap, [W-145](../../open/W-145-codex-regenerates-the-key.md) | — | **not read by any arm here** |
| this analysis | Claude, this session | yes | no |

**`informed`.** No delta against any other run is stated.

---

## 0. One change to how every verdict is computed, and it matters

All three tools were about to hard-code *"net >= 6"*.
[ADR-RS](../../../docs/adr/0133_predictions.md) decision 19 calls 6 the **floor
of all floors** — the bar that applies *before* the discordant count is known —
and says the real bar **rises with the flips**: 20 flips need 10, 50 need 16.

**A tool comparing against 6 alone would have passed a net of 8 on 30 discordant
pairs, which decision 19's own table refuses.** So the verdict is now the
**exact two-sided binomial p-value on the discordant pairs**, which is what that
table is computed from, in `tools/quality-controls/verdict.py`. It reuses
`resolution.py`'s arithmetic rather than adding a second implementation.

It reproduces the table exactly, and it re-reads the heading control's filed
numbers the same way: `b=16 c=21`, **p = 0.5114**, which is *no detected change*
under either reading.

---

## 1. W-142 — the control is **retired**, and the reason is not the one anyone expected

The pre-registration took the **re-aim**: the heading rebuild found `bm25f.heading`
3.0 → 0.0 moved the distractor count by a net of 5, so the suspicion was that
the `ext/sibling/` documents win on **body similarity** instead.

**They do not win on body similarity either.** Arms `bm25f.body` at 1.0
(shipped), 0.5, 0.25 and 0.0 (off), 124 questions, k = 5, `rung-01000`:

| `bm25f.body` | sibling hits | **per query** | seed hits | queries with >= 1 sibling | empty |
|---:|---:|---:|---:|---:|---:|
| 1.0 (shipped) | 256 | **2.06** | 272 | 90 / 124 | 0 |
| 0.5 | 259 | **2.09** | 274 | 88 / 124 | 0 |
| 0.25 | 261 | **2.10** | 281 | 88 / 124 | 0 |
| **0.0 (off)** | 262 | **2.11** | **158** | 80 / 124 | 5 |
| — | — | **1.96** | — | *expected from corpus composition alone* | |

`b = 42`, `c = 41`, **discordant 83, net 1, p = 1.0000** — a bar of 19 at that
count, and a p-value that could not be further from clearing it.

### 🔴 The endpoint is pinned at the corpus base rate

392 of 1 001 documents at `rung-01000` are `ext/sibling/`. **A top-5 drawn at
random from that corpus holds 1.96 of them.** Every arm observes 2.06–2.11 —
including the field switched **off entirely**.

**So the count is not measuring ranking. It is measuring how much of the corpus
is `ext/sibling/`.** Re-aiming it at a third field would reproduce this result,
because the field is not what is being measured.

⚠ **The arm works; the endpoint is inert.** Seed hits fall **272 → 158** and 5
queries return nothing at all when `body` goes to 0.0, so the weight really is
being applied. This is not a broken configuration.

### What that settles

- **C4's premise was never the problem, and neither was the saturation.** The
  2026-08-28 control asked a boolean about an event that never happens; the
  2026-09-12 rebuild asked a count; **this run shows the count has nowhere to
  go**. Three designs, one endpoint, and the endpoint is the fault.
- **The `heading` negative control is retired**, not re-aimed again.
- 🔴 **C1 and C3 rest on generator assertions, and have since 2026-08-28.**
  That is now stated plainly rather than pending a control that was always
  going to fail.

**A control that is measuring corpus composition is worse than no control**: it
returns a number, the number is stable, and nothing about it is about the
engine.

---

## 2. W-144 — excluding table tokens from `flen` **ranks better**, above a threshold

The [2026-09-12 run](../2026-09-12-priors-and-tables/report.md) §3 confirmed the
mechanism and saturated on quality: a `df == 1` prose term scored 12/12 in both
arms at every dilution, because its idf is unreachable by length normalisation.

**The fix is one change: probe terms at `df` in the tens.** Each pair shares a
nonsense term the **subject** says 6 times in ~400 prose tokens and the
**rival** says 3 times in ~400 prose tokens; the subject also carries a table
the rival does not. *More about the term in the same amount of prose* is the
annotator's judgement, not the feature under test.

**Verification gate first:** the recomputed body length equals the committed
value on **330 / 330** documents, so this is the shipped pipeline.
`avg_wlen` 457.6 → 293.0. Probe-term `df` **4–23**.

| family | n | hit@1 shipped | hit@1 no-table | discordant | net | p |
|---|---:|---:|---:|---:|---:|---:|
| **main** | 30 | **0 / 30** | **30 / 30** | 30 | +30 | **0.0000** |
| `inverse` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | — |
| `placebo` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | — |

**Both controls hold.** `inverse` (roles swapped, the prose-only document
relevant) answers 30/30 in **both** arms — so the counterfactual is not simply
promoting table-heavy documents. `placebo` (no table anywhere) is identical in
both arms — so nothing but the feature is moving.

### The dose-response, because one point is the author's choice

🔴 **A 30–0 at one table size is partly a statement about that size.** Held
fixed except the table, regenerated from the same seed at each step:

| table tokens | nominal share | hit@1 shipped | hit@1 no-table | p | outcome |
|---:|---:|---:|---:|---:|---|
| 0 | 0.00 | 30 / 30 | 30 / 30 | 1.0000 | inconclusive |
| 50 | 0.11 | 30 / 30 | 30 / 30 | 1.0000 | inconclusive |
| 100 | 0.20 | 30 / 30 | 30 / 30 | 1.0000 | inconclusive |
| 140 | 0.26 | 30 / 30 | 30 / 30 | 1.0000 | inconclusive |
| **160** | **0.29** | **0 / 30** | **30 / 30** | **0.0000** | **no-table better** |
| 200 | 0.33 | 0 / 30 | 30 / 30 | 0.0000 | no-table better |
| 400 – 2 000 | 0.50 – 0.83 | 0 / 30 | 30 / 30 | 0.0000 | no-table better |

**The defect switches on between a table share of 0.26 and 0.29** at this tf
ratio, and does not switch off again.

⚠ **The transition is a cliff because all 30 probes are built identically.** A
real corpus would give a gradient. What the cliff locates is the *threshold*,
and that is the number to carry forward.

### Why that threshold is the finding

From the same ladder, [measured on 2026-09-12](../2026-09-12-priors-and-tables/report.md) §3:
**31 % of `rung-01000` carries a table share >= 10 %**, and the **median share
among table-bearing documents is 0.344** — *above* the threshold at which the
shipped ranker starts losing here.

**The defect bites at table shares that real documents in the golden corpus
actually have.** That is a stronger statement than the mechanism confirmation
and it is what W-144 was missing.

🔴 **This is not a licence to ship the change.** `CLAUDE.md` §Conformance runs:
*never ship a ranking/behaviour change off a single synthetic corpus.* The
lifecycle step is a compare doc, and it is filed as
[`work/compare/table-tokens-in-flen.compare.md`](../../compare/table-tokens-in-flen.compare.md)
with a **proposed** verdict for Arpit.

---

## 3. W-115 — measured at last, and the answer splits

### 🔴 First, a correction to the previous run's diagnosis

[The priors run](../2026-09-12-priors-and-tables/report.md) §4 concluded: *"the
ladder carries `.md`, `.txt`, `.yaml`, `.eml` and `.html` — not one of the
formats W-115 touches."* **That sentence is wrong**, and re-deriving it changed
the fix. `git diff 94231b2 676e973 -- src/fux/ingest/extract.py`:

- **`.rst`, `.adoc` and `.org` already had their own regexes before W-115 and
  were not changed by it.** They are named in the diff only as context.
- What W-115 changed for ranking is **Markdown's grammar becoming fence-aware**
  — and Markdown is the default for every extension without its own pattern,
  `.txt` and every decoded document included — and **a key stopping being a
  heading below depth 2**.

**The ladder has the right formats and the wrong content.** Measured on
`rung-01000`: **1** of 800 `.md`/`.txt` documents carries a `#` line inside a
code fence; **2** of 146 `.yaml` documents nest deeper than two levels. ADR-RS
decision 23b — a data defect, not a null.

### The corpus, and its headroom proof

300 documents, 30 probes per family, each family on a **disjoint** slice of the
topic vocabulary. Both arms are HEAD; `old` patches two seams —
`ingest.extract._headings_and_body` to the fence-blind regex and `_label` to a
heading at every depth, **on all four modules that hold a reference to it**.

**`--selftest` (ADR-RS 22c(b)), run and reported before any ranking number:**

```
documents read in both arms:                         180 / 180
decoys whose heading set differs between the arms:    60 / 90
subjects whose heading set differs between the arms:  0 / 90
  depth    30 / 30      fence    30 / 30      placebo  0 / 30
SELFTEST PASSES
```

Every treated decoy is separable by the property under test, **no placebo decoy
is**, and no subject is. **Headroom is proven, not observed.**

### The result

| family | n | hit@1 old | hit@1 new | decoy@1 old | decoy@1 new | discordant | net | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **fence** | 30 | **0 / 30** | **30 / 30** | **30** | **0** | 30 | +30 | **0.0000** |
| `depth` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | 0 | 0 | — |
| `placebo` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | 0 | 0 | — |

**`fence`: the shipped arm ranks better, decisively.** The pre-W-115 engine puts
the document whose *only* mention of the term is a shell comment inside a
```bash block at **rank 1 in all 30 probes**. The shipped engine puts it at rank
1 in **none**.

**`depth`: Inconclusive (22d).** The key-depth cap demonstrably changes what is
mined as a heading — the selftest proves it on all 30 — and it **does not change
which document ranks first** on this endpoint.

### The dose-response, over how much prose evidence the correct document has

| subject tf | fence hit@1 old → new | fence decoy@1 old → new | p | depth |
|---:|---|---|---:|---|
| 1 | 0/30 → 0/30 | 30 → 30 | 1.0000 | inconclusive |
| 2 | 0/30 → 0/30 | 30 → 30 | 1.0000 | inconclusive |
| **3** | **0/30 → 30/30** | **30 → 0** | **0.0000** | inconclusive |
| 4 | 0/30 → 30/30 | 30 → 0 | 0.0000 | inconclusive |
| 6 | 0/30 → 30/30 | 30 → 0 | 0.0000 | inconclusive |
| 8 | 0/30 → 30/30 | 30 → 0 | 0.0000 | inconclusive |

- **`decoy@1 old` is 30/30 at every single `tf`.** A fenced shell comment took
  the top slot in the pre-W-115 engine **however much genuine prose evidence the
  correct document had**. Heading weight 3.0 on three fenced lines beat eight
  prose sentences.
- Below `tf = 3` the fix is not enough to put the *right* document first either
  — it only stops the wrong one winning. That is where the improvement begins,
  not where the defect does.
- **`depth` is inconclusive at every `tf` tested**, on both endpoints.

⚠ **`decoy@1` is reported and never adjudicated.** The pre-registered endpoint
is `hit@1`. `decoy@1` was already in the instrument when it was committed and
is the more sensitive question, so it is shown — but the verdict rests on the
bar that was frozen.

---

## 4. What this run does not do

- It changes **no default, weight or shipped behaviour**. Every arm is a
  measurement configuration.
- It states **no delta against any other run**.
- It measures nothing above 10 000 documents.
- It does **not** authorize W-144's change. That is a compare doc with a
  proposed verdict, and Arpit's call.
- It does not re-open `depth`. *No detected ranking effect on this endpoint* is
  the recorded outcome, and W-115 shipped it as a **noise-reduction** change,
  not a ranking one.

---

## Reference

- [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) — frozen at `aff3c82`, before the first number
- [`ANALYSIS.md`](ANALYSIS.md) — repro commands and what each item owes next
- [`VERDICT-W142.md`](VERDICT-W142.md) · [`VERDICT-W144.md`](VERDICT-W144.md) · [`VERDICT-W115.md`](VERDICT-W115.md)
- [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 19, 22, 23 ·
  [ADR-DECODE](../../../docs/adr/0139_decode.md) 14-16 ·
  [ADR-EXTRACTED](../../../docs/adr/0115_extracted-mode.md) ·
  [ADR-TABULAR](../../../docs/adr/0152_tabular.md)
