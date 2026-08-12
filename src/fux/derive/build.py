"""Build the derived T1 accelerator from the committed shards alone.

Reads `.fux/index/*.jsonl`, writes `.fux/runtime/`. Nothing else is an input —
that is the DoD ("rebuilds deterministically from committed bytes only") and
the reason the accelerator can be deleted at any moment without loss.

## The two build-time invariants, and why they fail the build loudly

`query/scan.py` is the oracle the accelerator must reproduce byte-for-byte,
and it derives its statistics from **raw bytes**, not from the parsed record:

- `df[h]` counts a document if `"<hash>"` appears anywhere on its line.
- `total_wlen` sums the first `"wlen":N` the regex finds on the line.

The accelerator derives the same numbers from the parsed record. These agree
only if no quoted 16-hex token ever appears outside `terms`, and if the regex
`wlen` is always the record's `wlen`. Both are true today and neither is
guaranteed by the schema — a document titled `deadbeefdeadbeef` would break
the first, silently, by inflating one term's `df` on the scan side only.

So the build **asserts both, per record, and refuses to build** when either
fails. That is the same discipline as the term-hash collision check in
`store/collisions.py`: a loud build failure beats a one-in-a-million ranking
divergence that no test would ever catch.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .. import store as store_mod
from ..errors import FuxError
from ..query.bm25f import BODY_WEIGHT, HEADING_WEIGHT
from ..store import fuxdir
from . import dense
from . import format as fmt

_QUOTED_HASH_RE = re.compile(rb'"([0-9a-f]{16})"')
_WLEN_RE = re.compile(rb'"wlen":(\d+)')

# The weights are floats in bm25f.py but are whole numbers, so a block's max
# weighted tf is an exact integer — which is what lets `mx` be a u32 and the
# compare doc's "mx is an integer" rule hold without rounding anywhere.
_HEADING_W = int(HEADING_WEIGHT)
_BODY_W = int(BODY_WEIGHT)
if _HEADING_W != HEADING_WEIGHT or _BODY_W != BODY_WEIGHT:  # pragma: no cover - guards a future edit
    raise AssertionError("BM25F field weights must be whole numbers for integer mx")


@dataclass
class BuildReport:
    docs: int
    terms: int
    blocks: int
    postings: int
    bytes_written: int


def build(root: Path) -> BuildReport:
    """Materialize `.fux/runtime/` from the committed index."""
    docs, codes, postings, stats, shard_stamp = _read_committed(root)

    directory = fuxdir.derived_dir(root, fmt.RUNTIME_DIR)
    postings_directory = directory / fmt.POSTINGS_DIR
    postings_directory.mkdir(parents=True, exist_ok=True)
    _clear(postings_directory)

    written = 0
    written += _write_docs(directory, docs)
    written += _write_json(directory / fmt.STATS_NAME, stats)
    written += dense.build_codes(directory, docs, codes)

    blocks, postings_count = _write_postings(root, postings, [d["wlen"] for d in docs])

    written += _write_json(
        directory / fmt.MANIFEST_NAME,
        {
            "schema": fmt.RUNTIME_SCHEMA,
            "index_schema": store_mod.SCHEMA_ID,
            "analyzer": store_mod.ANALYZER_VERSION,
            "block_size": fmt.BLOCK_SIZE,
            "docs": len(docs),
            "terms": len(postings),
            "blocks": blocks,
            "shards": {name: sha for name, sha, _, _ in shard_stamp},
        },
    )
    # Volatile on purpose, and excluded from the byte-identity assertion:
    # mtimes are the cheap staleness check and cannot be reproducible.
    _write_json(
        directory / fmt.STAMP_NAME,
        {"shards": {name: [size, mtime] for name, _, size, mtime in shard_stamp}},
    )

    return BuildReport(
        docs=len(docs),
        terms=len(postings),
        blocks=blocks,
        postings=postings_count,
        bytes_written=written,
    )


def _read_committed(root: Path):
    """One pass over the committed shards: doc table, postings, statistics.

    Returns `(docs, codes, postings, stats, shard_stamp)`. `docs` is sorted by
    id, so a document's index is stable across builds; `codes` is parallel to
    it (the dense lane's table, `None` where a record has no `code`); and
    `postings` maps a term hash to its `(docidx, tf_heading, tf_body)` list in
    docidx order.
    """
    records: list[dict] = []
    total_docs = 0
    total_wlen = 0
    shard_stamp: list[tuple[str, str, int, int]] = []

    for path in store_mod.iter_shard_paths(root):
        raw = path.read_bytes()
        stat = path.stat()
        shard_stamp.append(
            (path.name, store_mod.content_sha(raw), stat.st_size, stat.st_mtime_ns)
        )
        _, lines = store_mod.raw_record_lines(path)
        for lineno, line in enumerate(lines, start=2):
            total_docs += 1
            record = json.loads(line)
            _assert_invariants(path, lineno, line, record)
            m = _WLEN_RE.search(line)
            if m:
                total_wlen += int(m.group(1))
            records.append(record)

    records.sort(key=lambda r: r["id"])

    docs = [
        {
            "id": r["id"],
            "loc": r["loc"],
            "title": r.get("title", r.get("title_h", "")),
            "wlen": r.get("wlen", 0),
        }
        for r in records
    ]

    codes = [r.get("code") for r in records]

    postings: dict[str, list[tuple[int, int, int]]] = {}
    for docidx, record in enumerate(records):
        for term, tf in record.get("terms", {}).items():
            postings.setdefault(term, []).append((docidx, tf[0], tf[1]))

    stats = {"n": total_docs, "total_wlen": total_wlen}
    return docs, codes, postings, stats, shard_stamp


def _assert_invariants(path: Path, lineno: int, line: bytes, record: dict) -> None:
    """Refuse to build an accelerator that could disagree with the scan.

    See the module docstring. Both checks are cheap here (the build already
    holds the bytes and the parse) and impossible to add later.
    """
    quoted = set(_QUOTED_HASH_RE.findall(line))
    term_keys = {t.encode("ascii") for t in record.get("terms", {})}
    stray = quoted - term_keys
    if stray:
        example = sorted(stray)[0].decode("ascii")
        raise FuxError(
            f"{path}:{lineno}: the quoted 16-hex token {example!r} appears outside `terms` in "
            f"record {record.get('id')!r}. `query/scan.py` counts it toward that term's df from "
            f"the raw bytes, and the accelerator counts from the postings, so the two paths would "
            f"score this corpus differently. Refusing to build a divergent accelerator."
        )

    m = _WLEN_RE.search(line)
    regex_wlen = int(m.group(1)) if m else None
    parsed_wlen = record.get("wlen")
    if regex_wlen != parsed_wlen:
        raise FuxError(
            f"{path}:{lineno}: record {record.get('id')!r} has wlen {parsed_wlen!r} but the "
            f"byte-level regex reads {regex_wlen!r}. `query/scan.py` derives avg_wlen from the "
            f"regex and scores from the parse; they must agree. Refusing to build."
        )


def _write_postings(
    root: Path,
    postings: dict[str, list[tuple[int, int, int]]],
    wlens: list[int],
) -> tuple[int, int]:
    """Write term-major block lines plus the fixed-width offset table.

    Terms are grouped by hash prefix into 256 shards (mirroring the committed
    layout) and written in sorted hash order, so the offset table is sorted by
    construction and a term's blocks are one bisect away.
    """
    by_prefix: dict[str, list[str]] = {}
    for term in sorted(postings):
        by_prefix.setdefault(fmt.term_prefix(term), []).append(term)

    total_blocks = 0
    total_postings = 0

    for prefix, terms in by_prefix.items():
        lines: list[bytes] = []
        entries: list[bytes] = []
        offset = 0
        for term in terms:
            entries_for_term = postings[term]  # already docidx-ascending
            total_postings += len(entries_for_term)
            for block_no, start in enumerate(range(0, len(entries_for_term), fmt.BLOCK_SIZE)):
                block = entries_for_term[start : start + fmt.BLOCK_SIZE]
                line = json.dumps(
                    [term, [list(p) for p in block]],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                mx = max(_HEADING_W * tf_h + _BODY_W * tf_b for _, tf_h, tf_b in block)
                mnw = min(wlens[docidx] for docidx, _, _ in block)
                entries.append(
                    fmt.pack_entry(
                        bytes.fromhex(term),
                        block_no,
                        offset,
                        len(line),
                        mx,
                        mnw,
                        block[0][0],
                        block[-1][0],
                        len(block),
                    )
                )
                lines.append(line)
                offset += len(line) + 1
                total_blocks += 1

        fmt.postings_path(root, prefix).write_bytes(b"\n".join(lines) + b"\n")
        fmt.offsets_path(root, prefix).write_bytes(b"".join(entries))

    return total_blocks, total_postings


def _write_docs(directory: Path, docs: list[dict]) -> int:
    payload = b"".join(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
        for doc in docs
    )
    path = directory / fmt.DOCS_NAME
    path.write_bytes(payload)
    return len(payload)


def _write_json(path: Path, payload: dict) -> int:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return len(data)


def _clear(directory: Path) -> None:
    for path in directory.glob("*"):
        if path.is_file():
            path.unlink()
