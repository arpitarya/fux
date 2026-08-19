# 2026-08-18 — `ask` / `find` / `answer`: surface capture

**A surface capture, not a measurement.** No prediction is gated on it and no
threshold was pre-registered. It exists so [ADR-ASK](../../../docs/adr/0004_ask.md),
[ADR-FIND](../../../docs/adr/0005_find.md) and
[ADR-ANSWER](../../../docs/adr/0006_answer.md) quote real output rather than
described output.

- **Version:** `fux 0.32.0` from source · Python 3.11.15, Linux (Cowork cloud
  container — the device VM is 3.10, see [`../../MACHINE.md`](../../MACHINE.md)).
- **Corpus:** the fixture from
  [`../2026-08-18-ingest-and-index/evidence/fixture.sh`](../2026-08-18-ingest-and-index/evidence/fixture.sh)
  with `meta = "plain"`, so the accelerator builds (see
  [W-47](../../../archive/open/W-47-hashed-meta-blocks-accelerator.md) for why `hashed`
  cannot). Five records: three local documents, two URL documents.
- **Reproduce:** run the fixture, `fux ingest --refresh-urls`, then the commands
  below in order.

---

## 1 · The flag surface

```console
$ fux ask --help
usage: fux ask [-h] [--json] [--scan] [--top N] [--explain] [--hybrid] query

$ fux find --help
usage: fux find [-h] [--json] [--scan] [--top N] query

$ fux answer --help
usage: fux answer [-h] [--json] [--scan] query
```

| flag | `ask` | `find` | `answer` |
|---|---|---|---|
| `--json` | yes | yes | yes |
| `--scan` | yes | yes | yes |
| `--top N` | yes (default 5) | yes (default 5) | **no** — forced to 1 |
| `--explain` | yes | no | no |
| `--hybrid` | yes | **no** | **no** |

## 2 · `ask`

```console
$ fux ask "index format canonical" --top 3
4.0239  The committed index format  (docs/index-format.md)
0.6807  The refer plane  (docs/refer.md)
0.4647  Pruning was measured and failed  (docs/pruning.md)
# exit 0

$ fux ask "why did pruning fail" --explain
2.1973  Pruning was measured and failed  (docs/pruning.md)

[accelerator]
# exit 0
```

```console
$ fux ask "index format canonical" --json
{
  "results": [
    {
      "id": "file:docs/index-format.md",
      "title": "The committed index format",
      "loc": "docs/index-format.md",
      "score": 4.0238871954264575
    },
    {
      "id": "file:docs/refer.md",
      "title": "The refer plane",
      "loc": "docs/refer.md",
      "score": 0.6806662758497379
    },
    {
      "id": "file:docs/pruning.md",
      "title": "Pruning was measured and failed",
      "loc": "docs/pruning.md",
      "score": 0.4646740604430886
    }
  ]
}
```

## 3 · The differential law, demonstrated

The accelerator and the reference scan, same query, **byte-identical** — floats
included:

```console
$ diff <(fux ask "index format canonical" --json --top 5) \
       <(fux ask "index format canonical" --json --top 5 --scan) && echo IDENTICAL
IDENTICAL
```

## 4 · `--hybrid` is a different ranking

RRF scores, and two URL documents that lexical scoring did not surface at all
on this corpus:

```console
$ fux ask "index format canonical" --hybrid --explain
0.0328  The committed index format  (docs/index-format.md)
0.0323  The refer plane  (docs/refer.md)
0.0313  Pruning was measured and failed  (docs/pruning.md)
0.0159  Oncall handbook  (https://example.invalid/handbook/oncall)
0.0156  Deploy handbook  (https://example.invalid/handbook/deploys)

[hybrid]
```

**This is not evidence that hybrid is better.** Five documents, one query. The
measured verdict is net −6 on the graded corpus
([`../2026-08-12-m2-accelerator/`](../2026-08-12-m2-accelerator/report.md)),
which is why it ships default-off. Recorded here only to show that the flag
changes the ranking rather than refining it.

## 5 · `find`

```console
$ fux find "index format canonical" --top 3
docs/index-format.md
docs/refer.md
docs/pruning.md
# exit 0
```

Same query through `ask` — **identical ranking**, more prose:

```console
$ fux ask "index format canonical" --top 3
4.0239  The committed index format  (docs/index-format.md)
0.6807  The refer plane  (docs/refer.md)
0.4647  Pruning was measured and failed  (docs/pruning.md)
```

**`--json` is not terse** — it is the full result object, identical to
`ask --json`:

```console
$ fux find "index format canonical" --json
{
  "results": [
    {
      "id": "file:docs/index-format.md",
      "title": "The committed index format",
      "loc": "docs/index-format.md",
      "score": 4.0238871954264575
    },
    ...
  ]
}
```

## 6 · `answer`

```console
$ fux answer "why did pruning fail"
Pruning was measured and failed
  - Pruning was measured and failed

  -- docs/pruning.md

(from the index's own structure; passage-level answers arrive with the refer plane, M4)
# exit 0
```

```console
$ fux answer "index format canonical" --json
{
  "answer": {
    "title": "The committed index format",
    "phrases": [
      "The committed index format"
    ]
  },
  "citation": {
    "id": "file:docs/index-format.md",
    "loc": "docs/index-format.md",
    "score": 4.0238871954264575
  },
  "source": "index"
}
```

The title and the only phrase are the same string — the index being honest
about a three-line document, and precisely what M4 changes.

## 7 · No confident match

All three verbs, same behaviour, **exit 0**:

```console
$ fux ask "zzz nonexistent term"
No confident matches.
$ fux find "zzz nonexistent term"
No confident matches.
$ fux answer "zzz nonexistent term"
No confident matches.
```

```console
$ fux ask "zzz nonexistent term" --json
{
  "results": []
}

$ fux answer "zzz nonexistent term" --json
{
  "answer": null,
  "citation": null
}
```

Note the asymmetry: the `answer` no-match object has **no `"source"` key**,
while the hit case does. See [`ANALYSIS.md`](ANALYSIS.md).
