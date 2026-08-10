# OPEN-WORK — everything not yet built

*The single tracker for outstanding work in the v0.30 rebuild. Maintained by
every session (Cowork and Claude Code): finishing, starting, blocking, or
descoping ANY item updates this file in the same change. Two sections by
repo convention: humans first, agents second.*

---

## §1 · For humans — where the rebuild stands (2026-08-10)

**M0+M1 shipped: the first real code of the rebuild runs, end to end.**
`src/fux/` exists; `fux ingest` builds the committed store from this repo's
own docs, `fux ask` answers questions from it with citations — scan-only, no
accelerator. **R1** (canonical writer byte-determinism) **PASS**. **R2** (T0
answers real repo questions) **2/3 PASS**, one blocked on a pre-existing,
independently-flagged doc-hygiene gap unrelated to this build. Full measured
record, including a mid-build tokenizer fix (stopword filtering) that R2
itself surfaced and that was re-verified rather than patched over just the
one failing case: [ADR-0004](adr/0004-index-format.md) Consequences.

**Background (2026-08-09), unchanged since then:** the pruning gate ran
twice and settled it: INCONCLUSIVE ([ADR-0002](adr/0002-pruning-eval-gate.md))
→ **FAIL** ([ADR-0003](adr/0003-pruning-criterion-rerun.md)) — no selector
came within 35.9 pts of the bar at the 6 % budget. Arpit accepted option E:
**full postings, no pruning**. That decision, plus his JSONL push, produced
the format of record ([index-format compare](compare/index-format.compare.md)):
tiered JSONL — doc-major committed shards that git itself diffs and merges,
a derived blocked term-major accelerator with integer `mx` skipping, and
binary only as record properties. ADRs renumbered from 0001 for the v0.30
line (0016–0018 → 0001–0003; frozen artifacts keep old numbers — see
[adr/README](adr/README.md)); PLAN rewritten to revision 2 (M0–M8, R-series
predictions replacing the closed P-series).

**Open decisions (Arpit):**

1. ~~Move the v0.26 doc set?~~ **RESOLVED 2026-08-10 — Arpit's ruling:
   the root `archive/` is the only archive.** Flattened: `v0.26-docs/` and
   `v0.26-implemented/` are now root entries; `docs/archive/` is gone;
   [`archive/README.md`](../archive/README.md) indexes it all. Follow-up
   (optional, anyone's): add `archive/v0.26-docs` to root `fux.toml`
   sources and re-ingest, which would make R2-Q3's frozen citation
   satisfiable at last — a one-line config change + re-ingest, best done
   with the next build turn rather than as a lone commit.
2. **Ratify ADR-0001** (ingest-mode naming: `extracted`/`enriched`) —
   non-blocking, semantics already fixed.
3. **Start M2** ([`W-22`](#work-items), the T1 accelerator) — nothing blocks
   it now that W-21's DoD is met.
4. Paper §4–§6 are knowingly stale until M6 rewrites them from
   measurements — flagged, deliberate, not forgotten.

**Filed 2026-08-10, not blocking anything:** the agent-search-API landscape was
researched (Parallel, Perplexity, Exa, Brave and the web-index cost literature)
and produced three proposals —
[`proposals/agent-search-landscape.md`](proposals/agent-search-landscape.md)
(the evidence note; also where the wedge argument now lives),
[`proposals/caller-set-freshness-policy.md`](proposals/caller-set-freshness-policy.md)
and [`proposals/token-budget-retrieval.md`](proposals/token-budget-retrieval.md).
**Read the latter two before writing the W-24 (M4 refer plane) handoff** — both
shape the refer API's first surface and are expensive to retrofit. No W-nn or
prediction changed state.

## §2 · For AI agents — machine-oriented work ledger

Rules: pick the lowest OPEN item whose `blocked_by` is satisfied; specs
live in PLAN.md (revision 2) under the same milestone id; update this
table + WORKLOG in every change; **pruning work is forbidden outside
W-38** (plan law).

### Work items

| id | item | status | blocked_by | DoD (short) | spec |
|----|------|--------|-----------|-------------|------|
| W-20 | M0 scaffold: src/fux, pyproject 0.30.0.dev0, doctor, CI paths | **DONE** (2026-08-10) | — | `fux --version` + doctor run; CI green | [handoff](handoff/v0.30.0-m1-t0-slice-handoff.md) §2 |
| W-21 | M1 T0 slice: canonical store + git-dir ingest + scan `ask`, dogfooded — **incl. the AcmePay playground** (`examples/playground/`, 20 fixture docs; its `.fux/index/` gets committed as the visible demo) | **DONE** (2026-08-10) | W-20 | **R1 PASS** · **R2 2/3 PASS** (Q3 blocked on pre-existing `docs/archive/` gap, see §1) · playground walkthrough runs as written (2 doc bugs found+fixed) · ADR-0004 accepted | handoff §2–§9, [ADR-0004](adr/0004-index-format.md) |
| W-22 | M2 T1 accelerator: blocked term-major + `mx` + differential law + Hamming + RRF + find/answer | OPEN·**next** | W-21 | **R3** ≤150 ms warm on RFC corpus; differential suite green; ADR-0005 | PLAN §M2 |
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
| R1 | canonical writer byte-deterministic | shard sha256 identical, ubuntu+macos | **PASS** (2026-08-10) — local double-ingest identical; CI matrix asserts `tests_e2e/test_determinism.py` |
| R2 | T0 answers real repo questions | 3 frozen questions, correct citations, cold clone | **2/3 PASS** (2026-08-10) — Q1/Q2 cite correctly (Q2 needed a tokenizer fix, re-verified); Q3 blocked on the pre-existing `archive/v0.26-docs/` path gap, not this build. Detail: [ADR-0004](adr/0004-index-format.md) |
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
- "archived ADR-NNNN" = the v0.26 line under `archive/v0.26-docs/adr/`;
  bare ADR-NNNN = `docs/adr/`.
- The lab (`~/my_programs/fux-lab`: RFC corpus, manifest) persists — new
  runs are new directories inside it.
