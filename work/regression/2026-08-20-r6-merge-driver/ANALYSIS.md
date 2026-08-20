# ANALYSIS — 2026-08-20, R6 and the merge driver

## The diagnosis

**The driver works, and one third of the harness could not have shown it.**

Tiers 2 and 3 are informative and both pass: a shard with two documents edited
on opposite branches merges line-wise instead of conflicting on adjacency, and
a genuine same-`ver` disagreement is refused with both sides left in the file.
That is the substance of R6 and it holds.

Tier 1 merged cleanly **with the driver removed**. Two documents added on two
branches land in two different shard files, so git was merging two files that
each changed on one side. The tier described the everyday case correctly and
the everyday case does not exercise the feature.

**The verdict is INCONCLUSIVE for a reason that is about the frozen table, not
the engine.** §3.1 says an uninformative tier does not count toward the pass;
§3.2's table requires tiers 1 and 2 informative. Those two sentences disagree
about this exact result, and the disagreement was written into the
pre-registration hours before the run produced it.

## Changes made in the same change as this run

**1. The control arm is now permanent.** Every tier runs twice, and the report
records both arms. This was added while writing the pre-registration and
justified itself on the first execution.

**2. Tier 1b exists and is labelled post-hoc.** It answers tier 1's question
with the two added documents *selected by hashing* to share a shard: control
conflicts, treatment merges cleanly. It sits outside the verdict.

**3. ADR-MAINTENANCE's veto condition 2 becomes checkable** — it read *"held
pending Arpit's word"* and now names this run and its reproduce command.

## Specific improvements, each with a repro command

**A — Re-specify tier 1 so it can fail.** The fix is one line: choose the two
added documents by hashing rather than by name, which is exactly what tier 1b
does. Then tier 1 is informative by construction and the ambiguity cannot
recur.

```bash
.venv/bin/python tools/maintenance-bench/run.py --only r6
# tier 1 clean/clean -> UNINFORMATIVE; tier 1b clean/conflict -> informative
```

**This is deliberately NOT done in this change.** Editing the instrument after
seeing its result, in the same change that files the verdict, is how a
pre-registration stops meaning anything. It is a change for the *next* run,
which will carry its own verdict.

**B — Resolve the pre-registration's internal contradiction before re-running.**
§3.1 and §3.2 disagree about "all tiers match, some informative". Whichever
reading Arpit takes, the file should say only one of them.

```bash
sed -n '/### 3.1 The control arm/,/^## 4/p' tools/maintenance-bench/PRE-REGISTRATION.md
```

**C — Assert the refusal markers, permanently.** Tier 3 already checks that the
conflicted shard carries `<<<<<<< ours` / `>>>>>>> theirs` with both sides'
bytes. Keep that assertion in any re-spec: a driver that silently picked a side
would otherwise pass tier 3 by conflicting for the wrong reason.

```bash
uv run pytest -q tests/maintain/test_mergedriver.py
```

## Unresolved

- **The verdict is Arpit's to close.** Two readings of the frozen text both
  have support; this run does not pick one.
- **Add/add on the same shard path is still untested at the git level.** Git
  does not invoke a content merge driver when a file is added on both sides
  with no common ancestor. Tier 1b exercises adds whose *documents* share a
  shard but whose shard **file** already existed; the case where the shard file
  itself is new on both branches remains the limitation ADR-MAINTENANCE
  records.
- **One writer at a time is assumed and unmeasured.** Nothing here says what
  happens when two `fux ingest` processes race in one working tree.
