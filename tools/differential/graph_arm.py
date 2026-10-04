#!/usr/bin/env python3
"""N2: Node's in-memory graph plane against Python's `graph.json` bytes.

W-107 Phase 3. **Node does not read Python's `.fux/runtime/graph.json` here** —
both sides rebuild the same graph from the same records, and the digests must be
equal. Reading the derived file instead would prove nothing about whether the two
implementations agree.

⚠ **Since W-259 (2026-10-04) the Node READER does read that file when it is
fresh** (`graph/plane.mjs::planeFor`). This arm calls `buildPlane` directly, so
it never reaches the read, and it still starts Node with `FUX_GRAPH_REBUILD=1`
(`[env] graph_rebuild`) so that a later edit routing the snippet through
`planeFor` cannot quietly turn N2 into Python against Python.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

#: This checkout — the engine under test. **Never the corpus**: a golden rung
#: is a repo of documents with no `src/`, and reading the engine out of the
#: corpus is what kept this arm from running on one.
ENGINE = Path(__file__).resolve().parents[2]
NODE_DIR = ENGINE / "node"

sys.path.insert(0, str(ENGINE / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rungs  # noqa: E402
from fux.constants import fixed  # noqa: E402
from fux.graph import community as community_mod  # noqa: E402
from fux.graph import plane as plane_mod  # noqa: E402
from fux.graph.model import Graph, edges_from_records  # noqa: E402
from fux.store import reader  # noqa: E402

NODE_SNIPPET = """
const fs = require('fs');
import('%s').then(({buildPlane, planeBytes}) => {
  const records = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
  process.stdout.write(planeBytes(buildPlane(records)));
});
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus", nargs="?", default=None,
                    help="the repo whose index both readers read (default: .)")
    ap.add_argument("--rung", help=f"a golden-ladder rung: {', '.join(rungs.rung_names())}")
    ap.add_argument("--skip-document-verify", action="store_true")
    args = ap.parse_args()
    if args.rung and args.corpus:
        ap.error("--rung and a corpus path are two ways to say the same thing; pass one")
    if args.rung:
        try:
            root = rungs.resolve(args.rung, verify_documents=not args.skip_document_verify)
        except rungs.RungError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        print(f"rung         : {args.rung} at {root} (manifest verified)")
    else:
        root = Path(args.corpus or ".").resolve()
        print(f"corpus       : {root}")

    records: list[dict] = []
    for path in reader.iter_shard_paths(root):
        _, recs = reader.read_shard(path)
        records.extend(recs)
    if not records:
        print("no records — nothing to compare")
        return 0

    graph = Graph(edges_from_records(records))
    communities = community_mod.assign(graph)
    payload = {
        "schema": plane_mod.SCHEMA,
        "edges": [[e.src, e.kind, e.dst, e.grade] for e in graph.edges],
        "communities": {node: communities[node] for node in sorted(communities)},
    }
    py_text = json.dumps(payload, indent=None, sort_keys=False, separators=(",", ":")) + "\n"

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(records, handle)
        records_path = handle.name

    proc = subprocess.run(
        # A file:// URL, not a path. `as_posix()` yields `D:/a/...` on Windows,
        # and Node reads the drive letter as a URL scheme:
        # ERR_UNSUPPORTED_ESM_URL_SCHEME, protocol 'd:'.
        ["node", "-e", NODE_SNIPPET % (NODE_DIR / "src" / "graph" / "plane.mjs").as_uri(), records_path],
        capture_output=True, text=True, encoding="utf-8",
        env=dict(os.environ, **{fixed("env", "graph_rebuild"): "1"}),
    )
    if proc.returncode != 0:
        print(f"node exited {proc.returncode}: {proc.stderr.strip()}")
        return 1
    nd_text = proc.stdout

    py_digest = hashlib.sha256(py_text.encode("utf-8")).hexdigest()
    nd_digest = hashlib.sha256(nd_text.encode("utf-8")).hexdigest()

    print(f"records      : {len(records)}")
    print(f"nodes/edges  : {len(graph.nodes)} / {len(graph.edges)}")
    print(f"communities  : {len(set(communities.values()))}")
    print(f"python digest: {py_digest}")
    print(f"node digest  : {nd_digest}")
    if py_digest == nd_digest:
        print("N2           : IDENTICAL")
        return 0

    print("N2           : DISCORDANT")
    # Name the first differing byte rather than printing two 10 MB blobs.
    for i, (a, b) in enumerate(zip(py_text, nd_text)):
        if a != b:
            lo = max(0, i - 60)
            print(f"  first difference at byte {i}:")
            print(f"    python …{py_text[lo:i + 60]!r}")
            print(f"    node   …{nd_text[lo:i + 60]!r}")
            break
    else:
        print(f"  identical prefix; lengths {len(py_text)} vs {len(nd_text)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
