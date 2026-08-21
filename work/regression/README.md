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
| 2026-08-21 | [`2026-08-21-source-verbs`](2026-08-21-source-verbs/report.md) | **4 synthetic documents + 1 URL** behind a local fake fetcher, no network | **A surface capture, not a gate** — the W-63 verbs `fux add`/`remove`/`update`, verbatim, grounding [ADR-CLI](../../docs/adr/0002_cli-surface.md) decisions 1a–1e. Shows both remove-by-coverage branches, the scoped URL fetch and its stderr announcement, and **a URL leaving the index on an offline run** — W-63 defect 1, where deletion used to require the network. **Writing the transcript down found four defects the unit tests did not**, three of them in the change being captured: an L4 announcement that fired against an empty URL list; `add '*.pdf' --types` silently un-indexing every markdown document (W-55's invisible filter, from a new direction); a type-allowlist skip reported as a failed fetch; and `explain` answering for a document not in the corpus. All four fixed in the same change — see [ANALYSIS.md](2026-08-21-source-verbs/ANALYSIS.md) |
| 2026-08-21 | [`2026-08-21-progress-plane`](2026-08-21-progress-plane/report.md) | **synthetic 1 203 documents**, local, no network | **A surface capture, not a gate** — the W-64 progress bar on `fux ingest`/`fux build`, verbatim, grounding [ADR-CLI](../../docs/adr/0002_cli-surface.md) decision 9. **stdout is byte-identical with the bar on or off** for both write verbs (the invariant; now asserted per-verb in `tests_e2e/test_progress_surface.py`), and nothing paints when stderr is not a TTY, so every existing captured transcript reproduces unchanged. Found and fixed in the run: a phase whose total is not documents must name its unit, or `write`'s `252/252` under `edges`' `1203/1203` reads as loss. **Says nothing about 100k** — the repaint cost at R5's size is [W-26](../open/W-26-m6-scale-t2.md)'s to measure |
| 2026-08-21 | [`2026-08-21-graph-plane-profile`](2026-08-21-graph-plane-profile/report.md) | **synthetic 10k · 50k · 100k**, cloud container, not `fux-lab` | **A cost profile, not a gate** — loading `.fux/runtime/graph.json` is **9.34 s of a 9.54 s `fux graph`** at 100 000 docs (98 %); the PPR/`path` algorithms themselves are 0.197 s and sub-ms respectively. Two measured alternative layouts: node-major+seekable cuts query cost to 0.45 s but not build cost; communities-only (drop the edges already committed in `.fux/index/`) cuts build 5.57 s → 3.96 s. Feeds [`graph-plane-format.compare.md`](../compare/graph-plane-format.compare.md). Caveats: synthetic edge density unmeasured on a real corpus; not run in `fux-lab` |
| 2026-08-21 | [`2026-08-21-r7-preliminary-analysis`](2026-08-21-r7-preliminary-analysis/report.md) | **this repo's own committed index**, 345 real documents — no synthetic corpus, no fux-lab environment | **Not a verdict — no pre-registration exists.** R7 closed on Arpit's call rather than run the full pre-registered bench: real git-pack compression on the committed index measures **2.429×**, extrapolating to **~470 MB at 100k docs, ~2× over the 250 MB budget**. The shortfall was measured against today's plain-JSON placeholder format, not [ADR-POSTINGS](../../docs/adr/0013_postings.md)'s designed BIC/MPH encoding (⏳ proposed, unbuilt) the threshold was sized for — so this does **not** read as the "wire format is dead" FAIL a measured result would trigger; it motivates building the compact encoding rather than condemning the architecture |
| 2026-08-20 | [`2026-08-20-r5-hook-latency`](2026-08-20-r5-hook-latency/report.md) | **synthetic 1k · 10k · 100k**, throwaway git repos wired with `fux hooks` | **R5 FAIL** ([R5-HOOK](2026-08-20-r5-hook-latency/VERDICT.md)) — **44.4 s at the judged 100 000 documents against a 1 s bound**, 3.52 s at 10 000, and **0.651 s at 1 000, where it passes**. Cost tracks the corpus, not the commit. The attribution is the decisive part: **git is ~constant** (0.34 s at 100k) and two O(corpus) passes are the whole cost, split 51.5 % ingest / 47.6 % derive — so **a 10× speedup still misses the bound by 4.5×**, and only taking the work off the commit path reaches it. Fires [ADR-MAINTENANCE](../../docs/adr/0033_hooks.md) veto 1; the fork goes to Arpit as [`hook-at-scale.compare.md`](../compare/hook-at-scale.compare.md) |
| 2026-08-20 | [`2026-08-20-r6-merge-driver`](2026-08-20-r6-merge-driver/report.md) | the same harness, 100-doc repos | **R6 INCONCLUSIVE** ([R6-MERGE](2026-08-20-r6-merge-driver/VERDICT.md)) — **every tier matched its expected outcome**, and tiers 2 and 3 are informative against a control arm run with the driver unregistered: adjacency does not conflict, and a same-`ver` disagreement is **refused with both sides left in the file**. **Tier 1 merged cleanly without the driver too**, so it proves nothing — the control arm justified itself on its first run — and the frozen table does not cover "all match, some informative". A post-hoc tier 1b (adds selected by hashing into one shard) shows the mechanism does cover concurrent adds. The engine is not the reason for the verdict; the pre-registration's own arithmetic is |
| 2026-08-20 | [`2026-08-20-refer-plane-r4`](2026-08-20-refer-plane-r4/report.md) | **10 HTML documents on a mock server**, reached through the shipped consumer fetcher | **R4 PASS** — cold k=10 p95 **1.113 s** against a 3 s bound, warm p95 **0.016 s** against 300 ms, on the pre-registered 100 ms arm ([R4-REFER](2026-08-20-refer-plane-r4/VERDICT.md)). **Cold latency is the source's latency ten times over**: the plane fetches serially, paper §8's "(k=10, parallel)" is not built, and the 500 ms arm exceeds the bound at 5.069 s — so R4 holds for sources answering under ~295 ms and not beyond. The warm bound tested less than it appears to: with both caches warm there is no network, and the pre-registration said so before the run. ARC-vs-LRU measured and reported **post-hoc** — the metric was changed after seeing a number it then reversed — so `cache-policy.compare.md`'s trigger stays open |
| 2026-08-20 | [`2026-08-20-ingest-cost-profile`](2026-08-20-ingest-cost-profile/report.md) | **synthetic 1k + 5k**, no network | **A cost measurement, not a gate** — **92 % of a full ingest is `_fuxvec_code`**, the dense embedding, at both sizes. Carrying unchanged documents' extraction forward is **22.7× / 26.4×** faster and **byte-identical**. This is the evidence [ADR-INGEST](../../docs/adr/0007_ingest.md)'s veto condition required before decision 1 could be reopened; decision **1b** and `fux ingest --full` land with it. **Explicitly not R5** — prediction runs are held ([W-61](../open/W-61-maintenance-measurement.md)) |
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
