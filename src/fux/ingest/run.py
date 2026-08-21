"""`fux ingest` — orchestrates the git-dir adapter, the URL fetcher,
extractors, and the canonical store into one incremental build.

## Delta ingest — what is skipped, and what never is (M5)

**Every edge is re-resolved on every run; extraction is not.** An edge depends
on the rest of the corpus — a new document can resolve a link that dangled
yesterday — so edges cannot be carried forward. Extraction cannot depend on
anything but one document's own bytes (that is what `extracted` mode *means*),
so for a file whose `sha` is unchanged the prior record's `title`, `phrases`,
`terms`, `wlen` and `code` are reused verbatim.

That split is worth having because of where the time goes. Profiled at 1 000
documents, **92 % of a full ingest is `_fuxvec_code`** — the dense embedding —
and parsing plus edge resolution is under 5 %. Reusing extraction is therefore
almost all of the win at almost none of the risk, and it is what makes R5
(a 20-doc commit re-indexed in under a second) reachable at corpus sizes a
real repository has.

**A delta run is byte-identical to a full run.** Reuse is keyed on the content
sha and gated on the shard header still matching `store.HEADER`, so an analyzer
version bump invalidates every reused field at once rather than silently
mixing two analyzers in one index. `fux ingest --full` re-extracts regardless.

Two honest consequences, both recorded in ADR-MAINTENANCE:

- **Term-hash collision detection is complete only on a full run.** The tracker
  sees the raw terms of changed documents; an unchanged document contributes
  hashes it cannot un-hash. `--full` is the complete check.
- **A newly-available embedding bundle does not retro-fit `code`** onto
  unchanged documents until they change or `--full` runs.

`ver` bumps strictly on this record's own `sha` changing, independent of edges
(the M1 build-time decision on `ver` semantics). "Incremental" still also means
what `store.write_index` guarantees: a shard whose bytes come out identical is
left untouched on disk.

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
from .gitdir import Skipped, read_types, source_dirs, source_excludes, walk_sources
from .parse import parse


@dataclass
class IngestReport:
    written_shards: list[Path]
    doc_count: int
    changed_count: int
    skipped: list[Skipped]
    #: Documents whose extraction was carried forward instead of recomputed.
    reused_count: int = 0


def run(root: Path, *, refresh_urls: bool = False, full: bool = False) -> IngestReport:
    config = load_config(root)
    store_mod.ensure_layout(root)  # `.fux/` README + .gitignore, write-if-missing (ADR-DOTFUX)
    files, skipped = walk_sources(
        root,
        source_dirs(root, config.dirs_file),
        excludes=source_excludes(root, config.dirs_file),
        types=read_types(root),
    )
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

    file_shas = {f"file:{wf.rel_path}": store_mod.content_sha(wf.content) for wf in files}
    reusable = {} if full else _reusable(root, existing, file_shas)

    # Parsing is cheap and edges need it for every document, reused or not.
    parsed = {f"file:{wf.rel_path}": parse(wf.content) for wf in files}
    parsed |= {doc_id: parse(content) for doc_id, content in fresh.items()}
    # Extraction is the expensive half, so it runs only where it must.
    extracted = {
        doc_id: extract_mod.extract_fields(_loc_of(doc_id), doc)
        for doc_id, doc in parsed.items()
        if doc_id not in reusable
    }
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
        record = {
            "id": doc_id,
            "src": "git",
            "loc": wf.rel_path,
            "sha": file_shas[doc_id],
            "ver": 0,
            "mode": "extracted",
            "meta": "plain",
        }
        prior = reusable.get(doc_id)
        if prior is not None:
            # Carried forward: pure functions of bytes that have not changed.
            record.update({k: prior[k] for k in EXTRACTED_FIELDS if k in prior})
        else:
            fields = extracted[doc_id]
            record.update(
                {
                    "title": fields.title,
                    "phrases": fields.phrases,
                    "terms": store_mod.hash_terms(fields.terms, tracker),
                    "wlen": fields.wlen,
                }
            )
            if fields.code is not None:
                record["code"] = fields.code
        # Edges last, and never reused: they are the one field the rest of the
        # corpus can change without this document changing.
        record["edges"] = edges_mod.resolve(doc_id, scans[doc_id], known_ids, by_basename)
        record["ver"] = ver_for(doc_id, record["sha"])
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
            record["title_h"] = store_mod.title_hash(fields.title)
            # Materialise-first (P5): the bytes are already in hand this run,
            # so this costs a write, not a fetch. `write_index` refuses to
            # commit this record without it (`store/writer.py`).
            store_mod.DisplayCache(root).put(record["sha"], doc_id, fields.title)
        if fields.code is not None:
            record["code"] = fields.code
        records.append(record)

    records.extend(carried[doc_id] for doc_id in sorted(carried))

    written = store_mod.write_index(root, records)
    return IngestReport(
        written_shards=written,
        doc_count=len(records),
        changed_count=changed,
        skipped=skipped,
        reused_count=len(reusable),
    )


#: The fields extraction owns — pure functions of one document's own bytes, and
#: therefore the only ones a delta run may carry forward. `edges` is absent on
#: purpose, and `sha`/`ver` are recomputed because that is what they are for.
EXTRACTED_FIELDS = ("title", "phrases", "terms", "wlen", "code")


def _reusable(root: Path, existing: dict[str, dict], file_shas: dict[str, str]) -> dict[str, dict]:
    """Prior records whose extraction is still exactly right.

    Three conditions, all necessary:

    1. **The shard header matches `store.HEADER`.** It pins the schema id and
       the analyzer version, so a bump here invalidates every carried field at
       once. Mixing two analyzers inside one index would be undetectable
       afterwards and would break the differential law quietly.
    2. **The content sha is unchanged.** Extraction is a pure function of the
       document's bytes and its `loc`, both of which the sha and the id fix.
    3. **It is a `file:` record with `meta: plain`.** A `url:` record only
       reappears on a `--refresh-urls` run, and a hashed record's display
       fields were deliberately never stored in a reusable form.
    """
    paths = store_mod.iter_shard_paths(root)
    if not paths:
        return {}
    header, _ = store_mod.read_shard(paths[0])
    if header != store_mod.HEADER:
        return {}
    return {
        doc_id: record
        for doc_id, record in existing.items()
        if file_shas.get(doc_id) == record.get("sha")
        and record.get("src") == "git"
        and record.get("meta") == "plain"
    }


def _loc_of(doc_id: str) -> str:
    return doc_id.removeprefix("file:").removeprefix("url:")
