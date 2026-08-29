---
type: Setup
name: SETUP-BENCHMARK
title: SETUP-BENCHMARK — fux-benchmark, the version-comparison harness
description: "How the two-engine benchmark environment is stood up, why it is a third sibling rather than a fux-lab environment, and the rules that keep an A-vs-B number honest."
location: ~/my_programs/fux-benchmark
kind: scratch working directory — commits nothing, never a deliverable
timestamp: 2026-08-28T00:00:00Z
---

# SETUP-BENCHMARK — `fux-benchmark`, the version-comparison harness

> **This is a setup document, not a decision record.** It records how the
> benchmark harness is stood up and the standing rules that govern it. See
> [`README.md`](README.md) for what belongs in this directory.

- **Name:** `SETUP-BENCHMARK` — cite this by name
- **Location:** `~/my_programs/fux-benchmark` — a **sibling working directory**,
  not a repository we ship and not a directory in this one
- **Siblings:** [SETUP-PLAYGROUND](fux-playground.md) grades ·
  [SETUP-LAB](fux-lab.md) measures · **this one compares**
- **Written:** 2026-08-28 ahead of the thing it describes; **built the same
  day** and corrected here to what was actually stood up

---

## Which is which, now that there are three

- **The playground GRADES.** Ten adversarial documents, ~50 golden queries
  asserting *ranks*. *"Did this change break an answer?"* Output: pass / xfail.
- **The lab MEASURES.** One environment per corpus, **one pinned engine
  version** each, its own baselines. *"How big, how fast, how accurate?"*
  Output: numbers, filed into [`../regression/`](../regression/README.md).
- **The benchmark COMPARES.** **Two engines resident at once**, over
  byte-identical corpora. *"What is the difference between these two
  versions?"* Output: paired per-query rows and a p-value, filed into
  `../regression/` like everything else.

## Why it is not a `fux-lab` environment

The lab's whole shape is one `VERSION` per environment directory — that is what
makes a baseline mean something, and it is why a lab number is comparable to
its own history. A version comparison needs **two installs live in one run,
interleaved**, over **one corpus**. Forcing that into a lab environment would
either break the one-version invariant or require two environments whose
corpora were generated separately, which is exactly the thing that must not
happen.

⚠ **This is additive and does not touch SETUP-LAB's standing rule.** *Never
delete `fux-lab`, never start a parallel harness* stands. `fux-benchmark` is
not a replacement lab: it **imports** `fux-lab/shared/generate/` rather than
reimplementing corpus generation, and if the two ever disagree about how a
corpus is made, **the lab is canonical**. A benchmark that quietly forked the
generator would produce numbers that look comparable to lab numbers and are not.

## Shape

```
~/my_programs/fux-benchmark/          # a git repo — the lab was lost once for not being one
  shared/ -> ../fux-lab/shared/       # generation, imported not copied
  arms/
    A/venv/                           # pip install fux-engine==1.0.0
    B/venv/  B/src/                   # a --local clone at the frozen sha, pip install -e
  corpora/
    t100/ t1000/ t10000/ t1000b/      # generated once, sha256 recorded, gitignored
                                      #   t1000b is the null control's second seed
  runs/<date>/
    work/<arm>-<tier>/                # each arm's OWN copy of the corpus and its own .fux/
    rows/                             # per-query rows — one file per arm per tier
  bin/
    bench.py          # prepare | quality | mcnemar
                      #   ⚠ owed by W-97, not built: --tune/--value, playground, select, veto, difflaw
    latency.py        # B5/B6, interleaved A B A B, and the differential law
```

⚠ **Two Python files, not the seven shell scripts an earlier draft of this
document listed.** The scripts were never written; `bench.py` and `latency.py`
are what exists and what the filed run used. Corrected here rather than left as
a plan somebody would go looking for.

⚠ **Each work directory is its own git repository.** `fux setup` anchors on the
**nearest git root**, not on `cwd` — the first attempt wrote `.fux/`, `.claude/`
and `.github/` into `fux-benchmark/` itself and left the corpus with no index.
Both arms do it, so it is not a version difference; it is a harness rule.

**`ARMS.toml` is the point of the whole directory.** ⚠ **It is generated into
the RUN's evidence** (`work/regression/<run>/evidence/ARMS.toml`), not kept at
the harness root — a manifest that lives beside the harness describes whatever
the harness is today, and a filed number needs the manifest it was produced
under. One file naming, for each arm: the install source, the resolved version, the Python minor version, the
`separation_floor` and `doc_coverage_floor` it emits, whether `.fux/enrich` is
present, and the corpus sha256 it read. **Every filed number carries the arm
manifest it was produced under**, because an A-vs-B number whose two arms
differed in a floor or an enrichment is not a version delta and there is
otherwise no way for a reader to tell.

## Standing rules

**0. Never delete it, never start a fourth harness.** Same rule as the lab,
same reason. New comparison work is a new `runs/<date>/` inside it.

**1. The null control runs first, every time — and it is the same-corpus
repeat.** Arm A twice on the *same* corpus must give byte-identical rows. A
difference means the harness is nondeterministic and **every number in that
session is void**. Running this last, after the interesting numbers exist, is
how a broken harness gets believed. ⚠ **A cross-seed pairing (A on seed 12 vs
A′ on seed 13) is a rate check, not a determinism check** — query ids are
positional, so it compares different questions. Run it, report it
descriptively, never let it stand in for the repeat (the 2026-08-28 v1-vs-HEAD
B9 was read that way and carries the weakness).

**2. Arms are interleaved, never sequenced.** `A B A B`, not `AAAA BBBB`.
Thermal drift on a laptop is a real effect and sequencing hands the second arm
a different machine.

**3. Per-query rows are written as the run goes.** One row per query per arm,
under the run's own directory, before any aggregate is computed. An aggregate
reconstructed after the fact is not evidence — three of the four marked runs in
`../regression/README.md` are untestable for exactly this reason.

**4. The harness never picks a threshold.** Every bar lives in the frozen
pre-registration under [`../benchmark/`](../benchmark/README.md).
`bench.py mcnemar` reads rows and prints a p-value; it does not know what
"pass" means.

**5. It commits nothing that matters.** Corpora, venvs and raw timings are
gitignored scratch. What survives a run is what lands in
[`../regression/<date>-<run>/`](../regression/README.md) under the per-run
contract.

**6. A knob sweep never re-ingests, and proves it.** ADR-TUNE's rule is that
`.fux/tune.toml` cannot move `.fux/index/`. A sweep therefore builds **one**
index per corpus and runs one query pass per value — and hashes the index
before and after **every** pass. A knob that moves the hash is not a tune knob;
its passes are void and the run files the defect. The procedure is
[`RUNBOOK-TUNER`](../benchmark/RUNBOOK-TUNER.md).

**7. The procedure lives in a runbook, the bars in a pre-registration, and
neither restates the other.** [`RUNBOOK-BENCHMARK`](../benchmark/RUNBOOK-BENCHMARK.md)
is the step-by-step an agent executes against either frozen version
pre-registration; it carries every gate and hazard this harness has taught, and
it is corrected as the harness teaches more. This document says what the
harness *is*; the runbook says what to *do*.

## The two-session blind protocol

**One session cannot produce a `blind` run here.** Whoever writes the generator
or the query sets and then reads a score is `informed`, and no delta may be
stated from an `informed` run — both 2026-08-28 runs are filed that way and say
so. Blind is a handoff shape, not a process document:

| session | does | stops after | may never see |
|---|---|---|---|
| **1 — author** (Opus) | extends the generator, writes the hand-authored subsets, defines every observable, generates and `sha256`-records the corpora, **commits with the hashes in the message** | the commit | any arm's output on the eval corpus; prior per-query scores |
| **2 — execute** (Sonnet; Opus for `ANALYSIS.md`) | verifies the hashes, runs the gates and the arms, analyses, files | filing | the generator's source, session 1's transcript, any failure list |

The hash is the handoff. If session 2 must open the generator (a bug), the run
is reclassified `informed` and says why. Skipping the protocol is legitimate —
the run is then `informed`, files everything, and states no delta. Claiming
`blind` from one session is not. Step-by-step:
[`RUNBOOK-BENCHMARK` §6](../benchmark/RUNBOOK-BENCHMARK.md).

## Where it can and cannot run

**Not on the Cowork device VM** — no network, Python 3.10; both arms install
from PyPI / a local editable install and need ≥ 3.11. On the local macOS shell
`uv` fetches CPython 3.11 for both arms, which is how the 2026-08-28 run was
executed.

⚠ **And the cloud sandbox is only half a home.** Quality and byte numbers are
deterministic, so the cloud is fine for **B1, B2, B3, B7, B9**. **Wall-clock is
not comparable across surfaces**, so **B5 and B6 must run on one machine, in
one session** — and if that is Arpit's laptop, the latency half of a run is
his to execute and the agent's to analyse. A run that quietly measures latency
in the cloud and quality on the laptop has published two numbers that cannot be
read together.

## The hazard

**`shared/` is imported from the lab, so a bug there corrupts both arms
identically** — which looks exactly like *"no detected change"* rather than
like a bug. The null control catches nondeterminism; it does **not** catch a
generator that plants a fact no arm can retrieve. When a tier shows both arms
failing the same queries, hand-verify one planted fact against the generated
document before believing the corpus.

## Every run's evidence is filed

Per run, in the same change: create `work/regression/<date>-<run>/`, drop the
report with `classification:` frontmatter and an `## Authorship` section, write
`ANALYSIS.md`, save per-query rows and `ARMS.toml` under `evidence/`, add a
`VERDICT.md` for each pre-registered threshold ruled on, and add a row to
[`../regression/README.md`](../regression/README.md).

**The reproduce command must actually reproduce.** A run whose numbers cannot
be regenerated is an anecdote.

## What the first run learned about this harness

Filed at
[`../regression/2026-08-28-benchmark-v1-vs-head/`](../regression/2026-08-28-benchmark-v1-vs-head/report.md).

- 🔴 **A saturated suite looks exactly like two equal engines.** The marker
  queries came back 240/240 in both arms at every tier. **Size the query set for
  power *and* check the queries can express the effect** — a power table answers
  only the first.
- ⚠ **One session cannot produce a `blind` run here.** The pre-registration's
  §3 says so in advance, and it is right: whoever writes the generator and reads
  the score is informed. A blind run needs one session to author and freeze the
  corpus and stop, and a second that never reads it to execute.
- **`fux answer` writes its repeat-query `note:` to stderr**, so a harness must
  capture stdout alone. Merging the streams makes `--json` unparseable
  intermittently, which reads as a flaky engine.
