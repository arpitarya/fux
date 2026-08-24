"""On-disk shapes for the derived T1 accelerator.

Everything here lives under `.fux/runtime/` — derived, gitignored,
`CACHEDIR.TAG`-tagged (ADR-DOTFUX), and rebuildable from the committed shards
alone. **The committed format is untouched**; ADR-RECORD is frozen and this
milestone does not go near it.

## Why the offset table is binary, and why that is not a JSONL retreat

The index-format compare doc's B5 measurement reads a block's max-impact by
*string-slicing the block line* (397 ms -> 44 ms). Putting the same integer in
a fixed-width side table is strictly cheaper — a `struct.unpack` at a computed
index, with the block line never touched at all — and it keeps the block line
honestly valid JSON. Fixed-width integers inside the line would need zero
padding, which JSON forbids.

The table is derived, never committed, so no committed-bytes law applies to
it. `mx` and `mnw` are integers regardless, per compare doc §7.

## Entry layout — 40 bytes, `<8sHQIIIIIH`, no padding under `<`

| field | type | meaning |
|---|---|---|
| `term` | `8s` | raw 8-byte term hash (the 16-hex key, unhexlified) |
| `block_no` | `u16` | block ordinal within the term, from 0 |
| `offset` | `u64` | byte offset of the block line in its postings shard |
| `length` | `u32` | byte length of the block line, newline excluded |
| `mx` | `u32` | **max weighted tf** in the block: `max(3*tf_heading + tf_body)` |
| `mnw` | `u32` | **min `wlen`** in the block |
| `first_doc` | `u32` | lowest docidx in the block |
| `last_doc` | `u32` | highest docidx in the block |
| `count` | `u16` | postings in the block |

Entries are sorted by `(term, block_no)`, so a term's blocks are found by one
bisect and read as a contiguous run.

`first_doc`/`last_doc` exist so a deferred term can answer *"does this block
cover any of my candidates?"* without reading the block. Without them the
common-term path would parse every block just to discover it was irrelevant —
which is the exact cost the accelerator is built to avoid.

`mx` and `mnw` are both needed because a term's BM25F contribution is
increasing in weighted tf *and decreasing in `wlen`* — an upper bound over a
block requires the maximum of the first and the minimum of the second. `mx`
alone would be a valid but loose bound. See ADR-T1-ACCELERATOR and the proof
in `accel.block_bound`.
"""

from __future__ import annotations

import struct
from pathlib import Path

RUNTIME_DIR = "runtime"

#: Postings per block line. B5 measured this split; 128 is the measured shape.
BLOCK_SIZE = 128

#: Bumped whenever the derived layout changes shape. A mismatch rebuilds
#: rather than misreads — the derived plane is disposable by definition.
# v2 (W-73, 2026-08-23): the doc table carries `archived`, so the weighted
# bound and the archived flag are computed from the same fact on both paths.
# A v1 runtime is not read: `is_fresh()` refuses it and the build reruns.
# v3 (W-76 Phase 1): per-field extrema in the offset table, `flen` in the
# doc table. A v2 runtime is refused and rebuilt.
RUNTIME_SCHEMA = "fux.runtime.v3"

#: v3 (W-76 Phase 1 record half): `mx` and `mnw` become PER-FIELD arrays.
#:
#: They used to be two scalars, each a *weighted* sum computed at build time.
#: Once field weights are tunable at query time (ADR-TUNE decision 6, and
#: Arpit's fork B ruling of 2026-08-23) a weighted scalar is stale the moment
#: someone edits `tune.toml` — so either the accelerator rebuilds on every
#: ranking edit, which breaks ADR-TUNE's central promise, or the extrema stop
#: being weighted. They stop being weighted.
#:
#: `mx` is a per-field MAXIMUM tf (u16 — a single document holding 65 535
#: occurrences of one term in one field is not a corpus fux serves, and
#: `_write_postings` refuses to pack one). `mnw` is a per-field MINIMUM token
#: count (u32 — document lengths genuinely get large).
#:
#: Entry grows 40 B -> 62 B. The offset table is derived and disposable, so
#: this costs disk in `.fux/runtime/` and nothing in git.
_FIELD_COUNT = 5
ENTRY_STRUCT = struct.Struct("<8sHQI" + f"{_FIELD_COUNT}H" + f"{_FIELD_COUNT}I" + "IIH")
ENTRY_SIZE = ENTRY_STRUCT.size  # 40

#: Every key the doc table carries. **Part of the runtime contract, checked by
#: `is_fresh`.** Learned the hard way on 2026-08-23: `superseded` and `mtime`
#: were added to the table while `RUNTIME_SCHEMA` stayed put, and an
#: accelerator built minutes earlier kept being read -- so `ask --scan` applied
#: a supersession demotion and `ask --fast` did not. Same silent-divergence
#: class as W-73, arriving through staleness rather than through arithmetic.
#:
#: A schema string only moves when someone remembers to move it. This field
#: set moves whenever the table does, because it IS the table.
DOCS_FIELDS = ("id", "loc", "title", "flen", "archived", "superseded", "mtime")

DOCS_NAME = "docs.jsonl"
STATS_NAME = "stats.json"
MANIFEST_NAME = "manifest.json"
STAMP_NAME = "stamp.json"
POSTINGS_DIR = "postings"

#: Files whose bytes must be identical across two builds of the same index.
#: `stamp.json` is deliberately excluded — it carries filesystem mtimes, which
#: are the fast staleness check and are not reproducible by construction.
DETERMINISTIC_FILES = (DOCS_NAME, STATS_NAME, MANIFEST_NAME, "codes.jsonl", "graph.json")


def runtime_dir(root: Path) -> Path:
    return root / ".fux" / RUNTIME_DIR


def postings_dir(root: Path) -> Path:
    return runtime_dir(root) / POSTINGS_DIR


def postings_path(root: Path, prefix: str) -> Path:
    return postings_dir(root) / f"{prefix}.jsonl"


def offsets_path(root: Path, prefix: str) -> Path:
    return postings_dir(root) / f"{prefix}.idx"


def term_prefix(term_hash: str) -> str:
    """Postings shard for a term — its hash's first byte, mirroring the store."""
    return term_hash[:2]


def pack_entry(
    term: bytes,
    block_no: int,
    offset: int,
    length: int,
    mx: tuple[int, ...],
    mnw: tuple[int, ...],
    first_doc: int,
    last_doc: int,
    count: int,
) -> bytes:
    """`mx` and `mnw` are per-field tuples of length `_FIELD_COUNT`."""
    return ENTRY_STRUCT.pack(
        term, block_no, offset, length, *mx, *mnw, first_doc, last_doc, count
    )


def unpack_entry(buf, index: int):
    """`(term, block_no, offset, length, mx_tuple, mnw_tuple, first, last, count)`."""
    raw = ENTRY_STRUCT.unpack_from(buf, index * ENTRY_SIZE)
    n = _FIELD_COUNT
    return (
        raw[0], raw[1], raw[2], raw[3],
        raw[4 : 4 + n],
        raw[4 + n : 4 + 2 * n],
        raw[4 + 2 * n], raw[5 + 2 * n], raw[6 + 2 * n],
    )
