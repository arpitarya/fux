"""`ttl=` actually reaches the cache -- the half that makes it not a knob that lies.

`freshness.py` refused `max_age_seconds` on exactly this ground: a knob that
silently does nothing is the worst available outcome, because the caller
reasonably believes they bounded something. These pin the resolution so `ttl=`
cannot rot back into that.

No network, no clock: `_effective_ttl` is pure arithmetic and `_declared_ttls`
reads two committed files.
"""

from __future__ import annotations

import pytest

from fux import refer as refer_mod
from fux.refer.freshness import Policy


def eff(loc, policy, declared):
    return refer_mod._effective_ttl(loc, policy, declared)


# -- the min() rule ---------------------------------------------------------


def test_an_undeclared_url_takes_the_policy_unchanged():
    assert eff("https://x/a", Policy(cache_ttl_seconds=300), {}) == 300


def test_a_line_may_narrow_the_policy():
    assert eff("https://x/a", Policy(cache_ttl_seconds=3600), {"https://x/a": 900}) == 900


def test_a_line_may_NOT_widen_the_policy():
    """The whole reason the rule is `min` and not "the line wins"."""
    assert eff("https://x/a", Policy(cache_ttl_seconds=300), {"https://x/a": 86400}) == 300


def test_the_default_policy_can_never_be_widened_by_any_line():
    """W-60 verdict F, held by arithmetic rather than by a rule to remember.

    A caller who never opted into caching must never be served a cached byte.
    `ttl=` defaults to 24h on every line, so if the line could widen, adding a
    URL would silently switch caching on for a caller who did not ask.
    """
    default = Policy()
    assert default.cache_ttl_seconds == 0
    for declared in (0, 900, 86400, 10**9):
        assert eff("https://x/a", default, {"https://x/a": declared}) == 0


def test_ttl_zero_on_a_line_opts_that_url_out_entirely():
    # The case a per-URL attribute exists for: one runbook that must always be
    # checked, in a corpus the caller is otherwise happy to cache.
    p = Policy(cache_ttl_seconds=3600)
    assert eff("https://x/runbook", p, {"https://x/runbook": 0}) == 0
    assert eff("https://x/spec", p, {"https://x/runbook": 0}) == 3600


# -- the three layers, read off the committed files -------------------------


def _repo(tmp_path, urls_line, source_ttl=None):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text(urls_line + "\n")
    ttl_key = f'ttl = "{source_ttl}"\n' if source_ttl else ""
    (tmp_path / "fux.toml").write_text(
        "[sources.url]\n"
        'fetcher = ".fux/fetchers/http.py"\n'
        "max_parallel = 2\n" + ttl_key
    )
    return tmp_path


def test_a_line_that_declares_nothing_takes_the_source_wide_value(tmp_path):
    root = _repo(tmp_path, "https://x/a", source_ttl="15m")
    assert refer_mod._declared_ttls(root) == {"https://x/a": 900}


def test_a_line_that_declares_ttl_beats_the_source_wide_value(tmp_path):
    root = _repo(tmp_path, "https://x/a ttl=30s", source_ttl="15m")
    assert refer_mod._declared_ttls(root) == {"https://x/a": 30}


def test_with_neither_declared_the_built_in_default_applies(tmp_path):
    root = _repo(tmp_path, "https://x/a")
    assert refer_mod._declared_ttls(root) == {"https://x/a": 86400}


def test_a_bad_source_wide_ttl_is_refused_by_the_SAME_grammar(tmp_path):
    from fux.errors import FuxError

    root = _repo(tmp_path, "https://x/a", source_ttl="1x")
    with pytest.raises(FuxError, match="ttl"):
        refer_mod._declared_ttls(root)


def test_a_repo_with_no_url_source_reads_nothing(tmp_path):
    (tmp_path / "fux.toml").write_text("")
    assert refer_mod._declared_ttls(tmp_path) == {}


def test_an_UNCONFIGURED_repo_reads_nothing_and_does_not_raise(tmp_path):
    """⚠ **No `fux.toml` at all is not a malformed one.**

    The loader's refusal is for a file that exists and is wrong. `refer()` is
    reachable from a library caller with no config, and the first version of
    this function raised there -- which turned *opting into caching* into a new
    way for an answer to fail, the precise new failure mode its own contract
    says it does not add. Four `tests/refer/test_fetchcache.py` tests went red
    on it. The malformed case above still refuses; only absence is tolerated.
    """
    assert not (tmp_path / "fux.toml").exists()
    assert refer_mod._declared_ttls(tmp_path) == {}


# -- W-140 row 6: the knob that lied for real, not in theory -----------------


def test_answer_built_its_policy_with_caching_off_so_every_ttl_was_dead():
    """🔴 The arithmetic above was right and nothing could set its left operand.

    `answer_via_refer` constructed `Policy(mode=ALWAYS)` — `cache_ttl_seconds`
    at its default `0` — so `min(0, declared)` was `0` for every URL in every
    repo. `ttl=` was the knob this file exists to prove is not a lie, and it
    was a lie everywhere `fux answer` ran, with the `cached` verdict
    unreachable by construction.

    Pinned by reading the source: a behavioural test would need a fetcher, a
    clock and a cache directory to say what one line says.
    """
    import inspect

    from fux.query import refer_answer

    body = inspect.getsource(refer_answer.answer_via_refer)
    assert "cache_ttl_seconds=cache_ttl_seconds" in body, (
        "the caller's cache policy must reach the Policy the refer plane is given"
    )
    assert "Policy(mode=ALWAYS)" not in body, "a hard-coded policy makes every ttl= dead"


def test_the_caller_still_gets_no_cache_unless_it_asks():
    """W-60 verdict F, held by arithmetic: the default is still 0."""
    import inspect

    from fux.query.refer_answer import answer_via_refer

    default = inspect.signature(answer_via_refer).parameters["cache_ttl_seconds"].default
    assert default == 0


def test_the_flag_is_parsed_by_the_source_lists_own_duration_parser():
    """One validator — `--ttl 1x` and `ttl=1x` must fail identically (decision 10)."""
    from fux.errors import FuxError
    from fux.query import _cache_ttl_of

    class Args:
        cache_ttl = "15m"

    assert _cache_ttl_of(Args()) == 900

    class Bad:
        cache_ttl = "1x"

    with pytest.raises(FuxError, match="must be `0` or"):
        _cache_ttl_of(Bad())

    class Absent:
        pass

    assert _cache_ttl_of(Absent()) == 0
