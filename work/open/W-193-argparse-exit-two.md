---
type: OpenItem
id: W-193
title: "W-193 — argparse produces exit 2, and SR-CLI decision 5 says 2 is never produced"
description: "`fux update` now exits 2 with argparse's *invalid choice*. Decision 5 reserves 2 for strict-mode hooks and says fux does not produce it. The contradiction predates W-177; what W-177 changed is that a command line valid in the released 2.0.1 now produces one, so a consumer's CI reads a rename as infrastructure breaking. Found by the W-177 surface capture; the fix is a change to the error contract on every verb, which is Arpit's."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-193 — the exit code nobody decided

## ✅ RULED 2026-09-16 (Arpit, Cowork) — option 1: leave `2` to argparse, amend decision 5

**Ruling: option 1.** `2` stays argparse's de-facto usage code, and
[SR-CLI](../../records/0101_cli-surface.md) decision 5 is amended to say so:
**fux produces `0`, `1`, `130`; `argparse` produces `2` for a usage error raised
before `cli.main`'s boundary is reached.** The strict-mode reservation on `2` is
**retired** — it was never live, and a reservation nothing could claim is exactly
what makes a consumer read `fux update` → `2` as *the runner broke* rather than
*the verb is gone*.

**Not taken:** (2) overriding `ArgumentParser.error` — it changes the exit code
of **every malformed command line fux has ever accepted**, on the strength of one
deleted verb, and `2`-for-usage is the convention a consumer's tooling already
assumes; (3) renumbering the reservation — it keeps a dead reservation alive and
leaves two meanings documented on one code.

**Agent work, in order:**

1. **Amend SR-CLI decision 5** to the wording above, in the same change as
   anything else it touches (rule 52). Delete *"`2` is reserved and not
   produced"* and *"Do not treat `2` as live"*; state where the `2` comes from
   and that no `raise FuxError` site produces one.
2. **`CLAUDE.md` §Error contract** follows the record; it states no rule of its
   own.
3. **CHANGELOG**, under 3.0's breaking block: `fux update` is gone, `fux ingest`
   replaces it, **and the exit code a consumer will now see is `2` with an
   argparse usage message** — so a pipeline can tell a rename from an outage.
   The existing note says the verb is gone and stops there.
4. **A test pins it:** an unknown verb exits `2` with argparse's message on
   stderr, and a `FuxError` path still exits `1`.
5. ⚠ **No `exit_code=2` is introduced anywhere.** The amendment documents
   argparse's behaviour; it does not license fux code to produce a `2`. If the
   work turns out to need a `src/` change, **stop and re-inbox**.


**Model: Sonnet** once ruled; the ruling is Arpit's.

## What was found

[SR-CLI](../../records/0101_cli-surface.md) decision 5:

> **Exit codes: `0` ok · `1` error · `130` interrupted. `2` is reserved and not
> produced** — no `raise FuxError` site passes `exit_code=2`. It is kept in the
> contract for strict-mode hooks; a `2` appearing later narrows behaviour and is
> compatible. **Do not treat `2` as live.**

Measured in the [W-177 surface capture](../regression/2026-09-15-ingest-absorbs-update/report.md):

```console
$ fux update
fux: error: argument command: invalid choice: 'update' (choose from setup, doctor, …)
# exit 2

$ fux ingest --refresh-urls
fux: error: unrecognized arguments: --refresh-urls
# exit 2
```

**Decision 5 is not wrong about what it says.** It is a statement about
`raise FuxError` sites, and no fux code passes `exit_code=2`. The `2` comes from
`argparse.ArgumentParser.error`, which calls `sys.exit(2)` before `cli.main`'s
boundary is ever reached — so the one place decision 4 says errors are rendered
never sees it.

## Why it matters now rather than a month ago

**`fux badverb` has exited 2 since the parser existed.** Nobody typed it.

**W-177 deleted a shipped verb.** `fux update` was in the released
`fux-engine` 2.0.1 and is in consumers' pipelines. From 3.0 it produces a `2` —
and decision 5 told every one of those consumers *"do not treat `2` as live"*,
which is exactly the reading that makes a **rename** look like **the runner
broke**, not like the command failed.

⚠ **The same seam is already named in `CLAUDE.md` §Error contract**, where an
earlier copy claimed `2` meant *blocking (strict)* and the record said it was
never produced. That was resolved as a documentation defect. This is the first
time it produces a consequence for somebody outside this repo.

## The fork, for Arpit

1. **Leave it.** `2` stays argparse's de-facto usage code, and decision 5 is
   amended to say so — *"fux produces 0, 1, 130; argparse produces 2 for a
   usage error before the boundary"*. Costs nothing, documents reality, and
   leaves the strict-mode reservation dead.
2. **Take it.** Override `ArgumentParser.error` (and `exit`) to raise
   `FuxError`, so a usage error renders as `error: <message>` on stderr and
   exits `1` like every other error. **This changes the exit code of every
   malformed command line fux has ever accepted**, which is a breaking change
   in its own right — but 3.0 is the release that can carry one.
3. **Split it.** Keep `2` for argparse, and give decision 5's strict-mode
   reservation a different number. Cheapest to implement, and leaves two
   meanings on one code for whoever reads the contract next.

**Not decided by this session, deliberately.** Turning argparse's usage exit
into `1` is a change to the error contract on **every verb**, on the strength of
one deleted command; that is [SR-CLI](../../records/0101_cli-surface.md)'s
subject and its owner's call, not a side effect of a rename.

## What is NOT in scope

- Reviving `fux update`, under any spelling. Decision 16e is ruled.
- The `CHANGELOG` note. It already tells a consumer the verb is gone; it does
  not, and should not, promise an exit code the record has not settled.

## Repro

```bash
sh work/regression/2026-09-15-ingest-absorbs-update/evidence/fixture.sh /tmp/demo
cd /tmp/demo && fux update; echo "exit $?"
```
