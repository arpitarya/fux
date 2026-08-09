# OPEN-WORK — everything not yet built

*The single tracker for outstanding work in the v0.30 rebuild. Maintained by
every session (Cowork and Claude Code): finishing, starting, blocking, or
descoping ANY item updates this file in the same change. Two sections by
repo convention: humans first, agents second.*

---

## §1 · For humans — where the rebuild stands (2026-08-09, evening)

**The research phase is over; the build phase is packaged and ready.**

The pruning gate ran twice and settled it: INCONCLUSIVE
([ADR-0002](adr/0002-pruning-eval-gate.md)) → **FAIL**
([ADR-0003](adr/0003-pruning-criterion-rerun.md)) — no selector came within
35.9 pts of the bar at the 6 % budget. Arpit accepted option E: **full
postings, no pruning**. That decision, plus his JSONL push, produced the new
format of record ([index-format compare](compare/index-format.compare.md)):
tiered JSONL — doc-major committed shards that git itself diffs and merges,
a derived blocked term-major accelerator with integer `mx` skipping, and
binary only as record properties. All four load-bearing claims are
benchmarked (0.035 ms bisect · 397→44 ms common-term fix · one-line edit in
a 138 MB shard deltas to ~nothing · 0.38× git packing).

**Consequences landed today:** ADRs renumbered from 0001 for the v0.30 line
(0016–0018 → 0001–0003; frozen artifacts keep old numbers — see
[adr/README](adr/README.md)); PLAN rewritten to revision 2 (M0–M8,
R-series predictions replacing the closed P-series); the MST keyspace and
BIC wire verdicts superseded for the committed plane; the first build
handoff is ready.

**Open decisions (Arpit):**

1. **Run the M0+M1 prompt** — [`handoff/v0.30.0-m1-t0-slice-prompt.md`](handoff/v0.30.0-m1-t0-slice-prompt.md)
   (Sonnet; one Opus review checkpoint). Nothing else blocks the build.
2. **Ratify ADR-0001** (ingest-mode naming: `extracted`/`enriched`) —
   non-blocking, semantics already fixed.
3. Paper §4–§6 are knowingly stale until M6 rewrites them from
   measurements — flagged, deliberate, not forgotten.

## §2 · For AI agents — machine-oriented work ledger

Rules: pick the lowest OPEN item whose `blocked_by` is satisfied; specs
live in PLAN.md (revision 2) under the same milestone id; update this
table + WORKLOG in every change; **pruning work is forbidden outside
W-38** (plan law).

### Work items

| id | item | status | blocked_by | DoD (short) | spec |
|----|------|--------|-----------|-------------|------|
| W-20 | M0 scaffold: src/fux, pyproject 0.30.0.dev0, doctor, CI paths | OPEN·**next** | — | `fux --version` + doctor run; CI green | [handoff](handoff/v0.30.0-m1-t0-slice-handoff.md) §2 |
| W-21 | M1 T0 slice: canonical store + git-dir ingest + scan `ask`, dogfooded — **incl. the AcmePay playground** (`examples/playground/`, 20 fixture docs; its `.fux/index/` gets committed as the visible demo) | OPEN | W-20 | **R1** cross-platform byte-identity · **R2** three frozen questions cited · playground walkthrough runs as written · ADR-0004 accepted | handoff §2–§9 |
| W-22 | M2 T1 accelerator: blocked term-major + `mx` + differential law + Hamming + RRF + find/answer | OPEN | W-21 | **R3** ≤150 ms warm on RFC corpus; differential suite green; ADR-0005 | PLAN §M2 |
| W-23 | M3 graph lane: edges, community, explain/graph/path | OPEN | W-22 | archived relational eval passes; ADR-0006 | PLAN §M3 |
| W-24 | M4 refer plane: HTTP+Confluence, ARC, assembler, freshness fence | OPEN | W-22 | **R4** mock bench; ARC differential; offline honest; ADR-0007 | PLAN §M4 |
| W-25 | M5 maintenance: hooks, line-wise LWW merge driver, snapshot, hashed-meta enforcement | OPEN | W-23, W-24 | **R5** <1 s/20 docs · **R6** three-tier harness; ADR-0008 | PLAN §M5 |
| W-26 | M6 scale/T2: tpack, mmap segments, partial clone, 100k/1M bench, **paper §4–§6 rewritten to measured** | OPEN | W-25 | **R7**; every R measured or honest failure ADR; ADR-0009 | PLAN §M6 |
| W-27 | M7 dogfood & release gate (fux + Anton, two weeks) | OPEN | W-26 | Arpit ships a release he uses | PLAN §M7 |
| W-30 | Ratify ADR-0001 naming | OPEN·human | — | status → accepted | adr/0001 |
| W-38 | M8 deferred set: realistic-workload pruning *(optimization only)* · sentence/structure selection · query-views · enriched tier · BIC-in-T2 · MCP · knowledge-CI | PARKED | W-26 | one ADR + Arpit sign-off each | PLAN §M8 |

*(W-00…W-14 — the reset, hygiene, both gate runs, and their doc syncs —
are DONE and recorded in WORKLOG 2026-08-09; ids retired.)*

### Predictions (R-series, re-registered in PLAN rev 2; P-series closed)

| id | prediction | threshold | status |
|----|-----------|-----------|--------|
| R1 | canonical writer byte-deterministic | shard sha256 identical, ubuntu+macos | UNMEASURED — M1 |
| R2 | T0 answers real repo questions | 3 frozen questions, correct citations, cold clone | UNMEASURED — M1 |
| R3 | warm ask ≤ 150 ms on RFC corpus | bench incl. worst common terms | UNMEASURED — M2 |
| R4 | refer: cold k=10 ≤ 3 s / warm ≤ 300 ms | mock bench | UNMEASURED — M4 |
| R5 | 20-doc commit re-index < 1 s | hook bench | UNMEASURED — M5 |
| R6 | machine planes conflict-free; human conflicts preserved | harness | UNMEASURED — M5 |
| R7 | committed @100k target-density ≤ 250 MB packed; tier-auto correct | measured | UNMEASURED — M6 |

Closed: **P1 = FAIL** (ADR-0003; option E accepted — full postings).
P2–P7 retired with the rev-1 plan; their successors are R3–R7.

### Standing maintenance obligations (every session)

- WORKLOG entry per substantive exchange (CLAUDE.md law).
- This file's tables on any status change; DOC-REGISTRY row bumps for any
  doc touched; INTERVIEW before substantive direction changes.
- "archived ADR-NNNN" = the v0.26 line under `docs/archive/v0.26-docs/adr/`;
  bare ADR-NNNN = `docs/adr/`.
- The lab (`~/my_programs/fux-lab`: RFC corpus, manifest) persists — new
  runs are new directories inside it.
