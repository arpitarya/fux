---
type: Handoff Prompt
title: Claude Code prompt — Knowledge substrate v3 (handoff 0004)
description: Paste-ready prompt executing handoff 0004 — explore → plan → implement M1–M8 → eval gate → close out at v0.23.0.
status: implemented
implemented: 2026-07-22 (v0.23.0)
adrs: [0008](../adr/0008-substrate-store-lock-state.md), [0009](../adr/0009-retrieval-kernel-graph-verbs.md), [0010](../adr/0010-fuxvec-binary-dense-search.md), [0011](../adr/0011-profiles-lean-state.md)
timestamp: 2026-07-21T00:00:00Z
---

# Claude Code prompt — Knowledge substrate v3

Paste everything below into Claude Code at the repo root. **Precondition:
v0.22.x shipped, both suites + eval green.**

---

Build **phase 4 — the knowledge substrate** for the Fux engine, executing the
committed spec exactly.

**Explore first (do not skip, in this order):**
1. `CLAUDE.md` — binding: constraints ($0/stdlib/deterministic/no-model),
   enterprise litmus, docs law, doc style, worklog duty, OKF pattern.
2. `docs/handoff/0004-knowledge-substrate-handoff.md` — **the build contract**:
   DoD, normative schemas/formats (fux.db, fux.lock, .fux/state/, FuxVec,
   kernel), milestones M1–M8, edge cases, close-out.
3. `docs/proposals/knowledge-substrate.md` — the accepted design of record:
   every rationale, trade-off, size table, and reference. Decisions are closed;
   if you believe one must reopen, STOP and say so with evidence — never
   silently deviate (deviations go to implementation.md → Deviations + the ADR).
4. `docs/model-handoff-interview.md` + the verdict blocks in `docs/compare/`.
5. The shipped code you are extending: `src/fux/index/` (bm25f scoring is
   UNTOUCHABLE math), `src/fux/embed/`, `src/fux/query/`, `src/fux/ingest/`,
   and the suites incl. `tests_e2e/eval/`.

**Then plan:** post the M1–M8 milestone plan (from the handoff) with your file-
level breakdown per milestone before writing code. The phase-4 table is
**already pre-registered** in `docs/implementation.md` — you must update its
row **at every single milestone completion** (status + tests + note; never
batched), and keep the "Now working on" line current throughout. This is
binding (CLAUDE.md 4b).

**Hard rules for the whole phase:**
- Zero new runtime dependencies. `sqlite3` is stdlib; nothing else enters.
- Determinism everywhere: double-ingest → byte-identical fux.lock, state
  buckets, and fux.db; fixed seeds/tie-breaks for Bloom hashing, PPR, k-means
  (if IVF triggers); no wall-clock output (SOURCE_DATE_EPOCH discipline).
- **Parity is sacred:** v0.22 goldens must pass byte-for-byte for small-corpus
  JSON-profile `ask`/`find`/`answer` and for `--lexical-only` at every
  milestone from M4 on. Profile parity (full vs lean rankings identical) is
  eval-asserted at M7+.
- BM25F/RRF/extractive-answer *math* does not change — only the plumbing
  around it.
- Network stays inside the ingest fence (+ `db pull`, which is explicit user
  action); the import-fence test extends to the new modules.
- Update `docs/cli-examples.md` (normative formats) **before** implementing
  each new renderer; goldens derive from it.
- Docs style law: no walls of text in anything you write.

**Verify (phase gate, all required):**
- Both suites green at every milestone; final: unit + e2e + eval + the M8
  synthetic-100k benchmark with numbers recorded (ingest time, sizes vs the
  proposal §8b estimates, latencies full/lean, FuxVec scan time → IVF decision).
- Fresh-clone e2e: rm -rf `.fux/index` → doc-level answers from committed
  state; `fux ingest` restores chunk level; three-way `--check` messages exact.
- Eval gate: hybrid+dense_global+graph ≥ v0.22 hybrid (hit@5, MRR) **and** ≥1
  recorded zero-candidate miss rescued. If the gate fails, ship the substrate
  with graph/global behind flags, record honestly, and say so.

**Close out (per CLAUDE.md, all required):**
- ADRs 0008–0011 (with the flagged binary-quantization citations verified and
  cited properly in 0010).
- Full docs pass: fux-plan status, README (new verbs + state-in-git story),
  cli-examples, fux-toml (shipped keys move out of the proposed fence),
  GLOSSARY (fux.lock, state plane, FuxVec, lean profile, kernel…),
  DOC-REGISTRY rows, worklog phase report, interview state-of-play,
  implementation.md ✅s.
- Archive `docs/handoff/0004-*` with `status: implemented` + ADR links.
- Version **0.23.0**.

If any milestone cannot finish cleanly, stop there, leave the repo green at the
last completed milestone, and write up exactly what blocked you in the worklog
and implementation.md. Do not start work you cannot land.

Begin with M1. Show the milestone plan first.
