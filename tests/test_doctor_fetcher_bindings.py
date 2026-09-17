"""`fux doctor`'s `fetcher bindings` row — the price of an open `fetch=` set.

**W-178.** `fetch=` is a typed attribute validated by name shape, so a consumer
drops `.fux/fetchers/glassbox.py` in and writes `fetch=glassbox`. The price is
that a **typo parses**: `fetch=glasbox` is a perfectly legal line naming a file
nobody wrote, where the old enum would have refused it at read time.

🔴 **Without this row that line is discovered by the next person's ingest dying
mid-run**, on their machine, with their commit in the blame. Exactly the
argument W-101 item 2 made for `decoder bindings`, which is why the two are a
pair rather than two checks that happen to look alike.
"""

from __future__ import annotations

import pytest

from fux.doctor import _fetcher_bindings


def _repo(tmp_path, *, urls: str, fetchers=("http",)):
    (tmp_path / "fux.toml").write_text(
        '[sources]\nurls_file = ".fux/sources/urls"\n'
        '[sources.url]\nfetcher = ".fux/fetchers/http.py"\nmax_parallel = 4\n',
        encoding="utf-8",
    )
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text(urls, encoding="utf-8")
    d = tmp_path / ".fux" / "fetchers"
    d.mkdir(parents=True)
    for stem in fetchers:
        (d / f"{stem}.py").write_text("def fetch(url):\n    return ''\n", encoding="utf-8")
    return tmp_path


def test_a_name_with_a_file_passes(tmp_path):
    check = _fetcher_bindings(_repo(tmp_path, urls="https://x.test/a fetch=http\n"))
    assert check.ok
    assert "1 fetcher name(s) in use" in check.detail


def test_a_custom_name_with_a_file_passes(tmp_path):
    """The whole point of W-178, seen from `doctor`: a name fux never shipped."""
    repo = _repo(
        tmp_path, urls="https://x.test/a fetch=glassbox\n", fetchers=("http", "glassbox")
    )
    assert _fetcher_bindings(repo).ok


def test_a_name_with_no_file_fails_and_names_it(tmp_path):
    """The typo the enum used to catch, caught one layer later instead."""
    repo = _repo(tmp_path, urls="https://x.test/a fetch=glasbox\n")
    check = _fetcher_bindings(repo)
    assert not check.ok
    assert "glasbox" in check.detail
    assert "fails at ingest time" in check.detail


def test_it_reports_the_directory_contents_so_the_fix_is_visible(tmp_path):
    """A name with no file is usually a typo, and the fix is the list beside it."""
    repo = _repo(tmp_path, urls="https://x.test/a fetch=glasbox\n", fetchers=("http", "cdp"))
    detail = _fetcher_bindings(repo).detail
    assert "'cdp'" in detail and "'http'" in detail


def test_it_reads_the_list_not_the_index(tmp_path):
    """🔴 **The opposite choice from `decoder bindings`, and right for a
    different reason.**

    A decoder binding is interesting when it matches no *document*, so that
    check counts against the committed index. A fetcher name is wrong when it
    matches no *file* — true the moment the line is written, which is the
    moment somebody can still fix it cheaply. There is no index here at all.
    """
    repo = _repo(tmp_path, urls="https://x.test/a fetch=glasbox\n")
    assert not (repo / ".fux" / "index").exists()
    assert not _fetcher_bindings(repo).ok


def test_no_url_source_is_not_a_finding(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    assert _fetcher_bindings(tmp_path).ok


def test_it_never_imports_a_fetcher(tmp_path, monkeypatch):
    """🔴 **The reason the grammar checks shape and `doctor` checks existence.**

    Importing a fetcher runs module-level consumer code that may `connect()` to
    a browser. `fux doctor` is the command somebody runs when something is
    already wrong; it may not be the command that executes their fetcher — and
    it is offline by contract (SR-LAW-4 decision 4).
    """
    import importlib

    repo = _repo(
        tmp_path, urls="https://x.test/a fetch=glassbox\n", fetchers=("http", "glassbox")
    )
    (repo / ".fux" / "fetchers" / "glassbox.py").write_text(
        'raise AssertionError("doctor imported a fetcher")\n', encoding="utf-8"
    )

    def explode(*a, **k):  # pragma: no cover - the point is that it is not called
        raise AssertionError("doctor imported a module by path")

    monkeypatch.setattr(importlib.util, "spec_from_file_location", explode)
    assert _fetcher_bindings(repo).ok
