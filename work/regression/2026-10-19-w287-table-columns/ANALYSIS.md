---
type: Analysis
run: 2026-10-19-w287-table-columns
item: W-287
date: 2026-10-19
classification: informed
---

# ANALYSIS — W-287 stage B, before the verdict

**There is no result to analyse yet, by design.** The endpoints are computed
only by `evidence/decide.py`, which Arpit runs ([report](report.md)). This file
records what the run itself taught, which needs no score.

## 1. The G0 gate found a real defect, and it was not in the mechanism

The first capture STOPPED: with the ranking key **off**, 2 of 102 questions
cited a different member of an exact-score tie group than the engine without
row metadata. `rescore` and `assemble` broke ties on the *displayed* locator,
and C3 — a presentation change, `book.xlsx#Sheet!R12` — had changed that string.
Nothing was scored differently; the budget simply seated a different tied row.

- **Why it matters beyond this run:** an address is presentation, and here a
  presentation change silently moved an order. No unit test asked the question;
  the gate's literal definition — *off equals the engine without it* — did.
- **The fix generalises:** ties now break on `order_key`, the positional
  locator, everywhere in the refer plane, in both runtimes
  ([SR-REFER](../../../records/0127_refer-plane.md) decision 28a).

## 2. A threshold that "changes what is indexed" did not

The work item put the header-fill threshold in `[index]` because *"it changes
what is indexed"*. Measured, it changes **no committed byte**: the index is a bag
of terms, and a banner's words are body terms whether they head the columns or
sit above them. SR-TUNE decision 1's mechanical rule then refuses it from
`[index]`. It is a decoder cap. **The general lesson: "changes the index" is a
claim to test with `test_an_index_key_does_change_the_index`, not a reason.**

## 3. Construction arithmetic changed the design before any number

Worked by counting, before any arm: a `Field | Value` row named once by its
field could never beat a row whose VALUE says the field word twice, under any
weight on the column field, because the column field and the body share a
weight. So a record's field-name column became its key (B4 applied to B5).
Stated in the pre-registration; it is the kind of change a pre-registration
exists to make visible.

## 4. The refactor mid-run was proven neutral rather than assumed

Stage A was restructured into one table module after the capture (Arpit's
correction at 19:45). The re-capture was compared field for field with the
capture it replaced and found identical; only `REGISTER`'s `csv@2` moved the
index digest. A refactor that "should not change anything" was treated as a
claim and checked.
