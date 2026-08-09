# OPEN-WORK — everything not yet built

*The single tracker for outstanding work in the v0.30 rebuild. Replaces the
archived IMPLEMENTATION.md as the live tracker. Maintained by every session
(Cowork and Claude Code): finishing, starting, blocking, or descoping ANY
item updates this file in the same change. Two sections by repo convention:
humans first, agents second.*

---

## §1 · For humans — where the rebuild stands

**One paragraph.** The v0.26 engine is archived; the index-and-refer
architecture is decided through seven compare docs; nothing of v0.30 is built,
**and the plan is stopped at its first gate.** M0a (doc hygiene) and ADR-0016
(naming, proposed) are done. **P1 — the pruning claim the whole size story rests
on — has now been measured properly, and it FAILED.**

On 8 872 RFCs (median 967 distinct terms per document — the regime the paper
assumes), the best of four pruning selectors reaches **recall@20 = 0.627**
against an unpruned ceiling of **0.986** at the 6 % retention the size model
needs. That is **35.9 points** short of a **2-point** bar, and still 12.7 points
short at 30 % retention. Every validity check passed, so the run is evidence.
→ [ADR-0018](adr/0018-pruning-criterion-rerun.md).

**What this does and does not kill.** Index-and-refer is *not* falsified —
ranking from a committed index and fetching content from the systems that own it
is untouched. What is falsified is that the index can be made ~16× smaller **by
discarding postings**. The committed footprint goes from ~250 MB to **0.6–1.5 GB**
at 10⁶ documents, and partial clone plus external-shards-only committing stop
being optional. Whether it is still worth building at that size is Arpit's call.

**The best remaining argument that this is too harsh** is the query workload:
the eval asks the index to find a document from a verbatim 8–16 token sentence
out of it, which is close to a worst case. Real agent queries are short and
salient — made of exactly the terms pruning keeps. Testing that is **W-15**, the
next move, and it is the one thing that could reasonably overturn the verdict.

**Arpit's call, pending:** accept the FAIL and fund W-15, or overrule. **W-01
(the scaffold) stays blocked** either way — the pre-registered PASS condition
was not met.

**Decided and closed** (see [`compare/`](compare/README.md)): the
architecture (index-and-refer), the wire/runtime format split (BIC +
byte-aligned mmap), one MST keyspace, hashed-by-default meta, ARC cache.

**Open decisions** (need Arpit):

1. **P1's FAIL** ([ADR-0018](adr/0018-pruning-criterion-rerun.md)) — accept and
   fund the realistic-query re-measurement (W-15), or overrule. The threshold
   was **not** moved. The earlier INCONCLUSIVE run
   ([ADR-0017](adr/0017-pruning-eval-gate.md)) stands as the record of the
   refusal that produced this one.
2. **Ingest-mode naming** — `enriched` recommended over his original
   `extracted` ([why](compare/ingest-mode-naming.compare.md));
   [ADR-0016](adr/0016-ingest-mode-naming.md) is written and waiting to flip
   from `proposed` to `accepted`.
3. ~~**CLAUDE.md rewrite**~~ — **adopted** (the [diff](handoff/v0.30.0-claude-md.diff)
   is kept for the record); ingest-mode names since synced to ADR-0016's
   amendment.

**Closed since the last revision:** ~~top-64 vs top-128~~ — **decided negative**
by M1 (acme −9.09 pts at k=64, 3× the hard bar); ~~git commit of the reset~~ —
done, commit `7fb81a8`.

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
| W-00 | git-commit the reset | **DONE** 2026-08-09 | — | repo history has the archive commit | commit `7fb81a8` |
| W-03 | M0a doc hygiene: CLAUDE.md (as a **diff for review**), GLOSSARY, INTERVIEW, registry | **DONE** 2026-08-09 | W-00 | no doc names a path that doesn't exist | handoff §DoD, PLAN §M0 |
| W-02 | M0-ADR 0016: ingest-mode naming | **DONE (proposed)** · human-gate open | W-00 | ADR written; `status: proposed` recommending `enriched` — Arpit has not ratified, so both ADR and compare doc stay ⏳ | [ADR-0016](adr/0016-ingest-mode-naming.md) |
| W-04 | M1 KL selector + eval harness (archived engine = baseline; `tools/pruning-eval/`) | **DONE** 2026-08-09 | W-03 | 23 tests green; fixture+acme+orbit+synth-100k run; k=∞≡baseline and byte-identical re-run both verified | [tools/pruning-eval/](../tools/pruning-eval/README.md) |
| W-05 | M1 ADR-0017: P1 numbers + ship/kill verdict + conformance filing | **MEASURED · verdict = INCONCLUSIVE** · awaiting Arpit | W-04 | verdict vs **pre-registered** threshold; evidence reproduces | [ADR-0017](adr/0017-pruning-eval-gate.md) |
| W-13 | ~~M1-rerun: make P1 decidable~~ **DONE 2026-08-09 → FAIL** — long-doc corpus (RFCs + repo docs), 5 selector arms (KL / impact / A+B / **A+B+C** / none) at matched retention 6·15·30 %, **recall@20** as the gate | **DONE** | W-05 | corpus gate passed (967); retention matched ±0.12 pts; verdict **FAIL** | [handoff](handoff/v0.30.0-m1-rerun-handoff.md) · [prompt](handoff/v0.30.0-m1-rerun-prompt.md) · [compare](compare/pruning-criterion.compare.md) |
| W-14 | ~~Ratify or amend `compare/pruning-criterion.compare.md`~~ | **DONE (amended)** 2026-08-09 | W-13 | verdict marked ❌ falsified; the metric reframe survives, the selector is untested | compare/pruning-criterion |
| W-15 | **Re-measure P1 with a realistic query workload** (short, salient, keyword-style — what an agent actually sends), fresh pre-registration | OPEN·**next** | W-13 | the strongest remaining argument that the FAIL is too harsh, tested or refuted | [ADR-0018 §Limitations 1](adr/0018-pruning-criterion-rerun.md) |
| W-16 | Re-derive paper §5's size model at a retention that holds quality, or at no pruning | OPEN | W-15 | §5 states a measured footprint, not the falsified 6 % assumption | [ADR-0018 §Consequences](adr/0018-pruning-criterion-rerun.md) |
| W-17 | Test Rule A on a corpus with real headings, judged corpus-wide | OPEN | W-15 | the heading spine accepted or rejected on evidence (RFCs gave it a 1-term spine) | [ADR-0018](adr/0018-pruning-criterion-rerun.md) |
| W-01 | M0b scaffold: src skeleton, pyproject 0.30.0.dev0, CHANGELOG, CI paths | **BLOCKED** | **P1 = PASS** (measured FAIL) | `fux --version` runs | PLAN §M0b |
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
| P1 | pruning holds quality | recall@20 within 2 pts of unpruned @6 % retention | **FAIL** (2026-08-09, re-run) — on 8 872 RFCs (median 967 distinct terms/doc) the best of four selectors is **35.9 pts** below the unpruned index at 6 % retention, and **12.7 pts** below at 30 %. No arm within 2 pts at any rung. The compare doc's prediction was falsified in both halves. → [ADR-0018](adr/0018-pruning-criterion-rerun.md); the earlier INCONCLUSIVE run is [ADR-0017](adr/0017-pruning-eval-gate.md) |
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
