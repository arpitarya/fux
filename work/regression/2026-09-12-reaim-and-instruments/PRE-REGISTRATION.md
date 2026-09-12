---
type: Pre-Registration
description: "Three instruments built for three items that had none: W-142's re-aimed distractor control, W-144's graded table set, and W-115's fence/depth corpus. Arms, metrics and bars, frozen before the first number."
items: W-142, W-144, W-115
run: 2026-09-12-reaim-and-instruments
classification: informed
engine: fux-engine 2.0.0-alpha.7
filed: 2026-09-12
---

# Pre-registration — three instruments, three items

**This file is committed before any of the three tools is run.** That is the
habit [the previous run's ANALYSIS §7](../2026-09-12-priors-and-tables/ANALYSIS.md)
named as owed: *"commit the instrument before running it"*. The ladder run did;
the priors run did not; this one does, and git can prove the ordering.

---

## 0. The bar, stated once for all three

**[ADR-RS](../../../docs/adr/0133_predictions.md) decision 19's floor of all
floors is `net >= 6`.** A net of 1-5 cannot clear α = 0.05 at any discordant
count. It is not lowered, re-expressed, or supplemented with a looser secondary
bar for any endpoint below.

**Decision 22 applies to every endpoint**: headroom is reported per direction,
labelled `observed` or `proven`, and a zero in a direction is **Inconclusive**
in that direction (22d), never *"no detected change"*.

**Classification is `informed`.** Every instrument here was authored by Claude
in this session. No arm reads the sealed answer key, so nothing here waits on
[W-145](../../open/W-145-codex-regenerates-the-key.md) — and **no delta against
any other run is stated.**

---

## 1. W-142 — the re-aimed distractor control

**The question.** The heading control's rebuild found that switching
`bm25f.heading` from 3.0 to 0.0 moves the heading-matched distractor count by a
**net of 5** over 124 queries — below the floor. So heading matching is not what
puts `ext/sibling/` documents in the window. **Is body similarity?**

| | |
|---|---|
| **tool** | `tools/quality-controls/body_control.py` |
| **corpus** | the golden ladder, `rung-01000` (994 documents, 392 `ext/sibling/`) |
| **queries** | all 124 released questions, `questions.jsonl` — **no answer key is read** |
| **arms** | `bm25f.body` at **1.0** (shipped), 0.5, 0.25, **0.0** (off) |
| **k** | 5 |
| **endpoint** | count of `ext/sibling/` locations in the top-5, **per query** |
| **paired unit** | the query. `b`/`c` are queries whose sibling count rises/falls with the field off |

**The bar.** `net >= 6` between the 1.0 and 0.0 arms → the body field is the
mechanism, headroom is **proven** under 22c(a), and the control can adjudicate.
`discordant == 0` → Inconclusive (22d). `0 < net < 6` → not established.

**Decided in advance:** `rung-seed` is refused (no `ext/` document at all — the
2026-08-28 saturation). `body = 0.0` is a degenerate ranker and is an off arm,
not a proposal.

**What a result closes.** W-142's open choice is *re-aim or retire*. This run
takes the re-aim. **Whichever way the number falls, the item closes** — the
control either discharges or is retired with its premise stated as unsupported,
and C1/C3's dependence is recorded either way.

---

## 2. W-144 — the graded set over table-heavy documents

**The question.** Excluding table cells from `flen` moves ranking in the
predicted direction (41 of 44 top-1 changes). **Is the new order better?**

| | |
|---|---|
| **tool** | `tools/quality-controls/w144_graded.py` |
| **corpus** | purpose-built, deterministic, seed `20260912` — 24 probe pairs + 150 filler |
| **arms** | shipped `flen`, and `flen` with table-row tokens removed from `body` — **`avg_wlen` recomputed in each arm, never borrowed** |
| **endpoint** | `hit@1` against the declared relevant document |
| **paired unit** | the probe |

**Ground truth, and why it is not circular.** Each pair shares one nonsense
term. The **subject** says it 6 times in ~400 prose tokens; the **rival** says
it 3 times in ~400 prose tokens. Everything else about the two documents is the
same shape. *More about the term, in the same amount of prose* is the relevance
judgement an annotator makes and the one BM25 exists to encode — it is not the
feature under test.

**Headroom by construction, and why the last endpoint had none.** Every probe
term also appears once in each filler document, so its `df` is in the tens.
The 2026-09-12 endpoint used `df == 1` terms whose idf no length normalisation
can reach; that is the single change.

**Two controls, both pre-declared:**

- **`inverse`** — roles swapped, the prose-only document is relevant. **Both
  arms must answer it.** This catches a counterfactual that merely promotes
  table-heavy documents always.
- **`placebo`** — no table anywhere. **The arms must score identically.** If it
  moves, the `main` number is not attributable and the run is void.

**The bar.** `main` family, `net >= 6` → the named arm ranks better. `net < 6`
→ no detected change. `discordant == 0` → Inconclusive (22d). **A control
failure voids the `main` number regardless of its net.**

**What a result closes.** W-144's definition of done says *"a null closes this
item"* and the mechanism is already confirmed. A `better`, a `no detected
change` or a `worse` all adjudicate the open question and close it; only a
**control failure** leaves it open.

---

## 3. W-115 — the fence/depth corpus

**The question.** Did W-115's ranking half improve ranking? Three corpora have
returned zero.

🔴 **A correction is registered here, before any number.** The previous run's
diagnosis — *"the ladder carries `.md`, `.txt`, `.yaml`, `.eml` and `.html` —
not one of the formats W-115 touches"* — **is wrong**, and re-deriving it
changed the fix. `git diff 94231b2 676e973 -- src/fux/ingest/extract.py` shows
`.rst`, `.adoc` and `.org` already had their own regexes **before** W-115 and
were **not changed by it**. What changed for ranking is:

1. **Markdown's heading grammar became fence-aware** — and Markdown is the
   default for every extension without its own pattern, `.txt` and every
   decoded document included.
2. **A key stops being a heading below depth 2** (`decode/json.py::_label`,
   shared by `jsonl`, `xml`, `yaml`).

**So the ladder has the right formats and the wrong content.** Measured on
`rung-01000`: **1** of 800 `.md`/`.txt` documents carries a `#` line inside a
code fence, and **2** of 146 `.yaml` documents nest deeper than two levels. That
is ADR-RS decision 23b — a data defect, not a null.

| | |
|---|---|
| **tool** | `tools/quality-controls/w115_instrument.py` |
| **corpus** | purpose-built, deterministic, seed `20260912` — 20 probe triples + 120 filler |
| **arms** | **both are HEAD.** `old` monkey-patches two seams: `ingest.extract._headings_and_body` to the pre-W-115 fence-blind regex, and `decode.json._label` to a heading at every depth |
| **endpoint** | `hit@1` against the declared subject document |
| **paired unit** | the probe |

**Why not check out 94231b2.** 25 files and 1 290 lines changed between the two
commits. Running that tree would measure the whole range and call it W-115 —
the confound W-116's report had to unpick by hand. `max_phrases` stays at HEAD's
default in **both** arms, so it is not a variable here at all.

**Ground truth.** A **subject** document is genuinely about topic `T` — title,
headings and prose. A **decoy** is about something else and its only connection
to `T` is an incidental fenced shell comment (`# T ...`) or a fifth-level config
key. A shell comment inside a code block does not make a runbook a document
about that phrase; that is the judgement, and W-115 is the claim that the engine
should share it.

**Headroom proof (22c(b)).** `--selftest` asserts the two arms disagree about
**every** decoy's heading set and about **no** subject's. A run whose selftest
fails is measuring something else and says so. The selftest is run and reported
before any ranking number.

**`placebo` family:** the same question shape with no fence and no deep key. The
arms must score it identically.

**The bar.** Per family (`fence`, `depth`), `net >= 6` → the named arm ranks
better. `net < 6` → no detected change. `discordant == 0` → Inconclusive (22d).

**What a result closes.** W-115's definition of done is four numbered items: a
corpus that both grades and has headroom, a frozen pre-registration, a filed run
with per-probe rows, and *"whatever it returns — including no detected change —
recorded, and the 'unmeasured' language removed from every document that carries
it"*. All four are discharged by this run **provided the selftest passes**. If
the selftest fails the corpus is the fourth that cannot see the change and the
item stays open with a fourth named reason.

---

## 4. What this run does not do

- It does not change a default, a weight, or a shipped behaviour. Every arm is a
  measurement configuration.
- It states **no delta against any other run**.
- It says nothing about corpora above 10 000 documents, and measures none.
- **No arm reads the sealed answer key**, by any means. Every endpoint here is
  key-free and mechanically true from the generator's own declarations.

---

## 5. Amendments — both made BEFORE the first number, both in git

⚠ **This section is appended, never a rewrite.** The file above is as committed
at `aff3c82`. Two things changed between that commit and the first measurement,
and each is recorded here rather than edited into the text it contradicts.

### 5a. The verdict rule is the exact test, not a flat floor

**As registered:** *"`net >= 6`"*, §0.

**As run:** the **exact two-sided binomial p-value on the discordant pairs**,
clearing α = 0.05 — `tools/quality-controls/verdict.py`, which reuses
`resolution.py`'s arithmetic.

**Why.** `net >= 6` is
[ADR-RS](../../../docs/adr/0133_predictions.md) decision 19's **floor of all
floors** — the bar that applies *before* the discordant count is known. The real
bar **rises with the flips**: 20 flips need a net of 10, 50 need 16. A tool
comparing against 6 alone would have **passed a net of 8 on 30 discordant
pairs**, which decision 19's own table refuses.

🔴 **This is strictly stricter, which is the only direction an amendment may
go.** At every discordant count above 6 the exact test demands at least what the
flat floor demanded and usually more. **α did not move**, and no threshold was
loosened.

### 5b. The probe sets were widened

**As registered:** 24 probe pairs (W-144), 20 probe triples (W-115).

**As run:** 30 probes per family in both — 90 probes each.

**Why.** Eight probes per family cannot clear the bar except by a total sweep,
which makes a null uninformative for the reason decision 22d exists. The topics
are composed rather than listed so widening is mechanical.

⚠ **A larger `n` makes a given net easier to reach, and that is exactly why 5a
had to land with it.** Under a flat floor of 6, widening would have loosened the
test. Under the exact test the bar tracks the discordant count, so it does not.

**Neither change is a threshold move.** No number existed when either was made.
