---
type: Compare Doc
title: "The PII regex bound — how an ingest is kept from hanging on a consumer's pattern without a clock in the write path"
description: "Backlog B-260 (ex-B-232) as a fork: SR-PII owes a bound on a pathological regex and Python's `re` has no timeout. Five options — a stdlib static linter at load, a wall-clock timeout, a deterministic span window, the `regex` module with `timeout=`, and a `doctor` stress-timing row. Ruled 2026-10-04 by delegation: the linter decides the ingest (the only option that is the same on every machine), the doctor row carries the clock; the `regex` dependency is the reopen trigger."
status: ruled 2026-10-04 by delegation (W-251 §4, B-260) — (a) + (e); built 2026-10-04 (W-255, SR-PII decision 23)
timestamp: 2026-10-04T00:00:00Z
filed: 2026-10-04
---

# The PII regex bound

> **Verdict: RULED 2026-10-04 (by delegation, W-251 §4) — (a) + (e).**
> **(a)** A **static linter at load**, stdlib only (`re._parser`'s AST): a rule
> whose pattern has an unbounded repeat (`*`, `+`, `{n,}`) containing another
> unbounded or variable repeat — `(a+)+`, `(a|aa)*`, `(\w*\s?)*` — or a
> backreference inside an unbounded repeat, is **refused at load**, naming the
> rule and the fix (possessive `*+`, atomic `(?>…)`, Python ≥ 3.11 and so inside
> L7). It is a predicate on the pattern string, so it gives the same answer on
> every machine — the only option here allowed to decide an ingest (L4).
> **(e)** A **`doctor` stress-timing row**: each rule over fixed adversarial
> strings, warn above `fux.toml [doctor] pii_rule_budget_ms`. Wall-clock is
> legal there because doctor output is never a committed byte; it covers the
> polynomial class the linter cannot see. **Confidence: high on the split
> (deterministic decides, advisory times), medium on the linter's exact rule set
> (conservative by design — a safe nested quantifier is refused with the fix
> named).** **Reopen-trigger:** (e) shows a real consumer rule hanging a real
> ingest that (a) admitted — then option (d), the `regex` dependency, goes to a
> record as fux's first runtime dependency.

**Model: Sonnet** — W-255.

## Context

[SR-PII](../../records/0148_pii.md) Consequences, *Owed*: *"A pathological regex
can hang an ingest. Python's `re` has no timeout. Patterns that match the empty
string are refused and `doctor` compiles the rest; beyond that a consumer's
regex is a consumer's regex."* The module docstring (`ingest/pii.py:74–78`)
repeats it. The record said the bound was *"Owed, and filed in OPEN-WORK"*; it
never was — backlog row B-232 was its only home (W-251 §1), now B-260 → W-255.

What runs today: rules compile at load (`pii.py:252–258 _compile`; the
empty-match refusal at `:372`; a group bound at `:378`), then **one `rx.sub`
per rule per whole document body** (`:226–249 Rule.apply`, `:424–442 redact`),
called from `ingest/run.py` for the body, the frontmatter title, the locator and
the enrichment body. Allowed flags: `ignorecase|multiline|dotall|verbose`.
`doctor._pii_health` loads the rules — which compiles them — and nothing more.
`pyproject.toml`: `dependencies = []` — **fux has no runtime dependency**.
Redaction is Python-only; no Node twin is affected.

The constraint that decides the fork is L4, not cost: redaction writes
**committed bytes**. Any mechanism whose outcome depends on how fast the machine
is makes the committed index a function of the CPU — the determinism failure the
differential harness exists to catch and cannot see on one machine.

## Options

- **(a) Static linter at load.** Walk the pattern's `re._parser` AST; refuse the
  classic ReDoS shapes (nested unbounded repeats; a backreference inside one).
  A property of the string. Does not see polynomial blow-up.
- **(b) Wall-clock timeout** in the engine (worker thread or process). As a
  *skip*, committed bytes depend on CPU speed; as a *hard stop*, bytes stay clean
  but success is machine-dependent. **Also infeasible as a thread:** `_sre`
  holds the GIL for the whole match, so a watchdog thread cannot interrupt;
  `signal.alarm` is POSIX-only (the Windows-first litmus, SR-MAINTENANCE 1d);
  a subprocess per rule × document is ~10k × N processes.
- **(c) Deterministic span bound** — redact per line or fixed window, cap the
  span. Deterministic and portable, but `(a+)+$` hangs on 40 characters, and
  `dotall` / `multiline` / `\n`-spanning patterns are allowed today, so windows
  change what a rule matches. Lossy.
- **(d) The `regex` module with `timeout=`.** The only full solution. It is
  (b)'s clock in a C extension — a hard stop whose success is machine-dependent
  — plus fux's **first runtime dependency** (L2 permits an OSI licence; a record
  must still name it), a C build on the install path, and V0/V1 semantic drift
  from `re`.
- **(e) `doctor` stress-timing.** Each rule over fixed strings (`"a"*N`,
  `"1"*N`, a long `@`-less prose line), `perf_counter`, warn above a budget.
  Advisory, not in the write path. The shipped email rule
  (`templates/pii.toml.txt:88`, `[A-Za-z0-9._%+-]+@…`) is quadratic on a long
  `@`-less run — (e) shows that; (a) does not.

## Matrix

| | (a) linter | (b) wall-clock | (c) span bound | (d) `regex` + timeout | (e) doctor timing |
|---|---|---|---|---|---|
| keeps L4 (same committed bytes on every machine) | **yes** | **no** (skip) / success machine-dependent (stop) | yes | success machine-dependent | yes — never a committed byte |
| keeps L2 / zero runtime dependencies | yes | yes | yes | **no** — first dependency | yes |
| portable (Windows-first) | yes | no (`signal`) / no (GIL) | yes | yes | yes |
| stops the exponential class | **yes** | yes | **no** | yes | advisory |
| stops the polynomial class | no | yes | partly | yes | **shows it** |
| changes what a rule matches | no | no | **yes** | V0/V1 drift | no |
| size | S | L, and wrong | M, lossy | M + a dependency decision | S |

## Consequences of (a) + (e)

- `ingest/pii.py` gains `_lint`; `doctor` gains a `pii timing` row; the
  starter `pii.toml` and this repository's must pass the linter.
- L12: stress-string lengths are fixed values in `constants.toml [pii]`; the
  budget is a tunable in `fux.toml [doctor]`.
- A grep guard in the shape of the L5 import fence asserts **no wall-clock on
  any ingest path** — the row that would otherwise regress silently.
- SR-PII gains a decision and loses the *Owed* paragraph; SR-DOCTOR's check
  table gains a row; SR-CONFIG gains the key. B-260 leaves the backlog.

## References

- SR-PII Consequences, d12a, d17 · SR-DOCTOR · SR-MAINTENANCE 1d (the
  Windows-first litmus) · [L2](../../records/0004_LAW-2-zero-cost.md) ·
  [L4](../../records/0006_LAW-4-deterministic.md) ·
  [L12](../../records/0014_LAW-12-values-live-in-config.md).
- `src/fux/ingest/pii.py`, `src/fux/doctor.py::_pii_health`,
  `src/fux/templates/pii.toml.txt`.
- W-251 §4 (B-260); W-255.

## Reopen-trigger

(e) warns on a real consumer's rule **and** that rule has hung or dominated a
real ingest the linter admitted — then (d) is put to a record as the first
runtime dependency, with the clock's determinism cost stated. Or: Python's `re`
gains a timeout (then (d)'s cost vanishes and the question is only L4's).
