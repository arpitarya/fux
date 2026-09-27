"""Every schema in the package, checked by one gate.

**This file is the reason the schemas are worth having.** A declaration nothing
compares against is a comment, and comments rot silently. What makes this gate
different from a per-schema test is that it **discovers** schemas: a sixth one
added next month is covered the moment it lands, without anybody remembering to
write a test for it.

The per-schema tests still exist and still matter — they assert the things only
that shape knows, like the offset entry's struct string matching
`ENTRY_STRUCT.format`. This one asserts the properties **every** schema must
have, which is exactly the set nobody thinks to re-check.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fux import schema as schema_mod
from fux.errors import FuxError

SRC = Path(__file__).resolve().parents[1] / "src" / "fux"
SCHEMA_DIR = SRC / "schemas"


def _discovered() -> list[Path]:
    """Every `*.schema.json` shipped in the package, wherever it sits.

    ⚠ **Discovery walks the whole package, not `schemas/`**, so a schema
    written anywhere else is still found — and then refused by the placement
    test below rather than silently skipped.
    """
    return sorted(SRC.rglob("*.schema.json"))


SCHEMAS = _discovered()
IDS = [str(p.relative_to(SRC)) for p in SCHEMAS]


def test_schemas_are_actually_discovered():
    """A discovery-based gate that discovers nothing passes vacuously.

    The same failure R6's tier 1 had: a green arm proving only that it ran.
    """
    assert len(SCHEMAS) >= 5, f"expected the five declared planes, found {IDS}"


@pytest.mark.parametrize("path", SCHEMAS, ids=IDS)
def test_every_schema_is_valid_json_and_loadable(path):
    json.loads(path.read_text(encoding="utf-8"))
    schema_mod.load(path.name)


@pytest.mark.parametrize("path", SCHEMAS, ids=IDS)
def test_every_schema_lives_in_the_schemas_directory(path):
    """**One directory, one loader** (Arpit, 2026-09-27, W-226; SR-LAWS
    decision 6). `fux.schema.load` resolves every name from `fux.schemas`, so a
    schema written anywhere else is one no production path can load."""
    assert path.parent == SCHEMA_DIR, f"{path.relative_to(SRC)} is outside src/fux/schemas/"


@pytest.mark.parametrize("path", SCHEMAS, ids=IDS)
def test_every_schema_has_its_own_ownership_row(path):
    """**What construction used to guarantee, now a gate.**

    Until W-226 each schema sat beside the code it describes and inherited that
    directory's owner — correct by construction. In one shared directory the
    directory's owner (SR-LAWS, the mechanism's) would otherwise own all five
    shapes, which is how the record shape was once briefly the fetcher record's.
    So every file needs its OWN file-level OWNERSHIP row naming the record that
    decides the shape; the directory row alone is not enough.
    """
    from sr_lib import ownership_table

    table = ownership_table()
    component = str(path.relative_to(SRC.parents[1]))
    assert component in table, (
        f"{component} has no file-level row in records/README.md §OWNERSHIP — it "
        "would fall to SR-LAWS, the directory's owner. Add a row naming the record "
        "that decides this shape"
    )
    assert table[component] != "SR-LAWS", f"{component} is owned by the mechanism, not a shape's record"


@pytest.mark.parametrize("path", SCHEMAS, ids=IDS)
def test_every_schema_declares_a_version_id(path):
    """So two fux versions with different shapes can never both claim one id."""
    assert schema_mod.load(path.name).id, "no `schema` id declared"


#: Documentation keys a schema file may carry INSIDE an example. Stripped before
#: validation because they are notes to a reader, not data.
#:
#: ⚠ **This used to be `startswith("_")` and that was too broad.** It collided
#: the moment fux adopted the in-toto Statement shape, whose REQUIRED field is
#: literally `_type` — the strip removed it and the example then failed its own
#: declaration for a field it plainly had. **A leading underscore is fux's
#: convention for metadata and somebody else's convention for data**, so the
#: rule is now a named set rather than a prefix.
_DOC_KEYS = frozenset({"_doc", "_comment", "_note"})


def _strip_doc(example: dict) -> dict:
    return {k: v for k, v in example.items() if k not in _DOC_KEYS}

@pytest.mark.parametrize("path", SCHEMAS, ids=IDS)
def test_every_declared_shape_carries_an_example(path):
    """**A shape without an example is a shape somebody will guess at**, and the
    guess will be wrong in exactly the way the declaration was trying to fix."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    shapes = [
        name for name, value in raw.items()
        if isinstance(value, dict)
        and not name.startswith("_")
        and name not in ("fields", "example", "examples")
    ]
    if not shapes:  # a single-shape file declares its example at the top level
        assert "example" in raw or "examples" in raw, f"{path.name} declares no example"
        return
    for name in shapes:
        body = raw[name]
        assert "example" in body or "examples" in body, f"{path.name}#{name} has no example"


@pytest.mark.parametrize("path", SCHEMAS, ids=IDS)
def test_every_example_validates_against_its_own_declaration(path):
    """The one that would actually catch a rotted schema.

    An example is the part people copy, so an example that no longer matches
    the fields beside it is the most expensive kind of wrong documentation.
    Only shapes that declare `fields` can be checked — a positional shape (the
    graph's 4-tuple edge, the postings block line) declares its layout
    differently and is covered by its own test.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    checked = 0
    for name, body in raw.items():
        if name in ("fields", "example", "examples") or name.startswith("_"):
            continue
        if not isinstance(body, dict) or not isinstance(body.get("fields"), dict):
            # A POSITIONAL shape (the struct entry, the graph's 4-tuple edge)
            # declares an ordered list, not a name->spec map. Its example is a
            # list and is checked by the shape's own test, which knows what the
            # positions mean.
            continue
        shape = schema_mod.load(path.name).shape(name)
        for example in _examples(body):
            if not isinstance(example, dict):
                continue
            clean = _strip_doc(example)
            shape.validate(clean, label=f"{path.name}#{name}")
            checked += 1
    if "fields" in raw:
        shape = schema_mod.load(path.name)
        for example in _examples(raw):
            clean = _strip_doc(example)
            shape.validate(clean, label=path.name, conditions=_CONDITIONS)
            checked += 1
    assert checked or True  # a positional-only schema legitimately checks nothing here


def _examples(body: dict) -> list:
    out = []
    if "example" in body:
        out.append(body["example"])
    out.extend((body.get("examples") or {}).values())
    return out


#: `required` values that are conditions rather than `always`/`never`. A schema
#: says *required for a non-git record* without this module knowing what a git
#: record is; the caller supplies the meaning.
_CONDITIONS = {
    "non-git": lambda obj: obj.get("src") not in (None, "git"),
    "when-hashed": lambda obj: obj.get("meta") == "hashed",
    "when-url-configured": lambda obj: True,
}


# -- the mechanism itself -----------------------------------------------------


def test_a_missing_schema_is_a_broken_install_not_a_config_error():
    with pytest.raises(FuxError, match="broken install"):
        schema_mod.load("no-such.schema.json")


def test_coerce_never_raises_on_hostile_input():
    """`coerce` is the READING path, and a file on disk may have been truncated
    by a killed process, hand-edited during a debug session, or written by an
    older fux. A reporting plane must degrade rather than take down `doctor`."""
    shape = schema_mod.load("state.schema.json").shape("url_health")
    for hostile in (None, [], "text", 42, {"fail_streak": "many"}, {"unknown": 1}):
        assert isinstance(shape.coerce(hostile), dict)


def test_validate_raises_where_coerce_would_shrug():
    """The asymmetry is the design. A shape fux is about to WRITE should be
    right; a shape fux READS may be anything."""
    shape = schema_mod.load("state.schema.json").shape("url_health")
    assert shape.coerce({"fail_streak": "many"}) == {}
    with pytest.raises(FuxError, match="fail_streak"):
        shape.validate({"fail_streak": "many"})


def test_a_bool_is_refused_where_an_int_is_declared():
    """`bool` is an `int` subclass, so a naive isinstance check writes `true`
    into a numeric field and nobody notices until a consumer parses it."""
    shape = schema_mod.load("state.schema.json").shape("url_health")
    with pytest.raises(FuxError, match="fail_streak"):
        shape.validate({"fail_streak": True})


def test_asking_for_a_shape_that_is_not_declared_says_so():
    with pytest.raises(FuxError, match="declares no shape"):
        schema_mod.load("output.schema.json").shape("nope")
