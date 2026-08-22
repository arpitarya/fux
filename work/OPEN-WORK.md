# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — the inbox

**Empty.**

---

## Open items, by record

### [ADR-RS](../docs/adr/0036_predictions.md) — the prediction system, now owned

- **W-69** · `agent` · **STARTABLE** · build ADR-RS **veto 4's register check**,
  which is that record's **acceptance gate**. A test that walks
  `work/regression/*/VERDICT.md`, reads each `prediction:` id, and asserts a
  matching row in `IMPLEMENTATION.md`'s prediction table — **it would have
  caught R9**, which ran, passed and was cited in six documents while having no
  row, with nothing in the repo positioned to notice. **Small and mechanical**;
  the care is in the direction: *every filed verdict has a row*, not *every row
  has a verdict* (a RETIRED id has no verdict and must not fail). ⚠ **Accepting
  ADR-RS before this exists would mean accepting a record whose central claim is
  "the register is complete" while nothing verifies completeness** — the same
  class of error as an unmeasured gate. **Model: Sonnet** — decided design,
  assertable invariant — [detail](open/W-69-prediction-register-check.md)

### [ADR-GRAPH](../docs/adr/0029_graph.md) · [ADR-REFER](../docs/adr/0030_refer-plane.md) — the two planes that shipped ahead of their acceptance measurement

- **W-59** · `agent`+`arpit` · **R4 ran 2026-08-20 and PASSED** ([R4-REFER](regression/2026-08-20-refer-plane-r4/VERDICT.md)) — cold p95 **1.113 s** / 3 s, warm **0.016 s** / 300 ms, **with a boundary**: the plane fetches serially, so cold cost is `k ×` the source's latency and anything slower than ~295 ms breaches the bound at k=10. [ADR-REFER](../docs/adr/0030_refer-plane.md) went **`accepted` on 2026-08-21** (`9f8366e`, Arpit's call) — **with veto condition 2 left open, not closed**: the budget sweep reopens the record the moment it runs flat. **The stakes rose in the same change**: the plane is the default path in `fux answer` as of `v0.35.0`, so the assembler this item may delete is shipped code, not a spare part. **What keeps it open:** the budget sweep (**if it comes back flat the greedy assembler gets deleted, not kept**), which needs goldens a human must write (W-57); and ARC-vs-LRU, which was measured but **post-hoc** — the metric changed after seeing a number it reversed — so the cache compare doc's trigger is Arpit's to call — [detail](open/W-59-refer-plane-measurement.md)
- **W-57** · `arpit` · **blocked on the goldens — a human must write them** · the graph lane's acceptance measurement is unrun, and **re-scoped 2026-08-20**: `q005`/`q009`/`q011`/`q015` were ids in the lost golden set and cannot be recovered, so the targets are now **phenomena** (supersession · near-duplication · staleness≠wrongness), all three built deliberately into the rebuilt corpus. **The supersession gap already reproduces** — `what replaced helix mesh` returns the superseded doc above the ADR that replaced it — [detail](open/W-57-graph-lane-acceptance.md)

### [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) · [ADR-RANKING](../docs/adr/0012_ranking.md) — **parked**

*Both are gated on a pre-registered instrument that does not exist, is not an
item, and has no owner. **Parked with a trigger, not scheduled**: they resume
when the pre-registration is written, and not because they look ready.*

- **W-44** · `agent`+`arpit` · **the demotion weight landed 2026-08-22; the marker and disclaimer stay gated** · archived results — **scored normally, demotable, disclaimed**. **Landed:** the demotion weight ([ADR-DIR-LIST](../docs/adr/0022_dir-list.md) decision 11) — `[ranking] archived_weight` in `fux.toml`, **default `1.0`**, `fux.ingest.gitdir.archived_dirs()` reading the declaration (never a path), applied in the one shared `rank()` so the differential law carries it down both the scan and accelerator paths for free. Two tests, not one, per the ⚠ below: `tests/query/test_scan.py` asserts byte-identical results at the default **and** a live document overtaking an archived one once a weight is set; `tests_e2e/test_verbs.py` proves the same through the shipped CLI. **Still gated: the disclaimer** (decision 12, response-level, conditional) and the per-result `[archived]` marker — decision 10 says *"changing what a verb says about a document is a claim that needs an instrument"*, and the disclaimer says **more** than the marker, so it cannot be less gated. **Lifting that gate for the disclaimer alone is Arpit's call and is not assumed.** — [detail](open/W-44-archived-content-signalling.md)
- **W-52** · **PARKED** · `df` is computed over the union — **42% of live terms carry an inflated `df`**; **trigger: the same pre-registration, plus a second corpus** — [detail](open/W-52-df-over-the-union.md)

### No record — external validation

*Fux has never been measured against anything outside its own corpus or
fixtures. Owns no `src/`/`tools/` component — this is a measurement item,
not a build.*

- **W-62** · `agent`+`arpit` · **the README-fix half is agent-startable now; the three-way measurement and the five external installs are not** · moved here from PRIORITY.md's P8 row when that file was archived, 2026-08-21 — 50 real org-doc questions (Fux BM25F vs `rg` vs one commercial baseline, metric = agent task success and tokens, not p95) plus five external users' first-failure reports. **Why it matters**: 0 stars, a download pattern that looks like mirrors, and an industry converged on grep for local code — the wedge (private, off-disk enterprise docs) has never been tested against real docs or a real stranger's first fifteen minutes — [detail](open/W-62-measure-against-the-outside-world.md)

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
