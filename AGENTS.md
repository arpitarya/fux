# Working with fux in this repo

This repo has a committed fux index. Search it before you grep.

## Running fux — try these in order, stop at the first that works

    fux --version
    uv run fux --version
    ./.venv/bin/fux --version
    python -m fux --version

Probe ONCE per session, then reuse the rung that worked. `command not found`
on the first rung does NOT mean fux is absent: the engine is installed in a
virtualenv and the index is committed to this repo. Falling back to grep
because rung 1 failed is the specific mistake this list exists to prevent.

Never activate a virtualenv, and never install anything.

## Reading a result

- `fux ask "<question>"` — ranked answers with citations.
- `fux find "<question>"` — locations only, one per line, safe to pipe.
- `fux answer "<question>"` — the single best passage, fetched when reachable.

Add `--band` for a confidence block, or set `band = true` in
`.fux/output.toml` so every run carries one. `answerable: false` means **do not
answer from these results** — say what was searched and stop. `band: partial`
means answer, but name every term in `confidence.missing`.

## Archived documents are not evidence

A result marked archived describes how something USED TO work. The eight rules
below are VERBATIM from fux's canonical policy and are reproduced, never
reworded -- a paraphrase here would be a ninth version of a rule that exists
once on purpose.

<!-- fux:policy:begin v1 — VERBATIM in every rendering. Do not reword. -->
1. **Branch on the `archived` field in `--json`, never on the note's prose.** The wording is not a contract; the boolean is.
2. **Establish the stance before using an archived result** — history, current architecture, or building.
3. **When the stance is ambiguous, treat it as building.** That is the ordering with the worst downside if you guess wrong.
4. **Never drop the mark when summarising.** A summary that launders a retired design into plain prose is the failure this policy exists to prevent.
5. **Never port from an archived document.** Retired means someone decided against it — it may describe a subsystem the project deliberately deleted.
6. **Name the live successor; if there is none, say so** rather than presenting the archived document as the current state.
7. **If every result is archived, lead with that** before answering.
8. **Never infer "archived" from an `archive/` path segment.** The mark is declared on a source, never derived from a path; a path is a hint and can be wrong.
<!-- fux:policy:end v1 -->

## More

Operating detail — flags, output shapes, when each verb is the right one —
lives in the `fux-usage` skill, loaded on demand. This file stays short on
purpose: it is read on every interaction, and a manual here is a tax on every
request in the repo.

<!-- policy-version: 1 -->
