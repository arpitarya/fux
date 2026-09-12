---
type: OpenItem
id: W-107
title: "W-107 — the Node read plane: ask / find / answer / explain / graph / path / mcp from Node.js, zero dependencies, byte-equal to Python"
description: "A read-only port of the seven query verbs to one ESM file (npm: fux-search) so a Node-only host reads an index Python wrote. Four phases behind a pre-registered third arm of the differential law. Phase 0 CLOSED 2026-09-06: Arpit ruled option (b), scores equal after round(9) and ordering byte-equal; measured on darwin and glibc, with idf's argument domain enumerated exhaustively."
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
- [x] ✅ **BOTH LIMITS CLOSED 2026-09-06.**
      [`ADDENDUM-IDF`](../regression/2026-09-05-node-log-divergence/ADDENDUM-IDF.md)
      widened the `idf` population on this repo's own 838-document index
      (13 → 182 distinct, **7.69 % diverge**, 8.98 % of real BM25F scores
      differ bit-for-bit, **0 at `round(9)`**), and
      [`ADDENDUM-GLIBC`](../regression/2026-09-05-node-log-divergence/ADDENDUM-GLIBC.md)
      measured **glibc 2.39 / x86-64 / Node 22** — 722/100 000 wide,
      4.44 % of scores bit-different, **0 at `round(9)`, 0 top-5 moves** — and
      went further than the clause asked: the `idf` argument domain is
      **enumerated, not sampled**. `idf`'s argument is
      `(n - df + 0.5)/(df + 0.5) + 1` with `df ∈ 1..n`, so at a given corpus
      size it is finite; **all 10 939 arguments at `n ∈ {101, 838, 10 000}`**
      were checked, **841 (7.69 %) differ, 0 differ at `round(9)`**.
      ⚠ **Still unmeasured: musl, Windows, Node 20**, and
      [`log-probe.yml`](../../.github/workflows/log-probe.yml) **has still not
      been run** — the glibc figure came from a Linux container, not from CI.
- [x] **WRITTEN 2026-09-05, deliberately NOT FROZEN, and FROZEN IN FULL
      2026-09-06** (sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`).
      [`../benchmark/PRE-REGISTRATION-NODE.md`](../benchmark/PRE-REGISTRATION-NODE.md)
      — ids `N0`–`N4`, the byte-equal field table, both corpora, all three
      OS/libm pairs, and `N4`'s **p95 ≤ 150 ms** (3× the measured Python
      figure: a fence against an *algorithmic* divergence, not against a
      constant factor). 🔴 **§2's score-comparison cell is blank** and is the
      bullet below. **The document was not frozen and Phase 1 did not start
      until Arpit filled it in.**
- [x] ✅ **ARPIT RULED 2026-09-06 — option (b), tolerance at `round(9)`.**
      No Python change, no golden re-derivation, no hand-rolled transcendental:
      the arm compares the score *field* at `round(9)`, which is the resolution
      `rank.py`'s sort key already uses. **(a)** — `src/fux/query/portable_math.py`
      mirrored bit-for-bit in JS — was declined; it bought bit-identity at the
      price of a corpus-wide ranking change to fix a difference seven orders of
      magnitude below the sort key.
      🔴 **This file previously described (b) as accepting "ordering flips it
      can explain". That was wrong and is corrected here**: under
      [PRE-REG-NODE §2](../benchmark/PRE-REGISTRATION-NODE.md) the ordering
      assertion is **byte-equal under either option**, and a discordant top-5
      fails the arm. (b) tolerates a difference in the printed score, never a
      different ranking.
- [x] Decision recorded in
      **[ADR-RANKING decision 8a](../../docs/adr/0111_ranking.md)** — the sort
      key's resolution is the cross-runtime contract for the score, the order
      is byte-equal, and a divergence above `~1e-9` relative on any platform
      pair voids it.
- [ ] Decision restated as **ADR-NODE-SEARCH decision 1** when that record is
      created — owed at Phase 4, **as a link to ADR-RANKING 8a, never a second
      statement of the rule** (L0).

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
- ~~🔴 `arpit`: the Phase 0 `log()` pick~~ — **ruled 2026-09-06: (b),
  tolerance at `round(9)`.** The pre-registration is frozen in full.
  ▶ **Nothing blocks Phases 1–4. Phase 1 starts.**
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

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🟠 **Search v3 — what is left of it: W-107 Phases 1–4, then W-112.** ·
  *(spec: [`proposals/search-v3.md`](../proposals/search-v3.md) §8 · one detail
  file each under [`open/`](README.md))* · **Opus** executes, in Arpit's
  ratified order: **W-107 Phases 1–4** → **W-112**. `ratified: 2026-09-05`
  - **[W-107](W-107-node-read-plane.md)** · `agent` · *(**ADR-NODE-SEARCH** new · ADR-RANKING · ADR-MCP)* · the Node read plane — `npx fux-search ask|find|answer|explain|graph|path|mcp`, zero deps, one contract, a third arm of the differential law. ▶ **Phase 1 starts; nothing blocks it.** Phase 0's `log()` question is settled and the rule lives in [ADR-RANKING decision 8a](../../docs/adr/0111_ranking.md) — scores equal after `round(9)`, ordering byte-equal; [`PRE-REGISTRATION-NODE.md`](../benchmark/PRE-REGISTRATION-NODE.md) is frozen in full, sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`, and Phases 1–4 build against it. ⚠ **§4 still requires all three OSes before an arm is called green**, and only glibc/arm64 has been touched — [`log-probe.yml`](../../.github/workflows/log-probe.yml) is **unrun**, so musl, Windows and Node 20 are unmeasured. ⚠ **[L9](../../docs/adr/0011_LAW-9-environments.md): its frozen pre-registration names the playground** — the build (Phases 1–4) is unaffected, but any measured arm runs on fux-lab golden data under a superseding pre-registration ([W-138](W-138-reconcile-with-l9.md)). `filed: 2026-09-04`
