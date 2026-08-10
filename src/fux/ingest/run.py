"""`fux ingest` — orchestrates the git-dir adapter, extractors, and the
canonical store into one incremental build.

Every document is re-extracted and every edge re-resolved on every run, even
for docs whose own `sha` hasn't changed — an edge can depend on another doc
elsewhere in the corpus (a new doc can resolve a previously-dangling link),
so "incremental" cannot mean "skip unchanged files" at this layer. It means
what `store.write_index` already guarantees: a shard whose bytes come out
identical is left untouched on disk. `ver` bumps strictly on this record's
own `sha` changing, independent of edges (the M1 build-time decision on
`ver` semantics).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import store as store_mod
from ..config import load as load_config
from . import edges as edges_mod
from . import extract as extract_mod
from .gitdir import Skipped, walk_sources
from .parse import parse


@dataclass
class IngestReport:
    written_shards: list[Path]
    doc_count: int
    changed_count: int
    skipped: list[Skipped]


def run(root: Path) -> IngestReport:
    config = load_config(root)
    files, skipped = walk_sources(root, config.source_dirs)
    existing = store_mod.read_index(root)

    parsed = {f"file:{wf.rel_path}": parse(wf.content) for wf in files}
    extracted = {doc_id: extract_mod.extract_fields(doc_id.removeprefix("file:"), doc) for doc_id, doc in parsed.items()}
    scans = {doc_id: edges_mod.scan(doc) for doc_id, doc in parsed.items()}
    known_ids = set(parsed)
    by_basename = edges_mod.basename_index(known_ids)

    tracker = store_mod.CollisionTracker()
    records: list[dict] = []
    changed = 0
    for wf in files:
        doc_id = f"file:{wf.rel_path}"
        sha = store_mod.content_sha(wf.content)
        prior = existing.get(doc_id)
        if prior is not None and prior["sha"] == sha:
            ver = prior["ver"]
        else:
            ver = prior["ver"] + 1 if prior is not None else 1
            changed += 1

        fields = extracted[doc_id]
        edges = edges_mod.resolve(doc_id, scans[doc_id], known_ids, by_basename)
        record = {
            "id": doc_id,
            "src": "git",
            "loc": wf.rel_path,
            "sha": sha,
            "ver": ver,
            "mode": "extracted",
            "meta": "plain",
            "title": fields.title,
            "phrases": fields.phrases,
            "terms": store_mod.hash_terms(fields.terms, tracker),
            "wlen": fields.wlen,
            "edges": edges,
        }
        if fields.code is not None:
            record["code"] = fields.code
        records.append(record)

    written = store_mod.write_index(root, records)
    return IngestReport(written_shards=written, doc_count=len(records), changed_count=changed, skipped=skipped)
