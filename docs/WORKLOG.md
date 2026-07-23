# Worklog — the running session handoff

*A rolling, per-exchange record so a new chat can pick up cold. Think of each entry
as a mini exit-interview for the conversation that produced it: what was asked, what
was done, what was decided, and the exact next step. **Both Cowork and Claude Code
must append to this** at the end of every substantive exchange (CLAUDE.md binds you
to it). Newest entry on top. Keep entries short and true; this is continuity, not a
diary.*

**Entry format**

```
## YYYY-MM-DD — <one-line title>  ·  <Cowork | Claude Code>
- **Asked:** what the human requested.
- **Did:** what actually changed (files, decisions).
- **Decided / open:** verdicts reached, and what's still awaiting a call.
- **Next:** the single immediate next step.
```

---

## 2026-07-24 — phase 7 reviewed → release handoff (0008) packaged  ·  Cowork
- **Asked:** one handoff+prompt for all pending items — first commit/push/publish
  everything built, then the next steps.
- **Did:** wrote handoff+prompt `0008-release-and-followups` (→ **Sonnet**, publish
  human-gated). Grounded it in the real state: phase 7 is **staged uncommitted on
  main**, `__version__` already 0.26.0, tags through v0.25.0, publish is
  release-triggered (tag↔version guard + twine --strict + OIDC), and ~nothing since
  0.23.0 is on PyPI. Sequenced so the two approved README honesty edits + the
  CLAUDE.md fold land **before** the release is cut (PyPI must not render the old
  "cannot hallucinate" claim). Part B = fix the `zero_overlap_rescued` suite
  miscount. Part C (scoped, not executed) = the non-monotone fusion finding (Opus,
  own handoff) + chunk-level dense codes.
- **Decided / open:** Q1 — publish 0.26.0 only (recommended; supersedes 0.24/0.25,
  carries corrected README) vs back-publish older versions. Q2 — the go/no-go on
  the irreversible release (human-gated at M5).
- **Next:** run 0008 in Claude Code; it pauses at M5 for Arpit's publish go.

## 2026-07-24 — phase 7 built: supersession down-rank shipped enabled (v0.26.0)  ·  Claude Code
- **Asked:** execute handoff 0007 — the default-off down-rank penalty, calibrate
  it across four eval sets, re-measure the runner-up margin, gated on M1
  (Arpit reopening Option B) and M5 (his sign-off before enabling).
- **Did:**
  - **M1** — Arpit reopened B. Amended the supersession compare-doc verdict
    (A stands; B authorised default-off), updated INTERVIEW + IMPLEMENTATION.
  - **M2** — `[engine.hybrid] supersession_penalty` as a **rank offset** in RRF
    (`1/(k+rank+N)`), applied to the deterministic frontmatter-marked set only.
    Lean honours it too (parity law). Landed at `0` with every golden unchanged.
  - **M3** — swept fixture/acme/orbit/synthetic 1k/5k/10k. **Safe interval
    `[11, ∞)`** to 500; zero hit@5 regression on any gate, any value, any kind;
    hit@1 improves (orbit .566→.698, acme .491→.564). **100% of
    frontmatter-reachable inversions recovered** (orbit 5/5, acme 3/3) — every
    residual one is unmarked. Harness validated against orbit's published
    numbers before sweeping.
  - **M4** — re-measured the margin de-confounded. **Still empty.** The confound
    was real (orbit's minimal `factual` question improved) but not the cause: a
    `how-to` question sits at 1e-05 before *and* after; acme is identical, its
    minimum a `cross-doc` question — the legitimate-consensus mode the compare
    doc predicted years of reasoning ago.
  - **M5** — surfaced both readings of the "majority" gate (all inversions:
    orbit 62% ✅ / acme 33% ❌; reachable: 100% both). **Arpit chose enable at 15.**
  - **M6** — ADR 0015, both compare docs closed out, conformance run filed,
    README/CHANGELOG/PLAN/GLOSSARY/TOML/registry updated, handoff+prompt archived
    as `v0.26.0-*`, version bumped. 470 unit + 100 e2e green.
- **Decided / open:**
  - **Fabrication is now a documented product boundary**, not an open defect —
    three no-model discriminators refuted across two corpora, one de-confounded.
    The decline-floor reopen-trigger is **retired**; no fourth mechanism proposed.
  - **Two README honesty-claim edits are PROPOSED, not applied** (positioning is
    Arpit's call): the "never generative, so it cannot hallucinate" line and the
    "measured, unfixed limit" phrasing in § Honest limits, both of which M4
    turned from provisional into permanent.
  - **Open (Arpit, unchanged):** release to PyPI — 0.25.0 was never published and
    0.26.0 now sits on top of it.
- **Next:** Arpit rules on the two README wording proposals; then open the
  v0.26.0 PR and read `gh pr checks` before merging (no required checks on main).

## 2026-07-24 — orbit run reviewed → phase 7 packaged (down-rank)  ·  Cowork
- **Asked:** review the second-corpus (orbit-fulfillment) output; what next.
- **Did:** synthesized the generalization verdict — all three acme findings
  reproduce on an independent domain (staleness 8/12 meeting the ≥8/12 gate;
  fabrication 0/4 with **both** no-model mechanisms refuted; zero-overlap 1/6).
  Surfaced the key coupling: the margin refutation is **confounded** — smallest
  "answerable" margins come from superseded-twin ties, so Finding 1's fix is the
  prerequisite to a fair Finding 2 verdict. Wrote handoff+prompt
  `0007-supersession-downrank` (→ v0.26.0, **Opus**): default-off penalty knob,
  four-eval-set calibration, and the margin re-measurement it unblocks.
  Pre-registered phase 7 in IMPLEMENTATION.md; filed the two orbit engine/suite
  findings (non-monotone fusion; zero_overlap_rescued miscount).
- **Decided / open:** the anti-B argument weakened — the penalised set is
  deterministic (author frontmatter, 6/6 surfaced), only the magnitude is tuned.
  **M1 gate:** Arpit must reopen Option B before Claude Code starts.
  Parallel Arpit calls: release v0.25.0 to PyPI (committed af374f0, unpublished);
  reframe the "never fabricate" claim if M4 confirms the no-model boundary.
- **Next:** Arpit reopens B (or not); phase 7 executes in Claude Code.

## 2026-07-24 — second realistic corpus (orbit-fulfillment): all three findings generalize  ·  Claude Code

- **Asked:** build a second realistic ~1k-doc corpus in a domain far from fintech and
  determine whether the three acme findings generalize; measure the deferred
  runner-up **margin check** directly.
- **Did:**
  - New generator `fux-lab/shared/generate/make_orbit.py` (warehouse/order-fulfillment,
    944 files, 50 hand-written hero docs, 57 typed eval pairs, deterministic). Marker
    split **known by construction**: 6/12 superseded docs carry `superseded_by:`.
    Unanswerable vocabulary verified absent (0 files for crypto/drone/graphql/cafeteria).
  - New measurement tooling: `shared/regress/margin.py` (top vs runner-up separability)
    and `shared/regress/floor_sweep.py` (empirical `min_confidence` curve over the full
    eval set).
  - Filed `docs/conformance/2026-07-24-orbit-fulfillment/` (report + ANALYSIS + 10
    evidence files); updated `conformance/README.md`, both reopen-triggered compare docs,
    DOC-REGISTRY; updated `fux-lab/TEST-PLAN.md` §1/§7.
- **Decided / open:**
  - **Staleness generalizes: 8/12 inversions — the Option-B ≥8/12 gate is MET.** 6/6
    frontmatter-reachable superseded docs carry the v0.25.0 annotation and **5 of 6
    still outrank their replacement**. Mechanism: current doc wins BM25F outright in 6/8
    cases and loses on a dense edge as thin as 0.0006 cosine, which RRF flips.
    **The gate's second clause (a tunable penalty) is NOT tested — B stays deferred.**
  - **Fabrication generalizes: 0/4.** Absolute floor **empty** (needs ≥0.121, false-declines
    start at 0.105) and the **margin check is refuted — empty AND inverted** (unanswerable
    margins exceed the smallest answerable ones; the smallest answerable margins come from
    stale/current ties, so Finding 1 manufactures Finding 2's false-positive mode).
    Recorded as a **documented product boundary**, not an open defect.
  - **Zero-overlap generalizes: 1/6 clean dense rescues**; hybrid also *demoted* a lexical
    rank-5 hit out of top-5 (fusion is not monotone).
  - **v0.25.0 features confirmed on independent data:** annotation surfaces 6/6; the
    permissive `min_confidence` default re-confirmed as the only zero-false-decline value.
  - **Caveat, flagged prominently:** `fux-engine==0.25.0` **is not on PyPI** (merged as
    `af374f0`, never released), so the run used a locally-built wheel driven strictly as a
    black box. Numbers describe that commit, not a published artifact.
- **Next:** run the **penalty-tuning experiment** for supersession down-ranking, gated
  jointly on the fixture gate, acme, orbit and the synthetic tiers, graduating via an ADR.

---

## 2026-07-23 — phase 6 built end-to-end, v0.25.0 shipped  ·  Claude Code
- **Asked:** execute the `0006-trust-currency-prompt.md` paste-ready prompt
  (supersession awareness + `answer` confidence floor).
- **Did:** confirmed M1's gate directly with Arpit (both compare docs were
  still `status: proposed` on disk despite an earlier Cowork worklog entry
  assuming acceptance) — accepted Option A on both, plus the `fux-query` skill
  update, via explicit questions. Built M2–M5 incrementally, both suites green
  at every milestone: supersession parsing/persistence/resolution
  (`index.build_index::_supersession_meta`/`_resolve_supersession`,
  `state.DocState.superseded_by`, sqlite `format_version` 2→3), `find`/`ask`
  annotation (ordering + all 4 lexical goldens unchanged), `[answer]
  min_confidence` mechanism, `answer.prefer_current`/`best_confidence` shared
  with `why`'s new decline explanation. Delegated the two judgment-heavy
  real-corpus measurements to a background Opus subagent, resumed once to
  reuse its editable-install acme environment rather than rebuild it: (1)
  confidence-floor calibration against all 5 gates — **no value clears both
  the unanswerable and answerable gates; shipped `min_confidence = 0.0`**; (2)
  supersession recovery re-measurement — **5/12 markers, 3/9 inversions
  marked, 1 fully corrected + 1 de-cited at the `answer` level, 6
  unmarked/unreachable**. Wrote ADR 0013 + 0014, filed both conformance runs,
  graduated both source proposals to `docs/archive/`, archived the
  handoff+prompt as `v0.25.0-trust-currency-*`, updated CHANGELOG/README
  (What's new + Status + Honest limits)/PLAN §7-8/INTERVIEW/GLOSSARY/
  DOC-REGISTRY, bumped version 0.24.0→0.25.0. 444 unit + 100 e2e green
  throughout.
- **Decided / open:** both the supersession recovery and the confidence-floor
  fix are honestly **partial** — recorded plainly in every doc touched, not
  papered over. The CLAUDE.md edit (version line + phase-6 hard-won-knowledge
  section) was proposed for review per the handoff's explicit instruction, and
  Arpit approved it in-session — applied. No phase 7 is pre-registered.
- **Next:** phase 6 is fully closed. Candidates for phase 7 (not yet scoped):
  an absolute cross-query confidence signal for `answer` (ADR 0014 F1/F2), or
  Finding 2's deferred chunk-level dense codes (zero-overlap rescue).

## 2026-07-23 — phase 6 packaged + architecture diagram  ·  Cowork
- **Asked:** review the acme run in plain language; then plan/handoff/prompt the
  fixes; then a flow diagram of how Fux works, linked into the README.
- **Did:** wrote two compare docs (`supersession-handling`, `answer-decline-floor`)
  — both **accepted** by Arpit (annotate-not-down-rank; absolute floor, no margin).
  Wrote handoff+prompt `0006-trust-currency` (→ v0.25.0, **Model: Opus**),
  pre-registered phase-6 rows in IMPLEMENTATION.md, updated PLAN §7/§7a/§8.
  Added `docs/architecture-flow.mermaid` (validated: parses clean via mermaid+jsdom)
  and embedded it as a fenced `mermaid` block in README § How it works (renders on
  GitHub; ASCII sketch kept in a `<details>`). Bumped DOC-REGISTRY.
- **Decided / open:** M1 gate cleared. Skill-update open question → **yes**, update
  `fux-query` skill to read the `superseded` field (descriptive, not prescriptive).
  M4 calibration may legitimately return "no value satisfies all five gates."
- **Next:** phase 6 is executing in Claude Code (M2 in progress — parse+persist,
  with the `superseded` flag required in `.fux/state/`, not just the gitignored index).

## 2026-07-22 — acme-payments realistic run settles A vs B → B  ·  Cowork
- **Asked:** build a ~1 000-doc corpus with genuine prose diversity and run the
  conformance suite to settle whether the hybrid degradation is an engine defect
  (A) or a synthetic-corpus artifact (B). New environment inside fux-lab; pin 0.23.0.
- **Did:** authored `fux-lab/shared/generate/make_repo.py` (deterministic, stdlib,
  bespoke ADRs/runbooks/postmortems/RFCs/guides/API refs + 59 typed eval pairs +
  12 stale-vs-current pairs w/ 3 marker styles + 6 zero-overlap + 4 unanswerable);
  scaffolded `fux-lab/acme/` (VERSION 0.23.0); extended `shared/regress/run.py`
  with **additive, data-guarded** staleness-precision + typed-unanswerable-decline
  checks (no-op on synthetic tiers). Filed
  `docs/conformance/2026-07-22-acme-payments/` (report + ANALYSIS + evidence),
  indexed it, updated the proposal to **resolved**, split two new proposals,
  corrected the README/CHANGELOG "same rankings *and scores*" wording.
- **Decided / open:** **B — the 4× hybrid collapse is a corpus artifact.** On
  realistic prose hybrid hit@5 recovers .182→.855 (parity with lexical .873). The
  RRF reopen-trigger is answered: no fusion/reranker change warranted. **Three new
  real findings** the fixture gate missed: staleness 9/12 inversions (superseded
  doc outranks current), zero-overlap dense rescue 0/6 clean (even undiluted),
  honest-decline 0/4 on well-formed unanswerables (fabricates with sources).
  why/how-to/factual hit@5 = 1.00. Scorer matcher hand-verified before trusting
  numbers. No engine behaviour change shipped (one corpus = evidence, not proof).
- **Next:** graduate `staleness-ranking-ignores-supersession` (ingest-time
  supersession flag) and `honest-decline-well-formed-queries` (absolute-confidence
  floor) via compare docs + ADRs, each confirmed on a second realistic corpus.

## 2026-07-22 — conformance evidence gets a durable home (docs/conformance/)  ·  Cowork
- **Asked:** capture every test run's report + evidence into the fux repo in a
  dedicated place for analysis and improvement, and put the practice in CLAUDE.md
  so it is never missed.
- **Did:** created `docs/conformance/` with a README (the convention) and this
  run's folder `2026-07-22-scaling-1k-5k-10k/` (report.md, 5k.md, 10k.md,
  ANALYSIS.md, evidence/). ANALYSIS.md turns the numbers into two **measured**
  failure mechanisms + ranked fux improvements. Added a binding CLAUDE.md section
  "Conformance runs — file every one", a Layout entry, and a DOC-REGISTRY row.
- **Decided / open:** diagnosis (via 0.24.0 `fux why`/`--debug=trace`, retrieval
  byte-identical to 0.23.0): (1) zero-overlap miss = doc-vector dilution — correct
  doc at dense cosine 0.17-0.27, hamming ~110-126/256, outside the 500-prefilter
  → chunk-level dense codes is the structural fix; (2) hybrid demotion = RRF has
  no dense-quality floor — lexical rank 3/5 pushed to fused rank 6/10 because
  `dense_global_rescues=200` injects a near-random full list over near-identical
  prose. fux's trace is strong but mislabels fused lines `[lexical]` and omits
  per-doc source ranks — top observability win is a fusion trace. Ranking changes
  (admission threshold, confidence-weighted RRF, size-aware default) stay proposal
  candidates gated on the acme-payments run.
- **Next:** wire the capture into `fux-lab/shared/regress/run.py` (archive `fux why`
  + trace + doctor per run automatically); then run acme-payments (A-vs-B discriminator).

## 2026-07-22 — conformance scaling curve: 5k + 10k tiers run  ·  Cowork
- **Asked:** run the fux-lab conformance suite at 5k and 10k, compare against the
  1k baseline, produce a scaling curve, and file it per CLAUDE.md.
- **Did:** ran 5k and 10k (fux-engine 0.23.0, `--accept-baseline`) plus a
  same-machine 1k timing anchor. All in the cloud sandbox — the device VM has no
  network and Python 3.10 (< 3.11), so the pinned engine cannot install there;
  byte-budget and quality metrics are deterministic (a cloud 1k re-run was
  byte-identical to the Mac baseline), only wall-clock differs by machine. Wrote
  `fux-lab/{5k,10k}/results` + `baselines` and
  `fux-lab/results/2026-07-22-scaling-1k-5k-10k.md`; updated
  `docs/proposals/hybrid-degrades-at-scale.md`, `docs/DOC-REGISTRY.md`, `docs/INTERVIEW.md`.
- **Decided / open:** the 1k "hybrid 4x worse" gap is NOT stable — it CLOSES with
  scale (hit@5 lexical/hybrid 4.49x -> 2.00x -> 1.54x) because lexical collapses
  toward hybrid (.818 -> .385 -> .192) while hybrid stays flat (~.13-.19). Leans
  reading B (corpus artifact) but does NOT settle A vs B — same generator.
  Zero-overlap rescue 0 at every tier, now well-powered (0/14 at 10k) -> narrows
  ADR 0010's rescue claim. Per-doc budgets flat/declining (no superlinear term).
  Query latency linear from the start (~0.20s + 0.16s per 1k docs), no flat
  regime -> corroborates ADR 0011. Fresh-clone tail-score divergence reproduces at
  all scales (README/CHANGELOG "same rankings and scores" still inaccurate). Only
  FAIL is the known zero-overlap rescue. No engine change made — mitigations stay
  candidates until the A-vs-B experiment resolves.
- **Next:** run the acme-payments realistic corpus
  (`fux-lab/prompts/build-realistic-repo.md`) — the discriminator for A vs B.

## 2026-07-22 — phase 5 built: debug & observability (v0.24.0) · Claude Code
- **Asked:** execute handoff 0005 exactly — `[debug]` in fux.toml, a stdout-pure
  emitter, `fux doctor`, `fux why`, the `fux-debug` skill, M1→M6 with the
  stdout-purity gate written before any instrumentation existed.
- **Did:** all six milestones, green throughout, IMPLEMENTATION.md updated per
  milestone (never batched):
  - **M1** `DebugParams`/`_parse_debug` in `config.py` (wired via
    `debug.apply_config()` inside `load()` — one config-load call site, not one
    per command); `src/fux/debug.py` (`dbg()`/`timer()`/`is_enabled()`,
    flag>env>toml>off precedence, redaction, max_bytes truncation, unwritable-
    output fallback); `--debug[=LEVEL]` global CLI flag; `tests/conftest.py`
    (autouse debug-state reset — needed once `load()` had a global side effect);
    e2e stdout-purity + stderr-reproducibility tests.
  - **M2** `dbg()`/`timer()` at walk/convert/chunk/index/lock/state/graph
    (ingest side) and query/lexical/dense/graph/answer/hooks/web (query side);
    trace-level content previews gated on `redact=false`; caught and fixed a
    latent flaky-test risk (ingest's own `Elapsed: N.Ns` stdout line is
    wall-clock, unrelated to debug — normalized in the test, not the product).
  - **M3** `src/fux/doctor.py` — 7 groups, `--json`, exit 0/1; zero-match
    `[sources]` globs surfaced loudly; self-test ingests a canary doc in a
    scratch temp dir and proves ingest→index→query→citation end to end.
  - **M4** `src/fux/query/why.py` — corpus-presence → chunks → lexical → dense →
    graph → one verdict sentence; dense/graph evidence read from
    `kernel.retrieve()` itself so `why` can't disagree with a real query.
  - **M5** `fux-debug` skill in `agents/generate.py::_SKILLS`; one-line
    escalation pointer added to `fux-query`/`fux-ingest`; `fux setup --skills`
    now writes 3 skills.
  - **M6** `docs/example/DEBUG.md` new (7 worked failures); CLI/TOML/SETUP/
    SKILLS/GLOSSARY/DOC-REGISTRY/PLAN/INTERVIEW updated.
  - **Close-out:** ADR 0012 (answered all 4 open questions); CHANGELOG entry +
    README mirror + command list; archived the handoff+prompt pair as
    `docs/archive/v0.24.0-debug-observability-*.md` (status: implemented, ADR
    linked); bumped `__version__` → 0.24.0. Suites: **417 unit + 100 e2e**
    (+1 gated skip).
- **Decided / open:** `fux doctor`'s "Chrome for CDP" check is binary-presence
  only (`shutil.which`), not a live port probe — `import socket` outside
  `ingest/` trips the standing `test_import_fence.py` rule, and keeping that
  fence mattered more than one check's completeness (recorded in ADR 0012 and
  IMPLEMENTATION.md's Deviations). `why --all` deliberately not built (single-
  doc only, cost-scoped) — open for a future proposal if a real need appears.
- **Next:** none pending for phase 5. Next phase's head is still query-at-scale
  (ADR 0011) — the 100k-corpus ~10s query latency, unfixed.

---

## 2026-07-22 — release v0.23.1 (docs & examples) · Claude Code
- **Asked:** commit, push, and publish.
- **Did:** on main → branched `release/v0.23.1-docs-examples`. Confirmed all
  changes since 0.23.0 are docs/comments/test-path only (no engine change), so
  Arpit chose a **0.23.1 patch**. Bumped `__init__` → 0.23.1, added the CHANGELOG
  entry, mirrored it into README § What's new, updated CLAUDE.md identity + the
  smoke-test version assertions. Pre-flight green: **365 unit tests**, `python -m
  build`, `twine check --strict` both artifacts PASSED as 0.23.1. Committed the
  full working tree (this session's doc reorg + example bundle, plus pre-existing
  README/CHANGELOG work and the untracked `handoff/0005` debug-observability
  planning pair). Pushed → PR → merge → `gh release v0.23.1` → PyPI publish.
- **Decided / open:** patch, not minor — the wheel is functionally identical to
  0.23.0; the example bundle is docs, not a shipped feature. `handoff/0005` rode
  along in the same commit (it was already in the tree, registry-referenced).
- **Next:** none for this release; 0005 (debug & observability) is the next build.

---

## 2026-07-22 — three new example docs: SETUP / SKILLS / API · Claude Code
- **Asked:** add examples for (1) CLI setup variants + hooks installation,
  (2) skill usage, (3) the Python API creating a file in fux from another script.
- **Did:** created `docs/example/{SETUP,SKILLS,API}.md` (ALL-CAPS, no
  frontmatter). **Every block is verified against the real v0.23.x
  implementation**, not invented — ran `fux setup -y --agents --skills --hooks`
  on a scratch dir (captured the exact 8-file output + idempotent re-run),
  dumped the real `.claude/settings.json` and `.kiro/*.hook`, exercised
  `fux hook prompt-submit/session-end` I/O, and wrote+ran a real
  `find_root → load → ingest_paths → load_searcher.search` script (create file →
  `new=2…`, re-run → `unchanged`, `ingest --check` → `sha mismatch — re-ingest`).
  Corrected the `fux ask --json` shape in SKILLS.md after checking live output
  (`path`/`line_start`/`line_end`/`heading_path`/`fidelity`/`hybrid`, structured
  `corpus`, `engine`). Wired all five into `example/index.md`, `docs/index.md`
  (bundle line + OKF exemption), DOC-REGISTRY (3 rows), CLAUDE.md layout.
- **Decided / open:** grounded the API doc on the CLI's own entrypoints
  (`fux.config`/`fux.ingest`/`fux.index`) — no private path — so the example
  can't drift from the shipped CLI. Nothing open.
- **Next:** none — `example/` now has CLI, TOML, SETUP, SKILLS, API.

---

## 2026-07-22 — correction: fux-toml.md *is* the example → example/TOML.md · Claude Code
- **Asked:** the separate `example/fux.toml` I created was wrong — `fux-toml.md`
  itself is the example and should have been the thing moved into `example/`.
- **Did:** `rm docs/example/fux.toml`; `git mv docs/fux-toml.md
  docs/example/TOML.md` (name confirmed with Arpit — matches the ALL-CAPS
  example-dir convention set by CLI.md); stripped its frontmatter; fixed its
  now-deeper relative links (CLI.md became same-dir). **Updated the real code
  dependency:** `tests/test_config.py` reads this doc to assert the fenced
  example against the shipped dataclass defaults — repointed both paths to
  `docs/example/TOML.md` (16 config tests green). Merged the two DOC-REGISTRY
  rows into one; updated index.md (bundle line + OKF exemption list), CLAUDE.md
  layout, `example/index.md`, and `proposals/knowledge-substrate.md`.
- **Decided / open:** `example/` now holds exactly two maintained contracts —
  `CLI.md` (command I/O) and `TOML.md` (annotated config). There is no separate
  runnable `fux.toml` sample; the fenced block inside TOML.md is the copy source
  and the parser-asserted one. Nothing open.
- **Next:** none.

---

## 2026-07-22 — ALL-CAPS core docs + examples bundle · Claude Code
- **Asked:** `worklog.md`→`WORKLOG.md`; `fux-plan.md`→`PLAN.md`;
  `model-handoff-interview.md`→`INTERVIEW.md`; move `cli-examples.md` to a new
  `docs/example/` dir as `CLI.md`; add an example `fux.toml` there too.
- **Did:** `git mv` all four; **stripped YAML frontmatter** from WORKLOG/PLAN/
  INTERVIEW/CLI per the ALL-CAPS = no-frontmatter convention (they join
  IMPLEMENTATION/GLOSSARY/DOC-REGISTRY). Fixed CLI.md's six internal relative
  links for the extra dir depth. Created `docs/example/fux.toml` (complete
  copy-paste config, v0.23.x keys from `config.py`) + `docs/example/index.md`
  (OKF per-dir index). Rewired **every** live reference — README, CLAUDE.md
  (prose + layout block + convention list + log.md line), index.md, GLOSSARY,
  DOC-REGISTRY (+2 new rows), INTERVIEW, `adr/0002`, `adr/0011`,
  `compare/cli-surface`, `fux-toml.md`, `proposals/*`, and the doc-pointer
  comments in `src/fux/query/{statequery,verbs,api}.py` + two tests. Verified
  all relative `.md` links across docs/README/CLAUDE/DOGFOOD resolve.
- **Decided / open:** ALL-CAPS files carry **no** frontmatter (documented rule) —
  so promoting these four to ALL-CAPS dropped their OKF `type`; the convention
  explicitly exempts entry-point/tracker files, and index.md's OKF note was
  updated to say so. `fux-toml.md` stays the annotated *reference* (prose per
  key); `example/fux.toml` is the runnable example — both maintained. Archive
  prose naming old paths left as historical record; broken links I introduced
  (WORKLOG hist + one archived handoff) repointed to resolve. Nothing open.
- **Next:** none — new handoffs still use `NNNN-name.md` in flight.

---

## 2026-07-22 — archive docs renamed to release-version keys · Claude Code
- **Asked:** archive documents should be named by release version, not the
  in-flight `NNNN` index.
- **Did:** `git mv` all 8 archived handoff/prompt pairs to `vX.Y.Z-name.md`
  (0001→v0.20.0, 0002→v0.21.0, 0003→v0.22.0, 0004→v0.23.0); master-prompt kept
  unversioned (spans v0.20–v0.22, per Arpit). Rewired every live-doc link
  (`fux-plan.md` table + §7/§8, `adr/0008`, `proposals/knowledge-substrate.md`)
  and the `blocked_by:` frontmatter inside the archived docs. Folded the naming
  rule into CLAUDE.md (Archive section), refreshed `archive/README.md` with a
  shipped-artifacts index, bumped DOC-REGISTRY rows (CLAUDE/fux-plan/handoff/
  archive). Verified all `archive/*.md` markdown links resolve via a script.
- **Decided / open:** left historical prose that names `docs/handoff/000X-…`
  (worklog entries, archived-doc body instructions, IMPLEMENTATION.md:110's
  measured doc id) untouched — those record the paths that existed at build time;
  rewriting them would falsify the record. Nothing open.
- **Next:** none — future handoffs use `NNNN-name.md` while in flight, archive as
  `vX.Y.Z-name.md` on ship.

---

## 2026-07-22 — rename tracker to IMPLEMENTATION.md (git case fix) · Claude Code
- **Asked:** convert implementation.md to IMPLEMENTATION.md and update wherever
  necessary.
- **Did:** the file on disk was already `IMPLEMENTATION.md` but git still tracked
  it lowercase (case-preserving macOS FS) — `git mv -f docs/implementation.md
  docs/IMPLEMENTATION.md` so git agrees. Fixed the one stale live prose reference
  (`model-handoff-interview.md` §200k benchmark). Verified the maintained docs
  already used the uppercase name: CLAUDE.md, `docs/index.md`, `DOC-REGISTRY.md`.
- **Decided / open:** left lowercase refs in `archive/`, `docs/archive/`, ADR
  0002, and prior worklog entries — those are immutable/historical records, not
  live docs. Nothing open.
- **Next:** none — casing is now consistent across the live doc set.

---

## 2026-07-22 — v0.23.0 merged to main and published to PyPI · Claude Code
- **Asked:** merge everything to main and publish.
- **Did:** pre-flight (wheel builds 7.04 MB, model bundled, `twine check --strict`
  passes, clean-install smoke test) → pushed `feat/phase4-knowledge-substrate` →
  **PR #38** → full matrix green (linux 3.11–3.14, macOS 3.11/3.14, **Windows
  3.11/3.14**) plus both required checks (`fux gate`, `ai-review`) → merged →
  release **v0.23.0** → publish workflow uploaded both artifacts (200 OK).
  Verified from PyPI on a clean Python 3.12 venv: install, ingest (writes
  `fux.lock` + `.fux/state/`), `ask`, `path`, `explain`, **zero runtime deps**.
- **Decided / open:** two verification stumbles worth remembering, neither a
  product defect. (1) The first "clean install" check ran on the system Python
  **3.9**, below the supported floor — a local wheel install succeeded there and
  looked like a pass, so it proved less than it appeared; re-run on 3.12.
  (2) `pypi.org/pypi/.../json` served a **cached** response reporting 0.22.1 as
  latest for a minute after a successful upload — the publish job log (200 OK +
  "View at" URL) is the authority, not the JSON API. Don't conclude a publish
  failed from that endpoint alone.
- **Next:** unchanged — **query-at-scale** is the head of phase 5: score from
  `postings` by term instead of loading every row (~10 s at 100k today; table,
  index and exact corpus stats already exist). Scoped in ADR 0011.

## 2026-07-22 — phase 4 complete: knowledge substrate shipped at v0.23.0 · Claude Code
- **Asked:** three rulings (integer token-sums approved as amendment; early-return
  judgment approved; state budget → measure at M8 before optimizing), then
  M6 → M7 → M8 → close-out, with a discipline check first.
- **Did:** discipline check passed (M1–M5 already committed as clean milestone
  commits; tracker rows ✅ with counts) except one reconcile — `fux path`'s
  renderer did not match the format cli-examples had specified first, so the
  **code was changed to follow the doc**, and the multi-path form documented.
  - **M6 PPR-lite:** constants as specced; seed-*rank* personalization; graph
    joins RRF as a fourth list. Guard: fusion skipped for node seeds, since a
    neighbour's passage among a document's own would misattribute it.
  - **M7 profiles:** lean = a Searcher over re-derived candidates with the df
    sidecar injected, so the kernel never learns its profile. Mid-corpus switch
    (full→lean) keeps rankings **and** scores — **mutation-verified non-vacuous**
    (making `lean_searcher` return None fails the test). LRU uses a monotonic
    counter, never a clock. `db pull` sha-verifies and refuses mismatches.
  - **M8:** committed generator + harness; 100k measured. **state 22.96 MB
    (≤30 ✓), df 0.92 MB (≤5 ✓)**, db 1081 MB (77% of §8b), FuxVec scan **54 ms
    < 150 → IVF not built**, ingest 566 s. Relational eval added for
    explain/graph/path.
  - **Close-out:** ADRs 0008–0011 (0010's flagged citations **verified**, not
    asserted); full docs pass; 0004 pair archived; **v0.23.0**.
  - Suites **172+29 → 365 unit + 71 e2e**; eval hit@5 **1.000**; `--lexical-only`
    still exactly 0.762/0.952/0.833.
- **Decided / open:** two behaviour changes recorded in Deviations — a fresh
  clone now answers *exactly* (better than DoD 2's doc-level, so the docs were
  corrected to match), and `auto` gained `lean_threshold` because §G read
  literally would have flipped every small repo to lean silently.
  **The M3a size warning was wrong and is kept next to the measurement that
  corrected it** (351 B/doc projected from this repo's adversarial docs vs
  230 B/doc actual); per the ruling, no zlib change was made.
  **⚠ The honest finding:** at 100k a query takes ~10 s — `postings` is stored
  and indexed but never read at query time, so the whole index still loads into
  memory. Phase 4 solved *storage* at scale, not *query* at scale.
- **Next:** **query-at-scale** — score from `postings` by term instead of
  loading every row (table, index and exact corpus stats already exist).
  Scoped in ADR 0011; it is the head of phase 5. Branch
  `feat/phase4-knowledge-substrate` (10 commits) is ready for PR to main.

## 2026-07-22 — phase 4 M3a–M5: df sidecar, kernel, FuxVec · Claude Code
- **Asked:** Arpit's DoD-7 ruling (Option B — exact df sidecar, guarantee does **not**
  soften), commit M1–M3 first, then continue M4→M8.
- **Did:** committed the backlog as three clean commits (spec docs / M1–M3 / sidecar),
  then landed M3a, M4, M5 — each green, each committed.
  - **M3a df sidecar** (`state/df/`): term hashes sharded by hash low byte,
    delta-encoded + varint df; `_stats.bin` holds total_docs/total_chunks and
    per-field token **sums** (integers round-trip exactly, and `avg_wlen`
    recomputes for any weights without re-ingesting). `Searcher` gained an
    optional `stats` injection — scoring math untouched, only input provenance
    changes. Parity is enforced, not asserted: every term in the vocabulary,
    scored over a strict *subset* (where subset-derived idf would diverge),
    matches full exactly — and **mutation-tested** (removing the injection fails
    both parity tests). Collisions raise rather than silently merging df.
  - **M4 kernel:** `retrieve() -> ResultGraph` is now the only retrieval path;
    ask/find/answer are projections, and explain/graph/path are new ones.
    `explain` = ask seeded by a node (its own `top_terms` become the query), so
    there is genuinely one code path. Edges now persist in the JSON store too.
  - **M5 FuxVec:** full-corpus Hamming prefilter → exact int8 rerank →
    `dense_global` as a third RRF list. **Gate beats v0.22 hybrid:** hit@1
    .762→.810 · hit@5 .952→**1.000** · MRR .833→.873, and ADR 0006's named
    zero-overlap miss is rescued. `--lexical-only` still measures exactly
    .762/.952/.833 with its four goldens byte-identical.
- **Decided / open:** two judgment calls recorded (implementation.md → Decisions,
  → ADR 0010). (1) **dense_global does not fire when BM25F returns zero
  candidates** — removing that early return made "No confident matches"
  unreachable, since a binary prefilter always has a nearest neighbour; measured
  noise scores 0.23–0.26 cosine vs a true rescue's 0.34, so no floor separates
  them as the corpus grows. Re-reading ADR 0006 settled it: "zero lexical
  candidates" meant the correct *document* had no overlap, not the query.
  (2) The two **hybrid goldens were updated deliberately**, with the eval table
  as justification; the four `--lexical-only` goldens were not touched.
  **⚠ Open (size):** early measurement projects the state envelope to ~35 MB
  @100k against Arpit's 30 MB budget — `meta/` + `sigs/` are the risk, not
  `df/` (~2 MB). M8 measures properly; cheap fixes noted if it confirms.
- **Next:** **M6 — PPR-lite expansion** (damping 0.85, 3 iterations, top-10
  ≥0.01, `[engine.graph]` config) + graph list into RRF. Then M7 (profiles +
  `db pull`), M8 (100k benchmark + gate), ADRs 0008–0011, docs pass, v0.23.0.
  Version still 0.22.1.

## 2026-07-21 — phase 4 M1–M3: substrate, state plane, graph · Claude Code
- **Asked:** execute handoff 0004 (knowledge substrate v3) — the full phase, M1 first,
  milestone plan posted before any code.
- **Did:** posted the M1–M8 plan with file-level breakdown, then built and landed
  **M1–M3**, each green before the next.
  - **M1** — `index/sqlstore.py` (schema A, format_version 2, WAL, single-writer
    `.fux/index/.lock`, PK-sorted writes) beside the JSON store, with `[index] format
    = json|sqlite|auto` dispatch; `ingest/lock.py` writes **`fux.lock`** at the repo
    root (format B) and the operational manifest moves to `.fux/index/manifest.jsonl`;
    `--check` is now lock-only and three-way (DRIFT/STALE/STATE-DESYNC); `fux setup`
    writes `.fux/index/` to `.gitignore`. **Parity proven, not asserted:** all six
    v0.22 goldens pass byte-for-byte on the sqlite backend (`tests_e2e/test_sqlite_parity.py`).
  - **M2** — `fux/state/` committed lean plane (format C: 256 buckets ×
    codes/sigs/meta, `FUXSTATE1\0` header, sorted records); Bloom signatures
    (k=4, 9.6 bits/term, 8–128 B — handoff open question 1 **decided**);
    `embed/fuxvec.py` sign-quantizer; bulk/mirror tier (`docs_text` rows, no files
    on disk); `fux cat`; and the **fresh-clone query path** — `rm -rf .fux/index`
    still answers `find`/`ask` at doc level from committed state, and `fux ingest`
    rebuilds the state buckets byte-for-byte.
  - **M3** — `fux/graph/` deterministic extraction: `references`, `cites` (links
    under a citations heading, ranked as evidence), `crawled_from`, `tagged`
    (tag *nodes*, so N docs sharing a tag cost N edges not N²), all EXTRACTED
    grade; node payloads (outline, top_terms) into the `docs` row.
  - Bugs the tests caught and fixed: vectors were hardcoded to the JSON store;
    sqlite corruption escaped past the CLI error boundary; a local-only `fux ingest`
    silently evicted mirror-tier `docs_text`; `fux cat` could not resolve on a
    fresh clone (manifest is in the runtime plane — now falls back to the lock).
  - Suites **172+29 → 262 unit + 55 e2e**, all green. cli-examples.md updated
    *before* each new renderer, per the handoff.
- **Decided / open:** three deviations recorded in implementation.md → Deviations
  (all headed for ADRs 0008/0011): `web:<slug>` ids apply to **all** fetched pages,
  not just bulk (otherwise every curated web doc reads as a permanent
  STATE-DESYNC); the operational manifest survives, relocated, rather than being
  replaced by the lock; `fux answer` has **no** state-only mode — it is extractive
  *and cited*, and citations need line-anchored passages, so it declines with a
  reason rather than citing lines the index never scored. **Open:** profile
  ranking parity (DoD 7) needs corpus-level df to be exact — Bloom-derived df is
  approximate; decide and record honestly at M7/M8.
- **Next:** **M4 — the kernel** (`retrieve()` + `ResultGraph`, re-plumb
  ask/find/answer under it with v0.22 golden byte-parity, then the
  `explain`/`graph`/`path` renderers). M4–M8 + ADRs 0008–0011 + the docs pass +
  the 0.23.0 bump are **not** started; version is still 0.22.1.

## 2026-07-21 — dummy playground repo for dogfooding · Claude Code
- **Asked:** set up a sibling repo with dummy data to play with the fux package.
- **Did:** created `~/my_programs/fux-playground` (git-initialized, initial commit) — fictional
  "Kestrel Coffee" roastery corpus: 3 md docs, 1 txt note, 2 py files, inventory.json,
  suppliers.yaml. Ran `fux setup --docs docs,notes --code src --data data -y` + `fux ingest`
  via fux's own .venv (fux 0.22.1): 8 files → 8 chunks, BM25F + embeddings. Verified
  `ask`/`find`/`answer` all return sensible results; `.fux/` cache committed per convention.
- **Decided / open:** nothing decided; playground is throwaway-adjacent but committed so
  re-ingest determinism can be diffed. `answer` output for the JSON-flattened chunk is noisy
  (dumps the whole flattened lot list) — possible future chunking/answer tuning observation.
- **Next:** play with queries in `fux-playground`; consider it a scratch dogfood corpus.

## 2026-07-21 — Pipeline stages reviewed → full platform matrix (linux/macos/windows) · Claude Code
- **Asked:** review all pipeline stages for necessity; the package must work on
  Python ≥ 3.11 across unix/linux/mac — then "and windows as well".
- **Did:** restructured CI — matrix now linux (3.11–3.14) + macos + windows
  (3.11 + 3.14 boundaries); **"fux gate" became a strict aggregator**
  (`if: always()` + explicit needs-result checks — a skipped required check
  would otherwise count as satisfied), so the wall now transitively requires
  every platform green; **ai-review no longer re-runs the suites** (they ran 3×
  per PR with zero added signal — its value is the separation-of-duties refusal
  + $0-law + credential probes, now ~10 s). Windows product fixes that CI made
  necessary: CLI boundary reconfigures stdout/stderr to UTF-8 on win32 (cp1252
  consoles crash on `·`/`→`), and `.gitattributes` forces LF everywhere with
  explicit binary guards (CRLF checkout would silently break fixture shas +
  goldens per platform; renormalize showed zero drift). pyproject gains the
  3.14 classifier.
- **Decided / open:** publish stages unchanged (pure-py wheel = one build for
  all OS). **Result: all 11 checks green on first run — Windows and macOS
  passed both suites with no further fixes needed.** Merged as PR #36.
- **Bookkeeping note (honest):** the Cowork session's README rewrite was
  uncommitted in the shared working tree and got swept into PR #36's commit
  (`git add --renormalize .` staged it; the unstage didn't hold). The content
  is intact and correct on main — only the commit message is wrong about it.
  Main is protected, so the history stands as-is rather than being rewritten.
- **Next:** Anton dogfood.

## 2026-07-21 — Agent commits now attributed + Verified on GitHub · Claude Code
- **Asked:** commits showed "Unverified" — why, and fix by attributing agent
  commits to Arpit's account.
- **Did:** diagnosed via the commits API: commits were already GPG-signed with
  Arpit's own key (`E38B58D8FDEF7698`), but the committer email
  `claude-code@fux.local` belongs to no GitHub account → `reason: no_user`.
  Fix (empirically converged): the noreply address gave `bad_email` — GitHub
  also requires the committer email to appear in the signing key's identities —
  so repo-local `user.email` is now `arpitarya.dev@gmail.com` (the key's UID,
  verified on the account). Live result on this very commit:
  `verified: true, reason: valid`, attributed to `arpitarya`, author name still
  `Claude (agent)`, `Co-Authored-By: Claude` trailer intact — the agent trail
  survives in metadata while GitHub verifies against Arpit's key.
- **Decided / open:** nothing open — future agent commits in this repo are
  Verified. (Historic commits keep their badge; rewriting history for a badge
  is not worth it.)
- **Next:** merge this PR; Anton dogfood continues.

## 2026-07-21 — v0.22.1 published; scheduled protection audit removed · Claude Code
- **Asked:** (1) what is audit-protection.yml, is it needed? (2) remove it.
- **Did:** explained it (weekly drift alarm comparing live branch protection vs
  `.github/branch-protection.json`; fails loudly, needed an admin PAT secret that
  was never set). **Removed the workflow** at Arpit's call — the wall itself is
  untouched (required checks + enforce_admins verified live); the JSON source of
  truth + `scripts/audit-branch-protection.sh` / `apply-branch-protection.sh`
  stay for manual audits (`./scripts/audit-branch-protection.sh arpitarya fux
  main`). Also this exchange: **v0.22.1 released and verified on PyPI** — wheel
  6.98 MB, sdist now 133 files with zero old-build/CI leaks (the 0.22.0 sdist
  had shipped `archive/`); publish ran with the new tag↔version guard.
- **Decided / open:** no scheduled tamper alarm on the wall anymore — re-add the
  workflow + a `BRANCH_PROTECTION_TOKEN` PAT if that guarantee is ever wanted back.
- **Next:** Anton dogfood.

## 2026-07-22 — First external conformance run: hybrid degrades 4× at 1k · Cowork
- **Asked:** what came out of the 1k test.
- **Result:** the fux-lab suite ran against **fux-engine 0.23.0 from PyPI** —
  52 checks, **51 pass, 1 fail**, plus two findings hidden in INFO rows.
- **The headline (bad):** on 1 000 docs with 11 planted pairs,
  **lexical-only hit@5 0.818 / MRR 0.576** vs **hybrid hit@5 0.182 / MRR
  0.136** — lexical found 9/11, hybrid found 2/11. Opposite direction from the
  engine's own gate (fixture-scale ADR 0006/0010, hit@5 1.000). **Hybrid is the
  default path**, so if this generalizes the default is worse than the flag.
  Fires the recorded reopen-trigger in `compare/query-engine.compare.md`.
- **Cause NOT isolated — two readings, both plausible:** (A) RRF has no quality
  floor, so a noise-carrying dense list demotes correct lexical hits; (B) the
  synthetic corpus is adversarial for dense (450 notes from one paragraph
  template → near-identical sign-quantized codes → arbitrary dense order).
  Discriminating experiment named: **run the same suite on the realistic
  acme-payments corpus**. Recovers → B (add a dense-quality guard); still
  degrades → A (the default engine mode is wrong at scale).
- **Secondary:** zero-overlap rescue **0/2 in both modes** — likely because the
  planted sentence sits in a doc that is otherwise about something else, so the
  *document* vector is dominated by surrounding text. If confirmed, a real
  documentable limit of doc-level dense search (argues for chunk-level codes),
  and ADR 0010's rescue claim holds only when the answer dominates its doc.
- **Tertiary:** fresh-clone parity passed on **top-1 only** — "lower-rank scores
  differ; state plane is quantized". README/CHANGELOG claim "same rankings *and
  scores*". Either narrow the claim or close the gap — a docs-accuracy issue
  at minimum.
- **What passed:** byte-identical double-ingest; all three drift cases
  distinguishable with correct `--strict` exits; honest decline in all three
  verbs (`answer` → null, 0 sources, no fabrication); citations resolve;
  `--lexical-only` stable; every size/latency within ±15 % of baseline.
  Measured @1k: ingest 0.46 s · verbs ~0.12 s · state **200 B/doc** (vs 230
  projected) · index 2 051 B/doc · cache 1 014 B/doc · lock 208 B/doc.
- **Did:** filed `proposals/hybrid-degrades-at-scale.md` with all three
  findings, both readings, the discriminating experiment, and candidate
  mitigations (dense admission threshold · confidence-weighted RRF ·
  size-aware default · `fux doctor` reporting which mode wins). Indexed in the
  proposals README.
- **Vindication of the harness:** an independent black-box suite on a
  realistic-size corpus found in one run what a 21-pair fixture gate could not.
- **Next:** build the acme-payments corpus and re-run — that decides A vs B.

## 2026-07-22 — Phase 5 specced: debug & observability (0005) · Cowork
- **Asked:** a debugging plan for fux *everything*; expose a value in the toml;
  must work with skills too.
- **Did:** wrote `handoff/0005-debug-observability-handoff.md` + prompt, framed
  around **five questions debug must answer** (doc not in corpus · query didn't
  return it · answer wrong/thin · install/corpus bad state · slow/big). Design:
  **`[debug]` section in fux.toml** (`level` off/info/debug/trace, `categories`
  = pipeline stages, `output` stderr|path, `timing`, `redact`, `max_bytes`),
  precedence flag > `FUX_DEBUG` > toml > off, keeping `FUX_DEBUG=1` back-compat
  with the existing hooks contract. New `src/fux/debug.py` emitter with a hard
  invariant: **debug never writes to stdout** — so every golden must pass
  byte-identical at `--debug=trace` (the gate, written at M1 before any
  instrumentation). Redaction default-on (ids/paths/counts, never document
  text — enterprises will email these logs); deterministic lines so two trace
  runs diff clean. Two new commands: **`fux doctor`** (7 groups incl. a
  self-test and — deliberately prominent — *source globs matching zero files*,
  the commonest silent misconfig; every failing check prints what/why/**the fix
  command**) and **`fux why "<q>" --doc <path>`** for the *negative* case
  `--explain` can't cover, ending in a one-line verdict ("not returned: rank 47
  lexical, no dense candidate (cosine 0.19 < pool cut 0.31), no edge from any
  seed") — that sentence is the feature. **Skills requirement met:** new
  `fux-debug` skill (doctor → check → why → fidelity → raise level → *report,
  don't guess*) plus escalation pointers added to fux-query/fux-ingest.
  M1–M6 pre-registered in IMPLEMENTATION.md per the every-execution law; PLAN
  build queue + status rows added; registry bumped.
- **Decided / open:** four open questions routed to ADR 0012 (hand-rolled vs
  stdlib logging; whether `doctor --json` is CI-stable; `why --all`; whether
  `timing` belongs in `[debug]` or its own `[profile]`).
- **Next:** run `handoff/0005-debug-observability-prompt.md` in Claude Code
  (→ v0.24.0), or the 1k regression prompt first — independent of each other.

## 2026-07-22 — 1k regression prompt written · Cowork
- **Asked:** a prompt to execute 1k and do regression testing.
- **Did:** wrote `fux-lab/prompts/run-1k-regression.md` — five steps: (1) run
  `./setup.sh`; (2) **hand-verify every verb's real `--json` shape before
  trusting the suite** (the suite guesses `results[].path`, `sources[].path`
  etc. and was written blind); (3) run `./run.sh` and triage each failure
  against an explicit table — *suite guessed wrong* → fix the suite and record
  the correction; *suite right, engine differs* → **leave it failing** and
  record a finding; *environment problem* → fix and note whether setup.sh
  should have caught it; (4) deepen thin assertions (honest-decline path,
  whether fresh-clone parity actually exercises committed state or silently
  skips, the three drift cases, making the determinism hashes visible so a
  no-op can't masquerade as a pass, cold-vs-warm latency); (5) report the
  metrics table, every suite↔CLI correction, genuine findings phrased for
  upstream filing, and corpus gaps that feed the realistic-repo work.
  Carries the independence ground rule (never read the engine's source to
  explain behaviour). Indexed in lab README + TEST-PLAN §7.
- **Framing that matters:** the prompt tells the agent to expect failures and
  that *correcting the harness is the main work* — the suite has never met a
  real binary, so the first run is its acceptance test.
- **Next:** Arpit runs the prompt; findings feed back as engine observations.

## 2026-07-22 — Clean 1k rebuild; scaffolder is now the single source of truth · Cowork
- **Asked:** remove the 1k dir and do a clean setup.
- **Found first:** `shared/new-env.sh`'s template had drifted from the
  hand-improved `1k/setup.sh` — it still only generated a corpus, so a
  scaffolded 10k/100k would have reproduced the exact "no .fux/" confusion.
  Fixed before rebuilding: the scaffolder now emits the full flow (bootstrap →
  generate → `fux setup --agents --skills --hooks` → `ingest` → `--check` →
  the present/MISSING verification block with per-plane sizes), plus `run.sh`,
  the `fux` shim, and a README whose first line answers "Where is `.fux/`?".
  Template written from a quoted heredoc + sed substitution so the emitted
  script stays readable. Added `--force` to replace an existing env.
- **Did:** `rm -rf 1k` → `shared/new-env.sh 1k`. Verified by scaffolding a
  throwaway 10k and diffing: **identical modulo tier name and the heavy gate**,
  so all environments are now created the same way and cannot drift.
  Also removed `uv init` leftovers (`main.py`, `pyproject.toml`) from
  `playground/`, which had the same scaffolding noise.
- **State:** `1k/` is bare — VERSION, setup.sh, run.sh, fux, README, baselines/
  — awaiting its first `./setup.sh`. Playground keeps its ingested state.
- **Next:** `cd fux-lab/1k && ./setup.sh` (clean run), then `./run.sh`.

## 2026-07-22 — 1k setup confirmed working; discoverability fixed · Cowork
- **Asked:** "i executed it but i don't see .fux folder in 1k dir."
- **Found:** it ran correctly — `.fux/` is at **`1k/corpus/.fux/`**, not
  `1k/.fux/`, because the corpus directory *is* the project (by design). On
  disk: 935 sources in fux.lock, `.fux/` 9.9 MB (cache 4.0 · index 2.0 · state
  4.0), 958 cache files, 1 012 state shards, index.json 1.3 MB, plus the agent
  surface (AGENTS.md, CLAUDE.md, .claude/, .kiro/). So the **first real
  end-to-end fux-lab run succeeded** — first time the harness has driven the
  published 0.23.0 wheel.
- **Real defect was discoverability, not function:** nothing told the user the
  project lives one level down. Fixed: `setup.sh`'s closing block now prints an
  explicit NOTE ("the corpus directory IS the project — .fux/ is inside
  corpus/, NOT in the environment root") plus a present/MISSING table with
  per-plane sizes and lock entry count; `1k/README.md` opens with a callout
  answering "Where is .fux/?" before anything else.
- **Worth noting for the engine:** this is the same confusion a first-time Fux
  user could hit in a repo with a nested docs folder — a candidate line for
  DOGFOOD.md or `fux setup`'s completion message ("wrote fux.toml and .fux/ in
  <abs path>"). Recorded here as an observation, not yet a proposal.
- **Next:** `cd fux-lab/1k && ./run.sh` — the suite's own first real exercise.

## 2026-07-22 — 1k env fixed: corpus IS the project, setup now ingests · Cowork
- **Asked:** "setup 1k the proper way — i don't see .fux dir."
- **Diagnosed:** correct. The old `1k/setup.sh` stopped after generating the
  corpus; `fux setup`/`fux ingest` only ran later, inside a *symlinked
  workspace* the suite created — so the env looked empty and nothing was
  hand-queryable. (Arpit's run had installed fux-engine 0.23.0 fine; the gap
  was purely the missing configure+ingest steps.)
- **Did:** made **the corpus directory the project** — `fux.toml`, `fux.lock`
  and `.fux/` live *inside* `corpus/`, exactly as in a real repo; dropped the
  symlinked workspace entirely (symlink traversal was its own confound).
  `setup.sh` now: bootstrap → generate (skip if present, `--regen` to rebuild)
  → `fux setup --docs docs,notes,reports --code src --data data --images assets
  --agents --skills --hooks -y` → `fux ingest` → `--check` → **prints the
  `.fux/` tree and sizes** so "is it there?" is answered on screen. Added a
  `1k/fux` shim (runs the env's binary inside corpus/). Suite's
  `setup_workspace` → `ensure_project` (idempotent fallback only).
  **Made bootstrap uv-aware** — prefers `uv venv`/`uv pip` when available
  (honours `.python-version`, which this env pins to 3.14), falls back to
  stdlib venv+pip with a clear ≥3.11 message; verifies `fux --version` and
  records the exact build to `.installed`. Removed stray `uv init` scaffolding
  (`main.py`, `pyproject.toml`); kept `.python-version` and committed it.
- **Could not verify here:** the venv's interpreter symlinks to a host pyenv
  path invisible to the sandbox, and the sandbox is Python 3.10 — so `.fux/`
  still gets created on Arpit's first `./setup.sh`, not by me.
- **Next:** `cd fux-lab/1k && ./setup.sh` → then `./fux ask "…"` / `./run.sh`.

## 2026-07-22 — fux-lab restructured: one directory per environment, own .venv · Cowork
- **Asked:** inside fux-lab, one dir for playground with its own `.venv`,
  another for 1k with its own, and 10k/100k set up later on his go-ahead.
- **Did:** restructured to **environment directories, each self-contained**:
  `playground/` and `1k/` each own a `.venv`, `VERSION` (its pinned
  `fux-engine` build), `setup.sh`, corpus, workspace, results and baselines.
  Shared tooling moved to `shared/` (`bootstrap.sh` — venv + version-pinned
  install with a Python ≥3.11 guard; `generate/`; `regress/run.py`, now
  **env-scoped** via `--env` with all paths resolved inside the env and the
  binary defaulting to `<env>/.venv/bin/fux`). Reports now pin the version
  under test. `shared/new-env.sh <name>` scaffolds 10k/100k on demand, wiring
  the `--i-know-this-is-heavy` gate into their setup so the gate lives in a
  readable file rather than muscle memory. Playground gained a `./fux` shim
  (no venv activation) and a "try breaking it" section that feeds observations
  back into the suite. README/TEST-PLAN/.gitignore rewritten for the layout;
  shell + Python syntax verified; 19 tracked files, all venvs/corpora/results
  ignored.
- **Why per-env venvs:** each pins its own build, so 1k can test a release
  candidate while 100k holds the last known-good — and no run can contaminate
  another environment's baseline.
- **Next:** `cd 1k && ./setup.sh && ./run.sh` on a Python ≥3.11 machine (first
  real end-to-end run); 10k/100k await Arpit's go.

## 2026-07-22 — fux-lab decoupled: independent conformance harness · Cowork
- **Asked:** the lab must be a **separate entity, not linked to the local fux
  repo at all**.
- **Did:** fully decoupled `fux-lab` and reframed it as an **independent
  conformance/regression harness for the published `fux-engine` package**.
  Install is now `pip install fux-engine` (PyPI or a candidate wheel) — never an
  editable install from a source tree; the suite drives the `fux` binary via
  subprocess only and never imports fux. TEST-PLAN gained **§0 Independence**
  as a standing rule; the CLI contract is now **derived from observation**
  (`fux --help`, real `--json` output) rather than from the engine's docs; every
  report pins `fux --version` + install method. The realistic-repo prompt gained
  a hard ground rule: *do not read/clone/link any Fux source tree; if observed
  behaviour looks wrong, record it as a finding rather than fixing the suite or
  consulting the engine*. Removed all `../fux` references (verified: zero
  remaining). `git init`'d as its own repo — 9 tracked files, all generated
  content gitignored.
- **Why it's better:** testing the artifact catches packaging faults an editable
  install conceals — exactly the class that shipped in fux 0.22.0's sdist. The
  harness is also now handable to anyone with just the package name.
- **Decided / open:** harness is standalone; realistic generator still pending
  (prompt ready). Suite still unrun end-to-end (Python 3.10 sandbox).
- **Next:** Arpit runs the realistic-repo prompt from the lab.

## 2026-07-22 — Realistic-repo test spec (acme-payments, 1k) · Cowork
- **Asked:** a plan to execute like a *regular repo* — some source, some docs,
  etc. — plus a prompt to set it up right for 1k docs.
- **Did:** accepted the critique (the synthetic generator makes proportional
  buckets, not a repo) and wrote
  **`fux-lab/prompts/build-realistic-repo.md`** — the paste-ready build spec for
  `generate/make_repo.py` producing **acme-payments**: real repo shape (src
  across 5 services, ADRs/RFCs/runbooks/postmortems/meeting-noise, migrations,
  configs, workflows, diagrams, vendor PDFs, wiki mirror), power-law sizes, a
  genuine reference graph incl. deliberately broken links, and the headline
  property — **~12 stale-vs-current contradictions** (superseded ADRs, inline
  dated notes, and unmarked stale guides) where returning the *old* answer is
  the failure the corpus exists to catch. Eval set ~50 questions typed by kind
  (factual/why/how-to/cross-doc/**stale-vs-current**/zero-overlap/
  **unanswerable** — the last verifying Fux still *declines* honestly). Suite
  integration specified: per-kind quality breakdown (an aggregate 0.95 can hide
  0.4 on staleness), a **staleness-precision metric** failing on any inversion,
  and a decline check. TEST-PLAN gained §2b + the spec link; `.gitignore` +=
  `repos/`. Synthetic generator retained for the 10k/100k scale tiers.
- **Decided / open:** realistic repo is the *primary* 1k target; synthetic =
  scale only. Generator not yet built (prompt handed to Arpit).
- **Next:** run the prompt in Claude Code; expect suite↔CLI mismatches on its
  first real end-to-end run (recorded as unverified in TEST-PLAN §6).

## 2026-07-22 — fux-lab created: test plan, generator, regression suite, playground · Cowork
- **Asked:** a testing plan + playground in a **sibling** dir; regression tiers
  at 1k/10k/100k across all source types. Arpit's calls: sibling
  `~/my_programs/fux-lab`; nothing generated committed; **start at 1k**, larger
  tiers on his go; assert all four families (determinism, perf, size, quality)
  and *document everything in detail to improve fux*; maintain the plan for
  on-demand testing.
- **Did:** requested access to `~/my_programs` (only `fux` was mounted) and
  created **`fux-lab/`**: `TEST-PLAN.md` (the maintained spec — tier table,
  required corpus composition, the four assertion families, the report contract
  that phrases findings as candidate `docs/proposals/` entries, run
  instructions, maintenance rules); `generate/make_corpus.py` (stdlib,
  seeded/deterministic, 8 source types in fixed proportions, **planted link
  graph + eval pairs incl. zero-overlap + lexical distractors + adversarial
  shapes**, heavy-tier gate); `regress/run.py` (black-box CLI suite:
  double-ingest byte-identity, `--check` clean + DRIFT + `--strict`→2,
  fresh-clone parity, `--lexical-only` stability, citation resolution, all six
  verbs with latencies, size metrics, eval hit@1/hit@5/MRR per mode with
  zero-overlap rescue count, baseline diffing at ±15 %, dated markdown report);
  seeded `playground/`; `.gitignore` (corpora/workspaces/results out).
- **Verified:** 1k corpus builds — 1 008 files, 4.3 MB, 11 eval pairs — and
  **re-generates byte-identically**; gate refuses 10k without the flag; both
  scripts compile; missing-corpus path prints the exact fix.
- **Not verified (recorded in TEST-PLAN §6):** the suite has **never run
  end-to-end** — the sandbox is Python 3.10, fux needs ≥3.11. First real run is
  on Arpit's machine and doubles as the suite's own acceptance test.
- **Next:** Arpit runs the 1k suite locally; 10k/100k tiers await his go.

## 2026-07-22 — IMPLEMENTATION.md (every-execution law) + CHANGELOG · Cowork
- **Asked:** convert the implementation file to full caps; it must be updated on
  EVERY execution whatever the case; maintain a changelog linked from README
  with the latest change surfaced there.
- **Did:** renamed `docs/implementation.md` → **`docs/IMPLEMENTATION.md`**
  (two-step mv on the case-insensitive FS), frontmatter stripped per the
  ALL-CAPS convention, update contract rewritten: **every execution updates the
  file — completed, blocked, failed, interrupted, or abandoned** (🟡/⛔ + one-line
  why; no outcome skips it). CLAUDE.md 4b gained the third binding rule; layout,
  bundle index, registry, GLOSSARY, cli-examples links repointed (history left
  as-is). Created root **`CHANGELOG.md`** (0.19.0 → 0.23.0, keep-a-changelog
  style, from tracker data incl. the v0.23 eval table + known 10.6 s @100k
  limit); README gained **§ What's new** mirroring the latest entry + the
  CHANGELOG link; CLAUDE.md docs law gained 2b (changelog entry per bump,
  mirrored to README in the same change); registry rows for both.
- **Decided / open:** two new standing laws (every-execution tracker; changelog
  per bump). Nothing open.
- **Next:** next-phase head per the tracker: query-at-scale (postings unread at
  query time — ADR 0011).

## 2026-07-21 — M4+M5 reviewed; three rulings for the run-in · Cowork
- **Asked:** agent reported M4 (kernel re-plumb, six goldens byte-parity) + M5
  (FuxVec: hybrid+dense_global **0.810/1.000/0.873** vs v0.22's
  0.762/0.952/0.833; ADR 0006's named zero-overlap miss now retrieved;
  --lexical-only exactly preserved). Asked for the next-step prompt.
- **Rulings (Arpit via Cowork):** (1) **integer token-sums df header approved**
  — better than the spec'd averages (exact round-trip; avg_wlen recomputable
  for any weights without re-ingest); record as approved amendment in ADR 0008.
  (2) **Early-return judgment call approved** — correct reading of ADR 0006
  (rescue = doc-side zero overlap, via the third RRF list; noise floor
  0.23–0.26 vs 0.34 doesn't separate); record in ADR 0010 with those numbers.
  (3) **Budget risk: measure at M8 before optimizing** — if the synthetic 100k
  confirms >30 MB, apply per-bucket zlib first (simpler, no dictionary artifact
  to version), shared dict only if that misses; honest numbers either way.
- **Next:** continuation prompt → M6 (PPR-lite) → M7 → M8 → close-out at 0.23.0.

## 2026-07-21 — M3 escalation resolved: exact df sidecar, guarantee stays provable · Cowork
- **Asked:** the building agent escalated (correctly, per the no-silent-deviation
  rule): lean-profile BM25F can't be *provably* identical to full without exact
  corpus df — soften DoD 7 to eval-top-k, or grow the state plane?
- **Did (Arpit's call, via Cowork):** **grow the state — `state/df/XX.bin`
  sidecar** (delta-encoded term-hashes + varint df + corpus-stats header,
  ~2–5 MB @100k; incremental per-doc maintenance). DoD 7 *strengthened*:
  provably identical by construction (exact df sidecar + exact re-derived tf),
  asserted by full-corpus comparison on fixtures + eval as belt. Rationale:
  "identical rankings" is the brand promise (deterministic/compliance-grade) —
  softening converts a proof into an eval-shaped empirical claim. State
  envelope @100k: ~25–30 MB (still in Arpit's "around 10–20" band). Handoff
  format C + DoD 7 amended; proposal size table noted. Build state per the
  agent: M1–M3 done (uncommitted, suites green), M4–M8 pending, version 0.22.1.
- **Decided / open:** df sidecar in; continuation prompt handed to Arpit.
- **Next:** paste the continuation prompt into the running Claude Code session.

## 2026-07-21 — Milestone tracking law: pre-register + update every milestone · Cowork
- **Asked:** update the implementation file on every milestone, and put that in
  CLAUDE.md so it applies to every plan.
- **Did:** **Phase-4 table pre-registered** in `implementation.md` (M1–M8 +
  close-out, all ⬜, with the pre-registration note); "Now working on" updated.
  CLAUDE.md 4b split into its two binding halves: (1) every plan/handoff
  **pre-registers** its milestone table in implementation.md in the same change;
  (2) building agents update the row **at every single milestone completion**
  (status + tests + note — per milestone, never batched at phase end). The 0004
  prompt aligned: table already pre-registered, per-milestone updates binding.
- **Decided / open:** standing law for all future plans.
- **Next:** paste the 0004 prompt into Claude Code.

## 2026-07-21 — Proposal FINALIZED; plan + handoff 0004 + prompt written · Cowork
- **Asked:** finalize the proposal; create the plan, handoff, and prompt in as
  much detail as possible.
- **Did:** `proposals/knowledge-substrate.md` → **status: accepted** (graduated
  per lifecycle; header links the build spec). fux-plan: 0004 row added to the
  build queue (v3 — substrate; target v0.23.0, ADRs 0008–0011); §8 next-move
  rewritten. Wrote **`handoff/0004-knowledge-substrate-handoff.md`** — the
  build contract with normative specs: fux.db schema v2 (10 tables, WAL,
  single-writer lock, canonical ordering, citation-stable chunk ids), fux.lock
  format + staleness semantics, `.fux/state/` byte layouts (FUXSTATE1 magic,
  256 hash buckets, Bloom k=4 ~1 % FPR ≤128 B), FuxVec algorithm (quantize →
  Hamming top-500 fixed tie-breaks → exact rerank; IVF only if M8 shows
  >150 ms), kernel `retrieve()`/ResultGraph + PPR-lite constants (damping .85,
  3 iters, EXTRACTED 1.0/INFERRED 0.6, decay .8), CLI additions
  (explain/graph/path/cat/db pull), profiles incl. lean LRU; **M1–M8
  milestones** each with scope, plus DoD (8 phase-level criteria incl. v0.22
  golden byte-parity and the eval gate with zero-candidate rescue), 17 edge
  cases, 4 open questions routed to ADRs, close-out contract. Wrote the
  paste-ready **0004 prompt** (explore order, hard rules — parity sacred, math
  untouchable, cli-examples-before-renderers — verify gates, stop-clean
  semantics). Registry bumped.
- **Decided / open:** phase 4 fully specced. Nothing open in design.
- **Next:** paste `handoff/0004-knowledge-substrate-prompt.md` into Claude Code.

## 2026-07-21 — Git carries the state (committed lean plane) · Cowork
- **Asked:** git should carry the state — and it should be maintained.
- **Did:** the lean profile made this viable (~200 B/doc), so `.fux/state/` is
  now **committed, versioned state**: sharded by doc-id hash into 256 buckets
  (codes/sigs/meta, ~80 KB each @100k) so commits touching 50 docs change a few
  buckets, not a 20 MB blob; deterministic bytes = zero diff noise. What it
  buys: `git clone` → **instantly queryable** at doc level; `git log
  .fux/state/` = history of what the corpus knew; `git checkout <rev> && fux
  ask` = time-travel for free. **Maintained, enforced:** ingest rewrites
  state + lock atomically; session-end hook prompts the commit; CI's
  `--check --strict` becomes a **three-way state ↔ lock ↔ sources** gate —
  stale committed state fails the build. Honest limits: binary state (humans
  diff the lock), history growth (sharded deltas; high-churn/100k+ tiers switch
  to db-pull artifacts). §8 table, §8c subsection, §8e summary, appendix tree,
  M2 milestone all updated; gitignore narrows to `.fux/index/`.
- **Decided / open:** state-in-git folded into the ⏳ proposal.
- **Next:** Arpit's verdict → handoff 0004.

## 2026-07-21 — Lean profile: 100k docs in ~20 MB · Cowork
- **Asked:** can 100k docs land at ~10–20 MB total? Be creative; build from
  scratch if needed.
- **Did:** yes — by flipping the storage assumption. Entropy forbids compressing
  600 MB of text to 20 MB, but **determinism means Fux need not store text at
  all: sources are the storage; the index stores find + verify + re-derive**
  (deterministic converters + fux.lock shas reproduce exact bytes on demand).
  New §8c "lean profile" in the substrate proposal: **~200 B/doc persistent
  plane** — 32 B FuxVec code + 96–128 B **Bloom term signature** (validated by
  BitFunnel, Bing's production signature index, SIGIR'17 — fresh citation
  pulled) + ~50 B metadata → **100k ≈ 18–21 MB ✓**, 1M ≈ 200 MB. Query path:
  dense scan + signature prefilter → top ~50 docs → re-derive text → exact
  chunk BM25F/rerank (false positives only add candidates — rankings identical
  to full profile, eval-proven); bounded LRU keeps hot docs warm. Honest
  trades: cold-doc re-conversion latency; source availability at query time
  (web tiers may prefer full profile). Config `[index] profile = full|lean|
  auto`. Section renumbering fixed (8c lean, 8e fresh-clone summary);
  BitFunnel added to references.
- **Decided / open:** lean profile added to the ⏳ proposal; fits M5/M8.
- **Next:** Arpit's verdict on the proposal → handoff 0004.

## 2026-07-21 — Substrate proposal hardened: git contract, fux.lock, sizes, gaps · Cowork
- **Asked:** (1) exact git-committed file set — clone must rebuild from scratch;
  (2) a separate sources file with hash/date for staleness; (3) .fux size
  estimates at 1k/10k/100k/1M docs; (4) graphify as reference, not benchmark;
  (5) review the doc for gaps.
- **Did:** rewrote §8 as **the git contract** — invariant "clone rebuilds from
  scratch"; committed set = fux.toml + **fux.lock** + @lists + agent files;
  `.fux/` fully gitignored (curated-cache commit demoted to opt-in
  `[git] commit_cache` — the invariant outranks the diffs bet). New **§8a
  fux.lock**: committed root-level sorted-JSONL ledger (file kind: sha/bytes/
  converted_at/fidelity; url kind: sha/fetched_at/**max_age_days**) — staleness
  is structural (files by sha, web by age), `--check` works lock-only right
  after clone; replaces manifest.jsonl. New **§8b size envelope** with stated
  assumptions (~15 KB/doc bulk): 1k ≈ 15 MB · 10k ≈ 145 MB · 100k ≈ 1.4 GB ·
  1M ≈ 14 GB (text+postings dominate; vectors+codes <11 % — semantic is nearly
  free; lock sharding option >100k). §2 + references reworded: **graphify =
  prior art to learn from, never a benchmark**. New **§12 gaps review**, each
  resolved or ⚠ flagged: WAL concurrency, corruption=rebuild, chunk-id/citation
  stability, schema versioning, own-postings-vs-FTS5 made explicit, streaming
  ingest, ⚠ multi-corpus fan-out (federation's first requirement),
  ⚠ at-rest encryption deferred, db-pull auth v1, Windows/AV notes, relational
  eval pairs for graph/path. Appendix tree + M1 milestone aligned to the lock.
- **Decided / open:** proposal hardened; still one ⏳ awaiting Arpit's verdict.
- **Next:** Arpit's verdict → handoff 0004.

## 2026-07-21 — One proposal: knowledge-substrate.md (substrate + FuxVec) · Cowork
- **Asked:** merge the knowledge-substrate compare doc and the FuxVec proposal
  into ONE proposal with details on the approach.
- **Did:** created **`proposals/knowledge-substrate.md`** — the single
  consolidated post-v0.22 proposal, 11 sections: context (enterprise litmus),
  break analysis, SQLite store schema (incl. bulk `docs_text` + `codes`), the
  graph (deterministic + semantic edge tiers), the one-kernel/six-projections
  table, **FuxVec as §6 with the four-step approach detailed** (sign-quantize →
  big-int XOR/bit_count full scan → exact int8 rerank → deterministic IVF;
  storage verdicts incl. Parquet-as-export; standalone-package note; honest
  limits), source spec, git tiers + fresh-clone/db-pull story, enterprise
  inputs, the full sample-repo/CLI appendix (ask/answer/cat/explain/path with
  FuxVec + graph lines in --explain), and **§11 build sequencing** (handoff 0004
  milestones M1–M8, eval-gated). Deleted `compare/knowledge-substrate.compare.md`
  + `proposals/fuxvec.md`; repointed all links (compare README, proposals
  README, fux-plan, fux-toml ×2, cli-examples).
- **Decided / open:** one ⏳ document now carries the entire next phase.
- **Next:** Arpit's verdict on `proposals/knowledge-substrate.md` → handoff 0004.

## 2026-07-21 — Fresh-clone story, FuxVec proposal, answer example · Cowork
- **Asked:** (1) gitignored warehouse — what happens on a fresh clone? (2) build
  a vector db from scratch on JSON/Parquet as a package concept — push
  boundaries; (3) add a `fux answer` example.
- **Did:** substrate doc gained **"Fresh clone"** section — curated tier works
  immediately (cache is committed); bulk-local re-ingests to a byte-identical,
  manifest-verified warehouse; bulk-web either re-crawls (drift visible per doc)
  or uses the enterprise path: **warehouse as CI build artifact** + proposed
  `fux db pull` (download + sha-verify vs committed manifest — the lockfile/
  restore pattern). Wrote **`proposals/fuxvec.md`**: vector-db concept from
  scratch — sign-quantize 256-dim int8 → 256-bit codes (32 MB per 1M chunks),
  full-corpus scan via XOR + `int.bit_count()` (C-speed big-int popcount;
  ~tens of ms at 100k), exact int8 rerank of top ~500, deterministic IVF above
  ~100k, storage = packed shards/SQLite BLOBs (JSON for manifest/centroids;
  **Parquet = opt-in export extra** for DuckDB/Spark interop — pyarrow can't be
  a runtime dep); unlocks `dense_global` seeds → rescues ADR 0006's
  zero-candidate miss class; standalone `fuxvec` package noted as its own
  wedge. Substrate §3 vector-DB verdict updated ("adopting closed; building the
  concept proposed"); §8 gained the `fux answer` example (bulk logical-id +
  local file:line citations, graph-hop note). *Web quota blocked fresh cites —
  binary-quantization numbers flagged for build-time verification.*
- **Decided / open:** FuxVec = milestone inside the substrate handoff, eval-
  gated; `db pull` = proposed command. Substrate verdict still awaits Arpit.
- **Next:** Arpit's verdict on knowledge-substrate.compare.md → handoff 0004.

## 2026-07-21 — Litmus change: enterprise mega-project, not Anton · Cowork
- **Asked:** stop thinking of this project in reference to Anton; think from the
  point of a very large-scale project in corporations.
- **Did:** replaced the Anton litmus in CLAUDE.md with the **enterprise
  mega-project litmus** (scale is the default; enterprise realities are design
  inputs; the laws are the sales story: $0 = auditable supply chain, offline =
  no data egress, deterministic = compliance-grade). fux-plan §6a re-scoped
  (substrate = default forward path; standing proposals gain weight).
  knowledge-substrate doc: build trigger re-scoped (corporate corpora *start*
  past the breakpoint — substrate is the next phase, not a contingency) + new
  **"Enterprise design inputs"** section (proxy/SSO ingest, Windows fleets,
  air-gapped installs, corpus-per-boundary access model, audit priority).
  model-handoff-interview: direction-change Q&A added. Anton demoted to
  convenient small-scale testbed.
- **Decided / open:** litmus changed ✅. Substrate verdict still awaits Arpit's
  formal call, but its sequencing is now "next phase by default."
- **Next:** Arpit's verdict on knowledge-substrate.compare.md → handoff → build.

## 2026-07-21 — Documentation-style rule added to CLAUDE.md · Cowork
- **Asked:** add to CLAUDE.md — no large paragraphs in documents; split into
  points; make them roomier.
- **Did:** new **"Documentation style (required)"** section in CLAUDE.md, placed
  before the docs law: short points (one idea each), 3–4-line paragraph cap,
  blank lines between points/sections, tables for comparisons, takeaway-first
  bullets, and a fix-on-contact clause (splitting an existing wall of text is
  part of touching the doc — form is covered by the same staleness law as facts).
- **Decided / open:** binding for all future doc writing in the repo.
- **Next:** Anton dogfood (unchanged).

## 2026-07-21 — Correction accepted: bulk text lives IN the db, not as files · Cowork
- **Asked:** "saving 100k documents in cache is impractical — try to understand."
- **Did:** understood and fixed the real point — the previous tier design still
  put bulk text in a *gitignored file mirror*; but 100k files are impractical
  **as files** (walks, inodes, deletes, Windows/AV/sync), git or no git. Substrate
  doc corrected end to end: storage verdict is now **tier-dependent** — curated
  tier keeps per-file Markdown (review/git value at 10²–10⁴ docs); **bulk tier
  has no file cache at all** — converted text = `docs_text` rows in fux.db (one
  file on disk at any corpus size; SQLite reads small blobs ~35 % faster than
  the filesystem per its own benchmark). New `fux cat <doc>` materializes any
  single doc on demand; bulk citations use logical id + heading (no fabricated
  file paths); break-analysis row corrected (cache breaks at ~10⁴ *as files*);
  §7 tier table + §8 tree/CLI reworked ("never 100k files — your curated files
  plus one database"). CLAUDE.md + fux-plan tier language corrected to match.
- **Decided / open:** correction folded into the ⏳ substrate verdict (still
  awaiting Arpit's overall call on the doc).
- **Next:** Anton dogfood.

## 2026-07-21 — Consolidated into knowledge-substrate.compare.md · Cowork
- **Asked:** merge corpus-at-scale + document-knowledge-graph into ONE doc; show
  sample CLI + folder structure for the implemented substrate.
- **Did:** created **`compare/knowledge-substrate.compare.md`** — the single
  design of record for post-v0.22 architecture: verdict block with four decisions
  (SQLite substrate; doc-index-IS-the-graph; one kernel/six projections; git
  tiers), break analysis, prior-art (graphify/vector-DBs) condensed, source-spec
  extensions, research references, open build items — plus **§8 appendix**: the
  implemented-substrate walkthrough (fux.toml with globs/@lists/mirror tier;
  repo tree showing curated-committed vs mirror-gitignored vs one fux.db;
  worked CLI: resumable `--web` crawl, `ask` rescued via graph hop, `explain`
  node view, `path` with reliability + EXTRACTED tag, the new `--explain` graph
  line). Deleted the two superseded docs; fixed every live link (compare README,
  proposals README — graph marked *graduated*, fux-toml ×2, fux-plan,
  cli-examples). Worklog history left intact.
- **Decided / open:** one doc now carries the whole ⏳ decision; trigger
  unchanged (Anton: scale pain or relational questions).
- **Next:** Anton dogfood.

## 2026-07-21 — One kernel, six projections; sample-repo walkthrough · Cowork
- **Asked:** difference between ask/graph and explain/path — do they need to be
  separate, can one algorithm serve them? Plus: CLI usage + dir-structure examples
  for a sample repo.
- **Did:** researched PathRAG (AAAI'25: node-retrieval → flow-pruned paths with
  reliability scores → answers as ONE pipeline; paths are scored *byproducts*) and
  GraphRAG local search (entity-seeded = query-by-node). Designed the **unified
  kernel**: `retrieve(seed: text|node) → ResultGraph {seeds, expansion, paths,
  passages}`; all six verbs become projections (ask=passages, find=seeds,
  answer=synthesis, explain=node-seeded deep view, graph=nodes+edges, path=paths
  slice). Key insights recorded: `explain` is `ask` seeded by a node; **paths are
  retrieval provenance the PPR expansion already computes** — not a feature, a
  kept trail; `--explain` and `fux path` converge into one trust story. Written
  into corpus-at-scale §"One kernel, six projections" (engine implements one
  kernel + thin renderers; friendly verbs stay). Added **"A sample repo, end to
  end"** to cli-examples.md: acme-payments tree before/after, commit-vs-gitignore
  split per tier, human + agent daily flows, substrate-v2 era marked as proposed.
- **Decided / open:** one-kernel design folded into the substrate-v2 proposal;
  trigger unchanged.
- **Next:** Anton dogfood.

## 2026-07-21 — The merge: graph + corpus-at-scale = one knowledge substrate · Cowork
- **Asked:** is there an opportunity to merge the graph and corpus-at-scale?
  Creative, outside the box, with research.
- **Did:** found the unifying insight — **the level-1 doc index IS the graph's
  node table** (a doc entry's payload = a node's payload; the thin layer was the
  graph unrecognized). Designed "one substrate": single SQLite-v2 file with
  nodes/edges/chunks/postings/vectors; `ask`/`explain`/`graph`/`path` are three
  surfaces over the same tables; retrieval becomes seed (BM25F+dense on docs) →
  **deterministic PPR-lite expansion over edges** (multi-hop recall, zero model
  calls — the natural rescue for ADR 0006's zero-lexical-candidate miss class) →
  per-doc chunk detail → RRF with graph as third signal. Research validation:
  HippoRAG/LightRAG (PPR-from-seeds, 10–30× cheaper multi-hop; *operators beat
  structure* — cheap deterministic edges suffice), LazyGraphRAG (0.1 % indexing
  cost — defer expensive enrichment, exactly our host-session pattern),
  LiteSemRAG (LLM-free graph retrieval is a recognized lane). Bonus surfaces:
  community-detection → auto corpus map (OKF progressive disclosure, generated);
  `--explain` traversal lines; eval-gated. Written into
  `corpus-at-scale.compare.md` §"The merge"; graph proposal updated to point
  there. Two ⏳ items are now one "knowledge substrate v2" phase.
- **Decided / open:** merge proposed + recommended; trigger unchanged (Anton
  dogfood: scale pain *or* relational questions) → then compare verdict →
  handoff → ADR.
- **Next:** Anton dogfood — now the single gate for the substrate phase.

## 2026-07-21 — Document-knowledge-graph proposal parked · Cowork
- **Asked:** "how about creating a knowledge graph on all these documents — just
  a thought."
- **Did:** wrote `proposals/document-knowledge-graph.md` — the sanctioned vehicle,
  since CLAUDE.md bars graph resurrection without sign-off. Shape: a **document
  graph, not a code graph**, strictly a **derived view over the corpus**. Nodes =
  docs/URLs/tags (+ host-session concept nodes); edges in two tiers mirroring
  ingest — deterministic ($0: markdown `references`, citations, web
  `crawled_from` parent/depth, shared tags) and semantic (host-session skill,
  frontmatter-reviewable). Storage = SQLite-v2 rows (never a 512 MiB blob —
  graphify's ceiling). Surface: `fux graph` (neighborhood), `fux path` (how two
  docs connect), `fux explain` gains Links. Parked with a concrete graduation
  trigger: Anton dogfood surfaces a connects/depends/cites-shaped question that
  ask/answer handles poorly → graduates to a compare doc + ADR.
- **Decided / open:** parked, status: proposed. Nothing else open.
- **Next:** Anton dogfood (unchanged — and it's also this proposal's trigger).

## 2026-07-21 — Four course corrections from Arpit (purpose, $0 semantics, tiers, thin index) · Cowork
- **Asked:** (1) host-session LLM pass keeps fux $0; (2) the point is agents
  querying docs/links via Copilot/Claude extensions, not code; (3) vector-DB idea
  reframed — a thin layer over a *document* index with a drill-down command like
  `fux explain`; (4) millions of cache files in git is the wrong approach.
- **Did:** recorded all four in `corpus-at-scale.compare.md` §"Arpit's
  amendments": host-session semantic pass accepted as $0-legal (the old build's
  proven skill-token pattern — authoring may be model-assisted, checking/retrieval
  stay deterministic); docs-not-code focus accepted (sharpens wedge vs graphify;
  new fux-plan §6a); **two-level retrieval proposed + recommended** — compact
  doc-level index (entry + one vector per doc; 100k chunks → ~5k entries,
  brute-force viable forever, no ANN) routing to per-doc chunk loads, plus new
  `fux explain <doc>` drill-down verb; **git-tier correction accepted** — commit
  the *curated* corpus (10²–10⁴ files), gitignore bulk mirrors, commit
  fux.toml+manifest as the reproducible recipe ("git stores the recipe, not the
  warehouse"). CLAUDE.md purpose+tier folds; fux-plan §6a/§6b amended.
- **Decided / open:** 1, 2, 4 accepted; 3 recommended, folds into the SQLite-v2
  build when the scale trigger fires (`fux explain` can ship earlier as UX).
- **Next:** Anton dogfood on the shipped engine; scale work waits for its trigger.

## 2026-07-21 — Prior art: Graphify reviewed in full; vector-DB question closed · Cowork
- **Asked:** research how Graphify's index works; what about vector-DB-alikes?
- **Did:** read the full Graphify README (91.8k★, YC S26): it's a **knowledge
  graph, explicitly not a vector index** — tree-sitter AST locally for code (no
  LLM), an **LLM semantic pass for docs/media** (breaks Fux's $0 law), one
  graph.json (512 MiB cap — same single-blob pattern as our index.json, validating
  the SQLite-v2 proposal), Leiden communities, query/path/explain traversal, MCP,
  query-first hooks, committed graphify-out/ with a union-merge driver. Strategic
  note recorded: graphify ≈ the *archived* Fux build's graph layer, now
  market-validated — if the graph returns it's a view over the corpus. Vector DBs
  (LanceDB/Chroma/FAISS/sqlite-vec/ANN libs): all third-party runtime deps, and
  **ANN solves a problem Fux architected away** (candidates-first = ~200 exact dot
  products; nothing to approximate). Recorded escalation ladder for the
  zero-lexical-candidate miss class: SQLite-v2 brute-force → opt-in ANN extra.
  Both analyses added to `corpus-at-scale.compare.md` with references.
- **Decided / open:** no vector DB (closed with reasoning + reopen path); SQLite-v2
  proposal reinforced. Corpus-at-scale verdicts still ⏳ Arpit.
- **Next:** Arpit calls corpus-at-scale; Anton dogfood continues.

## 2026-07-21 — Scale review: corpus-at-scale compare + fux.toml reference · Cowork
- **Asked:** explain vectors.bin / index.json; is the cache scalable (thousands of
  files, millions of links)?; create + maintain a fux.toml example; sources could
  be folders/files/links at huge scale. Research it.
- **Did:** read the shipped store code (index.json = versioned JSON, full-load,
  postings derived in memory — ADR 0003; vectors.bin = single packed int8
  chunk-vector cache, (sha,fidelity)-keyed — ADR 0006). Researched scale paths:
  **stdlib `sqlite3`** (FTS5 ~3M rows/hr, snappy at 10k–100k docs; sqlite-vec
  brute-force numbers; Fux's dense pass is candidate-only so vectors don't
  bottleneck). Wrote `compare/corpus-at-scale.compare.md`: component-by-component
  break analysis (index.json breaks first ~25–50k chunks; the *cache* itself
  scales with sources and stays per-file Markdown forever — it's the product);
  proposed verdicts — index format v2 = single SQLite db (Fux's scorer unchanged,
  storage only; frontier solves million-link crawls) + `[sources]` globs/excludes,
  first-class files, `@list` files. Created maintained `fux-toml.md` (every
  shipped key + default from config.py; proposed extensions fenced). Registry +
  index + compare README synced.
- **Decided / open:** both scale verdicts ⏳ awaiting Arpit; build trigger = ~25k
  chunks or an outsized crawl.
- **Next:** Arpit reads corpus-at-scale; meanwhile Anton dogfood proceeds on the
  shipped formats (they're right-sized for it).

## 2026-07-21 — README upgraded to the old build's story-first format · Cowork
- **Asked:** review the README and upgrade it, referencing the older README's
  format.
- **Did:** rebuilt README.md on `archive/README.md`'s skeleton — tagline
  blockquote + badges, **The story** (the red-pipe narrative evolved for the
  query engine: the note exists, it's the *finding* that fails), **See it** (real
  as-shipped `fux ask`/`fux answer` output from cli-examples.md), Quickstart,
  ELI5, **Why it's different** (properties: deterministic, cited-or-didn't-happen,
  hybrid-offline, $0, agent-native, corpus-not-index), **How it works** (pipeline
  diagram + two-tier ingest + fenced web/CDP), collapsible full command surface,
  **The $0 guarantee** with honest limits (no synthesis, English-biased model,
  eval tie disclosed w/ ADR 0006 link), **The name** (kept; notes the rule-engine
  vision on hold), Status, closing CTA. Everything claims only shipped v0.22.x
  behaviour. Registry row bumped.
- **Decided / open:** nothing open.
- **Next:** Anton dogfood.

## 2026-07-21 — GLOSSARY.md rename + ALL-CAPS-no-frontmatter convention · Cowork
- **Asked:** rename glossary.md → GLOSSARY.md; ALL-CAPS markdown files need no
  YAML frontmatter.
- **Did:** renamed to [`GLOSSARY.md`](GLOSSARY.md) and stripped its frontmatter;
  stripped DOC-REGISTRY.md's frontmatter too (same rule); recorded the convention
  in CLAUDE.md §OKF (ALL-CAPS docs = entry-point files, exempt from `type` like
  CLAUDE.md/README.md; lowercase docs conform as before) and in the glossary's
  own Frontmatter entry; updated links in bundle index + registry row.
- **Decided / open:** convention adopted. Nothing open.
- **Next:** Anton dogfood (per the completed master run's close-out).

## 2026-07-21 — Pipeline review: sdist hygiene, publish guard, build-check → v0.22.1 · Claude Code
- **Asked:** review the pipeline with the new changes — is everything needed?
- **Did (review findings, all fixed except one):** (1) the 0.22.0 **sdist shipped
  the archived old build** (2.43 MB `archive/`) + `uv.lock` + `.github` — added
  hatch sdist excludes + a CI assertion that the sdist stays clean (root-level
  `archive/` only; `docs/archive/` is intended content); (2) **publish.yml had a
  silent-failure mode** — unbumped `__version__` + `skip-existing: true` = green
  no-op publish — added a tag↔version guard + `twine check --strict`, and scoped
  `id-token: write` to the publish job only; (3) restored the old CI's
  **build-check job** (`python -m build` + `twine check`) so metadata bugs fail
  PRs, not releases; added PR concurrency cancellation; `.DS_Store` gitignored.
  Bumped to **v0.22.1** so the corrected sdist is the published one.
- **Needs Arpit:** the `BRANCH_PROTECTION_TOKEN` secret is **missing** — the
  weekly protection audit will fail loudly (default GITHUB_TOKEN can't read
  protection). Create an admin-scoped PAT and `gh secret set BRANCH_PROTECTION_TOKEN`.
- **Next:** merge via the wall, release v0.22.1, verify the sdist on PyPI.

## 2026-07-21 — Release pipeline restored + v0.22.0 published via the wall · Claude Code
- **Asked:** push and publish the new package; create the pipeline and always
  publish it the right way.
- **Did:** ported the merge wall's CI to the rebuild — `.github/workflows/ci.yml`
  with the two required contexts: **"fux gate"** (both suites: determinism,
  goldens, eval gate, packaging budgets) and **"ai-review"** (new
  `scripts/ai-review.sh`: separation-of-duties refusal, $0-law probe on
  pyproject dependencies, credential probe on the diff, suites on the merge
  result — deterministic, model-free, per the old script's design) + a 3.11–3.13
  matrix job. Restored `publish.yml` (release → OIDC trusted publishing, `pypi`
  environment) and `audit-protection.yml` + `branch-protection.json` (note
  refreshed) + audit/apply scripts unchanged. README install now `pip install
  fux-engine`. Release path: PR through the protected branch → checks green →
  merge → GitHub release v0.22.0 → publish workflow → PyPI.
- **Decided / open:** the rebuild's "fux gate" IS the test suites until the rule
  engine returns; the wall itself (contexts, enforce_admins) is unchanged.
- **Next:** Anton dogfood (`pip install fux-engine` now works there).

## 2026-07-21 — MASTER RUN COMPLETE: all three phases shipped (v0.22.0) · Claude Code
- **Asked:** the 0000 master prompt — 0001 → 0002 → 0003 with hard gates; this is
  the final close-out entry.
- **Did:** all three phases implemented, gated, and archived in one run:
  **v1** query CLI (v0.20.0, ADRs 0001–0004), **v1.1** web/CDP/advanced ingest
  (v0.21.0, ADR 0005), **v2** hybrid engine (v0.22.0, ADRs 0006–0007).
  Full-suite final run: `tests/` **173 passed** · `tests_e2e/` **29 passed +
  1 gated skip** (office-with-extra) · eval gate green. README tells the whole
  story (install → setup → ingest → ask/find/answer → agent integration →
  corpus-in-git); 0000 master prompt archived `status: implemented`;
  DOGFOOD.md live for Anton.
- **Decided / open:** hybrid ships **enabled** (gate passed as a tie on the
  fixture set — honest reading + rank-level rescues in ADR 0006); vectors are
  derived data (gitignore-able; corpus = cache + manifest); every open question
  in the three handoffs is resolved and recorded in its ADR.
- **Next:** dogfood in Anton (DOGFOOD.md): configure, ingest, live with
  `fux ask`, build the private Anton eval pairs — those numbers pick what gets
  built next (reopen triggers live in the compare docs).

## 2026-07-21 — PHASE 3 REPORT: Hybrid engine v2 shipped (v0.22.0) · Claude Code
- **Asked:** master run, phase 3 — execute handoff 0003 (eval-first hybrid v2).
- **Did (shipped):** eval harness (21 committed Q→passage pairs incl. deliberate
  zero-overlap paraphrases; hit@1/hit@5/MRR; `--project/--pairs` for private
  Anton evals); `tools/distill/` (potion-base-8M → int8 per-vector → packed
  7.93 MB `model.bin`, sha-pinned, MIT license-checked, recipe documented);
  `fux.embed` stdlib runtime (BertNormalizer+WordPiece with exact token-id
  parity, mean-pool folded into the scale, exact int8 cosine, lazy 10 ms load);
  `.fux/index/vectors.bin` chunk-vector cache ((sha, fidelity)-keyed reuse);
  RRF fusion (k=60) over BM25F candidates with full per-result hybrid detail;
  `--lexical-only` byte-parity with v1 proven by unchanged pre-v2 goldens;
  answer question-similarity factor; wheel ships the bundle (6.98 MB ≤ 15 MB).
- **Eval (the gate, in ADR 0006):** lexical 0.762/0.952/0.833 vs hybrid
  0.762/0.952/0.833 — a tie satisfies the ≥ gate → hybrid enabled. Rank-level
  paraphrase rescues observed; the one remaining miss has zero lexical
  candidates (the recorded candidate-only trade). Warm hybrid query 0.2 ms.
- **Decided / open (ADRs 0006–0007):** re-packed potion over distill-our-own
  (no in-domain corpus yet — Anton's is the reopen trigger); single vector
  file over shards; vectors gitignore-able as derived data. Open risks:
  English-biased model (non-English degrades toward lexical); zero-candidate
  documents unreachable by dense (by design, measured).
- **Next:** final master close-out (full suites, README story, archive 0000).

## 2026-07-21 — PHASE 2 REPORT: Ingest v1.1 shipped (v0.21.0) · Claude Code
- **Asked:** master run, phase 2 — execute handoff 0002 (web, CDP, advanced tier).
- **Did (shipped):** stdlib `html.parser` HTML→Markdown converter (deterministic;
  link/title extraction); `[sources.web]` config + fenced crawl — urllib fetcher
  (UA/timeouts/retries/size cap/redirect-final-URL), robots.txt obeyed, BFS
  frontier with depth/budget/domain caps + URL and sha dedupe (dual provenance),
  attachments through the 0001 converters, `url`/`parent`/`depth`/`fetched_at`
  provenance, byte-stable re-crawl of unchanged pages, web entries persist across
  local-only runs and are excluded from `--check`; hand-rolled RFC 6455 WebSocket
  client (RFC-vector + fake-server tested) + minimal CDP capture (existing Chrome
  only, settle delay, actionable errors, websocket-client extra as flagged
  fallback) + `manual_cdp_smoke.py`; advanced tier `fux ingest --advanced` —
  Docling/tesseract upgrades, (sha, fidelity)-keyed index reuse, upgrades survive
  re-ingest and reset when the source changes; AGENTS contract + fux-ingest skill
  teach judge-and-upgrade; import-fence test (query/index can never touch network
  modules). ADR 0005; 0002 pair archived; README/plan/registry/cli-examples/
  interview updated; v0.21.0.
- **Test counts:** `tests/` 154 passed · `tests_e2e/` 24 passed + 1 gated skip,
  incl. fixture-site crawl (robots/oversize/off-domain skips surfaced).
- **Decided / open (in ADR 0005):** hand-rolled HTML→MD as the always-present
  default (open Q1); CDP settle = fixed configurable delay, networkIdle deferred
  to dogfood evidence (open Q2); crawl resumability deferred (open Q3).
  **Open risks carried:** rendered capture depends on local Chrome; changed-page
  re-ingests are not byte-reproducible (inherent to network sources); HTML
  converter is good-enough, not pandoc.
- **Next:** Phase 3 — execute `handoff/0003-hybrid-engine-v2-prompt.md`.

## 2026-07-21 — PHASE 1 REPORT: Query CLI v1 shipped (v0.20.0) · Claude Code
- **Asked:** master prompt 0000 — execute handoffs 0001 → 0002 → 0003 in sequence
  with hard phase gates. This entry is the phase-1 gate report.
- **Did (shipped):** the complete v1 surface per handoff 0001 — `fux setup`
  (wizard + full flags + `-y`, idempotent TOML merge), hand-rolled frontmatter
  parser (subset YAML, permissive, unknown keys round-trip), inferred-tier ingest
  (md/txt/code/json/yaml/image-stub; office via the `[ingest]` extra) → OKF cache
  with provenance + per-dir index.md + canonical manifest.jsonl +
  `--check`/`--strict`/`--list-inferred`/`--list-skipped`, heading chunker
  (256–512 words, fences/tables atomic, source line spans), true BM25F
  (weight-then-saturate; JSON index, incremental by sha), `fux ask`/`find`/
  `answer` per the cli-examples.md contract (+ `--json`/`--explain`/`--top`/
  `-C`/`--answer-max`; extractive TextRank answers with `[n]` citations),
  `fux setup --agents --skills --hooks` (AGENTS.md managed block + CLAUDE.md/
  copilot/Kiro pointers, fux-query/fux-ingest SKILL.md, fail-open hooks).
  ADRs 0001–0004; 0001 pair archived (`status: implemented`); README rewritten;
  DOGFOOD.md emitted (master rule 6); version 0.20.0.
- **Test counts:** `tests/` 108 passed · `tests_e2e/` 20 passed + 1 gated skip
  (office-with-extra). Byte-identical determinism proven for double-ingest AND
  fresh re-ingest; goldens normalized (3 dp, volatile keys stripped), updated
  only via `FUX_UPDATE_GOLDENS=1`.
- **Decided / open:** `converted_at` = SOURCE_DATE_EPOCH/source-mtime, never wall
  clock (determinism outranks the spec's letter — Deviations + ADR 0002); index
  format JSON by measurement (16 ms load @5k chunks; postings build 525 ms
  dominates — escape hatch: persist postings); token ≈ whitespace word validated;
  answer noise guards (stopword-free overlap, 35 % keep floor) earned from smoke;
  implementation reworked to match cli-examples.md as the normative UX contract
  (--check advisory + --strict→2, JSON key shapes, [n]+Sources citations).
  **Open risks carried:** postings-build cost at very large corpora; paraphrase
  recall weak until v2 hybrid (by design); Cowork has no hook surface
  (instruction files only).
- **Next:** Phase 2 — execute `handoff/0002-ingest-web-advanced-prompt.md`.

## 2026-07-21 — Glossary created · Cowork
- **Asked:** create a glossary.
- **Did:** created [`glossary.md`](glossary.md) (`type: Glossary`) — ~35
  alphabetical entries covering engine terms (BM25F, RRF, static embeddings,
  chunk/passage, extractive answer, TextRank, eval harness/MRR), ingest terms
  (cache/corpus/manifest/index, fidelity inferred/advanced, Docling, Tesseract,
  CDP, RFC 6455, drift, provenance), process terms (compare doc, proposal,
  handoff, ADR, goldens, worklog, determinism, `$0`), and agent terms (AGENTS.md,
  SKILL.md, fail-open, Anton). Each entry links to its owning doc. Registered in
  DOC-REGISTRY (trigger: new recurring term or meaning change) + bundle index.
- **Decided / open:** nothing open.
- **Next:** Anton dogfooding (DOGFOOD.md) — the build is complete at v0.22.0.

## 2026-07-21 — CLI examples doc: the input/output contract · Cowork
- **Asked:** create examples of CLI input and output, link to necessary documents,
  maintain it.
- **Did:** created [`cli-examples.md`](example/CLI.md) (`type: Reference`) — worked
  input/output for `fux setup` (wizard + flag forms), `fux ingest` (+ `--check`,
  `--list-inferred`, `--advanced`, `--web`), `ask` (incl. honest no-confident-match
  fallback), `find`, `answer` (extractive + citations), `--json` shape, `--explain`
  breakdown (BM25F factors; RRF detail noted for v2), and the error/exit-code
  contract in practice. Declared **normative**: e2e goldens derive from it;
  deviations go through the implementation tracker. Linked from: bundle index,
  cli-surface compare doc, handoff 0001 (formats normative), DOC-REGISTRY (trigger:
  any command/flag/output/exit change — update doc + goldens together).
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — Implementation tracker created + wired in · Cowork
- **Asked:** an implementation file tracking everything the building agent
  implements, updated at regular intervals / task completion; update the docs.
- **Did:** created [`implementation.md`](implementation.md) (`type: Implementation
  Tracker`): baseline table (✅ pre-build work), milestone tables for phases 1–3
  mirroring the handoffs (all ⬜, with per-row test counts + notes), a "Now working
  on" line the agent keeps current at regular intervals, a Deviations-from-spec
  section, and the binding update contract (flip on completion; never ✅ with
  failing tests). Wired it in: master prompt ground rule 5b + a "track as you go"
  line in all three phase prompts; CLAUDE.md docs-law item 4b + layout; registry
  row; bundle index entry.
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — docs/ is now an OKF-conformant bundle · Cowork
- **Asked:** update the existing documents with OKF as well.
- **Did:** added OKF frontmatter (`type` + title/description/timestamp) to every
  doc that lacked it — fux-plan (`Plan`), model-handoff-interview (`Succession
  Record`), worklog (`Log`), DOC-REGISTRY (`Registry`), all six compare docs
  (`Compare Doc`, status: accepted), the four directory READMEs (`Index`), ADR
  TEMPLATE (`ADR Template`). Created bundle-root [`index.md`](index.md) declaring
  `okf_version: "0.1"` with progressive-disclosure listing. Verified by script:
  all 26 docs/*.md now start with a frontmatter block. CLAUDE.md OKF section
  updated: bundle scope = `docs/` (+ future ingest cache); root CLAUDE.md/README
  are entry points outside the bundle.
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — Master prompt: one run for all three phases · Cowork
- **Asked:** one prompt to execute all of it, one by one.
- **Did:** wrote [`handoff/0000-master-prompt.md`](archive/master-prompt.md) —
  a single paste-ready prompt driving 0001 → 0002 → 0003 strictly in sequence with
  hard phase gates (DoD met + both suites green + ADRs + docs law + archive the
  pair + version bump before the next phase opens), phase reports appended to this
  worklog, stop-clean-on-failure semantics, and versions 0.20 → 0.21 → 0.22. Since
  the original plan gated 0002/0003 on Anton dogfood, the master prompt has Claude
  Code emit a `DOGFOOD.md` quickstart right after phase 1 so dogfooding runs in
  parallel with the remaining phases. Plan updated.
- **Decided / open:** continuous run accepted (dogfood in parallel, not as a gate).
- **Next:** paste `0000-master-prompt.md` into Claude Code and let it run.

## 2026-07-21 — Handoff+prompt pairs for everything finalized (0002, 0003) · Cowork
- **Asked:** create handoff + prompt documents covering *all* finalized work, not
  just v1.
- **Did:** wrote **0002 (Ingest v1.1)** — web crawling (urllib, robots.txt
  non-negotiable, depth/budget caps, HTML→MD via stdlib `html.parser`), CDP
  rendered pages (hand-rolled RFC 6455 client, fake-socket unit tests, Chrome
  optional), advanced tier (Docling/Tesseract extras, fidelity transitions,
  SKILL.md update), fixture HTTP-server e2e (no real network in tests), query-path
  isolation test. And **0003 (Engine v2)** — eval harness *first* (hit@1/5/MRR,
  recorded lexical baseline, the gate + reopen-instrument), distillation pipeline
  in `tools/distill/` (≤10 MB asserted, reproducible recipe, license check),
  stdlib-only inference (`fux.embed`, int8 dot products over BM25F candidates
  only), manifest-invalidated vector cache, RRF fusion + `--lexical-only`, ship
  gate = hybrid beats lexical on eval. Both pairs `blocked_by: 0001`. Plan now has
  the 3-phase build queue table; registry bumped.
- **Decided / open:** build order 0001 → dogfood → 0002/0003 in either order.
  Open question parked in 0003 for Arpit at review: commit vectors vs gitignore.
- **Next:** run the 0001 prompt in Claude Code.

## 2026-07-21 — Ideation (git-corpus bet) + v1 handoff & prompt written · Cowork
- **Asked:** Arpit's seed — the ingested corpus lives in git long-term and
  ultimately feeds product development. Think outside the box (uses, value, what to
  add), then a detailed implementation plan, with research.
- **Did:** researched signals (Knowledge-as-Code pattern Jan 2026; Karpathy LLM-Wiki
  paradigm; competitors semtools/rlama/qmd/llm-search — none version knowledge).
  Product-builder pass: winner = **product-memory corpus** (Arpit's seed, extended)
  — folded into fux-plan §6b + CLAUDE.md (deterministic diff-friendly cache is now a
  hard requirement); parked three proposals with OKF frontmatter:
  `research-to-spec`, `knowledge-diff` (fux diff/log, time-travel), and
  `audit-evidence-trail` (deterministic cited answers as evidence chain; Plane
  seed). Wrote the **detailed v1 implementation plan**:
  `handoff/0001-query-cli-v1-handoff.md` (DoD, in/out scope — web/CDP/OCR pushed to
  v1.1, embeddings v2; module layout; hard constraints; edge cases; both test
  suites; open questions; ADRs 0001–0004) + `0001-query-cli-v1-prompt.md`
  (paste-ready, explore→plan→implement→verify→close-out incl. archiving the pair
  and bumping to 0.20.0). Pre-mortem gate folded into the handoff (scope-drown,
  chunker quality, golden brittleness, parser correctness, cross-platform).
- **Decided / open:** git-corpus bet adopted into plan + CLAUDE.md ✅; v1 scope cut
  ✅ (local inferred-tier only). Nothing open.
- **Next:** run the 0001 prompt in Claude Code; dogfood the result in Anton.

## 2026-07-21 — Proposals dir, doc archiving, OKF conformance · Cowork
- **Asked:** add to CLAUDE.md — (1) proposal docs for later-stage ideas, (2) archive
  implemented docs, (3) follow the OKF pattern for the fux package and features.
- **Did:** identified OKF = **Google's Open Knowledge Format v0.1** (June 2026 open
  spec: markdown + YAML frontmatter bundles, required `type` field, index.md
  progressive disclosure, log.md history, citations; permissive consumption) — read
  the full spec; it's near-identical to Fux's native substrate, so conformance is
  cheap interop. CLAUDE.md: proposals added to lifecycle step 0
  (`docs/proposals/`, `status: proposed`, graduate to compare/plan), archive rule
  (`docs/archive/`, move on completion with `status: implemented` + ADR link), new
  "Follow the OKF pattern" section (type on every knowledge doc, cache = OKF
  bundle, worklog = log.md convention). Created `proposals/` + `archive/` READMEs;
  updated ingest doc (cache is an OKF bundle), DOC-REGISTRY (2 new rows), plan.
- **Decided / open:** all three ✅. Nothing open.
- **Next:** plan → handoff → prompt for query CLI v1 (OKF conformance now in scope).

## 2026-07-21 — Ingest types + e2e suite + doc registry; CLAUDE.md refreshed · Cowork
- **Asked:** ingest images/JSON/txt/YAML too; a thorough, *maintained* e2e test suite
  in a sibling dir; hooks + docs that prompt updating stale documents via a separate
  tracking file; update CLAUDE.md with the useful information. Research it.
- **Did:** researched OCR (Tesseract offline/open-source; Docling OCR stage; OCR
  quality is a first-class retrieval bottleneck → OCR belongs in the judge-able
  advanced tier), doc-freshness practice (last-reviewed signals, owners, docs-in-
  same-change, CI freshness scoring), pytest e2e patterns (per-dir conftest, golden
  files, subprocess CLI runs). Added file-type section to ingest doc (images:
  metadata stub inferred / OCR advanced; JSON stdlib-flattened; YAML fenced text —
  stdlib has no YAML parser; txt native). Created **`docs/DOC-REGISTRY.md`** (trigger
  + last-verified per doc; hook reads it at session end, advisory + fail-open; also
  step 5 of the generated agent contract). CLAUDE.md: replaced the stale
  "decisions pending" scope with the decided design summary, added `tests_e2e/`
  mandate (fixture corpus + goldens, maintained), registry in the docs law, layout
  refresh, and a standing **auto-fold rule** (durable session knowledge → CLAUDE.md
  in the same change). Synced plan + agent-integration doc.
- **Decided / open:** all three additions ✅. Nothing open.
- **Next:** plan → handoff → prompt for query CLI v1 (now includes e2e suite +
  registry hook in scope).

## 2026-07-21 — Sub-decisions resolved with research; `init` → `setup` · Cowork
- **Asked:** research the open sub-decisions (reranker-beyond-RRF; chunking unit;
  BM25F field weights) and rename `fux init` to `fux setup`.
- **Did:** researched chunking (structure-aware heading-based wins — up to ~9-pt
  recall swing, 15-pt accuracy spread across strategies; 256–512-token sweet spot)
  and BM25F (weighted-tf-then-saturate per Lucene `combined_fields`; titles 2–5×
  body is standard; k1=1.2/b=0.75 defaults). Resolved all three in
  `query-engine.compare.md` with references: **no reranker** (cross-attention needs
  ~22 M-param/~80 MB models — 8× over the 10 MB budget; RRF stays), **chunking =
  heading-based**, 256–512 tokens, heading-path context, code/tables atomic,
  `file:line` boundaries; **BM25F = heading 3.0 / path 2.0 / body 1.0**, overridable
  in `fux.toml`. Renamed `fux init` → **`fux setup`** across cli-surface,
  agent-integration, compare README, plan, handoff (worklog history left intact).
- **Decided / open:** all sub-decisions ✅ — **nothing is open**. Reopen-triggers
  recorded (eval-set evidence only).
- **Next:** plan → handoff → prompt for query CLI v1.

## 2026-07-21 — Agent-integration accepted; one-SKILL.md verdict; `fux init` · Cowork
- **Asked:** accept agent-integration; are per-tool skills (Claude/Copilot/Kiro) a
  good idea; single setup command, interactive + flags. Research it.
- **Did:** researched — **Agent Skills is an open standard since Dec 2025**
  (agentskills.io); by Mar 2026, 32+ tools incl. Copilot, Kiro, Codex, Cursor,
  Gemini CLI read the same `SKILL.md`, so **one skill file serves all tools** (the
  old build's per-platform skillgen is obsolete). Added Skills section to
  agent-integration doc (layer cake: AGENTS.md=when, SKILL.md=how, hooks=enforced;
  ship `fux-query` + `fux-ingest` skills). Added `fux init` to cli-surface doc:
  interactive wizard default, flag-per-prompt, `-y`, idempotent (npm init / gh auth
  / clig.dev pattern). Synced plan + compare README.
- **Decided / open:** agent-integration ✅; skills = one SKILL.md ✅; `fux init` ✅.
  **All major forks now decided.** Open sub-decisions only: reranker-vs-RRF (rec:
  RRF), chunking unit, BM25F weights.
- **Next:** plan → handoff → prompt for query CLI v1.

## 2026-07-21 — CLI verbs + CDP accepted; numpy-vendoring disproven; agent-integration proposed · Cowork
- **Asked:** accept cli-surface + ingest verdicts; ingest must also work over Chrome
  DevTools Protocol; could numpy be vendored as internal files and resynced per
  build; new fork — Claude/Copilot/Kiro hooks or md files (or both, or better) so
  agents know to query fux; everything backed by references.
- **Did:** researched CDP (JSON-RPC over WebSocket; stdlib has no WS client → hand-
  rolled RFC 6455 client on `socket`, user's own headless Chrome, `render = "cdp"`
  config), numpy internals (core is platform-compiled C extensions + BLAS — not
  copyable Python; vendoring = per-platform build farm), and the agent-instructions
  landscape (AGENTS.md = Linux Foundation standard read by Copilot/Cursor/Codex/
  Windsurf/Zed, picked up by Kiro + Claude Code; Kiro steering + hooks; Claude Code
  `UserPromptSubmit`). Marked cli-surface accepted; added CDP section to ingest doc;
  added numpy-vendoring resolution with proof to packaged-model doc; wrote
  `agent-integration.compare.md` (proposed: files + hooks from one `fux init-agents`
  generator, MCP deferred). Synced plan + compare README.
- **Decided / open:** CLI verbs ✅; CDP ingestion ✅; numpy vendoring ✗ (stdlib
  stands). Open: agent-integration verdict; reranker-vs-RRF; chunking; BM25F weights.
- **Next:** Arpit calls agent-integration → then plan → handoff → prompt for v1.

## 2026-07-20 — Verdicts confirmed + refinements; numpy resolved out · Cowork
- **Asked:** accept engine/ingest/model verdicts. Refinements: friendlier CLI
  commands than `fux query --flags`; "what if I don't use numpy?"; ingest as a skill
  + usable from other Python scripts; ingest follows links and their attachments
  multiple levels deep; converted docs need metadata for maintenance/traceability.
- **Did:** wrote `cli-surface.compare.md` (proposed `fux ask`/`find`/`answer`, verb
  per intent). Resolved numpy in `packaged-model.compare.md`: **stdlib-only** — with
  candidate-only ranking (BM25F top-200 → dot products) query latency is single-digit
  ms without numpy; chunk vectors precomputed at ingest. Extended
  `ingest-strategy.compare.md`: per-file traceability frontmatter (source, sha256,
  fidelity, converter, origin/url/parent/depth — first dogfood of the hand-rolled
  frontmatter parser), library-first `fux.ingest` API + agent skill, fenced `--web`
  crawling (max_depth, same_domain, robots.txt, attachments). Synced plan + compare
  README.
- **Decided / open:** all four major forks ✅ accepted; numpy ✅ out. Open: CLI naming
  verdict (proposed verbs), reranker-vs-RRF (rec: RRF only), chunking unit, BM25F
  field weights.
- **Next:** Arpit calls the CLI naming → plan → handoff → prompt for query CLI v1.

## 2026-07-20 — Query-CLI decisions locked; researched + 4 compare docs · Cowork
- **Asked:** decide the three forks with additions — two-tier ingest (inferred +
  advanced/agent-triggered) + manifest + config-driven dirs; staged engine v1/v2/v3
  with a look at BM25 alternatives; output option 2 plus non-LLM synthesis via a
  model *built into the package*; hard rule — no external model, but a bundled model
  ≤10 MB is allowed. Research it.
- **Did:** web-researched retrieval (BM25F, SPLADE, cross-encoders, RRF hybrid ~91 %
  recall), tiny packageable models (Model2Vec/Potion ~8 MB, numpy dep), and non-LLM
  synthesis (TextRank/LexRank extractive). Rewrote `query-engine`, `query-output`,
  `ingest-strategy` compare docs with accepted verdicts; added
  `packaged-model.compare.md`. Synced `fux-plan.md` (Decisions §6) + compare README.
- **Decided / open:** engine = BM25F → +bundled static embeddings via RRF → agent
  surface; output = passages default + `--answer` extractive (no LLM); ingest =
  two-tier + manifest + `fux.toml`; model = ≤10 MB static embeddings, stdlib inference
  + optional numpy. **Honest limit recorded:** ≤10 MB can't *generate* prose —
  `--answer` selects/orders source sentences. Open: stdlib-vs-numpy, reranker-vs-RRF,
  chunking unit, BM25F field weights.
- **Next:** resolve the open sub-decisions, then plan → handoff → prompt for query
  CLI v1.

## 2026-07-20 — Pivot to a document-query CLI; three compare docs · Cowork
- **Asked:** hold the rule engine; make the first deliverable a CLI that answers
  natural-language questions over documents in a defined set of folders. Produce a
  compare doc wherever there are multiple options, decide by reading them.
- **Did:** wrote `docs/compare/query-engine.compare.md`, `query-output.compare.md`,
  `ingest-strategy.compare.md` (+ `compare/README.md`). Grounded with references
  (BM25, RAG, sentence-transformers, MarkItDown/Docling). Synced the pivot into
  CLAUDE.md (scope + compare step 0), `fux-plan.md`, `model-handoff-interview.md`.
- **Decided / open:** proposed verdicts recorded in each compare doc; **all three
  forks await Arpit's call.** The engine fork also decides whether `$0`/no-LLM still
  binds this tool.
- **Next:** Arpit reads the compare docs and picks a verdict per fork → then
  plan → handoff → prompt for query CLI v1.

## 2026-07-20 — From-scratch rebuild: CLAUDE.md + package skeleton · Cowork
- **Asked:** review the old (non-working) build for context, then write a fresh
  CLAUDE.md and do basic Python package setup (keep the name, bump the version).
- **Did:** reviewed `archive/`; wrote binding CLAUDE.md (scope, constraints,
  lifecycle, docs-in-sync); scaffolded `src/fux/` (hatchling, v0.19.0, CLI +
  `FuxError`), README, `docs/fux-plan.md`, `docs/model-handoff-interview.md`,
  `docs/adr/TEMPLATE.md`. 4 smoke tests pass.
- **Decided / open:** src/ layout + hatchling; version 0.19.0 (bumped from old
  0.18.0); constraints carried forward from the old build.
- **Next:** (superseded by the pivot entry above).
