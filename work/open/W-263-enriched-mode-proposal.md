---
type: Handoff
name: W-263
description: "Research item (Arpit, 2026-10-04, W-251 #1): write a proposal for the never-built `enriched` ingest mode — what it would be, how it overlaps with `fux enrich`, and whether a model-assisted step could write index records (.fux/index/*.jsonl) itself — with a compare doc if there are several shapes. Nothing is retired or built until he rules on the proposal."
item: W-263
filed: 2026-10-04
ball: agent
---

# W-263 — a proposal for the `enriched` ingest mode

**Status: filed 2026-10-04, not started.** Research and a proposal only. **No
code, no record change.**

**Arpit, 2026-10-04 (Cowork), on W-251 §3 #1:** *"Create a proposal for
enriched ingest mode. And how it can overlap with fux enrich. Can it write an
index document itself? Index document being index.jsonl. Create a separate work
document to do all this research."* He did **not** take the recommendation to
retire it; the mode stays as it is (ratified 2026-08-19, unbuilt) until he rules
on this proposal.

**Model:** **Cowork**, Opus — a `research` item, never Claude Code (SR-WORK-OPEN-QUEUE rule 37a). Research-heavy, and it lands on two Laws.

## Questions the proposal must answer

1. **What the mode is, in one page.** The folded SR-ENRICHED content in
   [SR-ENRICH](../../records/0137_enrich.md) §*The `enriched` mode* (d1–d6):
   the `mode` value, edge grade `6` `INFERRED`, its L4 fence, provenance
   pinning, below-deterministic grading. Plain examples: a link a model infers
   between two documents that neither names.
2. **The overlap with `fux enrich`.** Today `fux enrich` pins text an agent
   wrote into `.fux/enrich/<sha>.md`, and records stay `mode: extracted`
   because fux only reads committed bytes. Which of the `enriched` mode's goals
   does `fux enrich` already reach (vocabulary, doc2query `ctx`,
   `superseded_by:`), which can it reach with a small extension (e.g. declared
   inferred edges in the enrich file), and which can it never reach?
3. **🔴 Can a model-assisted step write index records itself** — i.e. emit
   lines into `.fux/index/*.jsonl` directly? Walk it against:
   - **L4** (same sources → byte-identical index; no model in the maintenance
     path), **L1/L3**, and the index root hash;
   - the merge driver and `fux ingest --check` (CI proves the index is current
     by re-deriving it — a model-written line cannot be re-derived);
   - SR-EXTRACTED d3 (*a record with any other `mode` is a defect until the
     mode is built*) and the schema's `mode` enum.
   The likely answer is **"only through a committed, pinned artefact that ingest
   then reads deterministically"** (the `fux enrich` pattern) — but prove it or
   refute it; don't assume it.
4. **Shapes, if there is more than one** (→ a compare doc under `work/compare/`):
   e.g. (A) retire the mode, keep grade 6 reserved; (B) fold it into `fux
   enrich` as declared inferred edges; (C) a separate pinned `.fux/inferred/`
   plane ingest reads; (D) model writes index lines directly. Each against the
   Laws, cost, and what a golden run would have to prove.
5. **What it would take to measure** any surviving shape (SR-RS d23: the test
   data must contain the input the feature acts on) — and how this relates to
   [W-257](W-257-enriched-rung.md)'s enriched rung, which measures doc2query.

## Definition of done

1. `work/proposals/enriched-ingest-mode.md`, recommendation first, every claim
   cited to a record line or code path.
2. A compare doc if (4) has more than one live shape.
3. One 🔴 inbox row: Arpit picks a shape. W-251 §3 #1 points here.
