---
type: ADR
title: ADR-0012 — Debug & observability ([debug], fux doctor, fux why, fux-debug skill)
description: A hand-rolled, stdout-safe debug emitter; a seven-group whole-install diagnostic; a single-document negative-result explainer; and a third skill so agents self-diagnose without reading logs.
timestamp: 2026-07-22T00:00:00Z
---

# ADR-0012: Debug & observability

- **Status:** accepted
- **Date:** 2026-07-22
- **Feature:** Debug & observability (handoff 0005, M1–M6)

## Context

Fux is deterministic and cited, which makes it *auditable* — but not
*diagnosable*. Before this feature the only debug surface was
`FUX_DEBUG=1` inside `src/fux/hooks.py` (fail-open tracing on hook errors);
everything else in the pipeline — ingest decisions, chunk boundaries, index
reuse, candidate selection, dense scan, graph expansion, answer sentence
choice, state/lock consistency — was opaque. At the enterprise litmus
(10⁵–10⁶ documents, SSO, Windows fleets, air-gapped environments), "it
returned nothing and I don't know why" is the support burden a self-serve
diagnostic replaces.

Arpit's requirements (2026-07-22): a debugging plan covering *everything*;
the level **exposed as a value in `fux.toml`**; and it must **work with
skills**, so an agent can diagnose without a human reading logs.

## Decision

Four pieces, one per the five questions debug exists to answer (why isn't my
doc in the corpus / why didn't my query return it / why is the answer thin /
why is my install unhealthy / why is it slow):

1. **`[debug]` in `fux.toml` + `src/fux/debug.py`** — a hand-rolled emitter
   (`dbg()`/`timer()`/`is_enabled()`), never touching stdout, gated by
   `level` (off/info/debug/trace) and `categories`, with precedence
   `--debug[=LEVEL]` (flag) > `FUX_DEBUG=<level|1>` (env) > toml `level` >
   `off`. Redaction is on by default (paths/ids/counts/scores, never document
   text); `timing` gates the only wall-clock-derived field (`elapsed_ms`),
   so a `trace` run is otherwise byte-for-byte reproducible.
2. **`fux doctor`** — seven groups (environment, capabilities, config,
   corpus, consistency, agent surface, self-test), text + `--json`, exit 0
   healthy / 1 problems. Every failing check names what's wrong, why it
   matters, and the exact fix command. The zero-match `[sources]` glob — the
   #1 silent misconfig — is checked explicitly per source entry.
3. **`fux why "<query>" --doc <path>`** — walks corpus-presence → chunks →
   lexical (full-corpus rank + per-term idf/tf) → dense (FuxVec hamming/
   prefilter/cosine) → graph (seed vs. expanded-via-edge), ending in a single
   **verdict** sentence. Dense and graph evidence is read from
   `kernel.retrieve()` itself (not a parallel computation), so `why` can
   never disagree with what a real query would do.
4. **`fux-debug` skill** + a one-line escalation pointer added to both
   `fux-query` and `fux-ingest` — `fux doctor` → `fux ingest --check` →
   `fux why` → `--advanced` → `--debug=debug` → report, don't guess.

### Open questions, answered

1. **Hand-rolled emitter vs. stdlib `logging`.** Hand-rolled. The precedence
   rule (flag beats env beats toml) and the max-bytes truncate-with-notice
   behaviour are simpler to keep deterministic as a plain module with one
   piece of mutable state than to bolt onto `logging`'s handler/formatter/
   propagation machinery — and `fux.debug` is ~230 lines total, well inside
   "small and per-repo."
2. **Is `doctor --json` stable enough for CI gating?** Documented and
   stable, per the handoff's own recommendation: `{healthy, groups: [{name,
   ok, checks: [{name, ok, detail, why?, fix?}]}]}` is committed in
   `docs/example/CLI.md`/`DEBUG.md` as a contract, the same way `ask --json`'s
   shape is. `why` fields are less pinned intentionally — the resulting fields
   change if a corpus lacks a bundled model (`dense` reasons differ) or runs
   `--lexical-only` (`dense` is absent), so only `doc`/`in_corpus`/`verdict`
   are guaranteed present; `lexical`/`dense`/`graph` are advisory evidence.
3. **Does `why` deserve `--all`?** No, not in v0.24. `why` is deliberately
   single-document: its cost is a full-corpus lexical ranking pass
   (`Searcher.search(top=len(chunks))`) plus a `kernel.retrieve()` call sized
   to the whole corpus, both fine for one document on demand but not
   something to run once per document in a large corpus. If a "rank every
   doc's fate" view is ever wanted, it belongs as a batch report built from
   the same primitives — a proposal, not a `why` flag, and only once a real
   need appears (no enterprise scale-driven request for it yet).
4. **Does `timing` belong in `[debug]` or its own `[profile]` section?**
   `[debug]`. `timer()` lives in the same module as `dbg()` and is gated by
   the same `is_enabled()` check; a separate `[profile]` section would be a
   second config surface controlling one boolean, which is the premature
   abstraction CLAUDE.md warns against. Revisit only if profiling grows a
   second knob (e.g. a sampling rate) that doesn't fit `[debug]`'s shape.

## Alternatives considered

- **stdlib `logging`** — rejected per open question 1.
- **A single `--verbose` flag instead of levels/categories** — rejected: the
  five questions debug must answer span very different volumes of detail
  (one line per ingest vs. per-candidate scores), and a single flag can't
  express "debug the query path only" without drowning it in ingest noise.
- **`why --all`** — rejected per open question 3; kept as a future proposal
  if a concrete need shows up.
- **Doctor gates on missing optional capabilities** (markitdown/docling/
  tesseract/Chrome absent ⇒ unhealthy) — rejected: these are opt-in paths,
  not requirements: a lexical-only, no-office install is a fully valid,
  healthy configuration.

## Consequences

**Easier.** An agent (or a human) with a broken-looking corpus now has one
command (`fux doctor`) that names the fix, and one command (`fux why`) that
explains a single negative result instead of guessing. The `fux-debug` skill
makes this self-serve for an agent with no human reading stderr.

**Harder.** Every existing pipeline module now carries `import .. debug` and
scattered `dbg()`/`timer()` calls — a small, permanent readability tax, paid
once, in exchange for the whole pipeline being inspectable.

**Owed.** `fux doctor`'s "Chrome for CDP" capability check is binary-presence
only (`shutil.which`), not a live `localhost:<cdp_port>` reachability probe —
`tests/test_import_fence.py` forbids `import socket` outside `ingest/`, and a
live probe from `doctor.py` would violate that standing fence. If CDP
reachability diagnosis is ever wanted, it belongs inside the ingest package,
callable from doctor rather than implemented there directly.

## References (required)

- [The Twelve-Factor App — Logs](https://12factor.net/logs) — treat logs as
  event streams to stdout/stderr, never files the app manages; `fux.debug`
  follows this for the default (`stderr`), with an opt-in file path for the
  cases (long agent sessions, CI artifact capture) where a stream isn't
  enough.
- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) —
  the four golden signals shaped `fux doctor`'s corpus/consistency groups
  (is it there, is it fresh, is it consistent) more than a generic health
  check would have.
- [Rust's `tracing` crate — Structured, leveled, contextual logging](https://tokio.rs/blog/2019-08-tracing) —
  the category+level+key=value shape `dbg()` emits is the same "spans and
  events" idea, minus the async-context machinery Fux doesn't need.
- Internal: [handoff 0005](../archive/v0.24.0-debug-observability-handoff.md) (the
  build contract) · [ADR 0006](0006-bundled-model.md) (the model whose sha
  `fux doctor`'s environment group verifies) · [ADR 0010](0010-fuxvec-binary-dense-search.md)
  (the FuxVec prefilter `fux why`'s dense evidence reads).
