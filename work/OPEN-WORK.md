# OPEN-WORK — what is still open

*One or two lines per item. Everything else lives in the item's file under [`open/`](open/README.md). Rules are at the foot.*

**Lanes:** `agent` — an agent closes it alone · `arpit` — only Arpit can. Both run concurrently.

**A ball on every row, always one:** 🔴 blocked on Arpit, directly or through another item · 🟡 waiting on another item · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (Arpit only). Full legend: rule 6.

---

## Blocked on Arpit

| what he decides | filed | age |
|---|---|---|
| 🔴 **W-136 phase 1** — did Codex write the ~100 answer-key questions? No → re-run [prompt 1](golden/prompts/1-codex-seed.md). Yes → run [prompt 1b](golden/prompts/1b-codex-feature-coverage.md), then phase 2. | 2026-09-11 | 1d |
| ↳ **blocks:** W-136 phase 2 · W-106 · W-112 · W-115 · W-97 · W-142 · W-87 · W-143 · W-144 | | |

---

## Open items

### fux build

- 🟢 🧨 **W-140** · `agent` — **6 code rows left** (6, 7, 12's `--hops` fork, 14, 16, 20) and the 13 record/code disagreements, none critical; 12 closed and one moved to W-122 on 2026-09-11. [detail](open/W-140-guide-authoring-defects.md)
- 🟢 🧨 **W-138** · `agent` — rewrite the ~40 artifacts that still use the playground as an instrument, and add the guard test. [detail](open/W-138-reconcile-with-l9.md)
- 🟡 **W-139** · `agent`, after W-138 — build fux-benchmark: seven corpora, two versions, latency and ranked lists kept. [detail](open/W-139-benchmark-per-l9.md)
- 🟢 🧨 **W-122** · `agent` — generate CLAUDE.md's law section, consolidate the doc-only schemas, gate ADR-CONFIG against `config.py`. [detail](open/W-122-adrs-are-the-source.md)
- 🟢 **W-107** · `agent` — the Node read plane (`npx fux-search`), Phases 1–4; nothing blocks Phase 1. [detail](open/W-107-node-read-plane.md)
- 🔴 **W-106** · `agent`, blocked on W-136 — the vector gate still owes the two-architecture arm and a golden corpus. [detail](open/W-106-vector-gate.md)
- 🔴 **W-112** · `arpit`, after W-106 — the vector plane: needs a golden corpus, a re-run gate, then a compare doc to rule on. [detail](open/W-112-vector-plane.md)

### testing

- 🔴 **W-136** · `arpit` (Codex phases), then `agent` — the sealed golden benchmark, grown 10 → 10 000. [detail](open/W-136-golden-benchmark.md)
- 🔴 **W-115** · `agent`, blocked on W-136 — the chunking change is unmeasured for quality; no document may cite it as measured. [detail](open/W-115-chunking-quality-unmeasured.md)
- 🔴 **W-97** · `agent`, blocked on W-136 — the knob sweep (`rerank_weight`, `superseded_weight`), rerun on golden data under a new pre-registration. [detail](open/W-97-tuner-knob-sweep.md)
- 🔴 **W-142** · `agent`, blocked on W-136 — rebuild the saturated `heading` negative control with headroom. [detail](open/W-142-heading-negative-control.md)
- 🔴 **W-87** · `agent`, blocked on W-136 — the first `judged` run, and Part B, both on the golden ladder. [detail](open/W-87-what-good-means.md)
- 🔴 **W-144** · `agent`, blocked on W-136 — does a table inflate `flen` and mis-rank a table-heavy document? The `structure-aware-extraction` proposal's trigger fired when OOXML landed. [detail](open/W-144-structure-aware-extraction.md)

### adr update

- 🔴 **W-143** · `agent` after W-136, then `arpit` — remeasure the four no-op ranking priors: does any single value clear 0 broken? [detail](open/W-143-four-no-op-priors.md)

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
   ⚠ **This file was 209 lines on 2026-08-28 and most of it was tombstones** —
   struck-through table rows, ✅ notes, and a section whose entire content was
   *"Empty. All seven closed."* **The length of this file is the signal of how
   much is actually pending**, and a queue that narrates its own history stops
   being that signal.
3. **Completed items are removed, never ticked.** Closing is legal only once
   the outcome is recorded in [`IMPLEMENTATION.md`](IMPLEMENTATION.md) and any
   evidence is filed under [`regression/`](regression/README.md). **The row is
   deleted; the detail file moves to [`archive/open/`](../archive/open/)**
   (Arpit, 2026-08-19) — the reasoning that produced a call is worth keeping,
   the queue entry is not. The durable record is still the ADR plus the
   [WORKLOG](WORKLOG.md) entry; an archived file may be named, never cited. No
   tombstones, no DONE rows, no `closed/` inside `work/`.
   ⚠ **Check what the row was the ONLY home of before deleting it.** W-82's
   carried the one written statement that answer-time verification cannot fix
   recall; deleting the row would have lost the claim, so it moved to
   [ADR-URL-INGEST](../docs/adr/0107_url-ingest.md) decision 9 first.
4. **The markers here are assertions, not evidence. Re-derive, do not read.**
   Before treating anything as pending or done, reconcile against
   `regression/`, `IMPLEMENTATION.md`, and the repo itself (`git log`,
   `git tag`, the code). A stale ✅ overstates progress; a stale pending row
   that an unrelated commit already closed understates it — **both are the same
   class of defect**.
   ⚠ **Three blockers filed here evaporated the moment a session had a shell**
   (2026-08-27/28): a whole section headed *"blocked on an environment that does
   not exist on the build machine"* naming environments that were on the machine,
   R10's, and W-87 P1's. **All three were filed by sessions that could not look.**
   Re-derive first; it is cheaper than the work it prevents.
5. **Two lanes, ordered independently — they run concurrently.** `arpit` needs
   a human's hands; `agent` an agent can execute alone. Forcing one priority
   order across both is what makes a session sit idle behind a decision it was
   never going to make. Order **within** a lane; never across them.
6. **Priority is damage that accrues with elapsed time**, above damage that is
   merely present-but-static. A wrong constant that is the same size next month
   can wait; an unratified record that more code ships under every day cannot.
   Only the latter gets worse by waiting.
   **Row marks (Arpit, 2026-09-11).**

   **A ball, always — exactly one per row. The balls are the primary legend:**
   - 🔴 **blocked on Arpit's decision — directly, or through any chain of items that ends at one.** A direct one has a *Blocked on Arpit* row; every item behind it is in that row's `↳ blocks:` sub-row.
   - 🟡 **waiting on another item, or on Codex, whose chain does not end at Arpit** — the row names what.
   - 🟢 **no blockers, good to go.**
   - **Red wins:** an item waiting on several things is 🔴 if any chain ends at Arpit. When a state changes, re-ball that row and every row waiting on it.

   **Then optional, in this order after the ball:**
   - 🧨 **broken, or getting worse every day it waits.** Any session sets or clears it, on any ball.
   - 🔺 **do first** (Obsidian Tasks' highest-priority sign) — **set and removed only by Arpit.** An agent never adds one.

   - **An agent picks from 🟢 only:** 🟢 🧨 🔺 → 🟢 🔺 → 🟢 🧨 → 🟢. 🔴 and 🟡 wait.
   - **A session names every 🔴 decision in its first output, 🔺 first.**
   - **A 🔺 item waiting on an item without 🔺 is flagged to Arpit**, never fixed by giving the blocker 🔺.
7. **No separate prioritization or sequencing document.** Ordering lives here.
   A second document naming what to do next is always the stale one.
8. **Grouped by what closing it takes — `fux build` (code), `testing`
   (a run or a harness), `adr update` (a ruling or a record, no code and no
   measurement) — changed 2026-08-29 from grouping by record, on Arpit's
   direction.** Law zero is unchanged and still binds every item: each item's
   detail file names the record its change will have to update — if you
   cannot name one, say **"no ADR affected"** out loud. What moved is only the
   sort key, not the obligation.
9. **No git housekeeping, ever** (Arpit, 2026-09-11). Nothing in this file
   says what is or is not committed, staged, pushed or unpushed — in this repo
   or any other. It is not work, it is stale the moment it is written, and
   `git status` already answers it. **If a repository's state blocks work,
   name what the work needs** (*"the playground indexes nothing"*), never its
   git status. A row asking whether to push is not a row.

10. **One or two lines per item — always** (Arpit, 2026-09-11).
    - **A row is:** ball, optional 🧨 and 🔺, id, lane, what is open, a link to its file.
    - **Everything else goes in the item's file under [`open/`](open/README.md):** status, evidence, records, rulings, hazards, history.
    - **An item with no file gets one, and an id, before it gets a row** — and the row gets its ball (rule 6) the day it is filed.
    - **Every *Blocked on Arpit* row is followed by a `↳ blocks:` sub-row** (Arpit, 2026-09-11): every item waiting on that decision, directly or through another item — or `nothing else in the queue`. An item waiting on a decision, directly or through another item, is 🔴 and joins that sub-row in the same edit.
    - Enforced by `tests/test_open_work_rows_are_short.py`.

## Standing obligations (every session)

- **WORKLOG entry per substantive exchange** — a chat-only session counts.
  (The `Cost:` line was mandatory here until 2026-08-21 — dropped, PRIORITY
  P7: 58/58 entries had said `unmeasured`.)
- **This file and the item's detail file** on any status change; a DOC-REGISTRY
  row bump for any doc you touched; INTERVIEW kept current *during* the session.
- **Reconcile before you report** (rule 4).
- **Records are cited by name** — `ADR-RECORD`, never a number. "archived
  ADR-NNNN" *with its path* means the frozen v0.26 line under
  `archive/v0.26-docs/adr/`; a bare `ADR-<NAME>` means `docs/adr/`.
- **No behaviour change lands without its record updated in the same change.**
  If a change genuinely touches no recorded decision, say **"no ADR affected"**
  in the commit message rather than skipping the check silently.
- **The lab persists.** `~/my_programs/fux-lab` is never deleted or rebuilt —
  new runs are new environments inside it ([SETUP-LAB](setup/fux-lab.md)).
