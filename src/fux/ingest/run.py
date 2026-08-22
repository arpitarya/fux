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
never touches the network. Only the fenced paths load a consumer fetcher and
fetch; a configured URL whose fetch fails keeps its prior record, because a
transient network failure must never delete a document.

**Reconciliation is not fetching, and does not wait for it (W-63).** A URL no
longer in `.fux/sources/urls` disappears on the **next run, networked or not**
— its record is carried forward only while its line exists. This sentence used
to say the opposite, and said it as though it were the design: reconciliation
"happens only on the run that opted into the network". That made removing a
document require the one capability removal has no use for, and it is the
defect `_listed_url_ids` closes.

**A carried record's edges are re-checked, never trusted.** Extraction is a
pure function of one document's bytes and can be carried forward; an edge is a
claim about *another* document, so a carried record can point at something
this run no longer holds. `_without_dangling_edges` drops those, which is what
keeps the derived graph plane free of targets no verb can explain.

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
from ..config import DEFAULT_URLS_FILE
from ..config import load as load_config
from ..errors import FuxError
from ..progress import NULL as _NULL_PROGRESS
from . import edges as edges_mod
from . import extract as extract_mod
from . import sourcelist, urlsrc
from .edges import TAG_PREFIX
from .gitdir import (
    Skipped,
    archived_dirs,
    is_archived_loc,
    read_types,
    source_dirs,
    source_excludes,
    walk_sources,
)
from .parse import parse


@dataclass
class IngestReport:
    written_shards: list[Path]
    doc_count: int
    changed_count: int
    skipped: list[Skipped]
    #: Documents whose extraction was carried forward instead of recomputed.
    reused_count: int = 0


def run(
    root: Path,
    *,
    refresh_urls: bool = False,
    only_urls: set[str] | None = None,
    full: bool = False,
    progress=None,
    should_stop=None,
) -> IngestReport | None:
    """Walk the configured sources into the committed index.

    `only_urls` narrows **which listed URLs are fetched** on a networked run;
    every other listed URL is carried forward exactly as a failed fetch would
    be. It is what lets `fux add <url>` and `fux update <url>` touch the
    network for one document without a second write path into the index —
    the whole run still ends in the one `write_index` call below, so a scoped
    fetch and a full refresh produce the same bytes for everything they agree
    about (L3). `None` means every listed URL.

    `should_stop` is the **cooperative stop** the deferred runner is halted by
    (W-66 Phase 2, ADR-MAINTENANCE decision 1d). It is polled between units of
    work and **only ever before `write_index`**: once bytes start reaching a
    committed shard the run finishes, because `write_index` is the single path
    into the committed plane and a partial shard is the one outcome worse than
    a late one. Returning early therefore leaves the index byte-clean and the
    dirty list untouched.

    **Returns `None` if and only if `should_stop` was supplied and fired.** A
    caller that passes nothing can never receive it, which is why every
    existing call site is unaffected by the widened return type.
    """
    progress = progress or _NULL_PROGRESS
    stopping = should_stop or (lambda: False)
    # Snapshot first, before any work: a commit landing mid-run appends to the
    # list, and only what was pending when we *started* is ours to subtract.
    from ..maintain import dirty as dirty_mod

    covered = dirty_mod.read(root)
    config = load_config(root)
    store_mod.ensure_layout(root)  # `.fux/` README + .gitignore, write-if-missing (ADR-DOTFUX)
    files, skipped = walk_sources(
        root,
        source_dirs(root, config.dirs_file),
        excludes=source_excludes(root, config.dirs_file),
        types=read_types(root),
    )
    # `walk_sources` returns its whole list at once — nothing to report a
    # count against until it has already finished (W-64's "none until done").
    with progress.phase("walk", len(files)) as p:
        p.update(len(files))
    if stopping():
        return None
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
        # `url_meta` stays the **whole** list even under `only_urls`: it is what
        # reconciliation and carry-forward key on, so narrowing it here would
        # turn a scoped fetch into a corpus-wide deletion.
        to_fetch = resolved if only_urls is None else [e for e in resolved if e.url in only_urls]
        fetched, url_skipped = urlsrc.fetch_all(root, to_fetch, config.url.config)
        skipped = skipped + url_skipped
        fresh = {f"url:{fu.url}": fu.content for fu in fetched}
        for doc_id in url_meta:
            if doc_id not in fresh and doc_id in existing_urls:
                carried[doc_id] = existing_urls[doc_id]  # failed fetch keeps the prior record
    else:
        # Offline, and reconciled anyway (W-63). A `url:` record survives only
        # while its line does: de-listing is a fact about a committed file,
        # and reading a file is not a network call. **Fetching** needs the
        # fenced path; deletion never did.
        listed = _listed_url_ids(root, config, existing_urls)
        carried = {i: record for i, record in existing_urls.items() if i in listed}

    file_shas = {f"file:{wf.rel_path}": store_mod.content_sha(wf.content) for wf in files}
    reusable = {} if full else _reusable(root, existing, file_shas)

    # Parsing is cheap and edges need it for every document, reused or not.
    parsed = {f"file:{wf.rel_path}": parse(wf.content) for wf in files}
    parsed |= {doc_id: parse(content) for doc_id, content in fresh.items()}
    # Extraction is the expensive half — 92% of a full ingest, profiled at
    # 1 000 docs — so it is where the bar earns its place (W-64).
    to_extract = [doc_id for doc_id in parsed if doc_id not in reusable]
    extracted: dict[str, extract_mod.Extracted] = {}
    with progress.phase("extract", len(to_extract)) as p:
        for n, doc_id in enumerate(to_extract):
            # Polled every `_STOP_EVERY` documents rather than every one: the
            # check is a file read, and a stop noticed a few documents late is
            # still sub-second while a per-document poll would put a syscall
            # on the hot loop the progress plane exists to show moving.
            if n % _STOP_EVERY == 0 and stopping():
                return None
            extracted[doc_id] = extract_mod.extract_fields(_loc_of(doc_id), parsed[doc_id])
            p.update(1, detail=_loc_of(doc_id))
    # Re-resolved every run (M5): a new document can resolve a link that
    # dangled yesterday, so this cannot be carried forward like extraction.
    scans: dict[str, list] = {}
    with progress.phase("edges", len(parsed)) as p:
        for n, (doc_id, doc) in enumerate(parsed.items()):
            if n % _STOP_EVERY == 0 and stopping():
                return None
            scans[doc_id] = edges_mod.scan(doc)
            p.update(1)
    known_ids = set(parsed) | set(carried)
    # `code`-span basename resolution stays file-only: a backtick path is a
    # claim about the repo, never about a URL.
    by_basename = edges_mod.basename_index({i for i in known_ids if i.startswith("file:")})

    tracker = store_mod.CollisionTracker()
    records: list[dict] = []
    changed = 0
    # ADR-ARCHIVED-CONTENT decision 1: a record from a declared-archived source
    # says so on the record, the way `mode` and `meta` already do, so a record
    # read years later states the rule it was written under instead of having it
    # re-derived by whoever reads it. **Declared, never a path convention** —
    # this reads the same `.fux/sources/dirs` line the grammar parses.
    archived_srcs = frozenset(archived_dirs(root, config.dirs_file))

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
        # Absent when false, so a live record's shape is unchanged and no
        # existing consumer's parse breaks (decision 1).
        if archived_srcs and is_archived_loc(wf.rel_path, archived_srcs):
            record["archived"] = True
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

    # `known_ids` is exactly this run's final id set — every parsed document
    # becomes a record, and so does every carried one — which is what makes it
    # the right thing to re-check a carried record's edges against (W-63).
    records.extend(_without_dangling_edges(carried[doc_id], known_ids) for doc_id in sorted(carried))

    # `write_index` groups by shard internally and offers no per-shard hook,
    # so this phase is a bookend around it rather than a live count —
    # honest under W-64's "counts, not clocks" (no bytes are interpolated).
    shard_total = len({store_mod.shard_for(r["id"]) for r in records})
    # **The last stop point, and it is here on purpose.** Past this line the
    # run is committed to finishing: `write_index` is the only path bytes reach
    # a committed shard by, and stopping inside it is how a partial shard gets
    # written. Everything above is re-derivable from the sources for free.
    if stopping():
        return None
    with progress.phase("write", shard_total, "shards") as p:
        written = store_mod.write_index(root, records)
        p.update(shard_total)

    # W-66: a run that reaches here indexed the whole corpus, so the snapshot
    # it took at the top is now covered. **Subtracted, never cleared** — an id
    # recorded by a commit that landed while this run was in flight is not in
    # `covered` and stays pending (ADR-MAINTENANCE decision 1d). A run that
    # was stopped or died never reaches this line, so the list survives it.
    dirty_mod.discard(root, covered)

    return IngestReport(
        written_shards=written,
        doc_count=len(records),
        changed_count=changed,
        skipped=skipped,
        reused_count=len(reusable),
    )


#: How often the cooperative stop is polled inside the two per-document loops.
#: A stop is noticed within this many documents, which at any corpus size fux
#: is judged at is well under a second.
_STOP_EVERY = 64

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


def _listed_url_ids(root: Path, config, existing_urls: dict[str, dict]) -> set[str]:
    """The `url:` ids `.fux/sources/urls` currently declares (W-63).

    **Offline by construction.** This reads a committed file and nothing else;
    it is the reconciliation half of URL ingest, which never needed the
    network and until now was only reachable through the path that does.

    Two deliberate details:

    - **Not read at all when there is nothing to reconcile.** A repo with no
      `url:` records never touches the list, so a corpus that has only ever
      had directories is unaffected by this function existing.
    - **A missing list with surviving `url:` records is a loud error**, not a
      silent mass deletion. The alternative readings are both worse: treating
      absence as "nothing is listed" would empty every URL document because a
      file went missing, and treating it as "carry everything" is the defect
      this fixes. `dirs` already fails loudly on the same condition.
    """
    if not existing_urls:
        return set()
    rel_path = config.url.urls_file if config.url is not None else DEFAULT_URLS_FILE
    entries = sourcelist.read(
        root,
        rel_path,
        sourcelist.URLS,
        missing_hint=(
            f"the index holds {len(existing_urls)} url document(s) and nothing says which URLs "
            "belong to this corpus. Restore the file, or run `fux remove <URL>` for each"
        ),
    )
    return {f"url:{entry.value}" for entry in entries}


def _without_dangling_edges(record: dict, known_ids: set[str]) -> dict:
    """A carried record with edges to documents this run does not hold removed.

    `graph/model.edges_from_records` lifts a record's `edges` with no
    validation, on the documented promise that `ingest/edges.py` already
    dropped the dangling ones. **That promise holds only for a record
    re-resolved this run.** A carried `url:` record's edges were resolved
    against a *previous* run's corpus, so a document deleted since survives as
    an edge target — visible in the derived graph plane as an edge into a node
    no verb can explain.

    `tag:` targets are kept unconditionally: a tag node is invented by the
    edge itself and is never a document, so it cannot dangle.

    Returns the record **unchanged and uncopied** when nothing is dropped, so
    a run that changes nothing still writes byte-identical shards (L3).
    """
    edges = record.get("edges")
    if not edges:
        return record
    kept = [e for e in edges if e["dst"].startswith(TAG_PREFIX) or e["dst"] in known_ids]
    if len(kept) == len(edges):
        return record
    return {**record, "edges": kept}


def _loc_of(doc_id: str) -> str:
    return doc_id.removeprefix("file:").removeprefix("url:")
