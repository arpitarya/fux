---
type: Log
title: Worklog — the running session handoff
description: Per-exchange rolling record (OKF log.md convention, date-grouped, newest first) so a new chat picks up cold.
timestamp: 2026-07-21T00:00:00Z
---

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
  all OS). Windows suite runs for the first time in this PR — failures fix
  forward there.
- **Next:** merge; Anton dogfood continues.

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
- **Did:** created [`cli-examples.md`](cli-examples.md) (`type: Reference`) — worked
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
- **Did:** wrote [`handoff/0000-master-prompt.md`](handoff/0000-master-prompt.md) —
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
