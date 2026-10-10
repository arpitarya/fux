---
type: Handoff
name: W-270
description: "Arpit's ask (2026-10-10), after W-269 failed with a net hit@1 gain at λ = 2.0 (12 wins, 5 losses): re-test the gain-only section term at 2.0 on a NEW question set, set-6-claude, with new long documents, under a new bar that allows rank-1 losses when the net gain clears the SR-RS floor. W-269's verdict stands; nothing is re-read."
item: W-270
filed: 2026-10-10
ball: arpit
---

# W-270 — the gain-only section term at λ = 2.0, re-tested on `set-6-claude`

**Status: OPEN. 🔴 Arpit runs the authoring prompt** (DoD 2).

**Model:** DoD 2 — **Claude Opus, highest reasoning, in a fresh claude.ai chat**
(the designated author, A1). DoD 3 — **Opus** (the bar is the deliverable and
no test can catch a bad one). DoD 4–5 — **Sonnet** against the written
procedure. DoD 6 — **Arpit** scores; the decider is a frozen script.

| DoD | state | where |
|---|---|---|
| 1 · the authoring prompt, written from SR-WORK-TESTDATA | ✅ 2026-10-10 | [prompt 14](../golden/prompts/14-claude-gen5-section-seed.md) |
| 2 · 🔴 **Arpit** runs it in a fresh claude.ai chat, commits blocks 1–3, keeps block 4 | ⏳ | prompt 14 §How Arpit runs it |
| 3 · the bar frozen and committed alone, **before** the ladder rebuild and before any arm | ⏳ | `work/regression/<date>-section-retest-set-6/PRE-REGISTRATION.md` |
| 4 · the ladder rebuilt from `seed/` alone (generation 5, a new baseline) | ⏳ | [`work/golden/README.md`](../golden/README.md) phase 4 · A23 |
| 5 · capture: engine pinned at `03fbf782`, three arms on a copy of the new `rung-01000` | ⏳ | the run's `report.md` |
| 6 · 🔴 **Arpit** scores; a session that did not capture runs the frozen decider | ⏳ | the run's `VERDICT.md` |

## Why

**Arpit, 2026-10-10 (Claude Code),** reading W-269's verdict: *"Even though
there were rank 1 losses … wins were still higher, right?"* — then *"shouldn't
we go with two point zero?"* — then, on the recommendation to re-test first:
*"Okay. Let's have new set of questions."* Then he chose: **Claude authors it,
in a fresh session**, and **it adds new long documents**, not questions alone.

At λ = 2.0, W-269 measured `hit@1` 12 wins / 5 losses (net +7, 45 → 52) and the
`step10_section` pool's misses 23 → 13. It failed the frozen bar's clause 2
(zero rank-1 losses) ([VERDICT](../regression/2026-10-10-section-gain-only/VERDICT.md)).
**That verdict stands.** Three things kept it from being a ship decision:

- **λ = 2.0 was picked after the score**, the best of four tries on one set;
- the set had been read by **two** mechanisms (W-236 and W-269);
- the gain had costs: `other` pool misses 13 → 16, `section@1` 3 / 4.

A fresh set with fresh long documents answers whether the +7 survives
selection. A looser bar is legal **only** as a new pre-registration on a new
set ([SR-RS](../../records/0133_predictions.md) d10b), which is this item.

## The bar — proposed here, frozen at DoD 3

⚠ **Not frozen.** These are the numbers DoD 3 starts from; DoD 3 may tighten
them, never loosen them, and must be committed before the ladder rebuild.

| | |
|---|---|
| engine | branch `claude/gracious-galileo-aqrg8b` at **`03fbf782`** (W-269's build), unchanged |
| data | `set-6-claude` on a copy of generation 5's `rung-01000`, `ingest --full` |
| arms | baseline `sw-0.0`; **decided arm `sw-2.0`**; `sw-4.0` captured and **reported only**, because 2.0 was the top of W-269's grid and the trend still rose |
| G0 · G1 · G3 | W-269's, unchanged (byte identity at 0.0, the size bar, sectionless documents unmoved) |
| G2 | baseline `step10_section` `reorderable@1` **≥ 15** (W-269's 23 was on 45 tagged; this set asks for ≥ 60) |
| clause 1 | whole-set `hit@1` net (wins − losses) at `sw-2.0` **≥ 6**, the SR-RS paired-comparison floor |
| clause 2 | on questions **not** tagged `step10_section`, `hit@1` losses − wins **≤ 2** — the collateral cap W-269 had no clause for |
| outcome | PASS needs G0–G3 and both clauses; a clause-1 net of 4–5 is INCONCLUSIVE and goes to Arpit |

**What a PASS buys:** a ship case for `section_weight = 2.0`, which still owes
the merge (index `_format` `fux.index.v8`, this repository's re-ingest) and
the **8.0×** size ruling ([W-236 ANALYSIS](../regression/2026-10-10-section-records/ANALYSIS.md) §2).
**What a FAIL buys:** the section term is closed on two sets.

## Custody

- **The prompt's author (this session) may not author the set** (A1): it read
  W-269's scores. Arpit's fresh claude.ai chat is the designation.
- 🔴 **The key is Arpit's.** No session writes, reads or receives block 4.
- `informed`, permanently (A5): Claude authors the set and Claude's engine
  runs it. **Set 1 stays the only externally-authored set**, and a claim that
  needs one Claude did not write still needs set 1 (or a new Codex set).

## Reference

- [W-269 VERDICT](../regression/2026-10-10-section-gain-only/VERDICT.md) ·
  [W-269 report](../regression/2026-10-10-section-gain-only/report.md)
- [SR-SECTIONS](../../records/0161_sections.md) d5 ·
  [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) R10, A1–A24 ·
  [SR-RS](../../records/0133_predictions.md) d10b, d14, d19
