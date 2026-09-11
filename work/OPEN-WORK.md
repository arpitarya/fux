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

*Named here so a session leads with it instead of burying it. **Ages are
recomputed against the reading date, never copied** — a queue that copies its
ages stops flagging its own oldest item. As of **2026-09-11, two rows are past
CLAUDE.md's 5-day threshold**, and a session names each, with its age, in its
first output.*

🟢 **Rulings with their evidence are in
[`proposals/unblock-2026-09-05.md`](proposals/unblock-2026-09-05.md)** (`R-1`…`R-11`),
with a paste-ready Opus prompt beside each. Arpit strikes or accepts a line;
the row then closes through that prompt.

🔴 **Rule 4 has fired five times in twelve days — re-derive before believing a
row here, and start with any row whose blocker is an ENVIRONMENT.** On
2026-09-11 four rows said *hands*, *`device_bash` is wedged*, *no session can
run the suite* — and the first session with a shell closed all four in an hour.
`_to_delete/` did not exist. `ruff` was named as an unrun gate by two rows and
is in neither `[dev]` nor CI. **That is the third time this section has been
wrong about a machine** (2026-08-27, 2026-08-28, 2026-09-11), and it is the only
failure mode here with a perfect record.

⚠ **Two sessions wrote this tree at once on 2026-09-06 and again on
2026-09-11.** Diff before believing your own copy is current.

| what he decides | filed | age |
|---|---|---|
| 🔴 **Does the abstention result gate anything?** **Re-run done, and the answer is the same: 20 of 20 `answerable: true`, 0 ids flipped** — fourteen days and five ranking changes later ([the run](regression/2026-09-11-blind-unanswerable-rerun/report.md)). Band, separation and the `separation_floor` are each **demonstrated not to be the lever**. No threshold is proposed and R10 stays unmeasured — picking a floor from these 20 fits it to the set that exposed the problem | 2026-08-28 | 14d |
| 🔴 **The four no-op priors — pick an instrument, or close the knob.** The remeasure you ordered **cannot run**: three of the four priors move **0 of 50** goldens at every value including `0.0`, because the playground declares no `supersedes:` key on any branch of its history ([the run](regression/2026-09-11-four-priors-headroom/report.md)). **(a)** declare it (one frontmatter line — changes the committed index and every number filed against it), **(b)** build a purpose-made corpus, or **(c)** close the knob on the structural argument, which needs no corpus | 2026-09-11 | 0d |
| **W-136 phase 1 — run prompt 1 in Codex.** Codex writes the 10 seed documents into `work/golden/seed/` and the ~100 questions with answers into `work/golden/golden-answer/answers.jsonl` (Claude never reads it). Prompt: [`golden/prompts/1-codex-seed.md`](golden/prompts/1-codex-seed.md) · process: [`golden/README.md`](golden/README.md) | 2026-09-11 | 0d |
| **W-87 Part B — accept R-11?** Retarget Part B at the two corpora that exist — the repaired `fux-playground` (10 docs, 50 goldens) and `fux-benchmark` `t10000` — and retire the dependency on `acme`/`orbit`, which were wiped with their generator. Proposal: [`proposals/unblock-2026-09-05.md`](proposals/unblock-2026-09-05.md) R-11 | 2026-08-27 | 15d |

---

## Open items

### fux build

- 🔴 **W-122 — the remainder of L0: the generated `CLAUDE.md` block, the config
  consolidation, and the gate.** `agent` · *(records: ADR-LAW-0 · ADR-LAWS ·
  ADR-CONFIG · ADR-TUNE · ADR-OWNERSHIP)* · ✅ **L0 and the nine-record rename
  landed** (`5cf30bc`, `5912afb`). **Arpit ruled this
  2026-09-06**: a rule is stated in exactly one ADR and every other artifact
  links rather than restates; a record that conflicts with a Law is **void in
  the conflicting part**; a Law changes only on his ruling, named in the record.

  **What is actually left, re-derived 2026-09-11:**

  - **`CLAUDE.md`'s law section becomes generated and test-asserted.** It is
    still the normative home and the ruling says it stops being one. Until this
    lands, `CLAUDE.md` §Non-negotiable constraints and the nine records can
    disagree while both look correct — which is the exact restatement hazard
    L0 names.
  - 🔴 **The config consolidation has NOT happened.** `src/fux/config.schema.json`
    and `src/fux/derive/runtime.schema.json` both still exist (verified
    2026-09-11) and both were assessed documentation-only; the four
    runtime-loaded schemas stay, because they **enforce** rather than
    **describe**. ⚠ The phantom `[sources] types_file` key was one symptom of
    exactly this — a schema nothing parses drifts silently. **Removed 2026-09-11
    (W-130)**: the entry is gone and `load()` refuses the key by name.
  - **The gate R-2 asked for**: ADR-CONFIG's fenced key tree ↔ `config.py` as a
    parser, **both directions**, so *a key is real only if it is in the tree*.
    That is how `acquired_max_bytes` rotted in prose, and how `types_file`
    rotted until W-130 removed it.

  — [detail](open/W-122-adrs-are-the-source.md) `filed: 2026-09-06`

- 🟠 **Search v3 — seven items, RATIFIED by Arpit 2026-09-05; all seven now
  `agent`** · *(spec: [`proposals/search-v3.md`](proposals/search-v3.md) §8 ·
  one detail file each under [`open/`](open/README.md))* · **Opus** executes,
  in his stated order: ~~W-108~~ (**landed 2026-09-05** —
  [IMPLEMENTATION](IMPLEMENTATION.md), [the run](regression/2026-09-05-answer-top3/report.md)) →
  ~~W-107 Phase 0~~ + ~~W-106~~ (**both measured 2026-09-05** —
  [`node-log-divergence`](regression/2026-09-05-node-log-divergence/report.md),
  [`vector-gate`](regression/2026-09-05-vector-gate/report.md); **Phase 0 is
  CLOSED — Arpit ruled option (b) on 2026-09-06**, W-106 filed **without a
  verdict** on his ruling) →
  **W-107 Phases 1–4** → ~~W-109~~ (**landed 2026-09-05, gate 16-0** —
  [the run](regression/2026-09-05-expand/report.md)) → ~~W-110~~ (**built
  2026-09-05; its gate is AMBIGUOUS and in the inbox above** —
  [the run](regression/2026-09-05-doc2query/report.md)) → ~~W-111~~ (**landed
  2026-09-05** — [the run](regression/2026-09-05-declared-ties/report.md)) →
  **W-112**. ✅ **W-107 Phases 1–4 are UNBLOCKED**: the last unstruck decision
  in the ratification — Phase 0's `log()` choice — was ruled **(b), equal after
  `round(9)`**, on 2026-09-06, and the pre-registration is frozen in full
  (sha `0e3b4c8`). 🔴 **W-112 alone is still on Arpit**: a corpus and a compare
  doc. `filed: 2026-09-04` · `ratified: 2026-09-05`
  - **[W-106](open/W-106-vector-gate.md)** · `agent` · *(no record — a run)* · **MEASURED 2026-09-05, and NO VERDICT FILED** ([the run](regression/2026-09-05-vector-gate/report.md)) — Arpit's ruling, because **DENSE-CHUNK's frozen bar cannot be tested**: the playground's index was `fux.index.v1` (unreadable by this engine) and it has **no enrichment**, so *today's ask* is **28/50** against that control's **32/50**. Retrieval: both correctly-configured arms net **zero** (6/6 and 5/5 fixed/broken) and each moves **1 of 9** vocabulary-gap failures. 🔴 **The finding is reproducibility**: two implementations of one model agree to **cosine 0.9964** and share **0 of 125** int8 vectors, 41/50 top-5 orderings discordant. ⚠ **The DoD's `pooling: mean` is wrong for BGE** and the misconfigured arm scored best. **Still owed: the two-architecture arm** (arm64 only here) and a corpus.
  - **[W-107](open/W-107-node-read-plane.md)** · `agent` · *(**ADR-NODE-SEARCH** new · ADR-RANKING · ADR-MCP)* · the Node read plane — `npx fux-search ask|find|answer|explain|graph|path|mcp`, zero deps, one contract, a third arm of the differential law. **Phase 0 is CLOSED** ([the run](regression/2026-09-05-node-log-divergence/report.md) + [`ADDENDUM-IDF`](regression/2026-09-05-node-log-divergence/ADDENDUM-IDF.md) + [`ADDENDUM-GLIBC`](regression/2026-09-05-node-log-divergence/ADDENDUM-GLIBC.md)). Arpit ruled **(b) — scores equal after `round(9)`, ordering byte-equal** on 2026-09-06; [`PRE-REGISTRATION-NODE.md`](benchmark/PRE-REGISTRATION-NODE.md) is **frozen in full**, sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`, and the rule now lives in [ADR-RANKING decision 8a](../docs/adr/0021_ranking.md). ▶ **Phase 1 starts.** ⚠ The glibc number came from a Linux container, not from [`log-probe.yml`](../.github/workflows/log-probe.yml), which is **still unrun**; musl, Windows and Node 20 stay unmeasured and §4 still requires all three OSes before an arm is called green.
  - **[W-112](open/W-112-vector-plane.md)** · `arpit` · *(**ADR-VECTORS** new · ADR-DOTFUX · ADR-INGEST · ADR-ASK · ADR-PROVENANCE)* · the vector plane — `fux embed`, pinned `.fux/vectors/`, `--qvec`, rank-space fusion; fux never computes a vector. 🔴 **STILL BLOCKED, and the blocker changed shape.** W-106 produced no PASS to unblock it, and it produced something the plane's design has to answer: **a pinned committed vector is an artefact of one implementation** — two correct implementations of one model share **0 of 125** int8 vectors ([the run](regression/2026-09-05-vector-gate/report.md)). The determinism claim can only ever be *"same clone + same embedder build"*, never *"same model"*. **Blocked on: a restored corpus (W-87 Part B), a re-run gate, and the compare doc Arpit must rule on.**

### testing

- 🟠 **W-136 — the sealed golden benchmark.** `arpit` (Codex phases), then `agent` ·
  *(records: [ADR-RS](../docs/adr/0043_predictions.md) · [ADR-QUALITY](../docs/adr/0051_quality-contract.md) ·
  setup: [fux-benchmark](setup/fux-benchmark.md), [fux-lab](setup/fux-lab.md))* · **Arpit, 2026-09-11.**
  Codex writes 10 seed documents and ~100 questions with answers in
  `work/golden/golden-answer/` — **Claude never reads it**. Claude grows the corpus
  **10 → 10 000** without seeing a question; Codex freezes it and releases questions
  only; Claude runs fux per rung; Codex scores and returns per-query results with no
  answers. One test set for fux-benchmark and fux-lab. Process:
  [`golden/README.md`](golden/README.md) — [detail](open/W-136-golden-benchmark.md)
  `filed: 2026-09-11`

- 🔴 **W-116** · `agent` · *(record: [ADR-RS](../docs/adr/0043_predictions.md))* ·
  **W-115 re-ranked the corpus and NOTHING was measured.** Two populations
  moved: every document containing a fenced code block (the fence fix — in this
  repo, most of them), and every document of the formats whose decoder gained a
  heading skeleton or a depth cap. Arpit ruled on 2026-09-06 that these land as
  **defect fixes** rather than wait on a measurement — a `# comment` in a bash
  block was never a heading — and that ruling is recorded in all three ADRs.
  ⚠ **What it does not do is make them measured**, and no doc may cite them as
  such. ✅ **UNBLOCKED 2026-09-11 — both stated blockers are gone.** `fux-lab` was
  never missing (W-56 rebuilt it 2026-08-20), and the playground now has a current
  index and a `check.py --rows` writer (W-134, playground `fece5a3`). **Nothing
  is waiting: this is a paired before/after run someone can start.**
  ⚠ **Report it under [ADR-RS](../docs/adr/0043_predictions.md) decision 22** —
  per endpoint, per direction, observed/proven/unproven. 🔴 **Compute the headroom
  FIRST**: the 2026-09-11 four-priors probe found three of four ranking priors
  move 0 of 50 goldens on this corpus, so *"this corpus can see the change"* is
  a thing to establish rather than assume. The arms are two engine builds, so the
  index must be rebuilt under each — the fence fix changes extraction.
  `filed: 2026-09-06`

- **W-97** · `agent` · *(record: [ADR-TUNE](../docs/adr/0045_tuning.md) ·
  [ADR-RS](../docs/adr/0043_predictions.md))* · **the knob sweep — which
  `.fux/tune.toml` defaults are defensible, measured rather than argued.**
  Pre-registered as [`benchmark/PRE-REGISTRATION-TUNER.md`](benchmark/PRE-REGISTRATION-TUNER.md)
  (ids **T0–T5**, a third id space), procedure in
  [`benchmark/RUNBOOK-TUNER.md`](benchmark/RUNBOOK-TUNER.md). Three legs per
  knob — the generated suite **selects**, the hand-graded playground **vetoes**
  (bar: 0 broken; `q022`/`q033` named in advance for `superseded_weight`), a
  latency fence **prices**. Output is a **candidate table with no
  recommendation**; the change stays an ADR-TUNE amendment Arpit ratifies, and
  the four-priors item's *"remeasure first"* ruling is untouched. ⚠ **A THIRD knob joined on 2026-09-05**: `expand_weight`, shipped at `0.2` (Query2doc's 1:5) and **untested by [W-109's gate](regression/2026-09-05-expand/report.md)**, which ran every arm at that one value. It is the first knob this sweep has a corpus that can actually see move — 16 goldens changed state under it. ⚠ **And `rerank_weight` now moves TWO mechanisms**, not one: since W-108 it also scales the refer plane's passage proximity, which the sweep's design assumed it did not. **Re-derived in code and written into T1 on 2026-09-05 as a stated limit** — T1.a/T1.c read `ask` rows and do not fetch, so **T1.d's veto is the exposed leg**; the bar is unchanged and the verdict now owes the sentence. Scope is `rerank_weight`
  and `superseded_weight` only — `k1`/`b`, field weights and recency have no
  instrument with headroom (§6 lists the generator kinds owed).
  ✅ **One of the two blockers is CLEARED: `bench.py quality --tune TABLE.KEY=VALUE`
  landed 2026-09-05** — written before the warm-up, refusing to score if the
  committed index moved (T0.b enforced per pass rather than checked after),
  omission deleting `tune.toml` rather than writing an empty one, and every row
  carrying `tune` + `index_sha` so a pairing asserts a shared index **from the
  rows**. Smoke-run on `t100`, rows deleted: **no number from it is a result.**
  ⚠ **`expand_weight` is now in §1's defaults table and §6's out-of-scope
  table** — it was in neither, and §1 claims to be read from source. It cannot
  join this sweep: **no suite here passes `--expand`**, so no query can move it.
  ✅ **The per-query rows blocker is CLEARED** — W-134 landed 2026-09-11
  (playground `fece5a3`, `check.py --rows`). 🔴 **But T2's veto leg is blocked by
  something else, found the same day**: `superseded_weight` moves **0 of 50**
  goldens at every value on that corpus, because it declares no `supersedes:`
  key ([the run](regression/2026-09-11-four-priors-headroom/report.md)). **The
  named veto queries `q022`/`q033` cannot be broken by a knob that reaches
  neither.** T2 waits on the same instrument decision as the four-priors item
  above. **T1 (`rerank_weight`) is unaffected** — it has 13/37 proven headroom
  on this corpus and is runnable now. —
  [detail](open/W-97-tuner-knob-sweep.md) `filed: 2026-08-28`

- **The `heading` negative control is saturated and must be rebuilt.** `agent` ·
  *(record: [ADR-RS](../docs/adr/0043_predictions.md))* ·
  [C4](regression/2026-08-28-benchmark-contested/VERDICT-C4.md) returned its
  predicted null at **100 % in both arms with zero headroom**, so it returned
  the right answer for the wrong reason and **did not discharge its job**. Until
  it does, C1 and C3 rest on generator assertions rather than a live control.
  The fix is a control with headroom by construction — e.g. distractors that are
  *also* heading-matched. `filed: 2026-08-28`

- **W-87** · `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0051_quality-contract.md))* · **what
  "good" means, then measure.** P0, P1, P3, P4 and P5 are closed and
  `recall@k` now exists. ⚠ **Two things keep it open:** the `judged` series
  has never been exercised (no judged run exists), and **Part B cannot run**
  — `acme` and `orbit` went in the 2026-08-20 wipe with their generator, and
  `tools/pruning-eval/` hard-codes reading them. **Part B is Arpit's ruling on
  R-11** (inbox); the `judged` series is agent work once W-134 lands. —
  [detail](open/W-87-what-good-means.md)

### adr update

- 🟠 **THE FOUR NO-OP RANKING PRIORS — one problem, one blocker.** `agent`, then `arpit` ·
  *(records: [ADR-CONFIDENCE](../docs/adr/0052_confidence.md) ·
  [ADR-TUNE](../docs/adr/0045_tuning.md) ·
  [ADR-ARCHIVED-CONTENT](../docs/adr/0044_archived-content.md) ·
  [ADR-RS](../docs/adr/0043_predictions.md))* · ⚠ **Merged 2026-09-11 from FOUR
  rows — two inbox lines, W-94, and this one** — which between them said the
  same thing about one decision blocked on one action. `filed: 2026-08-28` ·
  `ruled: 2026-09-11`

  | knob | ships at | what it would act on |
  |---|---|---|
  | `archived_weight` | `1.0` | a source line declaring `archived=true` |
  | `superseded_weight` | `1.0` | a document another declares `supersedes:` |
  | `rerank_weight` | `0.0` | passage proximity, and since W-108 the refer plane's rescore too |
  | `recency_half_life_days` | `0.0` | a committed `mtime` |

  **Each is built, wired, reads its input, and multiplies by one.** So on
  ranking priors, `HEAD` **is** `1.0.0` — which explains the shipped-default
  nulls better than a saturated corpus did.

  ✅ **The disclosure half SHIPPED 2026-09-11.** `fux doctor`'s `ranking priors`
  row names every dead prior *and the count of documents it would have acted
  on*: **391 of this repo's own documents declare `archived=true`**. It refuses
  to recommend a value, test-bound.

  🟠 **Arpit ruled 2026-09-11: REMEASURE, then decide** — not ship, not close.
  **Lane: `agent` for the remeasure, then back to Arpit with the result.**

  🔴 **The remeasure's question is NOT *"which value?"***. `P-SUPERSEDE` did not
  fail because `0.5` was wrong: at `0.5` it fixed `q015`/`q049` and **broke
  `q022`/`q033`**, and *every* broken query had the **superseded document as its
  correct answer**. Supersession belongs to the **query's intent**, not to the
  document — *"what do we do now?"* and *"what did we do before?"* want opposite
  rankings from one corpus, and a per-document multiplier cannot express that.
  **So the pre-registered question is: does ANY single global value clear a
  `0 broken` bar?** ⚠ **A run answering NO is a success** and is the likelier
  answer — it would close the knob permanently and move the work query-side. A
  run designed only to find a good value cannot report that.

  🔴 **THE REMEASURE CANNOT RUN, AND THAT IS MEASURED — 2026-09-11.** The
  precondition check ran before it
  ([the run](regression/2026-09-11-four-priors-headroom/report.md)) and found
  **three of the four priors move 0 of 50 goldens at every value including
  `0.0`**: `superseded_weight`, `archived_weight` and `recency_half_life_days`
  all have **zero headroom on the hand-graded corpus.** `adr-0019` says
  *"Supersedes ADR-0007"* in **prose** and declares no `supersedes:` key —
  `git log -S "supersedes:"` is empty on **every branch of the playground's whole
  history**. So the pre-registered question is met **vacuously** at every value.
  ⚠ Caught by ADR-RS decision 22d hours after it was ratified; without it this
  files as a clean pass. ⚠ **The 2026-08-25 run's corpus is not recoverable** —
  it stands as measured and can be neither reproduced nor contradicted.
  ✅ `rerank_weight` is the one prior with headroom; net `+4` at `1.0`, 0 broken,
  **below the floor**, so the hold stands unchanged.

  🔴 **BACK TO ARPIT — the instrument needs a decision, and it is his:**
  **(a)** declare the supersession the corpus already states in prose (one
  frontmatter line; **changes the committed index and every golden number filed
  against it**), **(b)** build a purpose-made corpus with declared supersession
  and a query set split by intent, or **(c)** close the knob on the structural
  argument, which needs no corpus at all. The item's own text says a NO is a
  success; this is not a NO, it is *cannot ask*.

  **What the remeasure needs, none of which exists today:**

  - 🔴 **The hand-graded playground, indexed, with per-query rows** — the only
    corpus with queries whose correct answer IS the retired document. The
    v1-vs-HEAD benchmark corpus **cannot see the failure mode by construction**.
    Repaired by Arpit's 2026-09-11 ruling; the index and the rows are
    W-134, which landed 2026-09-11 (playground `fece5a3`).
  - **A frozen pre-registration** naming its `k`, its arms and the `0 broken`
    bar *before* the first number ([ADR-QUALITY](../docs/adr/0051_quality-contract.md)
    decision 2a). ⚠ W-110's gate was VOIDED for exactly the omission this would
    repeat.
  - **The query set split by intent** — *current-seeking* against
    *history-seeking* — declared in the pre-registration. A set holding only the
    first kind will clear any bar and prove nothing.
  - ⚠ **Not runnable from Cowork**: that bridge is Linux/py3.10/no-egress and
    the `.venv` is macOS-built (verified 2026-09-11).

  ⚠ **`rerank_weight = 1.0` was asked for on 2026-09-11 and is HELD**, on a
  premise that does not hold — it was wanted *as a way to make the reranker
  depend on `archived=true`*, and the reranker is **proximity only**, with no
  concept of retirement. The flag already reaches ranking through
  `archived_weight`; wiring it into the reranker too would state one rule in two
  places (L0). On its own merits the knob has `+4` hand-graded, `informed`,
  **below the resolution floor** — the same evidential position as
  `superseded_weight`, so shipping one on argument while holding the other on
  measurement would not be a defensible pair. ⚠ **Its `22 % → 100 %, 94 fixed,
  0 broken`** ([C2](regression/2026-08-28-benchmark-contested/VERDICT-C2.md))
  is **not** an argument for the default and the pre-registration said so before
  the number existed: that suite rewards exactly what the reranker does, and
  `c = 0` is a property of the generator, not a safety result.


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
   [ADR-URL-INGEST](../docs/adr/0017_url-ingest.md) decision 9 first.
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
9. **No git housekeeping, ever** (Arpit, 2026-09-11). Nothing in this file
   says what is or is not committed, staged, pushed or unpushed — in this repo
   or any other. It is not work, it is stale the moment it is written, and
   `git status` already answers it. **If a repository's state blocks work,
   name what the work needs** (*"the playground indexes nothing"*), never its
   git status. A row asking whether to push is not a row.

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
