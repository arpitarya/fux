---
type: Regression Run
name: ingest-absorbs-update-capture
description: "The W-177 surface captured verbatim — `fux ingest` doing everything `fux update` did, the bare verb going to the network, `--no-fetch` not, `--refetch-all`, `--failed`, `--check` beating `--list-skipped`, a pinned line never fetched, and the two deleted spellings failing."
status: complete
timestamp: 2026-09-15T00:00:00Z
---

# `fux ingest` after it absorbed `fux update`, captured

**What this is.** A **surface capture** — a verbatim transcript of the verb
[W-177](../../open/W-177-ingest-absorbs-update.md) reshaped, so
[SR-CLI](../../../records/0101_cli-surface.md) decision 16 and
[SR-INGEST](../../../records/0106_ingest.md) decision 21 are grounded in real
output rather than in an illustration. Same rule the
[source-verbs capture](../2026-08-21-source-verbs/report.md) followed:
**an invented transcript in a record is the class of thing this repo's
pre-registration discipline exists to stop.**

It is **not a measurement.** No number here is a claim about performance, and
every count is a property of the fixture. A surface capture carries no
`blind`/`informed` classification — [`README`](../README.md) §Per-run contract
row 7 exempts it.

**Reproduce:**

```bash
sh evidence/fixture.sh /tmp/demo && cd /tmp/demo && sh <repo>/work/regression/2026-09-15-ingest-absorbs-update/evidence/capture.sh
```

**The corpus.** Two markdown documents, one PDF, and **two URLs** — one
ordinary, one carrying `update=never`. Raw transcript:
[`evidence/capture.txt`](evidence/capture.txt).

🔴 **The fetcher appends to `.fux/fetchers/CALLED` on every call, and that file
is the whole instrument.** This capture's subject is *which invocations go to
the network*, and reading that off the stderr announcement would prove nothing:
the announcement is exactly what a bug would leave in place while the fetch
happened anyway, or remove while it still happened. The log is printed between
commands, and **what it does not grow is the finding**.

---

## The bare verb goes to the network — decision 16a

```console
$ fux ingest
fetching  2 listed URL(s) (network) — no dirty list yet, so nothing is known to be stale
  ! https://wiki.test/pinned — update=never; pinned, no fetch attempted; prior record kept
ingested 3 docs (3 changed, 0 carried forward), 1 not indexed, 0 skipped, 3 shards written
  not indexed https://wiki.test/pinned: update=never; pinned, no fetch attempted
accelerator: 26 terms, 26 blocks, 29 postings (derived, not committed)
# exit 0

--- .fux/fetchers/CALLED (after the first bare ingest) ---
https://wiki.test/runbook
```

**One line of the log, not two.** Both URLs are listed; the pinned one was
never fetched, and the announcement counts what is *considered* while the log
records what is *called*. That is DoD 5 — `update=never` is a property of the
line ([SR-URL-LIST](../../../records/0116_url-list.md) decision 14) and it
survived the verb change untouched.

## `--no-fetch` calls nothing — decision 16c, and the L4 fence

```console
$ fux ingest --no-fetch
ingested 3 docs (0 changed, 2 carried forward), 0 not indexed, 0 skipped, 0 shards written
accelerator: 26 terms, 26 blocks, 29 postings (derived, not committed)
# exit 0

--- .fux/fetchers/CALLED (after --no-fetch) ---
https://wiki.test/runbook
https://wiki.test/runbook
```

**The log did not grow.** Two entries before, two after — both from the two
bare runs above it. No announcement, no fetcher import, no socket. This is the
invocation `fux hooks` writes into `post-merge`, and
`tests/test_source_verbs.py::test_a_hook_path_ingest_opens_no_socket` pins the
same thing with `socket.socket` monkeypatched to raise.

⚠ **One reporting difference, and it is worth naming rather than smoothing
over.** The offline run says `0 not indexed` where the networked one said `1`.
The pinned URL's notice is produced by the fetch pass deciding not to fetch it,
so an offline run carries the record forward silently and never mentions the
pin. Not wrong — nothing about the pin changed — but *"how many documents are
not indexed"* is a different number depending on a flag that is not about
indexing. Filed as an observation; no decision is asked for.

## `--refetch-all` — decision 16b, and the pin still holds

```console
$ fux ingest --refetch-all
fetching  2 listed URL(s) (network) — `--refetch-all`
  ! https://wiki.test/pinned — update=never; pinned, no fetch attempted; prior record kept
...
--- .fux/fetchers/CALLED (after --refetch-all) ---
https://wiki.test/runbook
https://wiki.test/runbook
https://wiki.test/runbook
```

**The announcement names the flag by its new name**, and the log grew by
exactly one — **the pinned line is not fetched even here**, which is the case
the flag would most plausibly have been allowed to override and is not.

## `--check` is read-only, offline, and has a `--json` form

```console
$ fux ingest --check
  1 url document(s) not checked — verifying one means fetching it, and `--check` does not go to the network on its own
  fresh  2 others
nothing has drifted.
# exit 0

$ fux ingest --check --json
{
  "drifted": [],
  "fresh": 2,
  "unchecked_urls": 1
}
# exit 0
```

## `--check` beats `--list-skipped` — SR-INGEST decision 21b

```console
$ fux ingest --check --list-skipped
  1 url document(s) not checked — verifying one means fetching it, and `--check` does not go to the network on its own
  fresh  2 others
nothing has drifted.
# exit 0

$ fux ingest --list-skipped
# exit 0
```

**Given both, the drift report is what comes back.** The precedence is a
ruling, not argparse's order — and the second command shows what the first
would otherwise have printed, which is nothing on this fixture.

## `--failed`, and a positional entry

```console
$ fux ingest --failed
nothing to fetch — 0 with a failing last run (`--failed`)
ingested 3 docs (0 changed, 2 carried forward), 0 not indexed, 0 skipped, 0 shards written
# exit 0

$ fux ingest https://wiki.test/runbook
fetching  https://wiki.test/runbook (network — this entry only)
ingested 3 docs (0 changed, 2 carried forward), 0 not indexed, 0 skipped, 0 shards written
# exit 0

$ fux ingest docs/nothing.md
error: docs/nothing.md is not in any source list, so there is nothing to ingest. `fux add docs/nothing.md` lists it — `ingest` never creates a line
# exit 1

$ fux ingest --no-fetch docs/nothing.md
error: docs/nothing.md is not in any source list, so there is nothing to ingest. `fux add docs/nothing.md` lists it — `ingest` never creates a line
# exit 1
```

🔴 **The last one is the ordering inside `plan_url_refresh`, captured.**
`--no-fetch` returns early, so the entry has to be located *before* it —
otherwise `fux ingest --no-fetch <typo>` re-ingests the whole corpus and reports
success. Same error, same exit, with and without the flag.

## The two deleted spellings

```console
$ fux update
fux: error: argument command: invalid choice: 'update' (choose from setup, doctor, inspect, ingest, build, add, remove, …)
# exit 2

$ fux ingest --refresh-urls
fux: error: unrecognized arguments: --refresh-urls
# exit 2
```

**Both fail loudly, which is the point of no deprecation alias** (decision
16e). A script that still says `fux update` stops rather than quietly doing
something else.

🔴 **Both exit `2`, and [SR-CLI](../../../records/0101_cli-surface.md) decision
5 says `2` is RESERVED and NOT PRODUCED.** See [`ANALYSIS.md`](ANALYSIS.md) —
this is pre-existing argparse behaviour that W-177 did not create and did make
reachable from a command line that was valid last week.
