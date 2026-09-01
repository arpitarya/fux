"""`enrich=` on the URL list, and what makes it possible at all.

A `url:` document is enrichable only because `.fux/acquired/` holds its bytes
locally. Before the acquired plane, planning enrichment for a URL meant a
network fetch inside `fux enrich --plan` — an offline, read-only command (L4) —
so the attribute could not exist on that list.
"""

from __future__ import annotations

import pytest

from fux import enrich as enrich_mod
from fux.ingest import sourcelist
from fux.store import acquired

LOC = "https://wiki/runbook"
HTML = "text/html; charset=utf-8"
PAGE = (
    b"<!DOCTYPE html><html><head><title>Deploy runbook</title></head><body>"
    b"<h1>Deploy runbook</h1><p>Roll forward, never back.</p></body></html>"
)


def _repo(tmp_path, line, source_enrich=None):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text(line + "\n")
    extra = f"enrich = {str(source_enrich).lower()}\n" if source_enrich is not None else ""
    (tmp_path / "fux.toml").write_text(
        "[sources.url]\n"
        'fetcher = ".fux/fetchers/http.py"\n'
        "max_parallel = 2\n" + extra
    )
    return tmp_path


def _retain(root, loc=LOC, raw=PAGE, ctype=HTML):
    blob = acquired.save(root, loc, raw, ctype, ".html", run_seq=1)
    acquired.write_manifest(root, {loc: blob})
    return blob


# -- the attribute ----------------------------------------------------------


def test_the_urls_list_now_has_an_enrich_attribute():
    attr = next(a for a in sourcelist.URLS.attributes if a.name == "enrich")
    assert attr.values == ("true", "false")
    assert attr.default == "false"


def test_it_is_off_by_default_like_the_dirs_list():
    dirs = next(a for a in sourcelist.DIRS.attributes if a.name == "enrich")
    urls = next(a for a in sourcelist.URLS.attributes if a.name == "enrich")
    assert dirs.default == urls.default == "false"


def test_a_line_can_declare_it(tmp_path):
    (tmp_path / "urls").write_text("https://x/a enrich=true\n")
    entry = sourcelist.read(tmp_path, "urls", sourcelist.URLS, missing_hint="")[0]
    assert entry.attrs["enrich"] == "true"
    assert "enrich" in entry.declared


# -- the three layers -------------------------------------------------------


def test_an_undeclared_line_with_no_source_setting_is_off(tmp_path):
    root = _repo(tmp_path, "https://x/a")
    assert enrich_mod._enrich_urls(root) == set()


def test_the_source_wide_setting_turns_a_bare_line_on(tmp_path):
    root = _repo(tmp_path, "https://x/a", source_enrich=True)
    assert enrich_mod._enrich_urls(root) == {"https://x/a"}


def test_a_line_beats_the_source_wide_setting_in_both_directions(tmp_path):
    root = _repo(tmp_path, "https://x/a enrich=false", source_enrich=True)
    assert enrich_mod._enrich_urls(root) == set()

    root2 = _repo(tmp_path / "b", "https://x/a enrich=true", source_enrich=False)
    assert enrich_mod._enrich_urls(root2) == {"https://x/a"}


def test_a_repo_with_no_url_source_declares_nothing(tmp_path):
    (tmp_path / "fux.toml").write_text("")
    assert enrich_mod._enrich_urls(tmp_path) == set()


# -- reading the document from the acquired plane ---------------------------


def test_a_url_document_is_read_from_the_acquired_plane(tmp_path):
    _retain(tmp_path)
    text = enrich_mod._document_text(tmp_path, {"src": "url", "loc": LOC})
    assert text is not None and "Roll forward" in text


def test_a_url_document_with_nothing_retained_reads_as_none(tmp_path):
    assert enrich_mod._document_text(tmp_path, {"src": "url", "loc": LOC}) is None


def test_a_url_with_keep_false_reports_zero_chunks_rather_than_crashing(tmp_path):
    # `keep=false` opted this line out, so there is nothing to count. `--plan`
    # names it; it must not raise inside a planning command.
    assert enrich_mod._chunk_count(tmp_path, {"src": "url", "loc": LOC}) == 0


def test_a_retained_url_document_chunks(tmp_path):
    _retain(tmp_path)
    assert enrich_mod._chunk_count(tmp_path, {"src": "url", "loc": LOC}) >= 1


def test_a_corrupt_blob_counts_as_zero_never_raises(tmp_path):
    _retain(tmp_path, raw=b"\x00\x01\x02", ctype="application/pdf")
    assert enrich_mod._chunk_count(tmp_path, {"src": "url", "loc": LOC}) == 0


def test_a_file_document_still_reads_from_disk(tmp_path):
    (tmp_path / "a.md").write_text("# Title\n\nBody text here.\n")
    text = enrich_mod._document_text(tmp_path, {"src": "git", "loc": "a.md"})
    assert text is not None and "Body text" in text


def test_a_missing_file_document_reads_as_none(tmp_path):
    assert enrich_mod._document_text(tmp_path, {"src": "git", "loc": "gone.md"}) is None


# -- the scope --------------------------------------------------------------


def test_urls_get_ONE_synthetic_scope_named_after_their_file():
    # A `dirs` scope is a path prefix a human chose. A URL list has no such
    # structure, so per-host scopes would report coverage against a grouping
    # nobody declared.
    assert enrich_mod.URL_SCOPE == ".fux/sources/urls"
