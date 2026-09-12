---
type: Setup
name: SETUP-LAB
title: SETUP-LAB — fux-lab, the measurement environment
description: "How the scratch measurement environment is set up, what it holds now that the golden ladder is its only corpus, why new work is a new environment inside it rather than a rebuild, and where each run's evidence has to land."
location: ~/my_programs/fux-lab
kind: scratch working directory — commits nothing to git; its BUILT CORPORA are kept and reused (Arpit, 2026-09-12)
timestamp: 2026-09-12T00:00:00Z
---

# SETUP-LAB — `fux-lab`, the measurement environment

> **This is a setup document, not a decision record.** It records how the lab is
> stood up and the operational rules that govern it. See [`README.md`](README.md)
> for what belongs in this directory.

> 🔴 **THE BUILT CORPORA ARE KEPT. DO NOT WIPE THEM.** Arpit, 2026-09-12:
> *"Do not delete the one thousand, two thousand, five thousand, and ten thousand
> data setup. Keep it. We will keep on reusing the data."*
>
> **"Commits nothing" is about git, not about disk**, and the two have been
> confused once already: the **2026-08-20 `fux-lab` wipe took W-78's corpora with
> their generator**, and those measurements can never be reproduced. Rebuilding a
> 10 000-document corpus costs hours, and a rebuilt one has a **different
> `corpus_sha256`** — so every timing taken against the old one stops being
> comparable.
>
> - Never `rm -rf` a corpus directory to reclaim space or to "start clean".
> - Rebuild a rung or a folder **only** when its generator changed, and say so.
> - A run that has to stop is stopped by killing the **run** and deleting its
>   partial **rows** — never its corpus.



🔴 **What this environment is for, what data it may use, and the size it stops
at are stated by [L9](../../docs/adr/0011_LAW-9-environments.md) and nowhere
else.** Read it there. This document does not restate it
([L0](../../docs/adr/0002_LAW-0-authority.md)) — it says how to *run* it.

- **Name:** `SETUP-LAB` — cite this by name
- **Location:** `~/my_programs/fux-lab` — a **sibling working directory**, not a
  repository we ship and not a directory in this one
- **Siblings:** [SETUP-PLAYGROUND](fux-playground.md) ·
  [SETUP-BENCHMARK](fux-benchmark.md). See [`README.md`](README.md) §Which is which
- **Written:** 2026-08-18 · **rewritten 2026-09-12** under L9 ([W-138](../../archive/open/W-138-reconcile-with-l9.md))

---

## What it holds today

```
~/my_programs/fux-lab/                 # a git repo — it was lost once for not being one
  corpora/golden/                      # THE corpus: the ladder, built by W-136
    rung-seed/   rung-00100/  rung-00200/  rung-00500/  rung-01000/
      seed/      the 16 seed documents, byte-identical on every rung
      ext/       filler · adjacent · sibling · archive — the growth material
      .fux/      each rung is its own git repo with its own index
  shared/        new-env.sh · generate/ · regress/
  <env>/         one directory per measurement environment
```

- **The ladder is the instrument.** Its manifests, sha256 files and coverage
  reports are committed in *this* repo at
  [`work/golden/ladder/`](../golden/ladder), so a rung is verifiable from here
  without reading the lab.
- ⚠ **Rungs 2 000, 5 000 and 10 000 are not built.** Arpit capped the
  2026-09-12 session at 1 000. A measurement that needs a larger rung builds it
  first — [W-136](../open/W-136-golden-benchmark.md).
- 🔴 **The answer key is never in the lab, and never in an agent's hands.** It
  sits beside the benchmark in [`work/golden/`](../golden/README.md), gitignored,
  under the one rule that document states.

## The standing rule — never delete it, never rebuild it

**Never delete `~/my_programs/fux-lab`, and never start a parallel harness.**
New measurement work is a **new environment inside it**:

```bash
cd ~/my_programs/fux-lab
shared/new-env.sh <name>
cd <name>
# pin VERSION to the engine the run is about
./setup.sh                        # bootstrap → generate → fux setup → ingest → verify
./run.sh --accept-baseline        # first run establishes the baseline
./run.sh                          # subsequent runs compare against it
```

Arpit asked for this to be stated explicitly **in every prompt that drives a
run**; it is standing rule §0b in `fux-lab/TEST-PLAN.md`.

`new-env.sh` emits the whole flow — bootstrap, generate, `fux setup`, `ingest`,
`--check`, and a present/MISSING verification block with per-plane sizes — plus
`run.sh`, a `fux` shim, and a README whose first line answers *"where is
`.fux/`?"*. That last detail is not decoration: the scaffolder once emitted a
corpus only, and every scaffolded environment reproduced the same confusion.

⚠ **`new-env.sh` still generates a synthetic corpus.** Under L9 an environment
that produces a *filed measurement* reads a golden rung instead; the generator
survives for scaffolding, smoke runs and harness self-tests, which are not
measurements of quality. If you scaffold an environment for a filed run, point
it at `corpora/golden/rung-NNNNN` and say so in the report.

## Where it can and cannot run

**Not on the Cowork device VM.** It has **no network** and **Python 3.10**;
fux-engine needs ≥ 3.11 and installs from PyPI, so `setup.sh` cannot run there.

**Run the suite in the cloud sandbox** (network + Python 3.11): reconstruct
`shared/` and the environment directory in the container, run `./setup.sh` then
`./run.sh --accept-baseline`, and commit `results/`, `baselines/` and any new
tooling back to the device. Full surface notes in [`../MACHINE.md`](../MACHINE.md).

## What is comparable across machines, and what is not

- **Byte budgets and quality metrics are deterministic** and therefore
  comparable across machines.
- **Wall-clock is not.** Never compare a latency measured on one surface to one
  measured on another. Timing is the benchmark's job in any case
  ([SETUP-BENCHMARK](fux-benchmark.md)).

## The hazard in `shared/`

`shared/` is common to every environment, so **a bug there corrupts every
environment identically** — which looks exactly like a real finding. When a
quality number looks surprising, hand-verify `_score_pairs()`'s
`path.endswith(pair["doc"])` matcher against one known-good hit before believing
it.

`shared/regress/run.py` is accumulated tooling, corrected against four runs of
real observed CLI output. It is worth more than it looks.

## ⚠ Rebuilt 2026-08-20 — every pre-2026-08-20 environment is GONE

The whole directory was missing on 2026-08-20 (W-56), taking every baseline with
it. It was rebuilt as scaffolding and **is now a git repository, which it was
not before** — that is exactly why it was lost.

**What could not be rebuilt is every baseline and every corpus behind them.** A
corpus generated today is a *different* corpus, so a number taken now is a **new
baseline, not a comparison**, and every prior lab number is an unreproducible
historical record.

Two consequences that still bite:

- **R3's 27.2 ms p95 was measured on `rfc`**, 8 872 documents, which no longer
  exists. The number stands as a record; it cannot be re-run.
- **[`tools/pruning-eval/`](../../tools/pruning-eval/README.md) hard-codes
  `LAB = Path.home() / "my_programs" / "fux-lab"` and reads `acme` and `orbit`
  from it.** Both are gone. That harness ruled P1 and P1 closed **FAIL**
  permanently, so it is frozen history and nothing is owed — it is named here so
  a reader who opens it knows why it cannot run.

## What the lab established, and what happened to it

⚠ **Two of the three findings below are about a lane that no longer exists.**
The dense lane, its embedding model and `--hybrid` were deleted 2026-08-25 after
DENSE-CHUNK measured **0 fixed / 2 broken**; the corpora behind them (`acme`,
`orbit`) were lost in the wipe, so neither number can be reproduced. Kept as the
record of what the lab established, never as live guidance.

- **The synthetic "hybrid 4× worse" result did not reproduce** on a realistic
  corpus: hybrid hit@5 went `.182 → .855`, parity with lexical (`.873`). The
  collapse was near-identical template prose defeating dense retrieval — a
  corpus artifact, not an engine property.
- **Staleness: 9 of 12 inversions** — a superseded document outranking the
  still-true one, across all three marker styles. Ranking has no currency signal.
- **Zero-overlap dense rescue is 0 at every tier**, even where the answer
  dominates a short document.

## Every run's evidence is filed

Per run, in the same change: create `work/regression/<date>-<run>/`, drop the
report with `classification:` frontmatter and an `## Authorship` section, write
`ANALYSIS.md`, save the primary data **including per-query rows** under
`evidence/`, add a `VERDICT.md` if the run rules on a pre-registered threshold,
and add a row to [`../regression/README.md`](../regression/README.md).

**The reproduce command must actually reproduce.** A run whose numbers cannot be
regenerated is an anecdote.

## What L9 settled here, 2026-09-11

The 2026-08-22 *"multiple folders, each its own git repo, tiers 10 / 100 / 1000 /
5000 / 10000"* redesign sat in this document unexecuted for three weeks. **It is
answered, not deferred:** the ladder is the shape, its rungs are their own git
repos under `corpora/golden/`, and the tier list is L9's. The three open
questions that came with it — how `shared/` reaches independent repos, whether
the outer directory needs its own safety net, and the naming — are closed by the
layout above: `shared/` stays one copy at the lab root, the outer `.git` is the
safety net, and the name did not change.

## References (required)

- [ADR-LAW-9](../../docs/adr/0011_LAW-9-environments.md) — the law that gave this
  environment its one job and its data.
- [`work/golden/README.md`](../golden/README.md) — the sealed benchmark and the
  one rule about its key.
- [`../regression/README.md`](../regression/README.md) — where a run's evidence
  lands, and the per-run contract it lands under.
- **Why the instrument lives outside the system under test** — Sainz et al.,
  *NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for
  each Benchmark*, Findings of EMNLP 2023 — https://arxiv.org/abs/2310.18018
