# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — decisions

- 🔴 **Adopt the measured resolution floor?** `CLAUDE.md` §Conformance runs calls
  ±2 queries a placeholder; it is worse than provisional. A paired exact test
  needs a net of **6–16** depending on how many queries flipped, and **at net 2
  the p-value is never below 0.68** —
  [the run](regression/2026-08-28-resolution-floor/report.md),
  [ADR-RS](../docs/adr/0036_predictions.md) decision 19.
  ⚠ **It is the wrong SHAPE, not just the wrong number**: the bar tracks the
  **flips**, not the set size, so replacing `2` with `8` would be a better wrong
  answer.
  ⚠ **Two filed uplifts sit under the real bar** — the reranker's `28 → 32` and
  W-78's enrichment deltas — **named and re-judged by nothing.** The losses are
  one-sided: a *"no detected change"* under a loose bar stays true under a strict
  one, so the exposure is entirely on claims of **improvement**.
  **Adopting it changes how filed results read, which is why it is yours.**
  ⚠ **The cheaper half needs no ruling and is not done: a run should state its
  DISCORDANT COUNT, and no filed run does** — so no paired result on record can
  be tested from what was filed.

- **Ratify `is_rate_limited(exc)`, or replace it.** W-82 ruling 12's detection
  mechanism was **put to you and left unanswered**, so an agent took the
  recommended shape: the fetcher declares it, and **fux never parses a status
  code, a header or an error string** (the alternative — matching `"429"` in
  `str(exc)` — was refused as branching on prose). **It is built, shipped and
  verified against a real 429**
  ([run](regression/2026-08-27-daemon-real-url/report.md)), which is exactly why
  it needs saying out loud: **a shape nobody ratified is now load-bearing.**
  Same class as `L8` was. — [ADR-FETCHER](../docs/adr/0019_fetcher.md)

---

## Blocked on an author who has not looked

**Not an environment and not a decision.** Both need somebody who has not read
the goldens, and this is the one blocker a session cannot clear by trying harder.

| what | why it needs a different author |
|---|---|
| **W-87 P2** — the `unanswerable` class | It must be authored **blind**. The 2026-08-27/28 sessions read the goldens, the decoys and per-query scores across four runs, so anything they wrote is informed **by construction**. ⚠ **The 15 decoys are NOT this class** — they are a control, and using them would launder informed material into a blind slot |
| **W-87 P2** — `recall@k` known-relevant sets | The same problem in reverse: marking documents relevant **after** seeing which ones rank well fits the metric to the system it judges. **The annotation must precede the scores** |

---

## Open items, by record

### [ADR-QUALITY](../docs/adr/0044_quality-contract.md) · [ADR-RS](../docs/adr/0036_predictions.md)

- **W-87** · `arpit` · **what "good" means, then measure.** **P1, P3 and P4 are
  closed**; what remains is P2.
  ⚠ **P2 Part B cannot run as specified at all**: `acme` and `orbit` went in the
  2026-08-20 lab wipe **along with their generator**, and `tools/pruning-eval/`
  still hard-codes reading them. **Part A — the declarations — needs none of
  that, and declaring is most of the value.**
  ⚠ **All three quality controls are BUILT and NONE IS PROVEN**
  ([`tools/quality-controls/`](../tools/quality-controls/README.md)): no run has
  yet used one to adjudicate anything, and ADR-RS decision 15 losing `NOT BUILT`
  did not make a control into evidence. —
  [detail](open/W-87-what-good-means.md)

### Test-surface gaps

- **`tests_e2e/` has never run on Windows**, and `test_maintenance.py` is the
  suite most likely to differ: real git, real hooks, real detached processes.
  Verified on Linux/CPython 3.11.15 and macOS 15/arm64/CPython 3.14.2.

- ⚠ **`validate()` reaches an existing repo only when somebody copies the
  fetcher in.** `fux setup` is write-if-missing and never rewrites a consumer's
  file — the freeze [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) decision 6
  names. **Measured 2026-08-28:** a repo created before the change learned **0 of
  7** tokens until its `http.py` was replaced by hand. **Stated as a cost with no
  mechanism proposed** — a loader that rewrote a consumer's file would be a worse
  problem than the one it solves.

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
   [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) decision 9 first.
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
