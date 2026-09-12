#!/usr/bin/env python3
"""Build the two adversarial documents W-107's hazards H1 and H2 require.

**These are NEVER committed into a real index.** The harness writes them into a
throwaway copy of a corpus, because the hazards they probe are invisible on
ordinary data — H1 needs two documents whose scores tie exactly AND whose ids
straddle U+FFFF, and no real corpus has been written to contain one.

    python tools/differential/adversarial_corpus.py <corpus-root>
"""
from __future__ import annotations

import pathlib
import sys

#: The corpus the documents are written into — an argument, and never where
#: the engine is imported from. Both were `sys.argv[1]` until 2026-09-12, which
#: meant this script could only ever run on the fux checkout itself.
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
ENGINE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ENGINE / "src"))

from fux.store.canonical import canonical_dumps  # noqa: E402
from fux.store.format import shard_for, term_hash  # noqa: E402

HEADER = (
    b'{"_format":"fux.index.v2","analyzer":"v2",'
    b'"tf_fields":["body","heading","title","path","ctx"]}\n'
)


def _doc(doc_id: str, loc: str, title: str, phrases: list[str], body: dict[str, int]) -> dict:
    return {
        "archived": False, "edges": [], "flen": [sum(body.values()), 0, 2, 2],
        "id": doc_id, "loc": loc, "meta": "plain", "mode": "extracted",
        "mtime": 1788000000, "phrases": phrases, "sha": "0" * 40, "src": "git",
        "terms": {term_hash(t): [c] for t, c in body.items()}, "title": title,
    }


def documents() -> list[dict]:
    # H1 — identical scores, so the tie-break alone decides the order, and ids
    # that straddle the BMP boundary, where UTF-16 and code-point order differ.
    tie = {"zzqq": 3}
    return [
        _doc("file:h1-a.md", "h1-a.md", "ascii id", ["H1 ascii"], tie),
        _doc("file:h1-\ue000.md", "h1-\ue000.md", "pua id", ["H1 pua"], tie),
        _doc("file:h1-\ufffd.md", "h1-\ufffd.md", "bmp id", ["H1 bmp"], tie),
        _doc("file:h1-\U0001F600.md", "h1-\U0001F600.md", "emoji id", ["H1 emoji"], tie),
        _doc("file:h1-\U0002A6B2.md", "h1-\U0002A6B2.md", "cjk ext", ["H1 cjk"], tie),
        # H2 — non-ASCII in title and headings. Python prints `--json` with
        # `ensure_ascii=True` and `JSON.stringify` does not, so this is the
        # document that proves the comparison is on PARSED values.
        _doc(
            "file:h2-nonascii.md", "h2-nonascii.md",
            "Em\u2014dash, caf\u00e9, \u4e2d\u6587 and a \U0001F600",
            ["Heading with \u2014 and \u4e2d\u6587", "na\u00efve caf\u00e9"],
            {"zzqq": 3, "nonascii": 5},
        ),
    ]


def install(root: pathlib.Path) -> int:
    by_shard: dict[str, list[dict]] = {}
    for d in documents():
        by_shard.setdefault(shard_for(d["id"]), []).append(d)
    for shard, records in by_shard.items():
        path = root / ".fux" / "index" / f"{shard}.jsonl"
        data = path.read_bytes() if path.exists() else HEADER
        for record in records:
            data += canonical_dumps(record)
        path.write_bytes(data)
    return sum(len(v) for v in by_shard.values())


if __name__ == "__main__":
    print(f"installed {install(ROOT)} adversarial documents into {ROOT}/.fux/index/")
