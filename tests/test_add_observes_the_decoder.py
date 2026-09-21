"""`fux add <url>` observes the response's type once and writes `decoder=`.

W-199 DoD 10, the pipe ruling. **The add is where a URL's type is OBSERVED;
every run after it is DECLARED** — which is what takes the header-then-extension
ladder out of the maintenance path and puts its answer in a committed line.

🔴 **The fetcher here is a fixture file, so nothing opens a socket.**
`_observed_decoder` loads `.fux/fetchers/<stem>.py` by path and calls its
`fetch(url)`, exactly as ingest does; a fixture that returns
`(bytes, content_type)` is the whole network for this file.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fux import sources
from fux.errors import FuxError


def _args(entry, **flags):
    base = {
        "cdp": False, "http": False, "archived": False, "types": False,
        "dry_run": False, "decoder": None, "fetch": None, "ttl": None,
        "keep": False, "no_keep": False, "no_update": False,
        "no_ingest": True, "no_fetch": False, "no_accelerator": True,
    }
    return SimpleNamespace(entry=entry, **(base | flags))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\n'
        '[sources.url.routes]\n"x.test" = "probe"\n',
        encoding="utf-8",
    )
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text("", encoding="utf-8")
    (tmp_path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    monkeypatch.setattr("fux.sources.find_root", lambda: tmp_path)
    return tmp_path


def _fetcher(repo, returns):
    """Write `.fux/fetchers/probe.py`, returning `returns` verbatim."""
    d = repo / ".fux" / "fetchers"
    d.mkdir(parents=True, exist_ok=True)
    (d / "probe.py").write_text(f"def fetch(url):\n    return {returns}\n", encoding="utf-8")


def _urls(repo):
    return (repo / ".fux" / "sources" / "urls").read_text(encoding="utf-8")


# --- what it writes ---------------------------------------------------------


@pytest.mark.parametrize(
    "returns, expected",
    [
        ('(b"<html><body><p>hi</p></body></html>", "text/html; charset=utf-8")', "decoder=html"),
        ('(b"# T\\n\\nbody\\n", "text/markdown")', "decoder=prose"),
        ('(b"%PDF-1.7\\n", "application/pdf")', "decoder=pdf"),
        ('(b\'{"a": "the paging rotation"}\', "application/json")', "decoder=json"),
        # No recognised type: the URL's own extension is the second layer.
        ('(b"a,b\\n1,2\\n", "application/octet-stream")', "decoder=csv"),
    ],
)
def test_it_writes_the_decoder_it_observed(repo, returns, expected):
    _fetcher(repo, returns)
    assert sources.cmd_add(_args("https://x.test/doc.csv")) == 0
    assert expected in _urls(repo)


def test_the_flag_wins_over_what_was_observed(repo):
    """Edge case 8: the line is written as asked, and the same ingest then
    refuses it via the magic floor — the human sees the disagreement on the
    first run rather than never."""
    _fetcher(repo, '(b"<html>a sign-in shell</html>", "text/html")')
    assert sources.cmd_add(_args("https://x.test/p", decoder="xlsx")) == 0
    assert "decoder=xlsx" in _urls(repo)


def test_the_flag_skips_the_observation_entirely(repo):
    """The probe is one extra request per newly added URL. `--decoder` is how a
    consumer pays nothing for it — asserted by making the fetch fatal."""
    _fetcher(repo, '(_ for _ in ()).throw(RuntimeError("should not be called"))')
    assert sources.cmd_add(_args("https://x.test/p", decoder="prose")) == 0
    assert "decoder=prose" in _urls(repo)


def test_a_re_add_keeps_what_the_line_already_declared(repo):
    """🔴 The `fetch=` pin rule, for the other half.

    Re-adding a URL to change its `ttl` must not silently re-READ it as
    something else — the line is a declaration a human meant.
    """
    _fetcher(repo, '(b"<html><p>hi</p></html>", "text/html")')
    sources.cmd_add(_args("https://x.test/p", decoder="prose"))
    assert "decoder=prose" in _urls(repo)

    sources.cmd_add(_args("https://x.test/p", ttl="7d"))
    assert "decoder=prose" in _urls(repo), "the re-add re-observed a pinned line"
    assert "ttl=7d" in _urls(repo)


# --- what it refuses, and it writes nothing --------------------------------


def test_nothing_maps_is_refused_naming_the_type_and_the_stems(repo):
    """§2 item 4: it never guesses and never writes a line it cannot ingest."""
    _fetcher(repo, '(b"RIFF....WEBP", "image/webp")')
    with pytest.raises(FuxError) as excinfo:
        sources.cmd_add(_args("https://x.test/y.webp"))
    message = str(excinfo.value)
    assert "image/webp" in message and "--decoder" in message
    assert "Built-ins" in message
    assert "x.test" not in _urls(repo), "a refused add writes no line"


def test_a_refusal_fires_BEFORE_the_proposal(repo):
    """Edge case 6. A sign-in shell is valid HTML and would propose
    `decoder=html` perfectly happily — pinning the page fux could not read as
    the page it reads from now on."""
    (repo / ".fux" / "refusals.toml").write_text(
        '[[rule]]\nname = "sso"\nreason = "sign in wall"\nbody_contains = ["loginfmt"]\n',
        encoding="utf-8",
    )
    _fetcher(repo, '(b\'<html><input name="loginfmt"></html>\', "text/html")')
    with pytest.raises(FuxError) as excinfo:
        sources.cmd_add(_args("https://x.test/p"))
    assert "sign in wall" in str(excinfo.value)
    assert "x.test" not in _urls(repo)


def test_a_failed_observing_fetch_writes_no_line_and_says_what_to_do(repo):
    """🔴 **A changed outcome, and the one a consumer will notice.**

    `fux add` against a URL that was down used to write the line and exit 1
    (*"the line is written; the fetch failed"*). There is no line to write now:
    the attribute that makes it loadable is the one the fetch was for.
    """
    _fetcher(repo, '(_ for _ in ()).throw(OSError("connection refused"))')
    with pytest.raises(FuxError) as excinfo:
        sources.cmd_add(_args("https://x.test/p"))
    message = str(excinfo.value)
    assert "connection refused" in message
    assert "--decoder" in message and "nothing was written" in message
    assert "x.test" not in _urls(repo)


def test_a_fetcher_returning_no_bytes_is_refused_too(repo):
    _fetcher(repo, '(b"", "text/html")')
    with pytest.raises(FuxError, match="returned no bytes"):
        sources.cmd_add(_args("https://x.test/p"))
    assert "x.test" not in _urls(repo)


def test_no_fetch_makes_the_flag_mandatory(repo):
    """§3 edge case 7. `--no-fetch` forbids the one thing that observes a type,
    and there is no default to fall back on."""
    _fetcher(repo, '(b"<html><p>hi</p></html>", "text/html")')
    with pytest.raises(FuxError) as excinfo:
        sources.cmd_add(_args("https://x.test/p", no_fetch=True))
    assert "--decoder" in str(excinfo.value)
    assert "x.test" not in _urls(repo)


def test_no_fetch_with_the_flag_writes_the_line_offline(repo):
    _fetcher(repo, '(_ for _ in ()).throw(RuntimeError("should not be called"))')
    assert sources.cmd_add(_args("https://x.test/p", no_fetch=True, decoder="prose")) == 0
    assert "decoder=prose" in _urls(repo)


# --- --dry-run stays offline ----------------------------------------------


def test_dry_run_opens_nothing_and_says_what_fills_the_placeholder(repo, capsys):
    """🔴 A dry run that fetched in order to print a line it then does not write
    is the one place *write nothing* and *do nothing* would come apart on an L4
    surface."""
    _fetcher(repo, '(_ for _ in ()).throw(RuntimeError("should not be called"))')
    assert sources.cmd_add(_args("https://x.test/p", dry_run=True)) == 0
    out = capsys.readouterr().out
    assert "decoder=<observed>" in out
    assert "is not a stem" in out and "--decoder" in out
    assert _urls(repo) == "", "--dry-run writes nothing"


def test_the_placeholder_is_not_a_legal_stem():
    """So a copy-pasted preview fails loudly rather than loading as a decoder
    nobody has."""
    from fux.ingest import sourcelist

    assert sourcelist.URLS.attribute("decoder").reject(sources._OBSERVED_AT_ADD) is not None
