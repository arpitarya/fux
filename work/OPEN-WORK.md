---
type: Queue
description: "The single live work queue, two lanes, plus the Blocked-on-Arpit inbox."
---

# OPEN-WORK — what is still open

*One or two lines per item. Everything else lives in the item's file under [`open/`](open/README.md). Rules are at the foot.*

**Lanes:** `agent` — an agent closes it alone · `arpit` — only Arpit can. Both run concurrently.

**A ball on every row, always one:** 🔴 blocked on Arpit, directly or through another item · 🟡 waiting on another item · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (Arpit only). Full legend: rule 6.

---

## Blocked on Arpit

| what he decides | filed | age |
|---|---|---|
| 🔴 **W-145** — Codex re-runs [prompt 1](golden/prompts/1-codex-seed.md) part B and replaces the Claude-authored stopgap key, once his quota is back. [detail](open/W-145-codex-regenerates-the-key.md) | 2026-09-12 | 0d |
| ↳ **blocks:** **W-87's Part B**, which needs a key nobody has contaminated. Nothing else — it governs what a phase-5 number may *claim*, not whether phase 5 runs | | |
| 🔴 **W-146** — two rulings: is `ADR-WORK-QUEUE` written (OPEN-WORK's rules are stated twice, owned nowhere), and does *never restates* reach into docstrings? [detail](open/W-146-the-rest-of-l0.md) | 2026-09-12 | 0d |
| ↳ **blocks:** nothing else in the queue — they decide whether two named exposures get closed, not whether work runs | | |
| 🔴 **W-107** — **`PRE-REGISTRATION-NODE-2` is drafted; §7's two cells are yours**: does the latency fence `N9` live here or in fux-benchmark, and all eight rungs per push or two? [draft](benchmark/PRE-REGISTRATION-NODE-2.md) | 2026-09-12 | 0d |
| ↳ **blocks:** W-107's closure, and every differential-arm number — H3 bars calling any arm green until it exists | | |
| 🔴 **W-112** — W-106 closed **without a PASS and cannot produce one** (no corpus carries DENSE-CHUNK's bar). Proceed on the narrowed claim, wait for an instrument, or close? [detail](open/W-112-vector-plane.md) | 2026-09-12 | 0d |
| ↳ **blocks:** nothing else in the queue — search-v3's last item, and the only one left of §5 | | |
| 🔴 **W-147** — `.fux/output.toml` can switch the answer journal on, and ADR-PROVENANCE decision 10 says only the flag can — a fork that decision reserved and that shipped through a different record. [detail](open/W-147-the-journal-consent-surface.md) | 2026-09-12 | 0d |
| ↳ **blocks:** nothing — but one record is false and another is silent until he rules | | |
| 🔴 **W-143** — the four ranking priors answered **NO** ([verdict](regression/2026-09-12-priors-and-tables/VERDICT-W143.md)): close the knobs, move the mechanism query-side, or leave them at their no-op defaults. [detail](open/W-143-four-no-op-priors.md) | 2026-09-12 | 0d |
| ↳ **blocks:** W-97, whose candidate table is the same measurement and whose defaults are the same call | | |
| 🔴 **W-136** — the golden ladder is **complete, all eight rungs to 10 000**; everything an agent can do is done. **Phase 5 is Codex's hands** — [run prompt 5](golden/prompts/). [detail](open/W-136-golden-benchmark.md) | 2026-09-12 | 0d |
| ↳ **blocks:** **W-87**'s recall half and **W-144**'s cheap route, both of which read per-query scores off phase 5. Not W-145 — that governs what a number may *claim*, not whether it runs | | |
| 🔴 **W-144** — excluding table cells from `flen` **ranks better** ([verdict](regression/2026-09-12-reaim-and-instruments/VERDICT-W144.md)); one synthetic corpus may not ship a ranking change, so accept or override [the compare doc](compare/table-tokens-in-flen.compare.md). | 2026-09-12 | 0d |
| ↳ **blocks:** nothing else in the queue — the measurement is filed and the code is written; what is missing is the call | | |
| 🔴 **W-97** — the candidate table is filed with no recommendation, as pre-registered; the `superseded_weight` and `rerank_weight` defaults are an ADR-TUNE amendment only he makes. [detail](open/W-97-tuner-knob-sweep.md) | 2026-09-12 | 0d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🟡 **W-140** · `agent`, waiting on Arpit's `--hops` ruling — **1 code row left**: a runner-race flake **not reproduced in 11 attempts**, deliberately unchanged. 20 closed. [detail](open/W-140-guide-authoring-defects.md)
- 🔴 **W-107** · `agent` — the Node read plane: every agent-closable item is done. **O3 is drafted, not frozen** — `PRE-REGISTRATION-NODE-2` §7 has two cells only Arpit fills. [detail](open/W-107-node-read-plane.md)
- 🔴 **W-112** · `arpit` — the vector plane. W-106 closed without a PASS **and cannot produce one**: no corpus carries DENSE-CHUNK's bar. Determinism narrowed to *same embedder build*. [detail](open/W-112-vector-plane.md)

### testing

- 🔴 **W-136** · `arpit` — phase 2 **COMPLETE 2026-09-12, all eight rungs to 10 000**, nesting verified; **phase 5 scoring is Codex's hands** and is all that is left. [detail](open/W-136-golden-benchmark.md)
- 🔴 **W-145** · `arpit` — Codex regenerates the golden answer key; until then every golden number is `informed`. [detail](open/W-145-codex-regenerates-the-key.md)
- 🔴 **W-87** · `agent`, waiting on W-145 — P2's `unanswerable` gate is measured (0/124); recall needs phase 5 and **Part B needs an uncontaminated key**. [detail](open/W-87-what-good-means.md)
- 🔴 **W-144** · `arpit` — **answered 2026-09-12: the counterfactual ranks better** above a table share of ~0.29. One ruling: accept or override [the compare doc](compare/table-tokens-in-flen.compare.md). [detail](open/W-144-structure-aware-extraction.md)

### adr update

- 🔴 **W-147** · `arpit` — one ruling: is a committed `[cli.answer] journal = true` the explicit consent decision 10 asks for, or does `output.toml` refuse the key? [detail](open/W-147-the-journal-consent-surface.md)

- 🔴 **W-143** · `arpit` — **answered 2026-09-12: NO**, no single global value clears `0 broken` on any of the four priors. Close the knobs, move it query-side, or leave them. [detail](open/W-143-four-no-op-priors.md)
- 🔴 **W-97** · `arpit` — the candidate table is filed with no recommendation; the two defaults are an ADR-TUNE amendment. [detail](open/W-97-tuner-knob-sweep.md)
- 🔴 **W-146** · `arpit` — L0's remainder: eleven unhoused `CLAUDE.md` sections want records, and two rulings are owed. [detail](open/W-146-the-rest-of-l0.md)

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
   - ⚠ **The chain is read from the row's own words, by a fixed verb list** —
     `blocked on` · `after` · `waiting on` · `waits on`, followed by the id.
     `tests/test_open_work_rows_are_short.py` builds the whole red set from
     those four; a row that says *"through W-145"* names a real blocker the
     check cannot see, and fails as an unexplained 🔴. Use one of the four.

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
