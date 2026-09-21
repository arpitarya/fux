"""The `decoder=` half of the pipe — the LINE decides which decoder reads a URL.

**Arpit, 2026-09-18** (built 2026-09-21 as W-199 DoD 10): *"Whenever we add a
URL, after that, we have to define what kind of fetch it is, what kind of
decoder we want to use. And that is the one that gets saved in the URLs file."*

A **file**'s extension picks its decoder. A **URL** has no trustworthy
extension — `?download=1`, `/export`, an `application/octet-stream` — so fux
guessed from the `Content-Type`, then the URL, then fell back to prose, **on
every ingest**. Which decoder read a document was therefore a function of what
the server said that morning, which is a heuristic in the maintenance path
(L3). The line replaces the guess with a declaration.

The edge cases numbered below are
[`work/proposals/fetcher-routing.md`](../../work/proposals/fetcher-routing.md)
§3's.
"""

from __future__ import annotations

import pytest

from fux import decode as decode_mod
from fux.errors import FuxError
from fux.ingest import sourcelist, urlsrc


def _parse(text):
    return sourcelist.parse(text, sourcelist.URLS, origin="urls")


# --- the grammar -----------------------------------------------------------


def test_a_line_without_a_decoder_fails_to_load():
    """The break, by ruling: *"Nothing needs to be done. It is a breaking change."*"""
    with pytest.raises(FuxError) as excinfo:
        _parse("https://x.test/a fetch=http")
    message = str(excinfo.value)
    assert "does not state `decoder=`" in message
    assert "urls:1" in message, "the error names the line"
    assert ".fux/decoders/" in message, "and the fix"


def test_the_absence_error_names_the_DECODER_directory_not_the_fetcher_one():
    """🔴 Why `Attribute.required_hint` exists at all.

    `parse` raised **one** message, written for `fetch=`, naming
    `.fux/fetchers/` and SR-URL-LIST decision 16. A second required attribute
    would have been reported by pointing the reader at the wrong directory —
    the W-140 row 18 shape, a message transcribed where the fact lives one
    layer away.
    """
    with pytest.raises(FuxError) as fetch_missing:
        _parse("https://x.test/a decoder=prose")
    with pytest.raises(FuxError) as decoder_missing:
        _parse("https://x.test/a fetch=http")
    assert ".fux/fetchers/" in str(fetch_missing.value)
    assert ".fux/fetchers/" not in str(decoder_missing.value)
    assert ".fux/decoders/" in str(decoder_missing.value)


def test_an_empty_decoder_is_refused_on_a_url_line():
    """⚠ **The one difference from the `types` grammar, and it is deliberate.**

    On `types` an empty `decoder=` means *no declared binding* and the file's
    extension resolves it. A URL has no extension to resolve through, so
    *"resolve it later"* is the one answer this attribute may not carry.
    """
    with pytest.raises(FuxError, match="may not leave its decoder to be resolved later"):
        _parse("https://x.test/a fetch=http decoder=")


def test_the_same_empty_value_is_still_legal_on_the_types_grammar():
    """The control. One attribute name, two grammars, two rules."""
    (entry,) = sourcelist.parse("*.md decoder=", sourcelist.TYPES, origin="types")
    assert entry.attrs["decoder"] == ""


def test_a_generated_line_states_it_and_round_trips(tmp_path):
    """Edge case 12. `render_line` states every attribute; it must read back."""
    line = sourcelist.render_line(
        "https://x.test/a", sourcelist.URLS.defaults() | {"decoder": "xlsx"}, sourcelist.URLS
    )
    assert " decoder=xlsx " in line
    (entry,) = _parse(line)
    assert entry.attrs["decoder"] == "xlsx"
    assert entry.is_complete()


def test_a_pinned_line_survives_an_update_never_line():
    """Edge case 11. The grammar is uniform: nothing is fetched, the attribute is there."""
    (entry,) = _parse("https://x.test/a fetch=http decoder=pdf update=never")
    assert entry.attrs["decoder"] == "pdf"


def test_two_lines_for_one_url_with_different_decoders_is_a_hard_error():
    """Edge case 13 — and it comes free from the dedupe rule, which is the point.

    Two lines resolving to different decoders would ingest **different bytes for
    one document id**, and letting a merge artefact pick which is exactly what
    SR-URL-LIST decision 10 refuses.
    """
    with pytest.raises(FuxError, match="appears twice with conflicting attributes"):
        _parse(
            "https://x.test/a fetch=http decoder=html\n"
            "https://x.test/a fetch=http decoder=prose\n"
        )


def test_the_shape_is_checked_and_existence_is_not():
    """The same split `fetch=` makes, for the same reason: the parser cannot
    reach the registry, and reaching for it would make reading a committed file
    depend on importing every decoder."""
    with pytest.raises(FuxError, match="must be a decoder module name"):
        _parse("https://x.test/a fetch=http decoder=xlsx.py")
    # A name nobody shipped PARSES — that is edge case 2, and `fux doctor`'s
    # `url decoders` row is what reports it.
    (entry,) = _parse("https://x.test/a fetch=http decoder=xlxs")
    assert entry.attrs["decoder"] == "xlxs"


def test_the_line_is_the_only_layer():
    """⚠ **No `[sources.url] decoder`, by decision.** `keep`/`ttl`/`enrich`/
    `update` have a source-wide middle layer because each is a policy about
    REACHING a source; a decoder is a fact about one document's format."""
    entries = _parse("https://x.test/a fetch=http decoder=csv")
    (resolved,) = urlsrc.resolve_urls(entries, object())
    assert resolved.decoder == "csv"


# --- the resolution at ingest ---------------------------------------------


def test_the_declared_stem_decides_and_the_header_is_not_consulted():
    """Edge case 5: *the header loses, silently.* The line is the human's word."""
    html = b"<html><body><h1>T</h1><p>Body text here.</p></body></html>"
    as_html, why = urlsrc._decode_fetched(html, "html", "https://x.test/p")
    assert why == "" and as_html and "<h1>" not in as_html

    # Same bytes, same (imaginary) response, a different line.
    as_prose, why = urlsrc._decode_fetched(html, "prose", "https://x.test/p")
    assert why == "" and as_prose == html.decode("utf-8")
    assert as_html != as_prose, "the line changes what is indexed, which is the point"


def test_prose_reaches_no_module_at_all():
    assert decode_mod.decoder_named("prose") is None
    text, why = urlsrc._decode_fetched(b"# Heading\n", "prose", "https://x.test/p")
    assert why == "" and text == "# Heading\n"


def test_a_consumer_module_named_prose_is_refused_at_registry_build(tmp_path):
    """Edge case 1. It would be loaded, registered, and never called."""
    decoders = tmp_path / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    (decoders / "prose.py").write_text(
        "EXTENSIONS = ('.prose',)\ndef decode(raw, rel_path):\n    return 'x'\n",
        encoding="utf-8",
    )
    with pytest.raises(FuxError, match="reserved name 'prose'"):
        decode_mod.registry(tmp_path)


def test_the_pseudo_path_keeps_the_urls_own_suffix_when_the_decoder_claims_it():
    """🔴 Two built-ins branch on the extension, and choosing by NAME loses it
    unless the URL is consulted: `csv` reads a `.tsv` tab-separated and `mail`
    reads a `.mbox` as a mailbox."""
    csv = decode_mod.decoder_named("csv")
    assert urlsrc.decoder_rel_path(csv, "https://x.test/export.tsv") == "fetched.tsv"
    assert urlsrc.decoder_rel_path(csv, "https://x.test/api/export?f=1") == "fetched.csv"


def test_the_fallback_suffix_is_the_modules_own_first_extension_not_the_sorted_one():
    """⚠ `Decoder.extensions` is sorted, which makes `.xlsm` first for `xlsx`.

    Sorting is right for loading — two machines must agree — and answers a
    different question from *what is this format called*. `primary` is the
    author's own first extension, and it is what names the retained blob.
    """
    # The two where sorting and authorship disagree — the reason `primary` exists.
    for stem, sorted_first, primary in (
        ("xlsx", ".xlsm", ".xlsx"), ("docx", ".docm", ".docx"), ("html", ".htm", ".html"),
    ):
        module = decode_mod.decoder_named(stem)
        assert module.extensions[0] == sorted_first
        assert module.primary == primary
        assert urlsrc.decoder_rel_path(module, "https://x.test/d") == "fetched" + primary


def test_a_stem_naming_nothing_is_a_recorded_skip_not_a_crash():
    """Edge case 2, at ingest. The `_bind` message shape, naming both halves."""
    out, why = urlsrc._decode_fetched(b"payload", "xlxs", "https://x.test/a")
    assert out is None
    assert "no decoder module named 'xlxs'" in why
    assert "built-ins are" in why and "Fix the `decoder=`" in why


def test_the_two_skip_reasons_stay_distinguishable():
    """What 2026-08-27 bought and this ruling must not spend.

    *No decoder module named X* (somebody could write one, or fix the line) is
    not *X ran and found nothing readable* (only a model will help). Conflating
    them makes the enrichment queue useless.
    """
    missing = urlsrc._decode_fetched(b"x", "nosuch", "https://x.test/a")[1]
    empty = urlsrc._decode_fetched(b'{"a": 1}', "json", "https://x.test/a")[1]
    assert "no decoder module named" in missing
    assert "nothing readable" in empty and "no decoder" not in empty


# --- what `fux add` proposes (the resolution that LEFT the ingest path) ----


@pytest.mark.parametrize(
    "content_type, url, expected",
    [
        ("text/html; charset=utf-8", "https://x.test/p", "html"),
        ("text/markdown", "https://x.test/p", "prose"),
        ("text/plain", "https://x.test/p", "prose"),
        ("application/pdf", "https://x.test/p", "pdf"),
        ("application/json", "https://x.test/p", "json"),
        ("text/csv", "https://x.test/p", "csv"),
        (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "https://x.test/p", "xlsx",
        ),
        # No recognised type: the URL's own extension is the second layer.
        ("application/octet-stream", "https://x.test/report.xlsx", "xlsx"),
        # Neither: an unknown BINARY type maps to nothing and `fux add` refuses.
        ("image/webp", "https://x.test/y.webp", None),
    ],
)
def test_propose_decoder_is_the_old_ingest_resolution_moved(content_type, url, expected):
    """🔴 **Deliberately the same ladder, executed once.**

    The stem written onto a line must be the decoder the old ingest path would
    have chosen for the same response, or every existing corpus changes its
    bytes on the day somebody re-adds a URL.
    """
    assert urlsrc.propose_decoder(content_type, url, None) == expected


def test_nothing_maps_is_None_and_never_a_guess():
    assert urlsrc.propose_decoder("application/x-nonesuch", "https://x.test/d", None) is None


# --- the retained blob's name --------------------------------------------


def test_a_blob_is_named_by_the_declared_decoder():
    """SR-ACQUIRED: *the plane names files by what they are.*

    It was `_EXT_FOR[mime]`, which named a workbook served as
    `application/octet-stream` with no extension at all — a blob you can read
    and not double-click, in the case where knowing the format matters most.
    """
    assert urlsrc.acquired_ext("xlsx", None) == ".xlsx"
    assert urlsrc.acquired_ext("pdf", None) == ".pdf"


def test_prose_and_an_unresolvable_stem_stay_extensionless():
    """Prose is text of an unknown flavour — `.md`? `.txt`? — and inventing one
    would be the guess this ruling removed, one layer down."""
    assert urlsrc.acquired_ext("prose", None) == ""
    assert urlsrc.acquired_ext("nosuch", None) == ""


# --- the whole way through, into the committed index ----------------------


def test_the_line_decides_what_lands_in_the_index(tmp_path):
    """🔴 **The end-to-end claim, and the only one that can fail quietly.**

    Two repos, identical sources and an identical response, differing in one
    word on one line — and the committed records differ. That is the ruling
    working; it is also why the attribute is `required` rather than defaulted,
    because a wrong default here is a plausible index rather than an error.
    """
    from fux import store
    from fux.ingest.run import run

    body = '{"note": "the paging rotation hands over on Monday"}'
    written = {}
    for stem in ("json", "prose"):
        root = tmp_path / stem
        (root / ".fux" / "sources").mkdir(parents=True)
        (root / ".fux" / "fetchers").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
        (root / "fux.toml").write_text(
            "[sources]\n[sources.url]\nmax_parallel = 2\n", encoding="utf-8"
        )
        (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
        (root / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
        (root / ".fux" / "sources" / "urls").write_text(
            f"https://x.test/export fetch=probe decoder={stem}\n", encoding="utf-8"
        )
        # ⚠ The server calls it HTML on BOTH runs. The header decides nothing.
        (root / ".fux" / "fetchers" / "probe.py").write_text(
            f'def fetch(url):\n    return ({body!r}.encode(), "text/html")\n',
            encoding="utf-8",
        )
        run(root, refresh_urls=True)
        written[stem] = store.read_index(root)["url:https://x.test/export"]

    assert written["json"]["sha"] != written["prose"]["sha"], (
        "one word on one line must change the committed record, or the "
        "declaration is decorative"
    )
    # Same document id, same address, different bytes — which is the shape of
    # the claim: the line decides what ONE document's record holds.
    assert written["prose"]["loc"] == written["json"]["loc"] == "https://x.test/export"
