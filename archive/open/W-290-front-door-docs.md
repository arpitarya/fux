---
type: Handoff
name: W-290
description: "Arpit, 2026-10-20: the front-door docs — a consumer- and marketing-grade README, plus CONTRIBUTING, SECURITY, CODE_OF_CONDUCT and the GitHub templates."
item: W-290
filed: 2026-10-20
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-20
updated_by: "Claude Code (Opus 5.5)"
ball: done
---

# W-290 — The front-door docs: README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, templates

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Run the README's quickstart on the published `fux-engine` 4.1.0 in a clean container | every output block in the README is real | ✅ 2026-10-20 |
| 2 | Rewrite the README: plain-words section, real stale-answer demo, is-it-for-you, roadmap from the queue, FAQ | a page a consumer can adopt from, and that sells honestly | ✅ 2026-10-20 |
| 3 | Write `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` | a repo strangers can contribute to and report to | ✅ 2026-10-20 |
| 4 | Arpit unzips the four issue templates and the PR template into `.github/` | structured wrong-answer reports | ✅ 2026-10-20 — written by Claude Code (the zip never reached the repo) |

**Arpit, 2026-10-20 (Cowork):** *"i like the files that got created for codelaw add/create/update similar kind of file for sheetpane and fux"*

**Model:** Opus — public copy whose accuracy against the published package is the deliverable.

## Goal

The repo's front door states what installs today, proves it with real output, and says what is next.

## Definition of done

- Every command and output in the README was run against `fux-engine` 4.1.0 from PyPI (and `npx fux-engine@4.1.0`).
- The README says what PyPI and npm serve (4.1.0), not what the tree is versioned at (4.1.1, cut and not released).
- W-289's plugin packages are described as the next release, not as current behaviour.
- `.github/ISSUE_TEMPLATE/{bug_report,wrong_answer,feature_request,config}.yml` and `.github/PULL_REQUEST_TEMPLATE.md` are in the repo.

## Blockers

None. Step 4's files were written by Claude Code on 2026-10-20; Cowork's zip was never unpacked.

## Record affected

SR-WORK-REGISTRY §3 (rows for the three new docs; README, CHANGELOG and CLAUDE.md bumped). No other SR affected.

## Hazards

- The README's "4.1.0 is the latest release" and its plugin-packages note go stale at the next release; the README's registry row names that trigger.
- The SECURITY and wrong-answer links point at templates that 404 to a blank issue until step 4 lands.

## Reference

- [`README.md`](../../README.md) · [`CONTRIBUTING.md`](../../CONTRIBUTING.md) · [`SECURITY.md`](../../SECURITY.md) · [`CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md)
