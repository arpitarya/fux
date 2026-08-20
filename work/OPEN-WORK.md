# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — the inbox

**One, filed 2026-08-20.**

- **W-58** · **the compare doc is written and awaits a verdict** —
  [`record-freshness.compare.md`](compare/record-freshness.compare.md). Proposed
  **D — no age bound**: the engine already ships both endpoints of the freshness
  axis (`never` / `always`), and in HTTP — where the vocabulary comes from —
  `max-age` exists to **avoid the fetch**, not to make the answer more correct.
  That cost is unmeasured: **R4 has not run**. Deciding a cost optimisation
  before measuring the cost is backwards. **Not answered by W-60's verdict**
  (below) — that decision is scoped to a runtime cache, not the committed
  record.

---

## Open items, by record

### [ADR-GRAPH](../docs/adr/0030_graph-lane.md) · [ADR-REFER](../docs/adr/0031_refer-plane.md) · [ADR-RECORD](../docs/adr/0010_index-record.md) — the environments, and what they gate

- **W-58** · `arpit` · **the compare doc is written and awaits a verdict** — [`record-freshness.compare.md`](compare/record-freshness.compare.md). Proposed **D — no age bound**; `max_age_seconds` struck, content verification is the answer — [detail](open/W-58-no-recorded-ingest-time.md)
- **W-61** · `agent` · **held — Arpit's word required** · **M5 is built and its two gates are unrun.** [ADR-MAINTENANCE](../docs/adr/0033_maintenance.md) is **`proposed`, not accepted**, because of it. The harness is already written ([`tools/maintenance-bench/`](../tools/maintenance-bench/run.py)); what stands in its place is a *behaviour* test — the same merge conflicting without the driver and clean with it — which is **not R6**, and the record says so — [detail](open/W-61-maintenance-measurement.md)
- **W-59** · `agent` · **unblocked (the lab is back); held pending Arpit's word on prediction runs** · **the refer plane is built and unmeasured** — M4's core landed with 73 tests, and [ADR-REFER](../docs/adr/0031_refer-plane.md) is **`proposed`, not accepted**, because R4 has not run. Also unmeasured: the budget sweep (**if it comes back flat the greedy assembler gets deleted, not kept**) and ARC-vs-LRU against the cache compare doc's own reopen-trigger — [detail](open/W-59-refer-plane-measurement.md)
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

- **W-25** · `agent` · **next, and unblocked** · M5 maintenance — hooks, line-wise LWW merge driver, hashed-meta enforcement. **R5 and R6 need the lab (W-56)**: the build is unblocked, the gate is not — [detail](open/W-25-m5-maintenance.md)
- **W-26** · `agent` · **W-25 is done, but this cannot honestly start while prediction runs are held** · M6 scale & T2 — `tpack`, mmap segments, 100k/1M bench, paper §4–§6 rewritten to measured. **Its DoD requires *every* R prediction to have a measured value or an honest failure record**, and R4/R5/R6/R7 are all unrun (W-59 · W-61, held 2026-08-20). Building `tpack` and a T2 tier now would mean picking the tier-auto threshold by hand — which is the one thing the DoD forbids — and is the *build the fun part first* failure the gating rule exists to prevent — [detail](open/W-26-m6-scale-t2.md)
- **W-38** · **PARKED** · blocked by W-26 · M8 deferred set — one record + sign-off each; **pruning work is forbidden outside this item** — [detail](open/W-38-m8-deferred.md)

---

## Predictions still unmeasured

| id | prediction | threshold | measured at |
|----|-----------|-----------|-------------|
| R4 | refer plane | cold k=10 ≤ 3 s / warm ≤ 300 ms | **W-59** — the plane is built; the gate has not run |
| R5 | 20-doc commit re-index | < 1 s via hook | W-25 |
| R6 | machine planes conflict-free, human conflicts preserved | three-tier harness | W-25 |
| R7 | committed @100k target density | ≤ 250 MB packed; tier-auto correct | W-26 |

**All four run in `fux-lab`, and `fux-lab` is gone** ([W-56](open/W-56-sibling-environments-missing.md),
2026-08-20). No prediction in this table can be measured until it is back.

R1 **PASS** · **R2 3/3 PASS** ([run](regression/2026-08-12-r2-close/report.md)) ·
**R3 PASS** — worst-case p95 **27.2 ms** vs a 150 ms bar on 8 870 RFCs
([run](regression/2026-08-12-m2-accelerator/report.md)).
P1 **FAIL** — full postings, permanently
([verdict](regression/2026-08-09-pruning-rerun/VERDICT.md)); P2–P7 retired with
plan revision 1, their successors R3–R7.

**Where the build stands** is [`IMPLEMENTATION.md`](IMPLEMENTATION.md), not this
file. M0, M1, M2, **M3** and **M4's core** have shipped; **`v0.33.0` is on
PyPI** (2026-08-19, the sources rewrite — verified black-box from the published
wheel). M3 and M4 are **landed but unreleased and unmeasured**: their
acceptance runs are [W-57](open/W-57-graph-lane-acceptance.md) and
[W-59](open/W-59-refer-plane-measurement.md), both behind
[W-56](open/W-56-sibling-environments-missing.md).

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
