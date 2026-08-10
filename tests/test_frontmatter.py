"""Unit suite for the hand-rolled frontmatter parser — it is load-bearing."""

from __future__ import annotations

from fux.frontmatter import Frontmatter, dumps, parse


def test_basic_parse():
    fm = parse("---\ntype: Note\ncount: 3\n---\nbody line\n")
    assert fm.meta == {"type": "Note", "count": 3}
    assert fm.body == "body line\n"
    assert fm.body_start_line == 5  # 4 header lines, body begins on line 5


def test_no_frontmatter_is_all_body():
    text = "just a document\nwith lines\n"
    fm = parse(text)
    assert fm.meta == {} and fm.body == text and fm.body_start_line == 1


def test_no_closing_delimiter_degrades_to_body():
    text = "---\ntype: Broken\nnever closed\n"
    fm = parse(text)
    assert fm.meta == {} and fm.body == text


def test_empty_block():
    fm = parse("---\n---\nbody")
    assert fm.meta == {} and fm.body == "body"


def test_scalar_types():
    fm = parse(
        "---\n"
        "s: hello world\n"
        "i: 42\n"
        "neg: -7\n"
        "f: 2.5\n"
        "t: true\n"
        "n: null\n"
        "date: 2026-07-21\n"
        "ver: 0.19.0\n"
        "quoted: \"a: b\"\n"
        "single: 'it''s'\n"
        "---\n"
    )
    assert fm.meta["s"] == "hello world"
    assert fm.meta["i"] == 42 and fm.meta["neg"] == -7
    assert fm.meta["f"] == 2.5
    assert fm.meta["t"] is True
    assert fm.meta["n"] is None
    assert fm.meta["date"] == "2026-07-21"  # ISO dates stay strings
    assert fm.meta["ver"] == "0.19.0"  # not a float
    assert fm.meta["quoted"] == "a: b"
    assert fm.meta["single"] == "it's"


def test_lists_inline_and_block():
    fm = parse('---\ninline: [a, "b c", 3]\nblock:\n  - one\n  - two\nempty: []\n---\n')
    assert fm.meta["inline"] == ["a", "b c", 3]
    assert fm.meta["block"] == ["one", "two"]
    assert fm.meta["empty"] == []


def test_nested_mapping():
    fm = parse("---\nmetadata:\n  type: user\n  tags:\n    - a\n    - b\n---\n")
    assert fm.meta == {"metadata": {"type": "user", "tags": ["a", "b"]}}


def test_literal_block():
    fm = parse("---\ntext: |\n  line one\n  line two\n\n  after blank\nnext: 1\n---\n")
    assert fm.meta["text"] == "line one\nline two\n\nafter blank"
    assert fm.meta["next"] == 1


def test_comments_and_blank_lines_skipped():
    fm = parse("---\n# a comment\n\nkey: value  # trailing\n---\n")
    assert fm.meta == {"key": "value"}


def test_unknown_keys_preserved_roundtrip():
    meta = {
        "type": "Ingested Document",
        "some_future_key": "kept",
        "nested": {"a": 1, "b": ["x", "y"]},
    }
    fm = parse(dumps(meta, "body\n"))
    assert fm.meta == meta and fm.body == "body\n"


def test_roundtrip_identity_many():
    cases = [
        {"a": "plain"},
        {"a": ""},
        {"a": "has: colon", "b": "#lead", "c": "-dash", "d": "[brackety"},
        {"a": " padded "},
        {"n": None, "t": True, "f": False, "i": -3, "fl": 0.125},
        {"num_str": "42", "ver": "1.2.3", "boolish": "true"},
        {"lst": [1, "two", 3.0], "empty": []},
        {"uni": "café — naïve ✓", "emoji": "🎯"},
        {"multi": "first\nsecond\n\nfourth"},
        {"deep": {"x": {"y": "z"}}},
    ]
    for meta in cases:
        out = dumps(meta, "the body\nsecond line")
        fm = parse(out)
        assert fm.meta == meta, out
        assert fm.body == "the body\nsecond line"


def test_body_preserved_byte_exact():
    body = "# Title\n\n```py\nx = '---'\n---\n```\ntrailing"
    fm = parse(dumps({"k": "v"}, body))
    assert fm.body == body


def test_dumps_deterministic():
    meta = {"b": 1, "a": 2}  # insertion order preserved, not sorted
    assert dumps(meta, "x") == dumps(dict(meta), "x")
    assert dumps(meta, "x").index("b:") < dumps(meta, "x").index("a:")


def test_frontmatter_dataclass_defaults():
    fm = Frontmatter({}, "b")
    assert fm.body_start_line == 1
