"""The scan's section attachment — SR-SECTIONS decision 7 (W-278).

With `[ranking] section_weight > 0`, each sectioned candidate the scan found
gets `secs`: its sections that carry a query term in their own slots, as
`(k, flen, terms)` over the query's terms, in `k` order. **This module only
attaches; it scores nothing** — the section term's arithmetic is `rank()`'s
(SR-RANKING decision 6), and the accelerator attaches from its own runtime
handle (`derive/accel.py::_attach_sections`).

Two routes, one result, held equal by `tests/query/test_sections.py`:

- **the derived plane, when the runtime is fresh** — `sections.json` and the
  per-term section postings, about a twentieth of the bytes (W-270 measured the
  committed read at +328 ms a query at `rung-10000`, against L13's 100);
- **the committed plane otherwise**, by byte pattern, never a whole-line decode.

Owned by [SR-SECTIONS](../../../records/0161_sections.md). Node twin:
`node/src/query/sections.mjs`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .. import store as store_mod

__all__ = ["attach"]

#: A line's `flen`, off the raw bytes: `scan.py::_FLEN_RE`'s pattern. Not
#: imported from it, because `scan.py` imports this module.
_FLEN_RE = re.compile(rb'"flen":\[([0-9,\s]*)\]')

#: A line's id, off the raw bytes — a section line and a `docs.jsonl` line
#: alike. Both are canonical JSON with sorted keys, so the id is the first
#: string after `"id":`; an escape in it is decoded by `json`.
_ID_RE = re.compile(rb'"id":"((?:[^"\\]|\\.)*)"')


def attach(root: Path, candidates: list[dict], query_hashes: list[str]) -> None:
    """Attach `secs` to every sectioned candidate: the derived plane when
    fresh, the committed plane otherwise."""
    if not _from_runtime(root, candidates, query_hashes):
        _from_committed(root, candidates, query_hashes)


def _from_runtime(root: Path, candidates: list[dict], query_hashes: list[str]) -> bool:
    """The derived-plane route (W-278 DoD 2). When the runtime is fresh — `is_fresh`
    stamps every section shard beside the document shards — each sectioned
    candidate gets the same `secs` the committed plane would give it (`(k,
    flen, terms)` over the query's terms, in `k` order), read from
    `sections.json` and the per-term section postings: about a twentieth of
    the bytes, and no line of the committed plane decoded. **Returns False,
    attaching nothing, when the runtime is stale or absent**; the scan then
    reads the committed plane (`_from_committed`).
    """
    by_id = {record["id"]: record for record in candidates if record.get("nsec")}
    if not by_id:
        return True
    # Imported here: `derive/accel.py` imports the scan, which imports this.
    from ..derive import accel
    from ..derive import format as fmt

    if not accel.is_fresh(root):
        return False
    directory = fmt.runtime_dir(root)
    rows = json.loads((directory / fmt.SECTION_TABLE_NAME).read_bytes())["rows"]
    lines = (directory / fmt.DOCS_NAME).read_bytes().split(b"\n")
    ids: dict[int, str] = {}
    by_prefix: dict[str, dict] = {}
    bags: dict[str, dict[int, tuple[list[int], dict[str, list[int]]]]] = {}
    for term in query_hashes:
        prefix = fmt.term_prefix(term)
        if prefix not in by_prefix:
            path = fmt.section_postings_path(root, prefix)
            by_prefix[prefix] = json.loads(path.read_bytes()) if path.exists() else {}
        for secidx, tf in by_prefix[prefix].get(term, ()):
            docidx, k, flen = rows[secidx]
            doc_id = ids.get(docidx)
            if doc_id is None:
                raw = _ID_RE.search(lines[docidx]).group(1)
                doc_id = ids[docidx] = json.loads(b'"' + raw + b'"') if b"\\" in raw else raw.decode("utf-8")
            if doc_id in by_id:
                bags.setdefault(doc_id, {}).setdefault(k, (list(flen), {}))[1][term] = list(tf)
    for doc_id, bag in bags.items():
        by_id[doc_id]["secs"] = [(k, *bag[k]) for k in sorted(bag)]
    return True


def _from_committed(root: Path, candidates: list[dict], query_hashes: list[str]) -> None:
    """The committed-plane read, when no fresh runtime exists.

    Only the section shards that hold a sectioned candidate's sections are
    read (a section shares its parent's shard number, decision 4). Each query
    term's `"<hash>":[` entry is found in the shard's bytes directly, so a line
    that carries no query term is never visited, and one that does yields its
    id, its `flen` and the query's own `terms` entries by byte position, never
    a whole-line decode. A section's terms are a subset of its document's
    (decision 3's totality), so its parent was already a candidate.
    """
    by_id = {record["id"]: record for record in candidates if record.get("nsec")}
    if not by_id:
        return
    shards = {store_mod.shard_for(doc_id) for doc_id in by_id}
    keys = [(h, f'"{h}":['.encode("ascii")) for h in query_hashes]
    bags: dict[str, list[tuple[int, list[int], dict]]] = {}
    for path in store_mod.iter_section_paths(root):
        if path.stem not in shards:
            continue
        data = b"\n".join(store_mod.raw_record_lines(path)[1])
        found: dict[int, dict[str, list[int]]] = {}
        for h, key in keys:
            at = data.find(key)
            while at != -1:
                start = data.rfind(b"\n", 0, at) + 1
                open_ = at + len(key)
                close = data.index(b"]", open_)
                found.setdefault(start, {})[h] = [int(part) for part in data[open_:close].split(b",")]
                at = data.find(key, close)
        for start, hits in found.items():
            raw = _ID_RE.search(data, start).group(1)
            sec_id = json.loads(b'"' + raw + b'"') if b"\\" in raw else raw.decode("utf-8")
            parent = store_mod.section_parent(sec_id)
            if parent not in by_id:
                continue
            inner = _FLEN_RE.search(data, start).group(1).strip()
            flen = [int(part) for part in inner.split(b",")] if inner else []
            terms = {h: hits[h] for h in query_hashes if h in hits}
            bags.setdefault(parent, []).append((store_mod.reader.section_ordinal(sec_id), flen, terms))
    for parent, bag in bags.items():
        bag.sort(key=lambda entry: entry[0])
        by_id[parent]["secs"] = bag
