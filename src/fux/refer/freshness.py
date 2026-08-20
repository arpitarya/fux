"""The freshness policy — set by the caller, never owned by the engine.

Graduating `work/proposals/caller-set-freshness-policy.md`, **with its central
knob removed and filed**, for a reason found while building it.

## Why the caller decides

Three callers want three different answers from the same index, and no single
engine-wide policy is right for more than one of them:

| caller | wants |
|---|---|
| an agent mid-loop, ten retrievals deep | never fetch — latency dominates |
| a human asking "is this runbook still true" | always fetch — that *is* the question |
| CI, or a replayed `--audit` bundle | **never** — the index at that commit is the answer |

**The third row is the one that matters.** An explicit never-fetch bound is
what makes a replayed answer reproducible; without it "the same query at the
same commit" is a promise the engine cannot keep.

## `max_age_seconds` is NOT implemented, and that is deliberate

The proposal's shape was `{max_age_seconds, timeout_seconds}`, with age
measured "against the ledger's recorded `sha@index` provenance, not wall clock
at query time".

**There is no such provenance.** A committed record carries
`id · src · loc · sha · ver · mode · meta · title · phrases · terms · wlen ·
edges` (ADR-RECORD) — `ver` is a monotonic revision counter, not a time, and
nothing else in the record is temporal. `.fux/runtime/stamp.json` holds
filesystem mtimes but is derived and *explicitly excluded* from the
byte-identity assertion precisely because mtimes are not reproducible.

So the engine cannot compute an age, and shipping `max_age_seconds` would mean
shipping a knob that silently does nothing — the worst available outcome,
because a caller passing `max_age_seconds=60` would reasonably believe they had
bounded their staleness. Adding a recorded ingest time is a change to
ADR-RECORD with a real determinism question attached (it would have to derive
from `SOURCE_DATE_EPOCH` or source mtime), and that is its own decision.

**Filed as W-58.** What ships is what can be honest:

- **`never`** — do not fetch. Deterministic-replay mode.
- **`always`** — fetch every citation, bounded by `timeout_seconds`.

## Verification is by content, not by clock — and it is stronger

When a fetch does happen, freshness is decided by comparing the fetched bytes'
`sha` against the `sha` the index recorded. That answers *"is the index still
right"* exactly, where an age only ever answered *"is the index probably still
right"*. It needs no clock, which means it costs the determinism law nothing.

Nothing in this module imports `time`.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import FuxError

__all__ = [
    "Policy", "Decision", "Verdict", "NEVER", "ALWAYS", "MODES", "decide", "verify", "cached",
]

#: Do not fetch. The index at this commit is the answer.
NEVER = "never"

#: Fetch every citation, bounded by the timeout.
ALWAYS = "always"

MODES = (NEVER, ALWAYS)


@dataclass(frozen=True)
class Policy:
    """What the caller will tolerate. Immutable, and carried into the answer."""

    mode: str = NEVER
    timeout_seconds: int = 5
    #: Serve a previously fetched copy for this many seconds before going out
    #: again. **0 disables the cache**, and that is the default: a caller who
    #: never opted in can never be served a cached byte (W-60, verdict F).
    cache_ttl_seconds: int = 0
    #: Never cache this source's bytes at all, whatever the TTL says. The
    #: escape hatch for access-controlled and regulated documents, where a
    #: local copy outliving the reader's permission is the risk L5 exists for.
    no_cache: bool = False

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise FuxError(
                f"freshness mode must be one of {', '.join(MODES)}, got {self.mode!r}. "
                "There is no age-based mode: the committed record carries no ingest "
                "time, so an age bound could not be honoured (W-58)."
            )
        if not isinstance(self.timeout_seconds, int) or isinstance(self.timeout_seconds, bool):
            raise FuxError(f"timeout_seconds must be an integer, got {self.timeout_seconds!r}")
        if self.timeout_seconds <= 0:
            raise FuxError(f"timeout_seconds must be positive, got {self.timeout_seconds}")
        if not isinstance(self.cache_ttl_seconds, int) or isinstance(self.cache_ttl_seconds, bool):
            raise FuxError(f"cache_ttl_seconds must be an integer, got {self.cache_ttl_seconds!r}")
        if self.cache_ttl_seconds < 0:
            raise FuxError("cache_ttl_seconds must be >= 0 (0 disables the cache)")

    @property
    def forbids_fetch(self) -> bool:
        return self.mode == NEVER

    @property
    def caches(self) -> bool:
        """True when a cached copy may be served. `no_cache` always wins."""
        return self.cache_ttl_seconds > 0 and not self.no_cache

    def as_record(self) -> dict:
        """The policy as it is stamped into the answer bundle.

        A replay that silently used a different policy is the failure this
        exists to close, so the policy travels **with** the answer rather than
        being remembered by whoever ran the query.
        """
        return {
            "mode": self.mode,
            "timeout_seconds": self.timeout_seconds,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "no_cache": self.no_cache,
        }


@dataclass(frozen=True)
class Decision:
    """Whether to fetch this citation, and the reason — which the answer keeps."""

    fetch: bool
    reason: str

    def __bool__(self) -> bool:
        return self.fetch


def decide(policy: Policy) -> Decision:
    """Fetch, or answer from the index?"""
    if policy.forbids_fetch:
        return Decision(False, "policy:never")
    return Decision(True, "policy:always")


@dataclass(frozen=True)
class Verdict:
    """What a completed fetch said about the index's copy.

    `current` is `None` when no fetch happened — which is **not** the same as
    "fresh", and the three-state shape exists so nothing downstream can collapse
    "we did not look" into "we looked and it was fine".
    """

    current: bool | None
    indexed_sha: str
    fetched_sha: str | None
    note: str
    #: Set only on a TTL cache hit. Its presence is what makes `label` say
    #: `cached` — see the class docstring.
    age_seconds: int | None = None

    @property
    def label(self) -> str:
        """`current` · `stale` · `unverified` · `cached`.

        **`cached` is never folded into `current`.** A TTL hit says *we looked
        recently*, which is a different claim from *we just looked*, and
        collapsing the two is decision 4's "knob that lies" reappearing in a
        new place. A caller that wants to treat them alike may; the engine
        will not do it on their behalf.
        """
        if self.age_seconds is not None:
            return "cached"
        if self.current is None:
            return "unverified"
        return "current" if self.current else "stale"


def cached(indexed_sha: str, fetched_sha: str, age_seconds: int, ttl: int) -> Verdict:
    """A TTL cache hit. `current` still records whether the shas agreed.

    Both facts are kept: whether the cached bytes match the index, *and* that
    they were not fetched just now. Dropping either would make the verdict a
    smaller claim than the truth.
    """
    return Verdict(
        current=fetched_sha == indexed_sha,
        indexed_sha=indexed_sha,
        fetched_sha=fetched_sha,
        note=f"served from the local fetch cache, {age_seconds}s old (ttl {ttl}s)",
        age_seconds=age_seconds,
    )


def verify(indexed_sha: str, fetched_sha: str | None, note: str = "") -> Verdict:
    """Compare what the index recorded against what the source just returned."""
    if fetched_sha is None:
        return Verdict(None, indexed_sha, None, note or "not fetched")
    current = fetched_sha == indexed_sha
    return Verdict(
        current,
        indexed_sha,
        fetched_sha,
        note or ("source matches the index" if current else "source has changed since ingest"),
    )
