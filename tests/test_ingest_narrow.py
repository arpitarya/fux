"""`fux ingest` refreshes the dirty list; `--refetch-all` forces the full sweep.

⚠ **Renamed from `test_update_narrow.py` by W-177** (2026-09-15), which deleted
`fux update` and moved its whole surface onto `fux ingest`. The ruling below is
untouched by that: W-82 ruling 3 is about **which URLs**, never which verb.

W-82 ruling 3, landed 2026-08-28 (Arpit) together with ruling 10 — *"the two
must land together or the tail silently stops being refreshed at all."*

**Why narrow is the default rather than a flag.** *"If the dirty list is the
right thing to refresh, it should not have to be asked for. A user typing
`fux update` wants a current index, not a network sweep."* There is deliberately
no `--dirty` / `--stale` / `--changed`. (The quote is his, from 2026-08-28, and
names the verb of the day.)
"""

from __future__ import annotations

from pathlib import Path

from fux.maintain import dirty
from fux.sources import _narrow


class Entry:
    def __init__(self, value, exclude=False):
        self.value = value
        self.exclude = exclude


LISTED = [Entry("https://a.test/x"), Entry("https://b.test/y"), Entry("https://c.test/z")]


def test_refetch_all_forces_the_full_sweep(tmp_path):
    """⚠ **`--all` until W-177 renamed it.** Beside `--full` on `ingest` the old
    name read as its synonym, and the two are unrelated: `--full` re-extracts
    every document, `--refetch-all` fetches every URL."""
    targeted, why = _narrow(tmp_path, LISTED, all_urls=True)
    assert targeted is None, "None means every listed URL, not zero of them"
    assert "--refetch-all" in why
    assert "`--all`" not in why, "the announcement must not name a flag that is gone"


def test_an_absent_dirty_list_sweeps_everything(tmp_path):
    """⚠ **The fail-safe, and the reason this function exists at all.**

    `dirty.read` collapses missing-and-unreadable to `[]` because it feeds
    reporting paths where "cannot tell" should degrade quietly. A consumer that
    ACTS on the list cannot afford that: under narrow-by-default, empty means
    *fetch nothing*.

    A repo that has never run the hook, or whose `.fux/runtime/` was wiped,
    would otherwise have `fux ingest` become a silent no-op — **the exact
    "the tail silently stops being refreshed" failure ruling 3 warns about**,
    arriving through a file's tolerance rather than through the ruling.
    """
    assert not dirty.is_readable(tmp_path)
    targeted, why = _narrow(tmp_path, LISTED, all_urls=False)
    assert targeted is None, "absent must mean SWEEP EVERYTHING, never fetch nothing"
    assert "no dirty list" in why


def test_a_present_empty_dirty_list_fetches_nothing(tmp_path):
    """The other side of the same coin, and it must differ from absent.

    A list that exists and is empty is a real statement: nothing is known to be
    stale. That is the case narrow-by-default is FOR.
    """
    (tmp_path / ".fux" / "runtime").mkdir(parents=True)
    (tmp_path / ".fux" / "runtime" / "dirty").write_text("", encoding="utf-8")

    targeted, why = _narrow(tmp_path, LISTED, all_urls=False)
    assert targeted == set(), "present-and-empty is not absent"
    assert "0 known stale" in why


def test_only_the_stale_urls_are_fetched(tmp_path):
    (tmp_path / ".fux" / "runtime").mkdir(parents=True)
    (tmp_path / ".fux" / "runtime" / "dirty").write_text(
        "url:https://b.test/y\nfile:docs/a.md\n", encoding="utf-8"
    )

    targeted, why = _narrow(tmp_path, LISTED, all_urls=False)
    assert targeted == {"https://b.test/y"}
    assert "1 known stale" in why


def test_a_dirty_url_that_is_no_longer_listed_is_not_fetched(tmp_path):
    """The dirty list is advisory and outlives edits to the source list.

    Someone removes a URL line; the dirty list still names it. Fetching it would
    re-index a document the repo has said it no longer wants.
    """
    (tmp_path / ".fux" / "runtime").mkdir(parents=True)
    (tmp_path / ".fux" / "runtime" / "dirty").write_text(
        "url:https://gone.test/old\nurl:https://a.test/x\n", encoding="utf-8"
    )

    targeted, _ = _narrow(tmp_path, LISTED, all_urls=False)
    assert targeted == {"https://a.test/x"}


def test_an_excluded_entry_is_never_a_target(tmp_path):
    (tmp_path / ".fux" / "runtime").mkdir(parents=True)
    (tmp_path / ".fux" / "runtime" / "dirty").write_text("url:https://a.test/x\n", encoding="utf-8")

    listed = [Entry("https://a.test/x", exclude=True)]
    targeted, _ = _narrow(tmp_path, listed, all_urls=False)
    assert targeted == set()


# -- W-140 row 4: `--failed` was parsed and never read -----------------------


def _with_fail_streaks(root: Path, streaks: dict[str, int]) -> None:
    from fux.maintain import urlstate

    state = urlstate.read(root)
    for url, streak in streaks.items():
        health = state.urls.setdefault(url, urlstate.UrlHealth())
        health.fail_streak = streak
    urlstate.write(root, state)


def test_failed_selects_exactly_the_urls_whose_last_run_failed(tmp_path):
    """The flag existed, was documented, and did nothing.

    Until 2026-09-11 `fux update --failed` fell through to the ordinary narrow
    pass: it fetched the *stale* set and reported success. A flag that silently
    does something else is worse than one that errors, because the report reads
    as though the retry happened.
    """
    _with_fail_streaks(tmp_path, {"https://a.test/x": 2, "https://b.test/y": 0})
    dirty.record(tmp_path, ["url:https://c.test/z"])

    targeted, why = _narrow(tmp_path, LISTED, all_urls=False, failed_only=True)

    assert targeted == {"https://a.test/x"}, "the dirty URL is not a failing one"
    assert "--failed" in why


def test_failed_wins_over_all_because_it_is_the_more_specific_selector(tmp_path):
    """Asking for the failures and getting a full sweep is the same defect again."""
    _with_fail_streaks(tmp_path, {"https://a.test/x": 1})
    targeted, _ = _narrow(tmp_path, LISTED, all_urls=True, failed_only=True)
    assert targeted == {"https://a.test/x"}


def test_failed_never_fetches_a_url_that_is_no_longer_listed(tmp_path):
    """url-state outlives a source list; a removed line must not come back."""
    _with_fail_streaks(tmp_path, {"https://gone.test/x": 3, "https://a.test/x": 1})
    targeted, _ = _narrow(tmp_path, LISTED, all_urls=False, failed_only=True)
    assert targeted == {"https://a.test/x"}


def test_failed_with_nothing_failing_fetches_nothing(tmp_path):
    """The empty set and `None` mean opposite things — this one means nothing to do."""
    dirty.record(tmp_path, ["url:https://c.test/z"])
    targeted, why = _narrow(tmp_path, LISTED, all_urls=False, failed_only=True)
    assert targeted == set(), "an empty set is 'fetch nothing', never 'sweep everything'"
    assert "0 with a failing last run" in why
