# OPEN-WORK — what is still open

*Items first, grouped by what closing them takes — **fux build**, **testing**,
**adr update**. Every item still names the record it belongs to, inline: Law
zero (CLAUDE.md) still requires an owning record be nameable, it just isn't
the sorting key any more. **The rules and the standing obligations are at the
foot of this file** — read them once, then work from the top.*

**Lane tags:** `agent` — an agent can close it alone · `arpit` — only Arpit can.
The two run **concurrently**; never order one against the other.

---

## Blocked on Arpit

*Named here so a session leads with it instead of burying it. **The oldest is
5 days — at CLAUDE.md's threshold, not past it** — so nothing is age-flagged
today. A session that finds one that IS names it, with its age, in its first
output.*

| what he decides | filed | age |
|---|---|---|
| **The ETag acceptance criterion, re-worded or accepted.** *"`fux update` with a matching ETag performs no body download"* is **unmet as written** — CDP interception is at the **response** stage, so Chrome has already transferred the body; `validate()` saves the decode and the shard comparison, **not bandwidth**. Recorded as [ADR-CDP-FETCHER](../docs/adr/0020_cdp-fetcher.md) decision 12 rather than quietly satisfied | 2026-09-01 | 0d |
| **Whether the W-83 shape gets a gate.** A key was accepted in a record, assigned in the ownership table, and **never implemented** — every mechanical check passed, because the freshness gate proves a record was *touched*, never that it is *true*. That is the **second** recorded occurrence, which is what CLAUDE.md's two-strikes rule makes a trigger. ⚠ **No check was written**: "the record is true" is not mechanically definable, and shipping a loose approximation is the moving-threshold failure in another costume | 2026-09-01 | 0d |
| **`superseded_weight`** — W-94 below. Doing nothing is legitimate | 2026-08-28 | 4d |
| **`rerank_weight`** — the no-op pattern, under *adr update*. Doing nothing is legitimate | 2026-08-28 | 4d |
| **Whether zero abstentions out of 20 gates anything** — under *adr update* | 2026-08-28 | 4d |
| **Ratify the headroom obligation** into [ADR-RS](../docs/adr/0036_predictions.md) — under *adr update* | 2026-08-28 | 4d |
| **The 7 `partial` goldens** — needs a human or a third blind reader; under *testing* | 2026-08-28 | 4d |
| **W-87 — what "good" means**, Part B blocked on a corpus that was wiped | 2026-08-27 | 5d |

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

## Open items

### fux build

- 🔴 **W-94** · `arpit` · *(record: [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) ·
  [ADR-TUNE](../docs/adr/0038_tuning.md))* · **`superseded_weight` ships at
  `1.0`, so the supersession prior is a no-op out of the box.** Measured
  [2026-08-28](regression/2026-08-28-benchmark-v1-vs-head/VERDICT-B2.md):
  `1.0.0` and `HEAD` invert a superseded document over its successor
  **identically** — 21 of 40 chains at tier 1 000 — because `HEAD` parses
  `supersedes:`, builds the edge, resolves the flag onto the retired document,
  and then multiplies its score by one. **Post-hoc at `0.5`: 21/40 → 0/40.**
  **The machinery works and is switched off.**
  🔴 **This does NOT mean "lower the default", and the run says so itself.**
  [`P-SUPERSEDE`](regression/2026-08-25-supersession-and-reranker-default/VERDICT.md)
  ruled that change **FAIL** on 2026-08-25 — at `0.5` on the playground it fixed
  **`q015` and `q049`** and **broke `q022` and `q033`**, and *every* broken query
  had the **superseded document as its correct answer**. (⚠ This row and the
  v1-vs-HEAD presentation both said *"fixed one query"* until 2026-08-28; the
  [verdict](regression/2026-08-25-supersession-and-reranker-default/VERDICT.md)
  is primary and says two. The ruling is unaffected — the bar was *0 broken*.) **The benchmark corpus cannot see that
  failure mode by construction.** The two results are consistent and **the older
  one is more informative**, because its corpus contains the case that breaks.
  **What is actually open is narrower:** a corpus declaring `supersedes:` gets
  nothing and **is told nothing** — `fux doctor` could disclose that, which is
  not a ranking change. ⚠ **Doing nothing is legitimate**: a disclosure gap, not
  a defect. `filed: 2026-08-28`

### testing

- 🔴 **W-101 — the `fux doctor` pass, and it now carries FOUR things** ·
  `agent` · *(records: [ADR-TYPES](../docs/adr/0031_types-list.md) decision 11
  veto 4 · [ADR-ACQUIRED](../docs/adr/0050_acquired-plane.md) ·
  [ADR-URL-FRESHNESS](../docs/adr/0052_url-freshness.md) ·
  [ADR-REFUSAL](../docs/adr/0051_refusals.md) ·
  [ADR-PII](../docs/adr/0053_pii.md))* · **One pass at `doctor.py` closes all
  four; they are grouped because splitting them means four passes at one file.**

  1. 🔴 **The `as-ingested` share is the VETO CHECK for two accepted records**
     ([ADR-ACQUIRED](../docs/adr/0050_acquired-plane.md),
     [ADR-URL-FRESHNESS](../docs/adr/0052_url-freshness.md)) — **until `doctor`
     reports it, neither veto can be run at all.** That is the one with damage
     that accrues: every day more code ships under two records nobody can check.
  2. **Decoder bindings are not resolved.** A types file naming a decoder that
     was deleted, or one whose `EXTENSIONS` moved, is discovered only on the
     next `fux ingest`. ⚠ Since decision 11a there is a **third** thing only
     `doctor` can catch: a binding on an extension **no file in the corpus
     has** — what a typo in the *extending* direction looks like. Deliberately
     not an ingest error; a report is the right weight (*"3 bindings match no
     document"*).
  3. **No refusal rule counts.** An over-broad rule is visible only in a run's
     output, so a rule that silently refuses the whole corpus looks like a
     corpus with nothing in it.
  4. **No redaction counts.** They already exist in `redact()`'s return value
     and are simply not surfaced.

  ⚠ **What `doctor` structurally CANNOT see, and no amount of this item fixes:**
  a well-formed PII rule that is too broad removes real vocabulary, documents
  stop being findable, and nothing looks wrong.
  [`tools/pii-probe/`](../tools/pii-probe/README.md) is the only instrument for
  that. `filed: 2026-09-01`

- 🔴 **`.fux/enrich/` is committed and unredacted** · `agent` ·
  *(records: [ADR-PII](../docs/adr/0053_pii.md) decision 1 ·
  [ADR-ENRICH](../docs/adr/0040_enrich.md) decision 11)* · **A real hole in the
  rule ADR-PII states, not a nice-to-have.** A model handed a document writes
  enrichment prose into a **committed** file; decision 1 says that file should
  be redacted and it is not. The matcher already exists and
  `fux enrich --check` is where it belongs. ⚠ It is written into **both**
  records now, so no reading of decision 1 can be taken to say the surface is
  covered. `filed: 2026-09-01`

- **W-97** · `agent` · *(record: [ADR-TUNE](../docs/adr/0038_tuning.md) ·
  [ADR-RS](../docs/adr/0036_predictions.md))* · **the knob sweep — which
  `.fux/tune.toml` defaults are defensible, measured rather than argued.**
  Pre-registered as [`benchmark/PRE-REGISTRATION-TUNER.md`](benchmark/PRE-REGISTRATION-TUNER.md)
  (ids **T0–T5**, a third id space), procedure in
  [`benchmark/RUNBOOK-TUNER.md`](benchmark/RUNBOOK-TUNER.md). Three legs per
  knob — the generated suite **selects**, the hand-graded playground **vetoes**
  (bar: 0 broken; `q022`/`q033` named in advance for `superseded_weight`), a
  latency fence **prices**. Output is a **candidate table with no
  recommendation**; the change stays an ADR-TUNE amendment Arpit ratifies, and
  W-94's *"doing nothing is legitimate"* is untouched. Scope is `rerank_weight`
  and `superseded_weight` only — `k1`/`b`, field weights and recency have no
  instrument with headroom (§6 lists the generator kinds owed). Blocked on the
  playground emitting per-query rows and a `--tune` switch in `bench.py`. —
  [detail](open/W-97-tuner-knob-sweep.md) `filed: 2026-08-28`

- ⚠ **`separation_floor` is repo-configurable and R10 is still unmeasured.**
  *(record: [ADR-CONFIDENCE](../docs/adr/0045_confidence.md))* · Not a new
  item — R10 is [W-90]'s — but the failure mode is: a repo can make its own
  answers read `grounded` without touching the ranking, and **nothing
  mechanical catches it**. The guard is that the block publishes the floor it
  was judged under. **Any run comparing two arms must assert their floors are
  equal**; differing floors is a pre-registered threshold moving inside a
  comparison, and it is ADR-CONFIDENCE decision 13's reopen trigger.

- **Recall on a CLEAN corpus.** `agent` ·
  *(record: [ADR-QUALITY](../docs/adr/0044_quality-contract.md))* · The first
  `recall@k` ([run](regression/2026-08-28-first-recall/report.md), `@5` 0.9535)
  is `informed` — every installed enrichment file was authored by someone who
  had read these queries — so **it demonstrates the metric, not the engine.**
  The `none`/`placebo`/`real` arms already exist, so a clean absolute is one
  command. ⚠ Unlike `hit@k`, recall awards partial credit and **may separate
  arms `hit@k` could not**; that makes it a paired comparison needing discordant
  counts. `filed: 2026-08-28`

- **The 7 `partial` goldens.** `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0044_quality-contract.md))* · The two
  blind annotators' exact-set disagreements, taking the union, held out of
  `recall@k`'s denominator. They need a human or a **third blind reader** —
  any session that has seen the scores is the wrong party. 🔴 **Do not resolve
  them by picking whichever set makes recall look better.** `filed: 2026-08-28`

- **The `heading` negative control is saturated and must be rebuilt.** `agent` ·
  *(record: [ADR-RS](../docs/adr/0036_predictions.md))* ·
  [C4](regression/2026-08-28-benchmark-contested/VERDICT-C4.md) returned its
  predicted null at **100 % in both arms with zero headroom**, so it returned
  the right answer for the wrong reason and **did not discharge its job**. Until
  it does, C1 and C3 rest on generator assertions rather than a live control.
  The fix is a control with headroom by construction — e.g. distractors that are
  *also* heading-matched. `filed: 2026-08-28`

- ⚠ **A cross-seed "null control" is not a determinism check, and B9 was read as
  one.** `agent` · *(record: [ADR-RS](../docs/adr/0036_predictions.md))* ·
  Query ids are **positional**, so arm A on seed 12 paired against arm A on
  seed 13 compares *different questions*; the discordant count is a rate
  check. The determinism check is the **same-corpus repeat**.
  [C5](regression/2026-08-28-benchmark-contested/VERDICT-C5.md) was ruled on the
  repeat for that reason. 🔴 **The 2026-08-28 v1-vs-HEAD run's B9 carries the
  same weakness** — its "0 discordant of 240" across two seeds should be read as
  a rate check; its "300/300 identical rows on one corpus" is the half that does
  the work. `filed: 2026-08-28`

- **W-96** · `agent` · *(record: [ADR-RS](../docs/adr/0036_predictions.md))* ·
  **a `blind` version benchmark needs TWO sessions, and nothing makes that
  happen.** Whoever writes the generator and reads a score is `informed`, so
  the 2026-08-28 run is filed `informed` and states no delta. The protocol:
  one session authors and freezes the corpus, query sets and harness and
  **stops**; a second, which never reads them, executes and analyses.
  ⚠ **Not a process doc** — a handoff shape, worth one paragraph in
  SETUP-BENCHMARK plus the discipline to do it. `filed: 2026-08-28`

- **W-87** · `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0044_quality-contract.md))* · **what
  "good" means, then measure.** P0, P1, P3, P4 and P5 are closed and
  `recall@k` now exists. ⚠ **Two things keep it open:** the `judged` series
  has never been exercised (no judged run exists), and **Part B cannot run**
  — `acme` and `orbit` went in the 2026-08-20 wipe with their generator, and
  `tools/pruning-eval/` hard-codes reading them. —
  [detail](open/W-87-what-good-means.md)

- **`tests_e2e/` has never run on Windows**, and `test_maintenance.py` is the
  suite most likely to differ: real git, real hooks, real detached processes.
  *(no record — a test-surface gap, not a behaviour change)* · Verified on
  Linux/CPython 3.11.15 and macOS 15/arm64/CPython 3.14.2.

- ⚠ **`validate()` reaches an existing repo only when somebody copies the
  fetcher in.** *(record: [ADR-DOTFUX](../docs/adr/0003_fux-directory.md)
  decision 6)* · `fux setup` is write-if-missing and never rewrites a
  consumer's file. **Measured 2026-08-28:** a repo created before the change
  learned **0 of 7** tokens until its `http.py` was replaced by hand. A
  `doctor` notice now names the gap, so it is **VISIBLE, not CLOSED** — the
  consumer still copies the function in by hand. **No further mechanism is
  proposed**: a loader that rewrote a consumer's committed file would be
  worse than the problem.

### adr update

- **`rerank_weight` ships at `0.0`, and every ranking prior `HEAD` added is a
  no-op at the default.** `arpit` ·
  *(record: [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) ·
  [ADR-TUNE](../docs/adr/0038_tuning.md))* · Not a new fact —
  [2026-08-25](regression/2026-08-25-supersession-and-reranker-default/report.md)
  measured the reranker and recorded that *"the default still does not flip"*,
  and `P-RERANK-DEFAULT` was withdrawn as mis-framed. **What is new is the
  pattern**: `superseded_weight` `1.0`, `recency_half_life_days` `0.0` and
  `rerank_weight` `0.0` are all no-ops, so **on ranking priors B-core *is*
  `1.0.0`** — which explains the shipped-default nulls better than a saturated
  corpus alone did. Measured on a headroom-asserted suite
  ([C2](regression/2026-08-28-benchmark-contested/VERDICT-C2.md)): at `0.5` the
  reranker takes proximity contests **22 % → 100 %, 94 fixed, 0 broken**.
  🔴 **This is NOT an argument for the default, and the pre-registration said so
  before the number existed.** That suite rewards exactly what the reranker
  does; on **hand-graded** text the reranker is worth `28 → 32` — **+4, 0
  broken**, itself `informed` and below the floor. `c = 0` is a property of the
  generator, not a safety result. ⚠ **Doing nothing is legitimate** — the open
  work is recording this pattern where ADR-RANKING/ADR-RERANK can be checked
  against it, not building or measuring anything further. `filed: 2026-08-28`

- 🔴 **The engine abstains ZERO times out of 20.** `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0044_quality-contract.md))* ·
  Blind-authored `unanswerable` questions, confirmed unanswerable by a second
  blind session; the engine reported `answerable: true` on all 20, 17 of them
  at or above the `separation_floor`
  ([run](regression/2026-08-28-blind-unanswerable/report.md)). **This is
  load-bearing**: ADR-QUALITY decision 5 puts the class *inside* the gate, so
  the `recall@k` headline describes the **answerable half only**.
  ⚠ **No threshold is proposed and R10 is untouched, deliberately** — a floor
  fitted to the 20 numbers that exposed the problem is the moving-threshold
  failure in a new costume. **Needs a call on whether it gates anything.**
  `filed: 2026-08-28`

- **Ratify the headroom obligation into [ADR-RS](../docs/adr/0036_predictions.md).**
  `arpit` · *(record: [ADR-RS](../docs/adr/0036_predictions.md))* · **W-95 is
  built, run and filed**
  ([2026-08-28](regression/2026-08-28-benchmark-contested/report.md)): a
  contested-answer suite whose `--selftest` **asserts** that candidates are
  separable only by the property under test. On its primary endpoint, with
  **94 of 120 queries of headroom**, shipped-default `HEAD` and `1.0.0` are
  **both at 21.7 %** against a 25 % chance level — 0 discordant. 🔴 **The
  reusable rule, which is what W-95's row was the only home of: a power table
  says how many queries; it NEVER says whether the queries are HARD.** The
  proposed standing obligation — *every paired run states, for each endpoint,
  the current score and how many queries could change, beside the power figure*
  — is a **decision**, so it needs ratifying rather than filing. It earned its
  place immediately: it caught a saturated control inside the run that
  introduced it. `filed: 2026-08-28`

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
8. **Grouped by what closing it takes — `fux build` (code), `testing`
   (a run or a harness), `adr update` (a ruling or a record, no code and no
   measurement) — changed 2026-08-29 from grouping by record, on Arpit's
   direction.** Law zero is unchanged and still binds every item: each row
   still names, inline, the record its change will have to update — if you
   cannot name one, say **"no ADR affected"** out loud. What moved is only the
   sort key, not the obligation.

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
