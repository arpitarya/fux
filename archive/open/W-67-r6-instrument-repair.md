# W-67 — repair R6's instrument, then re-run tier 1

> **CLOSED 2026-08-22 · ARCHIVED.** §3.1/§3.2 reconciled, tier 1 re-specified to
> hash-select a shared shard, and R6 **re-run as a new pre-registration and a new
> verdict: PASS** ([the run](../../work/regression/2026-08-22-r6-rerun/VERDICT.md)).
> The 2026-08-20 pre-registration and the original R6-MERGE verdict were **not
> edited**. Outcome in [IMPLEMENTATION.md](../../work/IMPLEMENTATION.md).
> **Archive is not evidence** — may be named, never cited.


**Status:** **DONE 2026-08-22 — R6 re-run PASSED**
([R6-MERGE-RERUN](../regression/2026-08-22-r6-rerun/VERDICT.md)).
ADR-MERGE-DRIVER's veto 2 is satisfied on a measurement rather than a reading.
**One DoD box was deliberately not executed** — see §The departure below; the
row stays until Arpit has read that.
**Filed:** 2026-08-22 — the debt named by ADR-MERGE-DRIVER's acceptance.

## The departure — this item contradicted itself, and the safer branch was taken

**Read this before assuming the frozen file was edited. It was not.**

This item says two incompatible things:

- **§What lands 1** — *"§3.1 and §3.2 are made to agree"*, plus a DoD box
  requiring the frozen pre-registration's dead link at line 108 be repaired
  *"here and nowhere else"*, riding along **in the §3.1/§3.2 change**.
- **§What lands 3** — *"**The 2026-08-20 pre-registration and the filed R6-MERGE
  verdict are never edited.**"*

Both cannot hold. **Neither §3.1/§3.2 nor the dead link was touched**, and the
repair is a **new instrument file**,
[`PRE-REGISTRATION-R6-v2.md`](../../tools/maintenance-bench/PRE-REGISTRATION-R6-v2.md),
in the relationship `PRE-REGISTRATION-v2.md` already has to
`PRE-REGISTRATION.md` in `tools/pruning-eval/`. Four reasons:

1. **Splitting the commit does not fix the epistemics.** This item's own hazard
   says the repair must not be *"indistinguishable from tuning the ruler to fit
   the result"* — but whoever writes the missing row already knows the
   2026-08-20 result landed in it. Writing that row into the instrument that
   produced the result is post-hoc adjudication whether or not it is a separate
   commit.
2. **A new instrument makes the hole unreachable instead of adjudicated.** With
   tier 1 hash-selected, both machine tiers are informative and the
   partial-informativeness row never fires. It exists for completeness — a
   verdict table with a hole is defective regardless — and it **routes to
   Arpit** rather than resolving, so nothing was gained by writing it either
   way.
3. **The dead link's carve-out lost its premise.** It was justified by *"this
   item already opens that file for a legitimate reason"*. Nothing opened it,
   so the exception does not apply. And a frozen document's links are frozen
   too: W-61 *was* at `work/open/` on 2026-08-20, so the link records where it
   was, which is what an instrument's citations are for. No test enforces it
   (`tests/test_doc_registry.py` governs DOC-REGISTRY rows, not arbitrary
   markdown links), so nothing is broken by leaving it.
4. **It is strictly the more conservative branch.** If Arpit wants the frozen
   file edited, that is a one-line change he can direct. The reverse — undoing
   an edit to a frozen instrument — is not available.

**Spec:** this file.
**Closes with:** a repaired pre-registration whose §3.1 and §3.2 agree, and a
**new** R6 registration + verdict in which tier 1 is informative.
**Blocked by:** nothing.

**Model:** **Opus.** It edits a pre-registration and calls a gate — both are
explicitly Opus work, and the failure mode is a threshold that moved while
looking like it did not.

## Why this exists

[ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md) was accepted on
2026-08-22 on **Arpit's reading of an ambiguous rule**, not on a clean pass.

- [R6-MERGE](../regression/2026-08-20-r6-merge-driver/VERDICT.md) read
  **INCONCLUSIVE**: all three tiers matched, but tier 1 also merged cleanly
  with the driver **removed**, so it proves nothing.
- **§3.1 says** an uninformative tier *"does not count toward the pass"*.
- **§3.2's PASS row says** tiers 1 **and** 2 must be informative; its
  INCONCLUSIVE row says **neither** must be. The result fits **no row**.
- Arpit ruled §3.1 governs. Defensible — §3.1 is where informativeness is
  defined — but it is a reading, and a record now rests on it.

**Two strikes → a gate** (CLAUDE.md): this is the second time an instrument's
own text, rather than the engine, decided an outcome. The repair is mechanical
and it is owed.

## What lands

**1. §3.1 and §3.2 are made to agree** — in a change that files **no verdict**.
Whichever way they are reconciled, the *threshold* is untouched: "machine planes
conflict-free, human conflicts preserved" is verbatim and stays verbatim.
The table must have a row for *"all tiers match, some but not all informative"*,
because that is the case that fell through.

**2. Tier 1 is re-specified so it can be informative** — its two added documents
are selected **by hashing to share a shard**, which is exactly what the post-hoc
tier 1b already does and what makes the control arm conflict.

**3. A new pre-registration and a new verdict.** Frozen before the first number,
as its own file. **The 2026-08-20 pre-registration and the filed R6-MERGE
verdict are never edited** — the adjudication addendum on the latter is the only
thing that was added, and nothing further is.

## Definition of done

- [x] §3.1 and §3.2 agree, with a row covering partial informativeness, and the
      threshold restated **verbatim** rather than reworded. **Done in a new
      instrument, not by editing the frozen one** — see §The departure.
      `PRE-REGISTRATION-R6-v2.md` §2 carries the threshold character for
      character; §3.2 has four rows and the harness has four branches.
- [x] Tier 1 re-specified to hash-select a shared shard; the harness selects at
      run time, not by hope. **Promoted verbatim from the existing `tier1b`**,
      so the specification predates this session in git history even though the
      pre-registration does not. The old tier 1 is kept as an **unjudged** arm —
      "most concurrent adds need no driver" is a true finding.
- [x] A new pre-registration written **before** any number exists.
      ⚠ **Written, not committed** — the tree held a large uncommitted change
      set a concurrent session also had, so committing it alone was not
      available. `git log` therefore cannot evidence the ordering, which is a
      real weakening and is declared in that file's §0.1 and in the verdict.
- [x] R6 re-run and a **new** `VERDICT.md` filed beside its evidence —
      [R6-MERGE-RERUN](../regression/2026-08-22-r6-rerun/VERDICT.md), **PASS**.
- [x] ADR-MERGE-DRIVER reconciled: veto 2 satisfied on a PASS, in the same
      change as the verdict. Veto 5 did not fire (the §3.1 reading stands);
      vetoes 2 and 5 are marked SPENT and a new veto 6 fires if a future run
      lands on `PARTIAL`.
- [x] The run filed under `work/regression/` per the conformance-run law —
      report + ANALYSIS + evidence + a row in `work/regression/README.md`.
- [ ] ~~The frozen pre-registration's dead link is repaired~~ — **deliberately
      not done.** The carve-out that authorised it was premised on this item
      already opening that file, and nothing opened it. A frozen instrument's
      links are frozen too: W-61 *was* at `work/open/` when that file was
      written. **This box is left unticked rather than quietly dropped**, and
      it is the one thing here Arpit may want to overrule — see §The departure.

## Hazards

- **A pre-registered threshold may never move.** Repairing a *verdict table* so
  it covers a case it omitted is not moving a threshold; rewording what is being
  measured is. If the line between those is unclear in a specific edit, that
  edit is Arpit's, not the runner's.
- **Do not fold this into a verdict-filing change.** The instrument is repaired
  in one change and judged in another — otherwise the repair is indistinguishable
  from tuning the ruler to fit the result.
- **The post-hoc tier 1b is not evidence.** It was built after seeing the result
  it fixes. It tells you how to re-specify tier 1; it does not tell you the
  answer.
- **A FAIL here is a successful outcome**, not a failed task. It would mean the
  driver was accepted on a reading that a clean measurement does not support —
  which is exactly what this item exists to find out.

## Reference

- [R6-MERGE](../regression/2026-08-20-r6-merge-driver/VERDICT.md) — the verdict
  and its 2026-08-22 adjudication addendum.
- [`tools/maintenance-bench/PRE-REGISTRATION.md`](../../tools/maintenance-bench/PRE-REGISTRATION.md)
  §3.1 and §3.2 — the contradiction, frozen and not to be edited.
- [ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md) — veto conditions 2
  and 5.
- The harness: [`tools/maintenance-bench/run.py`](../../tools/maintenance-bench/run.py).
