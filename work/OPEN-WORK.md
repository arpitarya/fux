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
recomputed against the reading date, never copied** — they were written on
2026-09-01 and read as `0d`/`4d`/`5d` until 2026-09-05, which is how a queue
stops flagging its own oldest item. As of **2026-09-05 six rows are past
CLAUDE.md's 5-day threshold** and a session names each, with its age, in its
first output.*

🟢 **Every row below has a proposed ruling, with its evidence, in
[`proposals/unblock-2026-09-05.md`](proposals/unblock-2026-09-05.md)** (`R-1`…`R-11`),
and a paste-ready Opus prompt beside it. Arpit strikes or accepts a line; the
row then closes through that prompt.

✅ **The two rows that document found stale are gone** (rule 4, re-derived
2026-09-05): `tests_e2e/` runs on `windows-latest` × py3.11/3.14 on every push
and was green on `80ee187`; the clean-corpus `recall@k` is the doc2query run's
`none` arm and its numbers now sit in
[ADR-QUALITY](../docs/adr/0044_quality-contract.md) beside the fitted ones.

| what he decides | filed | age |
|---|---|---|
| **Whether the W-83 shape gets a gate.** A key was accepted in a record, assigned in the ownership table, and **never implemented** — every mechanical check passed, because the freshness gate proves a record was *touched*, never that it is *true*. That is the **second** recorded occurrence, which is what CLAUDE.md's two-strikes rule makes a trigger. ⚠ **No check was written**: "the record is true" is not mechanically definable, and shipping a loose approximation is the moving-threshold failure in another costume | 2026-09-01 | 4d |
| 🟢 **W-107 Phase 0 — `log()`: the measurement is FILED and this is now a one-word answer.** [`2026-09-05-node-log-divergence`](regression/2026-09-05-node-log-divergence/report.md): `Math.log` vs `math.log` **do differ** — 655 / 100 000 on darwin/arm64, the same order as the glibc figure W-107 cites — but **every difference is one ulp** (max rel `2.211e-16`) and **none survives `round(9)`**, which is `rank.py`'s own sort-key resolution. Over the corpora: **0 discordant scores, 0 discordant top-5, on 197 233 scored documents at 10 and 10 000 documents.** **(a) portable `log`** buys bit-identity and costs a Python-wide ranking change plus a re-derivation of every golden; **(b) tolerance at `round(9)`** costs nothing and asserts the sort key's own resolution. ⚠ **Two limits were named; ONE IS NOW CLOSED and it moved the number.** [The addendum](regression/2026-09-05-node-log-divergence/ADDENDUM-IDF.md) re-probed on **this repo's own 838-document index**, 605 frequency-stratified queries: the `idf` population goes **13 → 182** and **14 of 182 (7.69 %) diverge**, with **8.98 % of real BM25F scores differing bit-for-bit**. 🔴 So the original *"0 discordant"* was an artifact of 13 arguments — **and it changes nothing about the pick**: max relative `5.463e-16`, **0 differ at `round(9)`, 0 top-5 orderings move**. The evidence for **(b)** is stronger than it was, not weaker. 🔴 **The remaining limit is the whole of what is left: glibc — what CI runs — is still NOT measured** (no Linux here). It is one `workflow_dispatch` away — [`.github/workflows/log-probe.yml`](../.github/workflows/log-probe.yml), added 2026-09-05, **not yet run**. [`PRE-REGISTRATION-NODE.md`](benchmark/PRE-REGISTRATION-NODE.md) is written with **this one cell blank**; **W-107 Phase 1 does not start until he fills it** | 2026-09-05 | 0d |
| 🔴 **W-110's gate: which `k`?** The bar was *`net >= 6` on `recall@k`* and **never fixed `k`**. [The run](regression/2026-09-05-doc2query/report.md) is **net +7 at `recall@1`** (7 up, 0 down) and +3 / +2 / +1 at `@3` / `@5` / `@10` — because `recall@10` is already `0.9884` without enrichment, so the effect is real and **concentrated at the top of the ranking**. **Choosing `k` after seeing the numbers is the moving-threshold failure, so this session did not.** ✅ The `placebo` control moved **nothing at any `k`**, so the gain is the questions' content. ⚠ The doc2query−− filter refused **2 of 98** questions and moved no recall number — **unproven, not disproven** | 2026-09-05 | 0d |
| ⚠ **Whether the prior enrichment measurements need re-running.** W-110 found that a newly written enrichment was **never indexed on an incremental ingest** (reuse was keyed on the document's sha alone) — shipped that way from W-76 Phase 8 to 2026-09-05. **Every enrichment measurement on record ran through it**, and whether any under-measured enrichment depends on whether its harness ingested from clean. [`2026-08-24-blind-enrichment-second-author`](regression/2026-08-24-blind-enrichment-second-author/ANALYSIS.md)'s `+1 / −1` is the one that matters, because it is what motivated replacing prose with questions. **Not audited; a re-run needs a corpus that no longer exists (W-87 Part B)** | 2026-09-05 | 0d |
| **`superseded_weight`** — W-94 below. Doing nothing is legitimate | 2026-08-28 | 8d |
| **`rerank_weight`** — the no-op pattern, under *adr update*. Doing nothing is legitimate | 2026-08-28 | 8d |
| **Whether zero abstentions out of 20 gates anything** — under *adr update* | 2026-08-28 | 8d |
| **Ratify the headroom obligation** into [ADR-RS](../docs/adr/0036_predictions.md) — under *adr update* | 2026-08-28 | 8d |
| **The 7 `partial` goldens** — needs a human or a third blind reader; under *testing* | 2026-08-28 | 8d |
| **W-87 — what "good" means**, Part B blocked on a corpus that was wiped | 2026-08-27 | 9d |
| 🟢 **W-114 — `.github/skills/` for Copilot, or nothing?** A one-line verdict on [`copilot-skill-surface`](compare/copilot-skill-surface.compare.md). Copilot now reads `.github/skills`, `.agents/skills` **and `.claude/skills`**, so the default install already delivers fux's skills to it — including `fux-enrich`, which [ADR-ENRICH](../docs/adr/0040_enrich.md) decision 10 confined to Claude. **Proposed: C, write nothing new.** 🔴 The crux is unmeasured — duplicate-name behaviour across two skill directories — and C is the only option that does not depend on it. ⚠ C's cost is real: `install = ["copilot"]` alone gets no skills | 2026-09-06 | 0d |

---

## Measurement plumbing

- ✅ **The LAB emitter is fixed; the PLAYGROUND half is still open, and the
  reason is Arpit's staged tree.** `fux-lab/shared/regress/run.py` now writes
  `results/per-query.jsonl` — one row per query per arm, `{id, arm, query,
  doc, hit, rank, ms}`, on every scored run including a `--accept-baseline`
  one (a baseline nobody can re-derive is the same defect one run later);
  `--arm` names the arm and defaults to the env directory. Every aggregate it
  reports is now a sum over rows it filed. Smoke-run 2026-09-05 on a throwaway
  three-pair env: 2/3 hits, rows and aggregates agree.
  🔴 **`fux-playground/check.py` still writes nothing.** `grade()` already
  returns `{id, state, detail}` per golden, so it is a `--rows <path>` writer
  and nothing more — but **that repo has 74 files staged and its index staged
  as deletions, with no commit since 2026-08-20**. Editing it would tangle a
  new change into a pending commit that is Arpit's (R-11). **Left for after he
  commits or restores it.** `filed: 2026-08-28`

- ⚠ **The per-query-rows gate checks for a `.jsonl`, not for rows.** `tests/test_regression_runs.py::test_measured_run_files_its_per_query_rows` passes on **any** `.jsonl` under `evidence/` — [`2026-09-05-answer-top3`](regression/2026-09-05-answer-top3/report.md) satisfied it on a *copy of the goldens file* before its real rows were written. **This is the W-83 shape again**: a check that proves a file exists, never that it is the right file. Recorded rather than patched — a looser or cleverer check (is it one row per query? per arm?) cannot be written without knowing each run's arm structure, and shipping an approximation is the moving-threshold failure in another costume. **Whether this is a second strike is Arpit's call, alongside the W-83 gate question already in the inbox.** `filed: 2026-09-05`

- ⚠ **No run filed before 2026-08-28 has per-query rows**, so no paired result
  from before that date can be re-tested by anybody, ever. Unfixable
  retroactively; recorded so nobody re-derives it as a surprise.

---

## Open items

### fux build

- 🟢 **W-113** · `agent` · *(record: [ADR-URL-LIST](../docs/adr/0018_url-list.md) ·
  [ADR-URL-FRESHNESS](../docs/adr/0052_url-freshness.md) ·
  [ADR-CDP-FETCHER](../docs/adr/0020_cdp-fetcher.md))* · **`update = auto|never`
  on a URL line** — whether `fux update` goes out at all, resolved through the
  same three layers as `keep`/`ttl`/`enrich`. **Filed by Arpit's R-1 ruling,
  2026-09-05**, as the second half of it: the ETag criterion was accepted as
  [decision 12](../docs/adr/0020_cdp-fetcher.md) words it (no code), and this
  is the knob he asked for instead. 🔴 **It buys bandwidth by giving up
  freshness — it is NOT the ETag saving**, and decision 12 gains the veto
  condition that re-costs request-stage interception if refresh bandwidth is
  ever reported as a blocker. ⚠ `ttl=` is **ask-time** and does not reach
  `fux update`; `update=` takes two words and never a duration, so the two
  cannot be conflated. — [detail](open/W-113-url-update-policy.md)
  `filed: 2026-09-05`

- 🟠 **Search v3 — seven items, RATIFIED by Arpit 2026-09-05; all seven now
  `agent`** · *(spec: [`proposals/search-v3.md`](proposals/search-v3.md) §8 ·
  one detail file each under [`open/`](open/README.md))* · **Opus** executes,
  in his stated order: ~~W-108~~ (**landed 2026-09-05** —
  [IMPLEMENTATION](IMPLEMENTATION.md), [the run](regression/2026-09-05-answer-top3/report.md)) →
  ~~W-107 Phase 0~~ + ~~W-106~~ (**both measured 2026-09-05** —
  [`node-log-divergence`](regression/2026-09-05-node-log-divergence/report.md),
  [`vector-gate`](regression/2026-09-05-vector-gate/report.md); Phase 0 awaits
  one word from Arpit, W-106 filed **without a verdict** on his ruling) →
  **W-107 Phases 1–4** → ~~W-109~~ (**landed 2026-09-05, gate 16-0** —
  [the run](regression/2026-09-05-expand/report.md)) → ~~W-110~~ (**built
  2026-09-05; its gate is AMBIGUOUS and in the inbox above** —
  [the run](regression/2026-09-05-doc2query/report.md)) → ~~W-111~~ (**landed
  2026-09-05** — [the run](regression/2026-09-05-declared-ties/report.md)) →
  **W-112**. 🔴 **Every remaining search-v3 item is on Arpit**: W-107 Phases 1–4
  wait on the `log()` pick, W-112 on a corpus and a compare doc. ⚠ **One decision in the ratification was
  left unstruck — W-107 Phase 0's `log()` choice — and is in the inbox above
  rather than defaulted here.** `filed: 2026-09-04` · `ratified: 2026-09-05`
  - **[W-106](open/W-106-vector-gate.md)** · `agent` · *(no record — a run)* · **MEASURED 2026-09-05, and NO VERDICT FILED** ([the run](regression/2026-09-05-vector-gate/report.md)) — Arpit's ruling, because **DENSE-CHUNK's frozen bar cannot be tested**: the playground's committed index is `fux.index.v1` (unreadable by this engine) and its enrichment was **never committed**, so *today's ask* is **28/50** against that control's **32/50**. Retrieval: both correctly-configured arms net **zero** (6/6 and 5/5 fixed/broken) and each moves **1 of 9** vocabulary-gap failures. 🔴 **The finding is reproducibility**: two implementations of one model agree to **cosine 0.9964** and share **0 of 125** int8 vectors, 41/50 top-5 orderings discordant. ⚠ **The DoD's `pooling: mean` is wrong for BGE** and the misconfigured arm scored best. **Still owed: the two-architecture arm** (arm64 only here) and a corpus.
  - **[W-107](open/W-107-node-read-plane.md)** · `agent` · *(**ADR-NODE-SEARCH** new · ADR-RANKING · ADR-MCP)* · the Node read plane — `npx fux-search ask|find|answer|explain|graph|path|mcp`, zero deps, one contract, a third arm of the differential law. **Phase 0's measurement is DONE and filed** ([the run](regression/2026-09-05-node-log-divergence/report.md)); the pre-registration [`PRE-REGISTRATION-NODE.md`](benchmark/PRE-REGISTRATION-NODE.md) is written with **one cell blank** — Arpit's `log()` pick, in the inbox above with the number beside it. **Phases 1–4 are blocked on that one word**, and on nothing else.
  - **[W-112](open/W-112-vector-plane.md)** · `arpit` · *(**ADR-VECTORS** new · ADR-DOTFUX · ADR-INGEST · ADR-ASK · ADR-PROVENANCE)* · the vector plane — `fux embed`, pinned `.fux/vectors/`, `--qvec`, rank-space fusion; fux never computes a vector. 🔴 **STILL BLOCKED, and the blocker changed shape.** W-106 produced no PASS to unblock it, and it produced something the plane's design has to answer: **a pinned committed vector is an artefact of one implementation** — two correct implementations of one model share **0 of 125** int8 vectors ([the run](regression/2026-09-05-vector-gate/report.md)). The determinism claim can only ever be *"same clone + same embedder build"*, never *"same model"*. **Blocked on: a restored corpus (W-87 Part B), a re-run gate, and the compare doc Arpit must rule on.**

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
  W-94's *"doing nothing is legitimate"* is untouched. ⚠ **A THIRD knob joined on 2026-09-05**: `expand_weight`, shipped at `0.2` (Query2doc's 1:5) and **untested by [W-109's gate](regression/2026-09-05-expand/report.md)**, which ran every arm at that one value. It is the first knob this sweep has a corpus that can actually see move — 16 goldens changed state under it. ⚠ **And `rerank_weight` now moves TWO mechanisms**, not one: since W-108 it also scales the refer plane's passage proximity, which the sweep's design assumed it did not. **Re-derived in code and written into T1 on 2026-09-05 as a stated limit** — T1.a/T1.c read `ask` rows and do not fetch, so **T1.d's veto is the exposed leg**; the bar is unchanged and the verdict now owes the sentence. Scope is `rerank_weight`
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
  🔴 **Still blocked on the playground's per-query rows**, which are blocked on
  Arpit's staged `fux-playground` tree (R-11). —
  [detail](open/W-97-tuner-knob-sweep.md) `filed: 2026-08-28`

- ⚠ **`separation_floor` is repo-configurable and R10 is still unmeasured.**
  *(record: [ADR-CONFIDENCE](../docs/adr/0045_confidence.md))* · Not a new
  item — R10 is [W-90]'s — but the failure mode is: a repo can make its own
  answers read `grounded` without touching the ranking, and **nothing
  mechanical catches it**. The guard is that the block publishes the floor it
  was judged under. **Any run comparing two arms must assert their floors are
  equal**; differing floors is a pre-registered threshold moving inside a
  comparison, and it is ADR-CONFIDENCE decision 13's reopen trigger.

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

- **W-87** · `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0044_quality-contract.md))* · **what
  "good" means, then measure.** P0, P1, P3, P4 and P5 are closed and
  `recall@k` now exists. ⚠ **Two things keep it open:** the `judged` series
  has never been exercised (no judged run exists), and **Part B cannot run**
  — `acme` and `orbit` went in the 2026-08-20 wipe with their generator, and
  `tools/pruning-eval/` hard-codes reading them. —
  [detail](open/W-87-what-good-means.md)

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

- ⏳ **W-114** · `arpit` · *(record: [ADR-AGENT-POLICY](../docs/adr/0035_agent-policy.md))* ·
  **Copilot's skill surface — rule on the compare doc.** Decision 9a excluded
  `fux-decoder` from Copilot on a fact that has since expired: *"Copilot has no
  progressive-disclosure surface"*. It has one now. **The code half of this
  landed 2026-09-06** — Codex is the fourth vendor (decisions 11–12), and
  decision 13 records the finding that made the Copilot half a fork rather than
  a row: **Copilot reads `.claude/skills`**, so it already loads every skill fux
  writes for Claude, `fux-enrich` included. 🔴 **Nothing fux can do closes
  that** — the path is Anthropic's convention and another vendor chose to read
  it. What is owed is one verdict on
  [`copilot-skill-surface`](compare/copilot-skill-surface.compare.md).
  `filed: 2026-09-06`

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
