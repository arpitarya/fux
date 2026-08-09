---
type: Plan
title: "Fux v0.30 — the index-and-refer rebuild"
description: From-scratch implementation plan for the architecture in docs/paper/the-fux-index-paper.md and docs/architecture-components.svg — milestones M0–M8, each gated by falsifiable predictions P1–P7.
status: active
timestamp: 2026-08-09T00:00:00Z
---

# Fux v0.30 — the index-and-refer rebuild

## For AI agents — quick reference (read this block, then jump)

- **Live tracker:** [`OPEN-WORK.md`](OPEN-WORK.md) §2 — pick work there,
  not here; this file is the *spec* for each milestone id.
- **Hard gate:** no M2+ work while P1 is unmeasured or failed (W-05).
- **Decisions:** verdict-first in [`compare/`](compare/README.md); one
  still open (ingest-mode naming → ADR-0016, Arpit's call).
- **Laws:** $0 · stdlib · deterministic · offline-default · 1 feature =
  1 ADR (from 0016) · every rule referenced · WORKLOG every exchange ·
  OPEN-WORK + DOC-REGISTRY rows updated in the same change as the work.
- **Old world:** engine `../archive/v0.26/` (runnable, reference-only,
  M1's baseline); its docs `archive/v0.26-docs/`; port list below —
  port with tests, don't rewrite.
- **Handoffs:** every milestone ships as handoff doc + Claude Code prompt,
  model named per the milestone table (wrong model fails silently).

---

*The second reset. The v0.19–0.26 substrate engine is archived at
[`../archive/v0.26/`](../archive/v0.26/) — reference-only, kept runnable
because M1 uses it as the quality baseline. Its documentation (ADRs
0001–0015, compare docs, example docs, tracker, old flow diagram) is at
[`archive/v0.26-docs/`](archive/v0.26-docs/); the previous plan is at
[`archive/PLAN-v0.26.md`](archive/PLAN-v0.26.md). ADR numbering continues
from 0016 in a fresh [`adr/`](adr/); archived ADRs are cited by their old
numbers with the archive path.*

## What this build is

**One sentence:** rank from a small committed index; fetch content from the
systems that own it; verify at answer time.

Authority for every design decision, in order:

1. [`paper/the-fux-index-paper.md`](paper/the-fux-index-paper.md) — the
   architecture, size/latency models, predictions P1–P7.
2. [`architecture-components.svg`](architecture-components.svg) — the v2
   component map (one MST keyspace, wire/runtime split, two ingest modes).
3. [`architecture-index-and-refer.svg`](architecture-index-and-refer.svg) —
   the high-level flow.
4. The council rulings (WORKLOG 2026-08-09): "index" not "db"; hashed meta
   default; adapters capped git + HTTP + Confluence (MCP is the endgame);
   the pruning eval gates all build; DA minority report noted.

## Laws (unchanged from the engine's founding)

$0 default · stdlib-only runtime · deterministic to the byte · offline by
default (network only inside explicit fences) · git is the transport ·
1 feature = 1 ADR · every rule carries a reference · worklog every exchange.

New law from this architecture: **content is never durable outside its
source system** except under explicit `snapshot` policy.

## What survives from v0.26 (port, don't rewrite)

These modules are law-hardened and keep their tests; they are *ported* from
`archive/v0.26/` when their milestone needs them, imports rewritten, tests
carried:

| module | used by | port in |
|---|---|---|
| frontmatter parser | ledger, snapshot mode | M2 |
| converters (inferred/advanced tiers) | ingest (transient now) | M1 |
| chunker (heading-aware) | passage re-score | M5 |
| BM25F scoring math + exact-df discipline (ADR-0008) | kernel | M4 |
| RRF fusion (k=60, ADR-0007) | kernel | M4 |
| FuxVec embed + 32 B codes (ADR-0010) | V/ plane | M3 |
| PPR-lite + edge extraction (ADR-0009) | E/ plane, kernel | M3–M4 |
| synth corpus generator + bench + eval sets + goldens | M1 gate, M7 | M1 |
| CLI surface & verbs (ask/find/answer/explain/graph/path) | UX contract | M4 |

Everything else — storage, the SQLite substrate, per-file cache, lock,
state plane, profiles — is superseded and stays archived.

## Milestones

| # | name | proves | est. size | model for handoff |
|---|------|--------|-----------|-------------------|
| M0a | doc hygiene + ADR-0016 naming | — | small | Sonnet |
| M1 | **THE GATE: pruning eval** | P1 | ~200 LOC + harness | Sonnet build, Opus analysis |
| M0b | package scaffold — **only on P1 = PASS** | — | small | Sonnet |
| M2 | MST keyspace + ledger | P6 (join) | ~800 LOC | Opus |
| M3 | wire index (P/D/V/E/M) | P2 | ~1.2k LOC | Opus |
| M4 | runtime segments + kernel | P3 | ~1.5k LOC | Opus |
| M5 | refer plane (adapters/fetch/ARC/assembler) | P4 | ~1k LOC | Sonnet |
| M6 | maintenance (hooks, merge driver, snapshot) | P6, P7 | ~500 LOC | Sonnet |
| M7 | scale run @1M | P2, P3, P5 | bench work | Sonnet |
| M8 | deferred: AI-assisted mode · MPH dict · top-64 | — | — | — |

**Sequencing is a hard rule (council, pre-mortem seat): no milestone starts
before the previous one's DoD is met, and M1's DoD is *numbers in an ADR*,
not code merged.** M2+ exist in this plan conditionally on P1 passing.

---

### M0 — Repo hygiene, the naming ADR, and (conditionally) the scaffold

**Split amended 2026-08-09 by the M0/M1 handoff's debate gate.** The
original order scaffolded a package before P1 could falsify the
architecture it exists for — the pre-mortem seat's "build the fun part
first" failure. Corrected: **M0a (hygiene) → M0-ADR (naming) → M1 (the
gate) → M0b (scaffold, only on PASS)**. The live spec for all of it is
[`handoff/v0.30.0-m0-m1-gate-handoff.md`](handoff/v0.30.0-m0-m1-gate-handoff.md).

**M0a deliverables (unconditional).** CLAUDE.md synced to this plan
(proposed as a diff, never auto-applied); GLOSSARY given the v0.30
vocabulary; INTERVIEW gains a reset entry; DOC-REGISTRY's two ⚠ rows
cleared; OPEN-WORK statuses updated. **ADR-0016: the ingest-mode naming
decision** ("inferred" stays; the AI tier named — resolve the
EXTRACTED/INFERRED edge-grade collision by Arpit's call;
`enriched` recommended).

**M0b deliverables (only if P1 = PASS).** New `src/fux/` skeleton (`cli.py`, `errors.py`, package
layout mirroring the five planes: `keyspace/`, `wire/`, `runtime/`,
`refer/`, `ingest/`); `pyproject.toml` at `0.30.0.dev0` (hatchling, stdlib
runtime, extras for converters); CLAUDE.md synced to this plan (build
section replaced, laws restated, archive pointer); fresh CHANGELOG;
`.github/` workflow paths updated for the new tree.

**DoD.** M0a: no doc names a path that doesn't exist; ADR-0016 written.
M0b: `uv run fux --version` prints 0.30.0.dev0; `fux doctor` stub runs.

### M1 — THE GATE: document-centric pruning eval  *(P1)*

**Question.** Does KL top-k pruning hold ranking quality on Fux's corpora?

**Deliverables.** KL term selector (Büttcher–Clarke document-centric
scoring; ~200 LOC, stdlib); an eval harness that (a) runs the **archived
v0.26 engine** to produce full-index baseline rankings on the 100k
synthetic + acme + orbit corpora, (b) produces pruned-index rankings at
k = 128 and k = 64 through the same scorer, (c) reports hit@5, P@10, and a
rare-term recall slice, per corpus per k.

**DoD.** **ADR-0017 records the numbers and the ship/kill verdict.**
Thresholds (pre-registered, paper §8): within 2–3 pts hit@5 of baseline at
k=128 → proceed; worse → the architecture is falsified, return to snapshot
designs, this plan terminates at M1 and says so honestly.

**Notes.** Uses the archived engine as a *baseline generator only* —
reference-use, permitted by the archive's charter. Rare-term losses are
expected and measured, not hidden; the Bloom-signature mitigation is
designed but NOT built unless numbers demand it.

### M2 — The keyspace: MST store + ledger  *(P6 join half)*

**Deliverables.** Content-defined chunker (rolling hash, ~4 KB target,
fixed seed); content-addressed chunk files under `.fux/index/`; tree
builder with **unique-representation invariant**; root-hash computation;
reader (mmap, binary search within chunks); the **join** (per-entry LWW
register on (version ordinal, sha tie-break); observed-remove set for
membership); `L/` schema (locator, sha@index, `mode = refer|snapshot`,
`meta = hashed|plain`, version info); front-coded columnar wire encoding.

**DoD.** Property tests: same entries in any insertion order → byte-identical
chunks and root (the MST invariant, 1 000 random orders); join is
commutative + associative + idempotent (hypothesis-style randomized check,
stdlib-only harness); ledger for the 100k synthetic ≤ 12 MB. ADR-0018.

### M3 — The wire index: P/ D/ V/ E/ M/  *(P2)*

**Deliverables.** BIC encoder/decoder (pure Python — decode-once, speed
non-critical on the wire path); 4-bit impact quantization (global scale,
recorded in header); doc-id assignment = ledger sort order (clustering
lever, Figure 4); `D/` = sorted u64-hash array + Elias-Fano offsets + varint
df (MPH deferred to M8 as a pure-win upgrade); `V/` raw codes; `E/`
delta-varint typed adjacency; `M/` with `hashed|plain` enforcement at write
time — **hashed is the default for every non-git source; plain requires
explicit config** (council ruling).

**DoD.** Round-trip property tests on every encoder; wire size for the 100k
synthetic **≤ 30 MB** (P2 scaled: 300 MB / 10); collision detection on term
hashes raises at build (ADR-0008 discipline carried forward). ADR-0019.

### M4 — Runtime segments + the query kernel  *(P3)*

**Deliverables.** Inflator: wire → byte-aligned mmap segments (128-entry
posting blocks, per-block max-impact + skip, `memoryview.cast` decode);
MaxScore evaluation (block-max skipping; deterministic traversal, doc-id
ties); int-cached Hamming scan; CSR PPR (fixed 3 iterations, ported
constants); RRF fusion; the six verbs re-plumbed onto `retrieve()` over the
new kernel (ADR-0009's projection table unchanged).

**DoD.** P3 scaled: warm rank ≤ 150 ms at 100k on the bench machine;
relational eval passes; **new goldens baselined and committed** (rankings
legitimately differ from v0.26 — pruning changes the index; the goldens
that carry over unchanged are the *relational* and *decline* behaviors);
`--lexical-only` parity between MaxScore result set and exhaustive scoring
on the pruned index (correctness check: pruning may drop docs, skipping may
not). ADR-0020.

### M5 — The refer plane  *(P4)*

**Deliverables.** Adapters: git-dir (path+blob-sha read), generic HTTP
(conditional GET, ETag/Last-Modified), Confluence REST (bearer token from
env; page-version check). **Cap enforced: no further adapters in v0.30**
(council; MCP is the endgame and gets a proposal doc, not code). Fetch
layer (cache → adapter read-through); ARC cache keyed (locator, sha),
byte-budgeted, results-neutral by construction; answer assembler: transient
convert of fetched bytes → chunker → passage re-score → extractive answer +
confidence floor (ported ADR-0014 semantics) → citation carries fresh sha +
staleness stamp; freshness verification of the cited set behind
`[freshness] verify = true` (fenced network, off by default).

**DoD.** P4 on a local mock server: cold k=10 ≤ 3 s, warm ≤ 300 ms
end-to-end at 100k; offline test: external sources degrade to doc-level
answer + declared staleness, git sources fully functional; ARC never
changes a result (differential test vs cache-off). ADR-0021.

### M6 — Maintenance  *(P6 full, P7)*

**Deliverables.** `fux setup --hooks` (post-commit/merge/checkout → delta
ingest from ledger sha-diff); the merge driver: `fux merge-driver` wired
via gitattributes for keyspace paths — join `L/`, re-derive the rest;
snapshot mode (per-source: machine-made Markdown copy committed with
provenance frontmatter — the ported parser's home).

**DoD.** P7: 20-doc commit re-indexes < 1 s. P6: branch-merge harness —
concurrent same-doc ingest merges clean (tier 1), divergent-version merges
resolve identically on both sides (tier 2), snapshot-file human edits
conflict normally (tier 3, asserted *present*). ADR-0022.

### M7 — Scale  *(P2, P3, P5 at 10⁶)*

**Deliverables.** Synth generator extended to 1M docs (deterministic,
link-structured); full P-series measurement run; clone→first-answer bench
(P5: ≤ 5 min including inflation + repo-shard re-derivation); cache-warming
at setup (`fux setup --warm` prefetches top-N central docs); partial-clone
deployment note in docs.

**DoD.** The paper's §5–§6 tables updated from *projection* to *measured*,
deltas recorded; any prediction that failed gets an honest ADR, not a
threshold edit.

### M8 — Deferred (each needs its own ADR + Arpit sign-off)

AI-assisted ingest mode (pinning + grading contract per paper §3.2) · MPH
dictionary upgrade (~15 MB saving) · top-64 default (pending M1's k=64
numbers) · external-shards-only committing · Bloom-signature rare-term
mitigation · MCP adapter strategy.

---

## Risks (from the council + paper §9, with owners in the plan)

- **Pruning quality** → M1 is first, pre-registered, kill-capable.
- **Interpreted-Python constants** → every latency DoD measured at 100k
  before 1M; signature prefilter held in reserve (M8).
- **ACL leak via meta** → hashed default enforced at write time (M3), not
  in documentation.
- **Cold-fetch demo pain** → `--warm` in M7; mock-server bench in M5 keeps
  the number visible from the start.
- **Adapter sprawl** → hard cap in M5; MCP proposal instead of code.
- **DA minority report** (postings-by-term on v0.26 first) → superseded by
  the reset decision, recorded here so the road not taken stays visible.

## Process contract (per CLAUDE.md)

Every milestone: plan → handoff doc → Claude Code prompt (name the model —
see table above; wrong model fails silently), 1 ADR per feature with
references, worklog entry per exchange, docs synced in the same change.
The lab environment persists; new scale runs are new environments inside it.
