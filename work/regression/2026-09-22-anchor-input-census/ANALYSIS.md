---
type: Analysis
description: "Why fixing W-191's missing edges did not unblock step 1, what the two meanings of link-dependent cost, and the four things the seed corpus owes before the anchor arms may run."
run: 2026-09-22-anchor-input-census
item: W-168
filed: 2026-09-22
classification: informed
---

# ANALYSIS — a count that reads as *present* when the input is absent

## The diagnosis

**`ref_edge_census.py` was built to stop a feature being measured on a corpus
that lacks its input, and it reported `anchored=61` on a corpus that lacks the
anchor field's input.** Not a bug: `anchor_bearing` answers *did any link have
text the analyzer kept*, which was exactly W-191's question. The anchor field's
question is narrower — *does any linker say something the target does not say
about itself* — and nothing computed it until today.

🔴 **The gap is one subtraction wide**, and it costs nothing: an edge's `at`
keys and the target record's `terms` keys are the same hashed vocabulary, so
`set(at) - set(own_terms)` is exact, needs no document, and stays inside
[L2](../../../records/0004_LAW-2-content-never-durable.md).

## Why the corpus looks right and is not

**Good link text is the problem.** The seed's anchors are faithful and
descriptive — *"the Temperature Excursion Response SOP"*, *"Dock scheduling
rules 2026"*, *"the H2 2026 rate card"* — and a faithful anchor names a document
in the document's own words. The case the anchor field exists for is the
**unfaithful** one: the team nickname, the acronym, the "the old dock page"
that the page itself never calls itself.

⚠ **So this is not a corpus-quality defect to be fixed by writing better
links.** It is a *coverage* defect: the corpus has one kind of link and needs a
second kind beside it.

## The two meanings of "link-dependent", and what the collision cost

set-3 declares **`link_dependent: 14`** under [SR-RS](../../../records/0133_predictions.md)
decision 23c, and those 14 questions are genuinely link-dependent — in the
**multi-hop** sense. *"PROJ-124 says finance added a line to the rate card.
which line and how much"* requires following an edge to answer. **It exercises
the refer plane and the graph. It does not exercise the anchor field**, which
acts at retrieval time on the words a linker used.

🔴 **A tag that reads as the input and is not it is worse than no tag**, because
d23c's whole purpose is to let a later session check coverage without
re-deriving it. **Step 1's coverage tag must be a new one** — the report names
what it has to mean.

⚠ **This is the same shape as the run it is about**, one level up: a count
(`anchored=61`) and a tag (`link_dependent: 14`) that both read as *the input is
present*, neither of which is it.

## The specific things that follow

| # | change | state |
|---|---|---|
| 1 | the census counts **anchor-distinctive** terms/targets and exits `3` when a corpus has links and none | ✅ shipped with this run |
| 2 | a test that the distinction cannot silently collapse again | ✅ [`tests/test_ref_edge_census.py`](../../../tests/test_ref_edge_census.py), 8 cases |
| 3 | **the seed corpus gains anchor-only vocabulary and a hub**, plus questions asking for it in the linker's words, plus a new `23c` tag | 🔴 **owed — it is what step 1 waits on, and it is corpus authorship** |
| 4 | the anchor pre-registration records that its clause 5 is still in force, for a NEW reason | ✅ addendum, **no threshold moved** |

🔴 **Nothing here licenses turning `[bm25f] anchor` on.** It ships at `0.0`,
costs nothing there, and the frozen decision rule is untouched.

## What was NOT diagnosed

- **Whether the anchor field helps when the anchor only adds term frequency.**
  The fold still runs on redundant anchors and still changes scores; whether
  that *helps* is measurable on this ladder and is **not what step 1's
  pre-registration asks**, whose clause 2 forbids reporting *the best anchor
  weight* and whose data section names distinctive vocabulary as the input. A
  tf-only measurement would be **a different pre-registration** and this run
  does not write one.
- **Whether 1050 distinctive terms in this repository would move its rankings.**
  Unmeasured, and the pre-registration bars this corpus from producing a
  verdict. It is reopen-trigger evidence that the feature has a real input
  somewhere, and nothing more.
- **Why `supersedes` edges outnumber `ref` edges 1001 to 61 at `rung-10000`.**
  The filler documents carry supersession and no links, so link density falls
  as the corpus grows. It does not affect this finding — the distinctive count
  is 1 on every rung including `rung-seed` — but a link feature measured at
  scale on this ladder is measuring 61 edges among 10 000 documents.
