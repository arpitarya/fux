#!/usr/bin/env python3
"""Graph-plane cost profile — where the time goes in the M3 lane at scale.

Not a gate. No threshold is pre-registered here and none is adjudicated: this
is a profile in the sense of `work/regression/2026-08-20-ingest-cost-profile/`,
filed so a fork can be argued against numbers instead of intuition.

Run from the repo root:

    uv run python tools/graph-bench/profile.py 10000 50000 100000

It imports the real `fux.graph` modules — `model`, `community`, `walk` — so the
numbers are the engine's, not a re-implementation's. The corpus is synthetic
(see `corpus()`); the shape it assumes is stated in the report and is the
single largest caveat on every number below.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

from fux.graph import community
from fux.graph.model import Edge, Graph
from fux.graph.walk import ppr, routes

#: Edges per document. 8 `ref` + 3 `tag` is the shape this profile assumes and
#: is NOT measured from a real corpus — it is the profile's biggest caveat.
REFS_PER_DOC = 8
TAGS_PER_DOC = 3
#: One tag per 200 documents, so a tag is a hub of ~200 members. Hub degree is
#: what decides whether a walk stays local, so it is a parameter, not a detail.
DOCS_PER_TAG = 200
#: Reference locality: a document links within +/- this many ids. Real corpora
#: cluster; a uniform-random corpus is measured separately as the worse case.
REF_SPAN = 400


def corpus(n_docs: int, *, span: int | None = REF_SPAN, seed: int = 7) -> list[Edge]:
    rng = random.Random(seed)
    n_tags = max(1, n_docs // DOCS_PER_TAG)
    docs = [f"file:docs/d{i:07d}.md" for i in range(n_docs)]
    tags = [f"tag:t{i:05d}" for i in range(n_tags)]
    edges: list[Edge] = []
    for i, doc in enumerate(docs):
        for _ in range(REFS_PER_DOC):
            j = rng.randrange(n_docs) if span is None else min(n_docs - 1, max(0, i + rng.randint(-span, span)))
            if j != i:
                edges.append(Edge(doc, "ref", docs[j], 10))
        for _ in range(TAGS_PER_DOC):
            edges.append(Edge(doc, "tag", tags[rng.randrange(n_tags)], 10))
    return edges


def _payload(graph: Graph, labels: dict[str, str]) -> str:
    """Byte-for-byte what `graph/plane.py::build_plane` writes today."""
    return json.dumps(
        {
            "schema": "fux.graph.v1",
            "edges": [[e.src, e.kind, e.dst, e.grade] for e in graph.edges],
            "communities": {n: labels[n] for n in sorted(labels)},
        },
        separators=(",", ":"),
    ) + "\n"


def run(n_docs: int, out: Path) -> None:
    edges = corpus(n_docs)
    print(f"\n=== {n_docs:,} documents · {len(edges):,} edges ===")

    # --- today: build ---
    t = time.perf_counter(); graph = Graph(edges); t_adj = time.perf_counter() - t
    t = time.perf_counter(); labels = community.assign(graph); t_lpa = time.perf_counter() - t
    t = time.perf_counter(); text = _payload(graph, labels); t_ser = time.perf_counter() - t
    plane = out / "graph.json"; plane.write_text(text, encoding="utf-8")
    print(f"BUILD (today)   adjacency {t_adj:6.2f}s  LPA {t_lpa:6.2f}s  serialize {t_ser:6.2f}s"
          f"  total {t_adj + t_lpa + t_ser:6.2f}s  file {len(text)/1e6:6.1f} MB")

    # --- today: load, exactly as plane.load() does it ---
    t = time.perf_counter(); raw = plane.read_text(encoding="utf-8"); t_read = time.perf_counter() - t
    t = time.perf_counter(); doc = json.loads(raw); t_parse = time.perf_counter() - t
    t = time.perf_counter(); rebuilt = [Edge(s, k, d, g) for s, k, d, g in doc["edges"]]; t_lift = time.perf_counter() - t
    t = time.perf_counter(); g2 = Graph(rebuilt); t_graph = time.perf_counter() - t
    t_load = t_read + t_parse + t_lift + t_graph
    print(f"LOAD  (today)   read {t_read:6.2f}s  json.loads {t_parse:6.2f}s  Edge() {t_lift:6.2f}s"
          f"  Graph() {t_graph:6.2f}s  TOTAL {t_load:6.2f}s  <- paid per CLI invocation")

    # --- the answers themselves, once loaded ---
    mid = n_docs // 2
    seeds = [f"file:docs/d{i:07d}.md" for i in range(mid, mid + 5)]
    t = time.perf_counter(); scores = ppr(g2, seeds); t_ppr = time.perf_counter() - t
    t = time.perf_counter(); g2.out_edges(seeds[0]); t_explain = time.perf_counter() - t
    t = time.perf_counter(); routes(g2, seeds[0], f"file:docs/d{mid+100:07d}.md", hops=3); t_path = time.perf_counter() - t
    print(f"ANSWER          explain {t_explain*1000:6.2f}ms  PPR {t_ppr:6.3f}s (touched {len(scores):,})"
          f"  path(3) {t_path*1000:6.2f}ms")

    # --- how much adjacency a walk actually needs ---
    mass = set(seeds); fetches = 0
    for _ in range(3):
        fetches += len(mass)
        nxt = set(mass)
        for node in mass:
            nxt.update(d for d, _ in g2.neighbours(node))
        mass = nxt
    print(f"REACH           a seek-based PPR needs {fetches:,} adjacency fetches"
          f"; the walk lands on {len(mass):,} nodes ({100*len(mass)/len(g2.nodes):.1f}% of corpus)")

    # --- option B: node-major records + an offset index ---
    t = time.perf_counter()
    offsets: dict[str, list[int]] = {}
    pos = 0
    nm = out / "graph.jsonl"
    with nm.open("wb") as fh:
        for node in g2.nodes:
            line = json.dumps(
                {"n": node, "e": [[e.kind, e.dst, e.grade] for e in g2.out_edges(node)], "c": labels[node]},
                separators=(",", ":"),
            ).encode() + b"\n"
            offsets[node] = [pos, len(line)]; pos += len(line); fh.write(line)
    idx = out / "graph.idx"
    idx.write_text(json.dumps(offsets, separators=(",", ":")), encoding="utf-8")
    t_write_b = time.perf_counter() - t
    t = time.perf_counter()
    loaded = json.loads(idx.read_text(encoding="utf-8"))
    with nm.open("rb") as fh:
        p, ln = loaded[seeds[0]]; fh.seek(p); json.loads(fh.read(ln))
    t_explain_b = time.perf_counter() - t
    t = time.perf_counter()
    with nm.open("rb") as fh:
        for node in list(loaded)[:fetches]:
            p, ln = loaded[node]; fh.seek(p); json.loads(fh.read(ln))
    t_seeks = time.perf_counter() - t
    print(f"OPTION B        write {t_write_b:6.2f}s  file {nm.stat().st_size/1e6:6.1f} MB"
          f" + idx {idx.stat().st_size/1e6:5.1f} MB   explain {t_explain_b:6.2f}s"
          f"  graph {t_explain_b + t_seeks + t_ppr:6.2f}s ({fetches:,} seeks in {t_seeks:.2f}s)")

    # --- option C: communities only ---
    t = time.perf_counter()
    ctext = json.dumps({"schema": "fux.graph.v2", "communities": {n: labels[n] for n in sorted(labels)}},
                       separators=(",", ":")) + "\n"
    cf = out / "communities.json"; cf.write_text(ctext, encoding="utf-8"); t_ser_c = time.perf_counter() - t
    t = time.perf_counter(); json.loads(cf.read_text(encoding="utf-8")); t_load_c = time.perf_counter() - t
    print(f"OPTION C        serialize {t_ser_c:6.2f}s  file {len(ctext)/1e6:6.1f} MB  load {t_load_c:6.2f}s"
          f"   (edges then come from the committed shards — unmeasured here)")


if __name__ == "__main__":
    sizes = [int(a) for a in sys.argv[1:]] or [10000, 50000, 100000]
    out = Path(os.environ.get("FUX_GRAPH_BENCH_OUT", "/tmp/fux-graph-bench"))
    out.mkdir(parents=True, exist_ok=True)
    print(f"python {sys.version.split()[0]} · output {out}")
    for n in sizes:
        run(n, out)
