# Relational eval pairs — the graph lane's instrument

Retrieval metrics (hit@k, MRR) are **blind** to `explain`, `graph` and `path`:
they score passages, and these verbs return relationships. `relational.jsonl`
is the instrument for those.

It runs against `relational/`, a deliberately small linked corpus rather than
the main fixture. The main fixture has **no links whatsoever**, which is why a
graph measurement on it cannot discriminate: with no edges, PPR expansion has
nothing to walk. Adding links there would shift every document frequency and
invalidate the committed goldens, so the graph fixture is kept separate.

| kind | asserts |
|------|---------|
| `path` | a route exists `from`→`to` within `hops`, first hop of kind `expect` |
| `nopath` | no route exists — honest emptiness is a behaviour worth pinning |
| `neighbour` | `fux explain <doc>` lists exactly these edge targets |
| `graph` | `fux graph "<query>"` surfaces `expect_node` |

Run: `uv run pytest tests_e2e/test_relational.py`

## Ported from `archive/v0.26/`, with one adaptation — stated, not hidden

The corpus is **byte-identical** to the archived fixture and the seven cases
are the archived cases. Two things were adapted, and neither weakens what the
eval measures:

1. **The edge vocabulary.** The archived engine classified a markdown link as
   `references` or `cites` depending on the heading it sat under. This build's
   extractor (`ingest/edges.py`) emits `ref` / `tag` / `code` and makes no
   such distinction, so the two `expect` values become `ref`. Restoring the
   distinction would be a **new edge kind**, which is a decision needing its
   own record — not something a port may smuggle in.

2. **Targets are full doc ids.** `explain` reports `file:docs/rota-oncall.md`
   where the archived verb reported `docs/rota-oncall.md`, because a doc id in
   this build carries its source scheme (`file:` / `url:`) and a bare path
   would be ambiguous the moment a URL source is configured.

**What is *not* adapted is the substance**: the same routes must exist, the
same route must be absent, the same neighbours must be listed exactly, the
same node must surface, the output must be byte-stable across runs, and
reliability must decay with distance.
