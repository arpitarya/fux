# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — the inbox

**Two, both filed 2026-08-20, both opened by R5's failure.**

- **W-61 · the fork** — [`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md).
  R5 failed at 100 000 documents (44.4 s vs a 1 s bound) and
  [ADR-MAINTENANCE](../docs/adr/0033_hooks.md) veto 1 fired. Proposed
  **B — the hook defers**: commit cost becomes git's cost (**0.34 s at 100k,
  constant**), and it is the only option that reaches the bound at every size.
  The measured attribution rules out the obvious alternative — two O(corpus)
  passes are the whole cost, so even **10× faster still misses by 4.5×**.
- **W-61 · R6's arithmetic** — every tier matched, tiers 2 and 3 informatively,
  but tier 1 also merged cleanly with the driver removed. **The
  pre-registration's §3.1 and §3.2 disagree about this exact result** ("does
  not count toward the pass" vs "tiers 1 and 2 must be informative"), so the
  runner did not adjudicate it. The instrument, not the threshold, is what
  should change — and not in the same change that files the verdict.

---

## Open items, by record

### [ADR-GRAPH](../docs/adr/0030_graph.md) · [ADR-REFER](../docs/adr/0031_refer-plane.md) · [ADR-RECORD](../docs/adr/0010_index-record.md) — the environments, and what they gate

- **W-61** · `arpit` · **both gates ran 2026-08-20. R5 **FAIL** ([R5-HOOK](regression/2026-08-20-r5-hook-latency/VERDICT.md)) — 44.4 s at the judged 100 000 documents against a **1 s** bound, and **0.651 s at 1 000, where it passes**. R6 **INCONCLUSIVE** ([R6-MERGE](regression/2026-08-20-r6-merge-driver/VERDICT.md)) — every tier matched, but tier 1 matched with the driver *removed* too, so it proves nothing.** The cost is two O(corpus) passes, and **a 10× speedup still misses the bound by 4.5×** — only taking the work off the commit path reaches it. **Two calls now sit with Arpit**: the fork ([`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md), proposed **B — the hook defers**), and whether R6 reads as PASS under its own §3.1 or not-yet under §3.2 — [detail](open/W-61-maintenance-measurement.md)
- **W-59** · `agent`+`arpit` · **R4 ran 2026-08-20 and PASSED** ([R4-REFER](regression/2026-08-20-refer-plane-r4/VERDICT.md)) — cold p95 **1.113 s** / 3 s, warm **0.016 s** / 300 ms, **with a boundary**: the plane fetches serially, so cold cost is `k ×` the source's latency and anything slower than ~295 ms breaches the bound at k=10. [ADR-REFER](../docs/adr/0031_refer-plane.md) is still **`proposed`** — one gate passing is not the whole DoD. **What keeps it open:** the budget sweep (**if it comes back flat the greedy assembler gets deleted, not kept**), which needs goldens a human must write (W-57); and ARC-vs-LRU, which was measured but **post-hoc** — the metric changed after seeing a number it reversed — so the cache compare doc's trigger is Arpit's to call — [detail](open/W-59-refer-plane-measurement.md)
- **W-57** · `arpit` · **blocked on the goldens — a human must write them** · the graph lane's acceptance measurement is unrun, and **re-scoped 2026-08-20**: `q005`/`q009`/`q011`/`q015` were ids in the lost golden set and cannot be recovered, so the targets are now **phenomena** (supersession · near-duplication · staleness≠wrongness), all three built deliberately into the rebuilt corpus. **The supersession gap already reproduces** — `what replaced helix mesh` returns the superseded doc above the ADR that replaced it — [detail](open/W-57-graph-lane-acceptance.md)

### [ADR-DIR-LIST](../docs/adr/0023_dir-list.md) · [ADR-RANKING](../docs/adr/0012_ranking.md) — **parked**

*Both are gated on a pre-registered instrument that does not exist, is not an
item, and has no owner. **Parked with a trigger, not scheduled**: they resume
when the pre-registration is written, and not because they look ready.*

- **W-44** · **PARKED** · annotate archived results, never reorder — decided ([ADR-DIR-LIST](../docs/adr/0023_dir-list.md)); **trigger: a frozen query set with expected live-vs-archived answers exists** — [detail](open/W-44-archived-content-signalling.md)
- **W-52** · **PARKED** · `df` is computed over the union — **42% of live terms carry an inflated `df`**; **trigger: the same pre-registration, plus a second corpus** — [detail](open/W-52-df-over-the-union.md)

### No record yet — the unbuilt milestones

*Each writes its own record when it lands. **The detail file is the spec** —
`PLAN.md` was archived 2026-08-18 and its scope migrated into these files.*

- **W-26** · `agent` · **STARTABLE — the only agent-closable item on this queue** · M6 scale & T2 — `tpack`, mmap segments, 100k/1M bench, paper §4–§6 rewritten to measured. Its DoD wants *every* R prediction to carry **a measured value or an honest failure record**, and all four now do: R4 ✅ · R5 ❌ · R6 ⚠ · **R7 CLOSED unmeasured 2026-08-21** — [analysis](regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md); tier-auto correctness (R7's other half) stays unmeasurable until T2 exists — **still this milestone's own measurement to make, not a precondition for starting it.** **What it inherits from R5's failure:** 47.6 % of that 44 s is `fux build`, the derived plane M6 is about to add a *third tier* to — so measure any tier's rebuild cost before choosing its default. **What it inherits from R7's preliminary read:** the current committed index runs ~2× over a 250 MB@100k budget on real data — `ADR-POSTINGS`'s compact encoding (BIC/MPH, unbuilt) is the planned fix and is now better-motivated, not optional. **Unchanged:** tier-auto flips **by measurement, never by hand** — [detail](open/W-26-m6-scale-t2.md)
- **W-38** · **PARKED** · blocked by W-26 · M8 deferred set — one record + sign-off each; **pruning work is forbidden outside this item** — [detail](open/W-38-m8-deferred.md)

---

## Predictions

**No rows left in "still unmeasured" — R7 closed 2026-08-21, unmeasured, on
Arpit's call.** No
pre-registration was written and no formal run happened; preliminary analysis
against this repo's own committed index (real git-pack compression, measured:
2.429×) extrapolates to **≈470 MB at 100k docs — ~2× over the 250 MB
budget** — [analysis](regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md).
**This is not the "wire format is dead" FAIL** PRIORITY.md's P3 row names for
a measured result: the format that analysis measured is today's plain-JSON
placeholder, not `ADR-POSTINGS`'s designed BIC/MPH encoding (⏳ proposed,
unbuilt) the threshold was actually sized against, and the shortfall tracks
closely with a known, closeable representation cost (hex-string keys vs.
packed binary). R7 stays formally unmeasured until that encoding exists;
tier-auto correctness remains unmeasurable regardless, since T2 doesn't
exist yet either (W-26).

**The hold was lifted by Arpit on 2026-08-20** and **R4, R5 and R6 all ran
that day** — their results are below, with the failures stated as plainly as
the pass.

**The lab was never the blocker it was recorded as.** Its environments install
the published `0.33.0` wheel, which predates every unreleased plane, so all
three benches measure the working tree by path and record its sha.

**R4 PASS** — cold p95 **1.113 s** vs a 3 s bar, warm **0.016 s** vs 300 ms, on a 100 ms mock source
([R4-REFER](regression/2026-08-20-refer-plane-r4/VERDICT.md)); the plane fetches **serially**, so the bound is a
statement about the source's latency at k=10, not about fux.
**R5 FAIL** — **44.4 s** at 100 000 documents vs a **1 s** bar
([R5-HOOK](regression/2026-08-20-r5-hook-latency/VERDICT.md)); it **passes at 1 000** (0.651 s), and the boundary
is near ~1 500. **R6 INCONCLUSIVE** ([R6-MERGE](regression/2026-08-20-r6-merge-driver/VERDICT.md)) — the engine
behaved; one of three tiers could not have failed, so the frozen table does not cover the result.
**R7 CLOSED, unmeasured** — ~2× over budget extrapolated from real data, but
against the wrong (unbuilt-encoding) format;
[analysis](regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md).
R1 **PASS** · **R2 3/3 PASS** ([run](regression/2026-08-12-r2-close/report.md)) ·
**R3 PASS** — worst-case p95 **27.2 ms** vs a 150 ms bar on 8 870 RFCs
([run](regression/2026-08-12-m2-accelerator/report.md)).
P1 **FAIL** — full postings, permanently
([verdict](regression/2026-08-09-pruning-rerun/VERDICT.md)); P2–P7 retired with
plan revision 1, their successors R3–R7.

**Where the build stands** is [`IMPLEMENTATION.md`](IMPLEMENTATION.md), not this
file. M0, M1, M2, **M3** and **M4's core** have shipped; **`v0.33.0` is on
PyPI** (2026-08-19, the sources rewrite — verified black-box from the published
wheel). M3 and M4 are **landed and unreleased**; M5 is landed, unreleased, and being
measured now. **M4 is no longer unmeasured** — R4 passed 2026-08-20 — but
[ADR-REFER](../docs/adr/0031_refer-plane.md) stays `proposed` until the budget
sweep runs, and that needs goldens a human must write
([W-57](open/W-57-graph-lane-acceptance.md)). M3's acceptance run is behind the
same goldens.

---
---

# The rules

*Kept at the foot deliberately: they change rarely, and the items are what a
session needs first.*

1. **Maintained in the same change as the work**, never afterwards. An item
   finishes, a defect is found, scope moves, something blocks or unblocks: this
   file and the item's detail file change in that same edit. A session that
   updates the queue "at the end" has already lied to the one after it.
2. **A resolved thing leaves this file entirely — including the sentence saying
   it resolved.** No "X was decided and left the inbox", no "closed on the
   12th", no note explaining an absence. **A row that is still here is still
   open**, and that is the only thing this file says. An item's own row may
   state that its *decision* is made and its build is not — that is its status,
   not a tombstone. Everything else about a closed item lives in
   [`IMPLEMENTATION.md`](IMPLEMENTATION.md), the [WORKLOG](WORKLOG.md), and the
   archived detail file.
3. **Completed items are removed, never ticked.** Closing is legal only once
   the outcome is recorded in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) and any
   evidence is filed under [`regression/`](regression/README.md). **The row is
   deleted; the detail file moves to [`archive/open/`](../archive/open/)**
   (Arpit, 2026-08-19) — the reasoning that produced a call is worth keeping,
   the queue entry is not. The durable record is still the ADR plus the
   [WORKLOG](WORKLOG.md) entry; an archived file may be named, never cited. No
   tombstones, no DONE rows, no `closed/` inside `work/`.
   **The length of this file is the signal of how much is actually pending.**
4. **The markers here are assertions, not evidence. Re-derive, do not read.**
   Before treating anything as pending or done, reconcile against
   `regression/`, `IMPLEMENTATION.md`, and the repo itself (`git log`,
   `git tag`, the code). A stale ✅ overstates progress; a stale pending row
   that an unrelated commit already closed understates it — **both are the same
   class of defect**.
5. **Two lanes, ordered independently — they run concurrently.** `arpit` needs
   a human's hands; `agent` an agent can execute alone. Forcing one priority
   order across both is what makes a session sit idle behind a decision it was
   never going to make. Order **within** a lane; never across them.
6. **Priority is damage that accrues with elapsed time**, above damage that is
   merely present-but-static. A wrong constant that is the same size next month
   can wait; an unratified record that more code ships under every day cannot.
   Only the former gets worse by waiting.
7. **No separate prioritization or sequencing document.** Ordering lives here.
   A second document naming what to do next is always the stale one.
8. **Grouped by record, because that is where the work lands.** An item's group
   is the record its change will have to update — which is Law zero made
   visible: if you cannot name the record, say **"no ADR affected"** out loud.

## Standing obligations (every session)

- **WORKLOG entry per substantive exchange**, with its `Cost:` line — a
  chat-only session counts.
- **This file and the item's detail file** on any status change; a DOC-REGISTRY
  row bump for any doc touched; INTERVIEW kept current *during* the session.
- **Reconcile before you report** (rule 4).
- **Records are cited by name** — `ADR-RECORD`, never a number. "archived
  ADR-NNNN" *with its path* means the frozen v0.26 line under
  `archive/v0.26-docs/adr/`; a bare `ADR-<NAME>` means `docs/adr/`.
- **No behaviour change lands without its record updated in the same change.**
  If a change genuinely touches no recorded decision, say **"no ADR affected"**
  in the commit message rather than skipping the check silently.
- **The lab persists.** `~/my_programs/fux-lab` is never deleted or rebuilt —
  new runs are new environments inside it ([SETUP-LAB](setup/fux-lab.md)).
