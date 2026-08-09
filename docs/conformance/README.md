# Conformance runs — the measurement evidence index

*Every measurement run against a real or synthetic corpus is filed here:
the run's own report, an `ANALYSIS.md` that turns the numbers into specific
decisions, and the raw evidence under `evidence/`. Binding, per CLAUDE.md —
engine changes are made from measured data, not from memory.*

**The measurement environment is scratch; this directory is not.**
`~/my_programs/fux-lab/` holds one directory per corpus (its own venv, corpus,
baselines) and commits nothing. What survives a run is what lands here.

**This directory persists across rebuilds.** The v0.19–0.26 runs are evidence
about an engine that is now archived, but the *corpora*, the eval pairs and the
measured baselines they establish are still the instrument v0.30 is measured
against — M1's gate reuses acme and orbit directly.

## Per-run contract

| # | artifact | what it must contain |
|---|---|---|
| 1 | `<date>-<run>/` | one directory per run, dated |
| 2 | `report.md` | the run's own output, unedited (corrections noted, not silently applied) |
| 3 | `ANALYSIS.md` | the diagnosis → **specific** changes, each with a repro command; unresolved causes stated as unresolved |
| 4 | `evidence/` | the primary data the analysis rests on |
| 5 | a row below | plus a DOC-REGISTRY bump, same change |

**The reproduce command must actually reproduce.** A run whose numbers cannot
be regenerated is an anecdote.

## Runs

| date | run | corpus | what it established |
|---|---|---|---|
| 2026-08-09 | [`2026-08-09-pruning-rerun`](2026-08-09-pruning-rerun/) | **rfc** (8 872 docs) · repodocs | **P1 re-run → FAIL.** 5 selectors at matched retention, gated on recall@20: best arm 35.9 pts below unpruned at 6 % retention. [ADR-0018](../adr/0018-pruning-criterion-rerun.md) |
| 2026-08-09 | [`2026-08-09-pruning-eval`](2026-08-09-pruning-eval/) | acme · orbit · synth-100k | **M1, the P1 gate → INCONCLUSIVE.** The corpora's documents were too short for top-128 to prune anything. [ADR-0017](../adr/0017-pruning-eval-gate.md) |

### Archived runs (v0.19–0.26 engine)

Filed under [archived with the engine](../archive/README.md) with the engine they
measured, and kept runnable in [`../../archive/v0.26/conformance/`](../../archive/v0.26/conformance/):

| date | run | what it established |
|---|---|---|
| 2026-07-22 | acme-payments | the discriminating corpus; staleness inversions surfaced |
| 2026-07-22 | scaling 1k/5k/10k | hybrid-vs-lexical gap is not stable with scale; query latency linear |
| 2026-07-23 | min-confidence calibration | **no threshold separates answerable from unanswerable** → ADR-0014 ships the floor disabled |
| 2026-07-23 | supersession recovery | frontmatter supersession is reachable; ranking was not yet affected |
| 2026-07-24 | orbit-fulfillment | second corpus; generalised the supersession finding (8/12 inversions) |
| 2026-07-24 | fusion lexical hit loss | non-monotone RRF fusion isolated and scoped |
| 2026-07-24 | supersession penalty calibration | safe interval `[11, ∞)`; default 15 → ADR-0015 |
| 2026-07-24 | v0.26.0 release verification | black-box verification of the published wheel |

**Lexical baselines these runs established**, reused by M1 as a correctness
check on any new harness: fixture `hit@5 0.952 / MRR 0.833` · orbit
`hit@5 0.887` (n=53, lexical-only).
