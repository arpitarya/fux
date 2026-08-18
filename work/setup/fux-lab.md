---
type: Setup
name: SETUP-LAB
title: SETUP-LAB — fux-lab, the measurement environment
description: "How the scratch measurement environment is set up, why new work is a new environment inside it rather than a rebuild, and where each run's evidence has to land."
location: ~/my_programs/fux-lab
kind: scratch working directory — commits nothing, never a deliverable
timestamp: 2026-08-18T00:00:00Z
---

# SETUP-LAB — `fux-lab`, the measurement environment

> **This is a setup document, not a decision record.** It records how the lab
> is stood up and the standing rules that govern it. See [`README.md`](README.md)
> for what belongs in this directory.

- **Name:** `SETUP-LAB` — cite this by name
- **Location:** `~/my_programs/fux-lab` — a **sibling working directory**, not
  a repository we ship and not a directory in this one
- **Sibling of:** [SETUP-PLAYGROUND](fux-playground.md) — the two are often
  confused. The lab **measures**; the playground **grades**. See
  [`README.md`](README.md) §Which is which
- **Written:** 2026-08-18, from the accumulated record — the lab predates this
  document by weeks and had never been written up in one place

---

## What it is, and why it exists

The lab is where numbers come from. It holds **one directory per environment**
— a corpus, its own venv, its own baselines, and a pinned engine version — so a
measurement can be repeated against the same instrument that produced the
original.

It exists because the engine's own repo is the wrong place to measure the
engine. Corpora are large, generated, and version-pinned; baselines are only
meaningful against the exact corpus that produced them; and a measurement run
leaves debris that has no business in a repository whose whole premise is a
small committed index.

**The lab is scratch and commits nothing.** What survives a run is what lands
in [`work/regression/`](../regression/README.md), which is a repo law rather
than a convention.

## The standing rule — never delete it, never rebuild it

**Never delete `~/my_programs/fux-lab`, and never start a parallel harness.**
New test work is a **new environment inside it**:

```bash
cd ~/my_programs/fux-lab
shared/new-env.sh <name>
```

Arpit asked for this to be stated explicitly **in every prompt that drives a
run**, and it is recorded as standing rule §0b in `fux-lab/TEST-PLAN.md`.

**Why it matters:** the existing environments' baselines (`1k/`, `5k/`, `10k/`,
`acme`, `orbit`, `rfc`) are what a new run is *measured against*. Deleting them
means re-running everything before a new number means anything. Environments
are already isolated — own venv, own corpus, own results, own version pin — so
replacement buys nothing, and generated content is gitignored, so no cruft
accumulates.

## How to set up and run an environment

```bash
cd ~/my_programs/fux-lab
shared/new-env.sh <name>          # scaffolds the full flow, not just a corpus
cd <name>
# pin the version in VERSION to match whatever tiers this will be compared against
./setup.sh                        # bootstrap → generate → fux setup → ingest → verify
./run.sh --accept-baseline        # first run establishes the baseline
./run.sh                          # subsequent runs compare against it
```

`new-env.sh` emits the whole flow — bootstrap, generate, `fux setup`, `ingest`,
`--check`, and a present/MISSING verification block with per-plane sizes —
plus `run.sh`, a `fux` shim, and a README whose first line answers *"where is
`.fux/`?"*. That last detail is not decoration: the scaffolder once emitted a
corpus only, and every scaffolded environment reproduced the same confusion.

## Where it can and cannot run

**Not on the Cowork device VM.** It has **no network** and **Python 3.10**;
fux-engine needs ≥3.11 and installs from PyPI, so `setup.sh` cannot run there.

**Run the suite in the cloud sandbox** (network + Python 3.11): reconstruct
`shared/` and the environment directory in the container, run `./setup.sh` then
`./run.sh --accept-baseline`, and commit `results/`, `baselines/` and any new
tooling back to the device. Full surface notes in [`../MACHINE.md`](../MACHINE.md).

## What is comparable across machines, and what is not

- **Byte budgets and quality metrics are deterministic** and therefore
  comparable across machines.
- **Wall-clock is not.** Never compare a latency measured on one surface to one
  measured on another.

## The hazard in `shared/`

`shared/` is common to every environment, so **a bug there corrupts every tier
identically** — which looks exactly like a real finding. When a quality number
looks surprising, hand-verify `_score_pairs()`'s `path.endswith(pair["doc"])`
matcher against one known-good hit before believing it.

`shared/regress/run.py` is accumulated tooling, corrected against four runs of
real observed CLI output. It is worth more than it looks.

## Environments that exist

| environment | what it is |
|---|---|
| `1k` · `5k` · `10k` | the scaling tiers; their baselines are what new numbers are compared against |
| `acme` | the realistic ~1k-file repo (929 files, 877 ingested, 59 typed eval pairs) generated by `shared/generate/make_repo.py` — built as the A-vs-B discriminator |
| `orbit` | warehouse / order-fulfilment, from `shared/generate/make_orbit.py` — the second corpus that generalised the supersession finding |
| `rfc` | 8 872 RFCs, median 967 distinct terms/doc — the corpus that made the pruning gate decidable |
| `2026-08-12-m2-r3` | the R3 accelerator bench root |

`acme` and `orbit` are read from the lab by
[`tools/pruning-eval/`](../../tools/pruning-eval/README.md), which hard-codes
`LAB = Path.home() / "my_programs" / "fux-lab"`.

## What the lab has established

Three findings worth carrying, all of which came from the lab and none of which
the fixture gate caught:

- **The synthetic "hybrid 4× worse" result did not reproduce** on a realistic
  corpus: hybrid hit@5 went `.182 → .855`, parity with lexical (`.873`). The
  collapse was near-identical template prose defeating dense retrieval — a
  corpus artifact, not an engine property.
- **Staleness: 9 of 12 inversions** — a superseded document outranking the
  still-true one, across all three marker styles. Ranking has no currency
  signal.
- **Zero-overlap dense rescue is 0 at every tier**, even where the answer
  dominates a short document.

## Every run's evidence is filed

Per run, in the same change: create `work/regression/<date>-<run>/`, drop the
report, write `ANALYSIS.md`, save the primary data under `evidence/`, add a
`VERDICT.md` if the run rules on a pre-registered threshold, and add a row to
[`../regression/README.md`](../regression/README.md).

**The reproduce command must actually reproduce.** A run whose numbers cannot
be regenerated is an anecdote.
