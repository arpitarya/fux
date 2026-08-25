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

## ⚠ Planned redesign (2026-08-22) — not yet executed

**Arpit, 2026-08-22, direct:** *"[the lab] will have multiple folders in
it... All these directories are going to be individual git repos which will
have independent fux setup in them and should be used for testing or for
benchmarking by the agent."* Tier list confirmed in the same session: **10,
100, 1000, 5000, 10000** documents.

**Nothing below has been executed.** `fux-lab` on disk is still one git repo
with environment subdirectories — the rest of this document — until someone
builds this.

| | today (this document, below) | after this redesign |
|---|---|---|
| **outer structure** | `fux-lab` is one git repo; environments are subdirectories inside it | `fux-lab` is a plain directory; each tier is its own git repo inside it |
| **tiers** | `1k`, `5k`, `10k` (plus `acme`, `orbit`, `rfc`, `smoke`) | `10`, `100`, `1000`, `5000`, `10000` — the five numeric tiers Arpit named |
| **isolation** | already isolated (own venv/corpus/results/version pin) but sharing one `.git` | fully isolated, including version control |
| **`shared/` tooling** | one copy, common to every tier by construction | needs a strategy — see open questions below |

**Undecided, left alone unless a future ask says otherwise:** whether `acme`,
`orbit`, `rfc` and `smoke` — the existing non-numeric corpora documented below
— move into this structure, stay as they are, or are dropped.

**What survives untouched:** `shared/new-env.sh`, `shared/generate/make_corpus.py`
(seeded, byte-identical) and `shared/regress/run.py` all still do their job —
the question is only how they reach five independent repos instead of one.
The never-delete-or-rebuild standing rule and the cloud-sandbox requirement
(no network / Python 3.10 on the device VM) are unaffected.

**⚠ Hazard — the single-repo shape is why the 2026-08-20 loss was recoverable
at all.** `fux-lab` became a git repo specifically because losing it once,
with nothing to restore from, was expensive (see the rebuild note below).
Splitting into five independent repos with no enclosing repo removes
whatever protection that outer `.git` provided. **This redesign should not
drop that protection silently** — see open question 2.

**Open questions, Arpit's to resolve before anyone builds this:**

1. **How does `shared/` get into five independent repos?** Vendor a full
   copy into each (simple, can drift); keep one canonical `shared/` outside
   all five and have each tier pull from it (preserves "one fix, five tiers
   recover," adds a cross-repo dependency); or a git submodule per tier
   (correct versioning, adds submodule overhead).
2. **Does the outer `fux-lab` directory need its own safety net** — e.g. a
   manifest listing the five tier repos and their remotes/commits — or is
   reduced protection an accepted cost of independence?
3. **Naming** — Arpit called this "Fux setup" in conversation, not
   "fux-lab." This document assumes the existing name and location
   (`~/my_programs/fux-lab`) carry forward, since the purpose is unchanged and
   only the internal shape changes. Confirm before executing if a genuinely
   new, differently-named repo was meant instead.

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

## ⚠ Rebuilt 2026-08-20 — the environments below are GONE

**The whole directory was missing on 2026-08-20** (W-56), taking every baseline
with it. It has been rebuilt as scaffolding — `TEST-PLAN.md`,
`shared/new-env.sh`, `shared/generate/make_corpus.py` (seeded, byte-identical
for the same seed), `shared/regress/run.py`, and a `smoke/` environment run end
to end. **It is now a git repository, which it was not before** — that is
exactly why it was lost.

**What could not be rebuilt is every baseline and every corpus behind them.**
The table below is a record of what existed, not of what is there now. A corpus
generated today is a *different* corpus, so a number taken now is a **new
baseline, not a comparison**, and every prior lab number is an unreproducible
historical record.

Two consequences that bite immediately:

- **R3's 27.2 ms p95 was measured on `rfc`**, 8 872 documents, which no longer
  exists. The number stands as a record; it cannot be re-run.
- **`tools/pruning-eval/` hard-codes `LAB = Path.home() / "my_programs" /
  "fux-lab"` and reads `acme` and `orbit` from it.** Both are gone, so that
  harness cannot run until someone generates replacements — and replacements
  are not the same corpora.

## Environments that existed before 2026-08-20

| environment | what it is |
|---|---|
| `1k` · `5k` · `10k` | the scaling tiers; their baselines are what new numbers are compared against |
| `acme` | the realistic ~1k-file repo (929 files, 877 ingested, 59 typed eval pairs) generated by `shared/generate/make_repo.py` — built as the A-vs-B discriminator |
| `orbit` | warehouse / order-fulfilment, from `shared/generate/make_orbit.py` — the second corpus that generalised the supersession finding |
| `rfc` | 8 872 RFCs, median 967 distinct terms/doc — the corpus that made the pruning gate decidable |
| `2026-08-12-m2-r3` | the R3 accelerator bench root |
| **`smoke`** | **the only one that exists now** — 60 documents, seed 3, hit@5 1.0, created by the rebuild as proof the scaffolding runs |

`acme` and `orbit` are read from the lab by
[`tools/pruning-eval/`](../../tools/pruning-eval/README.md), which hard-codes
`LAB = Path.home() / "my_programs" / "fux-lab"`.

## What the lab has established

Three findings worth carrying, all of which came from the lab and none of which
the fixture gate caught:

⚠ **Superseded 2026-08-25 — the two rows below are findings about a lane that no longer exists.** The dense lane, the embedding model and `--hybrid` were deleted after DENSE-CHUNK measured **0 fixed / 2 broken**. They are kept as the record of what the lab established, not as live guidance; and the corpora behind them (`acme`, `orbit`) were lost in the 2026-08-20 wipe, so neither number can be reproduced.

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
