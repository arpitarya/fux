---
type: Prompt
title: "Prompt 2 — Claude Code grows the ladder, blind"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 2 — Claude Code: grow the ladder, blind

**Model: Opus** — the hard negatives decide whether the benchmark is hard, and
"no fact about a seed entity" is a judgment no test fully catches.

**Paste into Claude Code, from the root of the `fux` repo:**

```
Execute work/golden/README.md "Phase 2 — Extend the ladder" exactly.
Read CLAUDE.md §Golden answer key first. You may read work/golden/README.md,
work/golden/prompts/2-claude-extend.md and work/golden/seed/ — NOTHING else
under work/golden/. Never open, list, grep or hash golden-answer/. If any tool
output ever shows you a question or an answer, stop and report it.

Build ONE SELF-CONTAINED DIRECTORY PER RUNG under
~/my_programs/fux-lab/corpora/golden/: rung-seed, rung-00100, rung-00200,
rung-00500, rung-01000, rung-02000, rung-05000, rung-10000. Each is a git repo
with real copies (no links): seed files at seed/NN-….md exactly as named in
work/golden/seed/, new files under ext/<category>/. Content is nested — each
rung = the previous rung's files byte-identical + new files.
Follow the category mix and the rule that no new document states a fact about a
seed entity. Model-authored documents up to rung 500; a deterministic generator
(fixed seed, stable order) beyond, extending fux-lab/shared/generate/ if it fits.
For each finished rung: fux setup (sources: seed, ext; pii.toml present;
.fux/formats.toml including EVERY extension present — the seeds are .md, .txt,
.yaml, .eml, .html), fux ingest --full, confirm the skip list names no seed/
file, commit inside the rung. Also (README "Declare and date"): sources list
seed, seed/archive archived=true, ext, ext/archive archived=true; commit each
seed file at its work/golden/seed-dates.tsv date; never declare supersedes: on a
seed; write work/golden/ladder/rung-NNNNN.coverage and stop if its counts do not
match the declarations. Write work/golden/ladder/rung-NNNNN.sha256
("sha256  path  category  origin", documents only) and
work/golden/ladder/rung-NNNNN.index (engine version, index root hash).
Do not ask any query, do not write any question. Stop at 10000. Commit only
your own paths; do not push.
```

🔴 **Do not open `work/golden/questions/`.** It exists before the ladder does (Arpit, 2026-09-12) so phase 4 needs no hand-off, and a rung built by a session that read it is `informed` permanently. This phase reads `work/golden/seed/` and nothing else, and the report says so.
