# `tools/quality/` — the quality contract, frozen

**One file today: [`mix.toml`](mix.toml).** It carries the two declarations a
fux quality number is meaningless without — **which queries are scored**, and
**what an error costs**.

- **Owner:** [ADR-QUALITY](../../docs/adr/0141_quality-contract.md).
- **Discipline:** the same as a pre-registration
  ([`tools/pruning-eval/PRE-REGISTRATION.md`](../pruning-eval/PRE-REGISTRATION.md)
  is the worked example) — written before the number, never edited after it.

## Why it is committed before anything reads it

**`[cost]` is only honest if it predates the first score.** Weights set after a
score is seen are tuning, not a claim, and a metric chosen to flatter is
undetectable afterwards. Committing the file with nothing reading it is the
point, not an oversight.

## The two blocks are frozen differently, and that is deliberate

| block | kind | may it change? |
|---|---|---|
| `[cost]` | a **commitment** | **No.** Changing it after a filed score voids ADR-QUALITY decision 6 — veto condition 3 |
| `[mix]` | a **declared prior** | Yes, by **bumping `version`**. Never by a silent edit |

## What is not here yet

- **`recall@k` is not computed.** It needs known-relevant sets per query. The
  annotation exists (κ = 0.960) but the fifty goldens it was made over were
  retired with `fux-playground` by
  [L9](../../docs/adr/0011_LAW-9-environments.md) on 2026-09-11, and the golden
  ladder's questions carry no relevance claim — so **there is no set to compute
  it over at all** (W-87 phase P2).
- ⚠ **`mix.toml`'s WARNING comment is superseded, and the file is not edited to
  say so.** It reads *"the 50 playground goldens are not labelled by class
  yet"*; those goldens are retired. `mix.toml` is frozen the way a
  pre-registration is frozen, so the correction lives here.
- **The `unanswerable` class does not exist**, and must be authored **blind**.
- **No harness reads this file.** The first consumer is the run that files the
  first verdict under `mix@1`.

## Reference

- [ADR-QUALITY](../../docs/adr/0141_quality-contract.md) — the contract
- [`work/compare/what-good-means.compare.md`](../../work/compare/what-good-means.compare.md)
  — the research behind it
- [`work/open/W-87-what-good-means.md`](../../work/open/W-87-what-good-means.md)
  — the remaining phases
