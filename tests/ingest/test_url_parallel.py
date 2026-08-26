"""W-82 §3.3 — declared capability, the cap, and the two kinds of refusal.

The failure this design exists to avoid is not a crash. A blanket thread pool
over the shipped `cdp.py` — one module-global WebSocket, reused by every
`fetch()` — produces **plausible documents attributed to the wrong URLs**. That
lands in the committed index, **passes every determinism check** (the trailing
sort still runs), and is found only by a human reading an answer.
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
    assert urlsrc.resolve_parallel(_fetcher(declared=8), None) == 8


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


def test_the_shipped_cdp_fetcher_declares_one_explicitly():
    """Omission and `1` behave identically — the explicit line is where the
    REASON gets written for whoever copies the file and starts editing it."""
    from importlib import resources

    text = (resources.files("fux") / "templates" / "cdp.py.txt").read_text(encoding="utf-8")
    assert "MAX_PARALLEL = 1" in text
    assert "_session" in text  # the reason, named beside the constant


def test_the_shipped_http_fetcher_declares_more_than_one():
    """If the safe fetcher does not opt in, the mechanism ships dead."""
    from importlib import resources

    text = (resources.files("fux") / "templates" / "http.py.txt").read_text(encoding="utf-8")
    assert "MAX_PARALLEL = 8" in text
