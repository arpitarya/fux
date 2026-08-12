# OPEN-WORK — the index of what is still open

*One line per open item. **Detail lives in [`open/W-nn-*.md`](open/README.md)**,
one file per item. Nothing done is recorded here — a closed item's row and
its detail file are deleted in the same change that closes it, and its
durable record is its ADR plus the [WORKLOG](WORKLOG.md) entry.*

*Maintained by every session (Cowork and Claude Code): finishing, starting,
blocking, or descoping ANY item updates this file **and** its detail file in
the same change as the work.*

**Where the build stands (2026-08-12):** M0+M1 shipped — `fux ingest` and
`fux ask` work end to end on this repo, scan-only. **R1 PASS · R2 3/3 PASS**
(the third closed by W-42 on 2026-08-12 —
[the run](conformance/2026-08-12-r2-close/report.md)). The pruning gate
closed **FAIL**; the committed index carries full postings, permanently
([ADR-0003](adr/0003-pruning-criterion-rerun.md)). **[W-22](open/W-22-m2-t1-accelerator.md)
(M2, the T1 accelerator) is next and nothing blocks it.**

**Blocked on Arpit — the inbox (every session updates this, dated):** read the
Phase 0 report and the [ratification package](handoff/v0.32.0-ratification-package.md)
— five decisions in one sitting, clearing **W-30 · W-31 · W-32 · W-33** and
releasing the W-22/M2 start gate (waiting since 2026-08-12) · decide **W-44**
(retired-content signalling, filed 2026-08-12). Any row here older than **5 days**
is named, with its age, in every session's first output (CLAUDE.md, *Triage first*).

---

## Open items

Rule: pick the lowest OPEN item whose `blocked_by` is satisfied. `PLAN.md`
is the spec; the detail file is the state.

| id | item | status | filed | blocked_by | detail |
|----|------|--------|-------|-----------|--------|
| W-22 | M2 · T1 accelerator — blocked term-major, `mx` skipping, differential law, Hamming, RRF, `find`/`answer` | OPEN·**next** | ≤2026-08-11 | — | [W-22](open/W-22-m2-t1-accelerator.md) |
| W-23 | M3 · graph lane — edges, community, `explain`/`graph`/`path` | OPEN | ≤2026-08-11 | W-22 | [W-23](open/W-23-m3-graph-lane.md) |
| W-24 | M4 · refer plane — HTTP+Confluence, ARC, assembler, freshness fence | OPEN | ≤2026-08-11 | W-22 | [W-24](open/W-24-m4-refer-plane.md) |
| W-25 | M5 · maintenance — hooks, line-wise LWW merge driver, hashed-meta enforcement | OPEN | ≤2026-08-11 | W-23, W-24 | [W-25](open/W-25-m5-maintenance.md) |
| W-26 | M6 · scale & T2 — `tpack`, mmap segments, 100k/1M bench, **paper §4–§6 rewritten to measured** | OPEN | ≤2026-08-11 | W-25 | [W-26](open/W-26-m6-scale-t2.md) |
| W-27 | M7 · dogfood & release gate — fux + Anton, two weeks | OPEN | ≤2026-08-11 | W-26 | [W-27](open/W-27-m7-dogfood-release-gate.md) |
| W-30 | Ratify ADR-0001 (ingest-mode naming) | OPEN·human | 2026-08-12 | — | [W-30](open/W-30-ratify-adr-0001.md) |
| W-31 | Ratify ADR-0010 + ADR-0011 — both built and shipped, still ⏳ proposed | OPEN·human | 2026-08-12 | — | [W-31](open/W-31-ratify-adr-0010-0011.md) |
| W-32 | Adopt or reject the CLAUDE.md rewrite; apply the `.fux/` layout line | OPEN·human | 2026-08-12 | — | [W-32](open/W-32-claude-md-adoption.md) |
| W-33 | Resolve the ADR-numbering contradiction (CLAUDE.md "0016" vs adr/README "0001") | OPEN·human | 2026-08-12 | — | [W-33](open/W-33-adr-numbering-contradiction.md) |
| W-44 | Decide how retired content is signalled — the v0.26 doc set now answers questions about the *current* engine | OPEN·human | 2026-08-12 | — | [W-44](open/W-44-archived-content-signalling.md) |
| W-45 | Source exclusion — `[sources] dirs` is include-only, so committed measurement evidence contaminates the corpus it measures | OPEN | 2026-08-12 | — | [W-45](open/W-45-source-exclusion.md) |
| W-38 | M8 · the deferred set — one ADR + Arpit sign-off each; **pruning work is forbidden outside this item** | PARKED | ≤2026-08-11 | W-26 | [W-38](open/W-38-m8-deferred.md) |

## Predictions still unmeasured

| id | prediction | threshold | measured at |
|----|-----------|-----------|-------------|
| R3 | warm `ask` on the RFC corpus | ≤ 150 ms, worst common terms included | W-22 |
| R4 | refer plane | cold k=10 ≤ 3 s / warm ≤ 300 ms | W-24 |
| R5 | 20-doc commit re-index | < 1 s via hook | W-25 |
| R6 | machine planes conflict-free, human conflicts preserved | three-tier harness | W-25 |
| R7 | committed @100k target density | ≤ 250 MB packed; tier-auto correct | W-26 |

R1 **PASS**. **R2 PASS 3/3** (2026-08-12, cold tree — [run](conformance/2026-08-12-r2-close/report.md)).
P1 **FAIL** (option E, full postings); P2–P7 retired with plan revision 1 —
their successors are R3–R7.

## Standing obligations (every session)

- WORKLOG entry per substantive exchange (CLAUDE.md law).
- This index **and** the item's detail file, on any status change;
  DOC-REGISTRY row bumps for any doc touched; INTERVIEW before substantive
  direction changes.
- "archived ADR-NNNN" = the v0.26 line under `archive/v0.26-docs/adr/`;
  a bare ADR-NNNN = `docs/adr/`.
- The lab (`~/my_programs/fux-lab`: RFC corpus, manifest) **persists** — new
  runs are new directories inside it, never a rebuild.
