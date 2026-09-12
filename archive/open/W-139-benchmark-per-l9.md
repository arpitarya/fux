---
type: OpenItem
id: W-139
title: "W-139 — build fux-benchmark to L9: seven corpora, two versions, latency and ranked lists kept"
description: "L9 (2026-09-11) defines the benchmark: folders of 100/200/500/1000/2000/5000/10000 documents of ~1000 lines (≤~300 chars wide) with tables, charts, bullet points and Mermaid diagrams; a fixed query set; every run times each query and keeps its ranked list, across the current build and the newest release of the previous major."
status: implemented
lane: agent
timestamp: 2026-09-11T00:00:00Z
closed: 2026-09-12
implementation: "work/IMPLEMENTATION.md — 2026-09-12, W-139"
---

# W-139 — `fux-benchmark` rebuilt to L9

**Model: Opus** — the corpus generator's realism, the query-set design and the
timing method (warm-up, repeats, what counts as one query) are design calls a
wrong answer to which still produces clean-looking numbers.

**The law:** `CLAUDE.md` L9 · **rationale:** [ADR-LAW-9](../../docs/adr/0011_LAW-9-environments.md) ·
**setup:** [SETUP-BENCHMARK](../setup/fux-benchmark.md) (rewritten in W-138).

## ✅ CLOSED 2026-09-12 — built, run once, and filed

**All six DoD clauses are met.** The harness, the corpora, the query set, both
arms, the rows and the filed run:
[`work/regression/2026-09-12-benchmark-l9/`](../regression/2026-09-12-benchmark-l9/report.md).

**What it found on its first run**, before anything else was measured:

- **Arm B (`2.0.0-alpha.7`) ingests ~2× faster than arm A (`1.0.0`)** at every
  tier to 5 000 — 37.7 s → 17.3 s at 1 000 documents — and writes a **~5 %
  smaller index**. ⚠ The ratio degrades to 0.77 at 10 000 and **one point is not
  a trend**.
- **The query-latency gap is a FIXED ~28 ms, not a slower search.** B − A runs
  35.7 → 18.9 ms across 200 → 5 000 while the *ratio* collapses 1.32 → 1.02, and
  marginal cost per 1 000 documents converges. **Quoting the ratio alone is the
  trap** — *"32 % slower"* is true at 200 documents and meaningless at 5 000.
- **31–54 of 60 ranked lists differ between the two majors, and almost none at
  the top** (6 of 60 at rank 1, at 5 000 documents).

🔴 **Two corpora are excluded and both exclusions are this session's fault, not
findings.** `docs-00100`'s timing was contaminated by a busy-wait poll loop of
mine; `docs-10000`'s query pass was **destroyed by a run-id collision** with a
second session. `--path fast` was **not run at all** — time, not a decision. All
three are named in the report rather than smoothed over.

**One durable fix came out of it:** `bench.py` takes an owner lock on
`runs/<id>/` and refuses a directory a live process holds. The null control
could never have caught that class — it compares one arm to itself inside one
process.

---

## Definition of done

1. ✅ **Corpora** under `~/my_programs/fux-benchmark/corpora/`: `docs-00100`,
   `docs-00200`, `docs-00500`, `docs-01000`, `docs-02000`, `docs-05000`,
   `docs-10000` — each document ~1 000 lines, lines ≤ ~300 characters, with
   tables, charts, bullet points and Mermaid diagrams; a mix of machine-like and
   multi-author (professional and amateur) styles. Deterministic generator, fixed
   seed; a sha256 manifest per folder. **Not** the golden data — that is the lab's.
2. ✅ **Query set** per corpus: fixed, versioned, committed with its manifest. No answer key.
3. ✅ **Two installs every run:** the current build and the newest release of the
   previous major (today `fux-engine` newest `1.x`), each in its own virtualenv;
   each indexes each folder once per version.
4. ✅ **Per run, per version, per query:** latency (repeats and warm-up stated),
   and the **ranked list** — top-k paths, scores, ranks.
5. ✅ **Kept and compared:** results filed under `work/regression/<date>-benchmark-…/`
   with `evidence/latency.csv` and `evidence/ranked-lists.jsonl`; the next run
   diffs its ranked lists against the previous run for the same version and
   reports what moved.
6. ✅ Stops at 10 000 documents.

## Blocked on

- ~~**W-138** (SETUP-BENCHMARK rewritten)~~ — **discharged 2026-09-12**; this was built against the rewritten document.

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🟠 **W-139 — build fux-benchmark to L9.** `agent`, after W-138 · *(record:
  [ADR-LAW-9](../../docs/adr/0011_LAW-9-environments.md))* · seven corpus folders
  (100 → 10 000 docs of ~1 000 lines with tables, charts, bullets and Mermaid), a
  fixed query set, every run timing each query and keeping its ranked list across
  the current build and the newest `1.x`, diffed against the previous run. —
  [detail](W-139-benchmark-per-l9.md) `filed: 2026-09-11`
