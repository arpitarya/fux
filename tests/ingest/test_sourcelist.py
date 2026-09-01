"""The one grammar, tested once (ADR-URL-LIST decisions 2-13, ADR-DIR-LIST 2-3).

`urls` and `dirs` share a parser on purpose, so these tests are written against
the *spec* rather than against either file. A rule that holds here holds for
both lists by construction, which is the whole reason there is one reader.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import sourcelist


def _parse(text, spec=sourcelist.URLS):
    return sourcelist.parse(text, spec, origin="list")


def _values(text, spec=sourcelist.URLS):
    return [e.value for e in _parse(text, spec)]


def _defaults(spec=sourcelist.URLS, **overrides):
    """The RESOLVED attribute map for a line that declared `overrides`.

    ⚠ **Derived from the spec, never spelled out.** Five tests here hard-coded
    `{"fetch": ..., "meta": ...}` and went red the day `keep`, `ttl` and
    `enrich` joined `URLS` (W-100) -- the attributes moved and the tests did
    not. A test written against the *spec* cannot rot that way, which is what
    this module's own docstring claims it does. The set itself is pinned once,
    deliberately, in `test_the_url_attribute_set_is_exactly_these_six`: an
    attribute appearing without anybody noticing is the failure this file
    still has to catch.
    """
    resolved = {a.name: a.default for a in spec.attributes}
    resolved.update(overrides)
    return resolved


# -- comments, blanks, ordering -------------------------------------------


def test_blank_lines_and_whole_line_comments_are_ignored():
    text = "\n".join(["# heading", "", "   ", "https://x.test/a", "   # indented note"])
    assert _values(text) == ["https://x.test/a"]


def test_hash_after_whitespace_starts_a_comment():
    assert _values("https://x.test/a  # why this URL is here") == ["https://x.test/a"]


def test_hash_inside_an_entry_is_not_a_comment():
    """W-49. A fragment is part of the entry; stripping it dropped a document."""
    assert _values("https://x.test/page#section") == ["https://x.test/page#section"]


def test_a_fragment_and_a_trailing_comment_coexist():
    entries = _parse("https://x.test/p#frag  meta=plain  # public page")
    assert entries[0].value == "https://x.test/p#frag"
    assert entries[0].attrs["meta"] == "plain"


def test_the_loader_dedupes_and_sorts_so_file_order_is_presentation_only():
    a = _values("\n".join(["https://x.test/c", "https://x.test/a", "https://x.test/c"]))
    b = _values("\n".join(["https://x.test/a", "https://x.test/c"]))
    assert a == b == ["https://x.test/a", "https://x.test/c"]


# -- attributes ------------------------------------------------------------


def test_the_url_attribute_set_is_exactly_these_six():
    """The one place the URL attribute set is written out, on purpose.

    Every other test here derives from the spec so it survives a new
    attribute. This one does not, so a new attribute is *visible* -- it lands
    as one failing assertion naming what appeared, rather than as five
    unrelated ones (W-100) or as nothing at all.
    """
    assert [a.name for a in sourcelist.URLS.attributes] == [
        "fetch", "meta", "keep", "ttl", "enrich",
    ]
    assert _defaults() == {
        "fetch": "http",
        "meta": "hashed",
        "keep": "true",      # ADR-ACQUIRED: retention is on, the store is bounded
        "ttl": "24h",        # ADR-URL-FRESHNESS: not 0; see decision on the default
        "enrich": "false",   # ADR-PII: enrichment is always opted into
    }


def test_absent_attributes_take_their_defaults_and_are_not_declared():
    (entry,) = _parse("https://x.test/a")
    assert entry.attrs == _defaults()
    assert entry.declared == frozenset()
    assert not entry.is_complete()


def test_a_line_stating_every_attribute_is_complete():
    stated = " ".join(f"{a.name}={a.default}" for a in sourcelist.URLS.attributes)
    (entry,) = _parse(f"https://x.test/a {stated}")
    assert entry.declared == {a.name for a in sourcelist.URLS.attributes}
    assert entry.is_complete()

    # ... and one short of the set is not, whichever one is missing.
    (partial,) = _parse("https://x.test/a fetch=cdp meta=plain")
    assert partial.declared == {"fetch", "meta"}
    assert not partial.is_complete()


def test_attribute_order_on_a_line_does_not_matter():
    one = _parse("https://x.test/a fetch=cdp meta=plain")[0]
    two = _parse("https://x.test/a meta=plain fetch=cdp")[0]
    assert one.attrs == two.attrs


def test_an_unknown_key_is_a_loud_error_naming_file_and_line():
    with pytest.raises(FuxError, match=r"list:2: unknown attribute 'mata'"):
        _parse("https://x.test/a\nhttps://x.test/b mata=plain")


def test_an_unknown_value_is_a_loud_error_naming_file_and_line():
    with pytest.raises(FuxError, match=r"list:1: fetch='playwright' is not one of http, cdp"):
        _parse("https://x.test/a fetch=playwright")


def test_a_bare_flag_is_not_the_grammar():
    with pytest.raises(FuxError, match=r"list:1: 'plain' is not `key=value`"):
        _parse("https://x.test/a plain")


def test_a_repeated_key_on_one_line_is_an_error():
    with pytest.raises(FuxError, match=r"list:1: attribute 'meta' is given twice"):
        _parse("https://x.test/a meta=plain meta=hashed")


def test_a_duplicate_with_conflicting_attributes_names_both_lines():
    with pytest.raises(FuxError, match=r"list:1 and list:2"):
        _parse("https://x.test/a meta=plain\nhttps://x.test/a meta=hashed")


def test_a_duplicate_is_compared_on_resolved_attributes_not_on_the_text():
    """The reader is lenient: an absent attribute *is* its default."""
    (entry,) = _parse("https://x.test/a\nhttps://x.test/a meta=hashed")
    assert entry.attrs == _defaults()
    assert entry.declared == {"meta"}  # the more explicit of the two survives


# -- the per-file halves ---------------------------------------------------


def test_urls_rejects_a_non_http_scheme_at_its_line_number():
    with pytest.raises(FuxError, match=r"list:3: not an http\(s\) URL"):
        _parse("https://x.test/a\n# note\nftp://x.test/c")


def test_dirs_has_its_own_closed_attribute_set():
    (entry,) = _parse("archive/v0.26-docs archived=true", sourcelist.DIRS)
    # The set is CLOSED and now holds two: `archived` (ADR-DIR-LIST) and
    # `enrich` (ADR-ENRICH, W-76 Phase 8). `attrs` is *resolved* — every
    # attribute in the spec is present with its default — so this grows
    # whenever the closed set does, which is the point of asserting it.
    assert entry.attrs == {"archived": "true", "enrich": "false"}
    with pytest.raises(FuxError, match=r"unknown attribute 'meta'"):
        _parse("docs meta=plain", sourcelist.DIRS)


def test_dirs_rejects_an_absolute_path_or_an_escape():
    with pytest.raises(FuxError, match="not a repo-relative path"):
        _parse("/etc", sourcelist.DIRS)
    with pytest.raises(FuxError, match="escapes the repo root"):
        _parse("../elsewhere", sourcelist.DIRS)


def test_urls_attributes_are_not_legal_in_dirs_and_vice_versa():
    with pytest.raises(FuxError, match=r"unknown attribute 'archived'"):
        _parse("https://x.test/a archived=true", sourcelist.URLS)


# -- the writer ------------------------------------------------------------


def test_a_rendered_line_states_every_attribute_even_at_its_default():
    line = sourcelist.render_line("https://x.test/a", {}, sourcelist.URLS)
    stated = " ".join(f"{a.name}={a.default}" for a in sourcelist.URLS.attributes)
    assert line == f"https://x.test/a {stated}"


def test_a_rendered_line_round_trips_and_is_complete():
    line = sourcelist.render_line("https://x.test/a", {"fetch": "cdp"}, sourcelist.URLS)
    (entry,) = _parse(line)
    assert entry.value == "https://x.test/a"
    assert entry.attrs == _defaults(fetch="cdp")
    assert entry.is_complete()
