# Pre-registration — M6's first question: does T2 earn its place at 10 000 documents?

**Written before any number was produced.** The bar, the query populations, the
statistic and the decision rule are fixed here so they cannot be adjusted in the
direction the numbers happen to point. This file is committed, or at minimum
written, before the harness in this directory is run — see §0.2 for the honest
state of that guarantee.

If something below turns out to be under-specified once the data exists, the
move is to **record the ambiguity and hand the call to Arpit** — not to redefine
the term.

---

## 0. Disclosure

### 0.1 What is already known, and why this file is strict anyway

1. **R3 measured the T1 accelerator at 27.2 ms worst-case p95 on 8 870 RFCs**
   against a pre-registered 150 ms bar, on 2026-08-12
   ([the run](../../work/regression/2026-08-12-m2-accelerator/report.md)).
   8 870 documents is within 12 % of the current design point, so anyone
   writing this file has a strong prior that T1 clears the bar at 10 000.
2. **R3's own analysis already said T2 must not be pre-built** — *"the tripwire
   did not fire, so the escape stays unbuilt"* — and owed a re-measurement to
   M6.
3. **R3's corpus no longer exists.** The lab was lost on 2026-08-20 (W-56),
   taking the 8 872-RFC corpus with it. **A number taken now is a new baseline,
   not a confirmation of R3's**, and this file does not treat R3's 27.2 ms as
   evidence about anything measured here. What it takes from R3 is **the bar**,
   not the result.

The prior is therefore strong and the mitigation is that **the bar is not
invented here**. It is R3's own pre-registered 150 ms, reused unchanged at a new
corpus size. Choosing a *new* number after having seen R3's is the inversion the
pre-registration rule exists to stop;
[`graph-plane-format.compare.md`](../../work/compare/graph-plane-format.compare.md)
§6 says so in as many words, recommending exactly this — *"deriving it from the
**R3 precedent** (a query bar of 150 ms, on the accelerator) rather than from
anything measured here."*

### 0.2 The evidence chain, stated plainly

This file was written in a working tree carrying a large uncommitted change set
that a concurrent session also held, so **committing it alone before the run was
not available**. `git log` therefore cannot evidence the ordering.

What does: the bar is copied from a **frozen, already-committed** file
(`tools/pruning-eval/`-era R3, recorded in
`work/regression/2026-08-12-m2-accelerator/report.md`), so the number this run
is judged against predates this session by ten days and is not this session's to
choose.

### 0.3 The prediction id, and a collision that is not resolved here

This registers **R9**.

**R8 is already claimed**, by
[`graph-plane-format.compare.md`](../../work/compare/graph-plane-format.compare.md)
§6, for *"a graph verb answers in under X s at 100 000 documents"*. W-26's DoD
also refers to "whatever bar R8 sets" for T2. **Two documents claim R8 for two
different predictions.** This file does not adjudicate that — it takes R9 and
leaves R8 where it was named first and described in most detail. If Arpit would
rather T2 hold R8, renaming a prediction is cheap; silently overloading one is
not.

## 1. The question

**R9** — **at the 10 000-document design point, does the T1 accelerator answer
inside the R3 bar, or is a T2 tier needed?**

This is [W-26](../../work/open/W-26-m6-scale-t2.md)'s **first** question, and it
is asked before T2 is built rather than after. `tpack`, mmap byte-aligned
segments, partial clone and external-shards-only committing are all downstream
of it: if T1 clears the bar, the honest close is `ADR-T2-SEGMENTS` recording
**why T2 was not built**.

**What a FAIL would mean:** T1 is not sufficient at the design point and M6
builds T2. That is a larger, riskier milestone that also lands on the
maintenance path R5 just failed, so a FAIL is expensive and is not the outcome
being hoped for — which is precisely why the bar is fixed here.

## 2. The bar — R3's, verbatim, not restated loosely

**Warm `ask` ≤ 150 ms including worst-case terms.**

That string is R3's, reused unchanged. It is not reworded anywhere below, and no
tolerance is invented around it.

**The corpus size is 10 000 documents**, and the argument is made without
reference to any measurement: CLAUDE.md §Litmus makes 10 000 the design point as
of 2026-08-21, *"Fux is built, measured and judged at that size"*, and 50 000 and
100 000 are staged later targets that **may not gate work today**. A tier
question judged at a size fux is not built for would be measuring a system
nobody is shipping.

**The population curve is reported alongside and never blended into the
verdict**: 1 000 and 10 000 documents, each with its own row. That is M1's
lesson — *always report the fraction of the population a treatment actually
touches* — and it means a failure at 10 000 still yields the useful engineering
answer, *the size at which T1 stops being enough*.

### 2.1 What is timed

**`fux ask --fast` in-process, warm**, against a built accelerator: the T1 path,
which is what T2 would replace. Each query is run once to warm caches, then
timed as the **median of 3 runs**, exactly as R3 did — reusing a bar means
reusing the method that produced it.

The reference scan is timed too and reported beside it, **unjudged**. R3 found
the scan 28× over budget at RFC scale; whether that still holds is interesting
and gates nothing.

### 2.2 The query populations — reported separately, never blended

R3's threshold names worst-case terms explicitly, and an average over easy
queries is not R3.

| population | definition |
|---|---|
| **worst** | the 20 highest-`df` terms in the committed index, one query each |
| typical | 20 terms at the median `df` |
| multi-term | 20 queries of 3 terms each, drawn from the worst population |

**The verdict is read from `worst` alone.** The other two are reported.

### 2.3 The statistic

**p95 of the per-query medians**, judged on the `worst` population at 10 000
documents. R3 judged on p95 and reported median and max beside it; this does
the same.

### 2.4 The verdict rule

| outcome | condition | consequence |
|---|---|---|
| **PASS** | worst-population p95 **≤ 150 ms** at 10 000 documents | **T2 is not built.** `ADR-T2-SEGMENTS` is written as the record of a decision *not* to build, naming the measurement and the size at which it was taken |
| **FAIL** | worst-population p95 **> 150 ms** at 10 000 documents | T1 is insufficient at the design point; M6 builds T2 and `ADR-T2-SEGMENTS` records the format |

There is **no ambiguous band**: the bar is a hard inequality on a continuous
quantity, and inventing a tolerance would be the looser restatement the rule
forbids. What *is* handed to Arpit rather than adjudicated is anything the run
reveals about the bar's own construction — for instance, if the number is
dominated by a component the bar plainly did not have in mind.

**A PASS does not retire T2 forever.** It rules on 10 000 documents, which is
what the design point is. 50 000 is the next staged target and re-asking there
is a new pre-registration and a new verdict, never an edit to this one.

## 3. What this run does **not** measure, and does not claim

- **Not R7.** R7 is the committed-size prediction. Its budget was retired with
  the design point and **its re-derivation is explicitly Arpit's call**
  (W-26's re-scope box: *"Do not pick the number to fit the engine. If the
  re-derivation is not obvious, it is Arpit's call, not the runner's."*).
  Index size is recorded by this harness as **characterisation for the paper's
  §5 rewrite** and is **labelled post-hoc**; no budget is applied to it and no
  verdict is read from it.
  ⚠ **A budget chosen after reading that number would be contaminated by it.**
  R7's re-derivation should come from the paper's model and from product
  requirements, not from what the engine currently weighs.
- **Not tier-auto.** *"Tier-auto flips by measurement, never by hand"* governs a
  `[index] tier = t0|t1|t2|auto` knob that **does not exist in the code** —
  `fux.toml`'s `[index]` table holds only `shards`. There is nothing to flip and
  nothing here measures one.
- **Not a re-run or a confirmation of R3.** R3's corpus is gone (W-56). This is
  a new baseline on a new corpus.
- **Not the rebuild cost of a third tier.** W-26 warns that 47.6 % of R5's
  failing 44 s was `fux build`, and that any tier's rebuild cost must be
  measured before its default is chosen. That question only arises if this run
  FAILs.
- **Not portable milliseconds.** Latency is machine-specific (fux-lab TEST-PLAN
  §2). A re-run on another surface is a new measurement.

## 4. The instrument

- **Harness:** [`run.py`](run.py) in this directory.
- **Engine:** the working tree, by path. The commit sha is recorded in the
  report, with `+dirty` where the tree is not clean.
- **Corpus:** synthetic, generated by the lab's existing seeded generator
  (`~/my_programs/fux-lab/shared/generate/make_corpus.py`), deterministic and
  regenerable from `(docs, seed)`.
- **Surface:** recorded with the number.
- **Environment:** a **new** directory inside `~/my_programs/fux-lab`, per
  W-26's §Lab and TEST-PLAN §0b — the lab is never rebuilt.

## 5. Declared limitations (stated before the result, not after)

- **Synthetic corpus.** R3 ran on real RFCs. A generated corpus's vocabulary
  distribution and document lengths differ from real prose, and `df` — which
  decides the worst-case population — is exactly what a generator controls.
  **This is the limitation most likely to matter**, and it cuts both ways: a
  synthetic Zipfian corpus can be easier *or* harder than real text.
- **One surface, run locally rather than in the cloud.** W-26's §Lab says to run
  tiers in the cloud. No cloud runner is available in this session, so this runs
  on the device — the same deviation R3 declared, and stated for the same
  reason.
- **The evidence chain is weaker than R3's** (§0.2): this file was not committed
  before the run.
- **A strong prior** (§0.1): R3's 27.2 ms at 8 870 documents makes a PASS the
  expected outcome. Predicted here, in advance, so it cannot be presented
  afterwards as a finding.
