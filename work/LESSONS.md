---
type: Log
description: "Dated build lessons — what this project learned the hard way, newest first. A log rather than a record, because a record states what is true now and carries no history; these are the failures that shaped decisions, and the date is part of the lesson."
---

# LESSONS — what this build learned the hard way

**Why this is a log and not a record.** A record states what is true *now* and
**carries no history** ([the register](../records/README.md)); these entries
are dated failures, and the date is part of the lesson. Folded out of
`CLAUDE.md` §Hard-won build knowledge on 2026-09-14 (W-173), which is where
they had accumulated.

**How to use it.** Newest first. A lesson whose remedy is a *rule* belongs in a
record and is named here only as the failure that produced it. A lesson whose
remedy is *judgement* lives here and nowhere else — and it is unenforced by
construction, which is the honest half.

⚠ **Nothing here is normative.** Where an entry and a record disagree, the
record is the rule and this file is the anecdote that motivated it.

---

## 2026-09-14 — five items in one session

- 🔴 **Read the evidence, then write the reader.** Three defects in one
  afternoon had one cause: a parser written against a guessed shape. `ARMS.toml`
  is `[[arm]]` — an array of tables, one per arm *per corpus* — and a reader
  that guessed `[A]`/`[B]` sections printed *not filed* in every cell of a file
  that had every value in it. `differed` in a null-control JSON is a **list**,
  and a card read `[] differed`. A `level="warn"` doctor row with `ok=True`
  renders `[OK]`, so a disclosure disclosed nothing. **In all three the code
  ran, produced output, and was wrong** — the only thing that caught them was
  running the thing and reading what came out.
- 🔴 **A gate's flag and a gate's rendering are different contracts, and the
  rendering is the one a person meets.** `tests/test_doctor.py` asserted
  `row.ok` and `row.level == "warn"` — both correct as fields — while the line
  a reader saw said `[OK]` beside *every citation from these will be
  `unverified`*. **Assert the rendered line**, because asserting the fields is
  what let it ship.
- **A pre-registered rule is worth more when it fires against you.**
  `fux inspect`'s headline check, self-retrieval, reads **1.000 on every golden
  rung and 1.000 on forty copies of one runbook**. The rule said a floor that
  cannot separate a healthy corpus from a bad one is dropped to descriptive, so
  it was — and the alternative was a check that reads `ok` on every corpus
  anybody will ever run it on. **A rule only demonstrates it works by costing
  you something.**
- 🔴 **A false provenance claim about a threshold is worse than no claim.** A
  report of mine said its pre-registration was *"committed alone, ahead of the
  first number"*; the commit carried 28 files including the implementation, and
  the file was written after the measurement. **The criterion did predate the
  numbers** — in two named commits — which is the part that was checkable, and
  the correction says so rather than dropping the sentence.
- **A key present on one code path and absent on the other is worse than a key
  on neither.** `answer`'s citation is built from an `AskResult` on one path and
  a refer-plane citation on the other; adding `pinned` to the first would have
  had a consumer read `false` from the second for a question that genuinely was
  pinned. The note went to stderr, before either branch.
- **Truncate a list, and ship its count in the same breath.** A top-20 orphan
  list read `20` and the real number was **341** — and *20* is exactly what a
  cap of 20 looks like.

## 2026-09-12 — two sessions, one machine

- 🔴 **A RED TEST ON AN UNCOMMITTED TREE IS INVISIBLE TO EVERY MECHANISM HERE.**
  CI reads commits; the SR-freshness hook reads a commit message; `pytest` reads
  whatever you choose to run. A test that a working-tree change turns red stays
  red and unseen until somebody commits — **and then it fails for whoever
  committed it.** It bit two sessions on the same day for different reasons.
  The only cover is to run **both suites, whole**, before believing a change is
  done; reading the code and concluding is what failed.
  ⚠ **It recurred on 2026-09-14**: a session left 343 files staged with three
  suite failures on them, and the next session inherited both.
- 🔴 **A loaded machine does not produce noise — it produces a clean, localised
  anomaly that reads like a finding.** One session's corpus build inflated a
  single benchmark tier's ingest ratio to **0.77 against ~0.46 everywhere
  else**: tier-localised, internally consistent, and in exactly the shape a
  real regression takes. **Noise gets distrusted; this would have been filed.**
  Caught by two sessions comparing timestamps — a conversation, not a
  mechanism. Interleaving arms (`A B A B`) is the only structural defence and
  it protects the *difference*, never the absolute number.
- **So: say what you are running, and when, to anyone sharing the machine.** It
  is the only thing that worked. Recorded in
  [SETUP-BENCHMARK](setup/fux-benchmark.md) standing rule 0a as an
  **unguarded** gap, because it is one, and as
  [SR-WORK-SESSION](../records/0060_WORK-session.md) decision 12.
- **Concurrent sessions commit, too.** A peer committed a fix to code this
  session had written and not yet committed. **Re-derive `git status`
  immediately before staging, and commit with explicit pathspecs** —
  `git commit -- <paths>` — when the index carries another session's work.
  ([SR-WORK-SESSION](../records/0060_WORK-session.md) decision 10.)

## 2026-08-09 — M1, the pruning gate

- **A pre-registered threshold is only as good as the corpus that tests it.**
  M1's k=128 arm returned a zero delta on all three eval corpora — and prune
  coverage showed why: their documents' median vocabulary is **32–46 distinct
  terms**, so top-128 was a **no-op for 97 %+ of documents**. **Always report
  the fraction of the population a treatment actually touched**; an aggregate
  delta of zero over an untreated population is not evidence.
  ✅ **This one got an instrument on 2026-09-14**: `fux inspect`'s vocabulary
  percentiles are that fraction, computed for any corpus in one command
  ([SR-INSPECT](../records/0156_inspect.md)).
- **Recompute statistics over the pruned index, never borrow them.** `df`, `n`
  and field lengths must come from the surviving postings, because that is what
  production holds. Borrowing the baseline's statistics makes scores line up and
  measures a system nobody will ship. **Keep a diagnostic arm that *does*
  borrow** — it is how a loss gets attributed to missing postings versus
  shifted statistics.
- **Wrap the archive; never edit it.** The archived `Searcher` exposed a `stats`
  seam, built for the lean profile, that turned out to be exactly the hook the
  diagnostic arm needed. **Look for an existing seam before concluding an
  archived module has to change.**
- **The archived engine's own recorded numbers are a free correctness check.**
  The harness's fixture baseline reproduced the archived lexical eval exactly
  (hit@5 0.952 / MRR 0.833) and orbit's lab number (0.887) — which is what makes
  *"we varied only the index"* a verified fact rather than an intention.

## Earlier — v0.19–0.26, the archived build

**The full set is in git history:** `git show 6473987:CLAUDE.md`.

**Two items still bind, and both are stated in the records that own the code
rather than here:**

| lesson | its home |
|---|---|
| **BM25F means weight-then-saturate ONCE** — never sum per-field BM25 | [SR-RANKING](../records/0111_ranking.md) |
| **No wall-clock output anywhere on the maintenance path** — timestamps derive from `SOURCE_DATE_EPOCH` or source mtime, or the byte-identical guarantee breaks | [SR-LAW-3](../records/0005_LAW-3-deterministic.md) |

They are listed here as the *lessons*; the *rules* are in those two records and
are not restated.
