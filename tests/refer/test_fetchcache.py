"""The TTL fetch cache — W-60, verdict F.

Two properties carry the whole design, and both are hazards W-60 named:

1. **`cached` is never `current`.** Folding them would be decision 4's "knob
   that lies" reappearing in a new place.
2. **The TTL store is not ARC's store.** ARC's "cannot change the answer" proof
   depends on the content address being in the key; a TTL entry is served
   *before* the sha is confirmed, so the two must stay provably separate.
"""

from __future__ import annotations

import json

import pytest

from fux import store as store_mod
from fux.errors import FuxError
from fux.refer import Policy, refer
from fux.refer.arc import ARC
from fux.refer.fetchcache import DEFAULT_TTL_SECONDS, FetchCache
from fux.refer.freshness import ALWAYS, NEVER, cached, verify

PAGE = "# Handbook\n\nThe on-call rota hands over on Monday and telemetry is checked hourly.\n"


def sha_of(text: str) -> str:
    return store_mod.content_sha(text.encode("utf-8"))


class Clock:
    """A pinned clock. The engine's answers never read the real one."""

    def __init__(self, t: float = 1_000_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


# -- the store -------------------------------------------------------------


def test_a_fresh_entry_is_returned(tmp_path):
    clock = Clock()
    cache = FetchCache(tmp_path, clock=clock)
    cache.put("https://x.test/p", "sha1", b"bytes")
    entry = cache.get("https://x.test/p", 300)
    assert entry is not None and entry.content == b"bytes"


def test_an_expired_entry_is_a_miss(tmp_path):
    clock = Clock()
    cache = FetchCache(tmp_path, clock=clock)
    cache.put("https://x.test/p", "sha1", b"bytes")
    clock.advance(301)
    assert cache.get("https://x.test/p", 300) is None


def test_a_zero_ttl_disables_the_cache_entirely(tmp_path):
    """The opt-in default, regression-proofed: a caller who never asked for a
    cache cannot be served a cached byte by any path."""
    cache = FetchCache(tmp_path, clock=Clock())
    cache.put("https://x.test/p", "sha1", b"bytes")
    assert cache.get("https://x.test/p", 0) is None
    assert cache.get("https://x.test/p", -1) is None


def test_a_corrupt_entry_is_a_miss_not_an_error(tmp_path):
    """The cache is disposable; a query must not die for it."""
    cache = FetchCache(tmp_path, clock=Clock())
    cache.put("https://x.test/p", "sha1", b"bytes")
    next(cache.directory.glob("*.json")).write_text("{not json", encoding="utf-8")
    assert cache.get("https://x.test/p", 300) is None


def test_an_entry_whose_loc_does_not_match_is_a_miss(tmp_path):
    """Guards a digest collision, and a hand-edited file."""
    cache = FetchCache(tmp_path, clock=Clock())
    cache.put("https://x.test/p", "sha1", b"bytes")
    path = next(cache.directory.glob("*.json"))
    payload = json.loads(path.read_text())
    payload["loc"] = "https://y.test/other"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert cache.get("https://x.test/p", 300) is None


def test_a_backwards_clock_cannot_make_an_entry_look_fresh_forever(tmp_path):
    clock = Clock()
    cache = FetchCache(tmp_path, clock=clock)
    cache.put("https://x.test/p", "sha1", b"bytes")
    clock.advance(-10_000)
    entry = cache.get("https://x.test/p", 300)
    assert entry is None or entry.age_seconds(cache.now()) >= 0


def test_the_cache_lives_under_the_gitignored_runtime_plane(tmp_path):
    """Wall clock is allowed here for the same reason `stamp.json` allows it:
    derived, per-machine, and it never reaches a committed record."""
    cache = FetchCache(tmp_path, clock=Clock())
    cache.put("https://x.test/p", "sha1", b"bytes")
    assert cache.directory.is_relative_to(tmp_path / ".fux" / "runtime")
    assert not (tmp_path / ".fux" / "index").exists()


# -- the policy ------------------------------------------------------------


def test_caching_is_off_by_default():
    assert Policy().cache_ttl_seconds == 0 and not Policy().caches


def test_no_cache_beats_a_ttl():
    """The escape hatch for access-controlled sources, honoured regardless."""
    assert not Policy(mode=ALWAYS, cache_ttl_seconds=300, no_cache=True).caches


def test_a_negative_ttl_is_refused():
    with pytest.raises(FuxError, match="cache_ttl_seconds"):
        Policy(cache_ttl_seconds=-1)


def test_the_ttl_travels_in_the_bundle():
    record = Policy(mode=ALWAYS, cache_ttl_seconds=300).as_record()
    assert record["cache_ttl_seconds"] == 300 and record["no_cache"] is False


def test_the_default_ttl_constant_is_arpits_number():
    assert DEFAULT_TTL_SECONDS == 300


# -- `cached` is a fourth state, not a synonym -----------------------------


def test_cached_is_never_reported_as_current():
    assert cached("a", "a", 12, 300).label == "cached"
    assert verify("a", "a").label == "current"


def test_cached_still_records_whether_the_shas_agreed():
    """Both facts are kept: matched-the-index, and not-fetched-just-now."""
    assert cached("a", "a", 12, 300).current is True
    assert cached("a", "b", 12, 300).current is False
    assert cached("a", "b", 12, 300).label == "cached"


def test_cached_carries_its_age():
    assert cached("a", "a", 42, 300).age_seconds == 42


# -- through the plane -----------------------------------------------------


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "runbook.md").write_text("# R\n\nlocal content\n", encoding="utf-8")
    return tmp_path


def url_candidates():
    return [("url:https://x.test/p", "https://x.test/p", sha_of(PAGE))]


def test_a_ttl_hit_returns_what_a_live_fetch_would_have(repo):
    """The differential, in the ARC style: the cached answer must be the same
    bytes, and the only difference is the verdict label."""
    import json as json_mod

    calls = []

    def fetcher(url):
        calls.append(url)
        return PAGE

    policy = Policy(mode=ALWAYS, cache_ttl_seconds=300)
    clock = Clock()
    fc = FetchCache(repo, clock=clock)

    cold = refer(repo, "telemetry rota", url_candidates(), policy=policy, fetcher=fetcher, fetch_cache=fc)
    warm = refer(repo, "telemetry rota", url_candidates(), policy=policy, fetcher=fetcher, fetch_cache=fc)

    assert len(calls) == 1, "the second call should not have gone out"
    assert json_mod.dumps([c.__dict__ for c in cold.assembled.citations]) == json_mod.dumps(
        [c.__dict__ for c in warm.assembled.citations]
    ), "a TTL hit changed the citations"
    assert cold.documents[0].verdict.label == "current"
    assert warm.documents[0].verdict.label == "cached"


def test_the_cache_is_bypassed_entirely_when_the_ttl_is_zero(repo):
    calls = []
    policy = Policy(mode=ALWAYS)  # ttl 0
    fc = FetchCache(repo, clock=Clock())
    for _ in range(3):
        bundle = refer(
            repo, "telemetry", url_candidates(), policy=policy,
            fetcher=lambda u: (calls.append(u), PAGE)[1], fetch_cache=fc,
        )
        assert bundle.documents[0].verdict.label != "cached"
    assert len(calls) == 3


def test_no_cache_prevents_a_cached_verdict_even_with_a_ttl(repo):
    policy = Policy(mode=ALWAYS, cache_ttl_seconds=300, no_cache=True)
    fc = FetchCache(repo, clock=Clock())
    for _ in range(2):
        bundle = refer(repo, "telemetry", url_candidates(), policy=policy,
                       fetcher=lambda u: PAGE, fetch_cache=fc)
        assert bundle.documents[0].verdict.label != "cached"


def test_a_git_document_is_never_ttl_cached(repo):
    """A local read is free and always available; caching it would buy a
    staleness window in exchange for nothing."""
    fc = FetchCache(repo, clock=Clock())
    candidates = [("file:runbook.md", "runbook.md", sha_of("# R\n\nlocal content\n"))]
    for _ in range(2):
        bundle = refer(repo, "local", candidates,
                       policy=Policy(mode=ALWAYS, cache_ttl_seconds=300), fetch_cache=fc)
        assert bundle.documents[0].verdict.label == "current"
    assert not list(fc.directory.glob("*.json")) if fc.directory.exists() else True


def test_never_still_never_fetches_and_never_serves_a_cached_url(repo):
    """Decision 7 is unaffected: `never` does not fetch, so there is nothing
    to cache-serve."""
    fc = FetchCache(repo, clock=Clock())
    fc.put("https://x.test/p", sha_of(PAGE), PAGE.encode())
    bundle = refer(repo, "telemetry", url_candidates(),
                   policy=Policy(mode=NEVER, cache_ttl_seconds=300), fetch_cache=fc)
    assert bundle.documents[0].verdict.label == "unverified"


def test_the_ttl_store_is_not_arcs_store(repo):
    """ARC's proof depends on the content address being in its key; a TTL
    entry is served before the sha is confirmed. Two stores, provably apart."""
    arc = ARC(100_000)
    fc = FetchCache(repo, clock=Clock())
    refer(repo, "telemetry", url_candidates(), policy=Policy(mode=ALWAYS, cache_ttl_seconds=300),
          fetcher=lambda u: PAGE, cache=arc, fetch_cache=fc)

    assert ("https://x.test/p", sha_of(PAGE)) in arc          # ARC keyed by (loc, sha)
    assert list(fc.directory.glob("*.json"))                   # the TTL store, separate
    assert fc.directory.name == "fetch-cache"
