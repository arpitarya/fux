---
type: Analysis
title: "R9 — what a 12x margin does and does not prove, and the corpus gap behind it"
description: "T1 clears R3's bar at the design point with 12x headroom. The synthetic corpus is 18x lighter per document than R3's; the judged quantity survives that better than the ratio suggests, and the reason is worth keeping. Three improvements, one live trap in the lab."
status: final
timestamp: 2026-08-22T00:00:00Z
---

# Analysis — R9

**Ruling:** [`VERDICT.md`](VERDICT.md) — **PASS** ·
**Report:** [`report.md`](report.md)

## The diagnosis

**T1 clears the bar at the design point by 12×, and the reason it does is
structural rather than lucky.** The accelerator's warm cost is governed by
posting-list traversal, which scales with **how many documents contain a
term** — i.e. with corpus size — and not with how long those documents are.
The population curve shows it directly: 1 000 → 1.25 ms, 10 000 → 12.46 ms,
linear in document count across a decade.

That is the property that makes the verdict robust to the corpus caveat below,
and it is also the property that makes the extrapolation to 50 000 (~62 ms)
plausible rather than idle — while still being arithmetic, not a measurement.

## The corpus gap — the run's real weakness

Declared before the run as *"the limitation most likely to matter"*, and it
did:

| | R3 (real RFCs) | R9 (synthetic) | ratio |
|---|---|---|---|
| bytes/document | 25 930 | 1 420 | **18.3×** |
| distinct terms | 419 627 | 11 316 | **37×** |
| scan worst p95 | 4 248.8 ms | 25.07 ms | 170× |
| **accel worst p95** | **27.2 ms** | **12.46 ms** | **2.2×** |

**The two right-hand ratios are the whole analysis.** The scan, which reads
every byte of every shard, shows the corpus gap at nearly its full 170×. The
accelerator shows 2.2×. That is the difference between a bytes-bound cost and
a `df`-bound one, measured rather than argued.

**Density-corrected cross-check (post-hoc).** Real prose costs the accelerator
about 2.5× more per document than this generator's output. Applying that to
12.46 ms gives ~31 ms at 10 000 real documents, against R3's measured 27.2 ms
at 8 870 — **within 15 %**. Two independent instruments, four months and two
corpora apart, agreeing to that tolerance is good evidence the harness is
measuring what it claims to.

**What is still missing, and is owed:** nobody has measured T1 on a *real*
10 000-document corpus, because the one R3 used was lost with the lab (W-56)
and the lab's generator produces a closed vocabulary by construction. The
consistency argument above is not a substitute, and a 12× margin is large
enough that closing this gap is not urgent — but it is the measurement that
would actually settle the question, and it does not exist.

## A finding the report should not bury

**The three query populations barely separate on this corpus** — 12.46 /
12.54 / 12.63 ms — where on R3's real corpus they separated by 2.3×
(27.2 / 11.6 / 27.7 ms). With a 30-word closed vocabulary, the "highest `df`"
term and the "median `df`" term are nearly the same term, so
`worst` stops being a distinct population.

**This weakens the instrument specifically where R3's bar is strongest.** R3's
threshold names *worst-case terms* precisely because an average over easy
queries is not the test. On this corpus the worst-case population is not much
worse than the typical one, so the run does less adversarial work than the bar
intends. It does not change the verdict — every population is 12× inside the
bar — but a future run at 50 000 should fix the generator's vocabulary before
reusing this harness.

## Specific improvements

### 1. Give the lab generator an open vocabulary before the next tier run

`shared/generate/make_corpus.py` draws from a closed ~30-word `COMMON` list
plus planted rare terms, which is exactly right for eval pairs (the finding
above is a side effect, not a defect in what it was built for) and wrong for a
`df`-distribution measurement.

**Repro:** the term counts in [`report.md`](report.md) — 11 316 distinct terms
across 10 000 documents is ~1.1 new terms per document, where real prose
follows Heaps' law and R3 measured 47 per document.

**Not done here**, deliberately: changing the generator mid-item would have
changed the instrument after seeing its output.

### 2. The stray `.fux/` at the fux-lab root is a live trap

`fux setup` in a fresh `2026-08-22-r9-t2/repo/` reported **"nothing to do —
every consumer-owned file is already here"** and wrote nothing. `find_root()`
walks up for `fux.toml` **or** `.git`, and the lab root has both — plus a
`.fux/` left by an earlier session run from the wrong directory. So setup
resolved to the lab root, found files there, and correctly did nothing, while
the environment stayed empty.

**Nothing is wrong with `find_root`** — it did exactly what
[ADR-CONFIG](../../../docs/adr/0014_config.md) says. The trap is that a lab
environment nested inside a git repository is indistinguishable from a
subdirectory of that repository.

**Repro:** `cd ~/my_programs/fux-lab/<env>/repo && fux setup` with no
`repo/fux.toml` present. **Workaround used:** write `repo/fux.toml` first.
**Fix owed:** either `shared/new-env.sh` writes `repo/fux.toml`, or the stray
`.fux/` and `fux.toml` are removed from the lab root. Both are fux-lab's, not
this repo's — filed here because this repo is where the evidence lives.

### 3. The lab's `setup.sh` pins a stale published wheel

It installs `fux-engine==0.33.0` from PyPI; the current release is `0.35.0` and
a tier measurement wants the working tree anyway. Every environment scaffolded
by `new-env.sh` inherits `VERSION=0.33.0`.

**Repro:** `cat ~/my_programs/fux-lab/<any-env>/VERSION`.

## Unresolved, stated as unresolved

- **Whether a real 10 000-document corpus changes the answer.** Argued above to
  be unlikely (2.5× density correction against a 12× margin), not measured.
- **What the accelerator's rebuild cost does at a third tier.** W-26 warns that
  47.6 % of R5's failing 44 s was `fux build`, and that any tier's rebuild cost
  must be measured before its default is chosen. **Moot for now** — the PASS
  means no third tier is built — but the warning stands the day one is
  proposed.
- **Whether the linear curve holds past 10 000.** Two points make a line;
  they do not make a law. 50 000 is a new pre-registration.
