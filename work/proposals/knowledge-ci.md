---
type: Proposal
title: Knowledge CI — the lockfile for organizational knowledge
description: A CI gate where a PR fails when it contradicts recorded decisions — the committed index's root hash makes "what the corpus knew" a checkable build input.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# Knowledge CI — the lockfile for organizational knowledge

**The idea.** The committed index gives every corpus state a single root
hash and every decision a citable, sha-pinned location. That makes a new
CI class possible: a `fux check-pr` step that (a) verifies the index is in
sync with the sources the PR touches (staleness gate — the lockfile
analogy: `package.json` changed, lockfile didn't), and (b) queries the
corpus for decisions the diff plausibly contradicts (an ADR saying "never
X" while the PR does X) and posts them as review comments with citations.

**Why now-ish but not in plan.** (a) is nearly free after M6 (hooks +
`--check` reads the ledger) and could ship as an M6 stretch. (b) is the
visionary's 18–36-month position ("knowledge-CI"), needs the retrieval
quality of M4 plus precision tuning — a false-positive nag in CI kills
trust in one week. Deliberately parked until the engine dogfoods clean.

**Sketch.** GitHub Action: `fux ingest --check` (fail = stale index);
`fux ask --json` over terms extracted from the diff; findings above the
confidence floor post as non-blocking review comments citing doc + line +
sha. Advisory first, blocking never before a measured false-positive rate.

**Graduation trigger.** M6 lands and the fux repo itself runs (a)
green for two weeks; then (b) prototypes against this repo's own ADRs.

**References.** Council visionary seat (WORKLOG 2026-08-09) · paper §1.1
(agents act on answers) · the Fux founding objective (deviations can't
land) · [`audit-evidence-trail`](audit-evidence-trail.md) (the same
mechanism pointed at compliance).
