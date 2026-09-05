#!/usr/bin/env python3
"""W-106 — dump what gets embedded: the corpus's chunks, and the queries.

**This is the only file here that imports fux, and it imports the CHUNKER.**
`fux.refer._chunk.chunk` is what `answer` cites and what `rerank.boost` scores,
so a dense lane that chunked differently would be measuring a corpus fux does
not have. One chunker, the same argument `refer/_rescore.py` makes for one
scorer.

⚠ **Nothing under `tools/` is ever imported by `src/fux/`.** The import fence
(`tests/test_import_fence.py`) runs the other way and stays green: this reads
fux, fux never reads this. No embedder is installed by the runtime, and the two
that are installed here live in the scratch environment, never in CI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fux.refer._chunk import chunk  # noqa: E402


def main() -> int:
    corpus = Path(sys.argv[1])
    goldens = Path(sys.argv[2])
    out = Path(sys.argv[3])

    docs = sorted(p for p in (corpus / "docs").rglob("*.md"))
    chunks = []
    for path in docs:
        text = path.read_text(encoding="utf-8")
        loc = str(path.relative_to(corpus))
        for passage in chunk(text):
            chunks.append({
                "doc": loc,
                "ordinal": passage.ordinal,
                "heading": passage.heading,
                # The heading is prepended because it is the passage's own
                # field in `_rescore._terms_of` too -- dropping it here would
                # embed less than fux scores.
                "text": (f"{passage.heading}\n\n{passage.text}" if passage.heading else passage.text),
            })

    queries = [json.loads(line) for line in goldens.read_text(encoding="utf-8").splitlines() if line.strip()]

    out.write_text(json.dumps({
        "chunks": chunks,
        "queries": [{"id": q["id"], "q": q["q"]} for q in queries],
    }, indent=1), encoding="utf-8")
    print(f"{len(docs)} documents -> {len(chunks)} chunks, {len(queries)} queries -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
