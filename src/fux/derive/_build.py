"""Build the derived T1 accelerator from the committed shards alone.

Reads `.fux/index/*.jsonl`, writes `.fux/runtime/`. Nothing else is an input —
that is the DoD ("rebuilds deterministically from committed bytes only") and
the reason the accelerator can be deleted at any moment without loss.

## The two build-time invariants, and why they fail the build loudly

`query/scan.py` is the oracle the accelerator must reproduce byte-for-byte,
and it derives its statistics from **raw bytes**, not from the parsed record:

- `df[h]` counts a document if `"<hash>"` appears anywhere on its line.
- `total_flen` sums each field's raw token counts from the `flen` the regex
  finds. Raw, never weighted: the weights are tunable, and a stored number
  that is a function of a tunable is ADR-TUNE decision 6a's defect.

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
from ..progress import NULL as _NULL_PROGRESS
from ..store import fuxdir
from ..graph import plane as graph_plane
from ..store import TF_FIELDS
from . import format as fmt
from .format import _FIELD_COUNT

_QUOTED_HASH_RE = re.compile(rb'"([0-9a-f]{16})"')
_FLEN_RE = re.compile(rb'"flen":\[([0-9,\s]*)\]')

#: `mx` is a per-field u16. A document with more than this many occurrences of
#: one term in one field is not a corpus fux serves, and packing one would
#: silently truncate the bound — which is the one error direction that loses
#: documents. Refuse instead.
_MAX_TF = 0xFFFF


@dataclass
class BuildReport:
    docs: int
    terms: int
    blocks: int
    postings: int
    bytes_written: int


def build(root: Path, *, progress=None) -> BuildReport:
    """Materialize `.fux/runtime/` from the committed index."""
    progress = progress or _NULL_PROGRESS
    docs, postings, stats, shard_stamp, records = _read_committed(root, progress)

    directory = fuxdir.derived_dir(root, fmt.RUNTIME_DIR)
    postings_directory = directory / fmt.POSTINGS_DIR
    postings_directory.mkdir(parents=True, exist_ok=True)
    _clear(postings_directory)

    written = 0
    written += _write_docs(directory, docs)
    written += _write_json(directory / fmt.STATS_NAME, stats)
    # `graph_plane.build_plane` offers no per-item hook, so this is a bookend
    # around the call rather than a live count — the same honesty tradeoff as
    # the `write` phase in ingest.run.
    #
    # **The `codes` phase is gone** (2026-08-25): it derived a Hamming
    # prefilter over the committed per-chunk vectors, and both the vectors and
    # the lane that read them were deleted with the embedding model.
    #
    # The graph lane's plane, from the same single pass over the shards. It is
    # derived for the reason `plane.py` gives: a community label is global, so
    # committing one would turn a one-file commit into a corpus-wide diff.
    edge_total = sum(len(r.get("edges", [])) for r in records)
    with progress.phase("graph", edge_total, "edges") as p:
        written += graph_plane.build_plane(directory, records)
        p.update(edge_total)

    blocks, postings_count = _write_postings(root, postings, [d["flen"] for d in docs], progress)

    written += _write_json(
        directory / fmt.MANIFEST_NAME,
        {
            "schema": fmt.RUNTIME_SCHEMA,
            "index_schema": store_mod.SCHEMA_ID,
            "analyzer": store_mod.ANALYZER_VERSION,
            "block_size": fmt.BLOCK_SIZE,
            "docs_fields": list(fmt.DOCS_FIELDS),
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


def _read_committed(root: Path, progress=None):
    """One pass over the committed shards: doc table, postings, statistics.

    Returns `(docs, postings, stats, shard_stamp, records)`. `docs` is sorted by
    id, so a document's index is stable across builds, and `postings` maps a
    term hash to its `(docidx, per-field tf list)` list in docidx order.
    """
    progress = progress or _NULL_PROGRESS
    records: list[dict] = []
    total_docs = 0
    total_flen = [0] * len(TF_FIELDS)
    shard_stamp: list[tuple[str, str, int, int]] = []

    paths = list(store_mod.iter_shard_paths(root))
    with progress.phase("read", len(paths), "shards") as p:
        for path in paths:
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
                # Same derivation as `query/scan.py`, from the same bytes —
                # `_assert_invariants` has just proved the regex and the parse
                # agree on this record's `flen`, so either source is the same
                # number. Reading it from the regex keeps the two corpus-stat
                # passes literally identical rather than merely equivalent.
                m = _FLEN_RE.search(line)
                if m:
                    inner = m.group(1).strip()
                    for i, part in enumerate(inner.split(b",") if inner else []):
                        total_flen[i] += int(part)
                records.append(record)
            p.update(1)

    records.sort(key=lambda r: r["id"])

    # `archived` is carried, not re-derived. The scan reads the record's own
    # stamp first and only falls back to matching `loc` against the configured
    # archived directories; a doc table without the stamp forces the
    # accelerator down the fallback alone, so a record stamped `archived: true`
    # whose loc no longer matches a configured directory would be flagged by
    # one path and not the other. Same class of defect as W-73, on the flag
    # rather than the order (W-76 Phase 0 groundwork).
    docs = [
        {
            "id": r["id"],
            "loc": r["loc"],
            "title": store_mod.display_title(r),
            "flen": list(r.get("flen", [])),
            "archived": bool(r.get("archived", False)),
            # W-76 Phase 2, same reasoning as `archived` above: a fact the
            # scan reads off the record must be CARRIED here, not re-derived,
            # or the two paths weight the same document differently.
            "superseded": bool(r.get("superseded", False)),
            "mtime": r.get("mtime"),
        }
        for r in records
    ]

    postings: dict[str, list[tuple[int, list[int]]]] = {}
    for docidx, record in enumerate(records):
        for term, tf in record.get("terms", {}).items():
            postings.setdefault(term, []).append((docidx, list(tf)))

    newest_mtime = max((r["mtime"] for r in records if isinstance(r.get("mtime"), int)), default=0)
    # RAW per-field totals, never pre-weighted. The weights are a `tune.toml`
    # key, and a stored number that is a function of a tunable is exactly what
    # ADR-TUNE decision 6a forbids — the same defect the committed `wlen` had
    # before W-76 Phase 1, one plane up. Both query paths weight this at query
    # time, so changing a field weight needs no rebuild and cannot make
    # `--fast` and `--scan` disagree.
    stats = {"n": total_docs, "total_flen": total_flen, "newest_mtime": newest_mtime}
    # `records` rides along so the graph plane needs no second pass over the
    # shards; it is already sorted by id, which is what makes it usable.
    return docs, postings, stats, shard_stamp, records


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
        # The one shape this ever legitimately had: a `title_h` written before
        # the prefix landed. Name the migration rather than the symptom — the
        # record is not corrupt, it is old, and re-ingesting fixes it.
        migration = ""
        if record.get("title_h") == example:
            migration = (
                " This record's `title_h` predates the `h:` prefix "
                "(ADR-INDEX-LIFECYCLE): re-run `fux ingest --refresh-urls` to rewrite it."
            )
        raise FuxError(
            f"{path}:{lineno}: the quoted 16-hex token {example!r} appears outside `terms` in "
            f"record {record.get('id')!r}. `query/scan.py` counts it toward that term's df from "
            f"the raw bytes, and the accelerator counts from the postings, so the two paths would "
            f"score this corpus differently. Refusing to build a divergent accelerator."
            + migration
        )

    m = _FLEN_RE.search(line)
    if m is None:
        regex_flen = None
    else:
        inner = m.group(1).strip()
        regex_flen = [int(part) for part in inner.split(b",")] if inner else []
    parsed_flen = list(record.get("flen", [])) if "flen" in record else None
    if regex_flen != parsed_flen:
        raise FuxError(
            f"{path}:{lineno}: record {record.get('id')!r} has flen {parsed_flen!r} but the "
            f"byte-level regex reads {regex_flen!r}. `query/scan.py` derives avg_wlen from the "
            f"regex and scores from the parse; they must agree. Refusing to build."
        )


def _per_field_max(block) -> tuple[int, ...]:
    """The largest tf each field reaches anywhere in the block."""
    out = [0] * _FIELD_COUNT
    for _, tf in block:
        for i, count in enumerate(tf):
            if count > out[i]:
                out[i] = count
    for i, value in enumerate(out):
        if value > _MAX_TF:
            raise FuxError(
                f"term frequency {value} exceeds the u16 the offset table packs. "
                "A truncated `mx` under-estimates the block bound and loses documents, "
                "so the build refuses rather than writing one."
            )
    return tuple(out)


def _per_field_min_len(block, flens: list[list[int]]) -> tuple[int, ...]:
    """The smallest token count each field reaches anywhere in the block."""
    out = [0xFFFFFFFF] * _FIELD_COUNT
    for docidx, _ in block:
        flen = flens[docidx]
        for i in range(_FIELD_COUNT):
            value = flen[i] if i < len(flen) else 0
            if value < out[i]:
                out[i] = value
    return tuple(0 if v == 0xFFFFFFFF else v for v in out)


def _write_postings(
    root: Path,
    postings: dict[str, list[tuple[int, list[int]]]],
    flens: list[list[int]],
    progress=None,
) -> tuple[int, int]:
    """Write term-major block lines plus the fixed-width offset table.

    Terms are grouped by hash prefix into 256 shards (mirroring the committed
    layout) and written in sorted hash order, so the offset table is sorted by
    construction and a term's blocks are one bisect away.
    """
    progress = progress or _NULL_PROGRESS
    by_prefix: dict[str, list[str]] = {}
    for term in sorted(postings):
        by_prefix.setdefault(fmt.term_prefix(term), []).append(term)

    total_blocks = 0
    total_postings = 0

    with progress.phase("postings", len(postings), "terms") as p:
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
                    # PER-FIELD extrema, deliberately unweighted — see
                    # `derive/format.py::ENTRY_STRUCT`. `mx` over-estimates the
                    # block's true maximum weighted tf once recombined, and
                    # `mnw` under-estimates its true minimum length; both
                    # errors push the bound UP, which is the direction that
                    # never loses a document.
                    mx = _per_field_max(block)
                    mnw = _per_field_min_len(block, flens)
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

                p.update(1)

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
