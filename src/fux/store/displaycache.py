"""A content-addressed, gitignored cache of display text for `hashed` records.

PRIORITY.md P5, Arpit's rulings 2026-08-21 (`meta-privacy.compare.md`,
reopened). `meta: hashed` stops meaning *unreadable*: ingest already holds a
non-git document's bytes in memory before it writes the record (`fresh` in
`ingest/run.py`), so writing the derived title here costs a write, not a
fetch. `store/writer.py` then refuses to commit a `hashed` record unless this
cache already holds its `sha` — a reader-facing surface degrades to `title_h`
only when the cache has gone cold *after* the record was written, never
because ingest skipped the step.

## Content-addressed, not TTL — and why that is a different cache from ARC

Keyed on `sha` alone, like `refer/arc.py`'s `(loc, sha)` half: a document's
title is a pure function of its bytes, so a hit is correct for as long as it
exists, with no clock involved and no notion of staleness. This is
deliberately **not** `refer/fetchcache.py` (TTL, keyed on `loc`, serves
*before* a sha is confirmed) and **not** `refer/arc.py` (in-memory, one
query process) — a third, disk-resident, ingest-populated store, because none
of the other two are ever populated at ingest time or read across process
runs by `ask`/`find`/`explain`/`answer`/graph labels.

## Bounded, and eviction is silent by design

Titles are small, so eviction should be rare in practice — but an unbounded
cache is the slow-leak shape `ADR-CACHE` already refused for the TTL store,
and the same reasoning applies here. `max_bytes` bounds total size; entries
evict oldest-written first. A miss here is never an error: the reader
degrades to a labelled `title_h`, and `ingest` (for a *carried-forward*
record whose cache went cold) re-fetches to repopulate rather than commit
without one — the "force a re-fetch" ruling on the delta-path fork.

**No clock, unlike the TTL store.** `ADR-CACHE` decision 8 is deliberate:
"wall clock lives in the TTL store and nowhere else." This cache does not
need real time — only *which entry is older* to break a tie under
`max_bytes` — so eviction orders by a monotonic `seq` written into each
entry, not by `time.time()` or file mtime.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["DisplayCache", "CACHE_DIR", "DEFAULT_MAX_BYTES"]

CACHE_DIR = "display-cache"

#: No number was specified for this either (like `fetchcache.DEFAULT_MAX_BYTES`)
#: — chosen to bound a per-machine disposable cache of small text entries
#: without requiring active management. Tune via `DisplayCache(..., max_bytes=)`.
DEFAULT_MAX_BYTES = 50 * 1024 * 1024


class DisplayCache:
    """`sha -> (doc_id, title)` under `.fux/runtime/display-cache/`.

    Derived and gitignored, like every other `runtime/` child. Deleting it is
    always safe: the next `ask`/`explain`/... on an affected document degrades
    to a labelled hash instead of a title, and the next ingest that touches
    that document's sha repopulates it.
    """

    def __init__(self, root: Path, *, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        from ..derive import format as fmt

        self.directory = fmt.runtime_dir(root) / CACHE_DIR
        self.max_bytes = max_bytes

    def _path(self, sha: str) -> Path:
        return self.directory / f"{sha}.json"

    def get(self, sha: str) -> str | None:
        """The cached title for `sha`, or `None` on a miss (including a corrupt entry)."""
        path = self._path(sha)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return str(payload["title"])
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            # A corrupt entry is a miss, never an error — the cache is
            # disposable by construction and a query must not die for it.
            return None

    def put(self, sha: str, doc_id: str, title: str) -> None:
        """Write an entry, evicting the oldest others first if it would not fit."""
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._path(sha)
        payload = {"sha": sha, "doc_id": doc_id, "title": title, "seq": self._next_seq(keep=path)}
        body = json.dumps(payload)
        incoming = len(body.encode("utf-8"))
        if incoming > self.max_bytes:
            return
        self._evict_to_fit(incoming, keep=path)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(path)

    def _next_seq(self, *, keep: Path) -> int:
        """One past the highest `seq` among every entry but `keep` — so
        re-writing an existing sha still counts as the newest write, the way
        `refer/fetchcache.py`'s `fetched_at` does on a re-fetch."""
        highest = -1
        for path in self.directory.glob("*.json") if self.directory.is_dir() else ():
            if path == keep:
                continue
            highest = max(highest, self._seq_of(path))
        return highest + 1

    @staticmethod
    def _seq_of(path: Path) -> int:
        try:
            return int(json.loads(path.read_text(encoding="utf-8"))["seq"])
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            return -1  # unreadable entries are evicted first

    def _evict_to_fit(self, incoming: int, *, keep: Path) -> None:
        """Delete entries, oldest `seq` first, until `incoming` more bytes fit
        under `max_bytes`. `keep` is about to be overwritten by the caller, so
        its current size is freed without deleting the file out from under the
        write that follows.
        """
        sizes = {p: p.stat().st_size for p in self.directory.glob("*.json")}
        total = sum(sizes.values()) - sizes.get(keep, 0)
        if total + incoming <= self.max_bytes:
            return

        for path in sorted((p for p in sizes if p != keep), key=self._seq_of):
            if total + incoming <= self.max_bytes:
                break
            total -= sizes[path]
            path.unlink(missing_ok=True)

    def clear(self) -> None:
        for path in self.directory.glob("*.json"):
            path.unlink(missing_ok=True)
