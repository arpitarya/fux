---
type: Analysis
description: "Which verbs got a progress bar, how each was wired, and what the survey left open."
---

# W-238 — analysis

## Diagnosis

Three verbs spent seconds or minutes without printing anything. Each one has a
loop with a known total, so a count bar fits W-64's rules without a spinner.

- `identifiers` and `doctor` both run `inspect/idfamilies.identifier_families`:
  every indexed document is re-read and re-decoded, and then scanned for
  identifier candidates.
- `enrich --check` runs `_unretrievable`, one ranked query per question in
  every enrichment file.

## Changes, each with a repro command

1. **`cli._PROGRESS_COMMANDS`** gains `identifiers`, `doctor` and `enrich`.
   - Each verb takes `--progress` / `--no-progress`.
   - `identifiers` and `enrich` also gain `--no-output-config`
     (SR-OUTPUT decision 15).
   - `identifiers --json` now defaults to `None`, so `[cli.json]` can reach
     it (SR-OUTPUT decision 10).
2. **`[cli] progress_threshold`** is declared for `doctor`, `identifiers` and
   `enrich` in both readers' `CLI_VERBS`: `output_config.py` and
   `node/src/config/output.mjs`. It is the same table on both sides, so a
   committed `output.toml` validates the same way everywhere.
3. **The phases:**
   - `identifier_families(progress=)` opens `detect`, which counts every
     indexed document, readable or not.
   - `read_index_view(progress=)` already had `read` (from W-64/`inspect`).
   - `doctor` keeps the handle in a module global for the run, the pattern
     its `_RECORDS` already uses, instead of passing it through six nested
     check functions.
   - `enrich.plan(progress=)` opens `check` over the enrichment **files**, and
     only when `self_retrieval_k > 0`, meaning under `--check`. A document
     with no file costs one `stat`, so it is not counted.

```bash
.venv/bin/python -m pytest -q tests_e2e/test_progress_surface.py
```

## Not done, and why

- `explain`, `graph`, `path`, `ask`, `find`, `answer`, `verify --rerun`,
  `enrich --plan`: all finish under a second at `rung-10000`. A bar that
  flashes is noise (the item's own rule), so none of them gets one.
- **Node:** it ships only the read verbs, and all of those are fast. The one
  Node change is the `CLI_VERBS` table, for config parity.
- **Making `doctor` itself faster.** Its identifier check costs as much as
  `fux identifiers`, because it *is* `fux identifiers` without the printing.
  Faster detection (`_is_candidate`: 25 million calls on this repo) would be a
  separate item. Nobody has asked for it, so it is not filed.
- **Making `enrich --check` faster.** Each question is a whole
  `run_query(root, …)` call, at about 70 ms and 20 ms of system time each. The
  index is probably reloaded per question. That is worth a look if a real
  corpus declares scopes. Today none does.
