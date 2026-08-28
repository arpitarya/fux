# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Measurement plumbing

- **The lab and playground harnesses emit totals only.** `fux-benchmark`'s
  bench emits one row per query per arm, and
  `tests/test_regression_runs.py::test_measured_run_files_its_per_query_rows`
  gates it from **2026-08-29** — but `fux-lab/shared/regress/run.py` still
  reports `hit@k`/`mrr` aggregates and no rows. **A playground or lab run filed
  from 2026-08-29 will hit the gate with nothing to give it.** One emitter to
  fix, not a rule. `filed: 2026-08-28`

- ⚠ **No run filed before 2026-08-28 has per-query rows**, so no paired result
  from before that date can be re-tested by anybody, ever. Unfixable
  retroactively; recorded so nobody re-derives it as a surprise.

---

## Open items, by record

### [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) · [ADR-TUNE](../docs/adr/0038_tuning.md)

- 🔴 **W-94** · `arpit` · **`superseded_weight` ships at `1.0`, so the
  supersession prior is a no-op out of the box.** Measured
  [2026-08-28](regression/2026-08-28-benchmark-v1-vs-head/VERDICT-B2.md):
  `1.0.0` and `HEAD` invert a superseded document over its successor
  **identically** — 21 of 40 chains at tier 1 000 — because `HEAD` parses
  `supersedes:`, builds the edge, resolves the flag onto the retired document,
  and then multiplies its score by one. **Post-hoc at `0.5`: 21/40 → 0/40.**
  **The machinery works and is switched off.**
  🔴 **This does NOT mean "lower the default", and the run says so itself.**
  [`P-SUPERSEDE`](regression/2026-08-25-supersession-and-reranker-default/VERDICT.md)
  ruled that change **FAIL** on 2026-08-25 — at `0.5` on the playground it fixed
  one query and **broke two**, and *every* broken query had the **superseded
  document as its correct answer**. **The benchmark corpus cannot see that
  failure mode by construction.** The two results are consistent and **the older
  one is more informative**, because its corpus contains the case that breaks.
  **What is actually open is narrower:** a corpus declaring `supersedes:` gets
  nothing and **is told nothing** — `fux doctor` could disclose that, which is
  not a ranking change. ⚠ **Doing nothing is legitimate**: a disclosure gap, not
  a defect. `filed: 2026-08-28`

- ⚠ **`separation_floor` is repo-configurable and R10 is still unmeasured.**
  Not a new item — R10 is [W-90]'s — but the failure mode is: a repo can make
  its own answers read `grounded` without touching the ranking, and **nothing
  mechanical catches it**. The guard is that the block publishes the floor it
  was judged under. **Any run comparing two arms must assert their floors are
  equal**; differing floors is a pre-registered threshold moving inside a
  comparison, and it is ADR-CONFIDENCE decision 13's reopen trigger.

### [ADR-QUALITY](../docs/adr/0044_quality-contract.md) · [ADR-RS](../docs/adr/0036_predictions.md)

- 🔴 **The engine abstains ZERO times out of 20.** `arpit` · Blind-authored
  `unanswerable` questions, confirmed unanswerable by a second blind session;
  the engine reported `answerable: true` on all 20, 17 of them at or above the
  `separation_floor` ([run](regression/2026-08-28-blind-unanswerable/report.md)).
  **This is load-bearing**: ADR-QUALITY decision 5 puts the class *inside* the
  gate, so the `recall@k` headline describes the **answerable half only**.
  ⚠ **No threshold is proposed and R10 is untouched, deliberately** — a floor
  fitted to the 20 numbers that exposed the problem is the moving-threshold
  failure in a new costume. **Needs a call on whether it gates anything.**
  `filed: 2026-08-28`

- **Recall on a CLEAN corpus.** `agent` · The first `recall@k`
  ([run](regression/2026-08-28-first-recall/report.md), `@5` 0.9535) is
  `informed` — every installed enrichment file was authored by someone who had
  read these queries — so **it demonstrates the metric, not the engine.** The
  `none`/`placebo`/`real` arms already exist, so a clean absolute is one
  command. ⚠ Unlike `hit@k`, recall awards partial credit and **may separate
  arms `hit@k` could not**; that makes it a paired comparison needing discordant
  counts. `filed: 2026-08-28`

- **The 7 `partial` goldens.** `arpit` · The two blind annotators' exact-set
  disagreements, taking the union, held out of `recall@k`'s denominator. They
  need a human or a **third blind reader** — any session that has seen the
  scores is the wrong party. 🔴 **Do not resolve them by picking whichever set
  makes recall look better.** `filed: 2026-08-28`

- **W-95** · `agent` · **build a CONTESTED-answer suite; the marker suite is
  saturated.** `hit@5` came back **240/240 in both arms at every tier** — a term
  with `df = 1` is already rank 1 and no ranking change can move it, so `pb` and
  `pc` are structurally zero.
  🔴 **The reusable lesson, and it belongs to every paired run: a power table
  says how many queries, never whether the queries are HARD.** The
  pre-registration sized the set correctly and still could not detect anything.
  Both suites that *did* discriminate had contested answers. **Marker queries
  are a null-control instrument and must not be a primary endpoint again.**
  `filed: 2026-08-28`

- **W-96** · `agent` · **a `blind` version benchmark needs TWO sessions, and
  nothing makes that happen.** Whoever writes the generator and reads a score is
  `informed`, so the 2026-08-28 run is filed `informed` and states no delta. The
  protocol: one session authors and freezes the corpus, query sets and harness
  and **stops**; a second, which never reads them, executes and analyses.
  ⚠ **Not a process doc** — a handoff shape, worth one paragraph in
  SETUP-BENCHMARK plus the discipline to do it. `filed: 2026-08-28`

- **W-87** · `arpit` · **what "good" means, then measure.** P0, P1, P3, P4 and
  P5 are closed and `recall@k` now exists. ⚠ **Two things keep it open:** the
  `judged` series has never been exercised (no judged run exists), and **Part B
  cannot run** — `acme` and `orbit` went in the 2026-08-20 wipe with their
  generator, and `tools/pruning-eval/` hard-codes reading them. —
  [detail](open/W-87-what-good-means.md)

### Test-surface gaps

- **`tests_e2e/` has never run on Windows**, and `test_maintenance.py` is the
  suite most likely to differ: real git, real hooks, real detached processes.
  Verified on Linux/CPython 3.11.15 and macOS 15/arm64/CPython 3.14.2.

- ⚠ **`validate()` reaches an existing repo only when somebody copies the
  fetcher in.** `fux setup` is write-if-missing and never rewrites a consumer's
  file — [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) decision 6.
  **Measured 2026-08-28:** a repo created before the change learned **0 of 7**
  tokens until its `http.py` was replaced by hand. A `doctor` notice now names
  the gap, so it is **VISIBLE, not CLOSED** — the consumer still copies the
  function in by hand. **No further mechanism is proposed**: a loader that
  rewrote a consumer's committed file would be worse than the problem.

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
