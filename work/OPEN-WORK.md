# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit — hands, not decisions

**One item.** Six of the original seven closed on 2026-08-27 — five git
operations, then the daemon run below, once a session had a shell and Arpit
authorised the network.

| # | do this | why it is stuck |
|---|---|---|
| 1 | **Sanity-check `L8`** in `CLAUDE.md` §Non-negotiable constraints and [ADR-LAWS](../docs/adr/0001_laws.md) decision 8 | A law was written and reverted the same day, from one sentence. Nothing mechanical checks that it says what Arpit meant. ⚠ **Its one-line handle was found stale on 2026-08-27** in ADR-LAWS' §1 table, `INTERVIEW.md`, `IMPLEMENTATION.md` and `compare/README.md`, all carrying the *withdrawn* first form. Reconciled to the live law — **a reconciliation, not a ratification** |

---

## Blocked on Arpit — decisions

- **W-82 ruling 3 — narrow-by-default — is now unblocked and awaiting the
  call.** The reason it was held was that the daemon had never been shown to
  work; it now has been, against real external URLs
  ([run](regression/2026-08-27-daemon-real-url/report.md)): TLS, DNS, two CDNs,
  a page that changed externally and was re-indexed unassisted one sweep later,
  a real `404`, and the **first ever exercise of the rate-limit path against a
  real `429`**. ⚠ **Proxy and SSO remain uncovered** and they are exactly where
  a sweep silently stops inside a corporation — which is narrow-by-default's
  blast radius. **The recommendation is that it may land. The session does not
  take the call.**
- ⚠ **R10 is `INCONCLUSIVE` because the pre-registration contradicts itself**,
  and the question is one line —
  [VERDICT](regression/2026-08-27-r10-separation-floor/VERDICT.md). On a curve
  that crosses `t`, falls back one bin, then rises: does the selection rule's
  *"stays at or above it"* govern (floor `0.5`), or the verdict table's
  non-monotone row (no change)? **Either answer is a NEW pre-registration, never
  an edit to the frozen one.** ⚠ Whichever way, six queries sit at or above
  `0.5` and no reading supports shipping a constant.
- **The daemon's status carries no reason**, and the 2026-08-27 run sharpened
  it: `_sweep` returns `"failed"` for a `FuxError` about `max_parallel` exactly
  as it does for a dead network — **and a sweep that returns `"ok"` can skip
  URLs silently too.** Two of seven URLs were skipped in a real run and the only
  surface that said so was a foreground `fux update` nobody runs. Widening the
  shape is a `maintain/state.schema.json` change and is not an agent's call.
- **Does a URL belong in `.fux/enrich/queue.tsv`?** The file path routes an
  unreadable document there with its reason; the URL path routes it nowhere
  (`grep -c queue urlsrc.py` → `0`), so **a URL that needs a model can never be
  queued for one.** `queue.tsv` is committed, so this changes committed bytes.
  [ADR-FETCHER](../docs/adr/0019_fetcher.md) decision 11 names it, undecided.
- 🔴 **One of fifteen unanswerable questions is reported `grounded`.** The decoy
  control's first run
  ([report](regression/2026-08-27-decoy-control/report.md)): `coverage` and
  `missing` are **corpus-wide**, so a query whose terms scatter across four
  different documents reports `coverage: 1.0`, `missing: []`, and falls through
  to the separation test, which it clears at `0.58` — **the exact failure
  [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) exists to prevent.**
  ⚠ **No ruling on R10 catches it**: `0.58` is above the `0.5` R10's selection
  rule would have picked, which is worth knowing **before** ruling R10. The fix
  — coverage against the **cited document** rather than the corpus — changes a
  declared signal, `output.schema.json`, the MCP result and every consumer.
  ADR-CONFIDENCE decision 12 names it, untaken.
- **Nine playground goldens have no `known_failure` annotation.** `check.py`
  supports the marker and the playground README documents *"41 pass · 9 xfail"*,
  but no golden carries one, so a full run reports `FAIL — 9 of 50`.
  **Annotating them turns a red gate green** — a judgement about what the suite
  should assert, not an agent's to make.
- **`fux/ingest/__init__.py` re-exports `run` under the submodule's own name.**
  This has now caused **three separate defects in one day** — a `NameError` that
  import checks missed, a broken test, and the dead daemon sweep. Each site is
  guarded now and a structural check refuses the shape in `src/`, but **renaming
  the export would remove the trap at the source.** It is an API change across
  the codebase.
- **Two `tests_e2e` post-commit tests now overlap almost exactly** —
  `test_the_post_commit_hook_reindexes_after_a_commit` and
  `test_post_commit_defers_and_a_detached_runner_drains_the_list`: same corpus,
  same commit, same assertion. Flagged in the docstring rather than deleted;
  which one survives is a call about what the suite should say.
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
| **W-87 P1** — ~~the decoy set~~, ~~the placebo arm~~, **the sealed query subset** | ✅ **Two of three BUILT 2026-08-27** — [`tools/quality-controls/`](../tools/quality-controls/README.md). **Only the sealed subset is left, and it is not mechanical**: decision 15 says sealing *shrinks* the visible set and whoever builds it must resolve that tension rather than inherit it. On 50 goldens both halves end up too small — a judgement, not a build |
| **W-87 P2** — `recall@k` as the headline; the `unanswerable` class, authored **blind** | annotation across the 50 goldens. ⚠ **Part B cannot run at all**: `acme` and `orbit` went in the 2026-08-20 lab wipe **along with their generator**, and `tools/pruning-eval/` still hard-codes reading them |
| **W-87 P3** (= W-82 §3.0) — sanitized-sha stability | a real URL corpus — **and one now exists**, `fux-lab/2026-08-27-daemon-real-url`, with seven real external URLs. ⚠ **Not blocked by P0 and never was** — its ≥80 %/≤40 % threshold is already frozen |
| **W-87 P4** — forks 3 & 4, `validate` and token storage | P3's number |
| ~~**W-90 R10**~~ | ✅ **RAN 2026-08-27** — [`INCONCLUSIVE`](regression/2026-08-27-r10-separation-floor/VERDICT.md), and the reason is in the decisions above, not here |
| **W-82 §3.5** | **`fux-playground` is available.** Build work, not a blocked input |
| ~~`tests/test_adr_freshness.py`~~ | **RAN 2026-08-27** and found a defect in itself — see the test-surface note below |

⚠ **ADR-RS decision 15 still reads `NOT BUILT`** and **keeps the marker**: it
names three controls and the sealed subset is missing. A decision that names
three is not in force on two.

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

- **W-90** · `arpit` · **the confidence plane. R10 RAN on 2026-08-27** and is
  [`INCONCLUSIVE`](regression/2026-08-27-r10-separation-floor/VERDICT.md) —
  **not because the data was thin (it was), but because the pre-registration
  froze two rules that disagree on this curve.** One question, in the decisions
  section above. `SEPARATION_FLOOR` stays `0.10`.
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
