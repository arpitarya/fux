---
type: Handoff
name: W-255
description: "A pathological PII regex can hang an ingest (SR-PII Consequences, ex-B-232/B-260). Ruled by delegation 2026-10-04 per compare/pii-regex-bound: a stdlib static linter at load refuses the ReDoS class deterministically, and a `doctor` stress-timing row is where wall-clock lives — advisory, never in the write path. The `regex` dependency with a timeout is the reopen trigger, not the answer. Ratified, NOT built."
item: W-255
filed: 2026-10-04
ball: agent
---

# W-255 — the PII regex bound: lint at load, time in `doctor`

**Model:** Claude Code, **Sonnet** — a parser walk over `re._parser`'s AST and
one doctor row; the design is settled in
[`compare/pii-regex-bound`](../compare/pii-regex-bound.compare.md). **Ratified
2026-10-04 by delegation ([W-251](W-251-backlog-audit-rulings.md) §4, row
B-260), not built.**

## The ruling

SR-PII Consequences, *Owed*: *"A pathological regex can hang an ingest. Python's
`re` has no timeout. Patterns that match the empty string are refused and
`doctor` compiles the rest; beyond that a consumer's regex is a consumer's
regex."* The record said the bound was filed in OPEN-WORK; it never was (B-232
was its only home, now this item).

The compare's verdict, ruled **(a) + (e)**:

- **(a) Engine path — a static linter at load** (`ingest/pii.py::_compile`,
  beside the empty-match refusal). Using the stdlib `re._parser.parse` AST,
  refuse: an unbounded repeat (`*`, `+`, `{n,}`) whose body contains another
  unbounded or variable repeat (`(a+)+`, `(a|aa)*`, `(\w*\s?)*`), and a
  backreference inside an unbounded repeat. The refusal names the rule and the
  fix (possessive `*+`, atomic `(?>…)` — Python ≥ 3.11, inside L7). **This is
  the only option that is a predicate on the pattern string** — the same answer
  on every machine — so it is the only one allowed to decide an ingest (L4).
- **(e) `doctor` — a stress-timing row.** Each rule run over fixed adversarial
  strings (`"a"*N`, `"1"*N`, a long `@`-less prose line; lengths are fixed
  values in `constants.toml [pii]`), timed with `perf_counter`, warn above
  `fux.toml [doctor] pii_rule_budget_ms`. Advisory: doctor output is never a
  committed byte, so wall-clock is legal there and nowhere on the ingest path.
  It covers the **polynomial** class the linter cannot — the shipped email rule
  (`templates/pii.toml.txt:88`) is quadratic on a long `@`-less run, which (e)
  shows and (a) does not.

**Refused, with reasons in the compare:** (b) a wall-clock timeout in the
engine — `_sre` holds the GIL for the whole match so a watchdog thread cannot
interrupt, `signal.alarm` is POSIX-only, and a timeout that skips makes
committed bytes a function of CPU speed; (c) deterministic span windows —
`(a+)+$` hangs on 40 characters and `dotall`/`multiline` rules are allowed
today; (d) the `regex` module with `timeout=` — the only full solution, and it
costs fux its first runtime dependency and a clock in the write path. **(d) is
the reopen trigger**: if (e) shows a real consumer rule hanging a real ingest
that (a) admitted, the dependency decision goes to a record.

## Definition of done

1. `src/fux/ingest/pii.py`: `_lint(pattern) -> str | None` over
   `re._parser.parse`, called from `_compile`; a refused rule raises the same
   named `FuxError` shape the empty-match refusal uses, naming the rule and the
   construct. The starter `templates/pii.toml.txt` and this repository's
   `.fux/pii.toml` load clean.
2. `src/fux/doctor.py::_pii_health`: a `pii timing` row — per rule, the worst
   of the fixed strings in ms; `warn` above the budget key, naming the rule.
3. L12: stress-string lengths in `src/fux/constants.toml [pii]`; the budget in
   `fux.toml [doctor] pii_rule_budget_ms` (template + this repo's `fux.toml`;
   SR-CONFIG's key block and `tests/test_sr_config_keys.py` both directions).
4. Tests: the four canonical ReDoS shapes are refused at load with the rule's
   name; the whole starter passes the linter; a planted quadratic rule warns in
   doctor; **no wall-clock on any ingest path** — a grep guard in the shape of
   the L5 import fence.
5. Records, same change, `sr-hash.py --write`: SR-PII — a new decision (the
   linter: what it refuses, why static), the Consequences *Owed* paragraph
   rewritten to what is true; SR-DOCTOR's check table gains the row;
   SR-CONFIG the key. The duplicated SR-PII block is W-245's.
6. Both suites whole; a WORKLOG entry; `CHANGELOG.md` *Added*.

## Out of scope

- Redaction of paths (B-233, `cost`) and anything about what `doctor` repairs
  (it never does).
- A Node twin — redaction is Python-only (ingest).

## Hazards

- ⚠ `re._parser` is private stdlib. It has been stable since 3.11 and L7 pins
  ≥ 3.12; pin the import behind one function so a future rename is one edit.
- ⚠ The linter is conservative by design: a nested-quantifier rule that is
  actually safe is refused with the fix named. Say so in the error text.
