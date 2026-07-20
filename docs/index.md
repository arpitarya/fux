---
okf_version: "0.1"
---

# Fux docs — knowledge bundle root

The `docs/` tree is an OKF v0.1 bundle: every knowledge doc carries frontmatter with
a `type`; this index gives progressive disclosure. (Repo-root `CLAUDE.md` and
`README.md` sit outside the bundle — they are tool/user entry points, not concepts.)

# Core (read in this order)

* [Design of record](fux-plan.md) - scope, decisions, status, build queue.
* [Model handoff interview](model-handoff-interview.md) - succession judgment; read before substantive changes.
* [Worklog](worklog.md) - per-exchange session trail, newest first.
* [Implementation tracker](implementation.md) - live milestone status of the build; agent-updated continuously.
* [Doc registry](DOC-REGISTRY.md) - maintained docs, update triggers, last-verified dates.

# Decisions

* [Compare docs](compare/) - every fork's debate + accepted verdict + reopen-trigger (all closed).
* [Proposals](proposals/) - parked ideas with graduation triggers.
* [ADRs](adr/) - one per completed feature (arrive with the v1 build).

# Build

* [Handoffs](handoff/) - specs + paste-ready prompts: 0000 master, 0001 v1, 0002 v1.1, 0003 v2.
* [Archive](archive/) - implemented artifacts land here.
