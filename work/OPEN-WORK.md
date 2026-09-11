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
ages stops flagging its own oldest item. As of **2026-09-11, seven rows are past CLAUDE.md's 5-day threshold** and a
session names each, with its age, in its first output.*

🟢 **Rulings with their evidence are in
[`proposals/unblock-2026-09-05.md`](proposals/unblock-2026-09-05.md)** (`R-1`…`R-11`),
with a paste-ready Opus prompt beside each. Arpit strikes or accepts a line;
the row then closes through that prompt.

🔴 **Rule 4 has now fired five times in twelve days — re-derive before
believing a row here.** **2026-09-11 is the sharpest instance yet:** four rows
sat under *Blocked on Arpit* saying *hands*, *`device_bash` was wedged*, *no
session can run the suite* — and the first session with a shell closed all four
in an hour. `_to_delete/` did not exist. `ruff` was named as an unrun gate and
is in neither `[dev]` nor CI. The suite was **3 131 unit + 78 e2e green** on the
first honest run. **A row that has sat here for days is as likely to be stale as
to be blocked**, and a row whose blocker is an *environment* is the likeliest of
all — that is now the third time this exact section has been wrong about a
machine (2026-08-27, 2026-08-28, 2026-09-11).

⚠ **This file has been written by two sessions at once before** (2026-09-06);
diff before believing your own copy is current.

| what he decides | filed | age |
|---|---|---|
| 🔴 **THE ADR FRESHNESS GATE IS RED ON A COMMIT THAT IS ALREADY MADE, and the honest fixes are both his.** ✅ **Everything else in this row closed 2026-09-11**: `_to_delete/` is gone, the suite ran on the MacBook (**3 131 unit + 78 e2e green**), and the tree is committed. ⚠ **`ruff` was listed as an unrun gate and is not one** — it is in neither `[dev]` nor `.github/workflows/ci.yml`. 🔴 **What is left:** `94231b2bf` (W-114) fails `test_adr_freshness.py`. **Diagnosed 2026-09-11 and the gate is OVER-FIRING**: the commit changed `src/fux/config.py` only to add `"codex"` to `[agents] install`, and the three records it is convicted of missing — ADR-ACQUIRED, ADR-PII, ADR-URL-FRESHNESS — *describe* that file for `keep`/`acquired_max_bytes`, `enrich` and `ttl`, **none of which it touched**. The `describes` relation is file-scoped and the descriptions are key-scoped. **So there are exactly three moves and every one is a ruling:** (a) rebase to make the commit touch three records it has no business touching; (b) narrow `describes` to key scope — a gate change, and loosening a check to pass is the moving-threshold failure in another costume; (c) move `docs/adr/RULE-SINCE`, which the test's own docstring calls the blunt instrument that **retires ninety-five commits to forgive three**. **No session may pick one.** 🔴 **And 11 commits are unpushed** — pushing is outward-facing and was not asked for | 2026-09-06 | 5d |
| ⚠ **Whether the prior enrichment measurements need re-running.** W-110 found that a newly written enrichment was **never indexed on an incremental ingest** (reuse was keyed on the document's sha alone) — shipped that way from W-76 Phase 8 to 2026-09-05. **Every enrichment measurement on record ran through it**, and whether any under-measured enrichment depends on whether its harness ingested from clean. [`2026-08-24-blind-enrichment-second-author`](regression/2026-08-24-blind-enrichment-second-author/ANALYSIS.md)'s `+1 / −1` is the one that matters, because it is what motivated replacing prose with questions. ⚠ **AUDITED 2026-09-06 and the answer is NO — kept open at Arpit's request, not because the question is open.** `run.py:320` is `reusable = {} if (full or pii_moved) else _reusable(...)`, so **`--full` empties reuse and the defect cannot fire**; the `+1 / −1` run used `fux ingest --full` per arm and `2026-08-28-placebo-and-seal` wiped `.fux/index` and `.fux/runtime` per arm. **No re-run is needed and no corpus is required** — the row's earlier *"a re-run needs a corpus that no longer exists"* is withdrawn. 🔴 **What is genuinely open is a different thing**: `placebo-and-seal` SAW the symptom on 2026-08-28 (*"0 changed, 10 carried forward"*, all arms identical) and **worked around it per-arm instead of recognising an engine defect**, which hid it for a week — a measurement-discipline lesson owed to [ADR-RS](../docs/adr/0043_predictions.md), not an enrichment fact | 2026-09-05 | 6d |
| 🟠 **`superseded_weight` — RULED 2026-09-11: REMEASURE FIRST, then decide.** Arpit declined both standing options (ship the `fux doctor` disclosure now; do nothing). ⚠ **The ruling does NOT unblock it** — W-94 below carries what the remeasure needs, and the question it must actually ask, which is **not** *"which value?"* but *"does ANY single global value clear `0 broken`?"*. Blocked on the uncommitted playground | 2026-08-28 | 14d |
| 🟠 **`rerank_weight` — Arpit asked for `1.0` on 2026-09-11; HELD, and the reason is recorded in W-126.** The ask came from a premise that does not hold: *the reranker should depend on an archived flag*. **It cannot and must not** — the reranker is proximity only (coverage², min span, adjacency) and has no concept of retirement; the archived flag already reaches ranking through **`archived_weight`**, a different knob. Wiring it into the reranker would state one rule in two places (L0). ⚠ **`rerank_weight = 1.0` is a separate, corpus-wide ranking change** whose evidence is `+4` hand-graded, `informed`, **below the resolution floor** — so it falls under the same *remeasure first* ruling Arpit gave `superseded_weight` the same day, on the same blocked corpus | 2026-08-28 | 14d |
| 🟢 **W-126 — `archived=` on URL lines, and the no-op disclosure. READY TO BUILD, no decision owed.** Two things Arpit asked for on 2026-09-11 that need no measurement and change no ranking: URL source lines gain the `archived` attribute `dirs` lines already have, and `fux doctor` discloses every ranking prior that ships as a no-op. ⚠ **No new ADR** — see the item below for why. **Hand to Claude Code** | 2026-09-11 | 0d |
| **Whether zero abstentions out of 20 gates anything** — under *adr update* | 2026-08-28 | 14d |
| **Ratify the headroom obligation** into [ADR-RS](../docs/adr/0043_predictions.md) — under *adr update* | 2026-08-28 | 14d |
| **The 7 `partial` goldens** — needs a human or a third blind reader; under *testing* | 2026-08-28 | 14d |
| **W-87 — what "good" means**, Part B blocked on a corpus that was wiped | 2026-08-27 | 15d |
| ⚪ **W-121 — the CSV row-granularity run is `informed` and supplies no delta.** [ADR-TABULAR](../docs/adr/0062_tabular.md) shipped on your ruling, not on evidence clearing a bar (`hit@1` 0.229 -> 0.875, control 42/48, but one author wrote the generator AND the queries). A `blind` run over real spreadsheets is what would turn it into a grade — that is fux-playground's job, not the lab's (TEST-PLAN §0a). Doing nothing is legitimate; the veto condition is written | 2026-09-06 | 5d |
| 🔴 **W-116 — the chunking change re-ranked the corpus unmeasured**, on his own 2026-09-06 ruling that a defect fix does not wait on a measurement. Recorded as unmeasured in ADR-DECODE, ADR-REFER and ADR-EXTRACTED. Blocked behind **W-56** (`fux-lab` does not exist); here so the gap is not forgotten | 2026-09-06 | 5d |
| ⚪ **W-118 — do `fux-decoder` and `fux-usage` get `.github/skills/` too?** W-114 ruled **A** and shipped `fux-enrich` there, because that is what was named. The other two reach Copilot only through the `.claude/skills` cross-read (ADR-AGENT-POLICY decision 13), which is not a surface fux writes. **Doing nothing is legitimate** — the asymmetry is recorded and held by `test_the_two_rosters_differ_only_where_a_record_says_so`, so it cannot go quiet the way `fux-enrich`'s did. Two rows if yes | 2026-09-06 | 5d |

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

- 🔴 **`fux doctor` reports `[OK]` for a `fux.toml` that will not load.**
  `agent` · *(record: [ADR-DOCTOR](../docs/adr/0011_cli-surface.md) ·
  [ADR-DOTFUX](../docs/adr/0012_fux-directory.md) decision 6)* · **Found
  2026-09-11 while verifying that the `[decode]` refusal does not take `doctor`
  out** — it does not, which is the property [ADR-OUTPUT](../docs/adr/0054_output-defaults.md)
  decision 19 lost. But `doctor` then degrades to `fetcher optional functions:
  skipped (no readable fux.toml)` and **calls that `[OK]`**, so a repo whose
  config refuses gets a green doctor beside an ingest that exits 1. The verb
  whose job is to name the fix is the one verb that does not name it. **The fix
  is one new row — `fux.toml loads` — reporting the loader's own message**;
  ADR-DOTFUX decision 6's fifth ⚠ carries the diagnosis and says why it was
  filed rather than patched there. `filed: 2026-09-11`

- 🟢 **W-126 — `archived=` on URL lines, and `fux doctor` discloses the no-op
  priors.** `agent` · *(records: [ADR-ARCHIVED-CONTENT](../docs/adr/0044_archived-content.md) ·
  [ADR-URL-LIST](../docs/adr/0026_url-list.md) · [ADR-DOCTOR](../docs/adr/0011_cli-surface.md) ·
  [ADR-TUNE](../docs/adr/0045_tuning.md))* · **Arpit's asks of 2026-09-11,
  reduced to the parts that need no measurement.** Ready for Claude Code.
  `filed: 2026-09-11`

  **A · `archived` becomes a URL-line attribute.** `dirs` lines carry
  `Attribute("archived", ("true","false"), "false")`
  (`ingest/sourcelist.py`); **`urls` lines carry `fetch`, `meta`, `keep`,
  `ttl`, `enrich` and NOT `archived`** — verified 2026-09-11. A retired page
  behind a URL cannot be declared retired at all, which is a real asymmetry
  and Arpit's instinct was right. **Amends two records; adds no law and no
  new record.** ⚠ ADR-URL-LIST decision 12 applies — a fux-written line states
  every attribute at its default, and `archived` has a real default, so it is
  written rather than omitted.

  **B · `fux doctor` discloses every ranking prior that ships as a no-op.**
  `archived_weight 1.0` · `superseded_weight 1.0` · `rerank_weight 0.0` ·
  `recency_half_life_days 0.0`. 🔴 **All four mechanisms are built, wired and
  switched off, and nothing tells the author** — a repo that declares
  `archived=true` or `supersedes:` gets exactly nothing and is not told. **This
  is a disclosure, not a ranking change**, and it is the cheapest honest answer
  to the whole no-op pattern. ⚠ It states the fact and **refuses to recommend a
  value** — recommending one is the remeasure's job (W-94), not `doctor`'s.

  🔴 **NO NEW ADR IS WRITTEN, and this is the correction that matters.** Arpit
  asked for *"a new ADR for archive… let me check whether we have one. We do
  not."* **We do**:
  [ADR-ARCHIVED-CONTENT (0044)](../docs/adr/0044_archived-content.md),
  `accepted` 2026-08-22, in the ownership table, owning
  `tools/archived-signal-eval/`. **Writing a second one would break L0 the same
  week it was ruled** — a rule is stated in exactly one ADR. Part A is an
  amendment to it.

  🔴 **And the reranker is NOT how archived reaches ranking.** The ask was
  *"the reranker can depend on archived=true"*. It must not: the reranker is
  **proximity only** — coverage², min span, adjacency over the same analyzed
  token stream — and has no concept of retirement. The flag already reaches
  ranking at `rank.py:214` as `score × archived_weight`, and
  `_record_is_archived` resolves it. **Putting it in the reranker too would
  state one rule in two places.** ⚠ `archived` and `superseded` are
  **independent flags** — a document can be both.

- 🔴 **W-127 — how fux can and cannot know a document is retired, stated once
  where it can be cited.** `arpit` · *(record:
  [ADR-ARCHIVED-CONTENT](../docs/adr/0044_archived-content.md) ·
  [ADR-ENRICH](../docs/adr/0047_enrich.md))* · **Arpit asked the right question
  on 2026-09-11 and the answer is scattered across four records and two runs.**
  `filed: 2026-09-11`

  His question: *"a document might look like a legal document and say nothing
  about being retired — or ten documents could say it ten different ways."*
  **Correct, and it is the whole difficulty.** The answer fux has is three
  routes and one refusal:

  | route | verdict |
  |---|---|
  | **infer from text** (*"obsolete"*, *"deprecated"*, *"no longer in force"*) | 🔴 **refused, and measured to BACKFIRE** |
  | **`supersedes:`** on the successor | ✅ exact; needs a human, and cannot cover a document retired before its successor existed |
  | **`superseded_by:`** in an enrichment | ✅ exact, **and never touches the original** — [ADR-ENRICH decision 17](../docs/adr/0047_enrich.md) |

  🔴 **Inference does not merely fail, it inverts — measured here, not
  argued.** Two blind authors independently broke the **same two** queries
  ([`2026-08-24-blind-enrichment-second-author`](regression/2026-08-24-blind-enrichment-second-author/ANALYSIS.md))
  because **BM25F cannot see negation**: *"no longer current"* and *"is
  current"* are the same tokens, so honest retirement prose hands the retired
  document the query's own word. **The more honestly a document says it is
  retired, the higher it ranks for *current*.** The ten-phrasings problem is
  the smaller one — a phrasing heuristic is exact for the repo that invented it
  and a **silent convention for everybody else**, failing with no error.

  ⚠ **And the hard limit, which no ranking function escapes:** if nothing in
  the corpus declares the document retired, **the fact is not in the text** and
  nothing recovers it — not BM25F, not the reranker, not embeddings. **Fux
  should say it does not know**, which is W-126 part B.

  **What is owed:** ADR-ARCHIVED-CONTENT states the three routes and the
  refusal **in one place**, citing the blind run rather than restating it, so
  the next person asking this question reads one record instead of
  reconstructing it. ⚠ **`superseded_by:` in enrichment is the answer for an
  untouchable original and is easy to miss** — it is currently a decision
  inside ADR-ENRICH and is not discoverable from the archive record at all.

- 🔴 **W-122 — L0: ADRs are the only source of truth, and the Law records
  outrank every other record.** 🟢 **L0 AND THE RENAME LANDED 2026-09-06** (uncommitted);
  what remains is the generated CLAUDE.md block, the config consolidation and the gate. `agent` · *(records: **ADR-LAW-0** new ·
  ADR-LAWS restructured · ADR-LAW-1…8 promoted · ADR-CONFIG · ADR-TUNE ·
  ADR-OWNERSHIP)* · **Arpit ruled this 2026-09-06**, deciding R-2 and going
  past it. Two clauses: **source** — a rule is stated in exactly one ADR and
  every other artifact links, never restates; **precedence** — a record that
  conflicts with a Law is **void in the conflicting part**. **Amendment is
  entrenched**: a Law changes only on Arpit's ruling, named in the record.
  **`CLAUDE.md` stops being normative and becomes a pointer, permanently** —
  its law section is generated from the records and test-asserted.
  **The nine law files are renamed `*_LAW-n-*.md` and cited `ADR-LAW-n`**;
  L0 appends as `0002_LAW-0-authority.md` — with `LAW-` in the filename,
  contiguity stops mattering and no second renumber is needed.
  🟢 **This is what makes R-2's gate writable**: with one source, ADR-CONFIG's
  fenced key tree ↔ `config.py` is a parser, both directions — and *a key is
  real only if it is in the tree*, which is exactly how `acquired_max_bytes`
  rotted in prose. Carries the config consolidation (`config.schema.json` and
  `derive/runtime.schema.json` **deleted** — both verified documentation-only;
  the four runtime-loaded schemas untouched, because they *enforce* rather
  than *describe*). ⚠ **Supersedes ADR-LAWS decision 1, accepted the same
  day**, and ⚠ **a concurrent session renumbered the whole register on
  2026-09-06** — re-derive paths and land the rename in one commit by one
  agent. — [detail](open/W-122-adrs-are-the-source.md) `filed: 2026-09-06`

- 🟢 **W-113** · `agent` · *(record: [ADR-URL-LIST](../docs/adr/0026_url-list.md) ·
  [ADR-URL-FRESHNESS](../docs/adr/0059_url-freshness.md) ·
  [ADR-CDP-FETCHER](../docs/adr/0028_cdp-fetcher.md))* · **`update = auto|never`
  on a URL line** — whether `fux update` goes out at all, resolved through the
  same three layers as `keep`/`ttl`/`enrich`. **Filed by Arpit's R-1 ruling,
  2026-09-05**, as the second half of it: the ETag criterion was accepted as
  [decision 12](../docs/adr/0028_cdp-fetcher.md) words it (no code), and this
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
  - **[W-106](open/W-106-vector-gate.md)** · `agent` · *(no record — a run)* · **MEASURED 2026-09-05, and NO VERDICT FILED** ([the run](regression/2026-09-05-vector-gate/report.md)) — Arpit's ruling, because **DENSE-CHUNK's frozen bar cannot be tested**: the playground's committed index is `fux.index.v1` (unreadable by this engine) and its enrichment was **never committed**, so *today's ask* is **28/50** against that control's **32/50**. Retrieval: both correctly-configured arms net **zero** (6/6 and 5/5 fixed/broken) and each moves **1 of 9** vocabulary-gap failures. 🔴 **The finding is reproducibility**: two implementations of one model agree to **cosine 0.9964** and share **0 of 125** int8 vectors, 41/50 top-5 orderings discordant. ⚠ **The DoD's `pooling: mean` is wrong for BGE** and the misconfigured arm scored best. **Still owed: the two-architecture arm** (arm64 only here) and a corpus.
  - **[W-107](open/W-107-node-read-plane.md)** · `agent` · *(**ADR-NODE-SEARCH** new · ADR-RANKING · ADR-MCP)* · the Node read plane — `npx fux-search ask|find|answer|explain|graph|path|mcp`, zero deps, one contract, a third arm of the differential law. **Phase 0 is CLOSED** ([the run](regression/2026-09-05-node-log-divergence/report.md) + [`ADDENDUM-IDF`](regression/2026-09-05-node-log-divergence/ADDENDUM-IDF.md) + [`ADDENDUM-GLIBC`](regression/2026-09-05-node-log-divergence/ADDENDUM-GLIBC.md)). Arpit ruled **(b) — scores equal after `round(9)`, ordering byte-equal** on 2026-09-06; [`PRE-REGISTRATION-NODE.md`](benchmark/PRE-REGISTRATION-NODE.md) is **frozen in full**, sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`, and the rule now lives in [ADR-RANKING decision 8a](../docs/adr/0021_ranking.md). ▶ **Phase 1 starts.** ⚠ The glibc number came from a Linux container, not from [`log-probe.yml`](../.github/workflows/log-probe.yml), which is **still unrun**; musl, Windows and Node 20 stay unmeasured and §4 still requires all three OSes before an arm is called green.
  - **[W-112](open/W-112-vector-plane.md)** · `arpit` · *(**ADR-VECTORS** new · ADR-DOTFUX · ADR-INGEST · ADR-ASK · ADR-PROVENANCE)* · the vector plane — `fux embed`, pinned `.fux/vectors/`, `--qvec`, rank-space fusion; fux never computes a vector. 🔴 **STILL BLOCKED, and the blocker changed shape.** W-106 produced no PASS to unblock it, and it produced something the plane's design has to answer: **a pinned committed vector is an artefact of one implementation** — two correct implementations of one model share **0 of 125** int8 vectors ([the run](regression/2026-09-05-vector-gate/report.md)). The determinism claim can only ever be *"same clone + same embedder build"*, never *"same model"*. **Blocked on: a restored corpus (W-87 Part B), a re-run gate, and the compare doc Arpit must rule on.**

- 🔴 **W-94** · `arpit` · *(record: [ADR-CONFIDENCE](../docs/adr/0052_confidence.md) ·
  [ADR-TUNE](../docs/adr/0045_tuning.md))* · **`superseded_weight` ships at
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
  a defect.

  🟠 **ARPIT RULED 2026-09-11: remeasure, then decide.** Neither shipping the
  disclosure nor closing the row — a new measurement, and the call comes off it.

  🔴 **The remeasure must ask the right question, and it is not *"which
  value?"*.** `P-SUPERSEDE` did not fail because `0.5` was the wrong number; it
  failed because **supersession belongs to the QUERY'S INTENT, not to the
  document** — *"what do we do now?"* and *"what did we do before?"* want
  opposite rankings out of the same corpus, and one global multiplier cannot
  serve both. So the pre-registered question is: **does ANY single global value
  clear a `0 broken` bar?** ⚠ **A run that answers NO is a success**, and it is
  the likelier answer: it would close the knob permanently and move the work
  query-side, where the signal actually lives. A run designed only to find a
  good value cannot report that.

  **What it needs before it can run, none of which exists today:**

  - 🔴 **A corpus containing the failure mode.** The v1-vs-HEAD benchmark
    corpus **cannot see it by construction** — only the hand-graded playground
    has queries whose correct answer IS the superseded document (`q022`,
    `q033`). **`fux-playground` has 74 files staged and its index staged as
    deletions, with no commit since 2026-08-20** (R-11), and W-87 Part B's
    corpus was wiped. **Arpit commits or restores it, or there is nothing to
    measure on.**
  - **A frozen pre-registration**, per [ADR-QUALITY](../docs/adr/0051_quality-contract.md)
    decision 2a — naming its `k`, its arms (`1.0` against the candidates, swept
    in one pass) and the `0 broken` bar **before** the first number.
    ⚠ W-110's gate was voided for exactly the omission this would repeat.
  - **The query set split by intent** — *current-seeking* against
    *history-seeking* — declared in the pre-registration, because a set holding
    only the first kind will clear any bar and prove nothing.
  - ⚠ **This cannot be done from Cowork**: the bridge VM is Linux/py3.10/no
    egress and the committed `.venv` is macOS-built, so no session here can run
    the suite or the harness (verified 2026-09-11).

  ⚠ **Until the corpus is committed the row is blocked on Arpit twice** — once
  for the ruling, which he has given, and once for the environment.
  `filed: 2026-08-28` · `ruled: 2026-09-11`

### testing

- 🔴 **W-116** · `arpit` · *(record: [ADR-RS](../docs/adr/0043_predictions.md))* ·
  **W-115 re-ranked the corpus and NOTHING was measured.** Two populations
  moved: every document containing a fenced code block (the fence fix — in this
  repo, most of them), and every document of the formats whose decoder gained a
  heading skeleton or a depth cap. Arpit ruled on 2026-09-06 that these land as
  **defect fixes** rather than wait on a measurement — a `# comment` in a bash
  block was never a heading — and that ruling is recorded in all three ADRs.
  ⚠ **What it does not do is make them measured**, and no doc may cite them as
  such. A measurement needs `fux-lab`, which does not exist (**W-56**), so this
  row is blocked behind that one and is here to stop the gap being forgotten
  rather than to be worked next. Filed 2026-09-06

- ✅ **W-117 — CLOSED 2026-09-06, and its filing was wrong.** It said the
  `.pptx` slide floor was *"a tuning question… doing nothing is legitimate"*.
  Two more instances then turned up — six small `.jsonl` records collapsing to
  one passage, and any short band of a small table — and three instances of one
  shape is a defect, not a knob. Fixed in `_chunk._sibling_run` under W-120;
  [ADR-REFER](../docs/adr/0037_refer-plane.md) decision 26 records the reversal.
  Removed from the list once the outcome reaches IMPLEMENTATION.md.

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
  *(record: [ADR-CONFIDENCE](../docs/adr/0052_confidence.md))* · Not a new
  item — R10 is [W-90]'s — but the failure mode is: a repo can make its own
  answers read `grounded` without touching the ranking, and **nothing
  mechanical catches it**. The guard is that the block publishes the floor it
  was judged under. **Any run comparing two arms must assert their floors are
  equal**; differing floors is a pre-registered threshold moving inside a
  comparison, and it is ADR-CONFIDENCE decision 13's reopen trigger.

- **The 7 `partial` goldens.** `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0051_quality-contract.md))* · The two
  blind annotators' exact-set disagreements, taking the union, held out of
  `recall@k`'s denominator. They need a human or a **third blind reader** —
  any session that has seen the scores is the wrong party. 🔴 **Do not resolve
  them by picking whichever set makes recall look better.** `filed: 2026-08-28`

- **The `heading` negative control is saturated and must be rebuilt.** `agent` ·
  *(record: [ADR-RS](../docs/adr/0043_predictions.md))* ·
  [C4](regression/2026-08-28-benchmark-contested/VERDICT-C4.md) returned its
  predicted null at **100 % in both arms with zero headroom**, so it returned
  the right answer for the wrong reason and **did not discharge its job**. Until
  it does, C1 and C3 rest on generator assertions rather than a live control.
  The fix is a control with headroom by construction — e.g. distractors that are
  *also* heading-matched. `filed: 2026-08-28`

- ⚠ **A cross-seed "null control" is not a determinism check, and B9 was read as
  one.** `agent` · *(record: [ADR-RS](../docs/adr/0043_predictions.md))* ·
  Query ids are **positional**, so arm A on seed 12 paired against arm A on
  seed 13 compares *different questions*; the discordant count is a rate
  check. The determinism check is the **same-corpus repeat**.
  [C5](regression/2026-08-28-benchmark-contested/VERDICT-C5.md) was ruled on the
  repeat for that reason. 🔴 **The 2026-08-28 v1-vs-HEAD run's B9 carries the
  same weakness** — its "0 discordant of 240" across two seeds should be read as
  a rate check; its "300/300 identical rows on one corpus" is the half that does
  the work. `filed: 2026-08-28`

- **W-87** · `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0051_quality-contract.md))* · **what
  "good" means, then measure.** P0, P1, P3, P4 and P5 are closed and
  `recall@k` now exists. ⚠ **Two things keep it open:** the `judged` series
  has never been exercised (no judged run exists), and **Part B cannot run**
  — `acme` and `orbit` went in the 2026-08-20 wipe with their generator, and
  `tools/pruning-eval/` hard-codes reading them. —
  [detail](open/W-87-what-good-means.md)

- ⚠ **`validate()` reaches an existing repo only when somebody copies the
  fetcher in.** *(record: [ADR-DOTFUX](../docs/adr/0012_fux-directory.md)
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
  *(record: [ADR-CONFIDENCE](../docs/adr/0052_confidence.md) ·
  [ADR-TUNE](../docs/adr/0045_tuning.md))* · Not a new fact —
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
  against it, not building or measuring anything further.

  🟠 **ARPIT ASKED FOR `1.0` ON 2026-09-11. HELD — and the premise is corrected
  rather than the ask refused.** He asked for it *as a way to make the reranker
  depend on `archived=true`*. **That is not what the knob does**: the reranker
  is proximity only and has no concept of retirement, and the archived flag
  already reaches ranking through **`archived_weight`** — a different knob,
  also at its no-op (W-126 carries the correction in full). So the ask splits:

  - **the part needing no measurement is W-126**, ready to build;
  - **`rerank_weight = 1.0` itself is a corpus-wide ranking change** with `+4`
    hand-graded, `informed`, **below the resolution floor** — the same
    evidential position as `superseded_weight`, which Arpit ruled *remeasure
    first* **the same day**. Shipping one on argument while holding the other
    on measurement would not be a defensible pair.

  🔴 **THE FOUR NO-OP PRIORS ARE ONE PROBLEM, and all four are blocked on ONE
  corpus.** `archived_weight 1.0` · `superseded_weight 1.0` · `rerank_weight
  0.0` · `recency_half_life_days 0.0`. Each is built, wired and off; each needs
  the hand-graded playground to move defensibly, because that is the only
  corpus holding queries whose correct answer IS the retired document.
  **`fux-playground` has 74 files staged and its index staged as deletions,
  with no commit since 2026-08-20** (R-11). ⚠ **One action of Arpit's —
  committing or restoring that tree — unblocks all four, plus W-97's sweep and
  W-87 Part B.** Until then *"remeasure"* cannot start, and that is the honest
  state rather than four independent decisions.
  `filed: 2026-08-28` · `ruled: 2026-09-11`

- 🔴 **The engine abstains ZERO times out of 20.** `arpit` ·
  *(record: [ADR-QUALITY](../docs/adr/0051_quality-contract.md))* ·
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

- **Ratify the headroom obligation into [ADR-RS](../docs/adr/0043_predictions.md).**
  `arpit` · *(record: [ADR-RS](../docs/adr/0043_predictions.md))* · **W-95 is
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
