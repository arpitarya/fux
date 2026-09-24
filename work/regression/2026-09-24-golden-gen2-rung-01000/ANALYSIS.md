---
type: Analysis
run: 2026-09-24-golden-gen2-rung-01000
description: "Why this capture exists, why it needed no re-ingest, and the two things a reader of its score should know."
---

# ANALYSIS — the generation-2 baseline on the 42-seed ladder

## 1 · Why it exists

The 2026-09-23 rebuild made every earlier golden number describe a ladder that
no longer exists. That includes the 2026-09-22 `set-2-u` capture and the RM3
arms. Two open decisions need a score on the ladder as it now stands:

- **[W-215](../../../archive/open/W-215-generation-2-corpus.md) item 1:** does generation 2
  carry questions today's engine fails? That was the whole point of writing it.
- **[W-168](../../open/W-168-search-improvements.md) steps 1, 2, 4 and 9:** each
  one's pool is *tagged ∩ in the top 10 ∩ missing rank 1*. The last two terms
  come from a score.

## 2 · Why no re-ingest, unlike 2026-09-22

The rung's stamp names `2dbe870f` (alpha.3), and that is the engine this run
pinned. The 2026-09-22 capture had to re-ingest because its version and commit
both differed from the stamp. Here neither differs. **The ladder stays
homogeneous:** every rung is still at the index its stamp names.

## 3 · What to know when the score arrives

- **`set-3-u` was written to exercise steps 1, 2 and 4.** These inputs are now
  on the ladder, measured on 2026-09-24 from the seed alone:
  - 17 anchor-distinctive terms on 5 targets (the census exits 0);
  - 9 `Term (ABBR)` pairs;
  - a 21-line glossary.

  A `set-3-u` score is the first that can say whether those inputs produce
  *misses*. Misses are what W-219's floor of 6 needs.
- **Every band is `grounded`, `partial` or `weak`; none is `none`.** Under
  W-214, a question with no answer in the corpus still gets ten results.
  Abstention quality is therefore a score question, never a capture question.
