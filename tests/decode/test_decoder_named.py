"""`decode.decoder_named` — reaching a decoder BY NAME, not by extension.

SR-DECODE decision 21, built for the pipe ruling: a URL line declares
`decoder=<stem>` because a URL has no trustworthy extension, so the plane needs
a lookup that answers the question the line asks.

🔴 **It is `registry()`'s first two steps and deliberately NOT its third.** A
consumer module of that name replaces the built-in wholesale; the `[decoders]`
binding table — which maps an **extension** to a module — is not consulted at
all. Letting it re-route a declared line would undo the point of declaring one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux import decode
from fux.errors import FuxError
from fux.ingest import sourcelist
from fux.ingest import ingestlog


def _consumer(root, stem, body):
    d = root / ".fux" / "decoders"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{stem}.py").write_text(body, encoding="utf-8")


def test_a_built_in_resolves_by_its_module_name():
    assert decode.decoder_named("xlsx").name == "xlsx"
    assert decode.decoder_named("html").name == "html"


def test_an_unknown_name_is_None_and_never_a_guess():
    assert decode.decoder_named("xlxs") is None
    assert decode.decoder_named("") is None


def test_prose_resolves_to_None_because_it_names_a_BRANCH():
    """⚠ **The caller must check for it first.** *No module* and *no decoder
    runs* are the same answer here and opposite outcomes upstream."""
    assert decode.decoder_named(decode.PROSE_DECODER) is None


def test_the_reserved_word_is_spelled_the_same_in_all_three_places():
    """It appears in the decoder plane, the grammar and the ledger.

    Three implementations of one word rather than three restatements (L0's own
    test): a mismatch fails the parse or the registry build immediately, it
    cannot sit there looking correct. Held equal anyway, because the cost is one
    assertion.
    """
    assert decode.PROSE_DECODER == sourcelist.PROSE_DECODER == ingestlog.PROSE == "prose"


def test_a_consumer_module_replaces_a_built_in_of_the_same_name(tmp_path):
    _consumer(
        tmp_path, "html",
        "EXTENSIONS = ('.html',)\ndef decode(raw, rel_path):\n    return 'consumer html'\n",
    )
    module = decode.decoder_named("html", tmp_path)
    # `origin` is an OS path, so compare its COMPONENTS — a literal
    # "decoders/html.py" is a substring on posix and never on Windows, where
    # the separator is a backslash. This assertion was green on two platforms
    # and red on the third for exactly that reason.
    assert module is not None and Path(module.origin).parts[-2:] == ("decoders", "html.py")
    assert decode.decode_with(module, b"<p>x</p>", "fetched.html", tmp_path) == "consumer html"


def test_a_consumer_module_with_no_built_in_twin_resolves(tmp_path):
    _consumer(
        tmp_path, "vndthing",
        "EXTENSIONS = ('.vndthing',)\ndef decode(raw, rel_path):\n    return 'ran'\n",
    )
    assert decode.decoder_named("vndthing", tmp_path).name == "vndthing"
    assert decode.decoder_named("vndthing", None) is None, "root is what makes it reachable"


def test_a_decoders_binding_table_never_re_routes_a_NAME(tmp_path):
    """🔴 The precedence that makes a declared line worth declaring.

    `[decoders]` says *this repo has agreed `json` reads `.geojson`*. It does
    **not** say *`decoder=json` means something else now* — the line is the most
    specific thing there is.
    """
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".fux" / "formats.toml").write_text(
        'include = ["*.md"]\n\n[decoders]\ngeojson = "json"\n', encoding="utf-8"
    )
    # ⚠ `.geojson` is claimed by NOTHING, which is the binding shape `_bind`
    # accepts — taking an extension from the decoder that claims it is refused,
    # and that refusal is `test_binding.py`'s.
    _consumer(
        tmp_path, "vndthing",
        "EXTENSIONS = ('.vndthing',)\ndef decode(raw, rel_path):\n    return 'consumer'\n",
    )
    # The binding wins for the EXTENSION...
    assert decode.registry(tmp_path)[".geojson"].name == "json"
    # ...and changes nothing about either NAME.
    assert decode.decoder_named("json", tmp_path).name == "json"
    assert decode.decoder_named("vndthing", tmp_path).name == "vndthing"


def test_a_shared_helper_is_not_a_decoder(tmp_path):
    """`_`-prefixed files are a consumer's own imports, and the loader skips them."""
    _consumer(
        tmp_path, "_shared",
        "EXTENSIONS = ('.x',)\ndef decode(raw, rel_path):\n    return 'x'\n",
    )
    assert decode.decoder_named("_shared", tmp_path) is None


def test_a_consumer_file_named_prose_is_refused(tmp_path):
    _consumer(
        tmp_path, "prose",
        "EXTENSIONS = ('.prose',)\ndef decode(raw, rel_path):\n    return 'x'\n",
    )
    with pytest.raises(FuxError) as excinfo:
        decode.decoder_named("html", tmp_path)
    message = str(excinfo.value)
    assert "reserved name 'prose'" in message
    assert "would never be called" in message, "the error says WHY, not just that"


def test_decode_with_keeps_decodes_loud_failure_split(tmp_path):
    """SR-DECODE decision 7's split must not be reimplemented twice.

    A malformed document is `DecodeFailed` — data, caught by the walker, never
    fatal. A `FuxError` from inside a decoder still propagates.
    """
    _consumer(
        tmp_path, "boom",
        "EXTENSIONS = ('.boom',)\ndef decode(raw, rel_path):\n    raise ValueError('bad')\n",
    )
    module = decode.decoder_named("boom", tmp_path)
    with pytest.raises(decode.DecodeFailed, match="boom: ValueError: bad"):
        decode.decode_with(module, b"x", "fetched.boom", tmp_path)


def test_decode_is_decode_with_plus_an_extension_lookup():
    """The identity that keeps the two paths from drifting.

    `decode()` chooses by extension; the URL path chooses by name. Both run the
    same body, so a change to `bound_root` or to the failure split reaches both.
    """
    raw = b"a,b\n1,2\n"
    by_extension = decode.decode(raw, "docs/t.csv")
    by_name = decode.decode_with(decode.decoder_named("csv"), raw, "docs/t.csv")
    assert by_extension == by_name is not None


def test_primary_is_the_authors_first_extension_and_extensions_stays_sorted():
    module = decode.decoder_named("xlsx")
    assert module.extensions == tuple(sorted(module.extensions))
    assert module.primary == ".xlsx"
    assert module.primary in module.extensions
