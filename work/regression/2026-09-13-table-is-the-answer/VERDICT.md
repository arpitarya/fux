---
type: Verdict
description: "W-155's pre-registered question, answered YES: excluding table cells from flen promotes a data dump above the prose that answers, 30 of 30. And the YES is the weak kind, exactly as the pre-registration said it would be."
run: 2026-09-13-table-is-the-answer
item: W-155
pre_registration: work/regression/2026-09-13-table-is-the-answer/PRE-REGISTRATION.md
classification: informed
name: "the table-is-the-answer gap — does excluding table cells promote a document above a better answer?"
prediction: W-155
verdict: PASS
ruling: "YES, 30 of 30 — when the query term is a ROW LABEL in a document that says nothing about it, excluding table cells from flen promotes that document above the prose that answers (hit@1 30/30 -> 0/30, p < 0.0001, both controls holding). The mirror family is 30/30 the other way, so (b) fixes the rate-card case and breaks the data-dump case: the effect is decided by WHERE the term sits, and flen cannot see that. PASS means the pre-registered question was answered, not that (b) is endorsed — it is the weak kind of YES the pre-registration declared in advance, and the recommendation stays Arpit's"
filed: 2026-09-13
---

> **`verdict: PASS` means the pre-registration was ANSWERED**, which is the only
> vocabulary this register has (`PASS · FAIL · INCONCLUSIVE · VOID`). It is not
> an endorsement of option (b) — the answer it returns is **against** (b)'s
> stated case. Read `ruling:` above, and §"What this verdict does NOT do" below.

# VERDICT — the table-is-the-answer probes

**The pre-registered question**
([PRE-REGISTRATION.md](PRE-REGISTRATION.md) §2, frozen in commit `a414012`
before a single number existed):

> When a document's table carries the query term, does excluding table tokens
> from `flen[body]` promote that document **above** a prose document that better
> answers the query?

## 🔴 YES. Thirty of thirty.

| family | `hit@1` shipped | `hit@1` no-table | discordant | net | p |
|---|---:|---:|---:|---:|---:|
| **`dump`** — the question | **30 / 30** | **0 / 30** | 30 | **−30** | < 0.0001 |
| `content` — the upside | 0 / 30 | 30 / 30 | 30 | +30 | < 0.0001 |
| `main` — the appendix case | 0 / 30 | 30 / 30 | 30 | +30 | < 0.0001 |
| `inverse` — control | 30 / 30 | 30 / 30 | 0 | 0 | — |
| `placebo` — control | 30 / 30 | 30 / 30 | 0 | 0 | — |

The bar is [SR-RS](../../../records/0133_predictions.md) decision 19: at 30
discordant pairs, **a net of 12**. The `dump` family returns **30**.

**Both controls hold.** `inverse` answers 30/30 in both arms, so the
counterfactual is not simply promoting table-heavy documents; `placebo` is
identical in both arms, so nothing other than the feature is moving.

**The verification gate passed on 450 of 450 documents** — the recomputed body
length equals the committed `flen` everywhere, so this measured the shipped
pipeline.

## What the number means, stated as the pre-registration required

**Per the decision rule (§5): `c` clears the bar → (b) over-promotes → the gap
does NOT close, and the recommendation moves to (c) or (d).**

⚠ **AND IT IS THE WEAK KIND OF YES, which §8 declared in advance.** *"Favourable
wording can manufacture a pass; it cannot manufacture a failure. A NO here is
strong and a YES is weak — a YES would need independent probes before anybody
believed it."* **That clause binds this result.** The probe author was looking
for the harm and built a document shape that produces it; the p-value is honest
arithmetic over a construction that was chosen.

🔴 **But the mechanism underneath is ARITHMETIC, not a corpus property, and that
is what survives the weakness.** In the `dump` family option (b) cuts the export's
length from ~1 050 tokens to ~150 while leaving its `tf` at 3. **tf per unit
length roughly septuples.** No corpus can avoid that; the only corpus in which it
does not happen is one where no document has the query term in a table cell.

**So the finding is not *"(b) is wrong"* — it is narrower and sharper:**

> **(b)'s effect is decided by WHERE the query term sits, not by whether the
> table is an appendix.** The compare doc's recommendation assumed the first
> always implies the second. `main` and `content` show (b) is right when the
> term is in prose or is the table's subject; `dump` shows it is wrong when the
> term is a row label in material that says nothing about it — **and `flen`
> cannot tell those two apart, because it is a length and the difference is
> about meaning.**

## The replication, which was not part of the question

**`main` reproduces the 2026-09-12 filed run EXACTLY** — 0/30 shipped, 30/30
counterfactual, on a corpus with 150 probe terms instead of 90, a different
filler distribution and every `df` therefore different
([`2026-09-12-reaim-and-instruments/evidence/w144-graded.jsonl`](../2026-09-12-reaim-and-instruments/evidence/w144-graded.jsonl)).
That is a free consistency check on the harness and it passed.

## What this verdict does NOT do

- **It rules nothing.** [The compare doc](../../compare/table-tokens-in-flen.compare.md)
  is Arpit's to accept or override ([W-144](../../open/W-144-structure-aware-extraction.md)),
  and this run changes no code.
- **It does not say (c) or (d) is right.** It says (b)'s stated case is
  incomplete, and names the shape of the case it misses.
- **It measures no corpus outside this generated probe set.** Prevalence is
  [W-156](../../open/W-156-prevalence-outside-golden.md) and needs a ruling.
- **It is `informed`** — the probes were authored by the reader of the results.
  No delta here may be compared with a blind run.
