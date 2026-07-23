---
type: Conformance Analysis
status: final
date: 2026-07-24
run: 2026-07-24-orbit-fulfillment
engine: fux 0.25.0
corpus: orbit-fulfillment (944 files, 892 ingested sources, 900 chunks)
---

# Analysis — orbit-fulfillment, the second realistic corpus

## What this run was for

The acme-payments run (2026-07-22) produced three findings from **one** corpus.
The standing rule is that no behaviour change ships off a single corpus. This
run is the second data point every open decision was waiting on.

The corpus is deliberately **warehouse/order-fulfillment**, chosen so its
vocabulary shares almost nothing with fintech payments. If a match still fires
across that gap, it is a real match and not shared jargon.

## Headline — all three findings generalize

| finding | acme (0.23.0/0.25.0) | orbit (0.25.0) | generalizes? |
|---|---|---|---|
| staleness inversions | 9/12 | **8/12** | **yes** |
| — of which frontmatter-reachable | 5/12 (accidental) | **6/12 (by construction); 5 of those 6 inverted** | **yes — worse** |
| fabrication (unanswerable declined) | 0/4 | **0/4** | **yes** |
| absolute-floor separating interval | empty | **empty** | **yes** |
| **margin-check separating interval** | not measured | **empty, and inverted** | **new — refuted** |
| zero-overlap clean dense rescue | 0/6 | **1/6** | **yes (still failing)** |
| lexical hit@5 / hybrid hit@5 | .873 / .855 | **.887 / .887** | n/a |

**Nothing here is corpus-specific.** Two independently-authored corpora in
unrelated domains produce the same three defects.

## Environment caveat — read this before citing the numbers

> **⚠ CORRECTION (2026-07-24, phase 8): the premise of this section was wrong.**
> **`fux-engine==0.25.0` *was* on PyPI**, published 2026-07-23T08:17 from the
> `v0.25.0` release — as was 0.24.0. The frozen-wheel workaround below was
> therefore unnecessary.
>
> **The likely cause, worth knowing because it will recur:** `pip install
> fux-engine==0.25.0` fails with *"No matching distribution found"* on Python
> **< 3.11**, because the package requires `>=3.11`. That error is easily
> misread as "not published." Reproduced exactly during phase 8: the same
> command failed under Python 3.9.6 and succeeded under 3.12.
>
> **The measurements below are unaffected.** The frozen wheel was built from
> `af374f0`, the same commit released as v0.25.0, so the engine under test was
> the intended one. Only the *justification* for building it was mistaken.
> **Check `python -V` against `requires-python` before concluding a version is
> unpublished.**

**`fux-engine==0.25.0` is not on PyPI.** v0.25.0 is committed and merged to
`main` (`af374f0`, PR #43) but was never released. The harness's independence
rule says "install the published package from PyPI"; that was impossible.

- **What was done instead:** built a frozen wheel from the clean `main` working
  tree (`uv build --wheel`) and installed *that* into the environment's venv.
- **Independence preserved in substance:** the suite still drives only the `fux`
  binary through `subprocess` and never imports `fux`; no engine source was read
  to shape any assertion.
- **Precedent:** the acme environment already runs 0.25.0 the same way (an
  editable install of the local tree) — that is how the 0.25.0 acme numbers this
  run compares against were produced.
- **Consequence:** these numbers describe commit `af374f0`, not a published
  artifact. Re-run after release to confirm.

Repro:
```bash
cd ~/my_programs/fux && uv build --wheel --out-dir /tmp/fux-wheel
cd ~/my_programs/fux-lab/orbit && echo 3.11 > .python-version && rm -rf .venv
./setup.sh /tmp/fux-wheel/fux_engine-0.25.0-py3-none-any.whl && ./run.sh
```

## Corpus validity — the experiment's precondition

The generator is `fux-lab/shared/generate/make_orbit.py` (stdlib, seed 20260723,
byte-identical across runs — verified by `diff -r`).

- **944 files, 50 hand-written hero documents**, 57 typed eval pairs.
- **Marker split known by construction** (acme's 5/12 was accidental):
  **6** superseded docs carry machine-readable `superseded_by:`, 3 carry a dated
  inline note only, 3 carry no marker at all.
- **Unanswerable class verified genuinely unanswerable** — `crypto`,
  `cryptocurrency`, `drone`, `aerial`, `last-mile`, `graphql`, `cafeteria`,
  `catering`, `mobile app`, `bitcoin` return **0 files** across the corpus.
- **Prose read and accepted**: five generated files opened and read before any
  measurement. Domain language is authentic (totes, putwall, cross-dock, AMR,
  backorder, replenishment, dock doors, ASN); no fintech framing anywhere.

```bash
python3 shared/generate/make_orbit.py --out /tmp/a && python3 shared/generate/make_orbit.py --out /tmp/b && diff -r /tmp/a /tmp/b
```

## Finding 1 — staleness inversions reproduce (8/12), and the engine already knows

**8 of 12** stale-vs-current pairs put the superseded document above the still-true
one in default hybrid mode. The current doc is still *reachable* (in top-5 for
11/12) — it is simply outranked.

```bash
cd orbit && ./fux find "What is the same-day dispatch order cutoff time?" --json --top 10
```

### The decisive detail: the signal is present and unused

**6/6 frontmatter-reachable superseded docs carry the v0.25.0 annotation** when
retrieved (`"superseded": true`, `"superseded_by": "<path>"`), and **5 of those 6
still rank above their current replacement** — most at **rank 1**.

The engine is emitting "this document is superseded, here is its replacement"
about the document it just ranked first. The information needed to fix the
ranking is already computed, already machine-readable, and already in the
response. Nothing new has to be inferred.

Evidence: `evidence/supersession-annotation.txt`.

### Mechanism — RRF lets a hair-thin dense win override a decisive lexical win

From `evidence/inversion-mechanism.txt`:

| question | doc | lex rank | lex score | dense sim |
|---|---|---|---|---|
| primary parcel carrier | **current** | **1** | **19.80** | 0.5932 |
| | superseded | 2 | 15.07 | **0.7625** |
| dock door assignment | **current** | **1** | **32.10** | 0.7667 |
| | superseded | 2 | 16.58 | **0.7673** |
| same-day cutoff | **current** | **1** | **35.65** | 0.6738 |
| | superseded | 2 | 35.00 | **0.7016** |

- In **6 of 8** inversions the current doc **wins the lexical plane outright** —
  sometimes 2× the BM25F score — and loses anyway.
- The dense plane systematically prefers the superseded doc, sometimes by
  **0.0006 cosine** (dock doors), and RRF converts that into a rank flip.
- **Why dense prefers stale:** superseded docs here are short and state the old
  fact plainly, so the whole document is on-topic. Current docs are longer and
  cover more ground, so their embedding is diluted. This is a structural bias
  toward terse obsolete documents, not a quirk of one corpus.

### What this means for the down-rank decision

The Option-B reopen-trigger's first condition — *"a second realistic corpus
reproducing the inversion rate ≥ 8/12-equivalent"* — **is met at exactly 8/12**.

The second condition (a penalty tunable without regressing hit@5) is **not tested
here and must not be assumed**. This run deliberately changes no ranking
behaviour. What it does establish is that a penalty would usually only need to
overcome a *very small* fusion gap.

**Next step (not taken here):** a penalty-tuning experiment gated on the fixture
gate, acme, orbit, and the synthetic tiers together.

## Finding 2 — fabrication reproduces (0/4), and the margin check is now refuted too

All four typed unanswerable questions produced a fabricated extractive answer
with 3–5 citations. None declined.

```bash
cd orbit && ./fux answer "What is the uptime SLA percentage for the autonomous drone last-mile delivery fleet?" --json
```

The drone question is answered with sentences about AMR fleets and manifest
cutoffs — real sentences from real documents, stitched into a confident answer to
a question the corpus cannot address.

**The bare-gibberish path still works** (`find`/`ask`/`answer` all decline on
`xyzzy plugh frobnicate…`). The failure is specific to **well-formed questions in
the corpus's own vocabulary** — the realistic case.

### The absolute floor — empty interval, confirmed empirically

Swept `[answer] min_confidence` across the **full** 57-question eval set, setting
the config and observing real declines rather than assuming the comparison
(`evidence/floor-sweep.json`):

| floor | unanswerable declined | answerable false-declined |
|---|---|---|
| 0.0 (shipped) | 0/4 | 0/53 |
| 0.095 – 0.103 | 3/4 | **0/53** |
| 0.105 – 0.120 | 3/4 | 1/53 (zero-overlap) |
| **0.121** | **4/4** | **1/53** |
| 0.125+ | 4/4 | 2/53 (zero-overlap, stale-vs-current) |

- Declining all four needs **≥ 0.121**; zero false-declines holds only to
  **≤ 0.103**. **Interval empty.**
- Structurally identical to acme (which needed ≥ 0.25 against ≤ 0.087). Different
  scale, same verdict.

### The margin check — empty *and pointing the wrong way*

This is the measurement the acme run deferred and the last no-model mechanism
available. Measured top and runner-up scores for all 57 questions
(`evidence/margin-top-vs-runnerup.json`).

The hypothesis was: a genuine answer has a clear winner (large margin); an
unanswerable question has no clear winner (small margin) → decline on small
margin.

**The data inverts it.**

| class | margin range |
|---|---|
| unanswerable (n=4) | 0.00052 – 0.00411 |
| smallest answerable | **1e-05**, 1e-05, 7e-05, 0.00025, 0.00025, 0.00027 |

- Every unanswerable margin is **larger** than the six smallest answerable
  margins. `max(unanswerable) = 0.00411` vs `min(answerable) = 1e-05`.
- A threshold that declines the fabrications would first decline a `factual`
  question ("How many order lines can one pick wave contain?", margin 1e-05) and
  a `how-to` question — not just the predicted `cross-doc` false positives.
- **Why:** the smallest margins belong to questions where a document and its own
  superseded twin tie almost exactly. Finding 1 is *manufacturing* the margin
  check's false-positive mode. The two defects are coupled.
- The ratio variant fails identically (`max(unans) 1.0928` vs
  `min(ans) 1.000206`).

### Verdict on Finding 2

Both no-model discriminators are refuted on two independent corpora:

- absolute floor — **empty on acme, empty on orbit**
- runner-up margin — **empty and inverted on orbit**

**This is a product boundary, not a bug.** Extractive answering without a model
cannot distinguish "the corpus answers this" from "the corpus contains
topically-adjacent sentences." The honest options are (a) keep the permissive
default and document the limit, (b) offer the measured floor curve as an opt-in
knob with its false-decline cost stated, or (c) accept a model in the answer path
— which the constitution forbids on the maintenance path.

Recommendation: **(a) plus (b)**, and write the limit down as a documented
boundary rather than leaving it as an open defect.

## Finding 3 — zero-overlap dense rescue still fails (1/6 clean)

```bash
cd orbit && ./fux find "How do we make sure a picker is not routed to an empty location?" --json --top 10
```

Separating true rescues from lexical hits (`evidence/zero-overlap-rescue-detail.txt`):

| question | lexical rank | hybrid rank | verdict |
|---|---|---|---|
| picker routed to empty location | – | – | miss |
| inventory accuracy without shutting | **5** | **–** | **hybrid DEMOTED a lexical hit** |
| received goods with a waiting order | 8 | 6 | miss |
| popular products near shipping | – | – | miss |
| avoid walking the same aisle | 1 | 1 | top-5 via lexical, not a rescue |
| best-fitting shipping box | 7 | **1** | **clean dense rescue** |

- **1/6 clean dense rescues** (acme: 0/6). Marginally better, still a failure.
- The aggregate metric (`zero_overlap_rescued: 2`) **overstates** it — one of the
  two was already a lexical rank-1 hit. Report the clean-rescue number.
- **One active regression:** hybrid pushed a lexical rank-5 hit *out* of top-5.
  Fusion is not monotone — it can lose a document lexical alone would have found.
- All four misses were **inside the dense prefilter** (`in_prefilter: true`) with
  similarity 0.33–0.53. The candidates are reachable; the ranking is what fails.

Consistent with the standing diagnosis that this needs **chunk-level dense
codes** (its own phase). This run confirms the finding generalizes; it proposes
no fix.

## Per-kind quality (never an aggregate alone)

| kind | n | lexical hit@1 / hit@5 | hybrid hit@1 / hit@5 |
|---|---|---|---|
| factual | 17 | 0.647 / 0.941 | 0.471 / 0.941 |
| why | 8 | 0.875 / 1.000 | 0.875 / 1.000 |
| how-to | 6 | 1.000 / 1.000 | 1.000 / 1.000 |
| cross-doc | 4 | 0.500 / 1.000 | 0.750 / 1.000 |
| stale-vs-current | 12 | 0.583 / 0.917 | **0.333** / 0.917 |
| zero-overlap | 6 | 0.167 / 0.333 | 0.333 / 0.333 |
| **all** | **53** | **0.642 / 0.887** | **0.566 / 0.887** |

- **Hybrid is worse than lexical at hit@1 (0.566 vs 0.642)** on this corpus while
  tying at hit@5 — the same directional result as acme.
- The loss is concentrated in `stale-vs-current` (0.583 → **0.333**) and
  `factual` (0.647 → 0.471). Finding 1 is the mechanism: dense fusion promotes
  terse superseded documents.
- `how-to` is perfect in both modes; `why` is unaffected by fusion.
- **Do not read the aggregate alone** — hit@5 is identical (0.887) in both modes
  and hides a 0.076 hit@1 regression.

## v0.25.0 features, first contact with an independent corpus

- **Supersession annotation: works.** 6/6 frontmatter-reachable superseded docs
  surface `superseded` + `superseded_by` in `find --json`; `fux why --json`
  carries it too. Option A is functioning exactly as designed.
- **`[answer] min_confidence`: plumbing works, default is correct.** The knob
  changes decline behaviour monotonically across the sweep, and the shipped
  default (`0.0`) is the only value that false-declines nothing. The v0.25.0
  decision to ship permissive is **re-confirmed on a second corpus**.
- The annotation's limit is now measured: **annotation alone does not change
  rank**, which is precisely what Option B was deferred pending evidence on.

## Unresolved — stated as unresolved

- **Why the dense plane prefers short superseded documents** is explained here as
  embedding dilution on longer current documents. That is a *hypothesis
  consistent with* the measurements, not something this run isolated. A
  length-controlled experiment (same fact, matched document lengths) would settle
  it; it was not run.
- **Whether a down-rank penalty can be tuned without regressing hit@5** is
  untested. Nothing here supports a specific penalty magnitude.
- **Why 4 of 12 pairs did not invert** is not established. The non-inverting set
  (wave cap, cycle count, short pick, tote capacity) spans all three marker
  styles, so marker style does not explain it.
- **The 1/6 vs 0/6 zero-overlap difference** between orbit and acme is within
  noise at n=6 and should not be read as improvement.

## Specific engine decisions this run supports

1. **Supersession down-rank (Option B): first reopen condition MET.** 8/12 on a
   second realistic corpus, with 5/6 frontmatter-reachable pairs inverted and the
   annotation already present on the winning document. Next step is a
   penalty-tuning experiment, not a ship.
2. **Answer decline: close the floor and margin lines.** Both no-model
   discriminators are refuted on two corpora. Convert this from an open defect
   into a documented product boundary, and consider exposing the measured floor
   curve as an opt-in knob with its cost stated.
3. **Report clean dense rescues, not top-5 appearances.** The suite's
   `zero_overlap_rescued` metric counts lexical hits and overstates dense
   performance. Worth correcting in `shared/regress/run.py`.
4. **Fusion is not monotone.** Hybrid demoted a document lexical alone ranked 5th.
   Worth a named regression check — hybrid should not lose a lexical top-5 hit.

## Files

- `report.md` — the suite's own report (56 checks, 14 failures).
- `evidence/margin-top-vs-runnerup.json` — top/runner-up scores, all 57 questions.
- `evidence/floor-sweep.json` — the empirical min_confidence trade-off curve.
- `evidence/inversion-mechanism.txt` — lexical vs dense per inversion.
- `evidence/supersession-annotation.txt` — 6/6 annotation coverage.
- `evidence/zero-overlap-rescue-detail.txt` — clean rescue vs lexical hit.
- `evidence/per-question-outcomes.txt` — exact per-question ranks.
- `evidence/why-per-miss.json` — `fux why --json` for every miss, current *and*
  superseded document.
- `evidence/debug-trace-inversion.txt` — `--debug=trace` on an inversion.
- `evidence/doctor.json`, `evidence/corpus-manifest.json`.
