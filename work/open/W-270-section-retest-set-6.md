---
type: Handoff
name: W-270
description: "Arpit's ask (2026-10-10), after W-269 failed with a net hit@1 gain at λ = 2.0 (12 wins, 5 losses): re-test the gain-only section term at 2.0 on a NEW question set, set-6-claude, with new long documents, under a new bar that allows rank-1 losses when the net gain clears the SR-RS floor. W-269's verdict stands; nothing is re-read."
item: W-270
filed: 2026-10-10
ball: arpit
---

# W-270 — the gain-only section term at λ = 2.0, re-tested on `set-6-claude`

**Status: OPEN. 🔴 Scored by Arpit 2026-10-11; the decider is owed.** The baseline's `step10_section` `miss@1` is **11, below the frozen slice floor of 15**, so `evidence/decide.py` will STOP (L13: a data defect, never a verdict) — run by Arpit or a session that did not capture. Then what next is Arpit's: L13 says *a run that needs a smaller slice says so and asks Arpit*. The latency guardrail had already failed (+328 ms).

**Model:** DoD 2 — **Claude Opus, highest reasoning, in a fresh claude.ai chat**
(the designated author, A1). DoD 3 — **Opus** (the bar is the deliverable and
no test can catch a bad one). DoD 4–5 — **Sonnet** against the written
procedure. DoD 6 — **Arpit** scores; the decider is a frozen script.

| DoD | state | where |
|---|---|---|
| 1–2 · the test data (prompt 14, `set-6-claude`) | ✅ 2026-10-11 — **W-272** closed | [W-272](../../archive/open/W-272-section-test-data-gen5.md) |
| 3 · the bar frozen and committed alone, **before** the ladder rebuild and before any arm — L13 shape; pins W-273 phase 1's engine | ✅ 2026-10-11 — `b4d961cd`; L13 defaults, C2 margin 2, slice read from counts as a range | [`PRE-REGISTRATION.md`](../regression/2026-10-11-section-retest-set-6/PRE-REGISTRATION.md) |
| 4 · the ladder rebuilt from `seed/` alone (generation 5, a new baseline) | ✅ 2026-10-11 — all eight frozen; `rung-00100` = 118 docs (Arpit's ruling) | [rebuild](../regression/2026-10-11-ladder-gen5-rebuild/report.md) |
| 5 · capture: the engine W-273 phase 1 hands over (else `03fbf782`), three arms on a copy of the new `rung-01000` | ✅ 2026-10-11 — `b4d961cd`; G0, G1, G3 PASS; 🔴 **latency guardrail FAIL (+328 ms)**, so no PASS is possible | [report](../regression/2026-10-11-section-retest-set-6/report.md) |
| 6 · 🔴 **Arpit** scores; a session that did not capture runs the frozen decider | ✅ scored 2026-10-11 (slice 11 < 15); ⏳ decider | the run's `report.md` |

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

## The bar — law L13, frozen at DoD 3

**Re-based on [L13](../../records/0015_LAW-13-the-standing-bar.md) by Arpit's
ruling, 2026-10-10 (Cowork):** *"go with the proposed bar … create it as a law
SR."* The draft's clause 1 (*whole-set net ≥ 6*) was looser than SR-RS
decision 19 once more than six questions flip; it is replaced by L13's C1 + C3.
⚠ **Not frozen.** DoD 3 writes `L13, defaults` plus the parameters below, may
tighten any of them, and is committed before the ladder rebuild.

| L13 row | this run's parameter |
|---|---|
| engine | the commit [W-273](W-273-section-records-implementation.md) phase 1 hands over (W-269's `03fbf782` plus option (b): no section records for record formats) |
| data | `set-6-claude` on a copy of generation 5's `rung-01000`, `ingest --full` — a fresh set, as L13 decision 5 requires |
| arms | baseline `sw-0.0`; **decided arm `sw-2.0`**; `sw-4.0` captured and **reported only** |
| G · gates | W-269's G0 (byte identity at 0.0), G1 (the size bar), G3 (sectionless documents unmoved) |
| slice | `step10_section`: tagged questions that miss `hit@1` at baseline; **≥ 15** (L13 default), read from the scorer's counts |
| endpoint | `hit@1` — the step's claim is that the right document reaches rank 1 |
| C1 · helps | slice net at `sw-2.0` clears SR-RS decision 19 **at the observed flips**, by `verdict.py` |
| C2 · collateral | on questions outside the slice, `hit@1` losses − wins **≤ 2** (L13's default for this set's size, stated explicitly) |
| C3 · net positive | whole-set `hit@1` net at `sw-2.0` **> 0** |
| guardrails | L13 defaults: `hit@5` −1 at most · `evidence_quoted` −2 · `grounded` −2 · median `ask` +100 ms standalone at `rung-10000` |
| outcome | L13 decision 4's table |

Post-hoc, for orientation only: W-269 at `sw-2.0` on set-5 would have read
C1 ✅ (10 / 0), C2 ❌ (2 wins, 5 losses: −3, one past the margin), C3 ✅
(+7) — **INCONCLUSIVE**. It decides nothing (L13 decision 1).

**What a PASS buys:** a ship case for `section_weight = 2.0`, which still owes
the merge (index `_format` `fux.index.v8`, this repository's re-ingest) and
the **8.0×** size ruling ([W-236 ANALYSIS](../regression/2026-10-10-section-records/ANALYSIS.md) §2).
**What a FAIL buys:** the section term is closed on two sets.

## After the verdict (ruled with W-271, Arpit 2026-10-10)

- **PASS** → W-273 phase 2 ships `section_weight = 2.0`.
- **FAIL** → step 10 closes as measured on two sets; SR-SECTIONS stays
  `proposed` with both FAILs on it (not archived), so a `b > 0.5` re-try can
  reopen it.
- **INCONCLUSIVE** → Arpit rules, per L13 decision 4.

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
