---
type: Report
description: "W-168 step 1 remains unmeasurable, for a new and more specific reason: the golden ladder now HAS 61 anchor-bearing ref edges on every rung, and 0 anchor-distinctive terms. Every word a linker uses is already in the document it points at. fux's own repository, by contrast, carries 1050 distinctive terms across 594 targets."
run: 2026-09-22-anchor-input-census
item: W-168
filed: 2026-09-22
classification: informed
---

# The ladder has the links now, and still not the input

**This run rules on nothing and files no verdict.** It is the check
[the anchor pre-registration](../2026-09-15-anchor-text/PRE-REGISTRATION.md)
clause 5 requires **before** its arms may run, and the answer is that they still
may not.

## What changed since 2026-09-15, and what did not

| | 2026-09-15 | **2026-09-22** |
|---|---|---|
| `ref` edges per rung | **0** | **61** |
| anchor-bearing edges | 0 | **61** |
| anchor terms | 0 | **266** |
| **anchor-DISTINCTIVE terms / targets** | 0 / 0 | **1 / 1** |

🔴 **W-191 was fixed and step 1 is still blocked.** The ladder gained
link-bearing documents with set-3 (2026-09-21) and every count that existed
before today went from zero to healthy. **The count that matters went to one,
and that one is a filename.**

## The distinction this run exists to draw

**The anchor field contributes only where a linker supplies vocabulary the
target LACKS.** Where a linker repeats words the document already has, the fold
adds term frequency to terms `body`, `title` and `path` already carry — it
cannot make a document findable that was not findable before, which is the
claim step 1 was built on.

Measured over `work/golden/seed/`, with the engine's own analyzer, every link
target in the corpus:

```
 01-sop-temperature-excursion.md       linkers=9  anchor-terms=4  ANCHOR-ONLY= —
 13-dock-scheduling-rules-2026.md      linkers=5  anchor-terms=4  ANCHOR-ONLY= —
 11-decision-telematics-vendor-2026.md linkers=4  anchor-terms=4  ANCHOR-ONLY= —
 12-rate-card-2026-h2.md               linkers=4  anchor-terms=5  ANCHOR-ONLY= —
 …25 targets, and exactly one exception:
 09-dock-scheduling-wiki-export.html   linkers=2  anchor-terms=8  ANCHOR-ONLY=
                                         ['09', '09-dock-scheduling-wiki-export.html']
```

⚠ **The one exception is a bare-path link**, so its "distinctive vocabulary" is
the target's own filename. **It is noise, not an input.** A question would have
to contain the literal token `09` to exercise it.

**The linkers are good link text and that is precisely the problem.** *"the
Temperature Excursion Response SOP"* → `01-sop-temperature-excursion.md`;
*"Dock scheduling rules 2026"* → `13-dock-scheduling-rules-2026.md`. A human
wrote descriptive, faithful anchors, and a faithful anchor describes a document
in the document's own words.

## The question side follows from the corpus side

**0 of 373** retired questions (sets 1, 2 and 3) contain a term that a linker
supplies and the question's own primary document lacks.

🔴 **That is entailed, not coincidental.** A question can benefit from the
anchor field only if its wording includes a term the anchor supplies and the
target does not have. Corpus-wide there is exactly one such term and it is a
filename. **No question set written against this corpus can satisfy the
pre-registration's data row 3**, however it is worded — which is why the fix is
in the corpus and not in the questions.

⚠ **set-3's `link_dependent: 14` is a real tag and it is not this input.** Those
questions are link-dependent in the **multi-hop** sense — *"PROJ-124 says
finance added a line to the rate card. which line and how much"* — which
exercises the refer plane and the graph, not the anchor field. **Two different
meanings of "link-dependent", and only one of them is step 1's.**

## What the same census says about fux's own repository

| corpus | docs | `ref` | anchored | terms | **distinctive t/d** |
|---|---:|---:|---:|---:|---:|
| the golden ladder (every rung) | 28 – 10 000 | 61 | 61 | 266 | **1 / 1** |
| **this repository** | 1 672 | 4 768 | 4 768 | 30 038 | **1050 / 594** |

🔴 **The feature is not pointless; the benchmark corpus cannot see it.** In a
corpus where people link the way this repository's authors do, more than a
third of link targets are described by at least one word they do not use about
themselves.

⚠ **This is REOPEN-TRIGGER EVIDENCE AND NOTHING ELSE**, by the
pre-registration's own table: *"fux's own `records/` + `work/` + `docs/` — ❌ no.
This repository is where the idea came from and it is unusually densely
linked."* It may not produce a verdict and does not.

## What step 1 needs, stated so it can be handed over

1. **≥ 1 document in `work/golden/seed/` whose answering vocabulary appears
   ONLY in the link text pointing at it** — a house nickname, an acronym, a
   team's name for a page that the page itself never uses.
2. **≥ 1 document linked by MANY documents using UNRELATED words** — the hub
   case, which is the pre-registration's predicted failure direction and its
   clause 3.
3. **Questions phrased in the linker's words**, whose answer is (1).
4. **A `23c` coverage row naming both** — a new tag, because `link_dependent`
   already means something else here.

## What was changed as a result

`tools/quality-controls/ref_edge_census.py` now counts **anchor-distinctive**
terms and targets beside anchor-bearing edges, prints them as `terms/targets`,
and **exits 3** — a new code, distinct from `2`'s *no links at all* — when a
corpus has `ref` edges and no distinctive vocabulary.
[`tests/test_ref_edge_census.py`](../../../tests/test_ref_edge_census.py) is the
gate: **second strike, so a check**
([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 13). W-191
was the first, and the tool built for it reports `anchored=61` here, which reads
as *the input is present*.

⚠ **The exit code deliberately does not judge how MUCH is enough.** One
distinctive term exits `0`, and today that one term is a filename. Picking the
count at which a corpus becomes adequate is a threshold, and a threshold belongs
in a frozen pre-registration rather than in an instrument (SR-RS decision 10b).
**The tool reports the ratio; the reader judges.**

## Not a paired run, and no per-query rows

🔴 **This run is a census of a corpus, not a comparison of two arms.** It ran
**no query**, so there are **no per-query rows** (SR-RS decision 15) and **no
headroom** to disclose in either direction (decision 22) — there is no endpoint,
because nothing was scored.

⚠ **Saying so is the rule, not an exemption from it.** Both decisions name this
case explicitly, and a run that quietly filed neither would be
indistinguishable from a paired run that skipped them. **The moment step 1's
arms do run, both apply in full** — and the numbers they would need are exactly
the ones clause 5 is currently refusing to let anybody produce.

## Authorship

| artifact | author | what they could reach |
|---|---|---|
| `work/golden/seed/`, the ladder, set-3's link-bearing documents | Codex (seed), Claude (set-3 additions) | — |
| this census, this report | **Claude Code (this session)** | the corpus, the retired questions and their expected values |

**`informed`** — the retired sets are open to this session by
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) decision 14. **No
number here is about ranking quality**; every one is a property of the corpus.

## Reproduce

```console
$ .venv/bin/python tools/quality-controls/ref_edge_census.py \
    --corpora ~/my_programs/fux-lab/arms/runs/w213-head
$ .venv/bin/python tools/quality-controls/ref_edge_census.py \
    --index .fux/index --label this-repo
```

⚠ **The rungs must be built by an engine that can read them.** The frozen
`corpora/golden/rung-*` shards are analyzer `v2` and HEAD is `v3`; these counts
come from `fux-lab/arms/runs/w213-head/`, built with `arm_corpus.py` at
`7d41fdab`. Edge extraction is unchanged between them, and the counts are of
what `ingest` wrote.

**Evidence:** [`evidence/census.json`](evidence/census.json) (per rung),
[`evidence/census-this-repo.json`](evidence/census-this-repo.json),
[`evidence/census.txt`](evidence/census.txt).
