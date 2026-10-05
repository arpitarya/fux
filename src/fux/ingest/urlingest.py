"""The URL branch of ingest — reconciliation, re-acquisition and URL health.

**Owned by [SR-URL-INGEST](../../../records/0107_url-ingest.md)** since
2026-10-05 (W-261, Arpit's ruling that every `kind: component` record owns a
file). A pure move out of `ingest/run.py`, which keeps the walk and calls these
four (SR-INGEST's). What is here is decision 4's offline reconciliation
(`listed_url_ids`), the offline re-derivation of retained `url:` bytes
(`reacquire_urls`), and the networked run's per-URL outcome
(`observe_url_health`, `report_dead_urls`). The fetch itself is
`urlsrc.fetch_all` (SR-FETCHER's contract).
"""

from __future__ import annotations

import sys
from pathlib import Path

from .. import store as store_mod
from ..config import load as load_config
from ..errors import FuxError
from . import sourcelist, urlsrc

__all__ = ["listed_url_ids", "observe_url_health", "reacquire_urls", "report_dead_urls"]


def reacquire_urls(
    root: Path, carried: dict[str, dict], config
) -> tuple[dict[str, bytes], list[str], set[str]]:
    """Retained `url:` bytes, ready to re-enter the fresh path.

    Returns `(bytes_by_doc_id, stranded_locs, doc_ids_seen)`. ⚠ **The third
    value was `meta_by_doc_id` until W-194** (2026-09-20) deleted `meta`; it is
    now just the ids this path resolved, which is what the caller actually
    needed from it — `url_listed` keys reconciliation and carry-forward.

    **`refer.source.from_acquired` is IMPORTED, never reimplemented.** It decodes
    and sanitizes the blob exactly as ingest did, which is the whole reason the
    re-derived record's `sha` still equals the indexed one — a `sha` fingerprints
    the SOURCE, and an index storing the sha of redacted text would report every
    redacted document as permanently stale against its own unchanged source. A
    second copy of that pipeline is how the two would drift by one line and make
    that true anyway.

    **The URL list is read here, offline.** `resolve_urls(read_urls(...))` opens
    two committed files and no socket, so `archived` and the rest resolve on a
    plain `fux ingest` — which is the gap SR-PII named as *"the fresh-record
    path resolves `meta` and `archived` from the URL list, which an offline run
    does not read"*. It does now, on this path, and `meta` no longer exists.

    ⚠ **A URL with no retained blob is STRANDED, not silently kept.** Nothing
    can re-redact it without the network, so its record stays exactly as it is
    and its `loc` comes back for `doctor` to name. The alternative — dropping it
    — would delete a document because a policy changed, which is the one thing a
    redaction change must never do.

    **Never raises.** A blob that will not decode is stranded like an absent one;
    a re-derivation that fails must not fail an ingest that otherwise succeeded.
    """
    from ..refer import source as source_mod
    from .run import _loc_of

    if config.url is None:
        return {}, [], set()
    try:
        resolved = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
    except (FuxError, OSError):
        return {}, [], set()
    entries = {f"url:{entry.url}": entry for entry in resolved}

    out: dict[str, bytes] = {}
    seen: set[str] = set()
    stranded: list[str] = []
    # Sorted: the same tree must give the same index on two machines (L4), and
    # this set feeds `fresh`, whose iteration order decides record order.
    for doc_id in sorted(carried):
        entry = entries.get(doc_id)
        if entry is None:
            continue  # de-listed; reconciliation drops it, not this
        loc = _loc_of(doc_id)
        fetched = source_mod.from_acquired(root, doc_id, loc)
        if fetched is None:
            stranded.append(loc)
            continue
        out[doc_id] = fetched.content
        seen.add(doc_id)
    return out, stranded, seen


def observe_url_health(root: Path, *, fetched, skipped, listed, token_shas=None) -> None:
    """Record this networked run's per-URL outcome (W-82 3.1).

    **Best-effort, and that is deliberate.** This is a reporting plane; a
    failure to write it must never fail an ingest that otherwise succeeded.
    The same reasoning SR-MAINTENANCE decision 3 applies to hooks: a
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
    report_dead_urls(root, [s.rel_path for s in skipped])


def report_dead_urls(root: Path, failed_now: list[str]) -> None:
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
        url_source = load_config(root).url
    except Exception:  # pragma: no cover - a report must not break the run
        return
    if url_source is None:  # no [sources.url]: nothing was fetched to fail
        return
    streak = url_source.failing_streak  # `fux.toml [sources.url] failing_streak`
    for url in sorted(failed_now):
        health = state.urls.get(url)
        if health is None or health.fail_streak < streak:
            continue
        print(
            f"note: {url} has now failed {health.fail_streak} runs in a row. "
            f"Check the URL, or `fux remove {url}` if it is gone - a dead entry "
            "is re-fetched on every run and its indexed content never changes",
            file=sys.stderr,
        )


def listed_url_ids(root: Path, config, existing_urls: dict[str, dict]) -> set[str]:
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
    rel_path = config.urls_file
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
