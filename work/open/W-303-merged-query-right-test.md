---
type: Handoff
name: W-303
description: "Research item (Arpit, 2026-10-25): design the RIGHT test of the merged query W-300 shipped — a large real index package (codelaw's rules) pinned beside a real repository, questions not written by Claude, and the one risk the W-300 run could not see counted: a package pushing the repository's own answers off rank 1. Output: a proposal plus a pre-registration draft and a testing item to run it. No code."
item: W-303
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-303 — research: how to test the merged query the right way

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Pick the corpus: a **real** consumer repository (candidate: this repo's `docs/` + `records/`) with a **real, larger** package pinned beside it (candidate: codelaw's `@codelaw/rules-js`, 140 rules, packed with `fux pack`). Merged total ≤ 10 000 (SR-PKG-INDEX d9) | a package that can actually crowd the repository — the case W-300's 3-doc fixture could not show | ⏳ |
| 2 | Decide who writes the questions — **not Claude** (Arpit or Codex), so the run can be decided by the table (SR-RS d6) | a run that is not filed INCONCLUSIVE by construction | ⏳ |
| 3 | Name the slices: **repo-answer questions whose words overlap the package's** (the crowding slice — losses here are the risk) and package-answer questions (the gain) | the measurement aims at the risk, not at a win that was certain | ⏳ |
| 4 | Name the endpoints and the bar under L13: repo-answer `hit@1` losses `scope=all` vs `scope=repo` as C2; package `hit@1` as C1; latency on a package-bearing rung; whether `section@1` applies | every guardrail the W-300 run could not measure has a home | ⏳ |
| 5 | Decide whether it must be a golden set (L11, sealed) or open test data, and which rung carries the package | the run can be scored without anyone reading a key | ⏳ |
| 6 | Write the proposal + a pre-registration draft; file the run as a `testing` item; Arpit picks | a decision, and a runnable item | 🔴 Arpit decides |

**Status: filed 2026-10-25, not started.** Research and a proposal only — **no
code, no ranking change, no record change.**

**Arpit, 2026-10-25 (Cowork),** ruling W-300's L13 run: *"Yeah, declare it as
pass, but add a research item or add a testing item, how to test it this in the
right way. For now, go ahead and ship it."* And: *"keep scope as all."*

**Model:** **Cowork**, Opus — a `research` item, never Claude Code
([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rule 37a).

## Why

- **The W-300 run's 16–0 was close to certain by construction.** Every
  package-slice question was unanswerable from the repository alone, so the
  baseline had to miss and the merged query had to hit. It proved the plumbing
  and the byte-identity gates; it did not test ranking quality.
- **The real risk of `scope = all` as the default is crowding.** Shared idf over
  a merged corpus is correct, but a package larger than its consumer can push
  the repository's own answer off rank 1. The fixture was 3 package documents
  beside 6, so C2 (0 wins, 0 losses outside the slice) could not see it.
- **Three gaps were named in the verdict** and stand: the builder wrote the
  questions (SR-RS d6), no golden G was run (L11), and `section@1` and latency
  were unmeasurable on 9 documents
  ([VERDICT](../regression/2026-10-25-w300-merged-query/VERDICT.md)).

## The remedy if the right test fails

Arpit's ruling keeps `scope = all`. If the run this item designs FAILs on the
crowding slice, the remedy discussed in chat is a **one-line default change** —
`constants.toml [scope] default = "repo"` (L12) — not a ranker change, and it
goes to Arpit as any verdict does.

## Records

- **SR-PKG-INDEX** decision 10 (the merged query; the ruling this item follows up).
- **SR-LAW-13** (the bar the run is decided by) and **SR-RS** decision 6.
- No record is amended by this item; the testing item it files names its own.

## Out of scope

- Building anything, or changing `scope`'s default before a run says so.
- A per-segment prior or weight (W-300 §Out of scope still holds).
