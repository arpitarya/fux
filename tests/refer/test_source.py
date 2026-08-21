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


def test_a_fetcher_returning_the_wrong_type_is_refused(tmp_path):
    with pytest.raises(FuxError, match="expected str"):
        fetch_document(tmp_path, "url:https://x.test/p", "https://x.test/p", fetcher=lambda u: b"bytes")


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
