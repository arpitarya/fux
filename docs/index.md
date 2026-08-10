---
okf_version: "0.1"
---

# Fux docs — knowledge bundle root (v0.30 rebuild)

The `docs/` tree is an OKF v0.1 bundle: every lowercase knowledge doc
carries frontmatter with a `type`; this index gives progressive disclosure.
ALL-CAPS docs (`PLAN.md`, `OPEN-WORK.md`, `INTERVIEW.md`, `WORKLOG.md`,
`GLOSSARY.md`, `DOC-REGISTRY.md`) plus repo-root `CLAUDE.md`/`README.md`
are entry-point/tracker files, exempt from the `type` requirement by repo
convention. Large docs carry two sections — *For humans* then *For AI
agents* — update both or neither.

# Core (read in this order)

* [Plan](PLAN.md) - the v0.30 build: milestones M0–M8, gates, port list.
* [Open work](OPEN-WORK.md) - everything not yet built: human summary + agent work ledger + prediction status. **The live tracker.**
* [The paper](paper/the-fux-index-paper.md) - the architecture of record, with figures and falsifiable predictions P1–P7.
* [Overview diagram](architecture-overview.svg) - five components, one glance · [detailed diagram](architecture.svg) - tiers, record shapes, query path. Rev-1 diagrams archived.
* [Model handoff interview](INTERVIEW.md) - succession judgment; read before substantive changes.
* [Worklog](WORKLOG.md) - per-exchange session trail, newest first.
* [Doc registry](DOC-REGISTRY.md) - maintained docs, update triggers, last-verified dates.
* [Glossary](GLOSSARY.md) - recurring terms, defined once.

# Decisions

* [Compare docs](compare/) - six v0.30 forks, verdict at the top of each; one still ⏳ (ingest-mode naming).
* [Proposals](proposals/) - parked ideas with graduation triggers (3 new for v0.30 + 3 carried).
* [ADRs](adr/) - **numbered from 0001 for the v0.30 line** ([policy](adr/README.md)); "archived ADR-NNNN" always means the v0.26 set under archive.
  * [ADR-0001](adr/0001-ingest-mode-naming.md) - ingest-mode naming (`extracted`/`enriched`); ⏳ proposed, awaiting ratification.
  * [ADR-0002](adr/0002-pruning-eval-gate.md) - P1 first run: INCONCLUSIVE (the correct refusal).
  * **[ADR-0003](adr/0003-pruning-criterion-rerun.md) - P1 re-run: FAIL → option E, full postings. The decision the whole build now rests on.**

# Build

* [Handoffs](handoff/) - live build specs: the [M0/M1 pair](../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-handoff.md) + the [CLAUDE.md review diff](handoff/v0.30.0-claude-md.diff).
* [Conformance](conformance/README.md) - measurement evidence home (persists across rebuilds); latest: [the pruning eval](conformance/2026-08-09-pruning-eval/ANALYSIS.md).
* [`tools/pruning-eval/`](../tools/pruning-eval/README.md) - M1's gate: the frozen [pre-registration](../tools/pruning-eval/PRE-REGISTRATION.md), the KL selector, the harness.
* [Archive](../archive/) - **everything archived lives in the root archive** (Arpit's ruling, 2026-08-10): [v0.1](../archive/v0.1/) · [v0.26 engine](../archive/v0.26/) · [v0.26 docs](../archive/v0.26-docs/) · [v0.26 implemented artifacts](../archive/v0.26-implemented/) · [v0.30 rev-1 planning](../archive/v0.30-rev1-planning/).
* Engine archive: [`../archive/v0.26/`](../archive/v0.26/) - the full prior build, reference-only, runnable for M1's baseline.
