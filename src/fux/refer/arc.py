"""ARC — the refer plane's content cache, keyed `(loc, sha)`.

Adaptive Replacement Cache (Megiddo & Modha, FAST '03), decided in
`work/compare/cache-policy.compare.md` and built here.

## Why ARC and not LRU

A miss here is a **network fetch**, not a page fault, so the cost asymmetry is
enormous. And the maintenance operations this engine runs — a hook re-indexing
after a large merge — are exactly the bulk scans that flush an LRU's hot set.
ARC is scan-resistant, self-tuning between recency and frequency, and has **no
knob**, which matters on a tool where every configurable value is permanent.

## Two properties this implementation must never lose

**1. It cannot change a result.** The cache is keyed by `(loc, sha)` — content
address included — so a hit is byte-identical to what a fetch would have
returned, or it is not a hit. `tests/refer/test_arc.py` asserts cached and
uncached answers are the same bytes; that is the same differential discipline
M2 established for the accelerator, and it is what makes the cache safe to be
aggressive.

**2. No wall clock.** Recency is a monotonic counter, never a timestamp. A
cache that reads the clock makes the engine's output depend on when it ran.
"""

from __future__ import annotations

from collections import OrderedDict

__all__ = ["ARC", "CacheKey"]

CacheKey = tuple[str, str]  # (loc, sha) — the content address is part of the key


class ARC:
    """Adaptive Replacement Cache over `(loc, sha) -> bytes`, bounded by bytes.

    Four lists, as published: `t1` recent-once and `t2` recent-often hold live
    entries; `b1` and `b2` are *ghost* lists holding only keys, and they are
    what lets the policy notice its own mistakes and re-tune `p`.
    """

    def __init__(self, max_bytes: int) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes
        self.t1: OrderedDict[CacheKey, bytes] = OrderedDict()
        self.t2: OrderedDict[CacheKey, bytes] = OrderedDict()
        self.b1: OrderedDict[CacheKey, int] = OrderedDict()  # ghost: size only
        self.b2: OrderedDict[CacheKey, int] = OrderedDict()
        #: The adaptation target, in bytes, for how much of the budget `t1` gets.
        self.p = 0
        self.hits = 0
        self.misses = 0

    # -- size bookkeeping ---------------------------------------------------

    @property
    def live_bytes(self) -> int:
        return sum(len(v) for v in self.t1.values()) + sum(len(v) for v in self.t2.values())

    def __len__(self) -> int:
        return len(self.t1) + len(self.t2)

    def __contains__(self, key: CacheKey) -> bool:
        return key in self.t1 or key in self.t2

    # -- the operations -----------------------------------------------------

    def get(self, key: CacheKey) -> bytes | None:
        """A hit promotes into `t2` — seen twice means frequency, not recency."""
        if key in self.t1:
            value = self.t1.pop(key)
            self.t2[key] = value
            self.hits += 1
            return value
        if key in self.t2:
            self.t2.move_to_end(key)
            self.hits += 1
            return self.t2[key]
        self.misses += 1
        return None

    def put(self, key: CacheKey, value: bytes) -> None:
        """Insert, adapting `p` when the key is a ghost — a *recorded* mistake."""
        size = len(value)
        if key in self.t1 or key in self.t2:
            self.t1.pop(key, None)
            self.t2[key] = value
            return
        if size > self.max_bytes:
            return  # a single object larger than the whole budget is never cached

        if key in self.b1:
            # We evicted a recency entry and it came back: recency deserves more.
            ghost = self.b1.pop(key)
            self.p = min(self.max_bytes, self.p + max(ghost, 1))
            self._evict(size)
            self.t2[key] = value
            return
        if key in self.b2:
            # We evicted a frequency entry and it came back: recency deserves less.
            ghost = self.b2.pop(key)
            self.p = max(0, self.p - max(ghost, 1))
            self._evict(size)
            self.t2[key] = value
            return

        self._evict(size)
        self.t1[key] = value

    # -- replacement --------------------------------------------------------

    def _evict(self, incoming: int) -> None:
        while self.live_bytes + incoming > self.max_bytes and (self.t1 or self.t2):
            t1_bytes = sum(len(v) for v in self.t1.values())
            # Evict from t1 while it is over its adaptive target, else from t2.
            if self.t1 and t1_bytes > self.p:
                key, value = self.t1.popitem(last=False)
                self.b1[key] = len(value)
            elif self.t2:
                key, value = self.t2.popitem(last=False)
                self.b2[key] = len(value)
            else:
                key, value = self.t1.popitem(last=False)
                self.b1[key] = len(value)
            self._trim_ghosts()

    def _trim_ghosts(self) -> None:
        """Ghost lists hold keys, not content — but they are still bounded.

        Unbounded ghost lists are a slow memory leak that looks like nothing,
        which is the worst shape a leak can have.
        """
        limit = max(1, self.max_bytes // 64)
        while len(self.b1) > limit:
            self.b1.popitem(last=False)
        while len(self.b2) > limit:
            self.b2.popitem(last=False)
