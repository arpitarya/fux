"""`.fux/types.toml`'s reader and one-line editors — ADR-TYPES decision 12.

The resolution half (does a binding name a real module, does it redirect a
claimed extension) is `tests/decode/test_binding.py`. This file holds what the
file itself promises: the canonical layout round-trips, an edit changes one
line and nothing else, and a layout fux did not write is refused, not rewritten.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import typesfile

ORIGIN = ".fux/types.toml"


def test_render_then_parse_is_the_identity_on_the_model():
    text = typesfile.render(["*.md", "docs/*.txt", "*.md"], {"tar.gz": "zip", "csv": "csv"})
    listed = typesfile.parse(text, origin=ORIGIN)
    assert listed.include == ("*.md", "docs/*.txt"), "sorted and deduped (L3)"
    assert listed.decoders == {"csv": "csv", "tar.gz": "zip"}
    assert '"tar.gz" = "zip"' in text, "a dotted extension is quoted or TOML nests it"


def test_render_is_a_pure_function_of_its_input():
    a = typesfile.render(["*.txt", "*.md"], {"tsv": "csv", "csv": "csv", "pdf": "pdf"})
    b = typesfile.render(["*.md", "*.txt"], {"pdf": "pdf", "csv": "csv", "tsv": "csv"})
    assert a == b


def test_quote_escapes_what_toml_needs_escaped():
    for value in ['a"b', "a\\b", "tab\there", "odd\x01"]:
        text = f"include = [{typesfile.quote(value)}]\n"
        import tomllib

        assert tomllib.loads(text)["include"] == [value]


def test_add_include_inserts_one_sorted_line_and_touches_nothing_else():
    before = '# top\ninclude = [\n  "*.md",   # docs\n  # "*.log",\n  "*.txt",\n]\n\n[decoders]\ncsv = "csv"\n'
    after, action = typesfile.add_include(before, "*.rst", origin=ORIGIN)
    assert action == "added"
    assert after == before.replace('  # "*.log",\n', '  # "*.log",\n  "*.rst",\n')


def test_add_include_is_idempotent():
    text = 'include = [\n  "*.md",\n]\n'
    assert typesfile.add_include(text, "*.md", origin=ORIGIN) == (text, "unchanged")


def test_add_include_creates_the_array_above_the_first_table():
    text = '# mine\n[decoders]\ncsv = "csv"\n'
    after, _ = typesfile.add_include(text, "*.md", origin=ORIGIN)
    assert after.index("include = [") < after.index("[decoders]")
    assert typesfile.parse(after, origin=ORIGIN).include == ("*.md",)


def test_set_decoder_joins_the_group_of_its_module():
    text = typesfile.render([], {"htm": "html", "html": "html", "pdf": "pdf"})
    after, action, previous = typesfile.set_decoder(text, "xhtml", "html", origin=ORIGIN)
    assert (action, previous) == ("added", "")
    lines = after.splitlines()
    assert lines.index('xhtml = "html"') == lines.index('html = "html"') + 1


def test_set_decoder_starts_a_new_group_for_a_new_module():
    text = typesfile.render([], {"pdf": "pdf"})
    after, _, _ = typesfile.set_decoder(text, "geojson", "json", origin=ORIGIN)
    assert after.endswith('pdf = "pdf"\n\ngeojson = "json"\n')


def test_set_decoder_updates_in_place_and_keeps_the_comment():
    text = '[decoders]\ncsv = "csv"   # ours\n'
    after, action, previous = typesfile.set_decoder(text, "csv", "mycsv", origin=ORIGIN)
    assert (action, previous) == ("updated", "csv")
    assert after == '[decoders]\ncsv = "mycsv"  # ours\n'


def test_set_decoder_creates_the_table_when_there_is_none():
    after, _, _ = typesfile.set_decoder('include = [\n  "*.md",\n]\n', "pdf", "pdf", origin=ORIGIN)
    assert typesfile.parse(after, origin=ORIGIN).decoders == {"pdf": "pdf"}


def test_remove_deletes_exactly_one_line_from_either_key():
    text = typesfile.render(["*.md", "*.txt"], {"pdf": "pdf"})
    after, removed = typesfile.remove(text, "*.txt", origin=ORIGIN)
    assert removed == "*.txt" and after == text.replace('  "*.txt",\n', "")
    after, removed = typesfile.remove(after, "*.pdf", origin=ORIGIN)
    assert removed == "*.pdf decoder=pdf" and "pdf" not in after


@pytest.mark.parametrize(
    "text, edit",
    [
        ('include = ["*.md", "*.txt"]\n', lambda s: typesfile.add_include(s, "*.rst", origin=ORIGIN)),
        ('include = [\n  "*.md", "*.txt",\n]\n', lambda s: typesfile.add_include(s, "*.rst", origin=ORIGIN)),
        ('include = ["*.md", "*.txt"]\n', lambda s: typesfile.remove(s, "*.md", origin=ORIGIN)),
        ('decoders = { csv = "csv" }\n', lambda s: typesfile.set_decoder(s, "pdf", "pdf", origin=ORIGIN)),
        ('decoders.csv = "csv"\n', lambda s: typesfile.set_decoder(s, "pdf", "pdf", origin=ORIGIN)),
    ],
)
def test_an_editor_refuses_a_layout_it_did_not_write(text, edit):
    with pytest.raises(FuxError, match="will not edit it"):
        edit(text)


def test_the_reader_accepts_every_layout_the_editor_refuses():
    """Reader lenient, writer strict (ADR-URL-LIST decision 13, kept)."""
    listed = typesfile.parse('include = ["*.md", "*.txt"]\ndecoders = { csv = "csv" }\n', origin=ORIGIN)
    assert listed.allow == ("*.csv", "*.md", "*.txt")


def test_an_edit_that_would_produce_an_invalid_file_writes_nothing():
    """Every edit re-parses its own result, so `!` cannot sneak in through a verb."""
    with pytest.raises(FuxError, match="does not subtract"):
        typesfile.add_include('include = [\n  "*.md",\n]\n', "!*.min.md", origin=ORIGIN)


def test_convert_legacy_splits_bindings_globs_and_exclusions():
    include, decoders, exclusions = typesfile.convert_legacy(
        "*.md\n*.csv decoder=csv\ndocs/*.txt\n!*.min.md\n", origin=".fux/sources/types"
    )
    assert include == ["*.md", "docs/*.txt"]
    assert decoders == {"csv": "csv"}
    assert exclusions == ["*.min.md"]


def test_convert_legacy_refuses_what_the_old_grammar_refused():
    with pytest.raises(FuxError, match="per extension"):
        typesfile.convert_legacy("docs/*.json decoder=json\n", origin=".fux/sources/types")
