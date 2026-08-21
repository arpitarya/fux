---
type: Regression Run
name: progress-plane-capture
description: The W-64 progress plane captured verbatim on a 1 203-document corpus — every phase, both write verbs, and the stdout byte-identity check that is the whole invariant.
status: complete
timestamp: 2026-08-21T00:00:00Z
---

# The progress plane, captured

**What this is.** A verbatim capture of the bar W-64 added to `fux ingest` and
`fux build`, so [ADR-CLI](../../../docs/adr/0002_cli-surface.md) decision 9 is
grounded in real output rather than an illustration — the same rule the
[CLI surface capture](../2026-08-18-cli-surface/report.md) established.

**The corpus.** 1 203 synthetic documents, one heading and one body line each,
37 shared terms across them. Built by
[`evidence/fixture.sh`](evidence/fixture.sh). **Scores and counts are
properties of that fixture, not of the engine** — what is being captured here
is the *surface*, not a measurement.

---

## The invariant, checked first

**stdout is byte-identical with the bar on or off.** This is the only thing the
progress plane may never get wrong: a leak into stdout corrupts the `--json`
contract every agent consumer reads.

```console
$ fux build --progress   2>/dev/null > a.out
$ fux build --no-progress 2>/dev/null > b.out
$ diff a.out b.out
STDOUT IDENTICAL (build)

$ fux ingest --progress   2>/dev/null > c.out
$ fux ingest --no-progress 2>/dev/null > d.out
$ diff c.out d.out
STDOUT IDENTICAL (ingest)
```

Both diffs are empty. The same assertion runs per-verb in
[`tests_e2e/test_progress_surface.py`](../../../tests_e2e/test_progress_surface.py), which is
what keeps it true rather than merely observed once.

---

## `fux ingest` — the phases as a person sees them

Below is the **final committed frame of each phase**, which is what stays in
scrollback. Between them the line is repainted in place with `\r`.

```console
$ fux ingest
  walk     [████████████████████] 1203/1203
  extract  [████████████████████] 1203/1203  docs/doc1202.md
  edges    [████████████████████] 1203/1203
  write    [████████████████████] 252/252 shards
  read     [████████████████████] 252/252 shards
  codes    [████████████████████] 1203/1203
  postings [████████████████████] 1251/1251 terms
ingested 1203 docs (1203 changed, 0 carried forward), 0 skipped, 252 shards written
accelerator: 1251 terms, 1314 blocks, 10827 postings (derived, not committed)
```

**Seven phases, one continuous sequence.** `walk`/`extract`/`edges`/`write` are
`ingest.run()`'s; `read`/`codes`/`postings` are `derive.build()`'s, reached
because `fux ingest` builds the accelerator at the end. They do not interleave
because `main` constructs **one** `Progress` and hands it to both — the
two-bars-fighting-over-one-line failure decision 9 is written against.

Mid-run frames, lifted verbatim from
[`evidence/progress.txt`](evidence/progress.txt):

```text
  extract  [██████░░░░░░░░░░░░░░] 412/1203  docs/doc0411.md
  postings [█████████░░░░░░░░░░░] 600/1251 terms
```

**A phase whose count is not documents names its unit** — `252/252 shards`,
`1251/1251 terms` — so the drop from `edges`' 1 203 to `write`'s 252 cannot be
misread as losing 950 documents.

**`graph` painted nothing here, correctly.** This fixture's documents link to
nothing, so the phase's total is 0 — below the ~200 threshold, which is the
threshold rule doing exactly its job rather than a gap in the capture.

## `fux build` — the derived plane alone

```console
$ fux build
  read     [████████████████████] 252/252 shards
  codes    [████████████████████] 1203/1203
  postings [████████████████████] 1251/1251 terms
accelerator rebuilt from the committed index: 1203 docs, 1251 terms, 1314 blocks, 10827 postings
```

## What is *not* here, and that is the point

```console
$ fux ingest | tee log.txt     # stdout piped, stderr a TTY -> today's exact output
$ fux ingest > /dev/null       # nothing on stderr at all; no flag anywhere
```

**Off automatically when stderr is not a TTY.** Every existing captured
transcript under `work/regression/` reproduces unchanged, which is why the
gate is TTY detection and not politeness.

## Reproduce

```bash
sh work/regression/2026-08-21-progress-plane/evidence/fixture.sh /tmp/progress-demo
cd /tmp/progress-demo
python -m fux.cli ingest --progress 2>progress.txt
python -m fux.cli build  --progress 2>build.txt

# the invariant
python -m fux.cli build --progress    2>/dev/null > a.out
python -m fux.cli build --no-progress 2>/dev/null > b.out
diff a.out b.out    # expect: empty
```

`--progress` is needed in the reproduce because a captured run is a pipe, not
a terminal — without the force, both arms take the silent path and the
comparison proves nothing.
