---
type: Report
description: "Thirty probes where the table carries the query term, in both directions — the one gap the table-in-flen compare doc names in its own recommendation. Pre-registered and frozen in git before the first number."
run: 2026-09-13-table-is-the-answer
item: W-155
classification: informed
engine: fux-engine 2.0.0-alpha.7
pre_registration: work/regression/2026-09-13-table-is-the-answer/PRE-REGISTRATION.md
filed: 2026-09-13
---

# The table-is-the-answer probes

**The verdict is [`VERDICT.md`](VERDICT.md): YES, 30 of 30, and it is the weak
kind of YES the pre-registration declared in advance.** This is the run.

---

## 1. Authorship and classification — `informed`

| artifact | author | could reach the queries? | could reach the judgments? |
|---|---|---|---|
| [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) | Claude, this session | wrote them | wrote them |
| the two new probe families | Claude, this session | wrote them | wrote them |
| the corpus (generated) | `w144_graded.py gen`, deterministic, seed 20260912 | mechanical | mechanical |
| this report and the verdict | Claude, this session | yes | yes |

🔴 **`informed`, and no delta here may be compared with a blind run.** It is not
an "upper bound" — that would claim a bounded magnitude a leak does not have.
**Not a generalisation estimate.**

⚠ **The pre-registration was committed ALONE, ahead of the first number**
(`a414012`), so the freeze is checkable in `git log` rather than asserted. The
rest of the working tree is a peer session's staged rename and was deliberately
excluded from that commit.

## 2. What was built

Two families added to
[`tools/quality-controls/w144_graded.py`](../../../tools/quality-controls/w144_graded.py)
— **extended, never a second harness**, as the item required. They are the first
probes in which the **table carries the query term**; every family before them
used a table of unrelated cells, which is an *appendix*.

| family | table-heavy document | prose document | correct |
|---|---|---|---|
| **`dump`** | ~150 prose tokens, `T`×1 · table ~900 tokens, `T` in **3 row labels** | ~400 prose tokens, `T`×**6** | **the prose document** |
| **`content`** | ~150 prose tokens, `T`×1 · table ~900 tokens, `T` in **6 row labels** | ~400 prose tokens, `T`×**3** | **the table-heavy document** |

- **Terms 90–149**, so the existing 90 probes keep their terms and families —
  `terms(n)` is a prefix of `terms(n+k)`, which is why extending the list cannot
  renumber what exists.
- **Short prose on the table-heavy side is the construction, not an economy.** A
  rate card is mostly rows; 400 tokens of prose as well would make it a prose
  document with an appendix, which is the family already measured.
- **The term is placed in the first column, the label position**, because that
  is where a rate card carries its subject. Position carries no weight in BM25F
  — `body` tf is a count — so this is legibility, not a thumb on the scale.

## 3. The result

```
   family    n   hit@1 shipped   hit@1 no-table   discordant    net
     main   30         0 /30           30 /30             30    +30
  inverse   30        30 /30           30 /30              0     +0
  placebo   30        30 /30           30 /30              0     +0
     dump   30        30 /30            0 /30             30    -30
  content   30         0 /30           30 /30             30    +30
```

**`corpus n=450 · avg_wlen 532.7 → 291.4` with table tokens out.** Verification
gate: **450 / 450** documents' recomputed body length equals the committed
value.

- 🔴 **`dump` is the answer, and it is total.** The shipped ranker gets every one
  of the thirty right; the counterfactual gets every one wrong.
- **`content` is the mirror image** — the shipped ranker gets all thirty wrong,
  the counterfactual all thirty right. **(b) genuinely fixes the rate-card case.**
- **Both controls hold.** `inverse` 30/30 in both arms; `placebo` identical.

## 4. Headroom — and why zero here is the OPPOSITE of decision 22d

Both new families report **improvement headroom 0/30 and regression headroom
0/30**, and that is not the null [SR-RS](../../../records/0133_predictions.md)
decision 22d warns about.

- **22d's null is `discordant == 0`** — nothing moved, so nothing was measured.
- **Here `discordant == 30`** — *everything* moved. Both headroom counts are zero
  because **no probe is right in both arms or wrong in both**, which is the
  maximal-information case.

⚠ **The harness printed the same warning for both until this run.** It now
distinguishes them by the discordant count, because calling a total flip a null
is how a result gets thrown away.

## 5. What is engineered, and what is not

**Engineered:** the pair shapes. Every family is constructed so that one arm
wins by arithmetic, which is why every p-value is < 0.0001. **These are
mechanism demonstrations with a statistical form, not samples from a
population**, and the p-values should be read as *"the construction does what it
was built to do"* rather than as evidence about any corpus.

**Not engineered, and this is what survives:** the arithmetic. In `dump`, (b)
cuts the export's length from ~1 050 tokens to ~150 and leaves its `tf` at 3, so
**tf per unit length roughly septuples**. That is a property of the
counterfactual, not of the corpus. The only corpus in which it does not happen
is one where no document carries the query term in a table cell.

## 6. A replication nobody asked for, and it passed

**`main` reproduces the 2026-09-12 filed run exactly** — 0/30 shipped, 30/30
counterfactual — on a corpus with 150 probe terms instead of 90, different
filler and therefore a different `df` for every term
([the earlier rows](../2026-09-12-reaim-and-instruments/evidence/w144-graded.jsonl)).
Probe-term `df` here is **2–14**, so the `df == 1` saturation that made the
2026-09-12 endpoint Inconclusive is not in play.

## 7. 🔴 A scope question this run does NOT resolve, and will not pretend to

**W-155's own scope line reads:** *"OUT: any corpus outside `work/golden/` —
that is [W-156](../../open/W-156-prevalence-outside-golden.md) and it needs a
ruling first."* **This run used a generated probe corpus, not `work/golden/`.**

**Why it was run that way, said plainly rather than defended:**

- The same item's definition of done says *"the generator is
  `tools/quality-controls/table_flen.py` … **extend it, do not write a second
  one**"*, and the graded generator it points at
  ([`w144_graded.py`](../../../tools/quality-controls/w144_graded.py)) **builds
  its own synthetic probe corpus**. Extending it and staying inside
  `work/golden/` are not both possible.
- **The precedent is filed and cited.** VERDICT-W144 and VERDICT-W115 both ruled
  on generated probe corpora, on 2026-09-12, and both are in the register.
- The reading taken here is that W-155's OUT clause is about **prevalence** — do
  not go measuring how common this is on somebody's real corpus — and that a
  constructed probe set is an **instrument**, not a corpus.

⚠ **That reading is a judgement, and it may be wrong.**
[SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md) veto condition
2 says, literally, *"a measurement run is filed on data other than the golden
test data"* reopens the decision. **Under a literal reading this run fires it —
and so does every probe-instrument run filed since 2026-09-12.** That is exactly
the conflict [W-156](../../open/W-156-prevalence-outside-golden.md) exists to
resolve, and it is Arpit's.

**Nothing here depends on the answer.** If the ruling goes the other way, this
run is reclassified, not deleted — the numbers stand as measured and the
instrument is reusable on whatever corpus is then legal.

## 8. What this run does not do

- **It implements nothing.** (b), (c) and (d) are all untouched;
  [W-144](../../open/W-144-structure-aware-extraction.md) is Arpit's ruling.
- **It measures no real corpus.** Prevalence outside generated probes is
  [W-156](../../open/W-156-prevalence-outside-golden.md) and needs a ruling first.
- **It closes no prediction.**
