# OPEN-WORK — what is still open

*Items first, grouped by the record they belong to. **The rules and the standing
obligations are at the foot of this file** — read them once, then work from the
top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Agent work the resolution-floor ruling creates

- ✅ **Per-query rows now exist and are now gated** — this row's original
  complaint is closed. `fux-benchmark/bin/bench.py` emits one row per query per
  arm per tier, and
  [`2026-08-28-benchmark-v1-vs-head`](regression/2026-08-28-benchmark-v1-vs-head/report.md)
  is the first run in the store to file them (10 row files, every suite).
  `tests/test_regression_runs.py::test_measured_run_files_its_per_query_rows`
  is the owed check.
  ⚠ **Baselined at 2026-08-29, not 2026-08-28, and that is deliberate**: five
  runs were filed on the ruling's own day before any harness could emit rows,
  their reports are frozen, and turning a rule on by editing the evidence it
  governs is the failure `CLASSIFY_SINCE` exists to avoid. **So the gate fires
  first on the NEXT run filed**, and a fixture-level test guards the baseline
  from drifting past the runs it exempts.
  ⚠ **What is NOT closed: the lab and playground harnesses still emit totals
  only.** `fux-lab/shared/regress/run.py` reports `hit@k`/`mrr` aggregates and
  no rows. A playground or lab run filed from 2026-08-29 will hit the new gate
  and have nothing to give it — **that is the next thing to fix**, and it is one
  emitter, not a rule.
- ⚠ **The pre-2026-08-28 runs still have no per-query rows**, so no paired
  result filed before that date can be re-tested by anybody. That is unchanged
  and unfixable retroactively.
  ✅ **The `+9` is the exception and it is now settled.** This row previously
  said it was *"impossible to check, impossible to re-run (the corpora went in
  the 2026-08-20 wipe)"* — **both claims were false.** The wipe took `acme` and
  `orbit`; the `+9` was measured on **`fux-playground`**, which is on the
  machine. Re-run 2026-08-28: reproduces `32 → 41` exactly, and its discordant
  count is filed — **`n_d = 9`, `b = 0`, `c = 9`, `p = 0.0039`, which CLEARS
  the floor** ([run](regression/2026-08-28-placebo-and-seal/report.md)).
  It remains `informed` and is not a generalisation estimate.
  🔴 **Rule 4 with a receipt** — an item asserting a measurement was impossible
  was refuted by attempting it, in one command. **Fourth recorded instance** of
  a blocker filed by a session that could not look.

---

## Ready to run — nothing here is blocked on a decision

**Empty.** Everything that was here on 2026-08-28 ran; what came out of it is a
decision, and decisions live in the lane below.

---

## Open items, by record

### [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) · [ADR-TUNE](../docs/adr/0038_tuning.md)

- 🔴 **W-94** · `arpit` · **`superseded_weight` ships at `1.0`, so the
  supersession prior is a no-op out of the box.** Measured
  [2026-08-28](regression/2026-08-28-benchmark-v1-vs-head/VERDICT-B2.md):
  `1.0.0` and `HEAD` invert a superseded document over its successor
  **identically** — 21 of 40 chains at tier 1 000 — because `HEAD` parses
  `supersedes:`, builds the edge, resolves the flag onto the retired document,
  and then multiplies its score by one. **Post-hoc at `0.5`: 21/40 → 0/40**,
  21 fixed, 0 broken, marker retrieval untouched. **The machinery works and is
  switched off.**
  🔴 **This does NOT mean "lower the default", and the run says so itself.**
  [`P-SUPERSEDE`](regression/2026-08-25-supersession-and-reranker-default/VERDICT.md)
  already ruled that change **FAIL** on 2026-08-25 — at `0.5` on the playground
  it fixed one query and **broke two**, and *every* broken query had the
  **superseded document as its correct answer**. **The benchmark corpus cannot
  see that failure mode by construction**: every planted chain query's right
  answer is the successor. The two results are consistent and **the older one is
  more informative**, because its corpus contains the case that breaks.
  **So what is actually open is narrower:** a corpus that declares `supersedes:`
  today gets nothing from it **and is told nothing** — `fux doctor` could
  disclose that the prior is disabled, which is not a ranking change. The deeper
  fix is P-SUPERSEDE's own diagnosis: **supersession belongs to the query's
  intent, and a per-document multiplier cannot express it.**
  ⚠ **Doing nothing is a legitimate choice here** — this is a disclosure gap,
  not a defect. `filed: 2026-08-28`

- ⚠ **`separation_floor` is now repo-configurable and R10 is still unmeasured.**
      This is **not** a new item — R10 is [W-90]'s and unchanged — but the
      failure mode is new: a repo can now make its own answers read `grounded`
      without touching the ranking, and **nothing mechanical catches it**. The
      guard is that the block publishes the floor it was judged under. **Any
      future run that compares two arms must assert their floors are equal**;
      differing floors is a pre-registered threshold moving inside a comparison,
      and it is ADR-CONFIDENCE decision 13's reopen trigger.

### [ADR-QUALITY](../docs/adr/0044_quality-contract.md) · [ADR-RS](../docs/adr/0036_predictions.md)

- **W-95** · `agent` · **build a CONTESTED-answer suite; the marker suite is
  saturated.** `hit@5` came back **240/240 in both arms at every tier** on
  2026-08-28 — a term with `df = 1` is already rank 1 and no ranking change can
  move it, so `pb` and `pc` are structurally zero.
  🔴 **The reusable lesson, and it belongs to every paired run this repo files:
  a power table says how many queries, never whether the queries are HARD.**
  The pre-registration sized the set correctly and still could not detect
  anything. The two suites that *did* discriminate both had contested answers
  (chains: 50 % inversions; decoys: an occasional top-5 false positive).
  **Marker queries are a null-control instrument and must not be a primary
  quality endpoint again.** `filed: 2026-08-28`

- **W-96** · `agent` · **a `blind` version benchmark needs TWO sessions, and
  nothing makes that happen.** The pre-registration said it in advance and it
  was right: whoever writes the generator and reads a score is `informed`, so
  the 2026-08-28 run is filed `informed` and states no delta. The protocol is
  one session authoring and freezing the corpus, query sets and harness and
  **stopping**; a second, which never reads them, executing and analysing.
  ⚠ **Not a process doc** — it is a handoff shape, and it is worth exactly one
  paragraph in SETUP-BENCHMARK plus the discipline to do it. `filed: 2026-08-28`

- **W-87** · `arpit` · **what "good" means, then measure.** **P0, P1, P3, P4 and
  P5 are closed. Only P2 remains, and it is down to ONE ADR plus one impossible
  part.** ⚠ **This item cannot close** — its definition of done requires
  `recall@k` computed, and that now waits on a decision, not on work.
  ✅ **P1 CLOSED 2026-08-28.** All four controls built; **three used to
  adjudicate** (decoys 2026-08-27; `unanswerable` and placebo 2026-08-28).
  The placebo's result is a real clearing: matched-length content-free prose
  moved **one** query (`p = 1.0000`), so **source bias does not explain
  enrichment's lift** — though it clears source bias and *not* contamination.
  🔴 **The sealed subset is EXERCISED, NOT PROVEN** — it postdates the
  enrichment it was applied to, so its split cannot test contamination. That is
  chronology, not an unbuilt control; it lives in ADR-RS decision 15 now.
  ✅ **THE SCHEMA IS RULED — option B (Arpit, 2026-08-28).** The rank contract
  and the relevance set are **two fields**;
  [ADR-QUALITY](../docs/adr/0044_quality-contract.md) **decision 12** carries the
  four rules and [`tools/quality/goldens.py`](../tools/quality/goldens.py)
  enforces them (+12 tests). The evidence was two mutually-blind annotators at
  **κ = 0.960** finding **25 of 50** questions multi-document against one
  asserted ([run](regression/2026-08-28-annotator-agreement/report.md)).
  **The migrated 50-query set is built and validated — 43 `complete`, 7
  `partial`, 26 multi-document** — and `recall@k` becomes computable over 43/50
  the moment it lands.
  ⚠ **What is left is MECHANICAL, not a decision:** swap the playground's
  `queries.jsonl` for the migrated file (a sibling repo with its own
  uncommitted work — placed there as `goldens/queries.decision12.jsonl`, **not**
  overwritten), then compute the number and report it **with the 43/50 fraction
  beside it**, which rule b requires.
  ⚠ **P2 Part B still cannot run as specified**: `acme` and `orbit` went in the
  2026-08-20 lab wipe with their generator, and `tools/pruning-eval/` hard-codes
  reading them.
  🔴 **The abstention result is the largest finding and is NOT tracked by this
  row's DoD**: the engine did not abstain once on 20 of 20 blind-authored
  unanswerable questions. Named because P2's funnel starts at `in window`, and a
  system that never declines has no usable top of funnel. **No threshold
  proposed; R10 untouched.** — [detail](open/W-87-what-good-means.md)

### Test-surface gaps

- **`tests_e2e/` has never run on Windows**, and `test_maintenance.py` is the
  suite most likely to differ: real git, real hooks, real detached processes.
  Verified on Linux/CPython 3.11.15 and macOS 15/arm64/CPython 3.14.2.

- ⚠ **`validate()` still reaches an existing repo only when somebody copies the
  fetcher in — but the repo is now TOLD.** `fux setup` is write-if-missing and
  never rewrites a consumer's file, the freeze
  [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) decision 6 names.
  **Measured 2026-08-28:** a repo created before the change learned **0 of 7**
  tokens until its `http.py` was replaced by hand.
  ✅ **A `doctor` notice shipped 2026-08-28** — `fetcher optional functions`,
  decision 6's own named mechanism (*a loader refusal or a `doctor` check, never
  a rewrite*). It reads the fetcher **as text, never importing it** (doctor is
  offline; a fetcher may connect at import) and names each missing function, its
  record, and the cost. **Warning, never an error** — absence is legal by
  contract.
  ⚠ **The gap is VISIBLE, not CLOSED.** The consumer still copies the function
  in by hand. **No further mechanism is proposed**, and a loader that rewrote a
  consumer's committed file would be a worse problem than the one it solves.

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
