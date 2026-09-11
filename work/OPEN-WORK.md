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
ages stops flagging its own oldest item. As of **2026-09-11, one row is past
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
| 🔴 **Does the abstention result gate anything?** **Re-run done, and the answer is the same: 20 of 20 `answerable: true`, 0 ids flipped** — fourteen days and five ranking changes later ([the run](regression/2026-09-11-blind-unanswerable-rerun/report.md)). Band, separation and the `separation_floor` are each **demonstrated not to be the lever**. No threshold is proposed and R10 stays unmeasured — picking a floor from these 20 fits it to the set that exposed the problem. Under [L9](../docs/adr/0011_LAW-9-environments.md) any further abstention test runs in fux-lab on the golden set's `unanswerable` questions (W-136), never the playground | 2026-08-28 | 14d |
| 🔴 **The four no-op priors — pick an instrument, or close the knob.** The remeasure you ordered **cannot run**: three of the four priors move **0 of 50** goldens at every value including `0.0`, because the playground declares no `supersedes:` key on any branch of its history ([the run](regression/2026-09-11-four-priors-headroom/report.md)). **Two options left under [L9](../docs/adr/0011_LAW-9-environments.md)** (declaring it in the playground is void): **(b)** put declared supersession, `archived=true` sources, dated documents and intent-split questions into the golden test data (W-136) and remeasure in fux-lab, or **(c)** close the knob on the structural argument, which needs no corpus | 2026-09-11 | 0d |
| **W-136 phase 1 — did the answer key get written?** **The ten seed documents landed** (`work/golden/seed/`, committed 2026-09-11) — the half Claude can see. **The other half no Claude session can ever verify**: whether Codex wrote the ~100 questions and answers, and where. Say yes and **phase 2 is agent work, runnable at once**; say no and prompt 1 is re-run. Prompt: [`golden/prompts/1-codex-seed.md`](golden/prompts/1-codex-seed.md) · process: [`golden/README.md`](golden/README.md) | 2026-09-11 | 0d |

---

## Open items

### fux build

- 🔴 **W-138 — reconcile every artifact with L9.** `agent` · *(records: [ADR-LAW-9](../docs/adr/0011_LAW-9-environments.md) ·
  ADR-RS · ADR-QUALITY · ADR-ACCELERATOR · ADR-CONFIDENCE · ADR-ANSWER)* · **Arpit's L9,
  2026-09-11:** the playground is his hands only; the lab runs every measurement on
  golden test data ≤ 10 000; the benchmark only times queries and keeps ranked lists,
  current build vs previous major. ~40 docs, tools, tests and plans still use the
  playground as an instrument or mix the roles — rewrite them, and add a guard test
  that nothing under `src/ tools/ tests/ scripts/` reads the playground. —
  [detail](open/W-138-reconcile-with-l9.md) `filed: 2026-09-11`

- 🟠 **W-139 — build fux-benchmark to L9.** `agent`, after W-138 · *(record:
  [ADR-LAW-9](../docs/adr/0011_LAW-9-environments.md))* · seven corpus folders
  (100 → 10 000 docs of ~1 000 lines with tables, charts, bullets and Mermaid), a
  fixed query set, every run timing each query and keeping its ranked list across
  the current build and the newest `1.x`, diffed against the previous run. —
  [detail](open/W-139-benchmark-per-l9.md) `filed: 2026-09-11`

- 🔴 **W-122 — the remainder of L0: the generated `CLAUDE.md` block, the config
  consolidation, and the gate.** `agent` · *(records: ADR-LAW-0 · ADR-LAWS ·
  ADR-CONFIG · ADR-TUNE · ADR-OWNERSHIP)* · **Arpit ruled this 2026-09-06**: a
  rule is stated in exactly one ADR and every other artifact links rather than
  restates; a record that conflicts with a Law is **void in the conflicting
  part**; a Law changes only on his ruling, named in the record.

  **What is left, re-derived 2026-09-11:**

  - **`CLAUDE.md`'s law section becomes generated and test-asserted.** It is
    still the normative home and the ruling says it stops being one. Until this
    lands, `CLAUDE.md` §Non-negotiable constraints and the nine records can
    disagree while both look correct — which is the exact restatement hazard
    L0 names.
  - 🔴 **The config consolidation has NOT happened.** `src/fux/config.schema.json`
    and `src/fux/derive/runtime.schema.json` both still exist (verified
    2026-09-11) and both were assessed documentation-only; the four
    runtime-loaded schemas stay, because they **enforce** rather than
    **describe**. ⚠ A schema nothing parses drifts silently — which is how the
    phantom `[sources] types_file` key came to exist at all.
  - **The gate R-2 asked for**: ADR-CONFIG's fenced key tree ↔ `config.py` as a
    parser, **both directions**, so *a key is real only if it is in the tree*.
    That is how `acquired_max_bytes` rotted in prose, and how `types_file`
    rotted until W-130 removed it.

  — [detail](open/W-122-adrs-are-the-source.md) `filed: 2026-09-06`

- 🟠 **Search v3 — what is left of it: W-107 Phases 1–4, then W-112.** ·
  *(spec: [`proposals/search-v3.md`](proposals/search-v3.md) §8 · one detail
  file each under [`open/`](open/README.md))* · **Opus** executes, in Arpit's
  ratified order: **W-107 Phases 1–4** → **W-112**. `ratified: 2026-09-05`
  - **[W-107](open/W-107-node-read-plane.md)** · `agent` · *(**ADR-NODE-SEARCH** new · ADR-RANKING · ADR-MCP)* · the Node read plane — `npx fux-search ask|find|answer|explain|graph|path|mcp`, zero deps, one contract, a third arm of the differential law. ▶ **Phase 1 starts; nothing blocks it.** Phase 0's `log()` question is settled and the rule lives in [ADR-RANKING decision 8a](../docs/adr/0111_ranking.md) — scores equal after `round(9)`, ordering byte-equal; [`PRE-REGISTRATION-NODE.md`](benchmark/PRE-REGISTRATION-NODE.md) is frozen in full, sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`, and Phases 1–4 build against it. ⚠ **§4 still requires all three OSes before an arm is called green**, and only glibc/arm64 has been touched — [`log-probe.yml`](../.github/workflows/log-probe.yml) is **unrun**, so musl, Windows and Node 20 are unmeasured. ⚠ **[L9](../docs/adr/0011_LAW-9-environments.md): its frozen pre-registration names the playground** — the build (Phases 1–4) is unaffected, but any measured arm runs on fux-lab golden data under a superseding pre-registration ([W-138](open/W-138-reconcile-with-l9.md)). `filed: 2026-09-04`
  - **[W-106](open/W-106-vector-gate.md)** · `agent` · *(no record — a run)* · **the gate is measured and closed without a verdict** (Arpit's ruling — DENSE-CHUNK's frozen bar could not be tested: the playground's index was `fux.index.v1` and it carries no enrichment). 🔴 **What it found instead, and what W-112 has to answer: a pinned committed vector is an artefact of one implementation.** Two implementations of one model agree to **cosine 0.9964** and share **0 of 125** int8 vectors, with 41/50 top-5 orderings discordant ([the run](regression/2026-09-05-vector-gate/report.md)). ⚠ **The DoD's `pooling: mean` is wrong for BGE** and the misconfigured arm scored best. **Still owed: the two-architecture arm** (arm64 only so far) **and a corpus — under [L9](../docs/adr/0011_LAW-9-environments.md), fux-lab's golden test data (W-136).** `filed: 2026-09-04`
  - **[W-112](open/W-112-vector-plane.md)** · `arpit` · *(**ADR-VECTORS** new · ADR-DOTFUX · ADR-INGEST · ADR-ASK · ADR-PROVENANCE)* · the vector plane — `fux embed`, pinned `.fux/vectors/`, `--qvec`, rank-space fusion; fux never computes a vector. 🔴 **Blocked on three things:** a corpus — **under [L9](../docs/adr/0011_LAW-9-environments.md) the golden ladder in fux-lab (W-136)**, a re-run gate, and a compare doc Arpit rules on **once it is written** (not yet — nothing to decide today). ⚠ **The determinism claim the design can actually make is *"same clone + same embedder build"*, never *"same model"*** — W-106's `0 of 125` is why. `filed: 2026-09-04`

### testing

- 🟠 **W-136 — the sealed golden benchmark.** `arpit` (Codex phases), then `agent` ·
  *(records: [ADR-RS](../docs/adr/0133_predictions.md) · [ADR-QUALITY](../docs/adr/0141_quality-contract.md) ·
  setup: [fux-lab](setup/fux-lab.md))* · **Arpit, 2026-09-11.**
  Codex writes 10 seed documents and ~100 questions with answers in
  `work/golden/golden-answer/` — **Claude never reads it**. Claude grows the corpus
  **10 → 10 000** without seeing a question; Codex freezes it and releases questions
  only; Claude runs fux per rung; Codex scores and returns per-query results with no
  answers. The test data for fux-lab ([L9](../docs/adr/0011_LAW-9-environments.md)). Process:
  [`golden/README.md`](golden/README.md) — [detail](open/W-136-golden-benchmark.md)
  `filed: 2026-09-11`

- 🔴 **W-115 is STILL UNMEASURED FOR QUALITY, and now it is known why.** `agent`,
  **blocked on W-136** · *(records: [ADR-RS](../docs/adr/0133_predictions.md) ·
  [ADR-DECODE](../docs/adr/0139_decode.md))* · **The question has no instrument.**
  The corpus with goldens (**playground**) produces a **byte-identical index across
  the arms** — zero headroom, proven — and the corpus that can see the change
  (**fux's own repo**) has **no goldens**. So *"did ranking get better?"* cannot be
  asked today, and **no document may cite W-115 as measured.**
  ⚠ **Do not point this at the playground again** — that has been tried and it was
  wrong. **Ratified by [L9](../docs/adr/0011_LAW-9-environments.md): the instrument is [W-136](open/W-136-golden-benchmark.md)'s
  golden ladder in fux-lab** — the corpus decision is made, the corpus is not yet built.
  `filed: 2026-09-06` · `re-scoped: 2026-09-11`

- **W-97** · `agent`, blocked on W-136 · *(record: [ADR-TUNE](../docs/adr/0135_tuning.md) ·
  [ADR-RS](../docs/adr/0133_predictions.md))* · **the knob sweep — which
  `.fux/tune.toml` defaults are defensible, measured rather than argued.**
  Pre-registered as [`benchmark/PRE-REGISTRATION-TUNER.md`](benchmark/PRE-REGISTRATION-TUNER.md)
  (ids **T0–T5**, a third id space), procedure in
  [`benchmark/RUNBOOK-TUNER.md`](benchmark/RUNBOOK-TUNER.md). Three legs per
  knob — the generated suite **selects**, the hand-graded playground **vetoes**
  (bar: 0 broken; `q022`/`q033` named in advance for `superseded_weight`), a
  latency fence **prices**. Output is a **candidate table with no
  recommendation**; the change stays an ADR-TUNE amendment Arpit ratifies.
  Scope is `rerank_weight` and `superseded_weight` only — `k1`/`b`, field
  weights and recency have no instrument with headroom (§6 lists the generator
  kinds owed).

  🔴 **Under [L9](../docs/adr/0011_LAW-9-environments.md), nothing here is runnable today.** T1's 13/37 headroom was
  measured on the playground, which is no longer an instrument, and the generated
  selection suite is not golden test data. **Every leg moves to fux-lab golden data
  (W-136) under a new pre-registration that supersedes the frozen one** — the
  latency fence may run in fux-benchmark, which is its job. The tooling
  (`bench.py quality --tune`, per-query rows) carries over.

  🔴 **T2 (`superseded_weight`) cannot run**: the knob moves **0 of 50** goldens
  at every value on that corpus, because it declares no `supersedes:` key
  ([the run](regression/2026-09-11-four-priors-headroom/report.md)). **The named
  veto queries `q022`/`q033` cannot be broken by a knob that reaches neither.**
  T2 waits on the same decision as the four-priors item below — (b) or (c).

  ⚠ **`rerank_weight` moves TWO mechanisms, not one** — since W-108 it also
  scales the refer plane's passage proximity, which this sweep's design assumed
  it did not. T1.a/T1.c read `ask` rows and do not fetch, so **T1.d's veto is the
  exposed leg**; the bar is unchanged and the verdict owes that sentence.
  ⚠ **`expand_weight` ships at `0.2` (Query2doc's 1:5) and is untested** —
  [W-109's gate](regression/2026-09-05-expand/report.md) ran every arm at that one
  value. It is in §1's defaults table and §6's out-of-scope table, and **it cannot
  join this sweep: no suite here passes `--expand`**, so no query can move it. —
  — [detail](open/W-97-tuner-knob-sweep.md) `filed: 2026-08-28`

- **The `heading` negative control is saturated and must be rebuilt.** `agent`, blocked on W-136 ·
  *(record: [ADR-RS](../docs/adr/0133_predictions.md))* ·
  [C4](regression/2026-08-28-benchmark-contested/VERDICT-C4.md) returned its
  predicted null at **100 % in both arms with zero headroom**, so it returned
  the right answer for the wrong reason and **did not discharge its job**. Until
  it does, C1 and C3 rest on generator assertions rather than a live control.
  The fix is a control with headroom by construction — e.g. distractors that are
  *also* heading-matched. **Under [L9](../docs/adr/0011_LAW-9-environments.md) it is rebuilt inside the golden ladder**
  (heading-matched `sibling` documents in W-136 phase 2), not on a generated suite —
  agent work, blocked on W-136. `filed: 2026-08-28`

- **W-87** · `agent`, blocked on W-136 ·
  *(record: [ADR-QUALITY](../docs/adr/0141_quality-contract.md))* · **what
  "good" means, then measure.** ⚠ **Two things keep it open:**
  - **The `judged` series has never been exercised** — no judged run exists.
    ⚠ **Its input moves under L9** (2026-09-11): not the playground but fux-lab's
    golden test data — blocked on W-136.
  - 🔴 **Part B cannot run.** `acme` and `orbit` went in the 2026-08-20 wipe with
    their generator, and `tools/pruning-eval/` hard-codes reading them. **R-11's
    retarget at the playground is void under L9**; Part B runs in fux-lab on the
    golden ladder — agent work, blocked on W-136 (W-138 repoints the harness). —
  [detail](open/W-87-what-good-means.md) `filed: 2026-08-27`

### adr update

- 🟠 **THE FOUR NO-OP RANKING PRIORS — one problem, one blocker.** `agent`, then `arpit` ·
  *(records: [ADR-CONFIDENCE](../docs/adr/0142_confidence.md) ·
  [ADR-TUNE](../docs/adr/0135_tuning.md) ·
  [ADR-ARCHIVED-CONTENT](../docs/adr/0134_archived-content.md) ·
  [ADR-RS](../docs/adr/0133_predictions.md))* · `filed: 2026-08-28` ·
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

  🔴 **BACK TO ARPIT — two options left.** **(a)**, declaring the supersession in
  the playground, is **void under [L9](../docs/adr/0011_LAW-9-environments.md)**. **(b)** put declared supersession,
  `archived=true` sources, dated documents and a query set split by intent into the
  golden test data (W-136) and remeasure in fux-lab, or **(c)** close the knob on the
  structural argument, which needs no corpus at all. The item's own text says a NO is a
  success; this is not a NO, it is *cannot ask*.

  **What the remeasure still needs:**

  - **A frozen pre-registration** naming its `k`, its arms and the `0 broken`
    bar *before* the first number ([ADR-QUALITY](../docs/adr/0141_quality-contract.md)
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
