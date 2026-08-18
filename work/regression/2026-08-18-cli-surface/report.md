# 2026-08-18 — CLI surface capture

**This is a surface capture, not a measurement.** No prediction is gated on
it and no threshold was pre-registered. It exists so that
[ADR-CLI](../../../docs/adr/0002_cli-surface.md)'s examples are
verbatim rather than illustrated, and so a future session can diff the real
surface against the recorded one.

- **Version:** `fux 0.32.0`, from source (`PYTHONPATH=<repo>/src python3 -m fux.cli`).
- **Python:** 3.11.15, Linux (Cowork cloud container — the device VM is 3.10
  and cannot run the engine; see [`../../MACHINE.md`](../../MACHINE.md)).
- **Corpus:** the three-document fixture in
  [`evidence/fixture.sh`](evidence/fixture.sh).
- **Reproduce:** `./evidence/fixture.sh /tmp/fux-cli-demo && cd /tmp/fux-cli-demo`,
  then the commands below in order.

Scores are corpus-dependent and this corpus is tiny; read every number as a
property of *this fixture*, not of the engine.

---

## Environment

```console
$ fux --version
fux 0.32.0

$ fux
usage: fux [-h] [--version] {doctor,ingest,build,ask,find,answer} ...

rank, fetch, verify — an index over the systems that own your docs

positional arguments:
  {doctor,ingest,build,ask,find,answer}
    doctor              check environment and repo health
    ingest              walk configured sources into the committed index
    build               rebuild the derived accelerator from the committed
                        index
    ask                 answer a question from the committed index, with
                        citations
    find                ranked document locations, one per line
    answer              the single best answer the index can give

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
# exit 1
```

## `doctor`

```console
$ fux doctor
[OK] python version: 3.11, fux 0.32.0
[OK] repo root: /root/fuxlab/demo
[OK] .fux/ writable: /root/fuxlab/demo/.fux
[OK] index not gitignored: the committed index is tracked
[OK] .fux/ layout declared: every entry is declared
[OK] accelerator: not built - `ask` uses the reference scan; run `fux build` for the fast path
# exit 0
```

## `ingest`

```console
$ fux ingest
ingested 3 docs (3 changed), 0 skipped, 3 shards written
accelerator: 78 terms, 78 blocks, 82 postings (derived, not committed)
# exit 0

$ fux ingest --no-accelerator
ingested 3 docs (0 changed), 0 skipped, 0 shards written
# exit 0

$ fux ingest --refresh-urls
error: --refresh-urls: no [sources.url] configured in /root/fuxlab/demo/fux.toml
# exit 1
```

With two unindexable files added (`docs/empty.md`, `docs/logo.png`):

```console
$ fux ingest --list-skipped
docs/empty.md: empty
docs/logo.png: binary
# exit 0

$ fux ingest
ingested 3 docs (0 changed), 2 skipped, 0 shards written
  skip docs/empty.md: empty
  skip docs/logo.png: binary
accelerator: 78 terms, 78 blocks, 82 postings (derived, not committed)
# exit 0
```

## `build`

```console
$ fux build
accelerator rebuilt from the committed index: 3 docs, 78 terms, 78 blocks, 82 postings
# exit 0
```

## `ask`

```console
$ fux ask "why did pruning fail"
1.6378  Pruning was measured and failed  (docs/pruning.md)
# exit 0

$ fux ask "index" --top 2
0.2219  The committed index format  (docs/index-format.md)
0.1937  The refer plane  (docs/refer.md)
# exit 0

$ fux ask "why did pruning fail" --explain
1.6378  Pruning was measured and failed  (docs/pruning.md)

[accelerator]
# exit 0

$ fux ask "why did pruning fail" --scan --explain
1.6378  Pruning was measured and failed  (docs/pruning.md)

[scan]
# exit 0

$ fux ask "why did pruning fail" --json
{
  "results": [
    {
      "id": "file:docs/pruning.md",
      "title": "Pruning was measured and failed",
      "loc": "docs/pruning.md",
      "score": 1.637847521978314
    }
  ]
}
# exit 0

$ fux ask "quantum tunnelling in badgers"
No confident matches.
# exit 0
```

**`--scan` and the default path returned identical rankings and identical
scores**, which is the differential law of
[ADR-ACCELERATOR](../../adr/0005_derived-accelerator.md) holding on this
fixture. Three documents is not a test of it; the law's evidence is the
[M2 run](../2026-08-12-m2-accelerator/report.md), 6 088 comparisons.

## `ask --hybrid` (default-off)

With the bundled model present:

```console
$ fux ask "why did pruning fail" --hybrid --explain
0.0328  Pruning was measured and failed  (docs/pruning.md)
0.0161  The refer plane  (docs/refer.md)
0.0159  The committed index format  (docs/index-format.md)

[hybrid]
# exit 0
```

Note the score scale changes completely — RRF scores are rank-derived and are
**not comparable** to BM25F scores. Hybrid also pulled two unrelated documents
into the result set for a query the lexical path answered with one.

**With the model bundle absent (a source install), the same command crashes:**

```console
$ fux ask "why did pruning fail" --hybrid --explain
Traceback (most recent call last):
  ...
  File ".../fux/query/hybrid.py", line 97, in _dense_ids
    vec = get_model().embed(query)
          ^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'embed'
# exit 1
```

See [`ANALYSIS.md`](ANALYSIS.md).

## `find`

```console
$ fux find "what format is the committed index"
docs/index-format.md
docs/refer.md
docs/pruning.md
# exit 0

$ fux find "what format is the committed index" --json
{
  "results": [
    {
      "id": "file:docs/index-format.md",
      "title": "The committed index format",
      "loc": "docs/index-format.md",
      "score": 1.9505698733817989
    },
    {
      "id": "file:docs/refer.md",
      "title": "The refer plane",
      "loc": "docs/refer.md",
      "score": 0.3380831805329466
    },
    {
      "id": "file:docs/pruning.md",
      "title": "Pruning was measured and failed",
      "loc": "docs/pruning.md",
      "score": 0.2588384394244381
    }
  ]
}
# exit 0
```

## `answer`

```console
$ fux answer "what is the refer plane"
The refer plane
  - The refer plane

  -- docs/refer.md

(from the index's own structure; passage-level answers arrive with the refer plane, M4)
# exit 0

$ fux answer "what is the refer plane" --json
{
  "answer": {
    "title": "The refer plane",
    "phrases": [
      "The refer plane"
    ]
  },
  "citation": {
    "id": "file:docs/refer.md",
    "loc": "docs/refer.md",
    "score": 3.209471606244869
  },
  "source": "index"
}
# exit 0

$ fux answer "quantum tunnelling in badgers"
No confident matches.
# exit 0
```

## Errors

```console
$ cd /tmp && fux ask "anything"
error: no fux.toml or .git found — run from inside a configured repo
# exit 1
```

All expected failures render as `error: <message>` on **stderr** and exit 1.
