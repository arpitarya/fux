"""The refer plane — rank in the index, fetch from the source, cite a fresh sha.

This is the half of "index-and-refer" that the index is *for*. The committed
plane holds statistics and never content (L2), so an answer that quotes a
document has to go and get it — from the git checkout, or from the system that
owns it through the consumer's fetcher.

## The shape of one call

```
   ranked doc ids            fetch (git / consumer fetcher)
   from `ask`      ------->  bytes  ------->  chunk  ------->  rescore
                               |                                  |
                               v                                  v
                          verify sha                         assemble under
                        (current/stale)                       a byte budget
```

Six modules, one each:

| module | question it answers |
|---|---|
| `source` | where do this document's bytes come from? |
| `freshness` | may I fetch at all, and was the index still right? |
| `fetchcache` | do I need to go out at all, or did I look recently? |
| `arc` | have I already got these bytes? |
| `chunk` | which spans of this document are citable? |
| `rescore` | which of those spans answer *this* query? |
| `assemble` | which of those fit the caller's window? |

## Three properties the plane promises

**1. It cannot invent.** Every citation is a verbatim span of bytes that came
from the source, with the sha those bytes hashed to. No model is on this path
and none ever will be.

**2. Offline degradation is honest.** A `file:` source keeps full function with
no network at all. An external source that cannot be reached returns a
**declared** staleness — `unverified` — and never stale bytes presented as
fresh. The three-state verdict (`current` / `stale` / `unverified`) exists so
nothing downstream can collapse "we did not look" into "we looked and it was
fine".

**3. The policy travels with the answer.** A bundle records the freshness
policy it was produced under, per citation, because a replay that silently used
a different policy is indistinguishable from a replay that reproduced.

## What is not here yet

**R4 is unmeasured** — the cold/warm latency prediction runs in `fux-lab`, and
`fux-lab` does not exist (W-56). So this plane is built and unproven, and
ADR-REFER says so rather than claiming a gate it did not pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import arc as arc_mod
from . import fetchcache as fetchcache_mod
from . import freshness as freshness_mod
from ._assemble import DEFAULT_BUDGET, PER_DOC_FRACTION, Assembled, assemble
from ._chunk import MAX_PASSAGE_BYTES, MIN_PASSAGE_BYTES, chunk
from .freshness import (
    Policy,
    Verdict,
    as_ingested as as_ingested_verdict,
    cached as cached_verdict,
    verify,
)
from ._rescore import ScoredPassage, rescore
from ..errors import FuxError
from .source import Fetched, fetch_document, from_acquired

__all__ = [
    "Bundle",
    "Cited",
    "Policy",
    "refer",
    "DEFAULT_BUDGET",
]


@dataclass(frozen=True)
class Cited:
    """One document the plane looked at, and what it found out about it."""

    doc_id: str
    loc: str
    verdict: Verdict
    strategy: str
    note: str = ""

    def as_record(self) -> dict:
        return {
            "id": self.doc_id,
            "loc": self.loc,
            "freshness": self.verdict.label,
            "indexed_sha": self.verdict.indexed_sha,
            "fetched_sha": self.verdict.fetched_sha,
            "strategy": self.strategy,
            "note": self.note or self.verdict.note,
        }


@dataclass
class Bundle:
    """An assembled answer, plus everything needed to reproduce or audit it."""

    assembled: Assembled
    documents: list[Cited] = field(default_factory=list)
    policy: dict = field(default_factory=dict)

    def as_record(self) -> dict:
        return {
            "citations": [
                {
                    "id": c.doc_id,
                    "locator": c.locator,
                    "sha": c.sha,
                    "heading": c.heading,
                    "text": c.text,
                    "score": c.score,
                    "source": c.source,
                }
                for c in self.assembled.citations
            ],
            "documents": [d.as_record() for d in self.documents],
            "budget": {
                "bytes": self.assembled.budget,
                "used": self.assembled.used,
                "dropped": self.assembled.dropped,
            },
            "policy": self.policy,
        }


def refer(
    root: Path,
    query: str,
    candidates: list[tuple[str, str, str]],
    *,
    policy: Policy | None = None,
    budget: int = DEFAULT_BUDGET,
    per_doc_fraction: float = PER_DOC_FRACTION,
    min_passage_bytes: int = MIN_PASSAGE_BYTES,
    max_passage_bytes: int = MAX_PASSAGE_BYTES,
    rerank_weight: float = 0.0,
    k: int | None = None,
    cache: arc_mod.ARC | None = None,
    fetcher=None,
    fetch_cache: fetchcache_mod.FetchCache | None = None,
) -> Bundle:
    """Fetch, verify, re-score and assemble. `candidates` is `(id, loc, sha)`.

    The candidates come from the ranker — this plane does not decide *which*
    documents answer the query, only which of their passages do and which of
    those fit.

    The four `[refer]` keys arrive as parameters and default to the module
    constants, so an unconfigured caller gets byte-identical bundles. **None of
    them can change which documents are looked at or what a citation's `sha`
    is** — they move the passage boundaries and the byte budget, which is
    downstream of every fetch and every verdict. That is what keeps them
    tunables rather than a way to configure the freshness record.

    `rerank_weight` is the **fifth** value with that property and the only one
    that is not a `[refer]` key: it is `[ranking] rerank_weight`, reaching
    `rescore` so a passage is scored by the same proximity arithmetic that
    ranked its document (W-108). It defaults to `0.0` — **off** — rather than
    to `rerank.WEIGHT`, so a caller that has said nothing gets the bundle this
    function produced before the parameter existed. `refer()` may not switch on
    a knob that `ask` has switched off; only the caller's `Tune` decides.
    """
    policy = policy or Policy()
    decision = freshness_mod.decide(policy)

    documents: list[Cited] = []
    fetched: list[tuple[str, str, str, list]] = []

    if fetch_cache is None and policy.caches:
        fetch_cache = fetchcache_mod.FetchCache(root)

    # Read once per call, and only when it can matter -- see `_declared_ttls`.
    ttls = _declared_ttls(root) if policy.caches else {}

    for doc_id, loc, indexed_sha in candidates:
        result, cited = _obtain(
            root, doc_id, loc, indexed_sha, decision, cache, fetcher, policy, fetch_cache, ttls
        )
        documents.append(cited)
        if result is None:
            continue
        text = result.content.decode("utf-8", errors="replace")
        fetched.append(
            (
                doc_id,
                loc,
                result.sha,
                chunk(
                    text,
                    min_passage_bytes=min_passage_bytes,
                    max_passage_bytes=max_passage_bytes,
                ),
            )
        )

    _mark_changed_urls_dirty(root, documents)

    scored: list[ScoredPassage] = rescore(query, fetched, weight=rerank_weight)
    assembled = assemble(
        scored, budget=budget, k=k, source="fetched", per_doc_fraction=per_doc_fraction
    )
    return Bundle(assembled=assembled, documents=documents, policy=policy.as_record())


def _mark_changed_urls_dirty(root: Path, documents: list[Cited]) -> None:
    """The detector — W-82 §3.2, and the loop it closes is the point.

    This plane already fetches every cited URL and already computes whether its
    sha still matches the index. Until now it rendered `stale` to the caller and
    **threw that knowledge away**, so the index kept the old terms, the document
    stopped ranking, and nothing ever noticed. Recording the doc id here lets a
    narrowed `ingest.run(only_urls=...)` put the terms right.

    **This buys recall, not correctness.** A changed document could never be
    *mis-answered* — the verdict beside every citation is what stops that — it
    could only fail to surface. That is a weaker good, and it is priced as one.

    Three deliberate restrictions:

    - **`url:` ids only.** A `file:` document has an event already: git observes
      the change and `post-commit` re-indexes it. Recording those here would be
      a second write path into a flow that works.
    - **Only `current is False`, never `None`.** `None` is *"we did not look"* --
      a refused fetch, a network failure, a `never` policy. Marking those dirty
      would churn the list on exactly the days the network is bad, which is when
      it helps least.
    - **Best-effort.** An unwritable `.fux/runtime/` must never fail an answer
      that otherwise succeeded. `dirty.record` is advisory by contract, so a
      write that does not happen costs a delayed refresh and nothing else.

    ⚠ **On the "advisory, never authoritative" contract this leans on.**
    `dirty.py`'s docstring is the sentence that keeps L3 true: `fux ingest`
    re-walks the whole corpus regardless, so the list can never change a
    committed byte. A *URL* refresh driven by this list is authoritative for the
    URLs it names, because not fetching the rest is the entire point -- so the
    defence has to be said rather than assumed: **the `url:` half of the index
    is already a mosaic of different moments.** Every record holds whatever its
    last fetch produced, and no two were necessarily fetched together. A partial
    refresh changes the *spread* of those moments, not the kind of object the
    index is. L3 is *same sources -> same bytes*, and a URL is not the same
    source twice.

    ⚠ **This is not "just index the delta"**, which was ruled *not* the fix for
    R5. That was an offline filesystem walk that is already cheap; this is a
    networked path that is not, and the economics invert.
    """
    changed = [c.doc_id for c in documents if c.doc_id.startswith("url:") and c.verdict.current is False]
    if not changed:
        return
    try:
        from ..maintain import dirty

        dirty.record(root, changed)
    except Exception:  # pragma: no cover - a detector must not break an answer
        pass


def _declared_ttls(root) -> dict[str, int]:
    """`loc -> seconds`, from the committed URL list's `ttl=` attribute.

    ⚠ **Read only when the caller has already opted into caching.** With the
    default policy (`cache_ttl_seconds=0`) nothing here is opened, so the
    common path costs no file read and gains no new failure mode. When the
    caller HAS opted in, a malformed URL list raises here exactly as it does
    in `fux ingest` -- a file that exists and is wrong is the case a loader
    refusal is for (ADR-DOTFUX).

    The three layers -- built-in default, `[sources.url] ttl`, the line -- are
    resolved by `resolve_urls`, the same function that resolves `keep`. This
    never re-implements them.
    """
    from ..config import CONFIG_NAME
    from ..config import load as load_config
    from ..ingest import sourcelist, urlsrc

    # ⚠ **An UNCONFIGURED repo declares nothing; it is not a malformed one.**
    # The refusal above is for a file that exists and is wrong. `refer()` is
    # reachable from a library caller with no `fux.toml` at all, and raising
    # there would make opting into caching a new way for an answer to fail --
    # exactly the new failure mode this function's contract says it does not add.
    if not (Path(root) / CONFIG_NAME).is_file():
        return {}
    source = load_config(root).url
    if source is None:
        return {}
    entries = urlsrc.read_urls(root, source.urls_file)
    out: dict[str, int] = {}
    for resolved in urlsrc.resolve_urls(entries, source):
        seconds = sourcelist.parse_duration(resolved.ttl)
        if seconds is not None:
            out[resolved.url] = seconds
    return out


def _effective_ttl(loc: str, policy, declared: dict[str, int]) -> int:
    """`min(policy, declared)` -- the per-URL value NARROWS and never widens.

    Both halves of that are load-bearing, and they answer different failures:

    - **It cannot widen**, so a URL line can never serve a cached byte to a
      caller who did not ask for caching. The policy default is `0`, and
      `min(0, 86400)` is `0` -- W-60 verdict F holds by arithmetic rather than
      by a rule somebody has to remember.
    - **It can narrow**, so `ttl=0` on one line means *always go out for this
      one*, whatever the caller's policy says. That is the case a per-URL
      attribute exists for: a runbook that must never be answered from a
      cached copy sits in the same corpus as a spec that may.

    The same `min(configured, declared)` shape as `max_parallel`, and for the
    same reason: a declaration may lower a bound, never raise it.
    """
    seconds = declared.get(loc)
    if seconds is None:
        return policy.cache_ttl_seconds
    return min(policy.cache_ttl_seconds, seconds)


def _obtain(root, doc_id, loc, indexed_sha, decision, cache, fetcher, policy, fetch_cache, ttls=None):
    """Get one document's bytes, and record honestly what happened.

    **The `never` branch still reads a `file:` document.** Reading the local
    checkout is not a fetch — no network, no cost, no policy question — and
    refusing it would make `--audit` unable to quote the very repository it is
    auditing. What `never` forbids is going *out*.
    """
    from .source import GIT, resolve

    strategy = resolve(doc_id)
    if strategy != GIT and not decision.fetch:
        # Policy forbids going out -- but if the bytes this record was built
        # from are on disk, comparing against them is a REAL comparison and
        # strictly more than `unverified` has ever been able to say.
        retained = from_acquired(root, doc_id, loc)
        if retained is not None:
            return retained, Cited(
                doc_id, loc,
                as_ingested_verdict(indexed_sha, retained.sha, f"{decision.reason}; compared against .fux/acquired/"),
                strategy,
            )
        return None, Cited(doc_id, loc, verify(indexed_sha, None, decision.reason), strategy)

    # The TTL cache, before the network and **only for external sources**. A
    # `file:` read is free and always available, so caching it would add a
    # staleness window in exchange for nothing.
    ttl = _effective_ttl(loc, policy, ttls or {})
    if strategy != GIT and policy.caches and ttl > 0 and fetch_cache is not None:
        entry = fetch_cache.get(loc, ttl)
        if entry is not None:
            age = entry.age_seconds(fetch_cache.now())
            return (
                Fetched(doc_id, loc, entry.content, entry.fetched_sha, strategy),
                Cited(
                    doc_id, loc,
                    cached_verdict(indexed_sha, entry.fetched_sha, age, ttl),
                    strategy,
                ),
            )

    key = (loc, indexed_sha)
    if cache is not None:
        hit = cache.get(key)
        if hit is not None:
            # A hit is keyed by content address, so it IS the indexed bytes —
            # which is why the verdict below is the *same* verdict a fetch
            # would have produced, note included.
            #
            # **The note must not say "cache hit".** A first draft did, and the
            # differential test caught it: a caller diffing two runs would see
            # a difference caused purely by cache state, which is precisely
            # what the differential law forbids. How the bytes were obtained is
            # instrumentation and lives on the cache object (`ARC.hits`); the
            # bundle records what was learned about the *document*.
            return (
                Fetched(doc_id, loc, hit, indexed_sha, strategy),
                Cited(doc_id, loc, verify(indexed_sha, indexed_sha), strategy),
            )

    try:
        result = fetch_document(root, doc_id, loc, fetcher=fetcher)
    except FuxError as exc:
        # ⚠ **The case `.fux/acquired/` exists for.** Signed out, offline, or
        # the source is gone: without retained bytes this is `unverified`,
        # which is indistinguishable from never having looked. With them it
        # becomes `as-ingested` -- we could not look, but the passage still
        # matches the exact input the record was built from.
        retained = from_acquired(root, doc_id, loc)
        if retained is not None:
            return retained, Cited(
                doc_id, loc,
                as_ingested_verdict(indexed_sha, retained.sha, f"{exc}; compared against .fux/acquired/"),
                strategy,
                str(exc),
            )
        # Honest degradation: declared unverified, never stale-as-fresh.
        return None, Cited(doc_id, loc, verify(indexed_sha, None, str(exc)), strategy, str(exc))

    if cache is not None:
        cache.put((loc, result.sha), result.content)
    # ⚠ Gated on the EFFECTIVE ttl, not the policy. `ttl=0` on a line means
    # "never serve this from a cache", and a copy that is written but never
    # read is a copy of an access-controlled document sitting on disk for no
    # benefit at all.
    if strategy != GIT and policy.caches and ttl > 0 and fetch_cache is not None:
        fetch_cache.put(loc, result.sha, result.content)
    return result, Cited(doc_id, loc, verify(indexed_sha, result.sha), strategy)
