"""URL health state — W-82 §3.1, the reporting half of URL freshness.

Local, gitignored state under `.fux/runtime/` (ADR-DOTFUX's home for derived
planes) recording, per listed URL, **how the last few networked runs went**.
It exists because of one asymmetry: a file change is an event git observes, and
a URL change is not. Between `fux update` runs the `url:` half of the index is a
mosaic of whenever each URL last happened to be fetched, and until now **nothing
anywhere reported how old any of it was**.

## What this fixes is *silence*, not staleness

`fux doctor` had no URL check at all. Its checks were the background runner, the
Python version, the repo root, the layout and the accelerator — so a URL that
had failed every fetch for a month looked exactly like one fetched a minute ago.
[ADR-URL-INGEST](../../../docs/adr/0008_url-ingest.md) decision 4 is right that
a failed fetch keeps the prior record — a flaky network must never present as a
deletion — but the consequence is that **a permanently dead URL lives in the
index forever**, and nobody is told. `fail_streak` makes that consequence
visible.

**Report, never auto-delete.** Nothing here removes a record or edits a
committed byte. Auto-deleting on failure is precisely what decision 4 forbids,
and this counter does not weaken it — it makes the rule's cost legible instead
of invisible.

## Runs, not clocks — and this is a correction to the plan

W-75 specified this file as `{token, validated_at, changed_at, fail_streak}`.
**Two of those are timestamps, and they may not be here.**
[`refer/fetchcache.py`](../refer/fetchcache.py) states the invariant that
[ADR-REFER](../../../docs/adr/0030_refer-plane.md) rests on — *wall clock lives
in the TTL store and nowhere else* — and `store/displaycache.py` restates it.
A second wall-clock home would have been a quiet contradiction of an accepted
record.

So freshness is counted in **networked runs**, not seconds. `run_seq` increments
once per run that fetched anything; a URL records the `run_seq` at which a fetch
last confirmed it. *"Confirmed two runs ago"* is what a maintainer can act on
anyway — *"confirmed 41 minutes ago"* invites the age bound that
`record-freshness.compare.md` verdict D already refused.

⚠ **`token_sha` arrived 2026-08-28** with the optional `validate()`; the
paragraph below is kept because it records why the field was *absent* for so
long, and the answer — *declaring a field nothing writes is how a knob that
cannot work ships* — is still the rule.

⚠ **The historical note: `token` was deliberately absent.** It belonged to the optional `validate()`
fetcher function, which is **an unruled fork gated on a measurement**. Writing a
field nothing reads is how a knob that cannot work gets shipped.

## Advisory, exactly like the dirty list

A missing, truncated or corrupt file reads as *"nothing known"*. This is a
reporting plane: it can make `fux doctor` say less, and it can never change what
`fux ingest` writes. Nothing here is a second write path into the index.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..schema import load as load_schema
from ..store import fuxdir

STATE_NAME = "url-state.json"

#: The declared shapes, beside this module (`maintain/state.schema.json`).
SCHEMA_NAME = "state.schema.json"


def _shape(name: str):
    """One shape out of the multi-shape schema file.

    `state.schema.json` declares four related shapes rather than four files,
    because they are written and read by the same two modules and versioned by
    one string — the same argument the derived plane's schema makes.
    """
    return load_schema("fux.maintain", SCHEMA_NAME).shape(name)


def _file_schema():
    return _shape("url_state_file")


def _health_schema():
    return _shape("url_health")

#: Consecutive failed fetches before `fux doctor` names a URL individually.
#: A single failure is a flaky network; five in a row is a fact about the URL.
FAILING_STREAK = 5


@dataclass
class UrlHealth:
    """One URL's record. All counters, no clocks."""

    #: `run_seq` of the last run whose fetch succeeded. `None` = never yet.
    last_seen_run: int | None = None
    #: `run_seq` of the last run where the sanitized sha actually changed.
    last_changed_run: int | None = None
    #: Consecutive failed fetches, reset to 0 by any success.
    fail_streak: int = 0
    #: `sha256` of the last validation token this URL's fetcher returned.
    #: `None` = the fetcher has no `validate()`, or said it could not tell.
    #:
    #: ⚠ **THE HASH, NEVER THE TOKEN** (W-87 P4 fork 4, ruled 2026-08-28). An
    #: `ETag` is opaque to fux but not necessarily to everyone: it can be a
    #: content hash, a version counter, or an internal object id, and this file
    #: — while gitignored — is exactly the kind of local state that ends up in a
    #: support bundle. Storing `sha256(token)` compares as well as the token
    #: does and carries none of it, so **L5 is untouched by construction.**
    #:
    #: **Counters, no clocks** — unchanged. A token is an opaque equality
    #: witness, not a timestamp, even when a server happened to build it from
    #: one.
    token_sha: str | None = None

    def as_json(self) -> dict:
        return {
            "last_seen_run": self.last_seen_run,
            "last_changed_run": self.last_changed_run,
            "fail_streak": self.fail_streak,
            "token_sha": self.token_sha,
        }


@dataclass
class UrlState:
    run_seq: int = 0
    urls: dict[str, UrlHealth] = field(default_factory=dict)
    #: host -> times that host rate-limited a fetch (W-82 ruling 12).
    #:
    #: **Keyed by HOST, not by URL**, because a rate limit is a property of the
    #: server and not of one page — twelve 429s spread over twelve pages of one
    #: wiki is one fact, not twelve. Counts, never clocks, like everything else
    #: in this file.
    rate_limited: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> dict:
        return {
            "run_seq": self.run_seq,
            "urls": {url: h.as_json() for url, h in sorted(self.urls.items())},
            "rate_limited": dict(sorted(self.rate_limited.items())),
        }


def _path(root: Path) -> Path:
    return fuxdir.fux_dir(root) / "runtime" / STATE_NAME


def read(root: Path) -> UrlState:
    """The recorded state, or an empty one. **Never raises.**

    Every failure mode — absent, unreadable, truncated, not JSON, JSON of the
    wrong shape — degrades to "nothing known", because the only consumer is a
    report and a report must not be able to break `fux doctor`.
    """
    try:
        raw = json.loads(_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return UrlState()
    if not isinstance(raw, dict):
        return UrlState()
    # `coerce`, not a hand-rolled field-by-field check. Both do the same thing;
    # the difference is that the schema is the ONE place a new field has to be
    # declared, instead of a place plus a reader that must remember it.
    top = _file_schema().coerce(raw)
    state = UrlState(run_seq=max(0, top.get("run_seq", 0)))
    for host, count in (top.get("rate_limited") or {}).items():
        # A negative or non-integer count is a file somebody edited by hand;
        # dropping it is right, because a report must never be able to break
        # `fux doctor` (see this function's own contract above).
        if isinstance(host, str) and isinstance(count, int) and count > 0:
            state.rate_limited[host] = count
    health = _health_schema()
    for url, entry in (top.get("urls") or {}).items():
        if not isinstance(url, str):
            continue
        fields = health.coerce(entry)
        state.urls[url] = UrlHealth(
            last_seen_run=_non_negative(fields.get("last_seen_run")),
            last_changed_run=_non_negative(fields.get("last_changed_run")),
            fail_streak=max(0, fields.get("fail_streak", 0)),
            token_sha=fields.get("token_sha") or None,
        )
    return state


def _non_negative(value) -> int | None:
    """`coerce` guarantees the TYPE; this rejects a negative counter.

    Kept separate on purpose — a run counter below zero is not a type error, it
    is a value nobody could have written, and mixing the two into one check
    would make the schema responsible for arithmetic it cannot see.
    """
    return value if isinstance(value, int) and value >= 0 else None


def write(root: Path, state: UrlState) -> None:
    """Persist the state. Sorted keys and a trailing newline, like every other
    generated file here — this is gitignored, but a file that diffs cleanly is
    readable by a human debugging a failing URL, which is its whole audience."""
    directory = fuxdir.derived_dir(root, "runtime")
    text = json.dumps(state.as_json(), indent=2, sort_keys=True) + "\n"
    (directory / STATE_NAME).write_text(text, encoding="utf-8")


def record_rate_limits(root: Path, counts: dict[str, int]) -> None:
    """Add this run's rate-limit counts to the persisted state. **Never raises.**

    W-82 ruling 12. Read-modify-write rather than replace: the counts are
    cumulative across runs, which is what makes *"this host rate-limited you 12
    times"* a fact worth acting on rather than a blip.

    ⚠ **This never touches `[sources.url] max_parallel`.** The whole point of
    recording it is that the consumer decides — Arpit's standing rule, state the
    cost and do not clamp the knob.
    """
    if not counts:
        return
    try:
        state = read(root)
        for host, count in counts.items():
            if count > 0:
                state.rate_limited[host] = state.rate_limited.get(host, 0) + count
        write(root, state)
    except OSError:
        # A report that can fail an ingest is worse than a missing report.
        pass


def observe(
    root: Path,
    *,
    fetched: dict[str, str],
    failed,
    listed,
    token_shas: dict[str, str] | None = None,
) -> UrlState:
    """Record one networked run's outcome and bump `run_seq`.

    `fetched` maps URL -> the sanitized content sha this run produced; `failed`
    is the URLs whose fetch raised or returned nothing; `listed` is every URL
    the source list currently declares.

    Three rules, each with a reason:

    - **A success clears `fail_streak`.** The counter answers *"is this URL
      dead?"*, and one good fetch settles that.
    - **`last_changed_run` moves only when the sha differs** from the sha the
      previous run recorded — not when the fetch merely succeeded. A URL that
      is fetched daily and never edited must not look like it changes daily.
    - **A URL no longer listed is dropped.** The source list is intent; keeping
      health for a URL nobody asks about would make `doctor` report on documents
      that are not in the corpus.

    ⚠ **Called only from the networked path.** An offline `fux ingest` fetches
    nothing, so it learns nothing about any URL, and bumping `run_seq` there
    would age every URL for a run that never looked at one.
    """
    state = read(root)
    state.run_seq += 1
    listed_set = {u for u in listed}
    previous_shas = _read_shas(root)

    tokens = token_shas or {}
    for url in listed_set:
        health = state.urls.setdefault(url, UrlHealth())
        # Fork 3. Recorded for every URL this run learned a token for, whether
        # it was then fetched or skipped as unchanged — the point of storing it
        # is that the NEXT run can compare. A URL whose fetcher has no
        # `validate()` never appears here and keeps `token_sha = None`.
        if url in tokens:
            health.token_sha = tokens[url]
        if url in fetched:
            if previous_shas.get(url) not in (None, fetched[url]):
                health.last_changed_run = state.run_seq
            health.last_seen_run = state.run_seq
            health.fail_streak = 0
        elif url in set(failed):
            health.fail_streak += 1

    for url in [u for u in state.urls if u not in listed_set]:
        del state.urls[url]

    _write_shas(root, {**previous_shas, **fetched}, listed_set)
    write(root, state)
    return state


_SHAS_NAME = "url-shas.json"


def _read_shas(root: Path) -> dict[str, str]:
    """The sha each URL last produced, so `last_changed_run` can mean something.

    Kept beside the health file rather than read back out of the committed
    index: the index is the *current* truth, and by the time this runs the new
    record has not been written yet, so reading it would compare a value with
    itself.
    """
    try:
        raw = json.loads((fuxdir.fux_dir(root) / "runtime" / _SHAS_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in raw.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(raw, dict) else {}


def _write_shas(root: Path, shas: dict[str, str], listed: set[str]) -> None:
    directory = fuxdir.derived_dir(root, "runtime")
    kept = {url: sha for url, sha in shas.items() if url in listed}
    text = json.dumps(kept, indent=2, sort_keys=True) + "\n"
    (directory / _SHAS_NAME).write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class Summary:
    """What `fux doctor` renders. Computed here so the shape is testable."""

    indexed: int
    confirmed_last_run: int
    never_confirmed: int
    failing: int
    failing_urls: tuple[str, ...]
    run_seq: int

    @property
    def has_urls(self) -> bool:
        return self.indexed > 0


def summarize(state: UrlState, indexed_urls) -> Summary:
    """Fold the state and the index's `url:` records into one report.

    **The index is the population, not the state file.** A URL present in the
    index with no health entry has never been through a run that recorded one —
    which is exactly the *"never re-fetched since first ingest"* case the report
    exists to surface, and it would be invisible if this iterated the state.
    """
    urls = sorted(set(indexed_urls))
    confirmed = never = failing = 0
    failing_urls: list[str] = []
    for url in urls:
        health = state.urls.get(url)
        if health is None or health.last_seen_run is None:
            never += 1
        elif health.last_seen_run == state.run_seq:
            confirmed += 1
        if health is not None and health.fail_streak > 0:
            failing += 1
            if health.fail_streak >= FAILING_STREAK:
                failing_urls.append(url)
    return Summary(
        indexed=len(urls),
        confirmed_last_run=confirmed,
        never_confirmed=never,
        failing=failing,
        failing_urls=tuple(failing_urls),
        run_seq=state.run_seq,
    )
