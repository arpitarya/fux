"""A TTL-bounded, gitignored local cache for `url:` fetches.

W-60, Arpit's verdict F (2026-08-20). Separate from ARC on purpose — see below.

## Why this exists, and why it is not a latency optimisation

Confluence Cloud's REST API is rate-limited against a shared hourly point
budget, and Atlassian's own avoidance guidance is *"cache stable responses"*.
An agent asking ten questions about the same runbook must not fetch it ten
times: at enterprise scale that is not slow, it is **throttled**, and a
throttled fetch degrades to `unverified` for reasons that have nothing to do
with the document.

So this is an enterprise reality treated as a design input, and it is why the
build did not wait for R4.

## Why it is NOT stored in ARC, and why that separation is load-bearing

ARC is keyed `(loc, sha)` — the **content address is in the key**, so a hit is
byte-identical to what a fetch would have returned or it is not a hit. That is
the whole proof behind ADR-REFER decision 9's "cannot change the answer".

A TTL entry is served **before** the sha is confirmed: that is what a TTL *is*.
Putting it in ARC's keyspace would mean serving bytes under a key that no
longer proves anything, and the proof would be gone with no test to notice.
**Two stores, provably separate.** ARC caches what a fetch returned; this
caches whether a fetch is needed at all.

## Wall clock lives here, and only here

A TTL needs real time. That is the same treatment `runtime/stamp.json` already
gets: a **gitignored, per-machine, non-reproducible** artifact that never
reaches a committed record. Nothing here writes to `.fux/index/`, and the
committed record still carries no timestamp — [W-58](../../work/open/W-58-no-recorded-ingest-time.md)
and `record-freshness.compare.md` are **untouched by this** and remain a
separate open question.

## `cached` is a fourth verdict, never a synonym for `current`

ADR-REFER decision 6's three-state guarantee exists so nothing can collapse
"we did not look" into "we looked and it was fine". A TTL hit is a *fifth*
epistemic position — *we looked recently* — and folding it into `current`
would be decision 4's "knob that lies" reappearing in a new place. It carries
its `age_seconds` so a caller can decide for itself.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

__all__ = ["FetchCache", "CacheEntry", "CACHE_DIR", "DEFAULT_TTL_SECONDS", "DEFAULT_MAX_BYTES"]

CACHE_DIR = "fetch-cache"

#: Arpit's number, 2026-08-20. Only in force when a caller opts in — the
#: `Policy` default is 0, which disables the cache entirely.
DEFAULT_TTL_SECONDS = 300

#: No number was specified for this (PRIORITY.md P4, 2026-08-21) — chosen to
#: bound a per-machine disposable cache without requiring active management.
#: Tune it via the `FetchCache(..., max_bytes=...)` constructor argument.
DEFAULT_MAX_BYTES = 500 * 1024 * 1024


@dataclass(frozen=True)
class CacheEntry:
    loc: str
    fetched_at: int
    fetched_sha: str
    content: bytes

    def age_seconds(self, now: int) -> int:
        # Clamped at zero: a clock that moved backwards must not produce a
        # negative age that makes a stale entry look infinitely fresh.
        return max(0, now - self.fetched_at)


class FetchCache:
    """`loc -> (fetched_at, sha, bytes)` under `.fux/runtime/fetch-cache/`.

    Derived and gitignored, like every other `runtime/` child. Deleting it is
    always safe: the next query fetches.
    """

    def __init__(self, root: Path, *, clock=time.time, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        from ..derive import format as fmt

        self.directory = fmt.runtime_dir(root) / CACHE_DIR
        # Injected so a test can pin it. The engine's *answers* never read the
        # clock; only the decision of whether to re-fetch does.
        self._clock = clock
        self.max_bytes = max_bytes

    def _path(self, loc: str) -> Path:
        # Hashed filename: a `loc` is a URL and contains `/`, `?` and `:`.
        digest = hashlib.sha256(loc.encode("utf-8")).hexdigest()[:32]
        return self.directory / f"{digest}.json"

    def now(self) -> int:
        return int(self._clock())

    def get(self, loc: str, ttl_seconds: int) -> CacheEntry | None:
        """A live entry, or `None`. `ttl_seconds <= 0` disables the cache.

        The disable check comes **first and unconditionally**, so a caller who
        never opted in cannot be served a cached byte by any code path.
        """
        if ttl_seconds <= 0:
            return None
        path = self._path(loc)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            entry = CacheEntry(
                loc=payload["loc"],
                fetched_at=int(payload["fetched_at"]),
                fetched_sha=payload["fetched_sha"],
                content=bytes.fromhex(payload["content"]),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            # A corrupt entry is a cache miss, never an error. The cache is
            # disposable by construction and a query must not die for it.
            return None
        if entry.loc != loc:  # a digest collision, or a hand-edited file
            return None
        return entry if entry.age_seconds(self.now()) < ttl_seconds else None

    def put(self, loc: str, sha: str, content: bytes) -> None:
        """Write an entry, evicting the oldest others first if it would not fit.

        Unbounded before this: an entry only ever stopped counting toward
        `get()` once its TTL passed, and nothing ever deleted the file — a
        long-lived process caching many large documents grew this directory
        without limit. `max_bytes` bounds total size on disk; a single entry
        that alone exceeds it is refused rather than evicting everything else
        to make room for it.
        """
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "loc": loc,
            "fetched_at": self.now(),
            "fetched_sha": sha,
            "content": content.hex(),
        }
        body = json.dumps(payload)
        incoming = len(body.encode("utf-8"))
        if incoming > self.max_bytes:
            return
        path = self._path(loc)
        self._evict_to_fit(incoming, keep=path)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(path)

    def _evict_to_fit(self, incoming: int, *, keep: Path) -> None:
        """Delete entries, oldest `fetched_at` first, until `incoming` more
        bytes fit under `max_bytes`. `keep` is about to be overwritten by the
        caller, so its current size is freed without deleting the file out
        from under the write that follows.
        """
        sizes = {p: p.stat().st_size for p in self.directory.glob("*.json")}
        total = sum(sizes.values()) - sizes.get(keep, 0)
        if total + incoming <= self.max_bytes:
            return

        def fetched_at(path: Path) -> int:
            try:
                return int(json.loads(path.read_text(encoding="utf-8"))["fetched_at"])
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                return -1  # unreadable entries are evicted first

        for path in sorted((p for p in sizes if p != keep), key=fetched_at):
            if total + incoming <= self.max_bytes:
                break
            total -= sizes[path]
            path.unlink(missing_ok=True)

    def clear(self) -> None:
        for path in self.directory.glob("*.json"):
            path.unlink(missing_ok=True)
