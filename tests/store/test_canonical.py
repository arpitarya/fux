from __future__ import annotations

import json
import unicodedata

import pytest

from fux.errors import FuxError
from fux.store.canonical import canonical_dumps

_NFC_CAFE = unicodedata.normalize("NFC", "café")
_NFD_CAFE = unicodedata.normalize("NFD", "café")


def test_sorted_keys_and_compact_separators():
    out = canonical_dumps({"b": 1, "a": 2})
    assert out == b'{"a":2,"b":1}\n'


def test_ensure_ascii_false_keeps_unicode_literal():
    out = canonical_dumps({"title": _NFC_CAFE})
    assert _NFC_CAFE.encode("utf-8") in out
    assert b"\\u" not in out


def test_round_trips_through_json_loads():
    record = {"id": "file:a.md", "terms": {"abcd": [1, 2]}, "edges": [{"kind": "ref", "grade": 10}]}
    assert json.loads(canonical_dumps(record)) == record


def test_trailing_newline():
    assert canonical_dumps({"a": 1}).endswith(b"\n")


def test_rejects_float():
    with pytest.raises(FuxError, match="no floats"):
        canonical_dumps({"score": 1.5})


def test_rejects_null():
    with pytest.raises(FuxError, match="no nulls"):
        canonical_dumps({"community": None})


def test_rejects_non_nfc_text():
    # NFD "café" (e + combining acute U+0301) — the macOS-checkout hazard R1 guards.
    assert _NFD_CAFE != _NFC_CAFE
    with pytest.raises(FuxError, match="non-NFC"):
        canonical_dumps({"title": _NFD_CAFE})


def test_accepts_nfc_text():
    assert canonical_dumps({"title": _NFC_CAFE})


def test_rejects_non_string_dict_key():
    with pytest.raises(FuxError, match="non-string key"):
        canonical_dumps({1: "a"})


def test_nested_structures_validated():
    with pytest.raises(FuxError, match="no floats"):
        canonical_dumps({"edges": [{"kind": "ref", "grade": 1.0}]})


def test_rejects_non_nfc_dict_key():
    with pytest.raises(FuxError, match="non-NFC"):
        canonical_dumps({"anchors": {_NFD_CAFE: 1}})


def test_rejects_lone_surrogate():
    with pytest.raises(FuxError, match="not valid UTF-8"):
        canonical_dumps({"id": "file:docs/\udcff.md"})


def test_rejects_hostile_line_separators():
    for ch in (" ", " ", "\x85"):
        with pytest.raises(FuxError, match="line separator"):
            canonical_dumps({"title": f"line{ch}break"})


def test_golden_header_line():
    from fux.store.format import HEADER

    # _format bumped v1 -> v2 and tf_fields grew from [heading, body] to the
    # five-field, body-first order (W-76 Phase 1: see TF_FIELDS docstring).
    assert canonical_dumps(HEADER) == (
        b'{"_format":"fux.index.v2","analyzer":"v2","tf_fields":["body","heading","title","path","ctx"]}\n'
    )
