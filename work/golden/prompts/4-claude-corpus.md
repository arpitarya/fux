---
type: Prompt
title: "Prompt 4 — Claude Code creates or updates the benchmark corpus, blind"
item: W-189
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 4 — Claude Code: create or update the benchmark corpus, blind

**Test-data checklist:** [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) — this prompt carries **T10, T12, T14**. Check the whole list before running it; any item this data does not carry is named as *not carried*, never skipped.

**Model: Opus** — the hard negatives decide whether the benchmark is hard, and
"no fact about a seed entity" is a judgment no test fully catches.

⚠ **The ladder already exists** — eight rungs, `rung-seed` through `rung-10000`,
built 2026-09-12 from this same seed corpus and verified nesting byte for byte.
**The 2026-09-15 reset deleted the questions and answers, not the corpus**, so
this prompt is a **check** today, not a build: verify every manifest against its
rung and stop. Build only what is missing, and rebuild a rung only if
`work/golden/seed/` actually changed.

🔴 **Run this BEFORE prompts 2 and 3 where you can.** The questions live on disk
once Arpit commits them, and a rung built by a session that could have read them
is `informed` for good. When the order cannot be kept, the honour rule below is
the whole of what protects it.

**Paste into Claude Code, from the root of the `fux` repo:**

```
Execute work/golden/README.md "Phase 4 — the corpus" exactly.
Read CLAUDE.md Non-negotiable constraints (law L11) first. You may read
work/golden/README.md, work/golden/prompts/4-claude-corpus.md and
work/golden/seed/ — NOTHING else under work/golden/. Never open, list, grep or
hash work/golden/questions/, golden-answers/ or golden-answer/ — a key may be in
the first of those two and both are closed to you. If any tool output ever shows you
a question or an answer, STOP, say so, and file it before anything else.

FIRST: verify the eight existing rungs against work/golden/ladder/*.sha256 and
report. Build or rebuild ONLY what is missing or what a changed seed invalidates.

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

🔴 **Do not open `work/golden/questions/`.** The released question files sit
there so the run needs no hand-off, and **a rung built by a session that read
them is `informed` permanently.** This phase reads `work/golden/seed/` and
nothing else, and its report says so out loud. **Nothing mechanical enforces
this** — it is honour, and it is named here so a session cannot claim it did not
know.

**Next:** [prompt 5](5-claude-run.md) runs both sets against these rungs.
