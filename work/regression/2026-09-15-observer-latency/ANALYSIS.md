---
type: Analysis
run: 2026-09-15-observer-latency
description: "What a near-zero seam licenses W-170 to conclude, the one thing this instrument cannot see, and why the cap's weaker promise is the right one."
filed: 2026-09-15
---

# ANALYSIS — a free seam, and what that does not buy

## 1 · The diagnosis

**The hook's own cost is below the noise floor of a process-per-query
measurement, on a corpus of 1 239 documents and on one of 10 000.** The 10 000
delta is *negative*, which is the clearest statement available: whatever the
dispatch costs, it is smaller than the run-to-run variation of starting a Python
interpreter.

**That is the expected shape and it is worth saying why.** The dispatch runs
**once per process**, after the verb has rendered
([SR-OBSERVE](../../../records/0157_observe.md) decision 10d) — so its cost is a
constant, while everything the corpus size drives happened before it. A number
that *did* scale with the corpus would have meant the hook was reaching into the
verb, which is the one thing it must never do.

## 2 · What W-170's keep/remove call may now conclude

**Keep.** The evidence is that the seam a consumer pays for is `+0.7 ms` and
`−0.3 ms` on two corpora an order of magnitude apart, and that a hostile
observer cannot make `fux ask` slow.

⚠ **That is the seam's verdict, not the feature's**, and the distinction is
W-181's whole subject. A subscriber's observer does a subscriber's work; cage's
writes cage's ledger. **The reopen trigger is cage's number**, and until it
exists nothing here says what a real deployment pays.

## 3 · The cap: the record promises the weaker thing, and it is right to

Decision 6 said the observer is *killed*; decision 10b corrected it to
*abandoned*, because Python cannot safely interrupt arbitrary consumer code.

**Measured: `0 of 350` abandoned observers ever wrote their line**, across both
corpora, with a half-second grace after the sweep. In practice the thread dies
with the process.

🔴 **And that is exactly why the record must keep saying *abandoned*.** The
observed behaviour is a property of *this* shape — a short-lived CLI process
that exits while the thread sleeps. A consumer whose process outlives the sleep
(a longer verb, a slower machine, a shorter sleep) would see the write land, and
a record that promised *killed* would be wrong for them. **The weaker promise is
the true one**, and the measurement is the reason to trust the correction rather
than the reason to reverse it.

## 4 · What this instrument cannot see

1. **A subscriber's work.** By construction. §2.
2. **Any cost below ~1 ms.** Process-per-query is the shape a consumer pays, and
   it is a blunt instrument. An in-process timer would resolve the dispatch
   itself — and would measure something nobody runs, which is the trade
   `bench.py::ask` already makes for the same reason.
3. **Node.** Declared out of scope (SR-NODE-SEARCH decision 18).
4. **A repository with many observers.** One was installed. The dispatch is a
   loop, so N observers cost N times a call plus one directory listing — stated,
   not measured.

## 5 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | `tools/observer-bench/` — the reference observer, the slow observer, the interleaved runner | `python tools/observer-bench/run.py --root . --queries 40 --repeats 5 --cap-arm 2000` |
| 2 | **W-170's remaining obligation discharged**; it closes | `work/OPEN-WORK.md` |
| 3 | **W-186 filed** — every golden rung is unreadable by HEAD, found on the way to the second corpus. ⚠ **Closed the same day** | [the re-ingest](../2026-09-15-ladder-reingest/report.md) |

## 6 · Unresolved

- **Cage's number.** Not fux's to write, and the reopen trigger for §2.
- **The cost of N observers.** Stated as a loop, unmeasured.
- ⚠ **The absolute latencies are not comparable to any earlier ladder timing**,
  because the rung was re-ingested at `fux.index.v3` on a scratch copy. Nothing
  in this run needs them to be.
