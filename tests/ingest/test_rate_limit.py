"""W-82 ruling 12 — on a 429: back off, retry, report; never mutate the cap.

**The thing these tests actually guard is the refusal**: fux must never change
`[sources.url] max_parallel` on the consumer's behalf, and must never learn to
read HTTP. Everything else here is in service of those two.
"""

from __future__ import annotations

import time
import types

import pytest

from fux.ingest import urlsrc
from fux.maintain import urlstate



def _code_only(text: str) -> str:
    """Strip comments and string literals before a substring sniff.

    ⚠ **Third time this repo has needed this.** The daemon build hit it, the
    `AGENTS.md` build hit it, and these two guards hit it — a bare substring
    check reads a docstring EXPLAINING why something is refused as the thing
    being refused. The tempting fix is to delete the explanation.
    """
    import io
    import tokenize

    out = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


class Busy(Exception):
    """What a fetcher raises when the server refused for rate reasons."""


def _module(*, flaky_for: int = 0, declares: bool = True, exc=Busy):
    """A fetcher that refuses `flaky_for` times, then succeeds."""
    state = {"n": 0}

    def fetch(url):
        state["n"] += 1
        if state["n"] <= flaky_for:
            raise exc("429 Too Many Requests")
        return "ok"

    module = types.SimpleNamespace(fetch=fetch, calls=state)
    if declares:
        module.is_rate_limited = lambda e: isinstance(e, Busy)
    return module


def _run(module, urls=("https://wiki.corp/a",), workers=1):
    limited: dict[str, int] = {}
    sleeps: list[float] = []
    out = list(urlsrc._fetch_group(module, list(urls), workers, limited, sleep=sleeps.append))
    return out, limited, sleeps


# -- detection is DECLARED, never sniffed ----------------------------------


def test_a_fetcher_that_declares_nothing_is_never_retried():
    """Optional by design: every fetcher written before this keeps working."""
    module = _module(flaky_for=99, declares=False)
    out, limited, sleeps = _run(module)
    assert isinstance(out[0][2], Busy), "the failure is reported, not retried away"
    assert limited == {} and sleeps == []
    assert module.calls["n"] == 1, "exactly one attempt"


def test_fux_never_reads_the_error_message():
    """⚠ The guard that matters most here.

    The exception text says `429`. A fetcher that does NOT declare the
    predicate must still get no retry — otherwise fux has quietly learned to
    branch on prose, which is the same defect as reading a note's wording
    instead of its boolean.
    """
    module = _module(flaky_for=1, declares=False)
    _, limited, _ = _run(module)
    assert limited == {}


def _boom_module(flaky_for=1, message="consumer bug"):
    def boom(_exc):
        raise RuntimeError(message)

    module = _module(flaky_for=flaky_for)
    module.is_rate_limited = boom
    module.__name__ = "consumer_fetcher"
    return module


def test_a_predicate_that_raises_is_treated_as_not_rate_limited():
    """Consumer-owned code must not be able to fail an ingest."""
    out, limited, _ = _run(_boom_module())
    assert isinstance(out[0][2], Busy)
    assert limited == {}


def test_a_predicate_that_raises_SAYS_SO(capsys):
    """⚠ **Ruled by Arpit 2026-08-28: warn, never raise.**

    Before this, a predicate that threw returned `False` with no output, so
    **a broken predicate and a host that never rate-limits you were
    indistinguishable**: no backoff, no count, nothing in `fux doctor`. The
    isolation was right and the silence was not.
    """
    _run(_boom_module())

    err = capsys.readouterr().err
    assert "RuntimeError" in err and "consumer bug" in err
    assert "is_rate_limited" in err
    assert "NOT rate-limited" in err, "it must say what fux did instead"
    assert "no backoff" in err, "and what that costs"


def test_the_warning_is_once_per_run_not_once_per_url(capsys):
    """⚠ A predicate that throws throws on EVERY attempt of EVERY url.

    Undeduplicated, a 500-URL run would print thousands of identical lines and
    bury its own output — which is how a warning becomes a thing people filter.
    """
    urls = tuple(f"https://wiki.corp/{n}" for n in range(6))
    _run(_boom_module(flaky_for=99), urls=urls)

    assert capsys.readouterr().err.count("is_rate_limited") == 1


def test_a_working_predicate_prints_nothing(capsys):
    """The warning must not fire on the happy path."""
    _run(_module(flaky_for=1))
    assert "is_rate_limited" not in capsys.readouterr().err


def test_the_warning_never_becomes_a_raise():
    """The guarantee the warning sits on top of, restated where it could break.

    ADR-FETCHER decision 10: one consumer bug must never end an ingest of
    10 000 documents.
    """
    out, limited, _ = _run(_boom_module(flaky_for=99), urls=("https://a.test/x", "https://b.test/y"))
    assert len(out) == 2, "the batch completed"
    assert all(isinstance(row[2], Busy) for row in out)
    assert limited == {}


class WideningDict(dict):
    """A counter whose READ-to-WRITE window is artificially widened.

    ⚠ **Getting this right took three attempts, and the first two were vacuous
    tests that passed with the lock removed.** They are worth recording, because
    each looked obviously sufficient:

    1. *8 URLs on 8 workers, assert the total.* Passed 3/3 unlocked — with an
       instant `fetch`, the pool never has two threads alive at once, so nothing
       ever contends.
    2. *Sleep inside `get()` before the read.* Passed 3/3 unlocked even with
       **8 threads measured simultaneously inside `get()`** — because the sleep
       widened the wrong window. It delayed everyone's arrival at the read; the
       read and the write still executed back-to-back afterwards.

    **The window that matters is between the read and the write**, and it is
    two bytecodes wide. CPython's 5 ms switch interval means preemption almost
    never lands there, so ⚠ **this race cannot be provoked naturally** — the
    sleep below is what makes it deterministic instead of theoretical. Unlocked,
    this loses 28 of 32 refusals every time.
    """

    def get(self, key, default=None):
        value = super().get(key, default)  # the READ
        time.sleep(0.02)                   # ...the window before the WRITE
        return value


def test_the_host_counter_is_not_corrupted_by_concurrency():
    """⚠ **Found 2026-08-28 by reading the code, not by a failure.**

    `limited[host] = limited.get(host, 0) + hits` is a read-modify-write and
    `one()` runs under a thread pool, so two workers refused by the **same
    host** can lose a count. **The number this protects is the one `fux doctor`
    prints**, and a consumer reads it to decide whether to lower their cap — so
    an undercount understates precisely the problem the count exists to report.

    ⚠ **Unruled scope.** Arpit ruled the *warning*; this lock came with it
    because the defect is in the same four lines. It is a data race with no
    design content — there is no defensible alternative — but it was not asked
    for, and this note is here so it can be reverted as easily as it was added.
    """

    def fetch(url):
        time.sleep(0.02)  # keeps all 8 workers alive so they reach the counter together
        raise Busy("429")

    module = _module()
    module.fetch = fetch
    urls = [f"https://one.host/{n}" for n in range(8)]

    limited: dict[str, int] = WideningDict()
    list(urlsrc._fetch_group(module, urls, 8, limited, sleep=lambda _s: None))

    expected = len(urls) * (urlsrc.RATE_LIMIT_RETRIES + 1)
    assert limited["one.host"] == expected, (
        f"expected {expected} refusals, counted {limited['one.host']} — "
        f"{expected - limited['one.host']} lost to a race on the counter"
    )



# -- back off, retry, report ------------------------------------------------


def test_it_retries_with_exponential_backoff_and_then_succeeds():
    module = _module(flaky_for=2)
    out, limited, sleeps = _run(module)
    assert out[0][1] == "ok"
    assert out[0][2] is None
    assert sleeps == [1.0, 2.0], "exponential, not flat"
    assert limited == {"wiki.corp": 2}


def test_the_count_is_refusals_not_retries():
    """A URL refused twice and then answered still reports two.

    The host really did refuse two requests, and that is the number a consumer
    needs to decide whether to lower the cap.
    """
    _, limited, _ = _run(_module(flaky_for=2))
    assert limited["wiki.corp"] == 2


def test_retries_are_bounded_and_the_failure_is_still_reported():
    module = _module(flaky_for=99)
    out, limited, sleeps = _run(module)
    assert isinstance(out[0][2], Busy), "a permanently busy host is a skip, not a hang"
    assert len(sleeps) == urlsrc.RATE_LIMIT_RETRIES
    assert limited["wiki.corp"] == urlsrc.RATE_LIMIT_RETRIES + 1


def test_counts_are_keyed_by_host_not_by_url():
    """Twelve refusals across twelve pages of one wiki is ONE fact."""
    module = _module(flaky_for=0)
    calls = {"n": 0}

    def fetch(url):
        calls["n"] += 1
        if calls["n"] % 2:
            raise Busy("429")
        return "ok"

    module.fetch = fetch
    _, limited, _ = _run(module, urls=("https://wiki.corp/a", "https://wiki.corp/b"))
    assert list(limited) == ["wiki.corp"]


# -- the cap is NEVER touched ----------------------------------------------


def test_the_configured_cap_is_never_read_or_changed_by_the_retry_path():
    """⚠ Veto-shaped. Ruling 12's whole point is *state the cost, do not clamp
    the knob* — auto-lowering would make concurrency a number the user did not
    pick and cannot predict."""
    import inspect

    both = _code_only(
        inspect.getsource(urlsrc._fetch_one) + inspect.getsource(urlsrc._fetch_group)
    )
    for forbidden in ("max_parallel", "resolve_parallel"):
        assert forbidden not in both, (
            f"the retry path mentions {forbidden!r} — the cap is the consumer's, "
            "and ruling 12 refused auto-lowering it"
        )

    # ⚠ Tighter, on the retry decision ITSELF: `_fetch_one` is where a future
    # edit would be tempted to "just drop concurrency a bit" on a 429, and it
    # must not even be able to see the number.
    retry = _code_only(inspect.getsource(urlsrc._fetch_one))
    assert "workers" not in retry, (
        "the retry decision can see the worker count — that is one edit away "
        "from auto-lowering it, which ruling 12 refused"
    )


def test_retry_after_is_not_read_anywhere():
    """HTTP semantics fux deliberately stays out of."""
    import inspect

    code = _code_only(inspect.getsource(urlsrc))
    assert "Retry-After" not in code
    assert "retry_after" not in code


# -- persistence, so `fux doctor` can report it -----------------------------


def test_counts_persist_and_accumulate_across_runs(tmp_path):
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 3})
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 4, "docs.corp": 1})

    state = urlstate.read(tmp_path)
    assert state.rate_limited == {"wiki.corp": 7, "docs.corp": 1}, "cumulative, not replaced"


def test_recording_nothing_writes_nothing(tmp_path):
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    urlstate.record_rate_limits(tmp_path, {})
    assert urlstate.read(tmp_path).rate_limited == {}


def test_a_hand_edited_negative_count_is_dropped_not_trusted(tmp_path):
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 2})
    path = tmp_path / ".fux" / "runtime" / urlstate.STATE_NAME
    path.write_text(
        path.read_text(encoding="utf-8").replace('"wiki.corp": 2', '"wiki.corp": -5'),
        encoding="utf-8",
    )
    # A report must never be able to break `fux doctor`.
    assert urlstate.read(tmp_path).rate_limited == {}


def test_the_counts_survive_a_round_trip_through_the_schema(tmp_path):
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    state = urlstate.UrlState(run_seq=3, rate_limited={"a.example": 2})
    urlstate.write(tmp_path, state)
    assert urlstate.read(tmp_path).rate_limited == {"a.example": 2}


# -- the shipped fetcher implements it, which is what stops it being dead ---


def test_the_shipped_http_fetcher_declares_the_predicate():
    """An optional hook nobody implements is dead weight. The shipped fetcher
    implementing it is the clean test that this one is not."""
    from fux.setup import FETCHERS, template_bytes

    source = template_bytes(FETCHERS["http.py"]).decode("utf-8")
    assert "def is_rate_limited(" in source
    assert "rate_limited" in source


def test_the_shipped_fetcher_reads_a_flag_not_the_message():
    from fux.setup import FETCHERS, template_bytes

    source = template_bytes(FETCHERS["http.py"]).decode("utf-8")
    body = _code_only(source[source.index("def is_rate_limited("):])
    assert 'getattr' in body and 'rate_limited' in body
    assert "429" not in body, (
        "the predicate matches on the message — that is branching on prose"
    )


def test_the_shipped_fetcher_still_parses():
    import ast

    from fux.setup import FETCHERS, template_bytes

    ast.parse(template_bytes(FETCHERS["http.py"]).decode("utf-8"))


@pytest.mark.parametrize("code,expected", [(429, True), (500, False), (404, False)])
def test_the_shipped_predicate_fires_only_on_429(code, expected, tmp_path):
    """Execute the SHIPPED template, not a copy of its logic."""
    import urllib.error

    from fux.setup import FETCHERS, template_bytes

    namespace: dict = {}
    exec(compile(template_bytes(FETCHERS["http.py"]).decode("utf-8"), "http.py", "exec"), namespace)

    err = namespace["FetcherError"]("HTTPError: x")
    err.rate_limited = code == 429
    assert namespace["is_rate_limited"](err) is expected
    # An error from anywhere else carries no flag and is never a rate limit.
    assert namespace["is_rate_limited"](urllib.error.URLError("boom")) is False


def test_doctor_reports_the_count_even_with_nothing_indexed(tmp_path, monkeypatch):
    """⚠ **Found by RUNNING it, so it is gated** (CLAUDE.md, two strikes).

    The first build put the rate-limit note only in the branch that runs when
    URLs ARE indexed — so it was invisible in exactly the case that produces
    it: a host refusing you hard enough that nothing got indexed at all.
    """
    from fux import doctor

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 12})

    check = doctor._url_health(tmp_path)
    assert "rate-limited by wiki.corp x12" in check.detail
    assert "none indexed" in check.detail, "the empty-corpus branch, specifically"


def test_doctor_never_suggests_a_number_for_the_cap(tmp_path):
    """Ruling 12's refusal, restated where a future edit would break it."""
    from fux import doctor

    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 12})

    detail = doctor._url_health(tmp_path).detail
    assert "lower max_parallel to" not in detail
    assert "set max_parallel" not in detail
