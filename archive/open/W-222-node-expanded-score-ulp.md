---
type: Handoff
name: W-222
description: "The Node reader and the Python reader disagree in the last bit of an EXPANDED BM25F score on a small linked corpus, with a manual --expand and RM3 off. A differential-law breach, found while building W-221's re-run."
item: W-222
filed: 2026-09-25
ball: agent
---

# W-222: last-bit expanded-score gap between the readers

## What was seen

On `tests/query/test_rm3.py::_linked_corpus`, with `expand_weight = 0.3`:

- **Command:** `ask "alpha" --expand "beta delta"`
- **Python:** `file:rank01.md` scores `2.983456736842099`
- **Node:** the same document scores `2.9834567368420997`
- **Everything else agrees:** the other documents score the same, and the order is identical.

**Not caused by W-221.** The gap shows with RM3 off. Both readers feed back the
same ten documents and pick the same two terms, so the gap is downstream, in
the expanded scoring.

**Already ruled out:**

- `expand.build`: the same hash order in both readers
- `scoreRecord`/`score`'s loop: the same statements

**Not yet checked:**

- `termContribution` and the idf arithmetic under a term weight
- the order candidates reach `rank()`
- whether scan computes `wlen` differently from Node on this path

## Definition of done

1. Find the operation whose order or rounding differs, and make the readers
   byte-equal ([SR-NODE-SEARCH](../../records/0153_node-search.md)).
2. Remove the strict `xfail` on
   `test_node_reader_feeds_back_the_same_list[0.3]`. It turns red once the
   fix lands.
3. Both suites pass, whole.

## Blockers

None.

## Model

**Model: Sonnet** — a bounded float-order bug with a failing test already written.
