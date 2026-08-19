"""`fux ingest` — orchestrates the git-dir adapter, the URL fetcher,
extractors, and the canonical store into one incremental build.

Every document is re-extracted and every edge re-resolved on every run, even
for docs whose own `sha` hasn't changed — an edge can depend on another doc
elsewhere in the corpus (a new doc can resolve a previously-dangling link),
so "incremental" cannot mean "skip unchanged files" at this layer. It means
what `store.write_index` already guarantees: a shard whose bytes come out
identical is left untouched on disk. `ver` bumps strictly on this record's
own `sha` changing, independent of edges (the M1 build-time decision on
`ver` semantics).

URL docs (ADR-URL-INGEST) obey the offline-by-default law: a plain `fux ingest`
never touches the network — every existing `url:` record is carried forward
byte-identically. Only `--refresh-urls` loads a consumer fetcher and fetches;
on a refresh, a configured URL whose fetch fails keeps its prior record (a
transient network failure must never delete a document), while a URL no longer
in `.fux/sources/urls` disappears — reconciliation happens only on the run that
opted into the network.

Which fetcher runs, and whether a URL's display fields are hashed, are both
**per line** (ADR-URL-LIST decision 10): `urlsrc.resolve_urls` layers the
built-in default, the source-wide `[sources.url]` setting and the line, and
everything below it reads one already-resolved answer.

Every run calls `ensure_layout` first, so a fresh clone gets its `.fux/`
README and narrow `.gitignore` before anything is written into the directory
(ADR-DOTFUX). Both are write-if-missing; a consumer's edits survive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import store as store_mod
from ..config import load as load_config
from ..errors import FuxError
from . import edges as edges_mod
from . import extract as extract_mod
from . import urlsrc
from .gitdir import Skipped, walk_sources
from .parse import parse


@dataclass
class IngestReport:
    written_shards: list[Path]
    doc_count: int
    changed_count: int
    skipped: list[Skipped]


def run(root: Path, *, refresh_urls: bool = False) -> IngestReport:
    config = load_config(root)
    store_mod.ensure_layout(root)  # `.fux/` README + .gitignore, write-if-missing (ADR-DOTFUX)
    files, skipped = walk_sources(root, config.source_dirs)
    existing = store_mod.read_index(root)
    existing_urls = {doc_id: rec for doc_id, rec in existing.items() if doc_id.startswith("url:")}

    fresh: dict[str, bytes] = {}  # url doc_id -> fetched content, this run only
    carried: dict[str, dict] = {}  # url doc_id -> prior record, reused verbatim
    url_meta: dict[str, str] = {}  # url doc_id -> the `meta` policy its line resolved to
    if refresh_urls:
        if config.url is None:
            raise FuxError(f"--refresh-urls: no [sources.url] configured in {root / 'fux.toml'}")
        resolved = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
        url_meta = {f"url:{entry.url}": entry.meta for entry in resolved}
        fetched, url_skipped = urlsrc.fetch_all(root, resolved, config.url.config)
        skipped = skipped + url_skipped
        fresh = {f"url:{fu.url}": fu.content for fu in fetched}
        for doc_id in url_meta:
            if doc_id not in fresh and doc_id in existing_urls:
                carried[doc_id] = existing_urls[doc_id]  # failed fetch keeps the prior record
    else:
        carried = dict(existing_urls)  # offline run: every url record survives as-is

    parsed = {f"file:{wf.rel_path}": parse(wf.content) for wf in files}
    parsed |= {doc_id: parse(content) for doc_id, content in fresh.items()}
    extracted = {doc_id: extract_mod.extract_fields(_loc_of(doc_id), doc) for doc_id, doc in parsed.items()}
    scans = {doc_id: edges_mod.scan(doc) for doc_id, doc in parsed.items()}
    known_ids = set(parsed) | set(carried)
    # `code`-span basename resolution stays file-only: a backtick path is a
    # claim about the repo, never about a URL.
    by_basename = edges_mod.basename_index({i for i in known_ids if i.startswith("file:")})

    tracker = store_mod.CollisionTracker()
    records: list[dict] = []
    changed = 0

    def ver_for(doc_id: str, sha: str) -> int:
        nonlocal changed
        prior = existing.get(doc_id)
        if prior is not None and prior["sha"] == sha:
            return prior["ver"]
        changed += 1
        return prior["ver"] + 1 if prior is not None else 1

    for wf in files:
        doc_id = f"file:{wf.rel_path}"
        fields = extracted[doc_id]
        record = {
            "id": doc_id,
            "src": "git",
            "loc": wf.rel_path,
            "sha": store_mod.content_sha(wf.content),
            "ver": 0,
            "mode": "extracted",
            "meta": "plain",
            "title": fields.title,
            "phrases": fields.phrases,
            "terms": store_mod.hash_terms(fields.terms, tracker),
            "wlen": fields.wlen,
            "edges": edges_mod.resolve(doc_id, scans[doc_id], known_ids, by_basename),
        }
        record["ver"] = ver_for(doc_id, record["sha"])
        if fields.code is not None:
            record["code"] = fields.code
        records.append(record)

    for doc_id in sorted(fresh):
        fields = extracted[doc_id]
        record = {
            "id": doc_id,
            "src": "url",
            "loc": _loc_of(doc_id),
            "sha": store_mod.content_sha(fresh[doc_id]),
            "ver": 0,
            "mode": "extracted",
            "terms": store_mod.hash_terms(fields.terms, tracker),
            "wlen": fields.wlen,
            "edges": edges_mod.resolve(doc_id, scans[doc_id], known_ids, by_basename),
        }
        record["ver"] = ver_for(doc_id, record["sha"])
        # Per-URL, not per-source: a line may opt one public document out of
        # hashing (ADR-URL-LIST decision 10). It only ever loosens.
        if url_meta.get(doc_id) == "plain":
            record["meta"] = "plain"
            record["title"] = fields.title
            record["phrases"] = fields.phrases
        else:  # hashed meta — the non-git default (L5); no display text leaks
            record["meta"] = "hashed"
            record["title_h"] = store_mod.term_hash(fields.title)
        if fields.code is not None:
            record["code"] = fields.code
        records.append(record)

    records.extend(carried[doc_id] for doc_id in sorted(carried))

    written = store_mod.write_index(root, records)
    return IngestReport(written_shards=written, doc_count=len(records), changed_count=changed, skipped=skipped)


def _loc_of(doc_id: str) -> str:
    return doc_id.removeprefix("file:").removeprefix("url:")
