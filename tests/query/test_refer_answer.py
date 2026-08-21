"""PRIORITY.md P6: wiring the refer plane into `answer`.

`refer_answer.answer_via_refer` is the seam between `cmd_answer` and
`fux.refer.refer()` — this suite proves the fetcher resolution (the part
`refer()` itself does not own: which consumer fetcher a `url:` citation
gets, mirroring `ingest/urlsrc.py`'s own resolution exactly) and the honest
`None` degradation when nothing usable can be produced. The e2e proof of the
default-on behaviour and the sha-changes-on-edit case live in
`tests_e2e/test_verbs.py`, against the real CLI.
"""

from __future__ import annotations

from fux import store
from fux.query.refer_answer import _load_fetcher, answer_via_refer

#: Logs every lifecycle call to a sibling file, since `_load_fetcher` loads
#: the module internally with no handle the test can inspect afterwards —
#: the same reason `test_urlsrc.py`'s own fakes log to a dict, just on disk
#: because this module is loaded and discarded by a different process step.
FAKE_FETCHER = '''\
import pathlib

LOG = pathlib.Path(__file__).with_name("calls.log")

def _log(line):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\\n")

def connect():
    _log("connect")

def close():
    _log("close")

def configure(config):
    _log(f"configure:{config}")

def fetch(url):
    _log(f"fetch:{url}")
    return f"# Page\\n\\nrendered body for {url}\\n"
'''


def _sha(text: str) -> str:
    return store.content_sha(text.encode("utf-8"))


def _init_url_repo(tmp_path, *, url="https://x.test/a", config_table=""):
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nfetcher = "mw.py"\n' + config_table, encoding="utf-8"
    )
    (tmp_path / "mw.py").write_text(FAKE_FETCHER, encoding="utf-8")
    urls_path = tmp_path / ".fux" / "sources" / "urls"
    urls_path.parent.mkdir(parents=True, exist_ok=True)
    urls_path.write_text(f"{url}\n", encoding="utf-8")


# -- file: needs no fetcher at all ------------------------------------------


def test_file_document_needs_no_fetcher(tmp_path):
    (tmp_path / "runbook.md").write_text("# R\n\nthe rota hands over Monday\n", encoding="utf-8")
    bundle = answer_via_refer(
        tmp_path, "rota", "file:runbook.md", "runbook.md", _sha("# R\n\nthe rota hands over Monday\n")
    )
    assert bundle is not None
    assert bundle.assembled.citations
    assert bundle.assembled.citations[0].source == "fetched"


def test_file_document_missing_from_the_working_tree_degrades_to_none(tmp_path):
    """Indexed once, gone now — a real fact about the corpus, not a crash."""
    bundle = answer_via_refer(tmp_path, "rota", "file:gone.md", "gone.md", "deadbeef")
    assert bundle is None


# -- url: fetcher resolution mirrors ingest ----------------------------------


def test_url_document_uses_the_configured_fetcher(tmp_path):
    _init_url_repo(tmp_path)
    bundle = answer_via_refer(
        tmp_path, "page", "url:https://x.test/a", "https://x.test/a", _sha("nonsense")
    )
    assert bundle is not None
    assert bundle.assembled.citations
    assert "rendered body for https://x.test/a" in bundle.assembled.citations[0].text
    assert bundle.documents[0].verdict.label == "stale"  # the passed sha never matched


def test_connect_and_close_bracket_the_fetch(tmp_path):
    _init_url_repo(tmp_path)
    fetch, close = _load_fetcher(tmp_path, "url:https://x.test/a", "https://x.test/a")
    assert fetch is not None
    fetch("https://x.test/a")
    close()

    log = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert "connect" in log
    assert log.index("connect") < log.index("fetch:https://x.test/a") < log.index("close")


def test_configure_receives_the_opaque_config_table(tmp_path):
    _init_url_repo(tmp_path, config_table='[sources.url.config]\nport = 9222\n')
    fetch, close = _load_fetcher(tmp_path, "url:https://x.test/a", "https://x.test/a")
    try:
        assert fetch is not None
    finally:
        close()

    log = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("configure:") and "port" in line and "9222" in line for line in log)


def test_a_url_with_no_sources_url_configured_degrades_to_none(tmp_path):
    """No `[sources.url]` at all — nothing to resolve, no crash."""
    fetch, close = _load_fetcher(tmp_path, "url:https://x.test/a", "https://x.test/a")
    assert fetch is None
    close()  # the noop — must be safe to call unconditionally


def test_a_url_not_in_the_committed_list_degrades_to_none(tmp_path):
    """Configured source, but this exact URL was never recorded — same
    honest degradation as no config at all, not a crash."""
    _init_url_repo(tmp_path, url="https://x.test/other")
    fetch, close = _load_fetcher(tmp_path, "url:https://x.test/a", "https://x.test/a")
    assert fetch is None
    close()


def test_a_missing_fetcher_file_degrades_to_none(tmp_path):
    """`[sources.url]` configured, but `fux setup` was never run — the
    refer plane's own graceful `unverified` verdict is what should take
    over, not a crash here."""
    _init_url_repo(tmp_path)
    (tmp_path / "mw.py").unlink()
    fetch, close = _load_fetcher(tmp_path, "url:https://x.test/a", "https://x.test/a")
    assert fetch is None
    close()


def test_answer_via_refer_degrades_to_none_when_the_fetcher_is_missing(tmp_path):
    """The full path: a configured but un-set-up url: source answers `None`,
    never raises, so `cmd_answer` can fall back to the index-only path."""
    _init_url_repo(tmp_path)
    (tmp_path / "mw.py").unlink()
    bundle = answer_via_refer(
        tmp_path, "page", "url:https://x.test/a", "https://x.test/a", "deadbeef"
    )
    assert bundle is None
