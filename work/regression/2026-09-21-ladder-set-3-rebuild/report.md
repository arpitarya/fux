---
type: Report
run: 2026-09-21-ladder-set-3-rebuild
item: W-204
classification: surface capture
description: "Prompt 4 run as the check it says it is: check 4 reported all eight golden rungs STALE against a seed that had grown by eight documents, which is the one condition a rebuild is authorised on. All eight rebuilt from the current seed with the unmodified 2026-09-12 builder and re-frozen. The ladder went from 0 ref edges to 61 on every rung, and 18 632 ext documents came back byte-identical."
filed: 2026-09-21
---

# REPORT — the golden ladder, rebuilt on set 3's seed

**Not a paired run.** No arms, no judged queries, no threshold, and no question
asked of a rung. It is [prompt 4](../../golden/prompts/4-claude-corpus.md)
performed as what it says it is — *a check, not a build* — and the check failed,
which is what authorises the rebuild. A **surface capture**; it files no verdict.

🔴 **Honour declaration, which prompt 4 requires this report to make out loud.**
This session read `work/golden/seed/`, `work/golden/seed-dates.tsv`,
`work/golden/README.md`, `work/golden/prompts/` and `work/golden/ladder/` — and
**no answer, by any route, a paste included**. It did not open, list, glob, grep,
hash, count or stat anything at either spelling of the sealed-key directory
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) decision 5 closes.

⚠ **Prompt 4's ordering rule (*"run this BEFORE prompts 2 and 3 where you can"*)
was not kept and could not be**, for the third time: all three question sets were
on disk before this ran. **The honour rule above is the whole of what protects
this phase**, and nothing mechanical enforces it.

⚠ **`questions/set-3.jsonl` was committed by this session without being read.**
The set-3 authoring session wrote it and left, as L11 decision 6 requires of it,
and left it untracked. Before committing, its **JSON keys** were read — `id` and
`question`, identical to set 1 and set 2, with no answer-shaped field — and **no
value was**. A file is not published to a committed ref on trust.

## What the check found

| check | result |
|---|---|
| all eight rungs present in `fux-lab` | ✅ |
| manifests consistent, nesting verified | ✅ all seven steps |
| every manifest path inside `seed/` or `ext/` | ✅ |
| 🔴 **manifest `seed/` half vs `work/golden/seed/`** | 🔴 **8 documents absent, on all eight rungs** |

**What moved under them.** The set-3 authoring session added **eight documents**
— `16`–`22` and `archive/a06` — carrying the failing identifier shape
(`RF-118`/`RF-119`/`RF-120`, `PROJ-123`…`PROJ-125`) in body text **and** in
front-matter `doc_id:`, plus the link-bearing map document prompt 7 specified.
`work/golden/seed/` genuinely changed, which is the one condition prompt 4
authorises a rebuild on.

🔴 **The gate fired before a human did.** `tests/test_golden_ladder_seed.py`
failed on **8 of 8 rungs** in this session's baseline suite run — the check built
after the 2026-09-15 drift, catching the next one exactly as designed. The fast
suite was red from the moment the seed grew until the ladder was rebuilt, and
that is the intended behaviour, not a defect.

## What was done

All eight rebuilt by [`evidence/rebuild.py`](evidence/rebuild.py), a thin driver
over the **unmodified** 2026-09-12 builder and generator — `build_golden_rung.py`
and `make_golden_ext.py` are the reproducibility claim for `ext/`, and editing
them would have destroyed the one check worth making.

| rung | documents | archived | superseded | carrying `mtime` | index root |
|---|---:|---:|---:|---:|---|
| `rung-seed` | 28 | 6 | 4 | 28 / 28 | `c44a0f2bf585…` |
| `rung-00100` | 100 | 13 | 11 | 100 / 100 | `cfe6022f1a86…` |
| `rung-00200` | 200 | 23 | 21 | 200 / 200 | `522187041950…` |
| `rung-00500` | 500 | 53 | 51 | 500 / 500 | `0748b21c36d2…` |
| `rung-01000` | 1 000 | 103 | 101 | 1000 / 1000 | `fc53e0ccf0f1…` |
| `rung-02000` | 2 000 | 203 | 201 | 2000 / 2000 | `532de4cbffb1…` |
| `rung-05000` | 5 000 | 503 | 501 | 5000 / 5000 | `2ccfe6fcb527…` |
| `rung-10000` | 10 000 | 1003 | 1001 | 10000 / 10000 | `0697ba66f175…` |

| rung | seed | sibling | adjacent | filler | variant |
|---|---:|---:|---:|---:|---:|
| `rung-seed` | 28 | 0 | 0 | 0 | 0 |
| `rung-00100` | 28 | 29 | 22 | 14 | 7 |
| `rung-00200` | 28 | 69 | 52 | 34 | 17 |
| `rung-00500` | 28 | 189 | 142 | 94 | 47 |
| `rung-01000` | 28 | 389 | 292 | 194 | 97 |
| `rung-02000` | 28 | 789 | 592 | 394 | 197 |
| `rung-05000` | 28 | 1989 | 1492 | 994 | 497 |
| `rung-10000` | 28 | 3989 | 2992 | 1994 | 997 |

## 🔴 The one number that changed, and why it is this number

**`seed/` grew from 20 documents to 28**, and the builder computes
`ext_n = count - len(seed_docs)`. So **every rung above the seed keeps its
headline size** — 100, 200, … 10 000 — and carries **eight fewer generated
documents**. The alternative, keeping `ext` at 80 · 180 · … · 9 980, would put
the top rung at **10 008 documents and through the ceiling**
[SR-WORK-SCALE](../../../records/0057_WORK-scale.md) and
[SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md) set at
10 000. **The ceiling wins.**

⚠ **`rung-seed` is 28 documents, not 20.** It *is* the seed corpus, so its count
is `len(seed_docs)` by definition; the `20` in the old table was that
definition's value on 2026-09-12, not a target.

⚠ **`superseded` is one lower on every rung above the seed** (11 · 21 · 51 ·
101 · 201 · 501 · 1 001). Nothing was un-superseded: the ext stream is eight
documents shorter, and one supersession pair fell past the rung boundary. The
builder checks `declared == indexed` on every rung and all eight agree.

⚠ **Every rung's ext count is now ≡ 2 (mod 10).** The generator emits blocks of
ten holding the README's 40/30/20/10 mix exactly, so a rung ending mid-block is
two documents richer in `sibling` + `adjacent`. Measured at `rung-00100`: 29 ·
22 · 14 · 7 of 72, against an exact 28.8 · 21.6 · 14.4 · 7.2 — **the closest
integers to the declared mix**, so the effect is nil in practice. 🔴 **The
supersession pair at slots 5 and 6 is never split by a boundary at slot 2**,
which is what makes the shorter ext safe at all: the builder treats a
`supersedes:` target outside the rung as a hard error, and it fired on none.

## Determinism — measured, not asserted

[`evidence/diff_manifests.py`](evidence/diff_manifests.py) compares every
pre-rebuild manifest (snapshotted to `evidence/ladder-before-set-3/` before
anything ran) against its replacement:

| rung | ext in both manifests | **ext that differ** | **seed that differ** | dropped | added |
|---|---:|---:|---:|---:|---:|
| `rung-00100` | 72 | **0** | **0** | 8 | 8 |
| `rung-00200` | 172 | **0** | **0** | 8 | 8 |
| `rung-00500` | 472 | **0** | **0** | 8 | 8 |
| `rung-01000` | 972 | **0** | **0** | 8 | 8 |
| `rung-02000` | 1 972 | **0** | **0** | 8 | 8 |
| `rung-05000` | 4 972 | **0** | **0** | 8 | 8 |
| `rung-10000` | 9 972 | **0** | **0** | 8 | 8 |
| `rung-seed` | 0 | — | **0** | 0 | 8 |

✅ **18 632 generated documents came back byte-identical**, nine days and several
engine commits after they were last written. `make_golden_ext.py`'s
prefix-stability claim — *document `i` depends on `i` alone and never on
`--count`* — is now measured across a **change in `--count` itself**, which the
2026-09-15 refresh could not test because the count did not move.

## 🔴 The ladder has links for the first time

`ref_edge_census.py`, **exit 0**, all eight rungs
([`evidence/ref-edge-census.json`](evidence/ref-edge-census.json)):

| rung | documents | `ref` edges | anchor-bearing | anchor terms | sources | targets |
|---|---:|---:|---:|---:|---:|---:|
| every rung, `rung-seed` through `rung-10000` | 28 … 10 000 | **61** | **61** | **245** | **8** | **25** |

**It was 0 on all eight.** [W-191](../../../archive/open/W-191-the-ladder-carries-no-links.md)
was filed because three features were measured against a corpus with no `ref`
edge in it and `0 of 124 flips` was read as a result
([SR-RS](../../../records/0133_predictions.md) decision 23: **missing input is a
data defect, not a null**). The eight set-3 documents carry markdown links that
`edges._resolve_ref` actually resolves — 61 of them, every one carrying anchor
terms — so:

- **[W-168](../../open/W-168-search-improvements.md) step 1's obligation 8 is
  unblocked.** The anchor field has shipped since 2026-09-15 at `anchor = 0.0`
  and has **never been measured**, for want of a corpus containing the input.
- **W-161's two arms** and **W-176 gate 6** (W-204 phase E) have their input.

🔴 **Nothing here turns any of them on.** `[bm25f] anchor` stays `0.0` on every
rung; a weight moves only on its own passing pre-registered run. **Having the
input is not having the result.**

## What a reader must not carry forward

🔴 **Every golden number filed before 2026-09-21 names a corpus that no longer
exists.** That includes the 2026-09-20 phase A pass, which is kept as the
**pre-set-3 baseline** and may be read for what it measured — it may not be
differenced against this ladder's numbers. The seed changed, the ext tail
changed, and `index_root_sha256` moved on all eight.

⚠ **No pre-registration pins a rung index root**, so nothing frozen was
invalidated and **no threshold moved.**

## Reproduce

```bash
cd /Users/arpitarya/my_programs/fux
.venv/bin/python work/regression/2026-09-21-ladder-set-3-rebuild/evidence/rebuild.py
.venv/bin/python tools/differential/ladder_check.py
.venv/bin/python tools/quality-controls/ref_edge_census.py --corpora ~/my_programs/fux-lab/corpora/golden
```

**Verification after the rebuild:** `ladder_check.py` PASS on all four checks
including `seed_drift`; **18 828 documents hashed against their committed
manifests, 0 mismatched, 0 missing**; nesting verified across all eight; every
coverage count `declared == indexed`; `fux.index.v4`, analyzer `v2`; **0 seed
files on any skip list**.
