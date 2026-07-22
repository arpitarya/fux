---
okf_version: "0.1"
---

# Fux docs — knowledge bundle root

The `docs/` tree is an OKF v0.1 bundle: every lowercase knowledge doc carries
frontmatter with a `type`; this index gives progressive disclosure. (Repo-root
`CLAUDE.md`/`README.md` and ALL-CAPS docs — `PLAN.md`, `INTERVIEW.md`, `WORKLOG.md`,
`IMPLEMENTATION.md`, `GLOSSARY.md`, `DOC-REGISTRY.md`, and everything under
`example/` (`CLI.md`, `TOML.md`, `SETUP.md`, `SKILLS.md`, `API.md`) — are
entry-point/tracker files, exempt from the `type` requirement by repo
convention.)

# Core (read in this order)

* [Design of record](PLAN.md) - scope, decisions, status, build queue.
* [Model handoff interview](INTERVIEW.md) - succession judgment; read before substantive changes.
* [Worklog](WORKLOG.md) - per-exchange session trail, newest first.
* [Implementation tracker](IMPLEMENTATION.md) - live milestone status; updated on EVERY execution, whatever the outcome.
* [Doc registry](DOC-REGISTRY.md) - maintained docs, update triggers, last-verified dates.
* [Examples bundle](example/) - copy-from contracts: [CLI.md](example/CLI.md) (command I/O; goldens derive from it), [TOML.md](example/TOML.md) (annotated config), [SETUP.md](example/SETUP.md) (setup variants + hooks install), [SKILLS.md](example/SKILLS.md) (skill usage), [API.md](example/API.md) (drive the engine from a script).
* [Glossary](GLOSSARY.md) - every recurring term, defined once, linked to its owning doc.

# Decisions

* [Compare docs](compare/) - every fork's debate + accepted verdict + reopen-trigger (all closed).
* [Proposals](proposals/) - parked ideas with graduation triggers.
* [ADRs](adr/) - one per completed feature (0001–0004: config/setup, ingest+cache+chunker, BM25F+query, agent integration).

# Build

* [Handoffs](handoff/) - live build specs (empty — all three phases implemented; next plan starts here).
* [Archive](archive/) - implemented artifacts, version-named: master-prompt + v0.20.0 (v1) + v0.21.0 (v1.1) + v0.22.0 (v2) + v0.23.0 (substrate), each stamped with its ADRs.
* [Eval harness](../tests_e2e/eval/README.md) - the retrieval quality gate + Anton private-eval workflow.
* [Distillation recipe](../tools/distill/README.md) - how the bundled model is built (dev-only).
