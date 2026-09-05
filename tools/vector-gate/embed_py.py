#!/usr/bin/env python3
"""W-106 arm 2 — `sentence-transformers`, the same model, in Python.

**Not a second measurement of retrieval — a check on the FIRST one.** W-112
proposes committing pinned vectors; if two implementations of one model
disagree, a committed vector is not reproducible and the plane cannot be built
whatever the retrieval number says.

Installed in the scratch environment only. `src/fux/` never imports this and
CI never runs it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PREFIX = "Represent this sentence for searching relevant passages: "


def main() -> int:
    from sentence_transformers import SentenceTransformer

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    model_id = sys.argv[3] if len(sys.argv) > 3 else "BAAI/bge-small-en-v1.5"
    revision = sys.argv[4] if len(sys.argv) > 4 else None
    model = SentenceTransformer(model_id, revision=revision)

    chunks = model.encode([c["text"] for c in data["chunks"]], normalize_embeddings=True)
    queries = model.encode([PREFIX + q["q"] for q in data["queries"]], normalize_embeddings=True)

    import platform

    Path(sys.argv[2]).write_text(json.dumps({
        "arm": "sentence-transformers",
        "model": model_id,
        "revision": revision,
        "runtime": f"python {sys.version.split()[0]} {platform.system()}/{platform.machine()}",
        "dims": int(chunks.shape[1]),
        "chunks": [[float(x) for x in row] for row in chunks],
        "queries": [[float(x) for x in row] for row in queries],
    }), encoding="utf-8")
    print(f"{len(chunks)} chunk vectors + {len(queries)} query vectors -> {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
