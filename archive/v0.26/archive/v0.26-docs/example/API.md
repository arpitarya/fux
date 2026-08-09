# Python API — create a file in the corpus from a script

*Fux is a CLI, but the same engine is importable. This shows another script
creating a source document, ingesting it into the corpus, and querying it back —
all in-process, `$0`, offline, deterministic. Every code block below was run
against a scratch corpus (v0.23.x); the outputs are real.*

The whole surface you need is three modules:

| Import | What it gives you |
|--------|-------------------|
| `fux.config` | `find_root(start)` → the dir holding `fux.toml`; `load(root)` → a `Config` |
| `fux.ingest` | `ingest_paths(config, *, build_index=True, web=False)` → `IngestReport` |
| `fux.index` | `load_searcher(config)` → a `Searcher`; `.search(query, top=N)` → results |

- These are the exact entrypoints the CLI and the Claude Code hook call — no
  private hooks, no second code path.
- Everything raises `FuxError` (from `fux.errors`) for expected failures; catch
  it at your script's boundary, like the CLI's `main` does.

---

## The script

`make_and_query.py` — create a decision record, ingest, then ask about it:

```python
from pathlib import Path

from fux.config import load, find_root
from fux.ingest import ingest_paths
from fux.index import load_searcher

root = find_root(Path("."))       # walk up to the fux.toml
config = load(root)               # -> Config (raises FuxError if none)

# 1. Create a new source document inside a configured docs folder.
doc = root / "docs" / "decisions" / "0009-cache-ttl.md"
doc.parent.mkdir(parents=True, exist_ok=True)
doc.write_text(
    "---\ntype: ADR\ntitle: Crawled pages expire after 30 days\n---\n\n"
    "# Cache TTL\n\n"
    "Fux expires crawled web pages after 30 days; re-ingest refetches them.\n",
    encoding="utf-8",
)

# 2. Re-ingest. Incremental by sha: only new/changed files are converted,
#    and the index + committed state plane update in the same call.
report = ingest_paths(config)
print(f"new={report.new} updated={report.updated} "
      f"unchanged={report.unchanged} chunks={report.chunk_count}")

# 3. Query it back through the same ranker the CLI uses.
searcher = load_searcher(config)
for r in searcher.search("how long are crawled pages kept?", top=3):
    loc = f"{r.file}:{r.start}-{r.end}" if r.start is not None else r.file
    print(f"{r.score:.3f}  {loc}  · {r.heading}")
```

### Output — first run (fresh corpus, one seed doc already present)

```
new=2 updated=0 unchanged=0 chunks=2
2.198  docs/decisions/0009-cache-ttl.md:6-8  · Cache TTL
```

### Output — run it again (nothing changed)

Ingest is idempotent: identical bytes → no rewrite, everything `unchanged`:

```
new=0 updated=0 unchanged=2 chunks=2
2.198  docs/decisions/0009-cache-ttl.md:6-8  · Cache TTL
```

Edit the file and re-run and you'd see `new=0 updated=1 unchanged=1` — only the
touched document is re-converted and re-indexed.

---

## What the objects carry

**`IngestReport`** (from `ingest_paths`) — the counters you'll usually read:

| Field | Meaning |
|-------|---------|
| `new` / `updated` / `unchanged` | Per-file disposition this run (`total` sums them) |
| `chunk_count` | Chunks in the rebuilt index |
| `skipped` | `[(rel, reason), …]` — binary, missing extras, unknown ext |
| `removed` | Source files that disappeared since last ingest |
| `warnings` | e.g. a configured source folder that wasn't found |

**`ScoredChunk`** (from `Searcher.search`) — one ranked passage:

| Field | Meaning |
|-------|---------|
| `file` | Document id (POSIX-relative), the citation path |
| `start` / `end` | Source line span (`None` for synthetic bodies) |
| `heading` | Heading path of the chunk |
| `text` | The passage text |
| `score` | BM25F (or fused) score, higher = better |
| `ordinal` | Chunk index within its file |

For the fused hybrid view and per-term explain detail, prefer the CLI's
`fux ask --json` / `--explain` (see [CLI.md](CLI.md)) — the JSON adds `fidelity`,
`heading_path`, and the `hybrid` fusion block on top of these fields.

---

## Notes for embedding Fux in a script

- **Locate, don't hardcode.** `find_root(Path("."))` walks up to the `fux.toml`,
  so the script works from any subdirectory; `find_root` raises `FuxError` if
  there's no config (run `fux setup` first).
- **`build_index=True` is the default** — pass `build_index=False` to convert
  the cache without rebuilding the index (rare; useful when batching).
- **Web crawling is fenced.** `ingest_paths(config, web=True)` also crawls
  `[sources.web]`; it never runs unless you ask, and never on the query path.
- **Determinism holds through the API.** Same sources → byte-identical cache,
  manifest, and index; no wall-clock output. The API is as reproducible as the
  CLI because it *is* the CLI's code.
- **No model calls, ever.** `load_searcher` uses the bundled static-embedding
  model for the dense stage only; nothing reaches the network or an LLM.

---

## Related

[CLI.md](CLI.md) (the same operations as commands, with `--json` shapes) ·
[SETUP.md](SETUP.md) (what writes the `fux.toml` this script loads) ·
[TOML.md](TOML.md) (the config `load()` parses) · shipped entrypoints:
[`../../src/fux/ingest/__init__.py`](../../src/fux/ingest/__init__.py),
[`../../src/fux/index/__init__.py`](../../src/fux/index/__init__.py).
