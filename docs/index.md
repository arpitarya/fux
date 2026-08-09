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
* [Component diagram](architecture-components.svg) - the v2 map · [high-level flow](architecture-index-and-refer.svg).
* [Model handoff interview](INTERVIEW.md) - succession judgment; read before substantive changes.
* [Worklog](WORKLOG.md) - per-exchange session trail, newest first.
* [Doc registry](DOC-REGISTRY.md) - maintained docs, update triggers, last-verified dates.
* [Glossary](GLOSSARY.md) - recurring terms, defined once.

# Decisions

* [Compare docs](compare/) - six v0.30 forks, verdict at the top of each; one still ⏳ (ingest-mode naming).
* [Proposals](proposals/) - parked ideas with graduation triggers (3 new for v0.30 + 3 carried).
* [ADRs](adr/) - numbering continues from 0016; 0001–0015 are archived with the v0.26 engine.
  * [ADR-0016](adr/0016-ingest-mode-naming.md) - ingest-mode naming (`inferred`/`enriched`); ⏳ proposed, awaiting ratification.
  * **[ADR-0017](adr/0017-pruning-eval-gate.md) - P1, the pruning gate: INCONCLUSIVE. Read before starting any milestone.**

# Build

* [Handoffs](handoff/) - live build specs: the [M0/M1 pair](handoff/v0.30.0-m0-m1-gate-handoff.md) + the [CLAUDE.md review diff](handoff/v0.30.0-claude-md.diff).
* [Conformance](conformance/README.md) - measurement evidence home (persists across rebuilds); latest: [the pruning eval](conformance/2026-08-09-pruning-eval/ANALYSIS.md).
* [`tools/pruning-eval/`](../tools/pruning-eval/README.md) - M1's gate: the frozen [pre-registration](../tools/pruning-eval/PRE-REGISTRATION.md), the KL selector, the harness.
* [Archive](archive/) - implemented v0.26-era artifacts · [v0.26 docs](../archive/v0.26/archive/v0.26-docs/) (ADRs 0001–0015, compare, example, tracker) · [old plan](../archive/v0.26/archive/PLAN-v0.26.md).
* Engine archive: [`../archive/v0.26/`](../archive/v0.26/) - the full prior build, reference-only, runnable for M1's baseline.
