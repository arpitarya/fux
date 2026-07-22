# CLAUDE.md — coding-agent guide for the Fux engine (rebuild)

Fux is a portable, agent-aware knowledge engine. The *why* behind code is written
as version-controlled **rules** bound to the exact lines they explain, read by
agents *before* they touch anything, and checked **deterministically** — never by
a model — so a reason can't be silently deleted by someone confident, and can't
quietly go stale.

This is a **from-scratch rebuild**. The previous implementation (kept for reference
under [`archive/`](archive/)) tried to ship the whole vision at once and did not
work. This time the scope is deliberately narrow: **the rules substrate + the fix
loop**, done well, dogfooded in Anton, before anything else is added.

This file is binding. Read it before your first substantive change.

## What we are building (scope)

**First deliverable: the document-query CLI — design decided 2026-07-20/21;
v1 shipped 2026-07-21 (v0.20.0, ADRs 0001–0004); v1.1 web/CDP/advanced shipped
same day (v0.21.0, ADR 0005); v2 hybrid engine shipped same day (v0.22.0,
ADRs 0006–0007 — bundled 7.93 MB model, stdlib inference, RRF; eval gate
passed as a tie, hybrid enabled by default, `--lexical-only` preserves v1)** (every fork + sub-decision closed in [`docs/compare/`](docs/compare/);
read those before proposing changes — each records its reopen-trigger). The shape:

- **Engine:** v1 **BM25F** (stdlib; heading 3.0/path 2.0/body 1.0, k1=1.2, b=0.75) →
  v2 bundled **static-embedding model ≤10 MB** fused via **RRF** (no reranker — RRF
  only) → v3 agent surface. **No external model or service, ever; pure-stdlib
  inference (no numpy — vendoring disproven).**
- **CLI:** `fux ask` (passages) · `fux find` (files) · `fux answer` (extractive,
  cited — never generative) · `fux setup` (interactive wizard + full flags + `-y`) ·
  `fux ingest`. Modifiers: `--json`, `--explain`.
- **Ingest:** two-tier (inferred → advanced/agent-triggered), config `fux.toml`,
  manifest + per-file provenance frontmatter, chunking = structure-aware
  heading-based 256–512 tokens. Types: md/txt/code native; office+PDF via opt-in
  converters; JSON flattened (stdlib); YAML as fenced text (no stdlib parser);
  images = metadata stub (inferred) / OCR (advanced, Tesseract/Docling); web via
  urllib + fenced crawling + CDP rendered pages (hand-rolled RFC 6455 client).
- **Agent integration:** `fux setup --agents --skills --hooks` → AGENTS.md canonical
  + tool pointers, one SKILL.md (open standard) with `fux-query`/`fux-ingest`
  skills, Claude Code + Kiro hooks. MCP deferred (needs ADR).

**On hold (do not build yet, kept as the long-term core):**

1. **The rules substrate.** Frontmatter rules bound to code (file + line/symbol),
   parsed and validated with a hand-rolled, stdlib-only parser.
2. **The fix loop.** `check` doesn't stop at pass/fail — a blocking finding *tells
   the agent how to fix it*. The eventual killer feature.

Explicitly **out of scope for now** (was in the old build; do not resurrect without
an ADR and Arpit's sign-off): graph extraction/viewer, recall/embeddings, MCP
server, memory capture/governance, federation/packs, the compliance Plane.

**The corpus is a product asset, not a disposable index.** The ingest cache is
designed to be committed to git and maintained long-term, ultimately feeding product
development (specs, decisions, agent-driven builds — see PLAN.md §6b). Therefore
deterministic, diff-friendly cache output (sorted walks, stable serialization, POSIX
relative paths) is a hard requirement everywhere, and downstream corpus features
(diff/log, research-to-spec, audit trail) live as proposals in
[`docs/proposals/`](docs/proposals/). **Two tiers (2026-07-21):** the *curated*
corpus is per-file Markdown, committed; *bulk* corpora (big crawls/imports) get
**no file cache at all** — converted text lives as rows inside the substrate db
(one file on disk at any corpus size; 100k documents-as-files is impractical,
git or not). Commit the recipe (fux.toml + manifest), never the warehouse.

**Who Fux is for (2026-07-21):** an agent inside Copilot/Claude/Kiro querying
**documentation, decisions, and links** — not the code itself. Semantic enrichment
may ride the *host session's* model via skills (written back as reviewable
frontmatter); Fux's own code never calls a model — `$0` holds either way.

**Litmus for any new work (changed 2026-07-21, Arpit):** do **not** design in
reference to Anton. The design point is a **very large-scale project inside a
corporation** — think a 10k-engineer company's mega-project:

- **Scale is the default, not the trigger** — 10⁵–10⁶ documents, sprawling
  Confluence/SharePoint/wiki estates, thousands of repos, millions of links.

- **Enterprise realities are design inputs** — Windows-first fleets, proxies and
  SSO in front of every internal site, air-gapped/regulated environments,
  multi-team corpora with access boundaries, audit and compliance demands.

- **Fux's laws are enterprise features, not constraints** — `$0`/stdlib = a
  trivially auditable supply chain and no procurement; offline/no-API = no data
  ever leaves the tenant; deterministic = compliance-grade reproducibility.

The question per feature: *"does this hold up in that corporation's
mega-project?"* Anton remains a convenient small-scale testbed, but it is no
longer the priority filter.

## Non-negotiable constraints

- **`$0`, stdlib-only runtime.** No third-party *runtime* dependencies. The
  frontmatter parser and schema validator are hand-rolled on purpose — that is the
  zero-dependency guarantee and the product's central promise. Do not replace them
  with PyYAML / jsonschema. Dev/test tooling may use extras; the runtime path may
  not.
- **Deterministic — no LLM in the maintenance path.** `check`/`fix`/`verify` must be
  reproducible parse/AST/shell. No maintenance path may ever call a model — not to
  be "smarter" at ingest, not to summarize, not once. The moment a model sits in the
  enforcement path, the auditability and air-gap story are gone.
- **Python ≥ 3.11** (`tomllib`, modern typing). Match the surrounding style and
  density.
- **Small and per-repo.** The engine stays small. Scale, if it ever comes, is
  federation (git, CI) — never a server, never a platform.

## How work happens here (the lifecycle)

Every non-trivial feature moves through this pipeline, and the artifacts are
committed:

0. **Compare (when there's a fork).** Whenever a decision has multiple viable
   options, write a *compare doc* in [`docs/compare/`](docs/compare/) first —
   debate, matrix, grounded references, and a proposed verdict Arpit accepts or
   overrides — before committing to a plan. This is a standing rule.
   **Proposals (when it's an idea, not a fork).** An idea worth keeping but not
   being built now gets a *proposal doc* in [`docs/proposals/`](docs/proposals/) —
   same rigor (context, sketch, references), `status: proposed`. Proposals are
   parked, not lost: when picked up they graduate into a compare doc or plan entry.
1. **Plan** — the design of record. Update [`docs/PLAN.md`](docs/PLAN.md)
   before building: what, why, scope in/out, the decision.
2. **Handoff** — a self-contained spec: context, definition-of-done, constraints,
   key files, edge cases, tests, open questions. Lives under
   [`docs/handoff/`](docs/handoff/).
3. **Prompt** — the paste-ready Claude Code prompt that executes the handoff
   (explore → plan → implement → verify). Lives under [`docs/handoff/`](docs/handoff/)
   alongside its handoff.

Then, on completion:

4. **One feature → one ADR.** Every feature ships with exactly one Architecture
   Decision Record in [`docs/adr/`](docs/adr/) (see
   [`docs/adr/TEMPLATE.md`](docs/adr/TEMPLATE.md)): the decision, the context, the
   alternatives, the consequences.

**Every rule, ADR, and material decision must carry a reference** — a paper, a blog
post, or a concrete example link — that grounds *why* it was chosen. A rule or ADR
with no reference is incomplete. Ground the claim; don't assert it.

**Archive implemented docs.** When a handoff/prompt pair (or a proposal) is fully
implemented and its ADR is written, move it to [`docs/archive/`](docs/archive/) in
the same change, stamping `status: implemented` + the ADR link in its frontmatter.
Active directories hold *live* work only; history stays greppable, not underfoot.
(Repo-level `archive/` = the old build; `docs/archive/` = completed doc artifacts.)
**Naming (Arpit, 2026-07-22): archived handoffs/prompts are prefixed by the
release version they shipped, not their in-flight index** — e.g. an active
`docs/handoff/NNNN-name.md` archives as `docs/archive/vX.Y.Z-name.md`. The `NNNN`
index lives only in `docs/handoff/` while work is in flight; version is the
durable, greppable key once shipped. Orchestrator/meta docs that map to no single
release keep an unversioned name (e.g. `master-prompt.md`).

## Follow the OKF pattern (package and docs)

Fux follows Google's **Open Knowledge Format** (OKF v0.1) — an open spec for
knowledge as a directory of Markdown files with YAML frontmatter. It is nearly
identical to Fux's native substrate, so conformance is cheap and buys
interoperability with every OKF consumer:

- **The bundle is `docs/`** (plus the ingest cache once built) — root index at
  [`docs/index.md`](docs/index.md), which declares `okf_version: "0.1"`. Repo-root
  CLAUDE.md/README.md are tool entry points outside the bundle.
  **Convention (Arpit, 2026-07-21): ALL-CAPS markdown files carry no YAML
  frontmatter** — GLOSSARY.md, DOC-REGISTRY.md, DOGFOOD.md, IMPLEMENTATION.md,
  WORKLOG.md etc. are entry-point/tracker files like CLAUDE.md/README.md, exempt
  from the `type` requirement. Lowercase docs conform as before.
- **Frontmatter `type` on every knowledge doc** (the only OKF-required field) —
  e.g. `type: Compare Doc`, `type: Proposal`, `type: ADR`, `type: Handoff`; ingest
  cache files get `type: Ingested Document`. Our provenance keys (source, sha256,
  fidelity, …) are legal OKF extensions — consumers must preserve unknown keys.
  **All existing docs conform as of 2026-07-21**; every new doc conforms from birth.
- **The ingest cache is an OKF bundle**: per-directory `index.md` (progressive
  disclosure — agents see what exists before opening files), bundle-relative links,
  `# Citations` sections where claims trace to sources.
- **`log.md` semantics**: our `docs/WORKLOG.md` follows OKF's log convention
  (date-grouped, newest first). It is ALL-CAPS, so per the convention above it
  carries no frontmatter — the log.md semantics still hold.
- Conformance bar (OKF §9): parseable frontmatter + non-empty `type` everywhere; be
  permissive when consuming (unknown types/keys/broken links are not errors).

Reference: [OKF spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) ·
[annotated guide](https://okf.md/spec/). New features and their docs follow this
pattern from birth.

## Documentation style (required)

**No large paragraphs — they are hard to read.** When writing or updating any doc
in this repo:

- Split dense prose into **short points** (bullets or numbered lists), one idea
  per point.

- Keep paragraphs to **3–4 lines max**; if it runs longer, it's two points.

- Make it **roomy**: blank lines between points and sections; use tables for
  option/field comparisons; use headings to break up long sections.

- Lead each point with the takeaway (bold it when it helps scanning).

- When you touch a doc that has a wall of text, split it in the same change —
  the docs law's "fix stale docs on contact" applies to *form*, not just facts.

## Keep the docs in sync with the code (required)

**Every task updates the documentation — no exceptions.** This holds whether the task
touched code or not: a decision, a scope change, or a plan is also documentation. A
task is not "done" until the docs are true. Documentation is maintained, not
appended-to-and-abandoned — when a doc goes stale, fix it in the same change. At
minimum, per task, check and update:

1. **[`docs/PLAN.md`](docs/PLAN.md)** — design of record. Keep its status
   notes truthful when behaviour or scope changes.
2. **[`README.md`](README.md)** — the public front door. Update whenever the
   install/use surface, command list, or guarantees change.
2b. **[`CHANGELOG.md`](CHANGELOG.md)** — every version bump gets an entry, and
   the latest entry is mirrored into README § What's new in the same change.
3. **[`docs/INTERVIEW.md`](docs/INTERVIEW.md)** — the
   agent-succession handoff. **Read it before your first substantive change.**
   Update its "state of play" when direction, strategy, or a major decision changes,
   and add yourself to its maintainer line when you do. Every future model/session
   is now this document's maintainer — you will retire too; leave it better.
4. **[`docs/WORKLOG.md`](docs/WORKLOG.md)** — the running session handoff (see below).
4b. **[`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md)** — the live build
   tracker: milestone-level ✅/🟡/⬜ per phase. Three binding rules:

   - **When a plan/handoff is written:** its milestone table is **pre-registered**
     in IMPLEMENTATION.md (all ⬜) in the same change — every plan arrives with
     its tracker rows already in place.

   - **When building:** the agent updates the row **at every single milestone
     completion** (status + test count + one-line note) — per milestone, never
     batched at phase end — and keeps "Now working on" current at regular
     intervals. Never ✅ with failing tests.

   - **On EVERY execution, whatever the case:** success, failure, blocked,
     interrupted, or abandoned — the file is updated before the session ends.
     A failed run sets 🟡/⛔ with a one-line why; there is no outcome that
     skips the update.
5. **[`docs/DOC-REGISTRY.md`](docs/DOC-REGISTRY.md)** — the doc freshness tracker:
   one row per maintained doc with its update trigger and last-verified date. If your
   change fires a trigger, update the doc *and* bump its row. New maintained doc →
   new row, same change.
6. **The relevant ADR** and any guide/schema the change touches.
7. **[`tests/`](tests/)** — every behaviour change ships with a test.

**Auto-fold useful information into this file.** When a session produces durable,
repo-wide knowledge — a decision, a constraint, a disproven idea, a pattern worth
keeping — fold it into CLAUDE.md (concisely; details live in the linked docs) in the
same change. CLAUDE.md is the always-loaded contract; if a future agent would act
differently knowing something, it belongs here or is linked from here.

## Session continuity — the running worklog (required)

At the end of **every substantive exchange**, append an entry to
[`docs/WORKLOG.md`](docs/WORKLOG.md): what was asked, what was done, what was
decided or left open, and the single next step. This is a rolling exit-interview so a
*new chat can pick up cold* without re-deriving context. **This applies in both Cowork
and Claude Code** — the environment doesn't matter; the continuity does. Newest entry
on top; keep entries short and true. Distinct from `INTERVIEW.md` (the
strategic, cross-session succession record) — the worklog is the granular,
per-exchange trail. Update both when the exchange changed direction.

## Layout

```
src/fux/            the engine (import: `fux`); CLI entry `fux.cli:main`
  __init__.py       __version__ lives here (single source of truth)
  cli.py            argument dispatch; catch/render errors only at this boundary
  errors.py         the single FuxError — flat, no subclass hierarchy
docs/
  PLAN.md           design of record
  INTERVIEW.md      agent-succession handoff (read first)
  WORKLOG.md        per-exchange session handoff (append every exchange; OKF log.md style)
  IMPLEMENTATION.md live build tracker (milestone ✅/🟡/⬜; updated EVERY execution)
  DOC-REGISTRY.md   doc freshness tracker (triggers + last-verified)
  GLOSSARY.md       every recurring term, defined once
  example/          copy-from contracts — CLI.md (I/O), TOML.md (config), SETUP.md (setup+hooks), SKILLS.md, API.md
  compare/          decision records — debate, matrix, verdict, reopen-triggers
  proposals/        parked ideas — same rigor, status: proposed; graduate to compare/plan
  handoff/          plan → handoff → prompt artifacts (live work only)
  adr/              one ADR per feature (+ TEMPLATE.md)
  archive/          implemented handoffs/prompts/proposals (version-named vX.Y.Z-name.md)
tests/              unit suite (fast)
tests_e2e/          end-to-end suite: real CLI + fixture corpus + golden files
archive/            the old, non-working build — reference only, do not import
CHANGELOG.md        version history (repo root; latest entry mirrored in README)
```

## Error contract

Catch and render errors only at the boundaries (CLI `main`, hook entrypoints).
Internals keep raising. Raise the single `FuxError` (`src/fux/errors.py`) for
expected user-facing failures — **no subclass hierarchy**. CLI exit codes:
`0` ok · `1` error · `2` blocking (strict) · `130` interrupted.

## Build & test

```bash
uv sync                       # install (dev extras)
uv run pytest -q tests        # unit suite (fast; every behaviour change adds here)
uv run pytest -q tests_e2e    # end-to-end suite (see below)
uv run fux --version
```

**Two test suites, both maintained (required).** `tests/` is the fast unit suite.
**`tests_e2e/`** is a sibling directory that tests the package *as a user*: it
installs/imports the built package, runs the real CLI (`fux setup -y`, `fux ingest`,
`fux ask/find/answer`) via `subprocess` against a committed **fixture corpus**
(`tests_e2e/corpus/` — small real md/txt/json/yaml/pdf/image files) and compares
against **golden files** (`tests_e2e/goldens/` — expected outputs, updated
deliberately when behaviour changes intentionally, never regenerated blindly). Each
suite gets its own `conftest.py` (per-directory fixtures — standard pytest layout).
The e2e suite is **maintained, not disposable**: a feature is not done until both
suites cover it and pass. When the package is "done" for a milestone, the e2e suite
is the proof.

## Package identity (do not change casually)

- Distribution name: **`fux-engine`** (unchanged). Import package: **`fux`**.
- Version: **`0.24.0`** (0.18.0 old build → 0.19.0 skeleton → 0.20.0 v1 →
  0.21.0 v1.1 web/CDP/advanced → 0.22.0 v2 hybrid → 0.23.0 v3 substrate →
  0.23.1 docs & examples patch → 0.24.0 debug & observability). Bump in
  `src/fux/__init__.py` only.

## Merge wall — what actually blocks a merge (2026-07-22)

**There are no required status checks on `main`.** `fux gate` and `ai-review`
still run on every PR and their results are visible, but they do **not** block
merging (removed at Arpit's instruction, 2026-07-22). What remains:
`enforce_admins: true`, no force-push, no deletion — history is protected, the
quality gate is not.

Practical consequence for any agent working here: **CI green is now your
responsibility to check, not something the wall guarantees.** Before merging,
read `gh pr checks <n>` yourself and do not merge on red. The source of truth
for protection is [`.github/branch-protection.json`](.github/branch-protection.json);
restoring the wall means putting the two contexts back and re-applying.

## Hard-won build knowledge (auto-folded, 2026-07-22 — phase 5)

- **Write the stdout-purity test before the instrumentation it will gate.**
  M1 of the debug feature added the "goldens/`--debug=trace` stdout is
  byte-identical to `off`" test *before any `dbg()` call site existed* — so it
  was still exercising real code by M6, not trivially passing against an
  empty emitter. The pattern generalizes: when a hard invariant gates a whole
  feature, prove it can fail before you make it pass.
- **One config-load wiring point, not one per command.** `config.load()` calls
  `debug.apply_config()` itself, so every command (and every library caller)
  gets `[debug]` wired automatically — no `cli.py` handler had to be touched.
  `debug.init_from_cli()` (the `--debug` flag) is the one exception that must
  be called explicitly, from `cli.main()`, before `load()` runs.
- **The network-import fence applies to diagnostics too.** `fux doctor`
  cannot live-probe a CDP port (`import socket`) because
  `tests/test_import_fence.py` forbids network imports outside `ingest/` —
  a standing rule, not negotiable per-feature. Capability checks that would
  need the network stay binary-presence checks (`shutil.which`) instead.
- **`off` must cost nothing, including argument evaluation.** `dbg()` checks
  `is_enabled()` first and returns before formatting — but the *caller's*
  arguments are still evaluated eagerly (Python has no lazy call args), so
  call sites must keep those cheap (`len()`, not string-building) rather than
  relying on the guard alone.

## Hard-won build knowledge (auto-folded, 2026-07-22 — phase 4)

- **Git carries recipe *and* state.** `fux.toml` + `fux.lock` + `.fux/state/`
  are committed; `.fux/index/` is derived and gitignored. A clone answers before
  any ingest — and with the df sidecar it answers *exactly*, not approximately.
- **The df sidecar is load-bearing, not redundant statistics.** Lean can
  re-derive exact `tf` but never corpus-level `df`/`n`/`avg_wlen`. Without
  `.fux/state/df/`, "identical rankings across profiles" silently becomes
  "approximately identical". Never delete it to save bytes (it costs 9 B/doc).
- **Keep the zero-candidate early return in `_passages`.** It looks like it
  blocks FuxVec's rescue; it does not (the rescue case is *doc-side* zero
  overlap, served by the third RRF list). Removing it makes "No confident
  matches" unreachable, because a binary prefilter always has a nearest
  neighbour — measured noise 0.23–0.26 cosine vs a true rescue's 0.34.
- **Parity is scoped to `--lexical-only`.** The hybrid lists grow by design
  (dense_global at M5, graph at M6), so hybrid goldens change *with eval
  evidence*; the four lexical goldens must stay byte-identical forever.
- **Storage at scale ≠ query at scale.** `postings` is populated and indexed but
  not read at query time; a 100k query still loads the whole index (~10 s).
  Scoped in ADR 0011 — the head of the next phase.
- **Extrapolations from this repo's own docs are pessimistic** for the state
  plane (long ids, wide vocabulary → signatures pinned at the 128 B cap):
  projected 351 B/doc, measured 230 B/doc on the synthetic corpus.

## Hard-won build knowledge (auto-folded, 2026-07-21)

- **No wall-clock output anywhere on the maintenance path.** `converted_at` and
  cache `timestamp` derive from `SOURCE_DATE_EPOCH`/source mtime (ADR 0002) —
  wall clocks break the byte-identical re-ingest guarantee.
- **BM25F means weight-then-saturate once** — never sum per-field BM25 (ADR 0003).
- **Skipped ≠ drift:** files that can't ingest (binary, missing extras) must not
  surface as "new" in `--check` — `skip_reason()` is shared by convert and drift.
- **Stopwords are stripped only in the answer-overlap factor**, never in the
  index; and answer sentences under 35 % of the best score are dropped (both
  earned from fixture-corpus smoke noise, ADR 0003).
- **Goldens are pinned to the extra-less environment** — installing `[ingest]`
  changes corpus size and therefore every idf/score; office coverage is a
  separate `skipif` test.
