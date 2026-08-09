# OPEN-WORK — everything not yet built

*The single tracker for outstanding work in the v0.30 rebuild. Replaces the
archived IMPLEMENTATION.md as the live tracker. Maintained by every session
(Cowork and Claude Code): finishing, starting, blocking, or descoping ANY
item updates this file in the same change. Two sections by repo convention:
humans first, agents second.*

---

## §1 · For humans — where the rebuild stands

**One paragraph.** The v0.26 engine is archived; the index-and-refer
architecture is decided through six compare docs; nothing of v0.30 is built,
**and the plan is paused at its first gate.** M0a (doc hygiene) and ADR-0016
(naming, proposed) are done. **M1 — the pruning eval the whole architecture is
gated on — ran, and came back INCONCLUSIVE:** the pre-registered bar was met
(Δ hit@5 = 0.00 pts at k=128 on all three corpora), but top-128 pruning touched
only 0–2.5 % of documents and left 96–100 % of postings in place, because these
corpora's documents hold 32–46 distinct terms where the size model assumes
~2 000. Nothing was actually tested. **Nothing further gets built until P1 is
re-run on a long-document corpus** — see
[ADR-0017](adr/0017-pruning-eval-gate.md).

**The one number that is real:** at k=64 — still ten times milder than the
production setting — acme loses **9.1 points** of hit@5. That points against
P1, but it is an extrapolation, not a measurement, and it is labelled as one.

**Arpit's call, pending:** accept INCONCLUSIVE and fund the re-run (W-13), or
overrule and proceed. The scaffold (W-01) stays blocked either way until he
rules.

**The re-run is designed and packaged** (2026-08-09), and it changed more
than the corpus. Research into the criterion produced three amendments, held
in [`compare/pruning-criterion.compare.md`](compare/pruning-criterion.compare.md):
*(a)* the gate metric moves from the index's own hit@5 to **recall@20 of the
candidate set**, because the index feeds a fetch-and-re-score stage and is a
candidate generator, not the final ranker — published work finds re-rank
pipelines absorb pruning's recall loss; *(b)* the criterion opens to five
arms, since KL divergence structurally deletes a homogeneous corpus's subject
terms (it dropped `webhook` from `webhooks.md`) and a per-term backstop fixes
that by construction; *(c)* the budget becomes **retention-based**, so "keep
the top k" stops meaning different things on short and long documents.
Handoff and prompt are ready under [`handoff/`](handoff/README.md).

**Decided and closed** (see [`compare/`](compare/README.md)): the
architecture (index-and-refer), the wire/runtime format split (BIC +
byte-aligned mmap), one MST keyspace, hashed-by-default meta, ARC cache.

**Open decisions** (need Arpit):

1. **P1's INCONCLUSIVE verdict** — accept and fund the long-document re-run
   (W-13), or overrule. [ADR-0017](adr/0017-pruning-eval-gate.md) states the
   case; the threshold was **not** moved.
2. **Ingest-mode naming** — `enriched` recommended over his original
   `extracted` ([why](compare/ingest-mode-naming.compare.md));
   [ADR-0016](adr/0016-ingest-mode-naming.md) is written and waiting to flip
   from `proposed` to `accepted`.
3. **CLAUDE.md rewrite** — [`../CLAUDE.md.proposed`](../CLAUDE.md.proposed) +
   [diff](handoff/v0.30.0-claude-md.diff), proposed not applied. Adopt with
   `git mv`.

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
| W-13 | **M1-rerun: make P1 decidable** — long-doc corpus (RFCs + repo docs), 5 selector arms (KL / impact / A+B / **A+B+C** / none) at matched retention 6·15·30 %, **recall@20** as the gate | OPEN·**next** · handoff ready | W-05 | corpus gate (median ≥ 500 distinct terms) passes; retention matched ±1 pt; ADR-0018 states PASS/PARTIAL/FAIL/VOID against a frozen pre-registration | [handoff](handoff/v0.30.0-m1-rerun-handoff.md) · [prompt](handoff/v0.30.0-m1-rerun-prompt.md) · [compare](compare/pruning-criterion.compare.md) |
| W-14 | Ratify or amend `compare/pruning-criterion.compare.md` after W-13 | OPEN | W-13 | verdict block reflects measured outcome | compare/pruning-criterion |
| W-01 | M0b scaffold: src skeleton, pyproject 0.30.0.dev0, CHANGELOG, CI paths | **BLOCKED** | **W-05 = PASS** (not granted) | `fux --version` runs | PLAN §M0b |
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
| P1 | pruning holds quality | Δhit@5 ≤ 2–3 pts @k=128 | **INCONCLUSIVE** (2026-08-09) — Δ = +0.00 pts on all three corpora, i.e. the rule's letter is met, **but** top-128 pruned 2.5 % / 1.6 % / **0.0 %** of documents and retained 96–100 % of postings, so nothing was tested. At k=64, where it bites, acme loses **9.09 pts**. → [ADR-0017](adr/0017-pruning-eval-gate.md) |
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
