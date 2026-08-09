# OPEN-WORK — everything not yet built

*The single tracker for outstanding work in the v0.30 rebuild. Replaces the
archived IMPLEMENTATION.md as the live tracker. Maintained by every session
(Cowork and Claude Code): finishing, starting, blocking, or descoping ANY
item updates this file in the same change. Two sections by repo convention:
humans first, agents second.*

---

## §1 · For humans — where the rebuild stands

**One paragraph.** The v0.26 engine is archived; the index-and-refer
architecture (paper + component diagram) is decided through six compare
docs; nothing of v0.30 is built yet. The next two moves are M0 (scaffold +
the one open naming decision) and M1 — the pruning eval that the entire
architecture is gated on. If M1's numbers fail, the plan terminates
honestly at M1 and the storage-architecture compare doc reopens.

**Decided and closed** (see [`compare/`](compare/README.md)): the
architecture (index-and-refer), the wire/runtime format split (BIC +
byte-aligned mmap), one MST keyspace, hashed-by-default meta, ARC cache.

**Open decisions** (need Arpit):

1. **Ingest-mode naming** — "enriched" proposed over his original
   "extracted" ([why](compare/ingest-mode-naming.compare.md)); closes as
   ADR-0016 in M0.
2. **top-64 vs top-128** default — decided by M1's k=64 numbers, not taste.
3. **git commit of the reset** — the archive moves + new docs sit
   uncommitted in the working tree until Arpit reviews and commits.

**The build queue** is PLAN.md's M0→M8; nothing runs out of order; every
milestone's DoD includes its P-prediction. **Sequencing amended
2026-08-09** by the M0/M1 handoff's debate gate: the package scaffold moved
*after* the gate (M0a hygiene → ADR-0016 → M1 → M0b scaffold), so a
falsified P1 leaves no orphan scaffold. The live pair is
[`handoff/`](handoff/README.md). Deferred-by-design (M8 + 
proposals): AI-assisted ingest, MPH dictionary, Bloom rare-term
mitigation, external-shards-only committing, [MCP adapters](proposals/mcp-adapters.md),
[knowledge-CI](proposals/knowledge-ci.md), [wavelet self-index](proposals/wavelet-self-index.md).

---

## §2 · For AI agents — machine-oriented work ledger

Rules: pick the lowest OPEN item whose `blocked_by` is satisfied; a
milestone item's spec lives in PLAN.md under the same id; update this
table + WORKLOG in every change; never start M2+ while `P1.status != PASS`.

### Work items

| id | item | status | blocked_by | DoD (short) | spec |
|----|------|--------|-----------|-------------|------|
| W-00 | git-commit the reset (Arpit) | OPEN·human | — | repo history has the archive commit | WORKLOG 2026-08-09 |
| W-03 | M0a doc hygiene: CLAUDE.md (as a **diff for review**), GLOSSARY, INTERVIEW, registry | OPEN | W-00 | no doc names a path that doesn't exist | handoff §DoD, PLAN §M0 |
| W-02 | M0-ADR 0016: ingest-mode naming | OPEN·human-gate | W-00 | ADR written (accepted if Arpit answered, else proposed) | compare/ingest-mode-naming |
| W-04 | M1 KL selector + eval harness (archived engine = baseline; `tools/pruning-eval/`) | OPEN | W-03 | runs on fixture+acme+orbit+100k; sanity checks pass | handoff §5.2–5.3 |
| W-05 | M1 ADR-0017: P1 numbers + ship/kill verdict + conformance filing | OPEN·gate | W-04 | verdict vs **pre-registered** threshold; evidence reproduces | handoff §5.4, paper §8 |
| W-01 | M0b scaffold: src skeleton, pyproject 0.30.0.dev0, CHANGELOG, CI paths | OPEN | **W-05 = PASS** | `fux --version` runs | PLAN §M0b |
| W-06 | M2 MST store + ledger + join | OPEN | W-05=PASS | order-independence ×1000; join CAI props; ≤12 MB @100k | PLAN §M2 |
| W-07 | M3 wire planes P/D/V/E/M + hashed-meta enforcement + `mode=skip` | OPEN | W-06 | round-trips; ≤30 MB @100k (P2/10) | PLAN §M3, compare/meta-privacy |
| W-08 | M4 inflator + segments + MaxScore/Hamming/PPR/RRF kernel + 6 verbs | OPEN | W-07 | ≤150 ms warm rank @100k; new goldens; skip-vs-exhaustive parity | PLAN §M4 |
| W-09 | M5 adapters (git/HTTP/Confluence) + fetch + ARC + assembler + freshness fence | OPEN | W-08 | P4 mock ≤3 s cold; ARC differential test; offline degradation | PLAN §M5, compare/cache-policy |
| W-10 | M6 hooks + merge driver + snapshot mode | OPEN | W-09 | P7 <1 s/20 docs; P6 three-tier merge harness | PLAN §M6 |
| W-11 | M7 1M synth + full P-series measurement + `--warm` + paper §5–6 updated to measured | OPEN | W-10 | every P has a measured value or an honest failure ADR | PLAN §M7 |
| W-12 | M8 deferred set (each = own ADR + Arpit sign-off) | PARKED | W-11 | per item | PLAN §M8 |

### Prediction status (paper §8)

| id | prediction | threshold | status |
|----|-----------|-----------|--------|
| P1 | pruning holds quality | Δhit@5 ≤ 2–3 pts @k=128 | UNMEASURED — **the gate** |
| P2 | wire ≤ 300 MB @1M | measured | UNMEASURED |
| P3 | warm answer ≤ 300 ms @1M | measured | UNMEASURED |
| P4 | cold ≤ 3 s (k=10) | mock bench | UNMEASURED |
| P5 | clone→answer ≤ 5 min | fresh-clone bench | UNMEASURED |
| P6 | zero merge conflicts (tiers 1–2) | harness | UNMEASURED |
| P7 | 20-doc commit < 1 s | hook bench | UNMEASURED |

### Standing maintenance obligations (every session)

- WORKLOG entry per substantive exchange (CLAUDE.md law).
- This file's tables on any status change.
- DOC-REGISTRY row bump for any doc you touch.
- INTERVIEW.md before substantive changes; keep it + the vision current.
- Docs with both §humans and §agents: update BOTH or neither.
- The fux-lab environment persists — new runs are new environments inside
  it (see project memory / conformance README).
