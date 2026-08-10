# Implementation tracker

*The live, honest ✅/🟡/⬜ of the build. **Update contract (binding on EVERY
execution, whatever the case):** this file is updated in **every session that
executes anything** — milestone completed, milestone failed, run blocked, run
interrupted, partial progress, or even "attempted and abandoned." There is no
outcome that skips the update:*

- *Milestone completes → flip the row (status + tests + note).*
- *Long milestone in flight → bump "Now working on" at regular intervals
  (every significant commit or ~30 min).*
- *Blocked/failed/interrupted → set the row 🟡 or ⛔ with a one-line why, and
  leave "Now working on" pointing at the exact stuck point.*
- *Never ✅ with failing tests.*

*This file answers "where exactly is the build?" — the worklog answers "what
happened per exchange"; keep both.*

**Legend:** ⬜ not started · 🟡 in progress · ✅ done (tests green) · ⛔ blocked

## Now working on

> *(building agent: keep this one line current)* — **Phase 9 COMPLETE (M0–M5).**
> The filed "non-monotone fusion" finding was a **misdiagnosis**: RRF is monotone
> and 160/160 fused results reconcile to the formula with zero delta. Measured the
> real population — hybrid loses a lexical top-5 hit **~4% on realistic corpora**
> (~offset by gains), spanning four kinds incl. a `factual` case lost from rank 1;
> synthetic 9–64% unexplained; **supersession penalty not implicated.** Arpit
> **accepted** it — no fusion change (`compare/hybrid-losing-lexical-hits`); the
> lab demotion check now covers all kinds, and `proposals/chunk-level-dense-codes`
> is filed as the finding's real owner. **No version bump** (docs/investigation
> only). **Next, unstarted:** chunk-level dense codes (own phase), query-at-scale
> (ADR 0011).

## Baseline (pre-build, done in Cowork)

| Item | Status | Notes |
|------|--------|-------|
| Package skeleton (src/, hatchling, 0.19.0, CLI + FuxError, smoke tests) | ✅ | 4 unit tests |
| All design decisions + compare docs | ✅ | `compare/` — all accepted |
| Build specs 0000–0003 | ✅ | `handoff/` |
| OKF-conformant docs bundle | ✅ | 26/26 files |

## Phase 1 — Query CLI v1 (handoff 0001) → v0.20.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 config + `fux setup` (wizard/flags/-y, idempotent) | ✅ | 21 | config load/validate, find_root, wizard+flags+-y, idempotent merge |
| M2 frontmatter parser (load-bearing; unit-first) | ✅ | 13 | subset YAML: scalars/lists/nested/literal; permissive; round-trip |
| M3 ingest inferred tier → OKF cache + manifest + chunker | ✅ | 36 | converted_at = SOURCE_DATE_EPOCH/mtime (determinism; → ADR 0002 + Deviations) |
| M4 BM25F index + `ask`/`find` (+ --json/--explain) | ✅ | 16 | JSON index (open Q1 resolved), incremental by sha |
| M5 `answer` (extractive + TextRank + citations) | ✅ | 12 | passage × overlap × centrality; doc-order citations |
| M6 `setup --agents --skills --hooks` | ✅ | 8 | managed blocks, skills pair, fail-open hooks, settings merge |
| M7 `tests_e2e/` suite (corpus + goldens + determinism) | ✅ | 21 | found+fixed --check drift bug and answer noise; goldens pinned to no-extra corpus |
| Close-out: ADRs 0001–0004, docs law, archive pair, bump | ✅ | — | v0.20.0; DOGFOOD.md emitted; suites: 108 unit + 20 e2e (+1 gated skip) |

## Phase 2 — Ingest v1.1: web/CDP/advanced (handoff 0002) → v0.21.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 HTML→Markdown converter (stdlib, goldens-first) | ✅ | 12 | html.parser; deterministic; link/title extraction |
| M2 urllib fetcher + crawl frontier + robots + `--web` e2e | ✅ | 12+4 | frontier/robots/dedupe/config + fixture-server e2e (M5) |
| M3 RFC 6455 WebSocket client + CDP capture | ✅ | 14 | RFC vectors + fake-server handshake; websocket-client = flagged fallback |
| M4 advanced tier (Docling/Tesseract, fidelity transitions) | ✅ | 6 | (sha, fidelity)-keyed index reuse; upgrades survive re-ingest |
| M5 e2e additions + docs | ✅ | 4+2 | fixture site (robots/oversize/off-domain), import-fence test, manual CDP smoke |
| Close-out: ADR 0005, docs law, archive pair, bump | ✅ | — | v0.21.0; suites: 154 unit + 24 e2e (+1 gated skip) |

## Phase 3 — Hybrid engine v2 (handoff 0003) → v0.22.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 eval harness + lexical baseline recorded | ✅ | 2 | 21 pairs; lexical: hit@1 0.762 · hit@5 0.952 · MRR 0.833 |
| M2 distillation pipeline (`tools/distill/`, ≤10 MB asserted) | ✅ | — | potion-base-8M re-pack, int8, 7.93 MB, sha-pinned, MIT-checked |
| M3 stdlib inference (`fux.embed`, int8) | ✅ | 10 | exact tokenizer parity; int8 dot; lazy load 10 ms |
| M4 chunk-vector cache (manifest-invalidated) | ✅ | 4 | single vectors.bin; (sha, fidelity)-keyed reuse |
| M5 RRF fusion + `--lexical-only` + explain | ✅ | 3 | k=60; v1 byte-parity proven by unchanged goldens |
| M6 eval gate: hybrid ≥ lexical (numbers → ADR) | ✅ | 1 | tie (gate ≥ passes, ships enabled); rank-level rescues; ADR 0006 |
| M7 packaging (bundle in wheel, lazy load, size checks) | ✅ | 1 | wheel 6.98 MB ≤ 15; bundle ≤ 10 asserted; warm query 0.2 ms |
| Close-out: ADRs 0006–0007, docs law, archive pair, bump | ✅ | — | v0.22.0; suites: 172 unit + 28 e2e (+1 gated skip) |

## Phase 4 — Knowledge substrate v3 (handoff 0004) → v0.23.0

*Pre-registered 2026-07-21 with the handoff (per the CLAUDE.md rule: every plan
seeds its milestone table here before building; the building agent updates a
row at EVERY milestone completion — no batching).*

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 sqlite store + fux.lock (parity goldens; lock-only --check; migration) | ✅ | 33+12 | all 6 v0.22 goldens pass byte-for-byte on the sqlite backend; lock at root, manifest → runtime plane |
| M2 bulk tier (docs_text) + `fux cat` + committed `.fux/state/` sharding + three-way check | ✅ | 35+13 | fresh clone answers doc-level from state; rebuild reproduces state byte-for-byte; Bloom sized 9.6 bits/term, k=4 (→ ADR 0008) |
| M3 edges + nodes (deterministic extraction; thin-layer payloads) | ✅ | 22 | references/cites/crawled_from/tagged, all EXTRACTED; tag nodes (N not N² edges); on this repo's docs: 92 refs · 13 cites · 9 tagged |
| M3a df sidecar (`state/df/`) — Arpit's DoD-7 amendment | ✅ | 23 | exact df/n/Σfield-lengths; lean == full proven over the *whole* vocabulary on a subset (mutation-tested: removing the injection fails the test) |
| M4 kernel `retrieve()` + verb projections (explain/graph/path; v0.22 golden byte-parity) | ✅ | 23+6 | all 6 goldens byte-identical through the re-plumb; `explain` = ask seeded by a node (top_terms as query), so no second retrieval path; paths BFS + reliability (PPR at M6) |
| M5 FuxVec (codes, Hamming scan, exact rerank, dense_global into RRF) | ✅ | 16 | **eval gate beats v0.22 hybrid**: hit@1 .762→.810 · hit@5 .952→**1.000** · MRR .833→.873; ADR 0006's named zero-overlap miss rescued; `--lexical-only` still exactly .762/.952/.833 |
| M6 expansion (PPR-lite, paths + reliability, graph list into RRF) | ✅ | 20 | constants as specced; seed-rank personalization; `[engine.graph] in_rrf` is the **open-question-2 instrument** — on the 9-doc fixture graph on/off both measure .810/1.000/.873 (too few edges to discriminate; M8's generator must carry real link structure) |
| M7 profiles (full/lean/auto, LRU) + `db pull` v1 | ✅ | 19 | mid-corpus switch (full→lean) keeps rankings *and* scores — mutation-verified non-vacuous; LRU counter-based (no wall clock); `auto` gated on `lean_threshold` (→ Deviations); `db pull` sha-verified, refuses mismatch |
| M8 scale benchmark (synthetic 100k) + eval gate (≥ v0.22 hybrid + zero-candidate rescue) | ✅ | 9 | 100k measured: state **23 MB ≤30 ✓**, df **0.9 MB ≤5 ✓**, db 1081 MB (77% of §8b), FuxVec scan **54 ms < 150 → IVF not built**; gate beaten (1.000 hit@5); ⚠ **query latency 10.6 s @100k** — postings stored but not read at query time (→ ADR 0011, next phase) |
| Close-out: ADRs 0008–0011, docs law, archive pair, bump | ✅ | — | **v0.23.0**; suites: 365 unit + 71 e2e (+1 gated skip); citations in 0010 verified at build time; 0004 pair archived |

## Size envelope — MEASURED at 100k (M8)

The M3a extrapolation below was **wrong, and in the pessimistic direction** —
recorded rather than deleted, because a prediction that missed is worth keeping
next to the measurement that corrected it.

| component | M3a projection @100k | **measured @100k** | budget |
|-----------|---------------------|--------------------|--------|
| `state/df/` | ~2.1 MB | **0.92 MB** (9 B/doc) | ≤5 MB ✅ |
| `state/codes/` | ~5.1 MB | **4.00 MB** (40 B/doc) | — |
| `state/sigs/` | ~14.4 MB | **6.78 MB** (68 B/doc) | — |
| `state/meta/` | ~15.6 MB | **11.25 MB** (112 B/doc) | — |
| **state TOTAL** | ~35 MB ⚠ | **22.96 MB** (230 B/doc) | ≤30 MB ✅ |
| `fux.db` | — | 1 081 MB | ~1 400 MB est (77 %) |
| `fux.lock` | — | 21.5 MB | ~30 MB est (70 %) |

Why the projection missed: it extrapolated from *this repository's own docs*,
which are adversarial for the state plane — very long doc ids
(`docs/handoff/0004-knowledge-substrate-handoff.md`), long titles, and wide
per-document vocabulary that pins Bloom signatures at the 128 B cap. 351 B/doc
projected vs 230 B/doc actual.

**Per Arpit's ruling, the per-bucket-zlib change was contingent on the synthetic
confirming >30 MB. It did not, so nothing was changed.**

## Decisions taken during the build (→ ADRs)

- **M5 / dense_global does not fire when BM25F returns zero candidates.**
  Removing that early return made the honest "No confident matches" answer
  unreachable, because a binary prefilter always has a nearest neighbour.
  Measured on the fixture corpus: pure-noise queries score **0.23–0.26** cosine
  against a true rescue's **0.34** — the ranges overlap, so any absolute floor
  separating them is a magic number that only degrades as the corpus grows.

  Re-reading ADR 0006 settled it: *"zero lexical candidates"* there means the
  **correct document** had no lexical overlap, not that the query matched
  nothing at all (that query does return `docs/guide.md`). So the rescue path
  is the third RRF list, which always has candidates — and honest emptiness is
  preserved. → ADR 0010.

## Phase 5 — Debug & observability (handoff 0005) → v0.24.0

*Pre-registered 2026-07-22 with the handoff, per the CLAUDE.md rule: every plan
seeds its milestone table here before building; the building agent updates a
row at EVERY milestone completion — no batching.*

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 `[debug]` config + emitter (`debug.py`, precedence, redaction, **stdout-purity gate**) | ✅ | 44+5 | `DebugParams`/`_parse_debug` in config.py (calls `debug.apply_config` — the one wiring point every `load()` caller shares); hand-rolled emitter chosen over stdlib `logging` (simpler to keep the flag>env>toml precedence and max_bytes truncation deterministic — ADR 0012 open Q1); `tests/conftest.py` new (autouse debug-state reset — config.load()'s side effect needed isolating); e2e stdout-purity + stderr-reproducibility tests added to test_determinism.py |
| M2 instrument the pipeline (walk/convert/chunk/index/query/dense/graph/answer) | ✅ | 394+80 (+1) | `dbg()`/`timer()` at walk/convert/chunk/index/lock/state/graph (ingest side) + query/lexical/dense/graph/answer/hooks/web (query side); trace-level per-chunk/per-sentence content previews gated on `redact=false`; found + fixed a latent flaky-test risk (ingest's own `Elapsed: N.Ns` stdout line is wall-clock, unrelated to debug — normalized in the new determinism test rather than in product code) |
| M3 `fux doctor` (7 groups, text + `--json`, fix commands, self-test) | ✅ | 14+6 | environment/capabilities/config/corpus/consistency/agent-surface/self-test; capabilities group never fails health (optional paths only); zero-match `[sources]` globs surfaced loudly with fix command (the #1 silent misconfig); self-test ingests a canary doc in a scratch temp dir and proves ingest→index→query→citation end to end; **deviation**: no live CDP-port reachability probe — `import socket` outside `ingest/` trips the existing network-fence test (`test_import_fence.py`), so "Chrome for CDP" checks binary presence only (see Deviations) |
| M4 `fux why` (pipeline walk + verdict line; in/out of corpus, ranked-low) | ✅ | 8+7 | corpus presence (cache/skip-reason/on-disk-but-excluded/absent) → chunks → lexical (full-corpus rank + per-term idf/tf via `Searcher.search(top=all)`) → dense (FuxVec hamming/prefilter/cosine) → graph (seed vs. expanded-via-edge) → one verdict sentence; reuses `kernel.retrieve()` for dense+graph so `why` can never disagree with what a real query would do |
| M5 skills: `fux-debug` + escalation pointers in fux-query/fux-ingest | ✅ | 10+4 | third skill in `agents/generate.py::_SKILLS` (doctor→check→why→advanced→--debug=debug→report-don't-guess workflow); one-line escalation pointer added to both existing skills; `fux setup --skills` now writes 3 skill files, verified idempotent |
| M6 docs (`example/DEBUG.md` + CLI/TOML/SETUP/SKILLS/GLOSSARY) + suites | ✅ | 417+100 (+1) | `example/DEBUG.md` new (worked failures × 7); CLI/TOML/SETUP/SKILLS/GLOSSARY/DOC-REGISTRY/PLAN/INTERVIEW updated; e2e doctor/why/debug-level coverage landed incrementally at M1/M3/M4, confirmed complete here |
| Close-out: ADR 0012, docs law, archive pair, CHANGELOG+README, bump | ✅ | — | **v0.24.0**; ADR 0012 answers all 4 open questions; handoff+prompt archived as `v0.24.0-debug-observability-*.md`; CLAUDE.md hard-won-knowledge + version line updated |

## Phase 6 — Trust & currency (handoff 0006) → v0.25.0

*Pre-registered 2026-07-23 with the handoff, per the CLAUDE.md rule.*

**Model: Opus** (M4's calibration is judgment that fails silently — see the handoff).

Driver: the acme-payments realistic run — staleness inversions **9/12** and
unanswerable fabrication **0/4**, both missed by the synthetic tiers *and* the
21-pair fixture gate.

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 accept forks (2 compare docs → `accepted`) | ✅ | — | both accepted 2026-07-23 (Option A each); fux-query skill update also approved for M3 |
| M2 parse + persist supersession (frontmatter → substrate/state; chains, cycles, near-misses) | ✅ | 426 (+9) | `status`/`superseded_by` already round-trip via `_RESERVED` passthrough; new `index.build_index::_supersession_meta`/`_resolve_supersession` extract+resolve chains/cycles into `files[rel]`; `state.DocState` gained `superseded_by`; sqlite backend bumped to format_version 3 (4 new `docs` columns) — JSON/sqlite parity preserved |
| M3 annotate output (`--json` + human; **ordering unchanged, lexical goldens byte-identical**) | ✅ | 530 total (+4) | `_Ctx.supersession()` in `query/api.py` reads `ctx.files`, merged into `_chunk_json`/find's result dict + human markers; `fux-query` skill gained step 5 (prefer `superseded_by`); `example/CLI.md` documented; all four `--lexical-only` goldens confirmed byte-identical |
| M4 `[answer] min_confidence` floor + calibration against **all five** gates | ✅ | 544 total (+9) | mechanism: `AnswerParams.min_confidence` (validated `[0,1]`), `_run_answer` declines when `max(sentence.score) < floor` and `floor > 0.0`. **Calibrated** (background Opus agent, full acme sweep — `docs/conformance/2026-07-23-min-confidence-calibration/`): **no value clears all 5 gates** — gate 1 (4/4 unanswerable) needs floor ≥0.25, gate 4 (0 false declines/55 answerable) needs floor ≤0.087, empty interval. Shipped default stays **0.0 (disabled)** per the compare doc's rule; trade-off curve + follow-up (F1/F2: floor an absolute signal like dense cosine, not the pool-relative sentence score) filed in ANALYSIS.md |
| M5 `answer` prefers current + `fux why` explains both | ✅ | 544 total (+5) | `query/answer.py::prefer_current`/`best_confidence` shared by `_run_answer` and `why._answer_decline` (never disagree by construction); `answer`'s `sources` annotate `superseded`/`superseded_by` when the successor is absent; `WhyResult` gained `superseded`/`superseded_by`/`answer_decline`, verdict line prepends `answer declines: best score X < min_confidence Y` when applicable; `example/CLI.md`/`TOML.md` updated |
| M6 re-measure acme, ADRs 0013/0014, docs, archive, bump | ✅ | 444 unit + 100 e2e | supersession recovery measured (`docs/conformance/2026-07-23-supersession-recovery/`): 5/12 markers, 3/9 inversions marked, 1 fully corrected + 1 de-cited at `answer` level, 6 unmarked/unreachable; ADRs 0013 (supersession) + 0014 (confidence floor, shipped disabled) written; both proposals → `implemented` and moved to `docs/archive/`; handoff+prompt archived as `v0.25.0-trust-currency-*`; CHANGELOG/README/PLAN/INTERVIEW/GLOSSARY/DOC-REGISTRY updated; version bumped 0.24.0→0.25.0; CLAUDE.md edit proposed (not applied) pending Arpit's review |

**Deliberately out of scope** (each its own future phase, each gated on
evidence): fusion down-ranking of superseded docs · the runner-up margin check ·
chunk-level dense codes for the zero-overlap class (0/6, structural, risks the
~200 B/doc committed-state guarantee).

## Phase 7 — Supersession down-rank + margin re-measure (handoff 0007) → v0.26.0

*Pre-registered 2026-07-24 with the handoff. **M1 cleared 2026-07-24** — Arpit
reopened Option B for a default-off calibrated test; the compare-doc verdict is
amended. Enabling the default still requires a separate M5 sign-off.*

**Model: Opus** (M3/M4 calibration + margin re-read are judgment; "no safe
interval" is a valid outcome).

Driver: two independent realistic corpora — acme 9/12, **orbit 8/12** — show the
retired doc ranking #1 *with the v0.25.0 annotation attached* (orbit 5/6
frontmatter-reachable still invert). The reopen-trigger's ≥8/12 clause is met;
this phase tests the second clause (a tunable penalty).

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 reopen Option B (compare-doc verdict) | ✅ | — | reopened 2026-07-24; verdict amended, A stands, B authorised default-off only |
| M2 `[engine.hybrid] supersession_penalty`, default 0 = byte-identical | ✅ | 469 unit (+25) / 100 e2e | rank offset in fusion; **all goldens unchanged** — identity proven, not asserted; lean honours it too (parity law) |
| M3 calibrate across fixture+acme+orbit+synthetic | ✅ | 4 eval sets swept | **safe interval `[11, ∞)`** — 100% of *reachable* inversions recovered both corpora, zero hit@5 regression anywhere, hit@1 improves |
| M4 clean margin re-measure (Finding 2 unblock) | ✅ | orbit+acme, p0 vs p15 | **still empty after de-confounding** — confound was real but not the cause; fabrication = permanent no-model boundary |
| M5 ship gate — enable only with clean interval + Arpit sign-off | ✅ | 470 unit / 100 e2e | **Arpit approved: default 15.** Both "majority" framings surfaced first (all: orbit 62%/acme 33%; reachable: 100% both) |
| M6 ADR 0015, docs, archive `v0.26.0-*`, bump | ✅ | 470 unit / 100 e2e | ADR 0015; both compare docs closed; conformance run filed; version 0.26.0; **2 README honesty-claim edits proposed, NOT applied** |

**Both parallel items are now CLOSED by phase 8** — the README honesty claims are
applied and published, and the PyPI question resolved (0.24.0/0.25.0 were already
live; 0.26.0 is now too). **Deferred:** chunk-level dense codes (zero-overlap 1/6).

## Phase 8 — release v0.26.0 + follow-ups (handoff 0008) → shipped 2026-07-24

*Model: Sonnet (executed by Opus). The one irreversible step — the publish — was
human-gated and taken only on Arpit's explicit go.*

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 honesty edits + CLAUDE.md fold | ✅ | — | applied **before** the release was cut, so PyPI never rendered the old claim |
| M2 land phase 7 on a branch | ✅ | — | `feat/phase7-supersession-downrank`, commit `2455469`; nothing left loose on `main` |
| M3 PR + CI + merge | ✅ | 470 unit / 100 e2e | PR #44, **11/11 checks green** (linux·macos·windows × py3.11–3.14), merged `5ccd0a6` |
| M4 verify PyPI state | ✅ | — | **§10 Q1 moot** — 0.24.0 + 0.25.0 already live; nothing to back-publish |
| M5 publish (human gate) | ✅ | — | tag `v0.26.0` + Release on `5ccd0a6`; tag↔version guard + `twine --strict` + OIDC all passed |
| M6 verify the publish | ✅ | — | clean-venv `pip install fux-engine==0.26.0`; setup→ingest→find/ask/why all work; **PyPI README carries both corrected claims** |
| M7 trackers + retire frozen-wheel note | ✅ | — | orbit env now installs from PyPI; TEST-PLAN + orbit ANALYSIS corrected |
| M8 Part B — `zero_overlap_rescued` fix | ✅ | — | clean rescues only (**2 → 1**); new `zero_overlap_demoted` auto-detects the lexical-hit-lost case; orbit re-baselined deliberately |

**Two corrections this phase produced, both worth keeping:**

- **"0.25.0 is not on PyPI" was wrong.** `pip install` fails with *"no matching
  distribution"* on Python **< 3.11** because the package requires `>=3.11` — that
  error was misread as unpublished. Check `python -V` against `requires-python`
  first. The orbit numbers stand (same commit), only the justification was wrong.
- **A version string is not a build identity.** The first orbit re-baseline used a
  `0.26.0` wheel built *before* the M5 default flip (penalty still `0`) and would
  have pinned pre-release behaviour as the reference. Caught by reading the
  baseline diff and asking why a metric that should have moved did not.

## Phase 9 — fusion loses lexical top-5 hits (handoff 0009) → COMPLETE, no version bump

*Executed 2026-07-24 (Opus). **Outcome: ACCEPT — no engine change.** Docs +
investigation only; no version bump. The finding graduated to
`proposals/chunk-level-dense-codes.md`.*

**The filed framing was disproven** (M0). "Fusion is not monotone" is a
misdiagnosis: `1/(k + rank)` is strictly decreasing, so RRF **is** monotone in
per-list rank. The reported case reconciles to the exact specified arithmetic
(three lists — `bm25f`, `dense`, `dense_global`):

| doc | bm25f | dense | dense_global | computed | reported |
|---|---|---|---|---|---|
| hybrid #1 | 2 | 2 | 2 | 0.048387 | 0.04839 |
| hybrid #2 | 13 | 1 | 1 | 0.046485 | 0.04649 |
| **expected doc, #23** | **5** | **56** | **117** | **0.029655** | **0.02966** |

The correct document lost because its dense signal (**0.3297**) sits barely above
ADR 0010's **0.23–0.26 noise band** — two of three lists voted against it. That
is a *dense-quality* defect, faithfully propagated by fusion. The supersession
penalty is **not** implicated (doc is not superseded; the finding predates 0.26.0).

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M0 independently reconcile the RRF arithmetic | ✅ | 160/160, zero delta | reconciles incl. the penalty term — pre-work confirmed, phase proceeds |
| M1 correct the filed "non-monotone" wording | ✅ | — | orbit ANALYSIS + release-verification ANALYSIS + conformance index + harness label, all marked in place |
| M2 measure lexical-top-5-lost, all kinds × 4 eval sets | ✅ | 6 eval sets | **~4% realistic** (acme 2/55, orbit 2/53), ~offset by gains; synthetic 9–64% **unexplained**; 4 kinds affected, worst a `factual` lost from **lexical rank 1**; **penalty NOT implicated** (identical at 0 and 15) |
| M3 compare doc — guard vs accept vs fix-the-input | ✅ | — | written; **Arpit accepted ACCEPT** — no fusion change |
| M4 execute the verdict | ✅ | — | no ADR (no engine change); generalised the lab demotion check to all kinds (INFO, gains beside losses); filed `chunk-level-dense-codes` proposal as the finding's real owner |
| M5 close out | ✅ | 470 unit / 100 e2e | docs, archives (v0.26.0 release pair + phase9 pair), trackers |

**Outcome (M3/M4): ACCEPT.** It was indeed the zero-overlap/dense-quality finding
seen from the fusion side — measured, not asserted (see M2). No fusion change; the
finding now lives in `proposals/chunk-level-dense-codes.md`.

## Both orbit-run engine/suite findings — CLOSED
- ~~**Non-monotone fusion**~~ — **DISPROVEN 2026-07-24 (phase 9).** RRF is
  monotone; the demotion is correct arithmetic over a near-noise dense signal.
  The product question it raised (guard hybrid?) was **accepted** — no change;
  graduated to `proposals/chunk-level-dense-codes.md`.
- ~~**`zero_overlap_rescued` miscount**~~ — **FIXED 2026-07-24 (phase 8, M8).**
  The metric counted lexical hits as dense rescues (reported 2, actual clean 1).
  A clean rescue is now the *delta* — absent from lexical's top-5, present in
  hybrid's. `zero_overlap_in_top5` keeps the old looser number so nothing is lost.

## Deviations from spec

*(record any deliberate deviation from a handoff here, with the why and the ADR
that captures it — an empty section is the goal)*

- **0007 / the penalty knob lives in `[engine.hybrid]`, not a new `[retrieval]`
  table.** The handoff names `[retrieval] supersession_penalty`, but no
  `[retrieval]` section exists in `config.py` — every fusion parameter
  (`rrf_k`, `candidate_pool`) is already under `[engine.hybrid]`. A second
  top-level table would split ranking config across two places *and* imply the
  knob affects lexical retrieval, which it cannot (the penalty lives in fusion,
  so `--lexical-only` never reaches it). Approved by Arpit at M1. → ADR 0015.

- **0007 / the penalty is a rank offset, not an absolute RRF subtraction.** The
  handoff's `why` wording (`rrf penalised −X`) reads as a subtraction from the
  fused score. Chosen instead: a superseded chunk contributes
  `1/(k + rank + N)`. Rationale — the sweep unit ("ranks") is scale-free, so a
  magnitude calibrated on orbit carries to a 100k corpus, whereas a raw-score
  subtraction is entangled with `rrf_k` and the number of lists that fire.
  `N = 0` is exact identity either way. Approved by Arpit at M1. → ADR 0015.

- **0005 / `fux doctor`'s "Chrome for CDP" capability check is binary-presence
  only, not a live port probe.** The existing `tests/test_import_fence.py`
  forbids `import socket` (and `urllib.request`) anywhere outside `ingest/` —
  a standing rule that keeps the query/index/embed/state planes provably
  network-free. A live `localhost:<cdp_port>` reachability check would violate
  that fence from `src/fux/doctor.py`. `shutil.which()` over common Chrome/
  Chromium binary names (plus the macOS `.app` path) is the check instead;
  the actual CDP handshake is still only exercised at `fux ingest --web` with
  `render = "cdp"`, inside the fence. → ADR 0012.

- **0001 / `converted_at`:** derived from `SOURCE_DATE_EPOCH` (reproducible-builds
  convention) or the source file's mtime — never wall clock. The handoff lists
  `converted_at` as provenance *and* requires byte-identical double-ingest; a wall
  clock cannot satisfy both. Captured in ADR 0002.
- **0001 / example/CLI.md sketches:** the pre-build examples were aligned to
  as-shipped v1 (2026-07-21): setup wizard = one prompt per source type (no
  cache-location prompt — cache path is fixed in v1); ask/find scores are raw
  BM25F magnitudes, not 0–1; `--check` gained explicit new/missing annotations;
  answer JSON/citation shapes specified. The implementation was reworked to match
  the doc's normative shapes (`--check` advisory + `--strict`→2, JSON `path`/
  `line_start`/`line_end`/`heading_path`/`fidelity` keys, `[n]`+Sources answer
  citations, per-field explain tree, per-kind ingest summary).

- **0004 / df sidecar — SPEC AMENDED BY ARPIT, not deviated from (2026-07-21).**
  The M3 escalation found a real gap between two guarantees: DoD 7 promised
  rankings *identical* across profiles, but lean could only recover exact `tf`
  (by re-deriving text) — `df`, `n` and `avg_wlen` are corpus-level and were
  unavailable, so Bloom-derived `df` would have made "identical" mean
  "approximately". Arpit's call: **do not soften the guarantee; store the
  missing inputs exactly.** Handoff §C now specifies `state/df/XX.bin` and
  DoD 7 now requires a full-corpus lean-vs-full comparison test with the eval
  set as a belt. Implemented in `src/fux/state/df.py`; captured in ADR 0008.

  Two implementation choices inside that amendment, both recorded here:

  - **Per-field *sums* are stored, not averages.** Integers round-trip exactly
    (no float drift), and `avg_wlen = (h·ΣH + p·ΣP + b·ΣB) / n` can then be
    recomputed for *any* `[engine.bm25f]` weights without re-ingesting.
  - **Stats live in `df/_stats.bin`, not repeated per bucket.** The handoff says
    "one header record"; writing it into all 256 buckets would dirty every
    bucket whenever any document changed, defeating the sharding it exists for.
  - **Recomputed per ingest rather than delta-maintained.** The spec describes
    incremental upkeep (`df -= old, df += new`); the index is already fully
    loaded when the plane is written, so one pass is the same cost and cannot
    drift the way a running total can. Output bytes are identical either way.
  - **Hash collisions fail loudly.** Two terms sharing a u64 hash would merge
    their `df` and silently turn the exactness claim into an approximation, so
    the builder detects it and raises rather than absorbing it.

- **0004 / `web:` ids apply to *all* fetched pages, not just bulk-tier ones.**
  Handoff §B shows the `web:<slug>` id in the context of the bulk tier. Applying
  it only there breaks the three-way `--check`: state and index would key curated
  web docs by URL while the lock keys them by `web:` id, so every curated web doc
  would read as a permanent STATE-DESYNC. One id scheme everywhere; the URL rides
  along as provenance (JSON `url` field). → ADR 0008.

- **0004 / the operational manifest survives, relocated.** The handoff says
  `manifest.py` becomes `lock.py`. The lock is the committed *ledger* and
  deliberately carries only the fields §B lists — but ingest and query still need
  cache path, line offset and title. Those live on in
  `.fux/index/manifest.jsonl`, inside the gitignored runtime plane, written in
  the same scope as the lock. Git carries the recipe; the runtime keeps its
  joins. → ADR 0008.

- **0004 / `fux answer` has no state-only mode** *(superseded at M7 — kept for
  the trail)*. This held while a clone could only answer at doc level. Once the
  df sidecar landed, the lean path re-derives candidates and produces real
  line-anchored passages, so `answer` works on a fresh clone with full
  citations. The decline path survives only for the doc-level fallback, where
  sources are genuinely absent. → ADR 0011.

- **0004 / a fresh clone answers *exactly*, not at doc level (M7).** DoD 2 asks
  for doc-level answers from committed state; the df sidecar makes something
  strictly better possible, so a clone with its sources present now returns the
  same rankings *and scores* as the full profile. Doc-level ranking became the
  honest fallback for when sources cannot be re-derived (crawled corpora, or a
  clone without its documents). Exceeding a DoD is still a change to committed
  behaviour, so it is recorded here and reflected in example/CLI.md. → ADR 0011.

- **0004 / `auto` requires a size threshold, not just re-derivability (M7).**
  §G defines `auto` as "lean when every source in a tier is re-derivable". Taken
  literally that makes lean the default for *every* local repo, silently
  trading query latency for a footprint win that does not exist below a few
  thousand documents — and changing behaviour for every existing small corpus.
  `auto` now additionally requires `[index] lean_threshold` documents
  (default 10 000); `profile = "lean"` remains available explicitly at any
  size. → ADR 0011.
