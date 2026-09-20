"""The one grammar, tested once (SR-URL-LIST decisions 2-13, SR-DIR-LIST 2-3).

`urls` and `dirs` share a parser on purpose, so these tests are written against
the *spec* rather than against either file. A rule that holds here holds for
both lists by construction, which is the whole reason there is one reader.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import sourcelist


def _fill_fetch(text, spec):
    """Supply `fetch=` on any URL line that does not state one.

    🔴 **`fetch=` is REQUIRED on a URL line since 2026-09-20** (W-199 D2;
    SR-URL-LIST decision 16) — there is no default left to inherit. Nearly every
    case in this file is about something else (comments, duplicates, fragments,
    the `dirs` grammar), so the helper fills it in rather than every literal
    repeating it. **A case about `fetch` itself states its own and this leaves
    it alone.**

    ⚠ **Inserted BEFORE a trailing comment**, because `# note` at the end of a
    line would otherwise swallow it and the helper would silently do nothing.
    ⚠ **A `#` inside a URL is a FRAGMENT** — only ` #` (with the space) or a
    line that starts with `#` is a comment, which is the file grammar's own rule.

    ⚠ **The value filled in is `http`, which is the ATTRIBUTE's own `default`.**
    That keeps `_defaults()` comparable: a case asserting *an absent attribute
    is its default* would otherwise fail on the one attribute the helper
    supplied, which is the helper distorting the thing under test.
    """
    if spec is not sourcelist.URLS:
        return text
    out = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            out.append(line)
            continue
        if "fetch=" in stripped or not stripped.lower().startswith(("http://", "https://")):
            out.append(line)
            continue
        head, sep, tail = line.partition(" #")
        out.append(f"{head.rstrip()} fetch=http{(' #' + tail) if sep else ''}")
    return "\n".join(out)


def _parse(text, spec=sourcelist.URLS):
    return sourcelist.parse(_fill_fetch(text, spec), spec, origin="list")


def _values(text, spec=sourcelist.URLS):
    return [e.value for e in _parse(text, spec)]


def _defaults(spec=sourcelist.URLS, **overrides):
    """The RESOLVED attribute map for a line that declared `overrides`.

    ⚠ **Derived from the spec, never spelled out.** Five tests here hard-coded
    `{"fetch": ..., "keep": ...}` and went red the day `keep`, `ttl` and
    `enrich` joined `URLS` (W-100) -- the attributes moved and the tests did
    not. A test written against the *spec* cannot rot that way, which is what
    this module's own docstring claims it does. The set itself is pinned once,
    deliberately, in `test_the_url_attribute_set_is_exactly_these_seven`: an
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
    entries = _parse("https://x.test/p#frag  keep=false  # public page")
    assert entries[0].value == "https://x.test/p#frag"
    assert entries[0].attrs["keep"] == "false"


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

    It has now done its job twice on 2026-09-11: `archived` joined, and then
    `update` did, and each time this was the single failure that named it.

    🔴 **Every default here must be today's behaviour.** The URL list is
    committed, so a default that is not the status quo silently moves every
    existing clone the moment it upgrades.
    """
    assert [a.name for a in sourcelist.URLS.attributes] == [
        "fetch", "keep", "ttl", "enrich", "archived", "update",
    ]
    assert _defaults() == {
        "fetch": "http",
        "keep": "true",      # SR-ACQUIRED: retention is on, the store is bounded
        "ttl": "24h",        # SR-URL-FRESHNESS: not 0; see decision on the default
        "enrich": "false",   # SR-PII: enrichment is always opted into
        "archived": "false", # SR-ARCHIVED-CONTENT: declared, never inferred
        "update": "auto",    # SR-URL-LIST: today's behaviour, byte for byte
    }


def test_update_is_two_words_and_never_a_duration():
    """🔴 W-113's whole boundary, asserted rather than trusted.

    `ttl=` is **ask-time** — how long a citation may go unchecked inside `fux
    answer`. `update=` is **update-time** — whether `fux update` goes out at
    all. The moment `update=` accepts `24h` the two are indistinguishable at a
    glance, and the first person to conflate them will be right to.
    """
    update = next(a for a in sourcelist.URLS.attributes if a.name == "update")
    assert update.values == ("auto", "never")
    assert update.validate is None, (
        "`update` has gained a validator, which is how a closed word set becomes "
        "a typed value. `ttl` is the typed one; this must stay two words"
    )


def test_archived_is_the_same_attribute_on_both_lists():
    """W-126. A retired page behind a URL must be declarable the way a retired
    directory is — same name, same values, same default, one meaning."""
    url_attr = next(a for a in sourcelist.URLS.attributes if a.name == "archived")
    dir_attr = next(a for a in sourcelist.DIRS.attributes if a.name == "archived")
    assert (url_attr.values, url_attr.default) == (dir_attr.values, dir_attr.default)


def test_archived_has_no_source_wide_layer():
    """It is a fact about one DOCUMENT, not a policy about reaching a source.

    `keep`, `ttl` and `enrich` each have a `[sources.url]` middle layer because
    each answers "how do I reach these pages?". `archived` answers "is this page
    retired?", which no source-wide value can say, so `config.UrlSource` must
    never grow the key. `dirs` made the same call.
    """
    from fux.config import UrlSource

    assert not hasattr(UrlSource, "archived")


def test_absent_attributes_take_their_defaults_and_are_not_declared():
    """⚠ **A URL line always declares `fetch` now** (W-199 D2, 2026-09-20).

    The leniency being asserted is about every OTHER attribute: an absent one
    is its default and is not `declared`, so a later reader can tell a stated
    policy from an inherited one. `fetch` left that set because it has no
    source-wide layer to inherit from any more — the line states it or fails to
    parse — so `declared` can never be empty on a URL line again.
    """
    (entry,) = _parse("https://x.test/a")
    assert entry.attrs == _defaults()
    assert entry.declared == frozenset({"fetch"})
    assert not entry.is_complete()

    # The `dirs` grammar has no required attribute, so the empty case lives here.
    (dir_entry,) = _parse("docs", sourcelist.DIRS)
    assert dir_entry.declared == frozenset()


def test_a_line_stating_every_attribute_is_complete():
    stated = " ".join(f"{a.name}={a.default}" for a in sourcelist.URLS.attributes)
    (entry,) = _parse(f"https://x.test/a {stated}")
    assert entry.declared == {a.name for a in sourcelist.URLS.attributes}
    assert entry.is_complete()

    # ... and one short of the set is not, whichever one is missing.
    (partial,) = _parse("https://x.test/a fetch=cdp keep=false")
    assert partial.declared == {"fetch", "keep"}
    assert not partial.is_complete()


def test_attribute_order_on_a_line_does_not_matter():
    one = _parse("https://x.test/a fetch=cdp keep=false")[0]
    two = _parse("https://x.test/a keep=false fetch=cdp")[0]
    assert one.attrs == two.attrs


def test_an_unknown_key_is_a_loud_error_naming_file_and_line():
    with pytest.raises(FuxError, match=r"list:2: unknown attribute 'mata'"):
        _parse("https://x.test/a\nhttps://x.test/b mata=plain")


def test_an_unknown_value_is_a_loud_error_naming_file_and_line():
    """⚠ **This asserted on `fetch=` until W-178 made it typed** (2026-09-15).

    `fetch=playwright` is a **legal line** now — it names
    `.fux/fetchers/playwright.py`, which is the consumer's to write. ⚠ **`meta`
    carried this assertion from 2026-09-15 until W-194 deleted it** on
    2026-09-20; `keep` is the closed two-valued enum it moves to, so the
    *file:line* half of the contract stays asserted rather than deleted with
    the attribute.
    """
    with pytest.raises(FuxError, match=r"list:1: keep='raw' is not one of true, false"):
        _parse("https://x.test/a keep=raw")


def test_a_fetcher_name_nobody_shipped_parses(tmp_path):
    """🔴 **The whole of W-178, in one line of config.**

    A consumer drops `.fux/fetchers/glassbox.py` in and writes `fetch=glassbox`.
    The grammar validated **shape only** from that day; whether the file exists
    is `fux doctor`'s (`fetcher bindings`) and `urlsrc._fetcher_path`'s.
    """
    (entry,) = _parse("https://x.test/a fetch=glassbox")
    assert entry.attrs["fetch"] == "glassbox"


@pytest.mark.parametrize("bad", ["Glassbox", "cdp.py", "../evil", "_shared", ""])
def test_a_fetcher_name_that_is_not_a_module_stem_is_refused(bad):
    """Open VALUES, not open syntax — and the four refusals are the reason.

    A capitalised name, a `.py` suffix and a directory part would each resolve
    to a path that is not what the writer meant; `_shared` is the leading
    underscore that marks a helper the decoder registry skips, kept out here so
    the two consumer planes spell a name the same way.
    """
    with pytest.raises(FuxError, match="fetcher module name"):
        _parse(f"https://x.test/a fetch={bad}")


def test_a_bare_flag_is_not_the_grammar():
    with pytest.raises(FuxError, match=r"list:1: 'plain' is not `key=value`"):
        _parse("https://x.test/a plain")


def test_a_repeated_key_on_one_line_is_an_error():
    with pytest.raises(FuxError, match=r"list:1: attribute 'keep' is given twice"):
        _parse("https://x.test/a keep=true keep=false")


def test_a_duplicate_with_conflicting_attributes_names_both_lines():
    with pytest.raises(FuxError, match=r"list:1 and list:2"):
        _parse("https://x.test/a keep=true\nhttps://x.test/a keep=false")


def test_a_duplicate_is_compared_on_resolved_attributes_not_on_the_text():
    """The reader is lenient: an absent attribute *is* its default."""
    (entry,) = _parse("https://x.test/a\nhttps://x.test/a keep=true")
    assert entry.attrs == _defaults()
    # ⚠ `fetch` rides along on both lines now — the helper supplies it, and the
    # grammar requires it. What this case is about is `keep`: the more explicit
    # of the two duplicate lines survives.
    assert entry.declared == {"keep", "fetch"}


# -- the per-file halves ---------------------------------------------------


def test_urls_rejects_a_non_http_scheme_at_its_line_number():
    with pytest.raises(FuxError, match=r"list:3: not an http\(s\) URL"):
        _parse("https://x.test/a\n# note\nftp://x.test/c")


def test_dirs_has_its_own_closed_attribute_set():
    (entry,) = _parse("archive/v0.26-docs archived=true", sourcelist.DIRS)
    # The set is CLOSED and now holds two: `archived` (SR-DIR-LIST) and
    # `enrich` (SR-ENRICH, W-76 Phase 8). `attrs` is *resolved* — every
    # attribute in the spec is present with its default — so this grows
    # whenever the closed set does, which is the point of asserting it.
    assert entry.attrs == {"archived": "true", "enrich": "false"}
    with pytest.raises(FuxError, match=r"unknown attribute 'ttl'"):
        _parse("docs ttl=7d", sourcelist.DIRS)


def test_dirs_rejects_an_absolute_path_or_an_escape():
    with pytest.raises(FuxError, match="not a repo-relative path"):
        _parse("/etc", sourcelist.DIRS)
    with pytest.raises(FuxError, match="escapes the repo root"):
        _parse("../elsewhere", sourcelist.DIRS)


def test_urls_attributes_are_not_legal_in_dirs():
    """⚠ **This test lost its "and vice versa" half on 2026-09-11** (W-126).

    It used `archived` as the example of a `dirs`-only attribute, and `urls`
    now carries it. **No attribute is `dirs`-only any more** — `DIRS`' set
    (`archived`, `enrich`) is a subset of `URLS`' — so the reverse direction has
    nothing left to assert and asserting it on a substitute would be a test
    written to stay green. The direction that still carries real information is
    the one below, and `test_archived_is_the_same_attribute_on_both_lists`
    covers the overlap deliberately rather than by omission.
    """
    with pytest.raises(FuxError, match=r"unknown attribute 'fetch'"):
        _parse("docs fetch=cdp", sourcelist.DIRS)
    assert {a.name for a in sourcelist.DIRS.attributes} < {
        a.name for a in sourcelist.URLS.attributes
    }


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


def test_a_custom_fetcher_name_round_trips(tmp_path):
    """W-178: the writer must survive a value fux does not ship.

    A typed attribute is where a writer most easily stops round-tripping —
    `render_line` states every attribute, and a validator the writer's own
    output fails would make `fux add` produce a file `fux ingest` refuses.
    """
    line = sourcelist.render_line("https://x.test/a", {"fetch": "glassbox"}, sourcelist.URLS)
    assert "fetch=glassbox" in line
    (entry,) = _parse(line)
    assert entry.attrs == _defaults(fetch="glassbox")
    assert entry.is_complete()


def test_fetch_is_still_stated_at_its_default():
    """🔴 **The reason `fetch`'s default is `"http"` and not `""`** (W-178 15b).

    `render_line` omits an attribute whose default is EMPTY — the exception
    `types.decoder` needed, because a bare `decoder=` states no policy. A typed
    `fetch` with an empty default would inherit that exception silently and
    every generated URL line would stop stating `fetch=`, which SR-URL-LIST
    decision 12 forbids. Nothing in the grammar would have complained.
    """
    line = sourcelist.render_line("https://x.test/a", {}, sourcelist.URLS)
    assert "fetch=http" in line
