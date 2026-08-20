# 2026-08-20 — R6: the merge driver, three tiers and a control

**A measurement against a pre-registered threshold.** The tiers, the control
arm, the informativeness rule and the verdict table were frozen in
[`tools/maintenance-bench/PRE-REGISTRATION.md`](../../../tools/maintenance-bench/PRE-REGISTRATION.md)
§3 and committed **before** this harness produced a result (`d98874d`). The
ruling is [`VERDICT.md`](VERDICT.md).

This run also measured **R5**, whose ruling is filed separately at
[`../2026-08-20-r5-hook-latency/`](../2026-08-20-r5-hook-latency/report.md) —
one verdict per prediction, sharing one harness and one raw report.

- **Engine:** the working tree at `d98874d` (dirty — the harness was
  uncommitted while it ran). `src/` last changed in `3a9aabc`, before both this
  run and R4's, so the two describe the same engine.
- **Surface:** Darwin 25.3.0 arm64, Python 3.14.2.
- **Reproduce:** [`evidence/reproduce.sh`](evidence/reproduce.sh) — offline.
- **Raw:** [`evidence/report.json`](evidence/report.json) ·
  [`evidence/run.log`](evidence/run.log)

---

## 1 · The tiers

Each tier builds a throwaway 100-document git repository, wires it with
`fux hooks --install`, branches, edits, ingests on each branch, and runs a real
`git merge`. **Each runs twice** — with the merge driver registered
(*treatment*) and with it unregistered while `.gitattributes` still names it
(*control*, where git falls back to its ordinary text merge).

| tier | expected | treatment | control | informative? | matches? |
|---|---|---|---|---|---|
| **1 · disjoint adds** | no conflict | clean | **clean** | **no** | yes |
| **2 · one shard, two lines** | no conflict | clean | conflict on `.fux/index/16.jsonl` | yes | yes |
| **3 · same document, both sides** | conflict preserved | conflict on `.fux/index/08.jsonl` + `docs/doc-0.md` | same | n/a | yes |
| *1b · disjoint adds, one shard* | *(post-hoc)* | clean | conflict on `.fux/index/08.jsonl` | yes | yes |

**Every judged tier matched its expected column. Tier 1 was uninformative.**
That combination is not covered by the frozen verdict table, so the ruling is
`INCONCLUSIVE` with the reason stated — see [`VERDICT.md`](VERDICT.md).

## 2 · Tier 1, and why the control arm earned its place immediately

Tier 1 — *both sides add different documents* — merged cleanly **with and
without the driver**. The reason is structural: two documents added on two
branches hash into two different shard files, so git is merging two files that
each changed on one side only, which it has always been able to do.

**Without the control arm this tier would have been recorded as a pass**, and
it would have been evidence for nothing. The driver could have been absent and
the result identical. That is precisely the failure the pre-registration's §3.1
was written to prevent, and it fired on the first run.

**Post-hoc, tier 1b answers the question tier 1 was meant to ask.** Two added
documents whose ids are *selected by hashing* to land in the same shard: the
control conflicts on `.fux/index/08.jsonl`, the treatment merges cleanly. So
the mechanism does work for concurrent adds — tier 1's construction was simply
too easy to show it. **1b is labelled post-hoc and is excluded from the
verdict**, because it was built after seeing tier 1's result.

## 3 · Tier 2 — the case the driver exists for

Two documents that share a shard file, one edited on each branch. The pair is
found by hashing the live index at run time, not chosen by hand.

- **Control:** `.fux/index/16.jsonl` conflicts. Git sees neighbouring JSON
  lines changing on both sides and reports a conflict **on adjacency alone**.
- **Treatment:** clean, and both edits survive at the `ver` their own branch
  produced — asserted in the harness, not inferred, so a "clean merge" that
  silently dropped one side could not read as a pass.

This is the whole argument for the driver, and it holds.

## 4 · Tier 3 — the refusal, reported as prominently as the passes

Both branches edit `docs/doc-0.md` differently. Two things are asserted:

1. **`docs/doc-0.md` conflicts**, exactly as it always did. The human plane is
   untouched by any of this.
2. **`.fux/index/08.jsonl` conflicts too, with ordinary
   `<<<<<<< ours` / `>>>>>>> theirs` markers and both sides' bytes intact.**
   Facing two records at the same `ver` with different bytes, the driver
   refused rather than publishing a record neither branch produced.

The harness asserts the markers, so a driver that silently picked a side would
fail this tier rather than pass it quietly.

**Tier 3 is the reason a "no conflicts everywhere" result would have been bad
news.** A merge driver that never refuses is not conflict-free; it is lossy.

## 5 · What this run does not measure

- **Not `git rerere`, submodules, or octopus merges.** Two-parent merges only.
- **Not an add/add shard conflict.** Git does not invoke a content merge driver
  when a file is added on both sides with no common ancestor; that limitation
  is recorded in ADR-MAINTENANCE and was out of scope here by pre-registration.
- **Not concurrent processes.** One writer at a time is assumed; the prediction
  is about branches, not about two `fux ingest` runs racing.
