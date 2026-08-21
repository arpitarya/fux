---
type: Regression Run
name: source-verbs-capture
description: The W-63 source verbs captured verbatim — fux add / remove / update over all three lists, both remove-by-coverage branches, the scoped URL fetch, and the four errors each verb can raise.
status: complete
timestamp: 2026-08-21T00:00:00Z
---

# `fux add` / `fux remove` / `fux update`, captured

**What this is.** A **surface capture** — a verbatim transcript of the three
verbs W-63 added, so [ADR-CLI](../../../docs/adr/0002_cli-surface.md)
decisions 1a–1e are grounded in real output rather than in an illustration.
The same rule the [CLI surface capture](../2026-08-18-cli-surface/report.md)
established: **an invented transcript in a record is the class of thing this
repo's pre-registration discipline exists to stop.**

It is not a measurement. No number here is a claim about performance, and the
counts are properties of the fixture.

**The corpus.** Four documents, one of them a PDF the type allowlist rejects,
plus one URL. Built by [`evidence/fixture.sh`](evidence/fixture.sh). Raw
transcript: [`evidence/capture.txt`](evidence/capture.txt).

**The URL is served by a local fake fetcher, and that is the design, not a
shortcut.** Fux never fetches (ADR-FETCHER decision 1); the repo owns the
fetcher file. A capture that made a real request would not reproduce.

---

## `fux add` — record, then do the work

```console
$ fux add handbook
added     handbook archived=false
  in .fux/sources/dirs
ingested 3 docs (1 changed, 2 carried forward), 1 skipped, 1 shards written
  skip docs/architecture.pdf: not an indexed file type
accelerator: 20 terms, 20 blocks, 21 postings (derived, not committed)
# exit 0
```

**A single document needs no new list and no grammar change** — `dirs` always
accepted one, and `gitdir._candidate_paths` always branched on `is_file()`.
What was missing was only the command:

```console
$ fux add docs/architecture.pdf
added     docs/architecture.pdf archived=false
  in .fux/sources/dirs
ingested 3 docs (0 changed, 3 carried forward), 1 skipped, 0 shards written
  skip docs/architecture.pdf: not an indexed file type
accelerator: 20 terms, 20 blocks, 21 postings (derived, not committed)
  → the line is listed, and the type allowlist rejects it. `fux add '*.pdf' --types` allows it; adding a file never overrides the allowlist
# exit 0
```

**Adding a file never overrides the type allowlist.** Inclusion is a
conjunction with no precedence (ADR-DIR-LIST / ADR-TYPES), so the line is
written, the check still runs, and the verb says which of the three
conditions rejected the file — and how to change it. **Exit 0**: a listed
file the allowlist rejects is a fact about the corpus, not an error.

### The scoped fetch

```console
$ fux add https://wiki.corp/runbook --cdp --plain
added     https://wiki.corp/runbook fetch=cdp meta=plain
  in .fux/sources/urls
ingested 4 docs (1 changed, 3 carried forward), 1 skipped, 1 shards written
  skip docs/architecture.pdf: not an indexed file type
accelerator: 26 terms, 26 blocks, 27 postings (derived, not committed)
[stderr] fetching  https://wiki.corp/runbook (network — this URL only)
# exit 0
```

One of the engine's **two** named networked paths, and it says so on stderr —
scoped to the URL just added, not the whole list. `--no-fetch` opts out.

### The type allowlist is extended, never replaced

```console
$ fux add *.pdf --types
added     *.pdf
  in .fux/sources/types
ingested 4 docs (1 changed, 3 carried forward), 0 skipped, 1 shards written
accelerator: 25 terms, 25 blocks, 26 postings (derived, not committed)
# exit 0

$ fux add
.fux/sources/types:
  *.adoc
  *.markdown
  *.md
  *.org
  *.pdf
  *.rst
  *.txt
```

The PDF is now indexed (`0 skipped`), **and the six built-in patterns are
still there.** See ANALYSIS §2 — they are there because this run found them
missing first.

### Writing nothing

```console
$ fux add docs --dry-run
would add docs archived=false
  in .fux/sources/dirs
  then: ingest (no network)
# exit 0
```

---

## `fux remove` — two ways in, two ways out

**Its own line → delete the line:**

```console
$ fux remove handbook
removed   handbook archived=false
  in .fux/sources/dirs
ingested 3 docs (0 changed, 3 carried forward), 0 skipped, 0 shards written
accelerator: 22 terms, 22 blocks, 23 postings (derived, not committed)
  dropped file:handbook/rota.md from the index
# exit 0
```

**Covered by a listed ancestor → write an exclusion:**

```console
$ fux remove docs/onboarding.md
excluded  !docs/onboarding.md
  in .fux/sources/dirs — docs still listed; this path is subtracted from it
ingested 2 docs (0 changed, 2 carried forward), 1 skipped, 0 shards written
  skip docs/onboarding.md: excluded by !docs/onboarding.md
accelerator: 15 terms, 15 blocks, 15 postings (derived, not committed)
  dropped file:docs/onboarding.md from the index
# exit 0
```

**The verb states which branch it took**, because "removed" and "excluded" are
different facts about the file and a reader of the diff needs to know which.

**A URL is always a line delete** — `urls` has no exclusions, because there is
nothing to subtract from:

```console
$ fux remove https://wiki.corp/runbook
removed   https://wiki.corp/runbook fetch=cdp meta=plain
  in .fux/sources/urls
ingested 2 docs (0 changed, 2 carried forward), 1 skipped, 0 shards written
  skip docs/onboarding.md: excluded by !docs/onboarding.md
accelerator: 15 terms, 15 blocks, 15 postings (derived, not committed)
  dropped url:https://wiki.corp/runbook from the index
# exit 0
```

**That run made no network call**, and it is the point of W-63's defect 1: the
URL left the index on an ordinary offline ingest. Before this change it would
have survived until someone ran `--refresh-urls`, i.e. **deletion required the
network**.

**Neither listed nor covered → an error naming both checks:**

```console
$ fux remove elsewhere/nope.md
[stderr] error: elsewhere/nope.md is not in <root>/.fux/sources/dirs: it has no line of its own, and no listed entry covers it. Both were checked. `fux add elsewhere/nope.md` would list it; nothing needs removing
# exit 1
```

---

## `fux update` — re-read what is listed

```console
$ fux update --check
  fresh  2 others
nothing has drifted.
# exit 0

$ fux update
ingested 2 docs (0 changed, 2 carried forward), 1 skipped, 0 shards written
  skip docs/onboarding.md: excluded by !docs/onboarding.md
accelerator: 15 terms, 15 blocks, 15 postings (derived, not committed)
# exit 0
```

**`--check` writes nothing and is offline for the `dirs` half** — a file's
freshness is its bytes' sha against the record's, and both are local.

**No `fetching` line on that `update`,** because by this point in the run the
URL list is empty. See ANALYSIS §1: it printed one before this run caught it.

---

## Reproduce

```bash
sh work/regression/2026-08-21-source-verbs/evidence/fixture.sh /tmp/source-verbs-demo
cd /tmp/source-verbs-demo
python -m fux.cli ingest
python -m fux.cli add handbook
python -m fux.cli add https://wiki.corp/runbook --cdp --plain
python -m fux.cli remove docs/onboarding.md
python -m fux.cli update --check
```

Paths in the transcript above are abbreviated to `<root>`; everything else is
verbatim from [`evidence/capture.txt`](evidence/capture.txt).
