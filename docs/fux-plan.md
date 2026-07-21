---
type: Plan
title: Fux — design of record (rebuild)
description: The living design of record — scope, decisions, status, and next moves for the Fux rebuild.
timestamp: 2026-07-21T00:00:00Z
---

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

**Everything is decided, and every decided phase has its build spec** (handoff +
paste-ready prompt in [`handoff/`](handoff/)):

| # | Phase | Scope | Status |
|---|-------|-------|--------|
| [0001](archive/0001-query-cli-v1-handoff.md) | **v1** | setup wizard, inferred-tier local ingest → OKF cache, heading chunker, BM25F, ask/find/answer, agent files, both suites | ✅ **implemented** (v0.20.0, 2026-07-21; ADRs 0001–0004) |
| [0002](archive/0002-ingest-web-advanced-handoff.md) | **v1.1** | web crawling (urllib+robots), CDP rendered pages (hand-rolled RFC 6455), advanced tier (Docling/Tesseract), agent-triggered upgrades | ✅ **implemented** (v0.21.0, 2026-07-21; ADR 0005) |
| [0003](archive/0003-hybrid-engine-v2-handoff.md) | **v2** | eval harness first, then distilled ≤10 MB bundled model, stdlib inference, chunk-vector cache, RRF hybrid | ✅ **implemented** (v0.22.0, 2026-07-21; ADRs 0006–0007; gate passed as tie → ships enabled) |

Sequencing: 0001 → dogfood in Anton → then 0002 and/or 0003 in either order, each
gated by the dogfood telling us which pain is real. **Arpit's call (2026-07-21): one
continuous run instead** — [`handoff/0000-master-prompt.md`](handoff/0000-master-prompt.md)
executes 0001 → 0002 → 0003 sequentially with hard phase gates (DoD + suites + ADRs
+ archive + version bump per phase), emitting a `DOGFOOD.md` quickstart after phase
1 so Anton dogfooding runs in parallel. Next action: paste the master prompt into
Claude Code.

## 7. Status

| Area | Status | Notes |
|------|--------|-------|
| Package skeleton | ✅ | src/ layout, hatchling, CLI + FuxError, smoke tests |
| Query CLI — design decisions | ✅ | engine/output/ingest/model verdicts accepted; see `compare/` |
| Query CLI — **v1 build** (setup/ingest/BM25F/ask/find/answer/agents) | ✅ | **v0.20.0** (2026-07-21); ADRs 0001–0004; DOGFOOD.md emitted |
| Ingest v1.1 (web/CDP/advanced — handoff 0002) | ✅ | **v0.21.0** (2026-07-21); ADR 0005 |
| Hybrid engine v2 (bundled model + RRF — handoff 0003) | ✅ | **v0.22.0** (2026-07-21); ADRs 0006–0007; 173 unit + 28 e2e tests; eval numbers in ADR 0006 |
| Rules substrate | ⏸️ | held |
| Fix loop | ⏸️ | held |

## 8. Next move

**The master run (0001 → 0002 → 0003) is complete at v0.22.0.** Next: dogfood
in Anton via [DOGFOOD.md](../DOGFOOD.md) — build the private Anton eval set
(tests_e2e/eval/README.md), let its numbers drive what's next (the reopen
triggers live in the compare docs; the held rule engine remains the long arc).
