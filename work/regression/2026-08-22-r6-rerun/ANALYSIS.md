---
type: Analysis
title: "R6 re-run — what the repaired instrument bought, and what it did not"
description: "The PASS closes ADR-MERGE-DRIVER's veto 2 on a measurement rather than a reading. Two improvements fall out; one finding is worth keeping; the exclusion list needs re-reading now that a background runner exists."
status: final
timestamp: 2026-08-22T00:00:00Z
---

# Analysis — R6 re-run

**Ruling:** [`VERDICT.md`](VERDICT.md) — **PASS** ·
**Report:** [`report.md`](report.md)

## The diagnosis

**The engine was never the problem, and the 2026-08-20 run already said so.**
Every tier matched its expected column then, too. What failed on 2026-08-20 was
the *instrument*: tier 1 could not distinguish a working driver from an absent
one, and the verdict table had no row for the result that produced. This run
changes the instrument and nothing else, and the engine passes cleanly.

**That is the second time an instrument's own text, rather than the engine,
decided an outcome** — the first being R7's threshold turning out to measure a
format the tree does not contain. The two-strikes rule applied here and the
gate is §3.2's completeness: **a verdict table must have a row for every
combination its own §3.1 can produce.** That is now checkable by reading the
two sections against each other, and it is what the `PARTIAL` row exists for.

## Specific improvements

### 1. The verdict table is now total, and the harness proves it

`run.py`'s verdict branch has four arms and no `else` that invents an outcome.
Before, the `AMBIGUOUS` string was constructed at the bottom of an
if/elif chain as *"whatever the frozen table did not cover"* — an honest
stopgap, but it meant the harness could emit a verdict word the instrument had
never defined.

**Repro:** read `measure_r6`'s verdict block against
[`PRE-REGISTRATION-R6-v2.md`](../../../tools/maintenance-bench/PRE-REGISTRATION-R6-v2.md)
§3.2 — four rows, four branches, same order.

### 2. An unjudged arm no longer prints a verdict word

The first execution of this run printed `FAIL` against tier `1-disjoint`, which
contributes to no verdict at all. Nobody was misled — the summary line said
`PASS` — but a reader scanning console output for a red word would have found
one on a line that decides nothing, and that is how a filed number gets
misquoted later.

**Repro:** `.venv/bin/python tools/maintenance-bench/run.py --only r6` and read
the `1-disjoint` line; it says `unjudged`.

### 3. The exclusion list needs re-reading now that W-66 shipped

Both pre-registrations exclude *"concurrent **processes**. One writer at a time
is assumed; the prediction is about branches, not about two `fux ingest` runs
racing."* That exclusion was written on 2026-08-20, when nothing in fux could
start a second `fux ingest`. **W-66 Phase 2 shipped a background runner on
2026-08-22**, so two concurrent ingest processes are now a thing the product
itself can cause.

This is **not** a defect in R6 and does not touch this verdict: the
single-writer discipline is the runner's lock, asserted in
`tests/maintain/test_runner.py`, and the merge driver's job starts after two
*branches* exist. But the boundary between "branches" and "processes" is
thinner than it was when the exclusion was written, and the honest move is to
say so here rather than let a future reader assume R6 covered it.

**Unresolved, and stated as unresolved:** nothing has measured what happens if a
background runner is mid-`write_index` when a `git merge` fires the
`post-merge` hook. The lock makes the two ingests serialise; whether the merge
driver and a serialising runner interact well is untested.

## The finding worth keeping

**Most concurrent adds need no merge driver.** Tier `1-disjoint` — two people
adding different documents that land in different shard files — merges cleanly
with the driver *unregistered*. That is why the original tier 1 was
uninformative, and it is a true fact about the product rather than a flaw to be
tidied away, so the arm was kept and reported rather than deleted.

The corollary is the useful one: **the driver earns its place on same-shard
cases specifically.** With 256 shards, two random adds collide about 1 time in
256; on a busy repository that is not rare, and tier 1's re-specification is
what measures it.

## What this run does not claim

- **It does not supersede [R6-MERGE](../2026-08-20-r6-merge-driver/VERDICT.md).**
  That verdict stands as filed. This is a second measurement beside it.
- **It does not re-judge anything at a different corpus size.** R6 has never
  been a scale gate; 100 documents is what both instruments specify.
- **It is not evidence about `git rerere`, submodules, octopus merges, or
  add/add** — all excluded, in both pre-registrations, before either ran.
