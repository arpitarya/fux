---
type: Analysis
name: ingest-absorbs-update-analysis
description: "What the W-177 capture shows, the one thing it found that nobody asked about (argparse produces exit 2 for a verb this change deleted), and the two behaviours it deliberately does not claim."
---

# What the capture shows, and the one thing it found

## The eight claims, each grounded

Every definition-of-done item in
[W-177](../../open/W-177-ingest-absorbs-update.md) that a transcript can show,
with the line in [`evidence/capture.txt`](evidence/capture.txt) that shows it:

| DoD | shown by |
|---|---|
| 1 · `fux update` is gone, no alias | `invalid choice: 'update'`, exit 2 |
| 1 · `ingest --refresh-urls` is gone | `unrecognized arguments: --refresh-urls` |
| 2 · every flag landed | `--check`, `--json`, `--refetch-all`, `--failed`, `<entry>`, bare |
| 3 · `--check` beats `--list-skipped` | both given → the drift report comes back |
| 4 · the hook path opens nothing | `.fux/fetchers/CALLED` does not grow under `--no-fetch` |
| 5 · pinned lines still never fetch | the `update=never` URL is absent from the log, `--refetch-all` included |
| 6 · transient failure keeps the record | `! <url> — …; prior record kept`, exit 0 |
| 16a · a bare ingest goes to the network | the log grows by one on each bare run |

**The instrument is the fetcher's own log, not the announcement.** A capture
that read *"fetching 2 listed URL(s)"* off stderr and stopped there would pass
identically against an engine that announced and then fetched nothing, or
fetched and never announced. `.fux/fetchers/CALLED` is written by the consumer
fetcher itself, which is the only place in this architecture that knows
whether a request was actually made.

---

## 🔴 The finding: `fux update` exits `2`, and `2` is reserved

[SR-CLI](../../../records/0101_cli-surface.md) decision 5 is explicit —
*"`2` is reserved and not produced"*, kept for strict-mode hooks, *"do not treat
`2` as live"*. `fux update` and `fux ingest --refresh-urls` both exit `2`.

**This is argparse, and W-177 did not create it.** `fux badverb` has exited 2
since the parser existed, and decision 5 is a statement about `raise FuxError`
sites — no fux code passes `exit_code=2` and none does now.

**What W-177 changed is the reach.** Until 2026-09-15, producing a `2` required
typing a verb that never existed. Now it is produced by a command line that was
**valid in the released 2.0.1**, which is exactly the population decision 5
told to *"not treat `2` as live"*: a CI job that branches on `1` for *fux
failed* and treats anything else as *infrastructure broke* will misread a
2.0 → 3.0 upgrade as the pipeline being broken, not the command being renamed.

- **Not fixed here, and deliberately.** Turning argparse's usage exit into `1`
  is a change to the error contract across **every** verb, on the strength of
  one deleted command. That is a decision for
  [SR-CLI](../../../records/0101_cli-surface.md), not a side effect of a rename.
- **Not silently accepted either.** The `## Error contract` section of
  `CLAUDE.md` already carries the note that decision 5 and an earlier copy of
  that section disagreed about `2`; this is the same seam producing a real
  consequence for the first time.
- **Repro:** `sh evidence/fixture.sh /tmp/demo && cd /tmp/demo && fux update; echo $?`
- **Filed as** [W-193](../../open/W-193-argparse-exit-two.md).

---

## What this run does NOT claim

- **Nothing about performance.** Three documents and two URLs; every count is
  the fixture's.
- **Nothing about a real network.** The fetcher is local and fake, which is the
  consumer-fetcher boundary ([SR-FETCHER](../../../records/0117_fetcher.md)
  decision 1), not a shortcut. A capture that made a real request would not
  reproduce.
- **Nothing about the daemon.** Decision 16d splits hook from daemon by caller,
  and only the hook half is transcript-shaped —
  `tests/test_source_verbs.py::test_the_hook_script_is_the_invocation_that_test_pins`
  covers the strings, and the daemon's bare-verb call is
  `maintain/daemon.py`'s own `refresh_urls=True`, which predates this change.

## One observation, no decision asked for

**`not indexed` counts differently with and without `--no-fetch`.** A pinned
URL is reported as `not indexed` on a networked run and not mentioned at all on
an offline one, because the notice is produced by the fetch pass deciding to
skip it. Nothing about the pin changes; the *number on the summary line* does,
under a flag that is not about indexing. Recorded because a consumer diffing
two runs' summary lines would see a document appear and disappear.
