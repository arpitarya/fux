# Fux — design of record (rebuild)

*This is the design of record. Keep it truthful: update it in the same change that
alters behaviour, scope, or a resolved decision (CLAUDE.md binds you to this).*

## 1. What Fux is

A portable, agent-aware knowledge engine. The reason behind code is written as
version-controlled **rules** bound to the exact lines they explain, read by agents
before they act, and checked **deterministically** — never by a model.

## 2. Why the rebuild

The prior build (in [`archive/`](../archive/)) reached ~0.18.0 and pursued the full
vision at once — graph, recall, verify, MCP, memory, federation. It did not work as
a whole. The rebuild resets scope to the smallest thing that delivers the core
promise and can be dogfooded in Anton.

## 3. Constraints (non-negotiable)

`$0` stdlib-only runtime · deterministic, no LLM in the maintenance path ·
Python ≥ 3.11 · small and per-repo. See CLAUDE.md for the full contract.

## 4. Scope

**First deliverable (current):** a **CLI that answers natural-language questions over
documents in a defined set of folders.** The rule engine is *held* (kept as the
long-term core). Design forks are being settled in [`compare/`](compare/) before
building — see §5.

**Held (long-term core, not being built yet):** (1) the rules substrate — frontmatter
rules bound to code, hand-rolled stdlib parser + validator; (2) the fix loop —
`check` findings are repair instructions, not just verdicts.

**Out (for now, needs an ADR to revive):** graph, recall/embeddings, MCP server,
memory capture/governance, federation/packs, compliance Plane.

## 5. Lifecycle

Compare (when there's a fork) → Plan → Handoff → Prompt → build → **one ADR per
feature**. Every rule and ADR carries a reference (paper, blog, or example link).
See CLAUDE.md.

## 6. Decisions (accepted 2026-07-20)

The query CLI is a **staged hybrid, entirely `$0` and with no external model** — any
"smart" component is built and packaged inside this package at ≤10 MB with no required
external deps. Full debate + references in [`compare/`](compare/).

- **Engine:** v1 **BM25F** (stdlib lexical) → v2 add a **bundled static-embedding
  model** and fuse lexical+semantic with **Reciprocal Rank Fusion** → v3 **agent
  surface** (ask / reply / explain). SPLADE and cross-encoder rerankers deferred (out of
  the size budget).
- **Output:** ranked **passages** by default; `--files` locator; `--answer` =
  **extractive** synthesis (bundled embeddings + TextRank) with citations — no external
  LLM, deterministic, hallucination-free. (Generation in ≤10 MB is not feasible; we
  select/order source sentences, we don't generate.)
- **Ingest:** two-tier **`fux ingest`** — fast **inferred** conversion by default,
  **advanced** (layout/table/OCR) on demand or agent-triggered; a **manifest** tracks
  inferred files; **config file** (`fux.toml`) maps each file type to its source dirs.
  Extensions (accepted 2026-07-20): every cached file carries **traceability
  frontmatter** (source, sha256, fidelity, converter, origin/url/parent/depth) — the
  hand-rolled frontmatter parser's first dogfood; ingest is **library-first**
  (`fux.ingest` public API, CLI wrapper, agent **skill**); and it ingests **links +
  their attachments multiple levels deep** behind a fenced `--web` path (depth-capped,
  same-domain default, network never on the query path).
- **Packaged model:** Model2Vec/Potion-class static embeddings, distilled offline,
  quantized to ≤10 MB; **pure-stdlib inference — numpy resolved: not used** (candidate-
  only ranking makes stdlib single-digit-ms; see the compare doc's math).

- **CLI surface (accepted 2026-07-21):** verb per intent — **`fux ask`** (passages,
  default), **`fux find`** (file locator), **`fux answer`** (extractive cited answer);
  `--json`/`--explain` modifiers for the agent path.
- **Ingest, rendered pages (accepted 2026-07-21):** CDP mode (`render = "cdp"`) —
  drives the user's own headless Chrome over the DevTools Protocol via a hand-rolled
  stdlib WebSocket client (RFC 6455); `urllib` remains the default fetcher.
- **numpy follow-up (resolved 2026-07-21):** vendoring numpy as internal files is not
  possible — its core is platform-compiled C extensions, not copyable Python (proof in
  [`compare/packaged-model.compare.md`](compare/packaged-model.compare.md)).
  Pure-stdlib inference stands.

- **Agent integration (accepted 2026-07-21):** files + hooks from one generator —
  AGENTS.md canonical + CLAUDE.md/copilot-instructions/Kiro-steering pointers;
  Claude Code `UserPromptSubmit` + Kiro hooks for enforced injection; MCP deferred
  behind an ADR. **Skills: one `SKILL.md`** (Agent Skills open standard — read by
  32+ tools incl. Copilot, Kiro, Codex, Cursor) instead of per-tool variants; ship
  `fux-query` + `fux-ingest` skills. Obsoletes the old build's per-platform skillgen.
- **Setup (accepted 2026-07-21):** single **`fux setup`** (renamed from `fux init`) —
  interactive wizard by default, every prompt has a flag, `-y` for defaults,
  idempotent re-runs; `--agents --skills --hooks` covers agent integration.
- **Sub-decisions (resolved 2026-07-21, research-grounded):** **no bundled reranker**
  — RRF only (cross-attention rerankers start ~80 MB, 8× over budget; revisit on eval
  evidence); **chunking = structure-aware, heading-based**, 256–512 tokens,
  heading-path context, code/tables atomic, `file:line` boundaries; **BM25F defaults**
  heading 3.0 / path 2.0 / body 1.0, k1=1.2, b=0.75 — overridable under
  `[engine.bm25f]` in `fux.toml`.

- **Additions (accepted 2026-07-21):** ingest covers **images (metadata stub →
  OCR advanced tier via Tesseract/Docling), JSON (stdlib-flattened), YAML (fenced
  text v1), txt**; a maintained **e2e test suite** in `tests_e2e/` (real CLI +
  fixture corpus + golden files) alongside unit `tests/`; a **doc registry**
  ([`DOC-REGISTRY.md`](DOC-REGISTRY.md)) tracking every maintained doc's update
  trigger + last-verified date, wired into hooks (session-end prompt) and the
  generated agent instructions; and a standing CLAUDE.md rule to **auto-fold durable
  session knowledge into CLAUDE.md**.

- **Process + format additions (accepted 2026-07-21):** **proposal docs**
  (`docs/proposals/`, `status: proposed`, graduate to compare/plan when picked up);
  **archive implemented docs** (`docs/archive/`, moved in the completing change with
  `status: implemented` + ADR link); and **OKF conformance** — Fux's docs and ingest
  cache follow Google's Open Knowledge Format v0.1 (frontmatter `type` everywhere,
  per-dir `index.md`, log.md-style worklog, citations sections; provenance keys as
  legal extensions). Fux's substrate was already OKF-shaped; conformance buys interop
  with every OKF consumer for free.

## 6a. What Fux is for (sharpened 2026-07-21; re-scoped to enterprise same day)

**The ultimate consumer is an agent inside Copilot/Claude/Kiro querying
documentation, decisions, and links** — the context agents lack — not the code
itself (agents read code natively; graphify-class tools map it). Code stays
ingestable, but positioning, defaults, and priorities favor the docs corpus.

Corollary (accepted): semantic enrichment may ride the **host session's model**
(skill-directed, written back as reviewable frontmatter text) — Fux's own code
still never calls a model, so `$0` holds; retrieval and checking stay
deterministic.

**Design point (Arpit, 2026-07-21): a very large-scale corporate project — not
Anton.** Consequences:

- **The knowledge substrate is the default forward path**, not a
  wait-for-a-trigger contingency — enterprise corpora start at the scale where
  `index.json` breaks.

- **Enterprise inputs enter every design**: Windows fleets, proxy/SSO in front
  of internal sites (web ingest must speak them), air-gapped installs, multi-team
  corpora with access boundaries, audit demands.

- **Standing proposals gain weight**: [audit-evidence-trail](proposals/audit-evidence-trail.md)
  (compliance-grade answers) and, longer-term, multi-repo federation of corpora.

- **The sales story writes itself from the laws**: no data egress, no vendor API
  in the loop, auditable-by-reading supply chain, reproducible answers.

## 6b. Why the corpus lives in git (the product-memory bet, 2026-07-21)

Arpit's framing, adopted as design: **the ingest cache is a long-term, git-versioned
knowledge corpus that ultimately feeds product development** — not a disposable
index. Independent signals validate the bet: the *Knowledge as Code* pattern (git-
native, zero-dependency, plain-text canonical knowledge, Jan 2026) and Karpathy's
LLM-Wiki paradigm (compile raw material into a persistent Markdown wiki; query the
wiki). Consequences already in scope: deterministic, diff-friendly cache output is a
v1 *requirement*; the cache is an OKF bundle so any consumer can read it; knowledge
changes become reviewable in PRs like code. Downstream uses are parked as proposals
([research-to-spec](proposals/research-to-spec.md),
[knowledge-diff](proposals/knowledge-diff.md),
[audit-evidence-trail](proposals/audit-evidence-trail.md)) — and the long arc is the
held rule engine: agents developing *from* the corpus and never deviating.
Differentiation vs the field (semtools/rlama/qmd/llm-search): they index documents;
Fux *versions knowledge* — $0, offline, deterministic, cited, and git-historied.

**Tier amendment (Arpit, 2026-07-21, twice-corrected):** the git bet applies to
the **curated tier** (your docs/decisions/notes — 10²–10⁴ files, per-file
Markdown, committed). **Bulk corpora** (large crawls, mass imports) get **no
file cache at all** — 100k documents as files is impractical regardless of git;
their converted text lives as `docs_text` rows inside the substrate db (one
file on disk at any scale; `fux cat <doc>` materializes any single document on
demand). Commit `fux.toml` + the compact manifest — the *recipe*, reproducible
by re-ingest. Git stores the recipe; the db is the warehouse; the filesystem
carries neither. Scale architecture (proposed): two-level
doc index + `fux explain` drill-down — see
[`proposals/knowledge-substrate.md`](proposals/knowledge-substrate.md)
(the single consolidated proposal, 2026-07-21: one substrate incl. bulk text
in-db, one kernel, six verb projections, FuxVec dense search).

**Everything is decided, and every decided phase has its build spec** (handoff +
paste-ready prompt in [`handoff/`](handoff/)):

| # | Phase | Scope | Status |
|---|-------|-------|--------|
| [v0.20.0](archive/v0.20.0-query-cli-v1-handoff.md) | **v1** | setup wizard, inferred-tier local ingest → OKF cache, heading chunker, BM25F, ask/find/answer, agent files, both suites | ✅ **implemented** (v0.20.0, 2026-07-21; ADRs 0001–0004) |
| [v0.21.0](archive/v0.21.0-ingest-web-advanced-handoff.md) | **v1.1** | web crawling (urllib+robots), CDP rendered pages (hand-rolled RFC 6455), advanced tier (Docling/Tesseract), agent-triggered upgrades | ✅ **implemented** (v0.21.0, 2026-07-21; ADR 0005) |
| [v0.22.0](archive/v0.22.0-hybrid-engine-v2-handoff.md) | **v2** | eval harness first, then distilled ≤10 MB bundled model, stdlib inference, chunk-vector cache, RRF hybrid | ✅ **implemented** (v0.22.0, 2026-07-21; ADRs 0006–0007; gate passed as tie → ships enabled) |
| [v0.23.0](archive/v0.23.0-knowledge-substrate-handoff.md) | **v3 — knowledge substrate** | SQLite substrate (bulk text in-db) · fux.lock · committed lean state (`.fux/state/`) · one-kernel `retrieve()` + explain/graph/path/cat · FuxVec · full/lean profiles · db pull | ✅ **implemented** (v0.23.0, 2026-07-22; ADRs 0008–0011; eval hit@5 1.000) |
| [v0.24.0](archive/v0.24.0-debug-observability-handoff.md) | **v4 — debug & observability** | `[debug]` in fux.toml (level/categories/output/timing/redact) · stdout-pure emitter · `fux doctor` (install+corpus+consistency+self-test) · `fux why` (negative-result verdict) · **`fux-debug` skill** | ✅ **implemented** (v0.24.0, 2026-07-22; ADR 0012) |

Sequencing: v1 → dogfood in Anton → then v1.1 and/or v2 in either order, each
gated by the dogfood telling us which pain is real. **Arpit's call (2026-07-21): one
continuous run instead** — [`archive/master-prompt.md`](archive/master-prompt.md)
executes v1 → v1.1 → v2 sequentially with hard phase gates (DoD + suites + ADRs
+ archive + version bump per phase), emitting a `DOGFOOD.md` quickstart after phase
1 so Anton dogfooding runs in parallel. Next action: paste the master prompt into
Claude Code.

## 7. Status

| Area | Status | Notes |
|------|--------|-------|
| Package skeleton | ✅ | src/ layout, hatchling, CLI + FuxError, smoke tests |
| Query CLI — design decisions | ✅ | engine/output/ingest/model verdicts accepted; see `compare/` |
| Query CLI — **v1 build** (setup/ingest/BM25F/ask/find/answer/agents) | ✅ | **v0.20.0** (2026-07-21); ADRs 0001–0004; DOGFOOD.md emitted |
| Ingest v1.1 (web/CDP/advanced — v0.21.0 handoff) | ✅ | **v0.21.0** (2026-07-21); ADR 0005 |
| Hybrid engine v2 (bundled model + RRF — v0.22.0 handoff) | ✅ | **v0.22.0** (2026-07-21); ADRs 0006–0007; 172 unit + 29 e2e tests; eval numbers in ADR 0006 |
| Knowledge substrate v3 (v0.23.0 handoff) | ✅ | **v0.23.0** (2026-07-22); ADRs 0008–0011; 365 unit + 71 e2e; eval hit@5 **1.000** (beats v0.22); 100k benchmark: state 23 MB, FuxVec scan 54 ms (no IVF) |
| Debug & observability v4 (v0.24.0 handoff) | ✅ | **v0.24.0** (2026-07-22); ADR 0012; 417 unit + 100 e2e; `[debug]` toml + emitter, `fux doctor`, `fux why`, `fux-debug` skill |
| Trust & currency v5 (v0.25.0 handoff 0006) | ✅ | **v0.25.0** (2026-07-23); ADRs 0013–0014; 444 unit + 100 e2e; supersession annotated (not reordered), `answer` prefers current when both in pool; confidence floor built + calibrated, **shipped disabled (0.0)** — no value clears all 5 gates |
| Rules substrate | ⏸️ | held |
| Fix loop | ⏸️ | held |

## 7a. What the conformance runs changed (2026-07-22/23)

An independent black-box harness (`fux-lab`) measured the published package at
1k/5k/10k synthetic and ~1k **realistic** (acme-payments) scale. It retired one
scare and found three real defects — none of which the 21-pair fixture gate
could see.

- **Retired:** "hybrid degrades vs `--lexical-only` at scale." A synthetic-corpus
  artifact — near-identical template prose made dense ordering arbitrary. On
  realistic text hybrid ≈ lexical (hit@5 .855 vs .873). Four planned mitigations
  lost their justification.
- **Real — staleness (9/12).** The superseded document outranks the still-true
  one. Ranking has no currency signal at all. → phase 6.
- **Real — fabrication (0/4).** `answer` declines gibberish but invents confident,
  cited answers for well-formed out-of-scope questions. → phase 6.
- **Real — zero-overlap dense rescue (0/6 clean).** Fails *even when the answer is
  the whole document*, so the earlier "document-vector dilution" explanation was
  wrong. Points at chunk-level dense codes. → deferred, own phase.

**The standing lesson:** a fixture-scale eval gate cannot protect retrieval
quality. Realistic-corpus conformance is now the gate that matters, and its
evidence lives in [`conformance/`](conformance/).

## 8. Next move

**Phase 5 shipped (v0.24.0, 2026-07-22)** — build spec archived at
[`archive/v0.24.0-debug-observability-handoff.md`](archive/v0.24.0-debug-observability-handoff.md),
decision in [ADR 0012](adr/0012-debug-observability.md). Every stage is now
inspectable: `[debug]` toml + a stdout-safe emitter, `fux doctor` (seven-group
install/corpus health), `fux why` (single-document negative-result verdict),
and a third skill (`fux-debug`) so an agent self-diagnoses without a human
reading logs.

**Phase 6 — trust & currency — shipped (v0.25.0, 2026-07-23)** — build spec
archived at
[`archive/v0.25.0-trust-currency-handoff.md`](archive/v0.25.0-trust-currency-handoff.md),
decisions in [ADR 0013](adr/0013-supersession-awareness.md) (supersession) and
[ADR 0014](adr/0014-answer-confidence-floor.md) (confidence floor). Two honest,
partial results, not two clean fixes:

- **Supersession is annotated, not reordered** (the accepted verdict): `find`
  ranking is unchanged; `answer` prefers the current document when both are in
  its retrieved pool. Measured recovery on acme's 9/12 inversions: only **5 of
  12** stale docs carry a machine-readable marker, only **3 of the 9** original
  inversions do, and at the `answer` level the fix **fully corrects 1** and
  de-cites the retired doc in a 2nd — the rest are unmarked and
  deterministically unreachable. See
  [`conformance/2026-07-23-supersession-recovery/`](conformance/2026-07-23-supersession-recovery/).
- **The confidence floor was built and calibrated, then shipped disabled.**
  `docs/conformance/2026-07-23-min-confidence-calibration/` found the acme
  corpus's unanswerable and answerable score distributions interleave — no
  `min_confidence` value declines all 4 fabrications without also declining
  real answers. **The measured 0/4 fabrication defect is not fixed in this
  release**; the knob and its calibration evidence exist for a future
  cross-query-comparable signal (e.g. dense cosine) to use.

### Phase 7 (v0.26.0) — supersession down-ranks, fabrication is closed

**Option B shipped, on measurement.** The annotate-only verdict was reopened
after two independent corpora showed the engine annotating "this is superseded"
about the document it ranked **first** (acme 9/12, orbit 8/12 inversions).

- **`[engine.hybrid] supersession_penalty` (default 15)** — a rank offset in RRF
  fusion for author-marked superseded documents. A **penalty, not a filter**: the
  retired document stays reachable (measured rank 1 → 17, still returned). `0`
  restores pre-0.26 ranking exactly; `--lexical-only` never reaches it.
- **The default is a measurement.** Swept across all four eval sets: safe
  interval **`[11, ∞)`** to 500, **zero hit@5 regression on any gate at any value
  in any question kind**, recovering **100% of frontmatter-reachable inversions**
  (orbit 5/5, acme 3/3) while hit@1 improves. See
  [`conformance/2026-07-24-supersession-penalty-calibration/`](conformance/2026-07-24-supersession-penalty-calibration/).
- **The ceiling is the marked set**, permanently: 3/12 (orbit) and 6/12 (acme)
  inversions carry no marker. The remaining lever is **documentation, not
  engineering** — `superseded_by:` is the contract Fux acts on.
- **Fabrication is now a documented product boundary, not an open defect.** The
  runner-up margin check was re-measured on a corpus de-confounded by the very
  penalty above, and is **still empty** — a `how-to` question sits at margin
  1e-05 before and after; acme's minimum is a `cross-doc` question that never
  involved supersession. Three no-model discriminators are refuted across two
  corpora. **No fourth mechanism is proposed.**

### Phase 8 (2026-07-24) — v0.26.0 published

**v0.26.0 is live on PyPI**, with both README honesty edits landing *before* the
release was cut. The phase-7 calibration was re-confirmed **black-box from the
published package** (orbit inversions 8→3, hit@1 .566→.698, hit@5 flat) — the
first orbit run installed from PyPI rather than a locally-built wheel.

- **Correction:** 0.24.0 and 0.25.0 were already published. `pip install` fails
  with *"no matching distribution"* on Python **< 3.11** (the package requires
  `>=3.11`), and that was misread as unpublished. The frozen-wheel workaround is
  retired.
- **Part B:** `zero_overlap_rescued` now counts *clean* rescues only (2 → 1); the
  new `zero_overlap_demoted` auto-detects the fusion demotion case.

### Phase 9 (pre-registered, unstarted) — fusion loses lexical top-5 hits

**The filed "non-monotone fusion" finding is a misdiagnosis.** `1/(k + rank)` is
strictly decreasing, so RRF *is* monotone in per-list rank, and the reported case
reconciles to the exact specified arithmetic across all three lists. The correct
document lost because its dense similarity (**0.3297**) sits barely above ADR
0010's 0.23–0.26 noise band — a **dense-quality** defect that fusion faithfully
propagates. The supersession penalty is not implicated.

What remains is a product question, headed for a compare doc: **should hybrid be
barred from dropping a document `--lexical-only` would have returned in top-5?**
Guard, accept, or fix-the-input (chunk-level dense codes may simply own this).
**"No engine change" is an expected, valid outcome.** → handoff 0009.

**Then:** the deferred **chunk-level dense codes** (zero-overlap rescue, still
1/6 — gated on the ~200 B/doc committed-state budget) and **query-at-scale**
(ADR 0011 — a 100k query still loads the whole index). Also parked: an absolute,
cross-query-comparable confidence signal for `answer` (ADR 0014's F1/F2), now
about confidence *reporting* rather than a fix, since phase 7 closed the decline
line. None is scoped; each needs its own compare doc.

**Query-at-scale is deferred, not dropped** — at 100k documents a query takes
~10 s, because the query path still loads the entire index to build the
`Searcher`. `postings` is populated and indexed at ingest but never read at query
time. The substrate solved *storage* at scale; *query* at scale stays scoped and
unstarted (numbers and the fix in [ADR 0011](adr/0011-profiles-lean-state.md)),
alongside chunk-level dense codes for the zero-overlap class.

Beyond that: dogfooding (DOGFOOD.md + the private eval set) continues, and the
held rule engine remains the long arc.
