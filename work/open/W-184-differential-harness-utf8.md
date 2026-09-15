---
type: OpenItem
id: W-184
title: "W-184 — the differential harness dies on a non-UTF-8 file in a source dir"
description: "tools/differential/queryset.py::vocabulary decodes every walked file as UTF-8 and raises on the first that is not, so `run.py --root .` cannot run on this repository at all. Found 2026-09-15 while gathering W-168 step 1's differential evidence; pre-existing, unrelated to that change."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-184 — the differential harness cannot run on this repository

**Model: Sonnet** — a one-branch repair in a tool, with a test.

**Found 2026-09-15**, while gathering [W-168](W-168-search-improvements.md)
step 1's differential evidence. **Pre-existing and unrelated to that change** —
nothing in W-168 touches the walker.

```
python tools/differential/run.py --root .
  ...
  File "tools/differential/queryset.py", line 87, in vocabulary
    for term in set(tokenize(walked_file.content.decode("utf-8"))):
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0
```

`0x89` is a PNG's first byte. `walk_sources` yields **every** file in a
configured source directory, including the ones no decoder claims and ingest
skips; `vocabulary` decodes all of them.

## Why it matters more than a tool crash

🔴 **`tools/differential/` is the proof obligation for every ranking change**,
and it has been unrunnable on fux's own corpus for as long as a binary file has
sat in a listed directory. **Nothing noticed**, because the unit-suite
counterpart (`tests/derive/test_differential.py`) builds its own synthetic
corpora and passes — so the arm that runs over a real repo was dead and the
green one covered for it.

⚠ **W-168 step 1's evidence was gathered through an ad-hoc copy of the harness**
in a scratch directory: the same comparison, the same query generator, with the
undecodable files skipped. 692 queries × 4 `top` × 2 skipping modes, at
`anchor = 0.0` and `anchor = 2.0`, 0 mismatches each. **That is a workaround, and
it is named as one in [SR-T1-ACCELERATOR](../../records/0110_accelerator.md)
decision 15b rather than left to be discovered.**

## Definition of done

1. `vocabulary` skips a file it cannot decode as UTF-8, and **says how many it
   skipped** — a silent skip would let the query set quietly shrink.
2. ⚠ **Decide whether it should instead walk what INGEST walks.** The query set
   is generated from source text on purpose (`queryset.py`'s own docstring: it
   exercises the real analyzer), but a corpus term that never reaches the index
   generates a query that can never match. Whichever way it goes, say so in the
   docstring — the two are not the same set and the difference is the point.
3. `python tools/differential/run.py --root .` runs clean on this repository.
4. A test that fails on a binary file in a source dir, so this cannot come back.
5. ⚠ **Check the same decode assumption in the sibling arms** —
   `adversarial_corpus.py`, `node_arm.py`, `graph_arm.py`, `bench_r3.py`. One
   occurrence is a bug; four would be a pattern and
   [SR-WORK-SESSION](../../records/0060_WORK-session.md) decision 13's two-strike
   rule applies.

## Out of scope

Removing the binary files from the source dirs. They are legitimately there —
`docs/paper/figures/` — and a harness that dies on a PNG is the defect.
