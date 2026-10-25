---
type: Handoff
name: W-293
description: "Arpit's ask (2026-10-21, Cowork): take what codelaw does better into fux — built the same session (inbox-hook fix, decider from git, law gate, withdrawal script, install smoke, wheel cache, lean CLAUDE.md, one SR guard). What is left is proof on a real runner: the wheel cache restores on a push that changes no wheel input, and the law gate and smoke go green in ci.yml's build job."
item: W-293
filed: 2026-10-21
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Claude Code (Opus 5.5), step 7 read"
ball: agent
---

# W-293 — the first CI run of the codelaw ports

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Fix the inbox hook (`*Empty since`), name the decider from `git config` | an empty inbox is never announced; hooks portable | ✅ 2026-10-21 |
| 2 | `scripts/law-gate.py` in ci.yml and publish.yml | no release ships past a law (L2, L7, L8, L10, completeness) | ✅ built, green locally |
| 3 | `scripts/smoke.py` in ci.yml | PyPI install (no Node) and npm install (no Python) answer alike | ✅ built, green locally |
| 4 | `scripts/withdraw.sh` | a half-published release is withdrawn whole | ✅ built; `--report` run against 4.1.0 |
| 5 | Wheel cache keyed by `ci-key.py wheels` | a docs-only push skips the ~90 s wheel build | ✅ built |
| 6 | Lean `CLAUDE.md` (one line per law, L11 whole); history trimmed; one SR guard | 42 KB → 33 KB read by every session; the hook and CI cannot disagree | ✅ |
| 6a | 🟢 **Claude Code** (on Arpit's Mac) merges the law-gate, smoke and wheel-cache steps into the **current** `ci.yml` and `publish.yml` — never the 2026-10-21 chat copies, which predate W-292's `.mjs` wheel check (2026-10-24) — and runs both suites. Ruled 2026-10-25 (below) | the wiring lands: ci.yml's build job restores/saves `wheels/` under `ci-key.py wheels` (push only), then bundles both npm names, runs the law gate (✔ locally, 19 wheels · 1 sdist · 2 npm, 5.0.0) and the smoke; publish.yml runs the gate. The smoke got `commit.gpgsign false` for its fixture. ⚠ The smoke could not run on Arpit's Mac (ensurepip SIGABRTs in any fresh venv there) — step 7 is its first run | ✅ 2026-10-25 (Claude Code) |
| 7 | **First push to `main`: read the build job** — law gate ✔, smoke ✔; a second push touching only `work/` shows "wheels restored" | the ports proven on a runner, not only in a container | ✅ 2026-10-25 (Claude Code): run 40192043910 (`main`, 6aae2ae1) — wheel cache miss then saved, `✔ law-gate: 19 wheels, 1 sdist, 2 npm package(s)`, `✔ smoke: 5 calls`; run 40193299244 (tag `v5.0.0`, same tree) — `✔ wheels restored for ci-wheels-v1-bfe7b1e7…`, gate ✔, smoke ✔. The three unpushed work-only commits key to the same `bfe7b1e7…` (`ci-key.py wheels`), so their push restores by construction |

**Arpit, 2026-10-21 (Cowork):** *"look into code law. Is there something that can be taken from it?"* → *"Implement text and design change in Fox. Implement release safety. Implement fix now tiny."* → *"additionally implement CI wheel cache keyed by a hash of the inputs"*.

**Arpit, 2026-10-25 (Cowork docket):** *"A · Claude Code merges (Recommended)"* —
step 6a moves from his hands to Claude Code. Why: the 2026-10-21 chat copies
predate W-292's edits to both workflow files (2026-10-24), so pasting them would
delete the no-`.mjs`-in-a-wheel check; and Claude Code on his Mac has committed to
`.github/workflows/` before (W-289, W-292) — only the Cowork bridge may not.
Arpit still pushes; step 7 then reads the run.

**Model:** Claude Code, **Sonnet**: read two CI logs; fix only what they show.

## What step 7 checks

- `build · node units · ladder` prints `✔ law-gate: 19 wheels, 1 sdist, 2 npm package(s)` and `✔ smoke: 5 calls`.
- On the next push whose diff is only under `work/`, `docs/` or `records/` (not `records/README.md`), the build step prints `✔ wheels restored for ci-wheels-v1-…`.
- If smoke fails on the runner for PATH reasons (a `git` or `node` the symlink cannot see), fix the smoke, not the gate.

## Where it is decided

[SR-WORK-RELEASE](../../records/0063_WORK-release.md) decisions 17–20 · [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) decision 2a · [SR-WORK-BLOCKERS](../../records/0064_WORK-blockers.md) decision 9a · [SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 5.
