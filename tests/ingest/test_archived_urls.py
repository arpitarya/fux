"""`archived=` on a URL line — W-126, Arpit 2026-09-11.

A retired page behind a URL could not be declared retired at all: `dirs` lines
have carried `archived` since 2026-08-22 and `urls` lines did not. That was
never a decision, just the order the two lists were built in, and it left fux
worst at exactly the document it most needs the declaration for — BM25F cannot
see negation, so a page that honestly says "no longer current" hands the query
the token `current`.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fux.ingest.run import _archived_url_ids, _with_archived
from fux.ingest.sourcelist import URLS, parse
from fux.ingest.urlsrc import resolve_urls


def _repo(tmp_path, body):
    (tmp_path / ".fux" / "sources").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text(body, encoding="utf-8")
    return SimpleNamespace(url=None, urls_file=".fux/sources/urls")


# -- the declaration reaches the ingest ------------------------------------


def test_only_the_lines_that_declare_it_are_archived(tmp_path):
    config = _repo(
        tmp_path,
        "https://x.test/live\nhttps://x.test/old archived=true\n",
    )
    assert _archived_url_ids(tmp_path, config) == {"url:https://x.test/old"}


def test_archived_false_is_not_archived(tmp_path):
    """Stated-at-the-default is how every fux-written line looks."""
    config = _repo(tmp_path, "https://x.test/a fetch=http archived=false\n")
    assert _archived_url_ids(tmp_path, config) == set()


def test_an_absent_list_is_empty_and_never_raises(tmp_path):
    """The caller only asks when `url:` records exist, and a missing list with
    surviving records is already `_listed_url_ids`' loud error — this must not
    be a second, worse copy of it."""
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    assert _archived_url_ids(tmp_path, SimpleNamespace(url=None, urls_file=".fux/sources/urls")) == set()


def test_it_reads_the_list_without_a_sources_url_block(tmp_path):
    """`archived` is line-level only, so resolution needs no `[sources.url]`.

    That is what lets the OFFLINE ingest path resolve the flag as completely as
    the fetching one — a repo can retire a page and have it take effect on the
    next plain `fux ingest`, with no network.
    """
    config = _repo(tmp_path, "https://x.test/old archived=true\n")
    assert config.url is None
    assert _archived_url_ids(tmp_path, config) == {"url:https://x.test/old"}


# -- the resolved entry -----------------------------------------------------


def test_resolve_urls_carries_the_flag():
    entries = parse("https://x.test/old archived=true\n", URLS, origin="t")
    source = SimpleNamespace(fetcher=".fux/fetchers/http.py", meta="hashed", keep=True, ttl="24h")
    (resolved,) = resolve_urls(entries, source)
    assert resolved.archived is True


def test_an_undeclared_line_resolves_to_not_archived():
    entries = parse("https://x.test/a\n", URLS, origin="t")
    source = SimpleNamespace(fetcher=".fux/fetchers/http.py", meta="hashed", keep=True, ttl="24h")
    (resolved,) = resolve_urls(entries, source)
    assert resolved.archived is False


# -- carried records --------------------------------------------------------


def test_a_carried_record_gains_the_flag_without_a_refetch():
    """The point of applying this to carried records.

    A retired page is precisely the one that has stopped changing, so if the
    flag only landed when the bytes moved it would never land at all.
    """
    record = {"id": "url:https://x.test/old", "sha": "abc"}
    assert _with_archived(record, True) == {"id": "url:https://x.test/old", "sha": "abc", "archived": True}


def test_removing_the_declaration_clears_the_flag():
    """A flag that can be set and never cleared is a one-way door."""
    record = {"id": "url:https://x.test/old", "sha": "abc", "archived": True}
    assert "archived" not in _with_archived(record, False)


@pytest.mark.parametrize("archived", [True, False])
def test_an_agreeing_record_is_returned_UNCOPIED(archived):
    """L3: a run that changes nothing writes byte-identical shards, so the
    no-change path must not even allocate a new dict."""
    record = {"id": "url:x", "sha": "abc"}
    if archived:
        record["archived"] = True
    assert _with_archived(record, archived) is record
