"""The derived plane's declared shapes, checked against the code that writes them.

**A schema nothing compares against is a comment.** These tests are what make
`derive/runtime.schema.json` load-bearing: the struct string, the doc table's
field set and the runtime version are each asserted equal to the module that
actually produces them.

The reason is a real day. On 2026-08-23 `superseded` and `mtime` were added to
the doc table while `RUNTIME_SCHEMA` stayed put, so an accelerator built minutes
earlier kept being read — `ask --scan` applied a supersession demotion and
`ask --fast` did not. **A disposable plane that drifts does not corrupt the
index; it makes one of the two paths disagree, which is a fast wrong answer.**
"""

from __future__ import annotations

import json
from importlib import resources

import pytest

from fux.derive import format as fmt

SCHEMA_NAME = "runtime.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads((resources.files("fux.derive") / SCHEMA_NAME).read_text("utf-8"))


# -- the schema and the code agree -------------------------------------------


def test_the_runtime_version_matches(schema):
    """One string versions the whole plane, so the schema must move with it."""
    assert schema["schema"] == fmt.RUNTIME_SCHEMA


def test_the_offset_entry_struct_matches_the_code(schema):
    """The docstring table in `format.py` described this layout in prose and
    nothing checked it. It has already been wrong once — the entry grew 40 → 62
    bytes in W-76 Phase 1."""
    declared = schema["offset_table_entry"]
    assert declared["struct"] == fmt.ENTRY_STRUCT.format
    assert declared["size_bytes"] == fmt.ENTRY_SIZE == 62


def test_the_declared_field_codes_reconstruct_the_struct(schema):
    """Both directions. The `struct` string could match while the field table
    beside it described something else entirely — which is exactly the kind of
    documentation that reads as authority and is wrong."""
    codes = "".join(f["code"] for f in schema["offset_table_entry"]["fields"])
    assert "<" + codes == fmt.ENTRY_STRUCT.format


def test_the_docs_table_field_set_matches(schema):
    assert tuple(schema["docs_table_line"]["fields"]) == fmt.DOCS_FIELDS


def test_the_stats_field_set_matches_a_real_stats_file(schema, tmp_path):
    """Built, not hand-written: the assertion is against what `fux build`
    actually emits."""
    from fux.derive import build
    from fux.store import term_hash, write_index

    write_index(
        tmp_path,
        [{
            "id": "file:a.md", "src": "git", "loc": "a.md", "mode": "extracted",
            "meta": "plain", "title": "A", "phrases": [],
            "terms": {term_hash("alpha"): [1, 0]}, "flen": [4], "edges": [],
        }],
    )
    build(tmp_path)
    produced = json.loads((fmt.runtime_dir(tmp_path) / fmt.STATS_NAME).read_text("utf-8"))
    assert set(produced) == set(schema["stats"]["fields"])


# -- the examples are real, not decorative -----------------------------------


def test_the_offset_entry_example_packs_and_round_trips(schema):
    """An example that cannot be packed is a lie in a file whose whole job is to
    tell the truth about a binary layout."""
    ex = schema["offset_table_entry"]["example"]
    packed = fmt.pack_entry(
        bytes.fromhex(ex["term"]), ex["block_no"], ex["offset"], ex["length"],
        tuple(ex["mx"]), tuple(ex["mnw"]), ex["first_doc"], ex["last_doc"], ex["count"],
    )
    assert len(packed) == fmt.ENTRY_SIZE

    term, block_no, offset, length, mx, mnw, first, last, count = fmt.unpack_entry(packed, 0)
    assert term.hex() == ex["term"]
    assert [block_no, offset, length, first, last, count] == [
        ex["block_no"], ex["offset"], ex["length"], ex["first_doc"], ex["last_doc"], ex["count"]
    ]
    assert list(mx) == ex["mx"] and list(mnw) == ex["mnw"]


def test_the_docs_table_example_carries_exactly_the_declared_fields(schema):
    example = schema["docs_table_line"]["example"]
    assert set(example) == set(fmt.DOCS_FIELDS)


def test_the_stats_example_carries_exactly_the_declared_fields(schema):
    assert set(schema["stats"]["example"]) == set(schema["stats"]["fields"])


def test_the_postings_block_example_has_the_documented_shape(schema):
    term_hash, postings = schema["postings_block_line"]["example"]
    assert len(term_hash) == 16 and int(term_hash, 16) >= 0
    docidxs = [d for d, _tf in postings]
    assert docidxs == sorted(docidxs), "postings ascend by docidx within a block"
    for _d, tf in postings:
        assert 1 <= len(tf) <= 5, "per-field tf, trailing zeros trimmed"
        assert all(isinstance(v, int) for v in tf)


def test_every_declared_shape_carries_an_example(schema):
    """The rule, asserted rather than trusted: a shape without an example is a
    shape somebody will guess at."""
    shapes = [k for k, v in schema.items() if isinstance(v, dict) and not k.startswith("_")]
    assert shapes, "the schema declares no shapes at all"
    for name in shapes:
        assert "example" in schema[name], f"{name} declares no example"
