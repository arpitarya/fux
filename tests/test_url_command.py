"""`fux url` — the managing command (ADR-URL-LIST decisions 12 and 13).

Three properties carry the design: a written line states **every** attribute,
the command **never fetches**, and it edits **one line** rather than
regenerating the file.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fux import sources
from fux.errors import FuxError


def _args(url=None, **flags):
    base = {"cdp": False, "http": False, "plain": False, "hashed": False, "remove": False}
    return SimpleNamespace(url=url, **(base | flags))


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text("# my list\n", encoding="utf-8")
    return tmp_path


def _urls(repo):
    return (repo / ".fux" / "sources" / "urls").read_text(encoding="utf-8")


def _run(repo, monkeypatch, args):
    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    return sources.cmd_url(args)


# -- decision 12: a written line states everything -------------------------


def test_a_written_line_carries_every_attribute_even_at_its_default(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/a"))
    assert "https://x.test/a fetch=http meta=hashed" in _urls(repo)


def test_flags_decide_what_is_recorded(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/a", cdp=True, plain=True))
    assert "https://x.test/a fetch=cdp meta=plain" in _urls(repo)


def test_an_unflagged_attribute_keeps_what_the_line_already_said(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/a", cdp=True, plain=True))
    _run(repo, monkeypatch, _args("https://x.test/a", hashed=True))
    assert "https://x.test/a fetch=cdp meta=hashed" in _urls(repo)


def test_two_flags_for_one_attribute_is_an_error(repo, monkeypatch):
    with pytest.raises(FuxError, match="both set `fetch`"):
        _run(repo, monkeypatch, _args("https://x.test/a", cdp=True, http=True))
    with pytest.raises(FuxError, match="both set `meta`"):
        _run(repo, monkeypatch, _args("https://x.test/a", plain=True, hashed=True))


def test_a_non_http_url_is_refused_before_anything_is_written(repo, monkeypatch):
    with pytest.raises(FuxError, match="not an http"):
        _run(repo, monkeypatch, _args("ftp://x.test/a"))
    assert _urls(repo) == "# my list\n"


# -- one line, never the file ----------------------------------------------


def test_a_grouping_comment_survives_an_edit(repo, monkeypatch):
    (repo / ".fux" / "sources" / "urls").write_text(
        "# my list\n\n# team: platform\nhttps://x.test/a fetch=http meta=hashed\n", encoding="utf-8"
    )
    _run(repo, monkeypatch, _args("https://x.test/a", cdp=True))
    text = _urls(repo)
    assert "# team: platform" in text
    assert "https://x.test/a fetch=cdp meta=hashed" in text


def test_a_trailing_comment_survives_an_edit(repo, monkeypatch):
    (repo / ".fux" / "sources" / "urls").write_text(
        "https://x.test/a fetch=http meta=hashed   # why this URL is here\n", encoding="utf-8"
    )
    _run(repo, monkeypatch, _args("https://x.test/a", plain=True))
    line = _urls(repo).strip()
    assert line == "https://x.test/a fetch=http meta=plain  # why this URL is here"


def test_lines_land_in_sorted_order(repo, monkeypatch):
    for url in ("https://x.test/c", "https://x.test/a", "https://x.test/b"):
        _run(repo, monkeypatch, _args(url))
    entries = [line for line in _urls(repo).splitlines() if line.startswith("https")]
    assert entries == sorted(entries)


def test_the_file_always_ends_in_exactly_one_newline(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/a"))
    _run(repo, monkeypatch, _args("https://x.test/b"))
    text = _urls(repo)
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_the_file_is_written_lf_only_regardless_of_host_os(repo, monkeypatch):
    """`write_text`'s platform-default newline translation would commit CRLF
    on Windows and LF everywhere else, breaking L3's byte-identical
    guarantee across machines. `newline="\\n"` disables it.
    """
    _run(repo, monkeypatch, _args("https://x.test/a"))
    _run(repo, monkeypatch, _args("https://x.test/b"))
    raw = (repo / ".fux" / "sources" / "urls").read_bytes()
    assert b"\r" not in raw


def test_removing_a_url_deletes_its_line_and_nothing_else(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/a"))
    _run(repo, monkeypatch, _args("https://x.test/b"))
    _run(repo, monkeypatch, _args("https://x.test/a", remove=True))
    text = _urls(repo)
    assert "https://x.test/a" not in text
    assert "https://x.test/b fetch=http meta=hashed" in text
    assert "# my list" in text


def test_removing_a_url_that_is_not_listed_fails_loudly(repo, monkeypatch):
    with pytest.raises(FuxError, match="is not in"):
        _run(repo, monkeypatch, _args("https://x.test/nope", remove=True))


# -- fragments, which is why the parser changed ----------------------------


def test_a_fragment_bearing_url_round_trips_through_the_command(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/page#section", cdp=True))
    assert "https://x.test/page#section fetch=cdp meta=hashed" in _urls(repo)
    from fux.ingest.urlsrc import read_urls

    (entry,) = read_urls(repo, ".fux/sources/urls")
    assert entry.value == "https://x.test/page#section"
    assert entry.attrs["fetch"] == "cdp"


def test_two_urls_differing_only_by_fragment_get_two_lines(repo, monkeypatch):
    _run(repo, monkeypatch, _args("https://x.test/p#a"))
    _run(repo, monkeypatch, _args("https://x.test/p#b"))
    entries = [line for line in _urls(repo).splitlines() if line.startswith("https")]
    assert len(entries) == 2


# -- it never fetches (law L4) ---------------------------------------------


def test_the_command_opens_no_socket(repo, monkeypatch):
    """`--cdp`/`--plain` decide what is RECORDED, never what is fetched."""
    import socket

    def refuse(*args, **kwargs):  # pragma: no cover - the point is that it never runs
        raise AssertionError("fux url must not touch the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr("urllib.request.urlopen", refuse)
    _run(repo, monkeypatch, _args("https://x.test/a", cdp=True))
    assert "https://x.test/a" in _urls(repo)


def test_the_module_imports_no_network_library():
    source = (
        __import__("pathlib").Path(sources.__file__).read_text(encoding="utf-8")
    )
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            assert not any(
                name in stripped for name in ("urllib", "socket", "http.client", "ssl")
            ), stripped


# -- listing ---------------------------------------------------------------


def test_listing_marks_a_line_fux_did_not_write(repo, monkeypatch, capsys):
    (repo / ".fux" / "sources" / "urls").write_text(
        "https://x.test/a\nhttps://x.test/b fetch=cdp meta=plain\n", encoding="utf-8"
    )
    _run(repo, monkeypatch, _args())
    out = capsys.readouterr().out
    assert "* https://x.test/a fetch=http meta=hashed" in out
    assert "  https://x.test/b fetch=cdp meta=plain" in out
    assert "do not state every attribute" in out


def test_listing_an_empty_list_says_so(repo, monkeypatch, capsys):
    _run(repo, monkeypatch, _args())
    assert "no URLs listed" in capsys.readouterr().out
