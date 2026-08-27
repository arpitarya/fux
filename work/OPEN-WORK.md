# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — hands, not decisions

**Empty.** All seven closed on 2026-08-27 — five git operations, the daemon run,
and `L8` ratified. Removed rather than ticked, per rule 2.

---

## Blocked on Arpit — decisions

- ✅ **The fork counts were RE-DERIVED on 2026-08-27 and W-82 has ZERO open
  forks of its own.** 27 total; **18 ruled** by
  [the ledger](open/W-82-rulings-2026-08-27.md); of the remaining 9, **6** are
  §5.2's *"what right means"* (moved wholesale to
  [W-87](open/W-87-what-good-means.md)), **2** are forks 3 and 4 (moved to W-87
  P4 — **and fork 3's gate, P3, PASSED on 2026-08-27**), and **1** is §3.6 fork
  A, which the build answered rather than a ruling: the `fux-usage` skill
  shipped for both vendors. Verified against the code, not the prose —
  `__main__.py` exists (ruling 14), `copilot` is still in `install` (ruling 13).

---

## Blocked on an environment

⚠ **This section said "an environment that does not exist on the build machine"
until 2026-08-27, and on this machine that was false.** Both
`~/my_programs/fux-lab` and `~/my_programs/fux-playground` exist and work; the
playground still had its 50 goldens. The claim was filed by sessions that had no
shell and could not look. **Re-derive before believing a blocker** — rule 4.

| what | needs |
|---|---|
| ~~**W-87 P1**~~ | ✅ **ALL THREE BUILT** (2026-08-27/28) — [`tools/quality-controls/`](../tools/quality-controls/README.md). The sealed subset is 15 of 50, split by `sha256(id)`. ⚠ **5 of the 9 `known_failure` goldens landed in the sealed half** (33 % vs 11 %), which was **not corrected because correcting it means reading the scores** — a sealed score is not comparable to a visible one at this size |
| **W-87 P2** — `recall@k` as the headline; the `unanswerable` class, authored **blind** | annotation across the 50 goldens. ⚠ **Part B cannot run at all**: `acme` and `orbit` went in the 2026-08-20 lab wipe **along with their generator**, and `tools/pruning-eval/` still hard-codes reading them |
| **W-87 P3** (= W-82 §3.0) — sanitized-sha stability | a real URL corpus — **and one now exists**, `fux-lab/2026-08-27-daemon-real-url`, with seven real external URLs. ⚠ **Not blocked by P0 and never was** — its ≥80 %/≤40 % threshold is already frozen |
| **W-87 P4** — forks 3 & 4, `validate` and token storage | P3's number |
| ~~**W-90 R10**~~ | ✅ **RAN 2026-08-27** — [`INCONCLUSIVE`](regression/2026-08-27-r10-separation-floor/VERDICT.md), and the reason is in the decisions above, not here |
| **W-82 §3.5** | **`fux-playground` is available.** Build work, not a blocked input |
| ~~`tests/test_adr_freshness.py`~~ | **RAN 2026-08-27** and found a defect in itself — see the test-surface note below |

✅ **ADR-RS decision 15 lost `NOT BUILT` on 2026-08-28** — all three controls
are built. ⚠ **Built is not proven:** none has yet been used in a run that
adjudicates anything, and the marker moving does not make a control evidence.

⚠ **The ±2-query (4 pp) resolution floor is still a placeholder for a
measurement**, and **every "no detected change" ruling currently rests on it.**

---

## Open items, by record

### [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-RS](../docs/adr/0036_predictions.md)

- **W-82** · `arpit` · **the consolidation. Zero open forks of its own** —
  re-derived 2026-08-27, see §Blocked on Arpit — decisions. ⏸ **Ruling 3 is held
  on ONE CALL, not on evidence** — the daemon is verified against real external URLs
  ([run](regression/2026-08-27-daemon-real-url/report.md)) as well as
  [localhost](regression/2026-08-27-daemon-lifecycle/report.md). What is left is
  the judgement in §Blocked on Arpit — decisions: proxy and SSO are uncovered,
  and they are where a sweep silently stops inside a corporation.
  `fux update` still sweeps everything meanwhile, so nothing degrades while it
  waits. **Rulings 3 and 10 land together or neither
  does.** §3.0 and §3.5 are blocked on environments above.
  ⚠ **The gap that survives every ruling:** fetching at answer time fixes
  correctness and **cannot fix recall** — a changed URL never enters the
  candidate window, so it is never cited, never fetched, and nothing notices.
  ⚠ **Ruling 12's detection mechanism was never ruled** — the question was put
  and left unanswered, and the recommended shape was taken and named in the
  ledger. — [detail](open/W-82-the-consolidated-build.md) ·
  [rulings ledger](open/W-82-rulings-2026-08-27.md)

### [ADR-QUALITY](../docs/adr/0044_quality-contract.md) · [ADR-RS](../docs/adr/0036_predictions.md) · [ADR-LAWS](../docs/adr/0001_laws.md)

- **W-87** · `arpit` · **what "good" means, then measure.** **Nothing here is
  blocked on a decision.** P1–P4 are blocked on the inputs and environments
  listed above. — [detail](open/W-87-what-good-means.md)

### [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) · [ADR-QUALITY](../docs/adr/0044_quality-contract.md)

- **W-90** · ✅ **CLOSED 2026-08-28.** R10 ran, is
  [`INCONCLUSIVE`](regression/2026-08-27-r10-separation-floor/VERDICT.md), and
  its contradiction is **ruled**: the verdict table governs, so a non-monotone
  crossing is *no change* and `SEPARATION_FLOOR` stays `0.10`. `doc_coverage`
  ships as a published signal with **the gate ruled off** on a measurement.
  ⚠ **The verdict is unedited** — the rule is settled, the result is not
  overturned. ⚠ **Neither ruling reaches the `grounded` decoy at `0.58`**, which
  is recorded in ADR-CONFIDENCE decision 12 and is nobody's open item.
  ⚠ **`separation` is ORDINAL and Chow's rule assumes a probability** — the run
  named that gap rather than closing it, and **a report calling the result
  *calibrated* is wrong.** The wording was fixed in advance and was honoured.
  ⚠ **The power prediction held and was worse than forecast**: six queries sit
  at or above `separation 0.5`, the bin that first reaches `t` holds four, and
  the top two bins are **empty**. ⚠ **`separation == 1.0` never occurred**
  (n = 0) — the frozen special case did not fire on a 10-document corpus. —
  [detail](open/W-90-the-confidence-plane.md)

### [ADR-PROVENANCE](../docs/adr/0046_provenance.md) · [ADR-LAWS](../docs/adr/0001_laws.md)

- **W-91** · `arpit` · **the L8 sanity-check is the only thing left** (hands
  item 2). ⚠ **The AOL-2006 grounding is recorded as OVERRIDDEN, NOT REFUTED** —
  a later session may not cite the reversal as evidence the risk was disproved.
  — [detail](open/W-91-the-provenance-plane.md)

### Test-surface gaps

- **`tests_e2e/` is verified on TWO platforms** — Linux/CPython 3.11.15 and
  **macOS 15 / arm64 / CPython 3.14.2, 2026-08-27** (74 passed, 1 skipped;
  `fux-merge-index` not on `PATH`, which the suite skips loudly). **Windows is
  still unverified**, and `test_maintenance.py` is the suite most likely to
  differ: real git, real hooks, real detached processes.
- ✅ **The hook-vacuity gap is closed, and the claim it was filed under was
  wrong.** It read *"four hook tests go green-by-vacuity without `fux` on
  `PATH`"*. **Measured 2026-08-27** with `PATH=/usr/bin:/bin` (git present, fux
  absent): **4 failed, 9 passed** — the four post-commit tests assert a term is
  findable afterwards and fail hard. Exactly **one** passed vacuously,
  `test_nothing_fux_spawned_outlives_its_own_run`, whose every assertion is that
  something is ABSENT. It now carries a positive control, and
  `test_the_hook_environment_can_actually_find_fux` guards the whole class —
  including tests nobody has written yet. ADR-MAINTENANCE veto 10.
- ⚠ **The freshness gate convicted history, and had claimed in its own docstring
  that it never would.** `tests/test_adr_freshness.py` ran here for the first
  time on 2026-08-27 and flagged **eight commits** for not updating records that
  did not exist when they landed. The ownership table was read from the working
  tree; it is now parsed **per commit** from `git show <sha>:docs/adr/README.md`
  (ADR-OWNERSHIP decision 9), which is the third occurrence of a failure class
  `docs/adr/RULE-SINCE` had absorbed twice by retiring history. **`RULE-SINCE`
  did not move**, and a fourth entry on it would mean the fix failed
  (ADR-OWNERSHIP veto 6).

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
