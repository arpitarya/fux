# Relational eval pairs

`pairs.jsonl` measures *retrieval* (question → passage). `relational.jsonl`
measures the **graph surfaces** added in phase 4 — `explain`, `graph`, `path` —
which retrieval metrics cannot see at all.

It runs against `relational/`, a deliberately small linked corpus rather than
the main fixture. The main fixture has **no links whatsoever**, which is why
the M6 graph-in-RRF measurement could not discriminate: with no edges, PPR
expansion has nothing to walk. Adding links there would shift every document
frequency and invalidate the committed goldens, so the graph fixture is kept
separate.

Entry kinds:

| kind | asserts |
|------|---------|
| `path` | a route exists `from`→`to` within `hops`, first hop of kind `expect` |
| `nopath` | no route exists — honest emptiness is a behaviour worth pinning |
| `neighbour` | `fux explain <doc>` lists exactly these edge targets |
| `graph` | `fux graph "<query>"` surfaces `expect_node` |

Run: `uv run pytest tests_e2e/test_relational.py`
