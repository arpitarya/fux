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


def _write_fetcher(root, text, name="mw.py", encoding="utf-8"):
    """Write a fixture fetcher where the resolver looks for it.

    ⚠ **`.fux/fetchers/` is the only place now.** Until 2026-09-20 a fixture
    could put a fetcher anywhere and point `[sources.url] fetcher` at it; that
    key is deleted (W-199 D2) and the directory is fixed, so the fixture creates
    it rather than relying on `fux setup` having run.
    """
    path = root / ".fux" / "fetchers" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path



def _sha(text: str) -> str:
    return store.content_sha(text.encode("utf-8"))


def _init_url_repo(tmp_path, *, url="https://x.test/a", config_table=""):
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\n' + config_table, encoding="utf-8"
    )
    _write_fetcher(tmp_path, FAKE_FETCHER)
    urls_path = tmp_path / ".fux" / "sources" / "urls"
    urls_path.parent.mkdir(parents=True, exist_ok=True)
    # 🔴 Every URL line states its fetcher since 2026-09-20 (W-199 D2). A case
    # that pins a different one passes it in `url` and this leaves it alone.
    line = url if "fetch=" in url else f"{url} fetch=mw"
    urls_path.write_text(f"{line}\n", encoding="utf-8")


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
    fetch, close, _fa = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is not None
    fetch("https://x.test/a")
    close()

    log = (tmp_path / ".fux" / "fetchers" / "calls.log").read_text(encoding="utf-8").splitlines()
    assert "connect" in log
    assert log.index("connect") < log.index("fetch:https://x.test/a") < log.index("close")


def test_configure_receives_the_opaque_config_table(tmp_path):
    _init_url_repo(tmp_path, config_table='[sources.url.config]\nport = 9222\n')
    fetch, close, _fa = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    try:
        assert fetch is not None
    finally:
        close()

    log = (tmp_path / ".fux" / "fetchers" / "calls.log").read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("configure:") and "port" in line and "9222" in line for line in log)


def test_a_url_with_no_sources_url_configured_degrades_to_none(tmp_path):
    """No `[sources.url]` at all — nothing to resolve, no crash."""
    fetch, close, _fa = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is None
    close()  # the noop — must be safe to call unconditionally


def test_a_url_not_in_the_committed_list_degrades_to_none(tmp_path):
    """Configured source, but this exact URL was never recorded — same
    honest degradation as no config at all, not a crash."""
    _init_url_repo(tmp_path, url="https://x.test/other")
    fetch, close, _fa = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is None
    close()


def test_a_missing_fetcher_file_degrades_to_none(tmp_path):
    """`[sources.url]` configured, but `fux setup` was never run — the
    refer plane's own graceful `unverified` verdict is what should take
    over, not a crash here."""
    _init_url_repo(tmp_path)
    (tmp_path / ".fux" / "fetchers" / "mw.py").unlink()
    fetch, close, _fa = _load_fetchers(tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")])
    assert fetch is None
    close()


def test_answer_via_refer_degrades_to_none_when_the_fetcher_is_missing(tmp_path):
    """The full path: a configured but un-set-up url: source answers `None`,
    never raises, so `cmd_answer` can fall back to the index-only path."""
    _init_url_repo(tmp_path)
    (tmp_path / ".fux" / "fetchers" / "mw.py").unlink()
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
    fetch, close, _fa = _load_fetchers(tmp_path, [])
    assert fetch is None
    close()


def test_a_file_only_candidate_set_loads_no_fetcher(tmp_path):
    """No config read, no module import, no `connect()` — the `file:`-only
    corpus takes exactly the path it took before the dispatcher existed."""
    _init_url_repo(tmp_path)
    fetch, close, _fa = _load_fetchers(tmp_path, [("file:a.md", "a.md", "sha")])
    assert fetch is None
    close()
    assert not (tmp_path / ".fux" / "fetchers" / "calls.log").exists()


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
        '[sources]\n[sources.url]\nmax_parallel = 4\n',
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
    urls.write_text("https://x.test/a fetch=http\nhttps://x.test/b  fetch=cdp\n", encoding="utf-8")

    fetch, close, _fa = _load_fetchers(
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
        "https://x.test/a fetch=mw\nhttps://x.test/b fetch=mw\n", encoding="utf-8"
    )
    fetch, close, _fa = _load_fetchers(
        tmp_path,
        [("url:https://x.test/a", "https://x.test/a", "s1"),
         ("url:https://x.test/b", "https://x.test/b", "s2")],
    )
    try:
        fetch("https://x.test/a")
        fetch("https://x.test/b")
    finally:
        close()
    log = (tmp_path / ".fux" / "fetchers" / "calls.log").read_text(encoding="utf-8").splitlines()
    assert log.count("connect") == 1
    assert log.count("close") == 1


def test_a_url_with_no_route_raises_rather_than_fetching_with_the_wrong_module(tmp_path):
    """A `FuxError`, which `source._fetch_url` turns into *this document's*
    `unverified` verdict. Returning empty text instead would be a citation
    against bytes nobody fetched."""
    from fux.errors import FuxError

    _init_url_repo(tmp_path, url="https://x.test/a")
    fetch, close, _fa = _load_fetchers(
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


# -- W-174: `[sources.url] fetch_at_answer` -----------------------------------
#
# The behaviour these prove was BUILT AND UNREACHABLE until 2026-09-14:
# `Policy(mode=NEVER)` and `_obtain`'s never-branch have always existed, and
# this module constructed `Policy(mode=ALWAYS, ...)` literally. What is under
# test here is the SELECTOR — which mode the seam builds, and what it reports.


def test_fetch_at_answer_defaults_to_true(tmp_path):
    """Silence means today's behaviour. No repo changes meaning on upgrade."""
    _init_url_repo(tmp_path)
    _fetch, close, fetch_at_answer = _load_fetchers(
        tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")]
    )
    close()
    assert fetch_at_answer is True


def test_fetch_at_answer_false_rides_out_of_the_resolver(tmp_path):
    _init_url_repo(tmp_path, config_table="fetch_at_answer = false\n")
    _fetch, close, fetch_at_answer = _load_fetchers(
        tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")]
    )
    close()
    assert fetch_at_answer is False


def test_an_unresolvable_url_still_reports_the_real_policy(tmp_path):
    """⚠ The `not routes` path reads config, so it must not report a guess.

    Stamping the wrong mode into the receipt is the silent-policy-swap failure
    `Policy.as_record` exists to close, and this is an early return where
    config was genuinely read — so it returns what the repo actually said.
    """
    _init_url_repo(tmp_path, url="https://x.test/other")
    fetch, close, fetch_at_answer = _load_fetchers(
        tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")]
    )
    close()
    assert fetch is None
    assert fetch_at_answer is True


def test_a_file_only_candidate_set_reads_no_config_at_all(tmp_path):
    """The property `_load_fetchers` has always had, kept by the third value.

    `True` here is not a default — it is the honest answer to a question that
    was never asked. A `fux.toml` that would REFUSE to load proves nothing was
    read: `max_parallel` is required whenever `[sources.url]` exists.
    """
    (tmp_path / "fux.toml").write_text("[sources]\n[sources.url]\n", encoding="utf-8")
    fetch, close, fetch_at_answer = _load_fetchers(tmp_path, [("file:a.md", "a.md", "sha")])
    close()
    assert fetch is None
    assert fetch_at_answer is True


def test_never_verifies_against_acquired_and_never_opens_a_socket(tmp_path):
    """The whole point, end to end through `answer_via_refer`.

    The fake fetcher logs every call to `.fux/fetchers/calls.log` — beside
    itself, which is where it moved on 2026-09-20 — so *no log file at all* is
    the assertion that no socket was opened — stronger than trusting a mode
    string. Under `never` the fetcher is not even loaded, so `configure()` and
    `connect()` never run either.
    """
    from fux.store import acquired

    body = "# Page\n\nthe retained body\n"
    _init_url_repo(tmp_path, config_table="fetch_at_answer = false\n")
    blob = acquired.save(tmp_path, "https://x.test/a", body.encode("utf-8"), "text/markdown", ".md")
    # ⚠ `save()` writes the blob and NEVER the manifest (it runs under a thread
    # pool in the real path); `from_acquired` reads the manifest. A test that
    # saves and does not record is a plane with nothing findable in it.
    acquired.write_manifest(tmp_path, {"https://x.test/a": blob})

    bundle = answer_via_refer(
        tmp_path, "retained", [("url:https://x.test/a", "https://x.test/a", _sha(body))]
    )
    assert bundle is not None
    assert bundle.policy["mode"] == "never"
    assert bundle.documents[0].verdict.label == "as-ingested"
    assert not (tmp_path / ".fux" / "fetchers" / "calls.log").exists()


def test_never_with_no_retained_bytes_is_unverified_not_a_crash(tmp_path):
    """Arpit's ruling, 2026-09-14: disclosed, never refused. `fux doctor`
    carries the disclosure; the query keeps answering."""
    _init_url_repo(tmp_path, config_table="fetch_at_answer = false\n")
    bundle = answer_via_refer(
        tmp_path, "nothing retained", [("url:https://x.test/a", "https://x.test/a", "sha")]
    )
    assert bundle is None or bundle.documents[0].verdict.label == "unverified"
    assert not (tmp_path / ".fux" / "fetchers" / "calls.log").exists()


def test_cache_ttl_is_declared_inert_rather_than_silently_dropped(tmp_path, capsys):
    """W-140 row 6 from the other end: a knob that cannot act must say so."""
    _init_url_repo(tmp_path, config_table="fetch_at_answer = false\n")
    answer_via_refer(
        tmp_path,
        "q",
        [("url:https://x.test/a", "https://x.test/a", "sha")],
        cache_ttl_seconds=3600,
    )
    err = capsys.readouterr().err
    assert "--cache-ttl has no effect" in err
    assert "fetch_at_answer" in err
