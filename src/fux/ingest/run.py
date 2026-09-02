"""`fux ingest` — orchestrates the git-dir adapter, the URL fetcher,
extractors, and the canonical store into one incremental build.

## Delta ingest — what is skipped, and what never is (M5)

**Every edge is re-resolved on every run; extraction is not.** An edge depends
on the rest of the corpus — a new document can resolve a link that dangled
yesterday — so edges cannot be carried forward. Extraction cannot depend on
anything but one document's own bytes (that is what `extracted` mode *means*),
so for a file whose `sha` is unchanged the prior record's `title`, `phrases`,
`terms` and `flen` are reused verbatim.

That split was worth having because of where the time went. Profiled at 1 000
documents, **92 % of a full ingest was the dense embedding** — and parsing plus
edge resolution under 5 %. **That cost is gone entirely** (2026-08-25): the
model and the vector lane were deleted, so extraction is now pure tokenisation.
Reuse is kept because it is still the difference between re-tokenising a corpus
and re-tokenising a commit, which is what makes R5 (a 20-doc commit re-indexed
in under a second) reachable at the sizes a real repository has.

**A delta run is byte-identical to a full run.** Reuse is keyed on the content
sha and gated on the shard header still matching `store.HEADER`, so an analyzer
version bump invalidates every reused field at once rather than silently
mixing two analyzers in one index. `fux ingest --full` re-extracts regardless.

Two honest consequences, both recorded in ADR-MAINTENANCE:

- **Term-hash collision detection is complete only on a full run.** The tracker
  sees the raw terms of changed documents; an unchanged document contributes
  hashes it cannot un-hash. `--full` is the complete check.
- **A new extraction rule does not retro-fit onto unchanged documents** until
  they change or `--full` runs. This used to be stated about the embedding
  bundle and `code`; both were deleted on 2026-08-25, but the property is the
  carry-forward's and outlives any particular field.

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

import sys

from dataclasses import dataclass, field, replace
from pathlib import Path

from .. import store as store_mod
from ..config import DEFAULT_TYPES_FILE as TYPES_FILE
from ..config import DEFAULT_URLS_FILE
from ..config import load as load_config
from ..errors import FuxError
from ..progress import NULL as _NULL_PROGRESS
from . import edges as edges_mod
from . import extract as extract_mod
from . import fuxignore, sourcelist, urlsrc
from .edges import TAG_PREFIX
from .gitdir import (
    UNFETCHED,
    Skipped,
    archived_dirs,
    is_archived_loc,
    read_types,
    source_dirs,
    source_excludes,
    walk_sources,
)
from .. import decode as decode_mod
from . import pii as pii_mod
from . import queue as queue_mod
from .parse import parse, parse_document


@dataclass
class IngestReport:
    written_shards: list[Path]
    doc_count: int
    changed_count: int
    skipped: list[Skipped]
    #: Documents whose extraction was carried forward instead of recomputed.
    reused_count: int = 0
    #: Advisory lines the run wants printed but that changed nothing it did —
    #: today, only `.fuxignore` duplicating an exclusion the old lists still
    #: carry. **On the report rather than printed here**: `run()` is called by
    #: the daemon and by the hook's runner as well as by a person at a
    #: terminal, and only one of those has a stdout worth writing to.
    warnings: list[str] = field(default_factory=list)
    #: URLs whose `validate()` token was unchanged, so no body was fetched
    #: (fork 3). **Not a skip and not a fetch** — the prior record is correct
    #: and was carried forward, which is the opposite of a failure. Counted
    #: separately so a healthy run cannot read as a broken one.
    validated: int = 0


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
        ignores=fuxignore.read(root),
    )
    warnings = fuxignore.duplicate_warnings(
        root, dirs_file=config.dirs_file, types_file=TYPES_FILE
    )
    # `walk_sources` returns its whole list at once — nothing to report a
    # count against until it has already finished (W-64's "none until done").
    with progress.phase("walk", len(files)) as p:
        p.update(len(files))
    if stopping():
        return None
    existing = _existing_index(root, full=full)
    existing_urls = {doc_id: rec for doc_id, rec in existing.items() if doc_id.startswith("url:")}

    fresh: dict[str, bytes] = {}  # url doc_id -> fetched content, this run only
    carried: dict[str, dict] = {}  # url doc_id -> prior record, reused verbatim
    url_meta: dict[str, str] = {}  # url doc_id -> the `meta` policy its line resolved to
    #: URL documents whose bytes arrived and yielded nothing — the same
    #: discovered need for a model that an unreadable file is (ADR-FETCHER
    #: decision 11, ruled 2026-08-28).
    unreadable_urls: list[queue_mod.QueueEntry] = []
    validated_count = 0
    if refresh_urls:
        if config.url is None:
            raise FuxError(f"--refresh-urls: no [sources.url] configured in {root / 'fux.toml'}")
        resolved = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
        url_meta = {f"url:{entry.url}": entry.meta for entry in resolved}
        # `url_meta` stays the **whole** list even under `only_urls`: it is what
        # reconciliation and carry-forward key on, so narrowing it here would
        # turn a scoped fetch into a corpus-wide deletion.
        to_fetch = resolved if only_urls is None else [e for e in resolved if e.url in only_urls]
        # Fork 3: hand the fetcher's `validate()` what we last saw, so a URL
        # whose token has not moved costs no body fetch. `known_tokens` is read
        # from gitignored runtime state, so a wiped `.fux/runtime/` means every
        # URL is simply fetched — the safe direction.
        from ..maintain import urlstate as _urlstate

        _prior = _urlstate.read(root)
        known_tokens = {
            url: h.token_sha for url, h in _prior.urls.items() if h.token_sha
        }
        validation: dict = {}
        fetched, url_skipped = urlsrc.fetch_all(
            root,
            to_fetch,
            config.url.config,
            max_parallel=config.url.max_parallel,
            known_tokens=known_tokens,
            validation_out=validation,
            acquired_max_bytes=config.url.acquired_max_bytes,
        )
        # ⚠ **A validated URL is NOT a skip and NOT a fetch.** Its prior record
        # is correct and is carried forward verbatim — the same treatment a
        # failed fetch gets, for a completely different reason, which is why the
        # two are counted separately and never merged.
        validated_count = len(validation.get("unchanged", ()))
        for url in validation.get("unchanged", ()):
            doc_id = f"url:{url}"
            if doc_id in existing_urls:
                carried[doc_id] = existing_urls[doc_id]
        skipped = skipped + url_skipped
        fresh = {f"url:{fu.url}": fu.content for fu in fetched}
        # W-82 3.1: record how this run went, per URL. Only on the networked
        # path -- an offline `fux ingest` fetches nothing, so it learns nothing
        # about any URL, and bumping the run counter there would age every URL
        # for a run that never looked at one. Advisory and gitignored: it
        # cannot change a committed byte, only what `fux doctor` can say.
        _observe_url_health(
            root,
            fetched=fetched,
            skipped=url_skipped,
            listed=[doc_id[4:] for doc_id in url_meta],
            token_shas=validation.get("token_shas") or {},
        )
        # A URL whose bytes arrived and yielded nothing needs a MODEL, exactly as
        # a scanned PDF on disk does — so it goes in the same committed queue,
        # under the same `doc_id` convention. Ruled by Arpit 2026-08-28; the
        # asymmetry was a gap, not a decision (ADR-FETCHER decision 11).
        #
        # ⚠ **`UNFETCHED` is excluded, and that is the whole care here.** A 404
        # or a timeout is not something enrichment discharges, and `queue.tsv` is
        # COMMITTED — queueing one would put a permanent work item in front of
        # the whole team that no amount of model time closes.
        url_unreadable = [s for s in url_skipped if s.kind != UNFETCHED]
        for s in url_unreadable:
            unreadable_urls.append(
                queue_mod.QueueEntry(
                    doc_id=f"url:{s.rel_path}",
                    # ⚠ **Empty, and honestly so.** A skipped URL's bytes were
                    # not retained -- there is nothing to hash. The file path's
                    # sha exists because the working tree still holds the file;
                    # a URL's does not, and inventing one would make the queue
                    # claim an identity it cannot check.
                    sha="",
                    reason=s.reason,
                )
            )
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

    # Parsing is cheap and edges need it for every document, reused or not.
    # W-86 P1: files route through the decoder plane, which returns `None` for a
    # document nothing could read (an image, a scanned PDF). Those are dropped
    # here rather than raising — one unreadable file must not end an ingest of
    # 10 000 — and §8's committed queue is where they will be recorded.
    #
    # Parsing moved ABOVE `file_shas` so an unreadable document contributes no
    # sha either: a sha with no record behind it would make the reuse map claim
    # a document the index does not contain.
    parsed = {}
    unreadable: list[queue_mod.QueueEntry] = []
    for wf in files:
        doc = parse_document(wf.content, wf.rel_path, root)
        if doc is not None:
            parsed[f"file:{wf.rel_path}"] = doc
        else:
            # W-86 P6: a document nothing could read is written down rather than
            # forgotten. This is the ONLY place fux discovers that a model is
            # needed — `fux enrich` derives its scope from a declared `dirs`
            # line, which cannot know a `.png` exists.
            unreadable.append(
                queue_mod.QueueEntry(
                    doc_id=f"file:{wf.rel_path}",
                    sha=store_mod.content_sha(wf.content),
                    reason=decode_mod.reason(wf.rel_path, root),
                )
            )

    file_shas = {
        f"file:{wf.rel_path}": store_mod.content_sha(wf.content)
        for wf in files
        if f"file:{wf.rel_path}" in parsed
    }
    # ⚠ **Editing `.fux/pii.toml` invalidates every carried extraction.**
    # Redaction happens BELOW, before `extract_fields`, so a rule change alters
    # what should be indexed for documents whose bytes did not change. Reuse is
    # keyed on the content sha alone, so without this a rule added today would
    # never reach a document that did not also change, and the index would hold
    # terms built under two policies with nothing recording which. The digest
    # lives in `runtime/` -- derived, gitignored, and rebuilt by being wrong once.
    pii_rules = pii_mod.load(root)
    pii_moved = _pii_ruleset_moved(root, pii_rules)
    reusable = {} if (full or pii_moved) else _reusable(root, existing, file_shas)
    # URL documents still arrive as fetcher-produced markdown, so they keep the
    # prose path untouched. That changes when fork H makes `fetch()` return
    # bytes; until it is ruled, nothing here moves.
    parsed |= {doc_id: parse(content) for doc_id, content in fresh.items()}

    # ⚠ **Redaction sits HERE and the position is load-bearing** (ADR-PII).
    # `file_shas` and `content_sha(fresh[...])` are already computed from the
    # RAW bytes above, and the record keeps those: a sha fingerprints the
    # source, and `refer` verifies a citation by fetching that source and
    # comparing. An index storing the sha of redacted text would report every
    # document with one PII hit as `stale` against its own unchanged source,
    # forever -- a defect that presents as a working feature.
    #
    # Everything downstream of this line -- terms, title, phrases, flen, the
    # display cache, the edge scan -- is built from redacted text. Everything
    # NOT downstream of it -- `.fux/acquired/`, the refer plane, `fux answer`'s
    # quotes -- still sees the document as it is. That asymmetry IS the policy:
    # redact what gets committed, leave alone what stays local.
    #
    # ⚠ **This phase walks `parsed`, and `parsed` holds document bodies only.**
    # Enrichment is a SECOND source of committed vocabulary and it does not
    # pass through here -- it is read from `.fux/enrich/` inside the extract
    # loop below. It gets its own pass, in `_enrichment_for`; until W-102 it
    # had none. If you add a third source of `ctx`, the sentence above does
    # not cover that one either.
    pii_hits: dict[str, int] = {}
    if pii_rules:
        with progress.phase("redact", len(parsed)) as p:
            for doc_id, doc in parsed.items():
                body, hits = pii_mod.redact(pii_rules, doc.body)
                if hits:
                    parsed[doc_id] = replace(doc, body=body)
                    for name, count in hits.items():
                        pii_hits[name] = pii_hits.get(name, 0) + count
                p.update(1)

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
            # W-76 Phase 8: pinned enrichment, keyed by the SOURCE content
            # sha. A document that changed no longer matches its enrichment
            # file, so the stale text is simply not found -- staleness is
            # structural here rather than a check someone has to remember.
            # ⚠ **`pii_rules` is passed HERE and the omission was the defect**
            # (W-102). The redact phase above walks `parsed`, which holds
            # document bodies; enrichment is read from `.fux/enrich/` on this
            # line and went straight into `ctx` without ever passing through
            # it. An email address written in enrichment prose therefore became
            # a committed term on a document whose own body had been redacted,
            # one screen below the comment promising everything downstream is
            # built from redacted text. ADR-PII decision 1 says the committed
            # index is redacted; the enrichment body is part of it.
            ctx, ctx_hits = _enrichment_for(root, file_shas.get(doc_id, ""), pii_rules)
            for name, count in ctx_hits.items():
                pii_hits[name] = pii_hits.get(name, 0) + count
            extracted[doc_id] = extract_mod.extract_fields(
                _loc_of(doc_id),
                parsed[doc_id],
                ctx,
            )
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
    # W-86 P6: the queue is written before the index, so a stopped run still
    # leaves the backlog it discovered. It is committed, so it obeys the same
    # rule the shards do — identical bytes are not rewritten, and an ingest over
    # an unchanged corpus leaves `git status` clean.
    # One queue, both planes. Sorted by `doc_id` inside `write`, so `file:`
    # and `url:` entries interleave deterministically and a re-run on an
    # unchanged corpus is still an empty diff.
    queue_mod.write(root, unreadable + unreadable_urls)

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
        # W-86 P6, the half that was missing: a document nothing could read is
        # already in `unreadable` and contributes no sha, no extraction and no
        # scan. It must contribute no RECORD either. Without this line the loop
        # reached `file_shas[doc_id]` for a file the parse plane had dropped and
        # raised `KeyError`, ending the whole ingest -- the precise failure
        # dropping-rather-than-raising was introduced to prevent. One
        # `%PDF` header nothing can decode took down a 10 000-document run.
        if doc_id not in parsed:
            continue
        record = store_mod.recordschema.build(
            id=doc_id,
            src="git",
            loc=wf.rel_path,
            sha=file_shas[doc_id],
            ver=0,
            mode="extracted",
            meta="plain",
        )
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
                    "flen": store_mod.trim(fields.flen),
                }
            )
        # Edges last, and never reused: they are the one field the rest of the
        # corpus can change without this document changing.
        record["edges"] = edges_mod.resolve(doc_id, scans[doc_id], known_ids, by_basename)
        record["ver"] = ver_for(doc_id, record["sha"])
        records.append(record)

    for doc_id in sorted(fresh):
        fields = extracted[doc_id]
        record = store_mod.recordschema.build(
            id=doc_id,
            src="url",
            loc=_loc_of(doc_id),
            sha=store_mod.content_sha(fresh[doc_id]),
            ver=0,
            mode="extracted",
            terms=store_mod.hash_terms(fields.terms, tracker),
            flen=store_mod.trim(fields.flen),
            edges=edges_mod.resolve(doc_id, scans[doc_id], known_ids, by_basename),
        )
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
        records.append(record)

    # `known_ids` is exactly this run's final id set — every parsed document
    # becomes a record, and so does every carried one — which is what makes it
    # the right thing to re-check a carried record's edges against (W-63).
    records.extend(_without_dangling_edges(carried[doc_id], known_ids) for doc_id in sorted(carried))

    # `write_index` groups by shard internally and offers no per-shard hook,
    # so this phase is a bookend around it rather than a live count —
    # honest under W-64's "counts, not clocks" (no bytes are interpolated).
    # W-76 Phase 2 — the two ranking priors, stamped as FACTS.
    #
    # Both are applied here rather than inside the per-document loops because
    # both are corpus-wide: `superseded` is a relation another document
    # declares, and the git walk is deliberately ONE subprocess for the whole
    # corpus rather than one per document (10 000 process spawns would dwarf
    # the entire rest of an ingest, measured at 9.5 s for 10 000 documents).
    #
    # The weights that read these are tunable; these values are not. That is
    # ADR-TUNE decision 1's split, and it is why they can live in the
    # committed index at all.
    from .priors import git_commit_times, superseded_ids

    retired = superseded_ids(records)
    commit_times = git_commit_times(root, [r["loc"] for r in records if r.get("src") == "git"])
    for record in records:
        if record["id"] in retired:
            record["superseded"] = True
        mtime = commit_times.get(record.get("loc"))
        if mtime is not None:
            record["mtime"] = mtime

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
        warnings=warnings,
        validated=validated_count,
    )


def _enrichment_for(root, sha: str, rules=()) -> tuple[str, dict[str, int]]:
    """The pinned enrichment body for a content sha, redacted, plus its hits.

    Returns the text **after** the frontmatter: the frontmatter is provenance
    for a human and for `fux enrich --check`, not vocabulary for the index.
    Indexing it would put the model's name and a date into `ctx` and let a
    document match a query for its own metadata.

    **Validated before use.** A malformed file is ignored rather than indexed,
    because the failure mode of trusting it is silent: whatever text is in
    there becomes searchable vocabulary attributed to this document.

    ## Why redaction happens here rather than in the phase named after it

    ADR-PII's redact phase walks `parsed`, and `parsed` holds **document
    bodies**. Enrichment is a second source of committed vocabulary that never
    enters that map — it is read from `.fux/enrich/` at extraction time — so it
    needs its own pass or it has none. W-102: it had none, and the leak was
    into `.fux/index/` itself, not merely into the enrichment file.

    ⚠ **The sha is not recomputed and must not be.** `sha` is the *source
    document's* content sha, taken from raw bytes before any redaction, and it
    is both this file's name and the key `validate()` compares. Redacting the
    body changes what is indexed and changes nothing about identity — the same
    ordering ADR-PII decision 3 pins for documents, for the same reason: a sha
    over redacted text would report every enriched document `stale` against its
    own unchanged source.

    ⚠ **The frontmatter is deliberately outside the pass.** It is stripped
    before indexing already (ADR-ENRICH decision 8), so nothing in it reaches a
    committed term, and running rules over a `model:` value would refuse a file
    for text the index never sees. `fux enrich --check` draws the same line.
    """
    if not sha:
        return "", {}
    from ..enrich import enrich_path, match_end, validate

    path = enrich_path(root, sha)
    if not path.is_file() or validate(path, expected_sha=sha) is not None:
        return "", {}
    text = path.read_text(encoding="utf-8", errors="replace")
    body = text[match_end(text) :].strip()
    if not rules:
        # Byte-for-byte the pre-W-102 path for a repo with no `pii.toml`,
        # which is most of them. `redact()` would return the text unchanged
        # anyway; short-circuiting says so rather than relying on it.
        return body, {}
    return pii_mod.redact(rules, body)


#: How often the cooperative stop is polled inside the two per-document loops.
#: A stop is noticed within this many documents, which at any corpus size fux
#: is judged at is well under a second.
_STOP_EVERY = 64

#: The fields extraction owns — pure functions of one document's own bytes, and
#: therefore the only ones a delta run may carry forward. `edges` is absent on
#: purpose, and `sha`/`ver` are recomputed because that is what they are for.
#: Pure functions of bytes that have not changed, so a delta ingest may reuse
#: the prior value. **Read from the record schema** (W-83b) rather than
#: restated, because this tuple and the record's shape lived in different
#: modules and nothing compared them.
#:
#: ⚠ `edges` is deliberately absent, and it is the interesting exclusion: it is
#: the one field the rest of the corpus can change without this document
#: changing, so carrying it forward would freeze a link that a newly added
#: document should have resolved.
EXTRACTED_FIELDS = store_mod.recordschema.carried_fields()



def _existing_index(root: Path, *, full: bool) -> dict[str, dict]:
    """The prior index, or `{}` when `--full` is discharging a schema migration.

    ADR-INDEX-LIFECYCLE decision 10 owes a full re-ingest on every index older
    than the current analyzer and names `fux ingest --full` as the command that
    pays it. Reading the prior index unconditionally made that command **refuse
    the exact index it exists to replace** — the migration path was documented
    and unreachable.

    `--full` re-extracts every document from source anyway, so a foreign index
    contributes nothing to it *except* `url:` records, which came from the
    network and cannot be rebuilt offline. So:

    - **no `url:` records** — the foreign index is discarded and `--full`
      rebuilds from committed sources. Nothing is lost that a re-extraction
      does not restore.
    - **any `url:` records** — refuse, and name them. Deleting them silently
      is the failure this whole seam exists to prevent, and there is no offline
      way to carry them: their content is not recoverable from the shard,
      only their identity is.

    A delta run (`full=False`) is unchanged: it still reads, and still refuses
    a foreign index loudly, because carry-forward genuinely cannot proceed.
    """
    if not (full and store_mod.index_is_foreign(root)):
        return store_mod.read_index(root)

    header = store_mod.index_header(root) or {}
    stranded = store_mod.foreign_url_ids(root)
    if stranded:
        shown = "\n  ".join(stranded[:10])
        more = f"\n  ... and {len(stranded) - 10} more" if len(stranded) > 10 else ""
        raise FuxError(
            f"--full: the committed index was written by an older fux "
            f"(_format={header.get('_format')!r}, analyzer={header.get('analyzer')!r}) "
            f"and holds {len(stranded)} url: record(s) that a re-ingest cannot rebuild "
            f"offline:\n  {shown}{more}\n"
            f"Re-fetch them on a networked run instead: `fux update`."
        )
    return {}


#: Where the PII ruleset digest is remembered between runs. `runtime/` because
#: it is derived and gitignored, and because being wrong once is self-healing:
#: a missing file reads as "moved", which costs one full extraction and then
#: settles. That is the right failure direction -- the opposite (reading as
#: "unchanged") would silently keep terms built under retired rules.
PII_DIGEST_FILE = "pii-digest"


def _pii_ruleset_moved(root: Path, rules) -> bool:
    """Has `.fux/pii.toml` changed since the last run? Records the new answer.

    A repo with no rules writes no state and behaves exactly as it did before
    this feature existed -- the empty digest is compared against an absent
    file, both read as "", and nothing is created.
    """
    from ..store import fuxdir

    current = pii_mod.digest(rules)
    path = fuxdir.fux_dir(root) / "runtime" / PII_DIGEST_FILE
    try:
        previous = path.read_text(encoding="utf-8").strip()
    except OSError:
        previous = ""
    if current == previous:
        return False
    try:
        if current:
            fuxdir.derived_dir(root, "runtime")
            path.write_text(current + "\n", encoding="utf-8")
        elif path.exists():
            path.unlink()
    except OSError:
        # A digest we could not record means the next run re-extracts too.
        # Wasteful, never wrong -- and never a reason to fail an ingest.
        pass
    # ⚠ An empty previous digest with rules present is a repo that has never
    # run with redaction on, which genuinely needs the full pass.
    return True


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


def _observe_url_health(root: Path, *, fetched, skipped, listed, token_shas=None) -> None:
    """Record this networked run's per-URL outcome (W-82 3.1).

    **Best-effort, and that is deliberate.** This is a reporting plane; a
    failure to write it must never fail an ingest that otherwise succeeded.
    The same reasoning ADR-MAINTENANCE decision 3 applies to hooks: a
    diagnostic that can break the thing it diagnoses is worse than no
    diagnostic.
    """
    from ..maintain import urlstate

    try:
        urlstate.observe(
            root,
            fetched={fu.url: store_mod.content_sha(fu.content) for fu in fetched},
            failed=[s.rel_path for s in skipped],
            listed=listed,
            token_shas=token_shas or {},
        )
    except Exception:  # pragma: no cover - a report must not break the run
        return
    _report_dead_urls(root, [s.rel_path for s in skipped])


def _report_dead_urls(root: Path, failed_now: list[str]) -> None:
    """Name URLs whose failure STREAK has reached the bar (W-82 fork 8).

    ⚠ **The gap this closes: one failure and forty look identical.** Every
    failed fetch already prints as a skip with a reason, so a URL dead for
    three weeks reads exactly like one that blipped once — and the streak that
    tells them apart was only visible if somebody thought to run `fux doctor`.

    **The person who can fix a dead URL is the one who just ran `update`.**
    Telling them at `doctor` time means telling them when they went looking,
    which is not when it broke.

    **Only URLs that failed THIS run are considered** — a URL that succeeded
    has had its streak reset, so it cannot be dead, and walking the whole state
    would re-report URLs this run never touched.

    ⚠ **It never exits non-zero.** A wiki that moved is a fact outside the
    repo; turning it into a build break would fail CI on every run until
    somebody edits a source list, which is a worse trade than a loud line.

    Best-effort, like everything else on this plane.
    """
    if not failed_now:
        return
    from ..maintain import urlstate

    try:
        state = urlstate.read(root)
    except Exception:  # pragma: no cover - a report must not break the run
        return
    for url in sorted(failed_now):
        health = state.urls.get(url)
        if health is None or health.fail_streak < urlstate.FAILING_STREAK:
            continue
        print(
            f"note: {url} has now failed {health.fail_streak} runs in a row. "
            f"Check the URL, or `fux remove {url}` if it is gone - a dead entry "
            "is re-fetched on every run and its indexed content never changes",
            file=sys.stderr,
        )


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
