# 2026-08-18 — ingest, `.fux/` and the index lifecycle: surface capture

**A surface capture, not a measurement.** No prediction is gated on it and no
threshold was pre-registered. It exists so that ADR-DOTFUX, ADR-INGEST,
ADR-URL-INGEST and ADR-INDEX-LIFECYCLE quote real artifacts rather than
described ones.

- **Version:** `fux 0.32.0` from source · Python 3.11.15, Linux (Cowork cloud
  container; the device VM is 3.10 — [`../../MACHINE.md`](../../MACHINE.md)).
- **Corpus:** [`evidence/fixture.sh`](evidence/fixture.sh) — three local
  documents, two skip cases, and three URLs served by
  [`evidence/demo-middleware.py`](evidence/demo-middleware.py) with **no
  network**, so everything here reproduces on an air-gapped machine.
- **Reproduce:** `./evidence/fixture.sh /tmp/fux-ingest-demo && cd /tmp/fux-ingest-demo`,
  then the commands in order.

---

## 1 · The `.fux/` directory as generated

`fux ingest` writes `README.md` and `.gitignore` **only if missing**, then the
planes.

```console
$ find .fux -maxdepth 2 -type d | sort
.fux
.fux/index
.fux/middleware
.fux/runtime
.fux/runtime/postings
.fux/sources

$ cat .fux/.gitignore
# Derived planes only: rebuildable from the committed index and the
# source systems. NEVER add `*` here: `.fux/index/`, `.fux/sources/` and
# `.fux/middleware/` are committed, and a blanket ignore would drop them
# from git silently. `fux doctor` checks exactly that.
runtime/
cache/

$ cat .fux/runtime/CACHEDIR.TAG
Signature: 8a477f597d28d172789f06886806bc55
# This file is a cache directory tag created by fux.
# For information about cache directory tags, see https://bford.info/cachedir/
```

The generated `README.md` carries the declaration table itself — every child
is committed or derived, and `fux doctor` warns about anything undeclared.

## 2 · A committed record, verbatim

Shard files open with a format header line, then one document per line:

```console
$ head -c 240 .fux/index/2e.jsonl
{"_format":"fux.index.v1","analyzer":"v1","tf_fields":["heading","body"]}
{"code":"MlLhv73WJJYbpSiyUpUqGlZkY-rXcOv3D1-yqmU5txU","edges":[],"id":"file:docs/refer.md","loc":"docs/refer.md","meta":"plain","mode":"extracted","phrases":["The ref
```

The full record for `docs/refer.md` (terms elided — 23 of them, each a 16-hex
key to a `[heading_tf, body_tf]` pair):

```json
{
  "code": "MlLhv73WJJYbpSiyUpUqGlZkY-rXcOv3D1-yqmU5txU",
  "edges": [],
  "id": "file:docs/refer.md",
  "loc": "docs/refer.md",
  "meta": "plain",
  "mode": "extracted",
  "phrases": ["The refer plane"],
  "sha": "45edf1e06d49727c470c6cb93542eae093ee681c",
  "src": "git",
  "terms": { "15b18d006e8a6e50": [0, 1], "3d48c93aa729e567": [1, 0], "…": [] },
  "title": "The refer plane",
  "ver": 1,
  "wlen": 28
}
```

**Shard addressing** is `blake2b(id, digest_size=1)`, verified against the
files on disk:

```console
$ python3 -c "from hashlib import blake2b
for i in ['file:docs/refer.md','file:docs/pruning.md','file:docs/index-format.md']:
    print(i,'->',blake2b(i.encode(),digest_size=1).hexdigest()+'.jsonl')"
file:docs/refer.md        -> 2e.jsonl
file:docs/pruning.md      -> 88.jsonl
file:docs/index-format.md -> e6.jsonl
```

## 3 · The derived plane

```console
$ cat .fux/runtime/manifest.json
{
  "analyzer": "v1",
  "block_size": 128,
  "blocks": 78,
  "docs": 3,
  "index_schema": "fux.index.v1",
  "schema": "fux.runtime.v1",
  "shards": {
    "2e.jsonl": "2d4f19bcd8f8af905da1103648c3df21007d3255",
    "88.jsonl": "61abfc1c7540bf7b0626fbb9de360a42496b5908",
    "e6.jsonl": "c7c7b09f882e30a96612927a3d1921c79f4e57b2"
  },
  "terms": 78
}

$ head -1 .fux/runtime/docs.jsonl
{"id":"file:docs/index-format.md","loc":"docs/index-format.md","title":"The committed index format","wlen":38}

$ head -1 .fux/runtime/postings/03.jsonl
["0344439b989e1c65",[[0,0,1]]]
```

The manifest pins a **per-shard sha of the committed bytes**, which is how
staleness is detected without re-reading the corpus.

## 4 · Update: determinism, change, deletion

**Re-ingesting an unchanged corpus produces byte-identical shards.**

```console
$ sha1sum .fux/index/*.jsonl > /tmp/before
$ fux ingest >/dev/null && sha1sum .fux/index/*.jsonl > /tmp/after
$ diff /tmp/before /tmp/after && echo IDENTICAL
IDENTICAL
```

**Editing one document touches one shard, and bumps `ver`.**

```console
$ printf '\nA sentence added on 2026-08-18 to force a change.\n' >> docs/refer.md
$ fux ingest
ingested 3 docs (1 changed), 2 skipped, 1 shards written
  skip docs/empty.md: empty
  skip docs/logo.png: binary
accelerator: 85 terms, 85 blocks, 89 postings (derived, not committed)

# the record, before -> after
{'id': 'file:docs/refer.md', 'sha': '45edf1e0…', 'ver': 1, 'wlen': 28}
{'id': 'file:docs/refer.md', 'sha': '95af0076…', 'ver': 2, 'wlen': 35}
```

**Deleting a document removes its record and its shard file.**

```console
$ rm docs/pruning.md && fux ingest
ingested 2 docs (0 changed), 2 skipped, 0 shards written
...
$ ls .fux/index/
2e.jsonl  e6.jsonl          # 88.jsonl — pruning.md's shard — is gone
```

Note the reporting: `0 shards written` is true and slightly under-informative,
since a shard was *removed*. Nothing incorrect; worth knowing when reading a
run.

## 5 · Staleness is detected and reported honestly

After a build failure (§6) the runtime holds an out-of-date accelerator. The
engine does **not** answer from it silently:

```console
$ fux ask "who carries the pager" --explain
3.0934  30aef0c52cf11116  (https://example.invalid/handbook/oncall)

[scan]

$ fux doctor
...
[OK] accelerator: stale (the committed index changed since it was built) - `ask` falls back to the scan; run `fux build`
```

This was checked specifically because a stale-derived-plane read would be a
serious defect. It is handled correctly: the manifest's per-shard shas catch
the drift, `ask` falls back to the reference path, and `--explain` and
`doctor` both say so.

## 6 · URL ingestion

Offline is the default — a plain `fux ingest` never loads the middleware:

```console
$ fux ingest
ingested 2 docs (0 changed), 2 skipped, 0 shards written
```

`--refresh-urls` is the only path that does:

```console
$ fux ingest --refresh-urls
  [middleware] configure({'greeting': 'hello'})
  [middleware] connect()
  [middleware] close()
ingested 4 docs (2 changed), 3 skipped, 2 shards written
  skip docs/empty.md: empty
  skip docs/logo.png: binary
  skip https://example.invalid/gone: fetch failed: 404 not found
```

`configure` receives `[sources.url.config]` verbatim; `connect`/`close` bracket
the batch; a failed page becomes a **skip**, not a crash.

**With `meta = "plain"` this completes and the accelerator builds:**

```console
$ fux ingest --refresh-urls          # meta = "plain"
accelerator: 70 terms, 70 blocks, 74 postings (derived, not committed)
# exit 0
$ fux ask "who carries the pager" --explain
3.0934  Oncall handbook  (https://example.invalid/handbook/oncall)

[accelerator]
```

**With `meta = "hashed"` — the default — it fails:**

```console
$ fux ingest --refresh-urls          # meta = "hashed"
error: …/.fux/index/aa.jsonl:2: the quoted 16-hex token '30aef0c52cf11116'
appears outside `terms` in record 'url:https://example.invalid/handbook/oncall'.
`query/scan.py` counts it toward that term's df from the raw bytes, and the
accelerator counts from the postings, so the two paths would score this corpus
differently. Refusing to build a divergent accelerator.
# exit 1
```

The committed index is written; only the accelerator is refused, and every
subsequent `fux build` refuses too. See [`ANALYSIS.md`](ANALYSIS.md).

The hashed record, for reference — note `title_h` and the absence of `title`
and `phrases`:

```json
{
  "id": "url:https://example.invalid/handbook/oncall",
  "loc": "https://example.invalid/handbook/oncall",
  "meta": "hashed",
  "mode": "extracted",
  "sha": "2643f1afb68339f2f808d85f67aad193b820dd86",
  "src": "url",
  "title_h": "30aef0c52cf11116",
  "ver": 1,
  "wlen": 11
}
```
