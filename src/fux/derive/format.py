"""On-disk shapes for the derived T1 accelerator.

Everything here lives under `.fux/runtime/` — derived, gitignored,
`CACHEDIR.TAG`-tagged (SR-DOTFUX), and rebuildable from the committed shards
alone. **The committed format is untouched**; SR-RECORD is frozen and this
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

## Entry layout — 62 bytes, `<8sHQI` + `5H` + `5I` + `IIH`, no padding under `<`

**Was 40 bytes and `<8sHQIIIIIH` until W-76 Phase 1.** The two scalars that
grew are the reason: `mx` and `mnw` were single weighted numbers, and a
weighted extremum cannot be stored once when the weights are query-time tune
keys. They are now **per-field and deliberately UNWEIGHTED** arrays, recombined
at the query's own weights by `accel.block_bound`.

| field | type | meaning |
|---|---|---|
| `term` | `8s` | raw 8-byte term hash (the 16-hex key, unhexlified) |
| `block_no` | `u16` | block ordinal within the term, from 0 |
| `offset` | `u64` | byte offset of the block line in its postings shard |
| `length` | `u32` | byte length of the block line, newline excluded |
| `mx` | `5×u16` | per-field **max unweighted tf** in the block, one per `TF_FIELDS` |
| `mnw` | `5×u32` | per-field **min `flen`** in the block, one per `TF_FIELDS` |
| `first_doc` | `u32` | lowest docidx in the block |
| `last_doc` | `u32` | highest docidx in the block |
| `count` | `u16` | postings in the block |

**Why per-field extrema are safe.** They over-estimate `mx` and under-estimate
`mnw` relative to the true weighted extremum, and both errors push the bound
**up** — so a block that could contain a winner is never skipped. Measured cost
on this repo and on 10 000 real documents: **+0.0 % blocks scanned**, because
92.5 % of postings are single-field, which makes the per-field sum exact rather
than loose. Filed: `work/regression/2026-08-23-fork3-per-field-bound/`.

Entries are sorted by `(term, block_no)`, so a term's blocks are found by one
bisect and read as a contiguous run.

`first_doc`/`last_doc` exist so a deferred term can answer *"does this block
cover any of my candidates?"* without reading the block. Without them the
common-term path would parse every block just to discover it was irrelevant —
which is the exact cost the accelerator is built to avoid.

`mx` and `mnw` are both needed because a term's BM25F contribution is
increasing in weighted tf *and decreasing in `wlen`* — an upper bound over a
block requires the maximum of the first and the minimum of the second. `mx`
alone would be a valid but loose bound. See SR-T1-ACCELERATOR and the proof
in `accel.block_bound`.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from ..constants import fixed

RUNTIME_DIR = fixed("runtime", "dir")

#: Postings per block line. B5 measured this split; 128 is the measured shape.
BLOCK_SIZE = fixed("runtime", "block_size")

#: Bumped whenever the derived layout changes shape. A mismatch rebuilds
#: rather than misreads — the derived plane is disposable by definition.
# v2 (W-73, 2026-08-23): the doc table carries `archived`, so the weighted
# bound and the archived flag are computed from the same fact on both paths.
# A v1 runtime is not read: `is_fresh()` refuses it and the build reruns.
# v3 (W-76 Phase 1): per-field extrema in the offset table, `flen` in the
# doc table. A v2 runtime is refused and rebuilt.
#: v4 (2026-08-24, SR-TUNE): `stats.json` carries `total_flen`, the five raw
#: per-field token-count totals, in place of a pre-weighted `total_wlen`. The
#: field weights became `tune.toml` keys, so a weighted total stored here would
#: be a derived value that goes stale the moment a knob moves — and only on the
#: accelerator path, which is a differential-law break rather than a slow query.
#: v5 (2026-08-25, Arpit): `codes.jsonl` is gone. The dense lane and the
#: embedding model that fed it were deleted, so the plane no longer carries a
#: Hamming prefilter. **The bump is not strictly required for correctness** —
#: nothing reads the file any more, so a stale v4 plane could not diverge — but
#: a v4 plane leaves an orphan `codes.jsonl` on disk that no rebuild removes,
#: and this project has already been bitten once by trusting a schema string
#: that someone forgot to move (see `DOCS_FIELDS` below). Refusing the plane
#: costs one rebuild of a disposable directory.
#: v6 (2026-09-15, W-168 step 1): the ANCHOR plane. `anchors/<prefix>.json`
#: holds the reverse map term -> [(docidx, count)] folded from the `at` maps on
#: the committed edges; `docs.jsonl` carries each document's `alen`; and
#: `stats.json` carries `total_anchor_len`. All three are derived from the
#: committed shards alone and gitignored — which is the whole of Arpit's
#: 2026-09-15 ruling: the words are committed on the SOURCE's edge, and the
#: per-target fold that ranking needs is rebuilt, never committed.
#: v7 (2026-09-27, W-168 step 4): `mined.json`, the corpus table of
#: `Long Form (ABBR)` pairs — the union of every record's committed `abbr`,
#: sorted. Derived for step 1's reason: the table is corpus-wide, so committing
#: it would make one document's bytes a function of every other's. A v6 plane
#: has no such file and is refused and rebuilt rather than read as "no pairs".
#: v8 (2026-09-30, W-168 step 8): `docs.jsonl` carried `authors` and `commits`.
#: v9 (2026-10-03): they left with the authority prior, so `docs_fields` is v7's
#: again. The number moves forward so that a v8 plane is refused by name and
#: rebuilt, never read by a reader that does not expect its fields.
#: v10 (2026-10-10, W-236): the SECTION plane. `docs.jsonl` carries `nsec`;
#: `stats.json` carries `sec_units` and `sec_total_flen`; `sections.json` is
#: the section table and `sections/<prefix>.json` its postings — all derived
#: from the committed `.fux/index/sections/`, and the stamp and manifest pin
#: those shards beside the document shards. A v9 plane has none of it and is
#: refused and rebuilt rather than read as "no sections".
RUNTIME_SCHEMA = fixed("runtime", "schema")

#: v3 (W-76 Phase 1 record half): `mx` and `mnw` become PER-FIELD arrays.
#:
#: They used to be two scalars, each a *weighted* sum computed at build time.
#: Once field weights are tunable at query time (SR-TUNE decision 6, and
#: Arpit's fork B ruling of 2026-08-23) a weighted scalar is stale the moment
#: someone edits `tune.toml` — so either the accelerator rebuilds on every
#: ranking edit, which breaks SR-TUNE's central promise, or the extrema stop
#: being weighted. They stop being weighted.
#:
#: `mx` is a per-field MAXIMUM tf (u16 — a single document holding 65 535
#: occurrences of one term in one field is not a corpus fux serves, and
#: `_write_postings` refuses to pack one). `mnw` is a per-field MINIMUM token
#: count (u32 — document lengths genuinely get large).
#:
#: Entry grows 40 B -> 62 B. The offset table is derived and disposable, so
#: this costs disk in `.fux/runtime/` and nothing in git.
#: One `mx`/`mnw` slot per tf field, in `[index] tf_fields` order; the key is
#: the term hash, `[index] term_hash_bytes` wide.
_FIELD_COUNT = len(fixed("index", "tf_fields"))
_TERM_BYTES = fixed("index", "term_hash_bytes")
#: A postings shard is the term hash's first byte, as hex.
_PREFIX_CHARS = fixed("radix", "hex_digits_per_byte")
ENTRY_STRUCT = struct.Struct(f"<{_TERM_BYTES}sHQI{_FIELD_COUNT}H{_FIELD_COUNT}IIIH")
ENTRY_SIZE = ENTRY_STRUCT.size  # 62

#: Every key the doc table carries. **Part of the runtime contract, checked by
#: `is_fresh`.** Learned the hard way on 2026-08-23: `superseded` and `mtime`
#: were added to the table while `RUNTIME_SCHEMA` stayed put, and an
#: accelerator built minutes earlier kept being read -- so `ask --scan` applied
#: a supersession demotion and `ask --fast` did not. Same silent-divergence
#: class as W-73, arriving through staleness rather than through arithmetic.
#:
#: A schema string only moves when someone remembers to move it. This field
#: set moves whenever the table does, because it IS the table.
#:
#: `alen` (W-168 step 1) is the document's anchor token total. It is in the doc
#: table rather than in the anchor shards because **every candidate needs it
#: and only a matching candidate needs its terms**: a heavily-linked document
#: is a longer document, so its `wlen` carries the length whether or not a
#: single anchor word matches the query. Reading it from anywhere else would
#: mean one more file open per candidate.
DOCS_FIELDS = tuple(fixed("runtime", "docs_fields"))

DOCS_NAME = fixed("runtime", "docs")
#: W-168 step 1. Sharded by the term hash's first byte, mirroring `postings/`
#: and the committed store, for the same reason: a query reads one small file
#: per term instead of a corpus-wide map. Whole-file JSON rather than the
#: block-and-offset-table shape `postings/` uses — anchor postings are a small
#: fraction of body postings (link text is a handful of words, bodies are
#: thousands), so a bisectable fixed-width table would buy nothing and add a
#: second binary layout to keep in step.
ANCHORS_DIR = fixed("runtime", "anchors_dir")
STATS_NAME = fixed("runtime", "stats")
#: W-168 step 4 — `{"pairs": [[short_hashes, long_hashes], ...]}`, sorted.
MINED_NAME = fixed("runtime", "mined")
MANIFEST_NAME = fixed("runtime", "manifest")
STAMP_NAME = fixed("runtime", "stamp")
POSTINGS_DIR = fixed("runtime", "postings_dir")
SECTIONS_RT_DIR = fixed("runtime", "sections_dir")
SECTION_TABLE_NAME = fixed("runtime", "section_table")

#: Files whose bytes must be identical across two builds of the same index.
#: `stamp.json` is deliberately excluded — it carries filesystem mtimes, which
#: are the fast staleness check and are not reproducible by construction.
#:
#: `codes.jsonl` left this tuple on 2026-08-25 with the dense lane. A `v4`
#: plane still has the file on disk; `RUNTIME_SCHEMA` moved to `v5` in the same
#: change so such a plane is refused and rebuilt rather than read past.
DETERMINISTIC_FILES = (DOCS_NAME, STATS_NAME, MINED_NAME, MANIFEST_NAME, SECTION_TABLE_NAME, fixed("graph", "file"))


def runtime_dir(root: Path) -> Path:
    return root / fixed("fuxdir", "dir") / RUNTIME_DIR


def postings_dir(root: Path) -> Path:
    return runtime_dir(root) / POSTINGS_DIR


def anchors_dir(root: Path) -> Path:
    return runtime_dir(root) / ANCHORS_DIR


def anchors_path(root: Path, prefix: str) -> Path:
    return anchors_dir(root) / f"{prefix}.json"


def section_postings_dir(root: Path) -> Path:
    return runtime_dir(root) / SECTIONS_RT_DIR


def section_postings_path(root: Path, prefix: str) -> Path:
    return section_postings_dir(root) / f"{prefix}.json"


def stamp_name(path: Path) -> str:
    """A committed shard's key in `stamp.json` and `manifest.json`.

    A document shard is its bare name, as it always was; a section shard is
    `sections/<name>`, so the two planes' `00.jsonl` cannot collide (W-236).
    """
    from ..store import SECTIONS_DIR

    return f"{SECTIONS_DIR}/{path.name}" if path.parent.name == SECTIONS_DIR else path.name


def postings_path(root: Path, prefix: str) -> Path:
    return postings_dir(root) / f"{prefix}.jsonl"


def offsets_path(root: Path, prefix: str) -> Path:
    return postings_dir(root) / f"{prefix}.idx"


def term_prefix(term_hash: str) -> str:
    """Postings shard for a term — its hash's first byte, mirroring the store."""
    return term_hash[:_PREFIX_CHARS]


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
    term, block_no, offset, length, *fields, first, last, count = ENTRY_STRUCT.unpack_from(
        buf, index * ENTRY_SIZE
    )
    mx, mnw = tuple(fields[:_FIELD_COUNT]), tuple(fields[_FIELD_COUNT:])
    return term, block_no, offset, length, mx, mnw, first, last, count


def write_json(path: Path, payload: dict) -> int:
    """One derived JSON file, in the bytes every runtime plane shares: sorted
    keys, no spaces, UTF-8, one trailing newline. Returns the bytes written."""
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return len(data)
