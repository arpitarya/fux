"""W-82 §3.1 — the URL health state and what `fux doctor` renders from it."""

from __future__ import annotations

import json

import pytest

from fux.maintain import urlstate


@pytest.fixture
def root(tmp_path):
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    return tmp_path


# -- the file is advisory: every failure degrades to "nothing known" ---------


@pytest.mark.parametrize(
    "written",
    [
        None,  # absent
        "",  # empty
        "{not json",  # truncated / corrupt
        "[1, 2, 3]",  # valid JSON, wrong shape
        '{"run_seq": "twelve", "urls": "nope"}',  # right keys, wrong types
        '{"urls": {"u": {"fail_streak": -4, "last_seen_run": true}}}',  # hostile values
    ],
)
def test_read_never_raises_and_degrades_to_empty(root, written):
    """A report must not be able to break `fux doctor`.

    The dirty list makes the same promise for the same reason: "cannot tell"
    degrades to "nothing known" rather than raising on a reporting path.
    """
    if written is not None:
        directory = root / ".fux" / "runtime"
        directory.mkdir(parents=True)
        (directory / urlstate.STATE_NAME).write_text(written, encoding="utf-8")

    state = urlstate.read(root)
    assert state.run_seq >= 0
    assert all(h.fail_streak >= 0 for h in state.urls.values())


def test_roundtrip(root):
    state = urlstate.UrlState(run_seq=3, urls={"https://a": urlstate.UrlHealth(2, 1, 0)})
    urlstate.write(root, state)
    back = urlstate.read(root)
    assert back.run_seq == 3
    assert back.urls["https://a"].last_seen_run == 2
    assert back.urls["https://a"].last_changed_run == 1


def test_written_file_is_sorted_with_a_trailing_newline(root):
    urlstate.write(
        root,
        urlstate.UrlState(run_seq=1, urls={"https://z": urlstate.UrlHealth(), "https://a": urlstate.UrlHealth()}),
    )
    text = (root / ".fux" / "runtime" / urlstate.STATE_NAME).read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text.index("https://a") < text.index("https://z")


# -- observe(): the three rules -----------------------------------------------


def test_success_clears_the_fail_streak(root):
    for _ in range(3):
        urlstate.observe(root, fetched={}, failed=["https://a"], listed=["https://a"])
    assert urlstate.read(root).urls["https://a"].fail_streak == 3

    urlstate.observe(root, fetched={"https://a": "sha1"}, failed=[], listed=["https://a"])
    assert urlstate.read(root).urls["https://a"].fail_streak == 0


def test_last_changed_moves_only_when_the_sha_actually_differs(root):
    """A URL fetched daily and never edited must not look like it changes daily.

    This is the whole reason the shas are kept beside the health file: without
    them, "we fetched it" and "it changed" are indistinguishable.
    """
    urlstate.observe(root, fetched={"https://a": "sha1"}, failed=[], listed=["https://a"])
    first = urlstate.read(root).urls["https://a"].last_changed_run

    urlstate.observe(root, fetched={"https://a": "sha1"}, failed=[], listed=["https://a"])
    assert urlstate.read(root).urls["https://a"].last_changed_run == first

    urlstate.observe(root, fetched={"https://a": "sha2"}, failed=[], listed=["https://a"])
    changed = urlstate.read(root).urls["https://a"]
    assert changed.last_changed_run == changed.last_seen_run == 3


def test_a_delisted_url_is_dropped(root):
    urlstate.observe(root, fetched={"https://a": "s", "https://b": "s"}, failed=[], listed=["https://a", "https://b"])
    urlstate.observe(root, fetched={"https://a": "s"}, failed=[], listed=["https://a"])
    assert set(urlstate.read(root).urls) == {"https://a"}


def test_run_seq_increments_once_per_run(root):
    for expected in (1, 2, 3):
        urlstate.observe(root, fetched={}, failed=[], listed=[])
        assert urlstate.read(root).run_seq == expected


def test_a_url_not_attempted_this_run_is_not_marked_failing(root):
    """`only_urls` narrows a run. Everything else just gets one run older."""
    urlstate.observe(root, fetched={"https://a": "s", "https://b": "s"}, failed=[], listed=["https://a", "https://b"])
    urlstate.observe(root, fetched={"https://a": "s"}, failed=[], listed=["https://a", "https://b"])

    state = urlstate.read(root)
    assert state.urls["https://b"].fail_streak == 0
    assert state.urls["https://b"].last_seen_run == 1  # stale, not failing
    assert state.urls["https://a"].last_seen_run == 2


def test_shas_sidecar_drops_delisted_urls_too(root):
    urlstate.observe(root, fetched={"https://a": "s"}, failed=[], listed=["https://a"])
    urlstate.observe(root, fetched={}, failed=[], listed=[])
    raw = json.loads((root / ".fux" / "runtime" / "url-shas.json").read_text(encoding="utf-8"))
    assert raw == {}


# -- summarize(): the index is the population ---------------------------------


def test_a_url_in_the_index_with_no_health_entry_counts_as_never_confirmed(root):
    """The case the report exists to surface, and the one that would be
    invisible if this iterated the state file instead of the index."""
    summary = urlstate.summarize(urlstate.UrlState(), ["https://never-touched"])
    assert summary.indexed == 1
    assert summary.never_confirmed == 1
    assert summary.confirmed_last_run == 0


def test_summary_counts_split_confirmed_stale_and_failing(root):
    state = urlstate.UrlState(
        run_seq=9,
        urls={
            "https://fresh": urlstate.UrlHealth(last_seen_run=9),
            "https://stale": urlstate.UrlHealth(last_seen_run=4),
            "https://dead": urlstate.UrlHealth(last_seen_run=2, fail_streak=urlstate.FAILING_STREAK),
        },
    )
    summary = urlstate.summarize(state, ["https://fresh", "https://stale", "https://dead"])
    assert summary.indexed == 3
    assert summary.confirmed_last_run == 1
    assert summary.failing == 1
    assert summary.failing_urls == ("https://dead",)


def test_a_url_below_the_failing_streak_is_counted_but_not_named(root):
    """One failure is a flaky network; five in a row is a fact about the URL."""
    state = urlstate.UrlState(
        run_seq=2, urls={"https://flaky": urlstate.UrlHealth(last_seen_run=1, fail_streak=1)}
    )
    summary = urlstate.summarize(state, ["https://flaky"])
    assert summary.failing == 1
    assert summary.failing_urls == ()


def test_state_entries_for_urls_not_in_the_index_do_not_inflate_the_count(root):
    state = urlstate.UrlState(run_seq=1, urls={"https://ghost": urlstate.UrlHealth(last_seen_run=1)})
    assert urlstate.summarize(state, []).indexed == 0


def test_every_declared_field_survives_a_round_trip(tmp_path):
    """⚠ **The drift `state.schema.json` warns about, as a gate.**

    Its own comment: *"add a field and you must remember to teach the reader
    about it, or it is silently dropped on the next read."* That is exactly what
    happened when `token_sha` was added on 2026-08-28 — the field was declared,
    written, and **not read back**, so `validate()` learned a token every run and
    matched none, and the optimisation silently did nothing while every test
    passed.

    This walks the DECLARED shape rather than a hard-coded list, so a field added
    tomorrow is covered without editing this test.
    """
    from fux.maintain import urlstate

    declared = set(urlstate._health_schema().fields)

    state = urlstate.UrlState(run_seq=7)
    health = urlstate.UrlHealth()
    # A distinct, non-default value per declared field, so a dropped one shows.
    values = {
        "last_seen_run": 5,
        "last_changed_run": 3,
        "fail_streak": 2,
        "token_sha": "a" * 64,
    }
    assert declared <= set(values), f"undeclared in this test: {declared - set(values)}"
    for name, value in values.items():
        setattr(health, name, value)
    state.urls["https://x.test/a"] = health
    urlstate.write(tmp_path, state)

    back = urlstate.read(tmp_path).urls["https://x.test/a"]
    for name in declared:
        assert getattr(back, name) == values[name], (
            f"{name!r} is declared and written but does not survive `read` — "
            "the exact drift state.schema.json's header warns about"
        )
