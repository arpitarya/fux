"""Where bytes come from — and the fence that says fux still does not fetch."""

from __future__ import annotations

import ast
import inspect
import sys

import pytest

from fux.errors import FuxError
from fux.refer.source import GIT, URL, fetch_document, resolve

import fux.refer.source  # for the registry lookup below

source_mod = sys.modules["fux.refer.source"]


def test_the_scheme_picks_the_strategy():
    assert resolve("file:docs/a.md") == GIT
    assert resolve("url:https://x.test/p") == URL


def test_an_unknown_scheme_is_refused_rather_than_guessed():
    with pytest.raises(FuxError, match="unknown id scheme"):
        resolve("ftp:whatever")


def test_a_git_document_is_read_from_the_checkout(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8", newline="\n")
    fetched = fetch_document(tmp_path, "file:a.md", "a.md")
    assert fetched.content == b"# A\n" and fetched.strategy == GIT


def test_a_missing_git_document_is_a_dead_citation(tmp_path):
    with pytest.raises(FuxError, match="no longer in the working tree"):
        fetch_document(tmp_path, "file:gone.md", "gone.md")


def test_a_url_document_needs_a_fetcher_and_says_so(tmp_path):
    with pytest.raises(FuxError, match="no fetcher loaded"):
        fetch_document(tmp_path, "url:https://x.test/p", "https://x.test/p")


def test_a_fetcher_that_raises_becomes_a_fux_error_not_a_crash(tmp_path):
    """Consumer code runs here. It must never take the query down with it."""
    def boom(url):
        raise ZeroDivisionError("consumer bug")

    with pytest.raises(FuxError, match="ZeroDivisionError"):
        fetch_document(tmp_path, "url:https://x.test/p", "https://x.test/p", fetcher=boom)


def test_an_undecodable_type_is_refused_with_the_reason_not_a_type_complaint(tmp_path):
    """Undecodable is a stated reason about the response, never about Python types.

    A content type nothing claims has no markdown to compare against, so the
    caller is told which of the two it was — the same sentence ingest would
    have recorded as a skip.
    """
    response = (b"\x00\x01binary", "application/octet-stream")
    with pytest.raises(FuxError, match="no decoder for application/octet-stream"):
        fetch_document(tmp_path, "url:https://x.test/p", "https://x.test/p", fetcher=lambda u: response)


def test_a_pre_contract_fetcher_returning_markdown_still_verifies(tmp_path):
    """The transition ramp `_unpack` keeps, asserted where it is relied on.

    Every consumer fetcher written before 2026-08-26 returns prose. Refusing
    one here would break verification in repos that upgraded fux and nothing
    else.
    """
    fetched = fetch_document(
        tmp_path, "url:https://x.test/p", "https://x.test/p", fetcher=lambda u: "# Heading\n"
    )
    assert fetched.content == b"# Heading\n"


def test_a_tuple_returning_fetcher_is_decoded_exactly_as_ingest_decoded_it(tmp_path):
    """W-140 row 1 — the regression that made every URL citation unverifiable.

    Both shipped fetchers return `(bytes, content type)` since W-86 P8. This
    module went on requiring a `str`, so every live verification failed with
    `fetcher returned tuple, expected str` and fell back to `as-ingested` or
    `unverified` — a legitimate-looking verdict, which is why it survived.

    The assertion is not "it no longer raises": it is that the bytes this
    returns are **byte-identical to what ingest committed** from the same
    response. Anything less and a verified document reports `drifted` against
    itself.
    """
    from fux.ingest import urlsrc

    html = b"<html><body><h1>Title</h1><p>Body text here.</p></body></html>"
    response = (html, "text/html; charset=utf-8")

    fetched = fetch_document(
        tmp_path, "url:https://x.test/p", "https://x.test/p", fetcher=lambda u: response
    )

    markdown, why = urlsrc._decode_fetched(html, "text/html; charset=utf-8", "https://x.test/p", tmp_path)
    assert why == "" and markdown is not None
    assert fetched.content == urlsrc.sanitize(markdown)
    assert fetched.strategy == URL
    assert b"<h1>" not in fetched.content  # decoded, not the raw response


def test_the_decode_step_travels_with_the_normalization(tmp_path):
    """The identity that keeps the two halves from drifting apart again.

    `sanitize` was already shared and asserted; `_decode_fetched` was not, and
    that is exactly the half that fell behind the contract.
    """
    from fux.ingest import urlsrc

    assert source_mod._decode_fetched is urlsrc._decode_fetched
    assert source_mod._unpack is urlsrc._unpack


def test_verify_time_normalization_is_the_same_function_ingest_uses(tmp_path):
    """The load-bearing identity.

    A verify-time sha is compared against an ingest-time sha. If the two
    normalizations diverged by one character, every URL document would report
    as permanently stale — a defect that presents as a working feature.
    """
    from fux.ingest import urlsrc

    assert source_mod.sanitize is urlsrc.sanitize

    raw = "line\r\nnext after"
    fetched = fetch_document(tmp_path, "url:https://x.test/p", "https://x.test/p", fetcher=lambda u: raw)
    assert fetched.content == urlsrc.sanitize(raw)


def test_this_module_imports_no_network_library():
    """The same fence `sources.py` carries, on the module most tempted to break it."""
    for line in inspect.getsource(source_mod).splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            assert not any(
                name in stripped for name in ("urllib", "socket", "http.client", "ssl")
            ), stripped


def test_the_fetcher_is_injected_never_imported():
    """`src/fux/` must hold no path that reaches transport on its own."""
    tree = ast.parse(inspect.getsource(source_mod))
    calls = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert not any("import_module" in c or "spec_from_file" in c for c in calls), calls
