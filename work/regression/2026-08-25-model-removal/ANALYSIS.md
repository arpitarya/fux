---
type: Analysis
name: 2026-08-25-model-removal-analysis
description: "What the removal bought and what it cost: a 30x smaller wheel, a 22.6 % smaller committed index and a 6.8x faster ingest, against the permanent loss of any semantic lane. Plus three findings the change produced that nobody was looking for."
timestamp: 2026-08-25T00:00:00Z
---

# Analysis — removing the embedding model

## 1 · The trade, stated in both directions

**What was bought.** A wheel that is **30x smaller** — 6.84 MB to 233 KB — a
committed index **22.6 %** smaller, and a full ingest **6.8x** faster. For a
tool whose promise is *clone the repo, run the query, get the same answer*, the
wheel number is the one that matters most: the download was **97 % model**.

**What was given up, and it is not nothing.** Fux now has **no semantic lane at
all**, and no path to one that does not start by re-adding a dependency or a
bundle. Every failure mode that needs meaning rather than vocabulary — a query
whose words do not appear in the document that answers it — is now
**permanently** out of reach for this engine as built.

⚠ **That was already true in practice and is now true in principle.** The lane
existed, shipped `off`, and measured **0 fixed / 2 broken** at every setting
that fires. The removal did not lose a capability; it stopped paying for one.

## 2 · Why the cost was so lopsided, which is the transferable part

The lane cost **23 % of the committed plane, 97 % of the wheel and 85 % of every
ingest** — and returned nothing measurable. That ratio is worth understanding
rather than filing.

**The model mean-pools static token vectors.** No layers, no attention. A
document's vector is the average of its word vectors, so *"A supersedes B"* and
*"B supersedes A"* embed identically. **It was as order-blind as BM25F** — the
lane duplicated the lexical lane's blind spot at three orders of magnitude more
cost per byte.

**The generalisation:** *an added lane earns its cost only where it fails
differently from the lane it is added to.* A second opinion from a model that
makes the same mistakes is not a second opinion. Nothing in the design review
asked what the new lane's failures would look like — only whether it would be
faster and smaller, which it was.

## 3 · Three findings this change produced that nobody was looking for

**3.1 — `fuxvec.py` had been dead for two days and no test noticed.**
`doc_code`, `hamming`, `prefilter` and `CODE_BYTES` had **zero call sites** in
`src/`; `quantize` was reached only by `_fuxvec_code()`, which nothing called.
It went dead when W-76 Phase 1 removed the document-level `code` field on
2026-08-23. **`tests/embed/test_fuxvec.py` kept passing the whole time**, which
is precisely why it was invisible: a tested module looks alive.

*Improvement:* the repo has now deleted three orphaned modules in two days —
`hybrid.py`, `fuse.py`, `fuxvec.py`. **Nothing detects the fourth.** A check
that flags a `src/` module with no importer outside its own package and no
caller outside its own tests would have caught all three the day they died.
*Repro:* not built; filed as the one improvement this analysis actually asks for.

**3.2 — deleting the files did not delete the package.**
`git rm src/fux/embed/*` left the **directory**, and an empty directory is an
importable namespace package in Python 3, so `import fux.embed` still succeeded
and the test asserting its absence failed. **A deletion that leaves an
importable name behind is not a deletion.**
*Repro:* `git rm src/pkg/sub/*.py && python -c "import pkg.sub"` — succeeds.

**3.3 — the first differential check passed vacuously.**
`.fux/tune.toml` still carried `[dense]`, so every `fux ask` errored, both sides
of the comparison returned the empty string, and **six queries reported
IDENTICAL while proving nothing**. Caught only because the same command was run
once more with `--explain` and printed the error.

*This is the second vacuous pass this project has caught in two days* — the
first was a differential sweep that survived a mutant because BM25 saturation
made a weighted and an unweighted bound indistinguishable. **Both were
comparisons that could not fail.** *Improvement, applied here:* the harness now
asserts a non-empty result count **before** comparing, and prints `n=5` rather
than a bare verdict, so a future reader can see the comparison had something in
it. *Repro:* `evidence/measure.sh`.

## 4 · What this does not license

**It says nothing about whether a good dense lane would help.** The measurement
is about *this* model — a mean-pooled static embedding — on *this* corpus. A
model that sees word order was never tested, and the reason it was never tested
is [ADR-RERANK](../../../docs/adr/0041_rerank.md)'s determinism veto, which is
untouched by any of this and is still standing.

**And it does not make the corpus smaller for a user.** The 22.6 % is off the
*committed index*, not off their documents.

## 5 · Owed

- `.fux/tune.toml` in **fux-playground** still carries `[dense]` and will now
  error. It is a separate repository and this change cannot reach it.
- The dead-module check in §3.1 is unbuilt.
- ADR-RS decision 12's scope defect, found by this run being unable to report a
  file size without disclosing a conflict — [W-81](../../open/W-81-the-sealed-set-and-the-two-controls.md).
