# `work/regression/` — the measurement evidence store

**How to use this directory.** This is what other docs **point at** when they
need grounding. An ADR's reference, a status claim, a verdict in `compare/` —
all of them may cite a run here, and none of them may cite an archived doc
instead. A run filed here is the only kind of evidence that stays valid.

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
| 5 | `VERDICT.md` | **only when the run rules on a pre-registered threshold** — the ruling, its verdict, and the frozen pre-registration it was ruled against |
| 6 | a row below | plus a DOC-REGISTRY bump, same change |

**The reproduce command must actually reproduce.** A run whose numbers cannot
be regenerated is an anecdote.

**A verdict is cited, never replaced.** When a run adjudicates a
pre-registered prediction, that ruling is a `VERDICT.md` beside its evidence —
`type: Verdict`, with the prediction id and the pre-registration path in its
frontmatter. It is deliberately **not** an ADR: an ADR records a decision
someone can later supersede, and nothing supersedes a measurement except a
better measurement, which is a new run with its own verdict. The two P1
verdicts were ADRs until 2026-08-18 and were converted for exactly this reason.
The *decisions* that rest on a verdict stay in `docs/adr/`, citing it.

**Not every entry is a measurement.** A *surface capture* — a verbatim record
of what a command prints — belongs here too, because other docs cite it as
grounding and it must be reproducible for that to mean anything. Say which it
is at the top of the report: a capture gates no prediction and pre-registers
no threshold, and calling it a measurement would be the kind of overclaim the
pre-registration discipline exists to stop.

## Runs

| date | run | corpus | what it established |
|---|---|---|---|
| 2026-08-19 | [`2026-08-19-w54`](2026-08-19-w54/report.md) | **2-doc fixture + 6 URLs**, built by `fux setup` from nothing, no network | **A surface capture, not a measurement** — the whole URL path, which this repo's own corpus never touches. Closes **W-47** (`meta = "hashed"` now ingests *and builds*, exit 0), **W-49** (a fragment survives; two fragment-differing URLs are two records), **W-51** (`fux setup` writes both fetchers from wheel package data) and **W-53** (one grammar, two lists). The differential holds over a corpus containing hashed records — **which the harness had never seen**, and is why W-47 survived. Behind ADR-URL-LIST · ADR-DIR-LIST · ADR-FETCHER · ADR-HTTP-FETCHER · ADR-INDEX-LIFECYCLE. Supersedes `2026-08-18-ingest-and-index`'s fixture, which reproduces the pre-W-54 surface and was not edited |
| 2026-08-18 | [`2026-08-18-query-verbs`](2026-08-18-query-verbs/report.md) | the same 5-record fixture | **A surface capture, not a measurement** — every flag of `ask`/`find`/`answer`, both output modes, the empty case, and the **differential law demonstrated byte-identical**. Behind ADR-ASK · ADR-FIND · ADR-ANSWER. Found three minor output-contract inconsistencies ([W-48](../open/W-48-query-output-contract.md)) |
| 2026-08-18 | [`2026-08-18-ingest-and-index`](2026-08-18-ingest-and-index/report.md) | **5-doc fixture + 3 URLs**, no network | **A surface capture, not a measurement** — the generated `.fux/` tree, a committed record, the runtime manifest, determinism/change/deletion, and the full URL-fetcher contract via a no-network stand-in. Behind ADR-DOTFUX · ADR-INGEST · ADR-URL-INGEST · ADR-INDEX-LIFECYCLE. Found **[W-47](../../archive/open/W-47-hashed-meta-blocks-accelerator.md)**: hashed meta, the default, makes the accelerator unbuildable — **closed 2026-08-19**, see the run above |
| 2026-08-18 | [`2026-08-18-cli-surface`](2026-08-18-cli-surface/report.md) | **3-doc fixture** (`evidence/fixture.sh`) | **A surface capture, not a measurement** — no prediction gated on it. Every `fux` command and its verbatim output, freezing the contract in [ADR-CLI](../../docs/adr/0002_cli-surface.md). Found one defect: `ask --hybrid` crashes on a source install ([W-46](../open/W-46-hybrid-missing-model-crash.md)) |
| 2026-08-12 | [`2026-08-12-m2-accelerator`](2026-08-12-m2-accelerator/report.md) | **rfc** (8 870 docs) · playground (50 goldens) | **R3 PASS** — worst-case p95 **27.2 ms** vs a 150 ms bar (scan: 4 248.8 ms). Differential law holds byte-for-byte over 5 536 comparisons + every golden. **Hybrid fusion measured net −6 and ships default-off.** [ADR-T1-ACCELERATOR](../../archive/adr/0005_derived-accelerator.md) |
| 2026-08-12 | [`2026-08-12-r2-close`](2026-08-12-r2-close/report.md) | **this repo** (119 docs) | **R2 → 3/3 PASS.** The third frozen question's citation became reachable by adding `archive/v0.26-docs` to configured sources; R1 re-asserted; index +45.1 %. Post-hoc: retired v0.26 docs now answer questions about the *current* engine ([W-44](../open/W-44-archived-content-signalling.md)) |
| 2026-08-09 | [`2026-08-09-pruning-rerun`](2026-08-09-pruning-rerun/) | **rfc** (8 872 docs) · repodocs | **P1 re-run → FAIL.** 5 selectors at matched retention, gated on recall@20: best arm 35.9 pts below unpruned at 6 % retention. [P1-RERUN](2026-08-09-pruning-rerun/VERDICT.md) |
| 2026-08-09 | [`2026-08-09-pruning-eval`](2026-08-09-pruning-eval/) | acme · orbit · synth-100k | **M1, the P1 gate → INCONCLUSIVE.** The corpora's documents were too short for top-128 to prune anything. [P1-GATE](2026-08-09-pruning-eval/VERDICT.md) |

### Archived runs (v0.19–0.26 engine)

Filed under [archived with the engine](../../archive/README.md) with the engine they
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


---

## Path note (2026-08-18)

This directory was `docs/conformance/`. **The run documents inside it were not
rewritten** — `report.md`, `ANALYSIS.md` and everything under `evidence/` are
frozen records and still carry pre-move paths (`docs/compare/`, `docs/adr/`,
`work/OPEN-WORK.md`) and pre-rename ADR numbers. Resolve them with the move map
in [`../../docs/adr/README.md`](../../docs/adr/README.md) §Path note.

A frozen document is never edited. That rule is what makes the numbers in it
trustworthy, and it costs a little navigation in exchange.
