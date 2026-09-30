---
type: Handoff
name: W-238
description: "Every fux verb that walks the corpus paints the W-64 progress bar (Arpit, 2026-09-29). Today only ingest, build, add, remove and inspect do; identifiers, enrich --check, and the graph/query verbs' index load are silent. Extend _PROGRESS_COMMANDS, thread progress= through, amend SR-CLI."
item: W-238
filed: 2026-09-29
ball: agent
---

# W-238 — a progress bar on every verb that takes time

**Status: BUILT 2026-09-29 (Claude Code, Opus); archived.** `identifiers`, `doctor` and `enrich --check` paint; the read verbs measured under a second and do not ([run](../../work/regression/2026-09-29-w238-verb-latency/report.md), [SR-CLI](../../records/0101_cli-surface.md) decision 17). SR-CLI had no list of barred verbs to amend — decision 17 is that list now. *Was:* ratified 2026-09-29, not built. Arpit, 2026-09-29: *"fux cli verbs
which are suppose to take time add progress bar so that end user knows
something is happening."*

**Model:** Claude Code, **Sonnet**. No new mechanism — the W-64 plane
(`src/fux/progress.py`) already exists; this threads it into more verbs.

## What exists

- `progress.py` (W-64, [archive](../../archive/open/W-64-progress-plane.md)):
  stderr only, TTY-gated, counts not clocks, `[cli] progress_threshold` in
  `.fux/output.toml`, `--progress` / `--no-progress`, `FUX_NO_PROGRESS`.
- `cli.py:173` `_PROGRESS_COMMANDS = ("ingest", "build", "add", "remove", "inspect")`.
- `serve` already records the same phases onto its page (`_JobProgress`, W-220).
- Node ships read verbs only (`answer ask find graph mcp`) — no Node change unless step 1 finds one slow.

## Silent today, and why they are candidates

| verb | what walks the corpus | evidence |
|---|---|---|
| `identifiers` | `read_index_view(root)` with no `progress=` — the same shard read `inspect` bars as `read` | `identifiers_cmd.py:71` |
| `enrich --check` | one ranked query per question per document (`self_retrieval_k`) | `enrich.py:293-298` |
| `enrich --plan` | walks every enrichable document | `enrich.py` |
| `explain` / `graph` / `path` | `graph/plane.py:79 load(root)` | to measure |
| `ask` / `find` / `answer` / `verify --rerun` | cold index load | to measure |
| `doctor` | per-record counts (`doctor.py:436`) | to measure |

## Definition of done

1. **Measure first, in `fux-lab` (L9), never `fux-playground`.** Run every verb
   above at `rung-10000` and record which ones are silent long enough to
   notice. A verb that is not slow gets **no** bar — a bar that flashes is noise.
2. For each verb that is slow: add it to `_PROGRESS_COMMANDS`, add
   `_add_progress_flags`, and thread `progress=` down to the loop (the
   `inspect` pattern: `progress or NULL`, `with progress.phase(name, total, unit)`).
3. One `Progress` per invocation — a verb with two phases shows them in sequence, never two bars.
4. W-64's four rules hold unchanged: stdout byte-identical with the bar on or
   off, `--json` untouched, off when stderr is not a TTY, no clock anywhere.
5. `[cli] progress_threshold` is read for every new verb (L12 — no default in
   code); add the verb's key to `node/src/config/output.mjs`'s map only if the
   config reader requires it there.
6. Amend **SR-CLI** (`records/0101_cli-surface.md`) — the list of barred verbs — in the same change.
7. Update the `fux-*` skills that name `--no-progress` for the verbs gained.

## Out of scope

- ETA, elapsed time, rate — W-64 rule 3 forbids them.
- A spinner for verbs with no known total (a single URL fetch). Counts only.
- `mcp`, `hooks`, `daemon`, `tune`, `output`, `setup` — no corpus walk.

## Tests

- Per new verb: stdout identical with `--progress` and `--no-progress`
  (the existing W-64 pattern in `tests/`).
- `--json` output byte-identical with the bar forced on.
- A below-threshold run paints nothing.
