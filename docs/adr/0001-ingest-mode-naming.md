---
type: ADR
title: "ADR-0001: ingest-mode naming — extracted / enriched"
description: Names both ingest tiers. The model-assisted tier is `enriched`; the deterministic default is renamed from `inferred` to `extracted`, which aligns it with the ported edge grade EXTRACTED (= deterministic) and removes the residual half of the collision the first draft left behind.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# ADR-0001: ingest-mode naming — `extracted` / `enriched`

- **Status:** **proposed** — awaiting Arpit's ratification. Written now, not
  blocked on, per the M0/M1 handoff §7 ("if he has not answered when you reach
  it, write the ADR as proposed with the recommendation and move on").
- **Date:** 2026-08-09
- **Amended:** 2026-08-09, at Arpit's request ("another name for inferred would
  be good as well"). The amendment is **§Amendment**, and it changes the
  decision — the first draft fixed only half of the collision it diagnosed.
- **Feature:** ingest-mode vocabulary (paper §3.2) — the words used in
  `fux.toml`, the ledger, the glossary, and every later doc.

## Context

**The concept is settled; only the word is open.** Arpit's directive
(2026-08-09): *"ingest needs to happen without ai model — inferred mode;
ingest with AI model can be extracted mode."* Two tiers, one deterministic and
default, one model-assisted and opt-in. That is accepted and load-bearing —
paper §3.2 pins the AI tier's outputs into the index with provenance and grades
them below deterministic signal.

**The problem is a collision.** Archived ADR-0009 grades link-graph edges
`EXTRACTED` = **deterministic, parsed, no model** and `INFERRED` =
**model-derived**. That is the *exact inverse* of the proposed ingest-mode
mapping. Both grades survive in the edge schema ported at M3, so the two words
would mean opposite things in adjacent code and adjacent config.

**Why now:** every doc written from M1 onward uses these words. Naming after
the vocabulary has spread costs a rename across docs, config keys, and the
ported schema.

## Amendment (2026-08-09) — the first draft fixed only half the collision

**The defect.** This ADR was written to remove a collision with the ported edge
grades. It renamed the *AI* tier and left the deterministic tier as `inferred` —
but `INFERRED` is precisely the edge grade that means **model-derived**. So the
original draft shipped the identical collision it diagnosed, moved one word to
the left:

| word | as an edge grade (ported, ADR-0009) | as an ingest mode (first draft) |
|---|---|---|
| `EXTRACTED` / `extracted` | deterministic, parsed, **no model** | *(unused)* |
| `INFERRED` / `inferred` | **model-derived** | deterministic, **no model** ✗ |

A reader meeting `mode = inferred` next to `grade: INFERRED` gets the opposite
meaning in adjacent config and code. That is the whole failure this ADR exists
to prevent.

**The fix is free, and it is Arpit's own word on the other side.** ADR-0001
already moved the AI tier to `enriched`, which *vacates* `extracted`. Assigning
it to the deterministic tier makes the two vocabularies agree exactly:

| word | edge grade | ingest mode | agree? |
|---|---|---|---|
| `extracted` | deterministic, no model | deterministic, no model | **yes** |
| `enriched` / `INFERRED` | model-derived | model-derived | **yes** |

No rename of the ported edge schema. No collision anywhere. And it uses the
word from Arpit's directive verbatim — just on the tier the rest of the repo
already gives it to.

**Alternatives for the deterministic tier, considered:**

| name | for | against |
|---|---|---|
| **`extracted`** *(recommended)* | Aligns exactly with the ported `EXTRACTED` grade; uses Arpit's word; zero migration. | Visually close to `enriched` — both 9 letters, both start `e`. Real cost in logs and config scanning. |
| `derived` | Accurate and broad (covers conversion, chunking, term selection, codes); visually distinct. | Slightly abstract; "derived from what?" needs the doc. |
| `literal` | Strongest signal that nothing was invented; pairs cleanly with `enriched`. | Understates the tier — it converts PDFs and computes embedding codes, which is more than reading literally. |
| `parsed` | Unambiguous about determinism; short. | Understates for the same reason; a PDF→text conversion is not parsing. |
| keep `inferred` | Zero change; matches the archived *fidelity* vocabulary. | **Keeps the collision.** Rejected — it is the defect this amendment exists to fix. |

**If the `extracted`/`enriched` similarity bothers you, `derived`/`enriched` is
the runner-up** and costs nothing extra to choose. The one option that should
not survive is `inferred`.

## Decision

**`extracted` (default, no model) + `enriched` (opt-in, model-assisted).**
*(Amended — the first draft said `inferred`/`enriched`; see §Amendment.)*

- Config surface: `[ingest] mode = extracted | enriched`.
- `extracted` = deterministic, `$0`, offline: convert, chunk, select terms,
  compute codes, parse links. Everything is *taken from* the document; nothing
  is invented.
- `enriched` names the additive tier honestly: it *adds* signal on top of the
  deterministic pass; it never replaces it.
- The ported edge grades `EXTRACTED` / `INFERRED` are **left untouched**, and
  now agree with the mode names instead of contradicting them.
- **`inferred` is retired as an ingest-mode word.** It survives only in the
  archived *fidelity* vocabulary (`fidelity: inferred | advanced`), which is
  frozen with the v0.26 engine and is not part of v0.30's surface.

**Why not Arpit's original assignment** (`extracted` = the AI tier): it would
require renaming the ported edge grades so `EXTRACTED` stops meaning
"deterministic" repo-wide — one mechanical ADR plus edits to a schema being
ported with its tests. Keeping the word but flipping which tier owns it buys
the same clarity for zero migration. This ADR takes the cheap half of his
phrasing and drops the expensive half.

**Superseded rationale (first draft), kept for the record:** `extracted` was
originally rejected as "the one option that requires renaming something that
already ships." That reasoning was sound *for assigning it to the AI tier*, and
it does not apply to assigning it to the deterministic tier — where no rename
is needed at all. The first draft simply did not consider that assignment.

<details>
<summary>Original §Decision text, before the amendment</summary>

> **`inferred` (default, no model) + `enriched` (opt-in, model-assisted).**
> Config surface: `[ingest] mode = inferred | enriched`. `inferred` keeps its
> existing meaning and its alignment with the archived fidelity vocabulary.
> The ported edge grades `EXTRACTED` / `INFERRED` are left untouched.

</details>

**Why not Arpit's original word for the AI tier:** `extracted` there is the one
option that
requires renaming something that already ships and already has tests. It buys
a closer match to his phrasing and costs a mechanical-but-real rename ADR plus
edits to a schema being ported. `enriched` buys the same clarity for free.

**This is a recommendation with a live override.** `derived`/`enriched` is the
runner-up and costs nothing extra; see the amendment's table.

## Alternatives considered

| option | why it lost |
|---|---|
| **`inferred` / `enriched`** (this ADR's own first draft) | **Rejected by the amendment.** Fixes the collision on one word and reproduces it on the other: `INFERRED` is the edge grade for *model-derived*, so `mode = inferred` would sit next to `grade: INFERRED` meaning the opposite thing. |
| **`inferred` / `extracted`** (Arpit's original assignment) | Matches his phrasing exactly, which is worth real weight. Loses on cost: `EXTRACTED` must stop meaning "deterministic" everywhere in the repo — its own ADR plus edits to the M3 edge schema and the ported ADR-0009 tests. The only option with migration cost, and it *still* leaves `inferred` colliding. |
| **`inferred` / `advanced`** | Zero migration cost, but `advanced` already means "better converter, still no model" in the archived fidelity vocabulary. Trades one collision for another, and a quieter one — a reader would not *know* they were confused. |
| **`derived` / `enriched`** | Genuinely close second: collision-free, accurate, and visually distinct from `enriched` in a way `extracted` is not. Lost only because `extracted` additionally *agrees with* the ported edge grade rather than merely avoiding it — alignment beats non-collision. Take this one if the `e…ed`/`e…ed` similarity annoys you in practice. |
| **`literal` / `enriched`**, **`parsed` / `enriched`** | Both collision-free and pleasantly concrete, but both understate the tier: it converts PDFs, chunks, selects terms and computes embedding codes. "Literal" and "parsed" describe a subset of that work. |
| **rename both tiers** (e.g. `deterministic` / `assisted`) | Most self-describing of all. Rejected because it discards Arpit's vocabulary entirely for a marginal readability gain, and `deterministic` is a repo-wide *law*, so overloading it as a mode name weakens the stronger word. |

## Consequences

**Easier.** The two vocabularies now *agree* rather than merely avoiding each
other: `extracted` means "deterministic, no model" as a mode and as an edge
grade, and `enriched`/`INFERRED` both mean "model-derived". M2–M8 docs, the
ledger schema and the glossary can use the words without a footnote, and
nothing in the ported edge-grade code changes.

**Harder.** `extracted` and `enriched` look alike — same first letter, same
length, same ending. In a log line or a config diff that is a real scanning
cost, and it is the one concrete argument for the `derived` runner-up.

Also: the words are not assigned the way Arpit first said them. `extracted` is
his word, on the other tier. A maintainer reading his directive next to this
repo makes one hop; this ADR is that hop.

**We now owe:**
- `[ingest] mode = extracted | enriched` as the config surface when ingest is
  built (M2+); no other spelling accepted. **`inferred` is not a valid mode
  value** — it survives only in the frozen archived fidelity vocabulary.
- GLOSSARY entries updated for both terms (**done**, 2026-08-09), stating the
  edge-grade alignment explicitly.
- The `enriched` tier itself stays **deferred to M8** — this ADR names it, it
  does not schedule it. Its contract (outputs pinned with provenance, re-read
  never re-generated, graded below deterministic signal) is paper §3.2's and
  is unchanged by the naming.
- If Arpit picks `derived` instead: amend this ADR in place (it is still
  `proposed`); nothing else changes, since neither word touches the edge schema.
- If Arpit insists on his original *assignment* (`inferred` no-model /
  `extracted` AI): this ADR is superseded rather than amended, and the
  edge-grade rename ships as its own ADR with the ported ADR-0009 tests updated
  in the same change.

## References (required)

- **The compare doc that framed the fork:**
  [`../compare/ingest-mode-naming.compare.md`](../compare/ingest-mode-naming.compare.md)
  — debate, matrix, reopen-trigger.
- **The concept being named:**
  [`../paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md) §3.2
  (two ingest modes; the pinning + grading contract), which itself flags this
  collision as an open decision.
- **The colliding vocabulary:** archived ADR-0009 (retrieval kernel + edge
  grades) — [`archive/v0.26/archive/v0.26-docs/adr/0009-…`](../../archive/v0.26/archive/v0.26-docs/adr/0009-retrieval-kernel-graph-verbs.md).
- **Prior art for the distinction being drawn** (deterministic extraction vs
  model-derived enrichment, graded separately): Campos, R. et al., *YAKE!
  Keyword Extraction from Single Documents Using Multiple Local Features*,
  Information Sciences 509, 2020 —
  https://doi.org/10.1016/j.ins.2019.09.013 — the deterministic keyword
  extraction class the `inferred` tier uses, and the baseline any `enriched`
  output must be graded against.
- **Arpit's directive, verbatim:** WORKLOG 2026-08-09.
