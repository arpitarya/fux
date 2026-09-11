---
type: OpenItem
id: W-135
title: "W-135 — the headroom obligation enters ADR-RS"
description: "Arpit ratified 2026-09-11: every paired run reports, per endpoint and per direction, how many queries could have changed; headroom is 'proven' only with a feature-off/on arm or a generator self-test; zero headroom is Inconclusive; no minimum; a test enforces it for new runs."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-135 — the headroom obligation enters ADR-RS

**Model: Opus** — it writes a measurement rule into the record every future
verdict is judged under; a loose sentence here moves thresholds later, and no
test can catch a rule that is worded wrong.

## The ruling — Arpit, 2026-09-11

Ratified as recommended in this session, all five parts:

1. **Always report headroom.** Every paired run states, **for each endpoint**, the
   score in each arm and **how many queries could have changed**, beside the power
   figure. Computed from the per-query rows — no extra measurement.
2. **Per direction, named.**
   - *Improvement headroom* = queries **not right in both** arms.
   - *Regression headroom* = queries **not wrong in both** arms.
   - A report never prints a bare "headroom" without saying which.
3. **Observed vs proven.** The count from rows is **observed**. It may be called
   **proven** only when the run carries (a) a feature-off/on arm, or a positive
   control, that actually moves those queries, or (b) a generator `--selftest`
   asserting the candidates are separable only by the property under test.
   Otherwise the report labels it **unproven**.
4. **Zero headroom → Inconclusive.** A null in a direction with **0** headroom is
   **Inconclusive**, never *"no detected change"* — the C4 precedent.
5. **No minimum.** No threshold on how much headroom is "enough"; disclosure plus
   rule 4 is the whole rule. A floor would be the moving-threshold failure.

## Why (the grounding the record cites)

- [`regression/2026-08-28-benchmark-contested/report.md`](../regression/2026-08-28-benchmark-contested/report.md) §2 (C6):
  proximity 21.7 % / 21.7 % with **94** could-change — a real null; marker `hit@5`
  120/120 with **0** — no information; the `heading` control 40/40 with **0** —
  "passed" while testing nothing ([VERDICT-C4](../regression/2026-08-28-benchmark-contested/VERDICT-C4.md)).
- The proof mechanism: the same run's `rerank_weight` arm moved 26/120 → 120/120,
  which is what makes the 94 *proven*.
- A difficulty is **relative to the capability under test**: a query is easy for X
  if the engine answers it with X switched off.

## Definition of done

1. **[ADR-RS](../../docs/adr/0133_predictions.md)** gains a decision stating rules 1–5
   **once**, in place (no `Amended` section), with the reference above, and a veto
   condition that is checkable (e.g. *a filed verdict states "no detected change" on
   an endpoint whose report shows 0 headroom in that direction*). §1 updated if it
   summarises the decisions. No other record restates it — others link (L0).
2. **`tests/test_regression_runs.py`:** a measured run dated **on or after
   2026-09-11** whose report has no headroom disclosure fails. Baselined by date like
   `CLASSIFY_SINCE` / `ROWS_SINCE` — **no frozen report is edited**. Pin the baseline
   with the same exempt/applies pair of tests the per-query rule has.
   - Check for the disclosure's presence and its direction labels; **do not** try to
     re-derive the numbers from rows in this item.
3. **Pre-registration template / runbooks** that list what a report must contain
   link to the new decision (link, never restate).
4. The pending items that will file paired runs — W-133, W-134's smoke run excepted,
   the four-priors remeasure, W-97 — gain one line pointing at the decision, so
   they are written under it.
5. `uv run pytest -q tests tests_e2e` green; the commit passes the ADR gate.
6. **Close-out:** delete the W-135 row from `OPEN-WORK.md`; `IMPLEMENTATION.md` +
   `WORKLOG` entries; DOC-REGISTRY bump; `docs/GLOSSARY.md` gains **headroom**
   (improvement / regression, observed / proven); move this file to `archive/open/`.

## Hazards

- 🔴 **Do not re-grade any filed run** against the new rule. It applies forward.
- Do not invent a headroom minimum, and do not word rule 4 so that *"unproven"*
  headroom silently counts as zero — unproven is disclosed, not voided.
- Commit only your own paths. Do not push.

## Prompt

```
Execute work/open/W-135-headroom-obligation.md exactly.
Read CLAUDE.md (§Conformance runs, §A pre-registered threshold may never move),
ADR-RS, and the 2026-08-28 benchmark-contested report first. Explore → plan →
implement → verify. State the rule once, in ADR-RS; everything else links.
Baseline the test by date; edit no frozen report. Commit only your own paths;
do not push. Finish with the close-out list.
```
