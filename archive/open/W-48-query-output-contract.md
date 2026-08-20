# W-48 — three output-contract inconsistencies in the query verbs

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-18
**Blocked by:** — · **Model:** **Sonnet.** Three small, well-specified changes
against a written definition of done, with tests to verify them.

**Priority: low, deliberately.** Under OPEN-WORK rule 5 the damage here is
*static* — it is the same size next month. The only argument for doing it soon
is that output contracts are cheaper to change before there are many callers
than after.

## The three

1. **`--explain` cannot be read programmatically.** It appends
   `[accelerator]` / `[scan]` / `[hybrid]` in text mode only; `cmd_ask` returns
   before it when `--json` is set. A caller cannot log which path answered —
   which is exactly what is worth logging when a query is slow.
   **Do:** add `"path"` to the `--json` object when `--explain` is set.
   Additive; no existing consumer breaks.

2. **`answer --json` omits `"source"` on the no-match path.** The hit case emits
   `"source": "index"`; the empty case is `{"answer": null, "citation": null}`.
   [ADR-ANSWER](../../docs/adr/0006_answer.md) tells callers to key on
   `"source"` to detect the M4 upgrade, so its absence is a trap.
   **Do:** emit `"source": "index"` in both branches.

3. **`find`'s no-match line is prose on stdout.** `No confident matches.` lands
   in a pipe where a path was expected.
   **Do: nothing yet.** It is consistent across all three verbs and `--json`
   gives the machine-readable form. This is listed so the decision is visible,
   not to schedule it — [ADR-FIND](../../docs/adr/0005_find.md) names it as its
   strongest rejected alternative and ties it to the record's veto: **a real
   script observed breaking on it** is the evidence that reopens it.

## Definition of done

- Items 1 and 2 implemented; item 3 explicitly left alone with a one-line note
  in the WORKLOG saying so.
- Tests: `ask --json --explain` carries `"path"`; `answer --json` carries
  `"source"` in both branches.
- `CHANGELOG.md` under `[Unreleased] → Changed` — both are output-contract
  changes, however small.
- [ADR-ASK](../../docs/adr/0004_ask.md) §Consequences: drop the "`--explain` is
  text-only" note. [ADR-ANSWER](../../docs/adr/0006_answer.md) §Consequences:
  drop the missing-`"source"` note. **Same change** — Law zero.
- This file and its OPEN-WORK row deleted, outcome in
  [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazards

- **Do not "fix" item 3 by moving the message to stderr for `find` only.** That
  makes the three verbs behave differently for the same condition, which is a
  worse inconsistency than the one it solves.
- **Do not change the shape of `results`.** `find --json` and `ask --json`
  returning identical objects is a deliberate property
  ([ADR-FIND](../../docs/adr/0005_find.md)), not an oversight.

## Evidence

[`../regression/2026-08-18-query-verbs/ANALYSIS.md`](../regression/2026-08-18-query-verbs/ANALYSIS.md)
