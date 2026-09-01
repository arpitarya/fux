"""Phase 4 wiring — `refer` falls back to `.fux/acquired/` instead of shrugging.

No network. The fetcher is injected, which is how the whole refer suite avoids
opening a socket.
"""

from __future__ import annotations

import json

import pytest

from fux.errors import FuxError
from fux.refer import source as source_mod
from fux.store import acquired

DOC = "url:https://x/share/TOKEN"
LOC = "https://x/share/TOKEN"
HTML = "text/html; charset=utf-8"
PAGE = (
    b"<!DOCTYPE html><html><head><title>Deploy runbook</title></head><body>"
    b"<h1>Deploy runbook</h1><p>Roll forward, never back.</p></body></html>"
)


def _retain(root, raw=PAGE, ctype=HTML, loc=LOC):
    blob = acquired.save(root, loc, raw, ctype, ".html", run_seq=1)
    acquired.write_manifest(root, {loc: blob})
    return blob


# -- reading a retained document --------------------------------------------


def test_nothing_retained_is_none(tmp_path):
    assert source_mod.from_acquired(tmp_path, DOC, LOC) is None


def test_a_retained_document_reads_back(tmp_path):
    _retain(tmp_path)
    got = source_mod.from_acquired(tmp_path, DOC, LOC)
    assert got is not None
    assert got.strategy == source_mod.URL
    assert b"Roll forward" in got.content


def test_the_sha_matches_what_ingest_would_have_recorded(tmp_path):
    """THE property the whole fallback rests on.

    A verify-time sha is compared against an ingest-time sha. If the two
    pipelines diverge by one line, every retained document is marked stale
    forever -- a defect that presents as a working feature. This asserts the
    blob path produces the identical sha to the fetch path for identical bytes.
    """
    from fux.ingest.urlsrc import _decode_fetched, sanitize
    from fux import store as store_mod

    _retain(tmp_path)
    markdown, _ = _decode_fetched(PAGE, HTML, LOC, tmp_path)
    expected = store_mod.content_sha(sanitize(markdown))
    assert source_mod.from_acquired(tmp_path, DOC, LOC).sha == expected


def test_a_deleted_blob_reads_as_nothing_not_as_a_verdict(tmp_path):
    blob = _retain(tmp_path)
    acquired.blob_path(tmp_path, blob.sha, ".html").unlink()
    # "We have nothing to compare" is `unverified`, and must not be dressed up
    # as a comparison that happened.
    assert source_mod.from_acquired(tmp_path, DOC, LOC) is None


def test_a_corrupt_blob_costs_a_verdict_never_the_query(tmp_path):
    blob = _retain(tmp_path, raw=b"\x00\x01\x02 not html", ctype="application/pdf")
    assert source_mod.from_acquired(tmp_path, DOC, LOC) is None


def test_a_file_document_is_never_served_from_the_plane(tmp_path):
    # `file:` is already on disk; a second copy would be nonsense, and the
    # plane is `url:`-only by decision.
    _retain(tmp_path, loc="docs/a.md")
    assert source_mod.from_acquired(tmp_path, "file:docs/a.md", "docs/a.md") is None


# -- the verdict it produces ------------------------------------------------


def test_matching_retained_bytes_are_as_ingested_not_current(tmp_path):
    from fux.refer import freshness

    _retain(tmp_path)
    got = source_mod.from_acquired(tmp_path, DOC, LOC)
    v = freshness.as_ingested(got.sha, got.sha)
    assert v.label == "as-ingested"
    assert v.label != "current"       # we did not look at the world
    assert v.label != "unverified"    # but we did compare something real
    assert v.current is True


def test_the_output_schema_carries_the_sixth_verdict():
    from fux import schema as schema_mod
    import importlib.resources as resources

    raw = json.loads(
        (resources.files("fux.query") / "output.schema.json").read_text(encoding="utf-8")
    )
    text = json.dumps(raw)
    assert "as-ingested" in text
    # And the prose must not still claim four.
    assert "four-state" not in text
