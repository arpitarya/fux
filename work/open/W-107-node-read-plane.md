---
type: OpenItem
id: W-107
title: "W-107 — the Node read plane: ask / find / answer / explain / graph / path / mcp from Node.js, zero dependencies, byte-equal to Python"
description: "A read-only port of the seven query verbs to one ESM file (npm: fux-search) so a Node-only host reads an index Python wrote. Four phases behind a pre-registered third arm of the differential law. Phase 0 is Arpit's decision on log(): V8 and glibc disagree in the last ulp on ~1 % of inputs, so byte identity needs one portable log in both runtimes."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-107 — the Node read plane

**Model: Opus.** Phase 0 is a determinism decision and touches ranking
arithmetic; Phases 1–3 are transcription where a wrong last bit is invisible
until the differential arm fires. Sonnet may run the mechanical suites once
the pre-registration exists; Opus owns every gate.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §6 (design), §8
(plan), §9.6 (mechanics). Nothing below restates a bar.

## Goal

`npx fux-search ask|find|answer|explain|graph|path|mcp` on a repo whose index
Python committed, with **no Python on the host**, producing what Python
produces: same ids, order, locs, headings, band; scores equal after
`round(9)`; `graph.json` digest equal.

## Phase 0 — the `log()` decision (Arpit)

- [ ] Measure Python-vs-Node BM25F score divergence *as is* on the playground
      and the 10 000-document lab corpus (idf only — one script, both
      runtimes); file the discordant top-5 count.
- [ ] Write `work/benchmark/PRE-REGISTRATION-NODE.md`: the three-arm law,
      the exact comparison (which fields must be byte-equal, which are
      `round(9)`-equal), p95 bar for the Node scan at 10 000 documents,
      corpora, ISAs. Frozen sha before Phase 1.
- [ ] Arpit picks: **(a) portable `log`** — `src/fux/query/portable_math.py`
      (range reduction via `math.frexp`, atanh-series polynomial, basic ops
      only) used by `bm25f.idf`, mirrored bit-for-bit in JS via `DataView`;
      ADR-RANKING amended; differential law + goldens re-run in Python first;
      **or (b) tolerance** — no Python change, the arm compares scores at
      `round(9)` and accepts ordering flips it can explain.
- [ ] Decision recorded in ADR-NODE-SEARCH decision 1 and in ADR-RANKING.

## Phase 1 — `find`

- [ ] `node/fux-search.mjs`: BLAKE2b (RFC 7693, 32-bit halves, digest sizes
      1/8/20; pinned against Python `hashlib` and RFC Appendix A); analyzer
      (`_WORD_RE`, `_BOUNDARY_RE`, stopwords, `split_identifier`, Porter with
      `should_stem`); shard reader that refuses unknown `_format`/`analyzer`;
      BM25F `score_record`/`derive_wlen`; `Weighting` incl. recency
      (`ingest/priors.py`) and priority; TOML subset reader; `round(9)`
      half-even shim; Python-`repr` float formatter; sort on the exact key.
- [ ] Pinned by: hash test vectors; **every distinct term of the playground
      index analyzed both sides**; Porter `voc.txt`/`output.txt`;
      `find --json` over all goldens on both corpora, 0 discordant.

## Phase 2 — `ask` + `answer`

- [ ] Display title (no cache ⇒ Python's no-cache fallback), W-84 headings,
      confidence block, `--why`; chunker (`refer/_chunk.py`), rescore (with
      W-108's proximity once landed), assemble, receipt; `answer` on `url:`
      reads `.fux/acquired/` or returns `source: index`. **Never fetches.**
- [ ] `output.schema.json` validated in Node too (same file).

## Phase 3 — graph + `mcp`

- [ ] `edges_from_records` → label propagation (`graph/community.py`,
      determinized) → PPR-lite / routes; in-memory plane digest equals
      Python's `graph.json` on both corpora.
- [ ] MCP: newline-delimited JSON-RPC on stdio, `initialize` →
      `notifications/initialized`, `tools/list`, `tools/call`, `ping`; tool
      descriptions loaded from one shared JSON that `src/fux/mcp.py` also
      reads (a new file; ADR-MCP amended).

## Phase 4 — ship

- [ ] `ADR-NODE-SEARCH` (new): owns `node/`; decisions on the `_format`
      version policy, the never-fetch rule, the shared tool-description file.
- [ ] Ownership table + `tests/test_adr_ownership.py`; the freshness test
      maps each Python module to its Node twin.
- [ ] CI matrix Node 20/22 × ubuntu/macos(arm64)/windows; the differential
      arm runs on every push.
- [ ] npm `fux-search` published; README front door; CHANGELOG.
- [ ] `IMPLEMENTATION.md` row; this file to `archive/open/`.

## Blockers

- `arpit`: ratification; the Phase 0 decision.
- W-108 should land first so Phase 2 ports one rescore, not two.

## Hazards

- 🔴 **A port that "improves" anything has diverged.** Every difference is a
  defect until the pre-registration says otherwise.
- 🔴 `math.log`: 1 095 / 100 000 last-ulp disagreements measured (V8 fdlibm
  vs glibc 2.39); macOS libm is a third answer. Phase 0 exists because of
  this; do not skip it.
- Truncated `blake2b512` is **not** BLAKE2b-8 (parameter block). Test it.
- `Number(x.toFixed(9))` is half-up on exact binary ties; Python is
  half-even. Detect ties via `toFixed(20)`.
- A `_format` bump in Python without a Node release breaks every Node
  clone — version policy is the guard.
- `node/` must have **no** `package.json` dependencies; a build step is a
  dependency.

## Out of scope

`ingest`, `build`, `add/remove/update`, `enrich`, `embed`, `doctor`,
`setup`, the accelerator, any fetcher. A Node-side cache (`--fast`) until
the scan p95 is measured at 10 000 documents.
