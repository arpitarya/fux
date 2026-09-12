---
type: Analysis
description: "The fixed-cost reading of the latency gap, the three specific improvements this run earned, and the two things it deliberately does not conclude."
run: 2026-09-12-benchmark-l9
filed: 2026-09-12
---

# ANALYSIS — the first two-version run

## 0 · What this analysis may and may not use

🔴 **Corrected after filing.** The other session disclosed that it was saturating
cores in `fux-lab` from ~13:00 to ~15:10 — **the whole of this sweep's timing
window**. So:

- **Every absolute latency is inflated by an unknown amount.** No conclusion
  below rests on one.
- **The A − B difference survives better**, because the arms are interleaved and
  each pair is adjacent in time. It is not proven robust; it is *designed* to
  be, and that is a weaker claim than a measurement.
- **Ranked lists are untouched** — ordering is deterministic and the null
  control says so twice. §2 stands as written.

## 1 · The latency gap is a fixed cost, and the ratio hides that

**B − A is 35.7 → 31.5 → 26.3 → 26.7 → 18.9 ms across 200 → 5 000 documents.**
It does not grow with the corpus; if anything it shrinks. The ratio over the
same points is 1.32 → 1.02, and **the ratio is the misleading number**: quoted
alone, *"alpha.7 is 32 % slower"* is true at 200 documents and meaningless at
5 000.

Marginal cost per 1 000 documents converges — A 208.2 ms, B 211.9 ms at the
5 000-document point — so **the search itself costs the same in both majors**
and the difference is paid once per process.

**The likely cause is import and start-up surface**, which grew across the major
(tuning, output config, PII, the acquired plane, enrichment digests). ⚠ **This
run did not measure that** — it measured whole processes. Attributing it is a
profile, not a benchmark, and is improvement 1 below.

⚠ **And the shape itself could be an artifact.** A fixed per-process cost and a
machine under variable load both produce a difference that shrinks as a
proportion of a growing total. **Improvement 1 is now the thing that would
settle it**, and it is cheap: `time python -c "import fux"` on both arms takes
seconds and needs no corpus at all.

**Why it matters anyway:** `fux ask` is one process per question, and MCP is
the surface where that cost is paid on every tool call. At 200 documents a third
of the answer time is start-up.

## 2 · The head of the ranking is stable; the tail is not

54 of 60 lists differ at 5 000 documents and **6** differ at rank 1. The same
shape holds at every corpus size. Two readings, and only the first is supported:

- ✅ **A major version bump changed almost every list and almost no top answer.**
  That is a fact about these two builds on this corpus.
- ❌ *"Therefore the ranking is fine."* **Not supported** — there is no key here
  and this harness may not acquire one. Whether a moved rank-4 is better is a
  lab question against the golden ladder.

## 3 · Specific improvements, each with a repro

| # | improvement | repro / where |
|---|---|---|
| 1 | **Attribute the ~28 ms.** Time `python -c "import fux"` and `fux --version` in both arms; if start-up accounts for it, the finding is *import cost*, which is actionable and cheap | `for a in A B; do time arms/$a/venv/bin/python -c "import fux"; done` |
| 2 | **Time `--path fast` too.** The accelerator is the path `--fast` selects and this run never touched it; a version comparison that measures only the reference scan can miss a regression in the shipped fast path entirely | `bench.py latency --path fast` (already built) |
| 3 | **`docs-10000` needs re-running ALONE on a quiet machine** — not merely under a unique run id. A fresh id fixes the file collision and does nothing about CPU contention, and the other session declined to re-run for exactly that reason. It is the only tier whose ingest ratio departs from 0.46 | §The collision in the report |
| 4 | **The harness cannot tell it is sharing a machine.** The owner lock sees a neighbour in the same run directory; nothing sees a neighbour indexing 10 000 documents next door. A cheap partial: sample load average at the start and end of a `latency` pass and write it into the rows, so a reader can *see* the condition rather than be told about it afterwards by a person | `bench.py cmd_latency` |

## 4 · The harness learned one thing the hard way

🔴 **Two processes in one `runs/<id>/` destroy each other silently.** Not
theoretical: it happened at 15:11 today and cost this run its largest corpus.
`cmd_latency` truncates its CSV with `"w"`, so the loser is whoever wrote first,
and `summarise()` cheerfully printed a three-query summary in the same format as
a sixty-query one.

**Fixed here** — `runs/<id>/.owner` carries the writing pid and `bench.py`
refuses a directory a live process holds, naming it. ⚠ **The null control could
never have caught this**: it compares one arm to itself inside one process, and
the neighbour arrives from outside.

⚠ **What is still unguarded:** nothing detects a neighbour that starts *after*
the claim and uses a different run id but the same machine. Timings taken while
another benchmark runs are wrong and no file says so. The honest mitigation is
the one already in SETUP-BENCHMARK — *latency is machine-bound, one machine, one
session* — and it is a sentence, not a check.

## 5 · Unresolved, and named as unresolved

- ✅ **Why the ingest ratio moves from 0.46 to 0.77 at 10 000 documents — now
  probably answered, and not by the engine.** That tier was ingested 12:58 –
  13:17, **inside** the contention window the other session disclosed; the six
  tiers with a ~0.46 ratio were all measured before it opened. **The cleanest
  reading is the machine.** It is *not* settled — contention was not uniform, and
  the arms ran sequentially there rather than interleaved, so load could have hit
  them unequally in either direction. **Re-measure that tier alone.**
- **Whether any of the 6 rank-1 changes at 5 000 documents is an improvement.**
  Out of scope here by construction and permanently: this environment has no key
  and, under L9, may not acquire one.
