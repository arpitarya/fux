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

### [ADR-RANKING](../docs/adr/0012_ranking.md) · [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) — **parked**

*W-52 is gated on a pre-registered instrument **plus a second corpus**. The
instrument now exists — [`tools/archived-signal-eval/`](../tools/archived-signal-eval/PRE-REGISTRATION.md),
frozen and run 2026-08-22 ([W44-SIGNAL](regression/2026-08-22-archived-signal/VERDICT.md)) —
so **half of W-52's trigger is met and the other half is not.** Still parked
with a trigger, not scheduled: a second corpus is a real prerequisite, because
moving `df` or the demotion default is a ranking change and CLAUDE.md forbids
shipping one off a single corpus.*

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
