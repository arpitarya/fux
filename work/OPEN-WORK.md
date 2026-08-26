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

### [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-RS](../docs/adr/0036_predictions.md) · the whole register

- **W-82** · `arpit` + `agent` · **filed 2026-08-26 — the consolidation.** Arpit collapsed the queue to one item: **W-74, W-75, W-77 and W-81 were merged**, along with the five documents behind them, into [one file](open/W-82-the-consolidated-build.md). ⚠ **A merge, not a close** — nothing was decided by moving it, and the archived originals may be named, never cited. ⚠ **The two compare verdicts were folded in verbatim first** (§4.1 the clock, §4.2 concurrency), because archiving a compare doc makes its verdict uncitable and §1's calls rest on them. **Four calls were made 2026-08-26**: the content store is **not built** (§6, with a reopen trigger); the detector is the **query-driven dirty list**, unconditional; **every cited URL is fetched before the final answer** — which is already shipped, and which **withdrew `update --warm` and `answer --memo` outright**; and concurrency is **declared capability**, `min(declared, configured)`. ✅ **FIVE OF THE SIX PHASES ARE BUILT (2026-08-26)** — §3.1 the URL health report, §3.2 the detector, §3.3 parallel fetch and the cap, §3.4 the changed/unchanged line, §3.6 the agent surface — with nine records amended in the same change and **1 433 unit tests green**. ⚠ **§3.0 and §3.5 did NOT land and neither is a code task**: §3.0 needs a real URL corpus to run `fux update` twice against, §3.5 needs `fux-playground`, and neither exists on the build machine. ⚠ **`tests_e2e/` is unverified** — it fails identically (55/11) on a clean tree there, so no regression, but *green* is not claimable. ⚠ **Three corrections the build made to the plan**: `url-state.json` may carry **no timestamp** (wall clock lives in the TTL store and nowhere else), **Kiro was already in `KNOWN_AGENTS`** so §3.6 extended rather than added it, and rung 4 is **`python -m fux.cli`**, which already works — retiring fork B's urgency. **The original six phases were startable by an agent alone** — the Phase 0 measurement that rules the `validate` fork, the `fux doctor` URL report, the detector, parallel fetch with the cap, the changed/unchanged line, and **§3.6 the agent surface** — plus the measurement apparatus (sealed subset, decoy set, content-free placebo, orphaned-module check), which is independent of all of it. ⚠ **§3.6 fixes a live defect, added 2026-08-26 on Arpit's instruction:** `fux.agent.md` tells an agent to run a bare `fux ask` and, on failure, *"say so and fall back to ordinary search"* — so **in any repo where fux is installed in `.venv` and the venv is not active, the agent gets `command not found`, concludes "not installed", and silently uses grep instead.** The engine is present and the index is committed. The fix is a **four-rung invocation ladder** (`fux` → `uv run fux` → `./.venv/bin/fux` → `python -m fux`, ⚠ the last **does not exist today** — there is no `__main__.py`), probed once per session, **never activating anything**, plus a `fux-usage` skill that teaches operation rather than interpretation — the two shipped skills cover only archived-result reading and enrichment.  ⚠ **Vendors RULED 2026-08-26: Claude and Kiro.** The finding that makes it cheap: **Kiro implements the same open Agent Skills standard Claude does** (`SKILL.md` + `name`/`description`), so `.claude/skills/<n>/SKILL.md` is already a valid Kiro skill — **one template, two destinations** (`.kiro/skills/`), agreement by construction rather than by conformance test. ⚠ Three Kiro traps, each checked against its docs: **Kiro CLI supports no steering inclusion modes** (every `.kiro/steering/` file loads on every interaction, so `manual` does not protect you — which is the argument for a *skill*, not steering); **Kiro custom agents load neither skills nor steering by default** and need explicit `skill://` / `file://` `resources`, so a consumer on a custom agent gets nothing and no error; and the `compatibility` frontmatter field is **a declaration nothing enforces**, so the ladder must live in the body. ⚠ **`prepare-then-ask` was folded into §6.0 verbatim** — its two flags are withdrawn, but the findings under them (a memo validated by a TTL hit reports `current` on unconfirmed bytes; a replayed answer is a fifth epistemic position; a memo key must include the index root hash) would otherwise have been lost to the archive. ⚠ **Twenty-seven forks remain Arpit's** and no agent may pick a default on any: eight on URL freshness (one ruled), six on what *"right"* means, six record rulings plus the archived-link fork and the governance gap, one on ADR-RS decision 12's scope defect, and the agent surface's, of which vendor choice is now ruled. ⚠ **The gap that survives every ruling:** fetching at answer time fixes correctness and **cannot fix recall** — a changed URL never enters the candidate window, so it is never cited, never fetched, and nothing notices — [detail](open/W-82-the-consolidated-build.md)

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
