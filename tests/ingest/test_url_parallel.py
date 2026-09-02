"""W-82 §3.3 — declared capability, the cap, and the two kinds of refusal.

The failure this design exists to avoid is not a crash. A blanket thread pool
over the shipped `cdp.py` produces **plausible documents attributed to the wrong
URLs**. That lands in the committed index, **passes every determinism check**
(the trailing sort still runs), and is found only by a human reading an answer.

⚠ **This docstring said the cause was "one module-global WebSocket, reused by
every `fetch()`" until 2026-09-01, and that was false** (W-105).
`fetch_resource()` had opened a fresh socket per call for some time. The real
shared state was the id counter, the two message queues (**cleared at the top of
every fetch**) and the page target — `_page_target()` returned the *first* one,
so two workers drove one tab. A wrong cause in a test file is worse than none:
it is where the next person checks whether the hazard is still live.
"""

from __future__ import annotations

import threading
import time
import types

import pytest

from fux.errors import FuxError
from fux.ingest import urlsrc


def _fetcher(*, declared=None, fetch=None, name="test_fetcher"):
    module = types.SimpleNamespace(__name__=name)
    if declared is not None:
        module.MAX_PARALLEL = declared
    module.fetch = fetch or (lambda url: f"# {url}\n")
    return module


# -- resolve_parallel: min(declared, configured) -----------------------------


def test_an_undeclared_fetcher_is_called_one_at_a_time():
    """The default is byte-for-byte the behaviour that shipped before this
    existed. Opting in is the fetcher author's act, never fux's inference."""
    assert urlsrc.resolve_parallel(_fetcher(), None) == 1
    assert urlsrc.resolve_parallel(_fetcher(), 16) == 1


def test_the_cap_is_the_minimum_of_the_two():
    assert urlsrc.resolve_parallel(_fetcher(declared=8), 4) == 4
    assert urlsrc.resolve_parallel(_fetcher(declared=2), 8) == 2
    # ⚠ CHANGED BY W-83, and it is a behaviour change rather than a corrected
    # test. This line asserted `== 8` when §3.3 shipped: unconfigured meant
    # *whatever the fetcher declared*, so an untouched repo inherited
    # `http.py`'s 8. It now means `min(declared, DEFAULT_MAX_PARALLEL)`.
    assert urlsrc.resolve_parallel(_fetcher(declared=8), None) == urlsrc.DEFAULT_MAX_PARALLEL


# -- W-83: what SILENCE means ------------------------------------------------


def test_saying_nothing_gets_the_politeness_default_not_the_fetchers_ceiling():
    """A declaration answers *what is safe*, never *what is polite unasked*.

    `http.py`'s `MAX_PARALLEL = 8` is a true statement about `http.py` — a
    fresh `Request` per call — and not a claim about what the consumer's wiki
    can absorb. Nobody declared 8 for *this* repo.
    """
    assert urlsrc.DEFAULT_MAX_PARALLEL < 8, "the test is vacuous if they are equal"
    assert urlsrc.resolve_parallel(_fetcher(declared=8), None) == urlsrc.DEFAULT_MAX_PARALLEL
    assert urlsrc.resolve_parallel(_fetcher(declared=64), None) == urlsrc.DEFAULT_MAX_PARALLEL


def test_the_default_only_ever_lowers_never_raises():
    """`min`, not the constant. A fetcher declaring less keeps its own smaller
    number — which is the whole of `cdp.py`'s one-WebSocket protection."""
    assert urlsrc.resolve_parallel(_fetcher(declared=1, name="cdp"), None) == 1
    assert urlsrc.resolve_parallel(_fetcher(), None) == 1  # undeclared is still 1
    assert urlsrc.resolve_parallel(_fetcher(declared=2), None) == 2


def test_the_knob_still_reaches_the_declared_ceiling_silently(capsys):
    """The default decides what saying NOTHING means. It must not become a
    second clamp on what the consumer explicitly asked for."""
    assert urlsrc.resolve_parallel(_fetcher(declared=8), 8) == 8
    assert capsys.readouterr().err == ""


def test_exceeding_a_declared_capability_clamps_down_loudly(capsys):
    """CAPABILITY. Exceeding what the author said is safe is a correctness
    violation, not a preference — so it is clamped, and it says so."""
    assert urlsrc.resolve_parallel(_fetcher(declared=2, name="cdp"), 32) == 2
    err = capsys.readouterr().err
    assert "cdp" in err and "MAX_PARALLEL = 2" in err and "clamped" in err


def test_a_large_policy_value_is_honoured_with_a_warning_never_clamped(capsys):
    """POLICY. *State the cost, don't clamp the knob* — a large value is merely
    rude, and the note states the cost in the units that matter."""
    assert urlsrc.resolve_parallel(_fetcher(declared=64), 32) == 32
    err = capsys.readouterr().err
    assert "429" in err and "skip" in err


def test_a_value_below_one_is_broken_and_refuses():
    with pytest.raises(FuxError, match="max_parallel"):
        urlsrc.resolve_parallel(_fetcher(declared=8), 0)
    with pytest.raises(FuxError):
        urlsrc.resolve_parallel(_fetcher(declared=8), -3)


@pytest.mark.parametrize("bad", ["four", 0, -1, True, None])
def test_a_malformed_declaration_falls_back_to_safe_not_to_fast(bad):
    """A fetcher with a nonsense `MAX_PARALLEL` must not be *more* parallel than
    one with none. Guessing upward here is how the cdp corruption ships."""
    if bad is None:
        pytest.skip("absent is covered by the undeclared test")
    assert urlsrc.resolve_parallel(_fetcher(declared=bad), 8) == 1


# -- the test no amount of manual checking substitutes for --------------------


def test_a_fetcher_declaring_one_is_never_called_concurrently():
    """Asserted with a live counter inside the fetcher, not by reading the pool.

    W-82 §3.3 names this as the one owed test, and the reason is that the code
    *looks* correct either way: the bug is a timing property, and only an
    observation of two calls in flight can distinguish the two designs.
    """
    in_flight = 0
    peak = 0
    lock = threading.Lock()

    def fetch(url):
        nonlocal in_flight, peak
        with lock:
            in_flight += 1
            peak = max(peak, in_flight)
        time.sleep(0.01)
        with lock:
            in_flight -= 1
        return f"# {url}\n"

    module = _fetcher(declared=1, fetch=fetch)
    urls = [f"https://x/{n}" for n in range(8)]
    list(urlsrc._fetch_group(module, urls, urlsrc.resolve_parallel(module, 8)))
    assert peak == 1


def test_a_fetcher_declaring_more_actually_runs_concurrently():
    """The control arm. Without it, a pool that silently never parallelises
    would pass the test above and prove nothing."""
    in_flight = 0
    peak = 0
    lock = threading.Lock()

    def fetch(url):
        nonlocal in_flight, peak
        with lock:
            in_flight += 1
            peak = max(peak, in_flight)
        time.sleep(0.05)
        with lock:
            in_flight -= 1
        return f"# {url}\n"

    module = _fetcher(declared=4, fetch=fetch)
    urls = [f"https://x/{n}" for n in range(8)]
    list(urlsrc._fetch_group(module, urls, urlsrc.resolve_parallel(module, 4)))
    assert peak > 1


# -- determinism: the sort, not the loop --------------------------------------


def test_results_come_back_in_sorted_order_whatever_the_completion_order():
    """The finding that makes concurrency cheap here: **sequential fetching is
    not what makes the index deterministic — the sort is.**"""

    def fetch(url):
        time.sleep(0.02 if url.endswith("0") else 0.0)  # invert completion order
        return f"# {url}\n"

    urls = [f"https://x/{n}" for n in range(6)]
    module = _fetcher(declared=6, fetch=fetch)
    got = [url for url, _text, _exc in urlsrc._fetch_group(module, urls, 6)]
    assert got == urls


def test_per_url_error_isolation_survives_the_pool():
    """ADR-URL-INGEST decision 4 in code, and the reason an optional
    `fetch_many` was rejected: it would have moved this responsibility to every
    fetcher author, and most would not reimplement it correctly."""

    def fetch(url):
        if url.endswith("3"):
            raise RuntimeError("boom")
        return f"# {url}\n"

    urls = [f"https://x/{n}" for n in range(6)]
    results = list(urlsrc._fetch_group(_fetcher(declared=4, fetch=fetch), urls, 4))
    failed = [(u, e) for u, _t, e in results if e is not None]
    assert len(results) == 6
    assert len(failed) == 1 and failed[0][0].endswith("3")


@pytest.mark.parametrize("workers", [1, 4])
def test_the_two_paths_produce_identical_results(workers):
    """The differential arm. A pool that quietly dropped or reordered a URL
    would otherwise be invisible."""
    urls = [f"https://x/{n}" for n in range(10)]
    module = _fetcher(declared=8)
    got = [(u, t) for u, t, _e in urlsrc._fetch_group(module, urls, workers)]
    assert got == [(u, f"# {u}\n") for u in urls]


# -- the shipped fetchers declare what they actually are ----------------------


def _template(name: str) -> str:
    from importlib import resources

    return (resources.files("fux") / "templates" / f"{name}.py.txt").read_text(encoding="utf-8")


def test_the_shipped_cdp_fetcher_declares_one_explicitly():
    """Omission and `1` behave identically — the explicit line is where the
    REASON gets written for whoever copies the file and starts editing it."""
    text = _template("cdp")
    assert "MAX_PARALLEL = 1" in text
    # The reason, beside the constant. ⚠ This used to assert `_session`, which
    # named the WRONG cause — and `_session` is still in the file (it holds the
    # Chrome process), so the assertion would have stayed green through the
    # whole life of the defect. Anchor on the state that actually races.
    assert "def _own_target" in text


def test_the_shipped_http_fetcher_declares_more_than_one():
    """If the safe fetcher does not opt in, the mechanism ships dead."""
    assert "MAX_PARALLEL = 8" in _template("http")


# -- W-105: the cdp session shares nothing a second worker could corrupt ------


def test_cdp_keeps_no_protocol_state_on_the_shared_session():
    """🔴 The three shared fields, gone. Each produced the same wrong answer.

    `_msg_id` handed one id to two commands. `_results`/`_events` were
    **cleared at the top of every fetch**, so one worker wiped another's
    in-flight replies and paused requests. Both are per-`_Conn` now.
    """
    text = _template("cdp")
    for field in ("self._msg_id", "self._results", "self._events"):
        assert field not in text, (
            f"{field} is back on the shared session — that is state two workers "
            "race on, and the failure is a real page filed under the wrong URL"
        )
    assert "class _Conn" in text


def test_cdp_does_not_hand_two_workers_the_same_tab():
    """`_page_target()` returned the FIRST page target, so two threads called
    `Page.navigate` on one page. That is the corruption, most directly."""
    text = _template("cdp")
    # ⚠ Definition and call site, not the bare string: the file's comments
    # explain the old defect BY NAME, and a substring check would fail on the
    # explanation while passing on the bug.
    assert "def _page_target" not in text
    assert "self._page_target(" not in text
    assert "def _own_target" in text and "threading.local()" in text


def test_cdp_closes_exactly_the_tabs_it_opened():
    """Inferring the set by diffing /json would close a human's tabs; not
    tracking it leaks one per worker across a long run."""
    text = _template("cdp")
    assert "_opened" in text and "_close_target" in text


def test_cdp_guards_the_chrome_launch():
    """N workers arriving at a cold port must not all spawn a browser."""
    assert "threading.Lock()" in _template("cdp")


def test_cdp_still_ships_declaring_one():
    """7b. The refactor makes a higher number possible; only a live multi-URL
    run against real Chrome makes one justified, and no test here is that run.
    If this fails because someone raised it, go find the filed run first."""
    assert "MAX_PARALLEL = 1" in _template("cdp")


# -- W-105: the ceiling is settable from fux.toml ----------------------------


@pytest.mark.parametrize("name", ["cdp", "http"])
def test_both_shipped_fetchers_accept_fetcher_max_parallel(name):
    """⚠ It must be the SAME key in both, and that is not a style choice.

    `[sources.url.config]` reaches every fetcher verbatim and each
    `configure()` raises on a key it does not know — so a `cdp_`-prefixed
    spelling breaks any repo that also loads `http.py`. A tunable belonging in
    that table is one both fetchers have.
    """
    text = _template(name)
    assert '"fetcher_max_parallel": ("MAX_PARALLEL"' in text


@pytest.mark.parametrize("name", ["cdp", "http"])
def test_the_key_is_not_spelled_max_parallel(name):
    """`[sources.url] max_parallel` is POLICY and this is CAPABILITY. Two
    nested keys spelled alike is how they get confused in a bug report."""
    text = _template(name)
    assert '"max_parallel":' not in text


@pytest.mark.parametrize("name", ["cdp", "http"])
def test_a_ceiling_below_one_is_refused_not_clamped(name):
    """A silent clamp to 1 honours a number the consumer plainly did not mean —
    the same call `[sources.url] max_parallel` makes in fux's own config."""
    assert "_positive_int" in _template(name)


def test_configure_runs_BEFORE_resolve_parallel_reads_the_module():
    """🔴 The ordering the whole feature rests on, and NEITHER FILE STATES IT.

    `configure()` assigns `MAX_PARALLEL` on the module; `resolve_parallel()`
    reads it with `getattr`. If a refactor ever moved `resolve_parallel` above
    `configure_fetcher` in `fetch_all`, `fetcher_max_parallel` would silently
    do nothing — a configured value that is read but never applied, which is
    the exact shape of the W-83 defect this repo has already paid for once.
    """
    from pathlib import Path

    src = Path(urlsrc.__file__).read_text(encoding="utf-8")
    assert src.index("configure_fetcher(module,") < src.index("resolve_parallel(module,")


def test_a_configured_ceiling_is_what_resolve_parallel_uses():
    """End to end at the seam, on a stand-in module rather than a template."""
    module = _fetcher(declared=1)
    assert urlsrc.resolve_parallel(module, 8) == 1
    module.MAX_PARALLEL = 4  # what configure() does
    assert urlsrc.resolve_parallel(module, 8) == 4
