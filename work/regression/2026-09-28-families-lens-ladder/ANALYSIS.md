---
type: Analysis
run: 2026-09-28-families-lens-ladder
description: "Why the families lens's misfit floor cannot leave PROVISIONAL on the current ladder: the seed carries no planted misfit, and 14 of rung-01000's 16 misfits are a document's own title heading. Applies a title-heading change and a shared-heading rule to the lens, and names the decision that planting misfits in the seed needs."
---

# ANALYSIS — what the ladder can and cannot tell the families lens

## 1 · The lens finds the seed's templates

The eight seed families are the templates the seed's authors actually used. They
include the mapping studies, the lane qualifications and the reefer asset files.
They also include **four procedure + card pairs**: `40`+`56`+`57`, `43`+`58`+`59`,
`46`+`60` and `51`+`62`. Those are generation 3's R9 authority pairs (a maintained
document beside a one-person copy), which were written on one template. The R6
triples (`-procedure-` / `-decision-` / `-reference-`) do **not** share a family.
That is right: they are three shapes on one topic, and topic grouping is
`graph_shape`'s job (W-228 §4).

At rung-01000 the near-shape families absorb most of the older exact-set
signature: **94 exact-set families become 32**. That consolidation is what the
lens was built for.

## 2 · Why the floor cannot be tuned on this ladder

DoD 11 needs a corpus whose misfits are **known in advance**. The ladder has none:

- **`rung-seed`: 0 misfits.** No seed document was written to break its family.
- **`rung-01000`: 16 misfits, none planted.** They are what the ext generator
  happened to emit. **14 of the 16 are missing only the family's title heading**,
  and the quarantine siblings are the clearest case: they reuse the SOP's section
  skeleton under their own title.

So `misfit_share = 1.8 %` against a 20 % floor says only that this generator
rarely drops a section. Nothing here separates a true misfit from a false one.
**The floor stays PROVISIONAL.**

## 3 · Change A — keep the title heading out of the skeleton (applied, same session)

**The cause.** Most documents open with a heading that is their own title. That
heading is part of the skeleton, so:
- a document on the same template with a different title is a **misfit**
  (14 of 16 here);
- a template whose title carries a name **splits**. The dock-scheduling wiki is
  **four families** at rung-01000 (`Vantorix`, `Cindermoor`, `Halberd & Frost`,
  `Zephyrine` — 9 + 8 + 7 + 6 members) where it has one skeleton. The first
  heading of each is `<Company> Wiki - Dock scheduling rules`.

**The change.** A document's first heading is dropped from its skeleton when it
equals the document's title. That is the test `probes.py` already uses to find a
title heading. A family is then named by its shared sections.

**The second rule it needed.** With titles out, seeds `34` and `46` formed a
family with **no shared heading**. They share six front-matter keys, and
6 / (6 + 2 + 2) = 0.60 clears the cut. So only a **shared heading** now makes two
documents candidates for one family. Front-matter keys refine the score and
never found a family alone.

**What it changed** (report §After the lens change):
- rung-01000's misfits fell from **16 to 1**, and the one left is a real section
  difference;
- the four dock-wiki families merged into one.

The Raipur page stopped being a misfit: once the company title is out, its
extra `Raipur DC` heading no longer reaches `core_share`. SR-INSPECT decision 24
is amended. Two tests in `tests/test_inspect_families.py` pin the rules, and
both fail on the old lens.

**Repro of the effect:**
`jq '.misfits[] | select(.missing == [(.family | split(" · ")[0])])' evidence/families-rung-01000.json`
lists the 14.

## 4 · What DoD 11 still needs, and why that is Arpit's call

The input is **planted misfits in the golden seed**: documents written to a seed
family's template with a known section missing. Under
[SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md), that means:

- **A designated authoring session** writes the documents as fenced blocks, and
  Arpit commits them (A1–A3, A17–A20).
- **Additions only** (A20, T12). Every rung then fails
  `test_golden_ladder_seed.py` until the ladder is rebuilt, **~50 minutes**.
- 🔴 **A rebuilt ladder is a new baseline** (A23). W-168 steps 6–10 count their
  pools from set-4's score on **this** ladder (Arpit, 2026-09-28). A rebuild
  before they finish leaves them nothing comparable to count against.

The sequencing against W-168 is Arpit's to rule, so it is filed as a blocker.
