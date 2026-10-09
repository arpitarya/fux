---
type: Handoff
name: W-269
description: "Arpit's ask (2026-10-10, Cowork), after W-236 failed: test the recommended second mechanism for section records — a GAIN-ONLY term, so a document gains only where its best section beats the document scored as one unit, and a sectionless document gains nothing by construction. Built on the unmerged branch w236-sections, judged by W-236's frozen bar unchanged."
item: W-269
filed: 2026-10-10
ball: agent
---

# W-269 — section records, second mechanism: gain-only

**Status: filed 2026-10-10, not started.** 🟢 for Claude Code, **Opus**.

**Arpit, 2026-10-10 (Cowork),** on W-236's FAIL: *"Ideally, it should have
worked. Research-wise failed."* Then, on the recommended fix: *"Okay. Let's
create a work item for a recommended approach."* That is the ruling this item
carries: **gain-only, on the existing section plane.**

## Why — what W-236 measured

W-236 built U2 · B2 and failed (drift) at every weight: rank-1 losses
4 · 5 · 9 · 10, pool misses 23 → 26 · 26 · 28 · 28
([VERDICT](../regression/2026-10-10-section-records/VERDICT.md)). Its
pre-registration named the cause in advance as *the likelier failure*: a
sectionless (short) document is its own single section, so B2 gave it about
λ × its **whole** score, while a long document's best section holds only part
of its tf. The term favoured short documents.

The literature's gains (Callan 1994; Kaszkiel & Zobel 1997/2001; Bendersky &
Kurland 2008) come from long multi-topic documents against BM25 with
`b ≈ 0.75`. fux runs `b = 0.15`, so little length penalty is left to recover;
the compare doc's reopen trigger already names `b` above 0.5. **This item does
not change `b`.** It removes the short-document bias and measures whether any
headroom remains.

## The mechanism (to be fixed in the record before any build)

Recommended form, for a candidate document `d`:

```
G(d)  = max(0, max_k S_sec(d#s_k) − S_self(d))
S(d)  = ( S_doc(d) + λ · G(d) ) · w(d)
```

- `S_self(d)` is the document's body and heading slots scored **as one unit
  under the same section statistics** (`avg_wlen` of the section view, document
  `df` and `n`) that score its sections.
- A **sectionless document has `S_sec = S_self`, so `G = 0`** — the bias W-236
  measured cannot occur. A long document gains only where its query words are
  **concentrated** in one section, which is the case the step exists for.
- `G ≤ max_k S_sec`, so SR-SECTIONS decision 7's accelerator skip ceiling stays
  a sound bound unchanged. Re-check it, do not assume it.
- The exact form is the design step's (DoD 1). A form that needs a fork of
  Arpit's goes to him before code.

## Definition of done — in this order

1. **Amend [SR-SECTIONS](../../records/0161_sections.md) decision 5** to the
   gain-only term (B2 stays the ruled blend; this is its gain-only variant),
   and note the reopen in [`compare/section-units`](../compare/section-units.compare.md).
   Restamp. Still `proposed`.
2. **Pre-register, frozen, committed alone before any build code:**
   - **W-236's bar unchanged** — the same clauses (no new rank-1 misses
     anywhere; `hit@1` net on the `step10_section` pool read from score counts),
     the same set (`set-5-claude`, gen-4 `rung-01000`), the same G0/G1/G2 gates,
     and a decider whose hash is frozen with it. **No threshold moves**
     ([SR-RS](../../records/0133_predictions.md) d10b).
   - The λ grid, fixed here. The gain is smaller than a full section score, so
     W-236's grid need not carry over — but it is chosen now, never after a
     number.
   - **One added gate, G3:** at every λ, every sectionless document's score is
     byte-identical to `λ = 0`. It tests the diagnosis directly.
3. **Build on a branch from `w236-sections` (`f2a139fd`)**, unmerged: Python and
   Node (differential law), the accelerator bound, both suites green.
4. **Capture the arms.** 🔴 **Arpit scores** (`just golden-score <run>`). A
   session that did not capture runs the decider and files the VERDICT.
5. **On FAIL:** the step closes as measured. Record both mechanisms' results in
   SR-SECTIONS and the compare doc; the branch is Arpit's.
   **On PASS:** nothing merges until [ANALYSIS §2](../regression/2026-10-10-section-records/ANALYSIS.md)'s
   size question is ruled by Arpit — on this repository the section plane is
   8.0× the document plane (`.jsonl` 75.6 %). Then SR-SECTIONS is accepted in
   the merging change, with the `_format` bump and CHANGELOG (Breaking).

## Hazards

- ⚠ **Every number is `informed`**, and this is the **second mechanism on the
  same 90 questions** — a PASS here is weaker evidence than W-236's FAIL was.
  Say so in the VERDICT.
- ⚠ The capturing session has seen W-236's per-query rows. The grid and form are
  fixed before any arm; that is the only defence, so keep it.
- One mechanism per arm. `b` is not touched; raising it is a separate ruling.
- ⚠ U1 stays refused (no section index from fetched content).

## Records this will touch

SR-SECTIONS (decision 5, the FAIL banner, then `accepted` only on a merged
PASS) · compare/section-units (status) · SR-RANKING · SR-NODE-SEARCH ·
SR-TUNE (`section_weight`, on PASS) · SR-RS (only if a new gate needs a rule).

**Model:** Claude Code, **Opus** — a ranking change across both readers.
