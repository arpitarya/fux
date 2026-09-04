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
from fux.query.refer_answer import _load_fetchers, answer_via_refer

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
        '[sources]\n[sources.url]\nmax_parallel = 4\nfetcher = "mw.py"\n' + config_table, encoding="utf-8"
    )
    (tmp_path / "mw.py").write_text(FAKE_FETCHER, encoding="utf-8")
    urls_path = tmp_path / ".fux" / "sources" / "urls"
    urls_path.parent.mkdir(parents=True, exist_ok=True)
    urls_path.write_text(f"{url}\n", encoding="utf-8")


# -- file: needs no fetcher at all ------------------------------------------


def test_file_document_needs_no_fetcher(tmp_path):
    (tmp_path / "runbook.md").write_text("# R\n\nthe rota hands over Monday\n", encoding="utf-8")
    bundle = answer_via_refer(
        tmp_path, "rota",
        [("file:runbook.md", "runbook.md", _sha("# R\n\nthe rota hands over Monday\n"))],
    )
    assert bundle is not None
    assert bundle.assembled.citations
    assert bundle.assembled.citations[0].source == "fetched"


def test_file_document_missing_from_the_working_tree_degrades_to_none(tmp_path):
    """Indexed once, gone now — a real fact about the corpus, not a crash."""
    bundle = answer_via_refer(tmp_path, "rota", [("file:gone.md", "gone.md", "deadbeef")])
    assert bundle is None


# -- url: fetcher resolution mirrors ingest ----------------------------------


def test_url_document_uses_the_configured_fetcher(tmp_path):
    _init_url_repo(tmp_path)
    bundle = answer_via_refer(
        tmp_path, "page", [("url:https://x.test/a", "https://x.test/a", _sha("nonsense"))]
    )
    assert bundle is not None
    assert bundle.assembled.citations
    assert "rendered body for https://x.test/a" in bundle.assembled.citations[0].text
    assert bundle.documents[0].verdict.label == "stale"  # the passed sha never matched


def test_connect_and_close_bracket_the_fetch(tmp_path):
    _init_url_repo(tmp_path)
    fetch, close = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is not None
    fetch("https://x.test/a")
    close()

    log = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert "connect" in log
    assert log.index("connect") < log.index("fetch:https://x.test/a") < log.index("close")


def test_configure_receives_the_opaque_config_table(tmp_path):
    _init_url_repo(tmp_path, config_table='[sources.url.config]\nport = 9222\n')
    fetch, close = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    try:
        assert fetch is not None
    finally:
        close()

    log = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("configure:") and "port" in line and "9222" in line for line in log)


def test_a_url_with_no_sources_url_configured_degrades_to_none(tmp_path):
    """No `[sources.url]` at all — nothing to resolve, no crash."""
    fetch, close = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is None
    close()  # the noop — must be safe to call unconditionally


def test_a_url_not_in_the_committed_list_degrades_to_none(tmp_path):
    """Configured source, but this exact URL was never recorded — same
    honest degradation as no config at all, not a crash."""
    _init_url_repo(tmp_path, url="https://x.test/other")
    fetch, close = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is None
    close()


def test_a_missing_fetcher_file_degrades_to_none(tmp_path):
    """`[sources.url]` configured, but `fux setup` was never run — the
    refer plane's own graceful `unverified` verdict is what should take
    over, not a crash here."""
    _init_url_repo(tmp_path)
    (tmp_path / "mw.py").unlink()
    fetch, close = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is None
    close()


def test_answer_via_refer_degrades_to_none_when_the_fetcher_is_missing(tmp_path):
    """The full path: a configured but un-set-up url: source answers `None`,
    never raises, so `cmd_answer` can fall back to the index-only path."""
    _init_url_repo(tmp_path)
    (tmp_path / "mw.py").unlink()
    bundle = answer_via_refer(
        tmp_path, "page", [("url:https://x.test/a", "https://x.test/a", "deadbeef")]
    )
    assert bundle is None


# -- W-108: the list path ----------------------------------------------------


def _write(tmp_path, name: str, text: str) -> tuple[str, str, str]:
    (tmp_path / name).write_text(text, encoding="utf-8")
    return (f"file:{name}", name, _sha(text))


def test_three_documents_are_referred_in_one_call(tmp_path):
    """The whole point of W-108: **one** `refer()` call over three documents,
    so `_rescore` computes passage `df` across all of them and the contest is
    fair. Three separate calls would score each document's passages against
    only its own siblings, which is a different — and wrong — question."""
    pad = " ".join(f"pad{i}" for i in range(40))
    a = _write(tmp_path, "a.md", f"# A\n\nthe rota {pad}\n")
    b = _write(tmp_path, "b.md", f"# B\n\nthe rota hands over on Monday {pad}\n")
    c = _write(tmp_path, "c.md", f"# C\n\nunrelated {pad}\n")

    bundle = answer_via_refer(tmp_path, "rota hands over", [a, b, c])
    assert bundle is not None
    assert {d.doc_id for d in bundle.documents} == {"file:a.md", "file:b.md", "file:c.md"}
    # The winning passage may come from a document that was not first in.
    assert bundle.assembled.citations[0].doc_id == "file:b.md"


def test_the_assembled_answer_never_exceeds_the_budget(tmp_path):
    """The budget invariant, with three documents competing for it.

    ⚠ **This is `used <= budget`, and it is NOT "no more bytes than one
    document used".** Three documents fill a budget one document left mostly
    empty — measured at a mean 2 517 -> 6 467 bytes over the 43 graded queries
    ([the run](../../work/regression/2026-09-05-answer-top3/report.md)). The
    bound the caller declared is what holds; the bytes actually spent go up,
    which is the price of the recall and is reported rather than asserted away.
    """
    pad = " ".join(f"pad{i}" for i in range(400))
    docs = [_write(tmp_path, f"{n}.md", f"# {n}\n\nthe rota hands over {pad}\n") for n in "abc"]
    bundle = answer_via_refer(tmp_path, "rota hands over", docs)
    assert bundle is not None
    assert bundle.assembled.used <= bundle.assembled.budget


def test_one_unreachable_document_costs_its_own_citation_and_no_more(tmp_path):
    """Per-document degradation. A `url:` citation with no fetcher configured
    drops out; the `file:` documents beside it still answer."""
    pad = " ".join(f"pad{i}" for i in range(40))
    good = _write(tmp_path, "good.md", f"# G\n\nthe rota hands over {pad}\n")
    bundle = answer_via_refer(
        tmp_path, "rota hands over", [("url:https://x.test/a", "https://x.test/a", "deadbeef"), good]
    )
    assert bundle is not None
    assert {c.doc_id for c in bundle.assembled.citations} == {"file:good.md"}
    unreachable = next(d for d in bundle.documents if d.doc_id.startswith("url:"))
    assert unreachable.verdict.label == "unverified"


def test_every_document_failing_is_the_only_none(tmp_path):
    """`None` is reserved for *nothing usable at all* — the caller's signal to
    fall back to the index path. One survivor is not that case."""
    assert answer_via_refer(
        tmp_path, "rota", [("file:gone.md", "gone.md", "x"), ("file:also-gone.md", "also-gone.md", "y")]
    ) is None
    assert answer_via_refer(tmp_path, "rota", []) is None


def test_an_empty_citation_list_loads_no_fetcher(tmp_path):
    fetch, close = _load_fetchers(tmp_path, [])
    assert fetch is None
    close()


def test_a_file_only_candidate_set_loads_no_fetcher(tmp_path):
    """No config read, no module import, no `connect()` — the `file:`-only
    corpus takes exactly the path it took before the dispatcher existed."""
    _init_url_repo(tmp_path)
    fetch, close = _load_fetchers(tmp_path, [("file:a.md", "a.md", "sha")])
    assert fetch is None
    close()
    assert not (tmp_path / "calls.log").exists()


def test_two_urls_behind_different_fetchers_each_get_their_own(tmp_path):
    """🔴 The defect the dispatcher exists to prevent.

    `refer()` takes one `fetcher` for the whole call. Handing both URLs the
    first one's module compares a rendered page against a shell and reports a
    **false staleness on every query** (`refer/source.py`). Each URL must reach
    the fetcher its own line names.

    `fetch=` is a closed set — `http` or `cdp` — so those are the two names,
    and they are exactly the pair the failure is about: `http.py` sees a
    rendered page's shell, `cdp.py` sees the page."""
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\nfetcher = ".fux/fetchers/http.py"\n',
        encoding="utf-8",
    )
    fetchers = tmp_path / ".fux" / "fetchers"
    fetchers.mkdir(parents=True)
    for name in ("http", "cdp"):
        (fetchers / f"{name}.py").write_text(
            FAKE_FETCHER.replace('"calls.log"', f'"calls-{name}.log"').replace(
                "rendered body for", f"{name} body for"
            ),
            encoding="utf-8",
        )
    urls = tmp_path / ".fux" / "sources" / "urls"
    urls.parent.mkdir(parents=True, exist_ok=True)
    urls.write_text("https://x.test/a\nhttps://x.test/b  fetch=cdp\n", encoding="utf-8")

    fetch, close = _load_fetchers(
        tmp_path,
        [("url:https://x.test/a", "https://x.test/a", "s1"),
         ("url:https://x.test/b", "https://x.test/b", "s2")],
    )
    try:
        assert "http body for https://x.test/a" in fetch("https://x.test/a")
        assert "cdp body for https://x.test/b" in fetch("https://x.test/b")
    finally:
        close()

    # The fake logs beside its own module file, which here is `.fux/fetchers/`.
    for name in ("http", "cdp"):
        log = (fetchers / f"calls-{name}.log").read_text(encoding="utf-8").splitlines()
        assert log.count("connect") == 1 and "close" in log


def test_two_urls_behind_one_fetcher_connect_once(tmp_path):
    _init_url_repo(tmp_path, url="https://x.test/a")
    (tmp_path / ".fux" / "sources" / "urls").write_text(
        "https://x.test/a\nhttps://x.test/b\n", encoding="utf-8"
    )
    fetch, close = _load_fetchers(
        tmp_path,
        [("url:https://x.test/a", "https://x.test/a", "s1"),
         ("url:https://x.test/b", "https://x.test/b", "s2")],
    )
    try:
        fetch("https://x.test/a")
        fetch("https://x.test/b")
    finally:
        close()
    log = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    assert log.count("connect") == 1
    assert log.count("close") == 1


def test_a_url_with_no_route_raises_rather_than_fetching_with_the_wrong_module(tmp_path):
    """A `FuxError`, which `source._fetch_url` turns into *this document's*
    `unverified` verdict. Returning empty text instead would be a citation
    against bytes nobody fetched."""
    from fux.errors import FuxError

    _init_url_repo(tmp_path, url="https://x.test/a")
    fetch, close = _load_fetchers(
        tmp_path,
        [("url:https://x.test/a", "https://x.test/a", "s1"),
         ("url:https://x.test/missing", "https://x.test/missing", "s2")],
    )
    try:
        import pytest

        with pytest.raises(FuxError):
            fetch("https://x.test/missing")
    finally:
        close()
