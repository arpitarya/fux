# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — the inbox

**Two calls, both filed 2026-08-20 out of R5's failure.** The three
non-blocking calls filed 2026-08-21 are all closed — each was taken on the
default its own detail file pre-authorised, which is what those defaults are
for. (W-64's hook question: show the bar. W-63's two: `fux url` deleted
outright, `ingest --refresh-urls` hidden for one release.)

> **The design point moved to 10 000 documents on 2026-08-21** (Arpit —
> CLAUDE.md §Litmus, which is the one normative home and is not restated here).
> **It did not close anything in this inbox**, and the rows below say what it
> did change. It did lower W-61's urgency from a 44 s problem to a 3.5 s one.

- **W-61 · the fork** — [`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md).
  **Open, lower urgency** (Arpit, 2026-08-21). R5 failed at 100 000 documents
  (44.4 s vs a 1 s bound) and [ADR-MAINTENANCE](../docs/adr/0033_hooks.md)
  veto 1 fired. Proposed **B — the hook defers**: commit cost becomes git's
  cost (**0.34 s at 100k, constant**), the only option reaching the bound at
  every size. **The design-point change did not close this — R5 fails at
  10 000 too, 3.523 s against the same 1 s bound**, passing only near ~1 500.
  What it *did* change is the option set: §0 of the compare doc shows that at
  10k the fixed cost is 0.216 s and **a 4× speedup of the two O(corpus) passes
  now reaches the bound**, where at 100k nothing under 100× did. **D is live
  again**; B still wins on holding at every size. The matrix still weights
  `holds at 10⁶ (×3)` and is re-weighted by whoever rules, in that change.
- **W-61 · R6's arithmetic** — the record it decides is
  [ADR-MERGE-DRIVER](../docs/adr/0034_merge-driver.md) since the 2026-08-21
  split, not ADR-MAINTENANCE. Every tier matched, tiers 2 and 3 informatively,
  but tier 1 also merged cleanly with the driver removed. **The
  pre-registration's §3.1 and §3.2 disagree about this exact result** ("does
  not count toward the pass" vs "tiers 1 and 2 must be informative"), so the
  runner did not adjudicate it. The instrument, not the threshold, is what
  should change — and not in the same change that files the verdict.

---

## Open items, by record

### [ADR-GRAPH](../docs/adr/0030_graph.md) · [ADR-REFER](../docs/adr/0031_refer-plane.md) · [ADR-RECORD](../docs/adr/0010_index-record.md) — the environments, and what they gate

- **W-61** · `arpit` · **both gates ran 2026-08-20. R5 **FAIL** ([R5-HOOK](regression/2026-08-20-r5-hook-latency/VERDICT.md)) — 44.4 s at the judged 100 000 documents against a **1 s** bound, and **0.651 s at 1 000, where it passes**. R6 **INCONCLUSIVE** ([R6-MERGE](regression/2026-08-20-r6-merge-driver/VERDICT.md)) — every tier matched, but tier 1 matched with the driver *removed* too, so it proves nothing.** The cost is two O(corpus) passes, and **a 10× speedup still misses the bound by 4.5×** — only taking the work off the commit path reaches it. **Two calls now sit with Arpit**: the fork ([`hook-at-scale.compare.md`](compare/hook-at-scale.compare.md), proposed **B — the hook defers**), and whether R6 reads as PASS under its own §3.1 or not-yet under §3.2. **Re-scoped 2026-08-21 — open at lower urgency**: the 10k design point leaves R5 failing (3.523 s vs 1 s) but makes it a 3.5 s problem rather than a 44 s one, and revives option D. **Neither the frozen pre-registration nor the filed verdict is edited** — a 10k bound would be a new pre-registration and a new verdict — [detail](open/W-61-maintenance-measurement.md)
- **W-59** · `agent`+`arpit` · **R4 ran 2026-08-20 and PASSED** ([R4-REFER](regression/2026-08-20-refer-plane-r4/VERDICT.md)) — cold p95 **1.113 s** / 3 s, warm **0.016 s** / 300 ms, **with a boundary**: the plane fetches serially, so cold cost is `k ×` the source's latency and anything slower than ~295 ms breaches the bound at k=10. [ADR-REFER](../docs/adr/0031_refer-plane.md) is still **`proposed`** — one gate passing is not the whole DoD. **What keeps it open:** the budget sweep (**if it comes back flat the greedy assembler gets deleted, not kept**), which needs goldens a human must write (W-57); and ARC-vs-LRU, which was measured but **post-hoc** — the metric changed after seeing a number it reversed — so the cache compare doc's trigger is Arpit's to call — [detail](open/W-59-refer-plane-measurement.md)
- **W-57** · `arpit` · **blocked on the goldens — a human must write them** · the graph lane's acceptance measurement is unrun, and **re-scoped 2026-08-20**: `q005`/`q009`/`q011`/`q015` were ids in the lost golden set and cannot be recovered, so the targets are now **phenomena** (supersession · near-duplication · staleness≠wrongness), all three built deliberately into the rebuilt corpus. **The supersession gap already reproduces** — `what replaced helix mesh` returns the superseded doc above the ADR that replaced it — [detail](open/W-57-graph-lane-acceptance.md)



### [ADR-DIR-LIST](../docs/adr/0023_dir-list.md) · [ADR-RANKING](../docs/adr/0012_ranking.md) — **parked**

*Both are gated on a pre-registered instrument that does not exist, is not an
item, and has no owner. **Parked with a trigger, not scheduled**: they resume
when the pre-registration is written, and not because they look ready.*

- **W-44** · **PARKED** · annotate archived results, never reorder — decided ([ADR-DIR-LIST](../docs/adr/0023_dir-list.md)); **trigger: a frozen query set with expected live-vs-archived answers exists** — [detail](open/W-44-archived-content-signalling.md)
- **W-52** · **PARKED** · `df` is computed over the union — **42% of live terms carry an inflated `df`**; **trigger: the same pre-registration, plus a second corpus** — [detail](open/W-52-df-over-the-union.md)

### No record — external validation

*Fux has never been measured against anything outside its own corpus or
fixtures. Owns no `src/`/`tools/` component — this is a measurement item,
not a build.*

- **W-62** · `agent`+`arpit` · **the README-fix half is agent-startable now; the three-way measurement and the five external installs are not** · moved here from PRIORITY.md's P8 row when that file was archived, 2026-08-21 — 50 real org-doc questions (Fux BM25F vs `rg` vs one commercial baseline, metric = agent task success and tokens, not p95) plus five external users' first-failure reports. **Why it matters**: 0 stars, a download pattern that looks like mirrors, and an industry converged on grep for local code — the wedge (private, off-disk enterprise docs) has never been tested against real docs or a real stranger's first fifteen minutes — [detail](open/W-62-measure-against-the-outside-world.md)

### Every record that argues from the old design point — the reconciliation

*No record owns this because it touches most of them. **Filed 2026-08-21, the
same day the design point moved**, so that the staleness it names is an item
rather than a silent inconsistency — the P2 precedent, at one tenth the size.*

- **W-65** · `agent` · **STARTABLE** · reconcile the record set to the
  10 000-document design point. **Nine live documents assert 10⁵–10⁶ as the
  design point** and are now stale: `ADR-POSTINGS` (doc-major is *argued from*
  that scale), `ADR-RECORD`, `ADR-TYPES`, `ADR-GRAPH`, `GLOSSARY`, and four
  compare docs (`pruning-criterion`, `file-type-filter`, `source-exclusion`,
  `refer-fetch-cache`, `storage-architecture`). **The fix is relabelling, not
  deletion** — an argument that holds at 10⁶ usually still holds at 10⁴, and
  the ones that *only* work at scale are exactly what this item must surface
  rather than quietly rewrite. **Two hard rules: frozen pre-registrations and
  filed `VERDICT.md`s are never edited** (`tools/maintenance-bench/PRE-REGISTRATION.md`
  stays as written), and **the paper is W-26's, not this item's** —
  [detail](open/W-65-design-point-reconciliation.md)

### No record yet — the unbuilt milestones

*Each writes its own record when it lands. **The detail file is the spec** —
`PLAN.md` was archived 2026-08-18 and its scope migrated into these files.*

- **W-26** · `agent` · **STARTABLE — the only agent-closable item requiring no external setup · RE-SCOPED TO 10 000 DOCUMENTS, Arpit 2026-08-21** · M6 scale & T2 — `tpack`, mmap segments, **10k + RFC bench (100k and 1M struck)**, paper §4–§6 rewritten to measured **at 10k**. **R7's budget is re-derived and pre-registered at 10k before any number is taken — the old ≤ 250 MB @100k row is history, not a divisor.** **And the milestone's first question is now whether T2 earns its place at all at 10k** — R3 measured 27.2 ms p95 on 8 870 RFCs, which is the design point almost exactly, so "T1 is enough" is a legitimate close that writes `ADR-T2-SEGMENTS` as a decision *not* to build. Its DoD wants *every* R prediction to carry **a measured value or an honest failure record**, and all four now do: R4 ✅ · R5 ❌ · R6 ⚠ · **R7 CLOSED unmeasured 2026-08-21** — [analysis](regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md); tier-auto correctness (R7's other half) stays unmeasurable until T2 exists — **still this milestone's own measurement to make, not a precondition for starting it.** **What it inherits from R5's failure:** 47.6 % of that 44 s is `fux build`, the derived plane M6 is about to add a *third tier* to — so measure any tier's rebuild cost before choosing its default. **What it inherits from R7's preliminary read:** the current committed index runs ~2× over a 250 MB@100k budget on real data — `ADR-POSTINGS`'s compact encoding (BIC/MPH, unbuilt) is the planned fix and is now better-motivated, not optional. **Unchanged:** tier-auto flips **by measurement, never by hand** — [detail](open/W-26-m6-scale-t2.md)
- **W-38** · **PARKED** · blocked by W-26 · M8 deferred set — one record + sign-off each; **pruning work is forbidden outside this item** — [detail](open/W-38-m8-deferred.md)

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

- **WORKLOG entry per substantive exchange** — a chat-only session counts.
  (The `Cost:` line was mandatory here until 2026-08-21 — dropped, PRIORITY
  P7: 58/58 entries had said `unmeasured`.)
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
