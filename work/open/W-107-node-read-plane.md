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

- [x] **DONE 2026-09-05.** Measure Python-vs-Node BM25F score divergence *as
      is* on the playground and the 10 000-document corpus; file the discordant
      top-5 count. →
      [`2026-09-05-node-log-divergence`](../regression/2026-09-05-node-log-divergence/report.md),
      `blind`, per-query rows for all 290 queries.
      **`Math.log` and `math.log` DO differ** — 655 / 100 000 wide doubles on
      darwin/arm64, the same order as the glibc figure in Hazards below — but
      **every difference is one ulp** (max rel `2.211e-16`) and **not one
      survives `round(9)`**, which is `rank.py`'s own sort-key resolution.
      Over the corpora: **0 discordant scores and 0 discordant top-5 on
      197 233 scored documents**, checked on both the real sort key and an
      exact one. Python's scan **p95 = 50.2 ms at 10 000 documents**.
      ⚠ **Two limits bound every sentence of that**: the `idf` argument
      population in those corpora is **13 distinct values** (a property of a
      10-document corpus and a synthetic 10 000-document one, not of fux), and
      **glibc — what CI runs — was not measured**, because this machine has no
      Linux.
- [x] **WRITTEN 2026-09-05, and deliberately NOT FROZEN.**
      [`../benchmark/PRE-REGISTRATION-NODE.md`](../benchmark/PRE-REGISTRATION-NODE.md)
      — ids `N0`–`N4`, the byte-equal field table, both corpora, all three
      OS/libm pairs, and `N4`'s **p95 ≤ 150 ms** (3× the measured Python
      figure: a fence against an *algorithmic* divergence, not against a
      constant factor). 🔴 **§2's score-comparison cell is blank** and is the
      bullet below. **The document is not frozen and Phase 1 does not start
      until Arpit fills it in.**
- [ ] 🔴 **ARPIT PICKS — the only thing blocking Phases 1–4.** (a) or (b),
      one word, with the numbers above beside them: **(a) portable `log`** — `src/fux/query/portable_math.py`
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

- ~~`arpit`: ratification~~ — **ratified 2026-09-05.**
- 🔴 `arpit`: **the Phase 0 `log()` pick.** The measurement is filed; the
  pre-registration is written with that one cell blank. Nothing else blocks
  Phases 1–4.
- ~~W-108 should land first so Phase 2 ports one rescore, not two~~ —
  **W-108 landed 2026-09-05.** Phase 2 ports the rescore **with** its proximity
  multiplier, per-passage locators, and the URL-keyed fetcher dispatch. ⚠ Node
  never fetches, so the dispatcher has **no Node twin**: `answer` on a `url:`
  document reads `.fux/acquired/` or returns `source: index`.

## Hazards

- 🔴 **A port that "improves" anything has diverged.** Every difference is a
  defect until the pre-registration says otherwise.
- 🔴 `math.log`: 1 095 / 100 000 last-ulp disagreements measured (V8 fdlibm
  vs glibc 2.39); macOS libm is a third answer. Phase 0 exists because of
  this; do not skip it. **Re-measured 2026-09-05 on Apple libm vs
  V8/darwin-arm64: 655 / 100 000, all one ulp, none surviving `round(9)`** —
  the hazard is confirmed as a property of `log` and **quantified as seven
  orders of magnitude below the sort key's resolution.**
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
