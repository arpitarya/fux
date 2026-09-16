---
type: Regression Run
name: consumer-fetchers-capture
description: "`fetch=<name>` resolving to a fetcher fux never shipped, captured verbatim — the answer it produces, the `fetcher bindings` doctor row that passes, and the one-letter typo that now parses and is caught by that row instead of by the grammar."
status: complete
timestamp: 2026-09-15T00:00:00Z
---

# A consumer's own fetcher, named on a line and used

**What this is.** A **surface capture** for
[W-178](../../open/W-178-consumer-planes-open-sets.md), so
[SR-URL-LIST](../../../records/0116_url-list.md) decision 15 and
[SR-DOCTOR](../../../records/0152_doctor.md)'s new `fetcher bindings` row rest
on real output. **Not a measurement** — no number here is a performance claim,
and a surface capture carries no `blind`/`informed` classification
([README](../README.md) §Per-run contract row 7).

**Reproduce:**

```bash
sh evidence/fixture.sh /tmp/demo && cd /tmp/demo && sh <repo>/work/regression/2026-09-15-consumer-fetchers/evidence/capture.sh
```

**The corpus.** One markdown document and **two URL lines**: one through the
shipped `http` fetcher, one through **`glassbox`** — a file that exists only in
the fixture. Both fetchers are local; nothing touched a network. Raw
transcript: [`evidence/capture.txt`](evidence/capture.txt).

🔴 **Before 2026-09-15 this fixture could not be ingested at all.** `fetch=` was
a closed tuple of the two fetchers fux ships, so `fetch=glassbox` was refused by
the grammar before anything looked at the directory.

---

## It ingests, and the answer comes from the consumer's module

```console
$ fux ingest
fetching  2 listed URL(s) (network) — no dirty list yet, so nothing is known to be stale
ingested 3 docs (3 changed, 0 carried forward), 0 not indexed, 0 skipped, 3 shards written
# exit 0

$ fux answer "pager rota"
# The pager rota

glassbox carried this one, and fux ships no such module

  -- https://wiki.test/rota:L1-L3 (sha 0ade98fe262f, current)
# exit 0
```

**Asserted on the ANSWER, not on the exit code.** A run that swallowed the
fetch and exited 0 is the failure this is aimed at — the bytes have to be
`glassbox.py`'s, cited, with a `current` verdict.

## The doctor row passes when the file is there

```console
$ fux doctor | grep fetcher
[OK] fetcher bindings: 2 fetcher name(s) in use, each resolving to a file in fetchers/
```

## 🔴 The price of an open set, and where it is paid

One letter removed — `fetch=glasbox` — and the line is still **perfectly legal**:

```console
$ fux doctor | grep fetcher
[FAIL] fetcher bindings: 1 URL line(s) name a fetcher with no file: glasbox.
       /tmp/demo/.fux/fetchers/ has ['glassbox', 'http']. Every fetch through one of
       these fails at ingest time - write the module, or fix the `fetch=` name

$ fux ingest
fetching  2 listed URL(s) (network) — no dirty list yet, so nothing is known to be stale
error: fetcher not found: .fux/fetchers/glasbox.py (looked in /tmp/demo/.fux/fetchers/glasbox.py)
       — fetchers/ has ['glassbox', 'http'], so check the `fetch=` name on the line, or point
       [sources.url] fetcher at your own file. `fux doctor` reports this before a run
# exit 1
```

**This is the whole argument for the doctor row, measured rather than
asserted.** The typo does not degrade the run — `fux ingest` **exits 1 and
indexes nothing**, so one wrong character on one line takes the entire corpus
down until somebody reads the error. The grammar used to catch that at read
time; `doctor` catches it now, before a run, and the run's own message is the
backstop.

⚠ **The ingest message was wrong for exactly this case and is fixed here.** It
said *"run `fux setup` to write the shipped fetchers into `.fux/fetchers/`"* and
nothing else — correct advice while `fetch=` was an enum, and actively
misleading for `glasbox`, where `fux setup` writes two files and neither is the
one the line names. It lists the sibling stems now, which is what turns a typo
into a one-character fix.

## What this run does NOT claim

- **Nothing about performance.** Three documents.
- **Nothing about a real fetcher.** Both are four-line local files, which is the
  consumer-fetcher boundary ([SR-FETCHER](../../../records/0117_fetcher.md)
  decision 1), not a shortcut — a capture that made a real request would not
  reproduce.
- **Nothing about `fux add`.** There is deliberately no `--fetch <name>` flag;
  the custom-name route is `fux add <URL> --no-ingest`, edit the value, then
  `fux ingest <URL>`. That is a surface decision, not a gap this run found.
