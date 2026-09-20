"""The committed record's shape, declared once in `store/index-record.schema.json`.

The shape used to live in four places — assembled inline twice in
`ingest/run.py`, policed by `DISPLAY_FIELDS` in `store/writer.py`, carried by
`EXTRACTED_FIELDS` in `ingest/run.py`, and described in prose by SR-RECORD —
and **nothing compared them**. Adding a display field meant remembering to touch
a tuple in a different module, and forgetting was silent: the field shipped and
L5's check simply did not look at it.
"""

from __future__ import annotations

import json
from importlib import resources

import pytest

from fux.errors import FuxError
from fux.store import canonical, recordschema, writer


def _git_record(**over):
    base = dict(
        id="file:a.md", src="git", loc="a.md", sha="abc123", ver=1,
        mode="extracted", title="A", phrases=["H"],
        terms={"0123456789abcdef": [1, 0, 0, 0, 0]}, flen=[4], edges=[],
    )
    base.update(over)
    return base


# -- THE test: the schema changed no committed byte -------------------------


def test_building_through_the_template_is_byte_identical_to_the_inline_dict():
    """**The gate on this whole change.**

    A refactor of how a record is assembled must not move a single committed
    byte. If it does, every existing index needs a migration and the schema id
    is a lie — so this compares the canonical encoding, not the dicts.
    """
    inline = {
        "id": "file:a.md",
        "src": "git",
        "loc": "a.md",
        "sha": "abc123",
        "ver": 0,
        "mode": "extracted",
    }
    built = recordschema.build(
        id="file:a.md", src="git", loc="a.md", sha="abc123",
        ver=0, mode="extracted",
    )
    assert canonical.canonical_dumps(built) == canonical.canonical_dumps(inline)


def test_key_order_in_the_template_cannot_reach_a_committed_byte():
    """`canonical_dumps` sorts keys, which is what makes the schema's order
    presentational. Asserted rather than assumed — if this ever stops being
    true, the schema silently becomes a wire format."""
    a = recordschema.build(id="file:a.md", src="git", loc="a.md", sha="s", ver=0,
                          mode="extracted")
    b = {k: a[k] for k in reversed(list(a))}
    assert canonical.canonical_dumps(a) == canonical.canonical_dumps(b)


# -- the schema IS the single source of truth -------------------------------


def test_display_fields_come_from_the_template():
    """L5's check reads the schema, so a new display field is protected the
    moment it is declared — not the moment someone remembers a tuple."""
    assert writer.DISPLAY_FIELDS == recordschema.display_fields()
    assert set(writer.DISPLAY_FIELDS) == {"title", "phrases"}


def test_carried_fields_come_from_the_template():
    from fux.ingest.run import EXTRACTED_FIELDS

    assert EXTRACTED_FIELDS == recordschema.carried_fields()


def test_edges_is_never_carried_forward():
    """The interesting exclusion. `edges` is the one field the rest of the
    corpus can change without this document changing, so carrying it forward
    would freeze a link a newly added document should have resolved."""
    assert "edges" not in recordschema.carried_fields()


def test_the_template_schema_matches_the_index_schema():
    """Two fux versions with different record shapes must never both call their
    output `fux.index.v3`."""
    from fux.store.format import SCHEMA_ID

    assert recordschema.shape().schema == SCHEMA_ID


def test_every_field_ingest_writes_is_declared():
    """The both-directions half. A field the code writes and the schema does
    not declare is exactly the drift this file exists to stop."""
    written = {
        "id", "src", "loc", "sha", "ver", "mode",
        "title", "phrases", "terms", "flen", "edges",
        "archived", "superseded", "mtime",
    }
    assert written == set(recordschema.shape().fields)


# -- build(): defaults, omission, and the typo that used to ship --------------


def test_a_field_the_template_does_not_declare_is_refused():
    """It used to sail into the committed index and never be read again — no
    error, no test, a field that exists forever and means nothing."""
    with pytest.raises(FuxError, match="not declared"):
        recordschema.build(id="file:a.md", titel="typo")


def test_omit_when_false_leaves_the_field_out_entirely():
    """SR-ARCHIVED-CONTENT decision 1: absent, not false, so a live record's
    shape is unchanged and no existing consumer's parse breaks."""
    record = recordschema.build(id="file:a.md", src="git", loc="a.md", sha="s",
                               ver=0, mode="extracted", archived=False)
    assert "archived" not in record

    marked = recordschema.build(id="file:a.md", src="git", loc="a.md", sha="s",
                               ver=0, mode="extracted", archived=True)
    assert marked["archived"] is True


def test_defaults_apply_only_to_always_required_fields():
    record = recordschema.build(id="file:a.md", src="git", loc="a.md", sha="s")
    assert record["ver"] == 0 and record["mode"] == "extracted"
    assert "title" not in record  # optional and unset stays absent


# -- validate(): a tool, not a checkpoint -------------------------------------


def test_a_well_formed_record_validates():
    recordschema.validate(_git_record())


def test_a_missing_required_field_is_named():
    record = _git_record()
    del record["sha"]
    with pytest.raises(FuxError, match="sha"):
        recordschema.validate(record)


def test_meta_and_title_h_are_refused_as_undeclared_fields():
    """⚠ **REPLACES `test_a_non_git_record_must_state_meta` and
    `test_a_hashed_record_must_carry_title_h`.** Both asserted L5's shape: a
    non-git record had to state `meta`, and a hashed one had to carry
    `title_h`. W-194 (Arpit, 2026-09-20) deleted both fields, so what is
    asserted now is the other half of the same property — **a record still
    carrying them does not validate.** Deleted, not deprecated: the
    `fux update` precedent (W-177), no accept-and-ignore.
    """
    for dead in ("meta", "title_h"):
        record = _git_record(id="url:https://x", src="url", loc="https://x")
        record[dead] = "anything"
        with pytest.raises(FuxError, match=f"undeclared field.*{dead}"):
            recordschema.validate(record)


def test_an_enum_outside_its_set_is_refused():
    with pytest.raises(FuxError, match="src"):
        recordschema.validate(_git_record(src="ftp"))


def test_a_bool_is_not_accepted_where_an_int_is_declared():
    """`bool` is an `int` subclass in Python, so a naive isinstance check lets
    `ver=True` through and writes `true` into a numeric field."""
    with pytest.raises(FuxError, match="ver"):
        recordschema.validate(_git_record(ver=True))


def test_writing_false_where_the_template_says_omit_is_refused():
    with pytest.raises(FuxError, match="OMITTED"):
        recordschema.validate(_git_record(archived=False))


def test_validate_is_not_called_on_the_write_path(tmp_path):
    """Deliberate: `canonical_dumps` refuses floats, nulls and hostile text.
    A second gate on the hot path would re-check what it already guarantees.
    (⚠ `write_index`'s L5 meta policy was the other one named here until W-194
    deleted the rule and the law on 2026-09-20.)

    Asserted by writing a record with an undeclared field — `validate` would
    reject it, and the writer does not.
    """
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    record = _git_record()
    record["undeclared_but_harmless"] = "x"
    writer.write_index(tmp_path, [record])  # no raise
    with pytest.raises(FuxError):
        recordschema.validate(record)


# -- the schema is package data, and ships ---------------------------------


def test_the_template_ships_in_the_package():
    """Not just present in the source tree — reachable through
    `importlib.resources`, which is how an installed wheel finds it."""
    raw = (resources.files("fux.store") / recordschema.SCHEMA_NAME).read_text("utf-8")
    parsed = json.loads(raw)
    assert parsed["schema"] and parsed["fields"]


# -- the examples are checked against the schema that declares them ----------


def test_both_examples_validate_against_the_schema():
    """**An example nobody checks is the documentation most likely to be
    wrong**, because it is the part people copy. These go through the same
    `validate()` a hand-built record does.
    """
    import json
    from importlib import resources

    raw = json.loads(
        (resources.files("fux.store") / recordschema.SCHEMA_NAME).read_text("utf-8")
    )
    for name, example in raw["examples"].items():
        record = {k: v for k, v in example.items() if not k.startswith("_")}
        recordschema.validate(record)


def test_the_examples_encode_to_real_committed_lines():
    """One step past validation: the canonical encoder refuses floats, nulls,
    hostile line breaks and over-deep nesting. An example that validates but
    cannot be written is still a lie about what a record looks like."""
    import json
    from importlib import resources

    raw = json.loads(
        (resources.files("fux.store") / recordschema.SCHEMA_NAME).read_text("utf-8")
    )
    for example in raw["examples"].values():
        record = {k: v for k, v in example.items() if not k.startswith("_")}
        line = canonical.canonical_dumps(record)
        assert line.endswith(b"\n") and json.loads(line)["id"] == record["id"]


def test_the_url_example_is_shaped_like_the_git_one():
    """⚠ **REPLACES `test_the_hashed_example_carries_no_display_text`**, which
    asserted L5 on the example a reader copies: a hashed record held `title_h`
    and nothing readable. W-194 deleted the fork, so the two examples now
    differ only in `src`, `loc` and the id — and this asserts exactly that,
    because an example that quietly kept a dead field is how a consumer learns
    a shape fux no longer writes."""
    import json
    from importlib import resources

    raw = json.loads(
        (resources.files("fux.store") / recordschema.SCHEMA_NAME).read_text("utf-8")
    )
    url = {k: v for k, v in raw["examples"]["url"].items() if not k.startswith("_")}
    git = {k: v for k, v in raw["examples"]["git"].items() if not k.startswith("_")}
    assert "meta" not in url and "title_h" not in url
    assert url["src"] == "url" and git["src"] == "git"
    assert set(recordschema.display_fields()) <= set(url), (
        "the url example must carry display text now — that IS the W-194 change"
    )


def test_the_git_example_omits_archived_rather_than_writing_false():
    """`omit_when` shown, not just declared."""
    import json
    from importlib import resources

    raw = json.loads(
        (resources.files("fux.store") / recordschema.SCHEMA_NAME).read_text("utf-8")
    )
    assert "archived" not in raw["examples"]["git"]
    assert "superseded" not in raw["examples"]["git"]

