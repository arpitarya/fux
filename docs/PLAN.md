---
type: Plan
title: "Fux v0.30 — the index-and-refer build, revision 2"
description: The post-gate plan. P1 measured FAIL; Arpit accepted option E (full postings); the index pivoted to tiered JSONL with git as the Merkle tree. Milestones M0–M8, ADRs from 0001, first slice packaged as a handoff.
status: active
timestamp: 2026-08-09T00:00:00Z
---

# Fux v0.30 — the index-and-refer build (revision 2)

## For AI agents — quick reference (read this block, then jump)

- **Live tracker:** [`OPEN-WORK.md`](OPEN-WORK.md) — an **index** of open
  items (restructured 2026-08-12); pick work there, then read the item's
  detail file in [`open/`](open/README.md). This file is the *spec* for
  each milestone id; the detail file is the *state*.
- **The gate is closed.** P1 was measured twice ([ADR-0002](adr/0002-pruning-eval-gate.md)
  INCONCLUSIVE → [ADR-0003](adr/0003-pruning-criterion-rerun.md) **FAIL**),
  and Arpit accepted option E: **full postings, no pruning anywhere in the
  build**. Do not re-introduce pruning; it survives only as an M8
  optimization experiment.
- **Format of record:** [`compare/index-format.compare.md`](compare/index-format.compare.md)
  — tiered JSONL, doc-major committed, blocked term-major derived, binary
  only as record properties (`code`, `tpack`). ADR numbering starts at
  0001 ([`adr/README.md`](adr/README.md)); "archived ADR-NNNN" always
  means the v0.26 line.
- **Laws:** $0 · stdlib · deterministic (no floats, no wall-clock in
  committed bytes) · offline-default · 1 feature = 1 ADR, referenced ·
  WORKLOG every exchange · OPEN-WORK + DOC-REGISTRY in the same change.
- **Old world:** engine `../archive/v0.26/` (runnable, reference-only);
  port with tests, don't rewrite (list below). The RFC corpus
  (manifest-pinned, in the lab) and `tools/pruning-eval/` are reusable
  bench infrastructure.
- **Handoffs:** every milestone ships as handoff + prompt with the model
  named. The live pair is in [`handoff/`](handoff/README.md).

---

## What changed since revision 1 (the honest delta)

1. **The pruning premise died in measurement.** Two pre-registered runs;
   the second, on a corpus that could actually test it (8 872 RFCs, median
   967 distinct terms/doc), put the best selector **35.9 pts** short of a
   2-pt bar at the 6 % budget. Option E accepted: the committed index
   carries **full postings**.
2. **The format pivoted to tiered JSONL** (Arpit's push, then measured):
   sorted JSONL *is* an index (0.035 ms bisect); git *is* the Merkle tree
   (a one-line edit in a 138 MB shard commits in 2.5 s and deltas to
   ~nothing); the common-term trap closes via 128-posting block lines with
   integer `mx` skipping (397 → 44 ms). The MST substrate and BIC wire are
   **superseded for the committed plane** and survive only inside tier T2.
3. **M2 shrank ~500 LOC** (no custom Merkle tree); codec work moved to the
   T2 tier most repos never reach; the clone story improved — a fresh
   clone answers via scan before any build step.
4. **ADRs renumbered from 0001** for the v0.30 line (0016–0018 → 0001–0003;
   frozen artifacts keep old numbers, see `adr/README.md`).

Design authority, in order: the index-format compare doc · the paper
(`paper/the-fux-index-paper.md` — §4/§5 pending amendment, flagged in M6) ·
the other compare docs · council + session rulings in WORKLOG.

## Port-don't-rewrite (from `archive/v0.26/`, with their tests)

| module | used by | port in |
|---|---|---|
| frontmatter parser | ingest, snapshot mode | M1 |
| tokenizer + analyzer chain | ingest, query | M1 |
| BM25F scoring math + exact-df discipline | kernel | M1 (scan) / M2 (accelerated) |
| FuxVec embed + 32 B codes | `code` property, dense lane | M1 / M2 |
| converters (fidelity tiers) | transient convert | M4 |
| RRF fusion (k=60) | kernel | M2 |
| PPR-lite + edge extraction | graph lane | M3 |
| chunker (heading-aware) | passage re-score | M4 |
| CLI verb surface (ask/find/answer/explain/graph/path) | UX contract | M2–M4 |

## Milestones

| # | name | proves | est. size | model |
|---|---|---|---|---|
| M0 | scaffold (0.30.0.dev0) | — | small | Sonnet |
| M1 | **T0 vertical slice**: committed store + git-dir ingest + scan `ask`, dogfooded on this repo | R1, R2 | ~900 LOC | Sonnet build · Opus review of the canonical writer |
| M2 | T1 accelerator + full lexical/dense kernel | R3 | ~800 LOC | Opus |
| M3 | graph lane: edges, community, explain/graph/path | — | ~400 LOC | Sonnet |
| M4 | refer plane: HTTP+Confluence adapters, ARC, assembler, freshness fence | R4 | ~900 LOC | Sonnet |
| M5 | maintenance: hooks, line-wise merge driver, snapshot mode, hashed-meta enforcement | R5, R6 | ~500 LOC | Sonnet |
| M6 | scale: T2 (`tpack` + mmap segments), partial clone, 100k/1M bench, paper §4–§6 updated to measured | R7 | bench + ~600 LOC | Sonnet bench · Opus analysis |
| M7 | dogfood & release gate: Anton + fux daily use, DOGFOOD.md, real README | — | docs + fixes | Sonnet |
| M8 | deferred experiments (each = ADR + Arpit sign-off) | — | — | — |

**Sequencing:** M0→M1→M2 strict; M3/M4 may interleave after M2; M5 before
M6; M7 gates any release. No milestone starts before the previous DoD.

### M0 — scaffold

`src/fux/` skeleton (`store/`, `derive/`, `query/`, `ingest/`, `refer/`,
`cli.py`, `errors.py`), `pyproject.toml` 0.30.0.dev0 (hatchling, stdlib
runtime, converter extras), fresh CHANGELOG, `fux --version` + `fux doctor`
stub, `.github/` paths fixed. **DoD:** both commands run; CI green on the
empty package.

### M1 — the T0 vertical slice

*(the live handoff:
[`archive/v0.30.0-m1-t0-slice-handoff.md`](archive/v0.30.0-m1-t0-slice-handoff.md))*

Committed store exactly per the index-format spec: canonical writer/reader,
256 shards, `_format` header, 16-hex term hashes with build-time collision
check. Git-dir adapter + `extracted`-mode ingest: tokenize → `terms`/`wlen`;
`title` + heading-derived `phrases`; `ref`/`tag`/`code` edges; FuxVec
`code`. `fux ingest` and `fux ask` (B2 prefilter scan + ported BM25F —
correct first, fast at M2). Dogfood on this repo's own docs. **DoD:** R1
byte-identical double-ingest (asserted cross-machine in CI); R2
`fux ask` answers a real question about this repo with citations from a
cold clone; ADR-0004 accepted; goldens started.

**Where the goldens live (2026-08-12).** The graded corpus was extracted
into the sibling repository `fux-playground` and `examples/` was deleted
from this tree ([ADR-0012](adr/0012-playground-sibling-repo.md)). Fifty
ranked golden queries over ten documents; **41 pass, 9 are named engine
gaps** carrying a written mechanism. Scope is unchanged — this is where
M1's "goldens started" now points.

### M2 — the T1 accelerator

Derived blocked term-major JSONL + offset table; integer `mx` skipping;
**the differential law** — accelerator results ≡ scan results, asserted
byte-for-byte as a test, the same discipline the ARC cache carries.
Int-cached Hamming lane; RRF fusion; `find`/`answer` verbs. **DoD:** R3 on
the RFC corpus (8 872 docs): warm `ask` ≤ 150 ms including worst-case
common terms; differential suite green; ADR-0005. **Also:** the
playground's `known_failure` class 3 (term presence beating aboutness —
`q008`/`q017`/`q030`/`q031`/`q036`) is a named acceptance target for the
dense lane; each is an `XPASS` when it closes.

### M3 — the graph lane

Edge extraction ported; `community` assignment (deterministic
label-propagation or Leiden-class with fixed seed — decided in ADR-0006);
PPR-lite; `explain`/`graph`/`path` verbs. **DoD:** the archived relational
eval passes on the new kernel; ADR-0006. **Also:** the playground's
supersession and near-duplicate gaps (`q005`, `q009`, `q011`, `q015`)
are named acceptance targets for this lane — they are precisely the
queries no amount of term statistics can answer.

### M4 — the refer plane

> Scope note (2026-08-10): a `url` *source* landed early via a consumer-owned
> middleware file — [ADR-0010](adr/0010-url-source-consumer-middleware.md)
> (⏳ proposed). The adapter cap below is untouched (core ships no URL
> adapter; all network lives in the consumer's file), but this milestone's
> refer plane must decide the verify-time fetch path for `src:"url"` docs.

HTTP (conditional GET) + Confluence adapters — **the cap holds**; more
systems arrive via [`proposals/mcp-adapters.md`](proposals/mcp-adapters.md),
not code. ARC cache keyed `(loc, sha)`, results-neutral by construction.
Transient convert + chunker + passage re-score on fetched bytes. Freshness:
every answer stamped; live verification behind `[freshness] verify`
(fenced network, default off). **DoD:** R4 mock-server bench (cold k=10
≤ 3 s, warm ≤ 300 ms); ARC differential test; offline degradation honest
(git sources full function, external → declared staleness); ADR-0007.

### M5 — maintenance

Hooks (post-commit/merge/checkout → delta ingest = re-emit changed lines);
merge driver via gitattributes: line-wise LWW on `(ver, sha)`, machine
planes never conflict, snapshot-mode human files conflict normally **on
purpose**; `meta: hashed` enforced at write time for every non-git source
(the council's ACL ruling, as code not docs). **DoD:** R5 (20-doc commit
< 1 s); R6 three-tier merge harness; ADR-0008.

### M6 — scale and T2

`tpack` writer/reader (same records, one property swaps); mmap byte-aligned
segments as the T2 accelerator; partial-clone deployment doc;
external-shards-only committing; bench at 100k synthetic + RFC + 1M
synthetic if feasible. **The paper's §4 (keyspace) and §5–§6 (size,
latency) are rewritten from projection to measurement here.** **DoD:** R7;
tier-auto flips by measurement; every R has a measured value or an honest
failure ADR; ADR-0009.

### M7 — dogfood & release gate

Fux answering real questions daily in the fux and Anton repos for two
weeks; DOGFOOD.md refreshed; README becomes a real front door; CHANGELOG
current. Launch work (product-gtm) starts only after this gate. **DoD:**
Arpit ships a release he has been using himself.

### M8 — deferred (parked with triggers, never ambient)

Realistic-query-workload pruning experiment — now purely an *optimization*
study (could shrink T1/T2; cannot block anything) · sentence-unit selection
+ the format-aware structure extractor (spine retest, Graphify-inspired) ·
query-log views · the `enriched` AI ingest tier (pinning contract) · BIC
codec inside T2 · MCP adapters · knowledge-CI · wavelet self-index note.

## Predictions, re-registered (R-series; the P-series is closed by ADR-0002/0003)

| id | prediction | threshold | measured at |
|---|---|---|---|
| R1 | canonical writer is byte-deterministic | double-ingest sha-identical, two environments | M1 |
| R2 | T0 slice answers real questions on this repo | cited answer from a cold clone, no accelerator | M1 — **3/3 PASS** 2026-08-12 ([run](conformance/2026-08-12-r2-close/report.md)) |
| R3 | warm `ask` ≤ 150 ms on the RFC corpus, worst-case terms included | bench | M2 |
| R4 | refer plane: cold k=10 ≤ 3 s, warm ≤ 300 ms | mock bench | M4 |
| R5 | 20-doc commit re-indexes < 1 s via hooks | bench | M5 |
| R6 | machine planes merge conflict-free; human conflicts preserved | harness | M5 |
| R7 | committed @100k target-density ≤ 250 MB git-packed; tier-auto correct | measured | M6 |

## Risks

- **Canonical-JSON reproducibility across environments** — the design's
  foundation; R1 exists to catch it first. Mitigations pinned in the
  handoff: no floats, sort_keys, explicit separators, unicode
  normalization decided in ADR-0004, analyzer version in the header.
- **JSONL parse tax worse on real shapes than benched** — R3 is the
  tripwire; T2 is the designed escape.
- **Shard churn at high edit rates** — measured fine at 138 MB; shard
  count is a knob (256 → 1024) if real usage disagrees.
- **Scope creep back toward pruning or extra adapters** — both forbidden
  here; M8 or MCP proposal respectively.

## Process contract (unchanged)

Plan → handoff → prompt per milestone, model named (wrong model fails
silently); 1 feature = 1 ADR with references; worklog every exchange;
OPEN-WORK + DOC-REGISTRY updated in the same change as the work; the lab
(`fux-lab`, RFC corpus) persists — new runs are new directories inside it.
