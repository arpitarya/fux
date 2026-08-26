"""W-84 — `ask` is heading-level: the sections that match, never a line range.

The unit under test is `query/headings.py::headings_for`, plus the two surfaces
that render it (`fux ask` in text and `--json`) and the one that must **not**
change (`fux find`'s piped stdout).

**What these tests are really guarding** is that this stays display-only. It
runs on the already-unified result list, exactly like `_resolve_title` (P5), so
it can never reach a score, an ordering, or the differential law. A test that
asserts a heading appears is easy; the ones that matter here are the ones that
assert the selection is a deterministic function of the record, that a
`hashed` record yields nothing, and that no match yields silence rather than an
invented outline.
"""

from __future__ import annotations

import argparse
import json as json_mod

import pytest

from fux.query import cmd_ask, cmd_find
from fux.query.headings import MAX_HEADINGS, headings_for
from fux.query.tokenize import tokenize
from fux.store import DisplayCache, content_sha, term_hash, title_hash, write_index

DOC_ID = "file:docs/mesh.md"
TITLE = "The mesh"
PHRASES = [
    "Overview",
    "Rollback procedure",
    "Rollback and recovery",
    "Deploying the mesh",
    "A rollback rollback rollback story",
]


def _h(word: str) -> str:
    """Hash the ANALYZED form — the query analyzes before hashing too, so a
    fixture that hashed the raw word would never be found."""
    return term_hash(tokenize(word)[0])


def _record(**overrides) -> dict:
    record = {
        "id": DOC_ID,
        "src": "git",
        "loc": "docs/mesh.md",
        "mode": "extracted",
        "meta": "plain",
        "sha": content_sha(DOC_ID.encode("utf-8")),
        "title": TITLE,
        "phrases": list(PHRASES),
        "terms": {_h("rollback"): [3, 2], _h("procedure"): [1, 1]},
        "flen": [40, 12],
        "edges": [],
    }
    record.update(overrides)
    return record


def _corpus(tmp_path, record=None):
    write_index(tmp_path, [record or _record()])
    return tmp_path


def _args(**overrides) -> argparse.Namespace:
    base = dict(query="rollback", top=5, json=False, scan=True, explain=False, hybrid=False)
    base.update(overrides)
    return argparse.Namespace(**base)


# -- the selection rule -------------------------------------------------


def test_only_matching_headings_are_returned():
    got = headings_for(_record(), "rollback")
    assert all("ollback" in h for h in got)
    assert "Overview" not in got
    assert "Deploying the mesh" not in got


def test_more_distinct_query_terms_wins_over_more_repetitions():
    """`Rollback procedure` covers two of the asked-about terms. The heading
    that says `rollback` three times covers one, and must lose — otherwise a
    document's most emphatic heading beats its most relevant one."""
    got = headings_for(_record(), "rollback procedure")
    assert got[0] == "Rollback procedure"
    assert got.index("A rollback rollback rollback story") > 0


def test_ties_break_on_document_order_not_set_iteration():
    """Two headings match one term each; the earlier one in the document wins.
    Determinism is L3, and a set-ordering dependence here would be invisible
    until it moved between interpreters."""
    got = headings_for(_record(), "rollback")
    assert got.index("Rollback procedure") < got.index("Rollback and recovery")
    assert got == headings_for(_record(), "rollback")


def test_the_analyzer_is_the_one_both_sides_share():
    """Porter stemming is in the pipeline, so the plural finds the singular.
    A heading matcher with its own notion of a word would silently disagree
    with the ranking that chose the document."""
    assert headings_for(_record(), "rollbacks") == headings_for(_record(), "rollback")


def test_at_most_MAX_HEADINGS_are_shown():
    got = headings_for(_record(), "rollback procedure mesh deploying overview")
    assert len(got) == MAX_HEADINGS


# -- the four ways it must return nothing --------------------------------


@pytest.mark.parametrize(
    "record, query, why",
    [
        (_record(), "kubernetes", "no heading matches — silence, not the first three"),
        (_record(phrases=[]), "rollback", "a document with no headings"),
        (_record(phrases=None), "rollback", "a record whose `phrases` is null"),
        (None, "rollback", "no record found in the shard at all"),
    ],
)
def test_nothing_is_invented(record, query, why):
    assert headings_for(record, query) == [], why


def test_a_query_of_pure_stopwords_yields_nothing():
    """The analyzer drops it to zero terms. Matching on an empty term set would
    match every heading, which reads as relevance and is not."""
    assert headings_for(_record(), "the and of") == []


def test_a_non_string_phrase_is_skipped_not_raised():
    """A committed record is data read off disk, not a promise. A malformed
    shard must not take a query down with it."""
    assert headings_for(_record(phrases=["Rollback procedure", 7, None]), "rollback") == [
        "Rollback procedure"
    ]


# -- the L5 case: a hashed record has no display text at all -------------


def test_a_hashed_record_yields_no_headings(tmp_path):
    """`store/writer.py` refuses to write `phrases` on a `hashed` record — the
    ACL-mismatch leak L5 closes. So this is empty by construction, and this
    test exists to prove there is no path that re-introduces the text."""
    sha = content_sha(b"url:https://x.test/handbook")
    DisplayCache(tmp_path).put(sha, "url:https://x.test/handbook", "Oncall")
    hashed = {
        "id": "url:https://x.test/handbook",
        "src": "url",
        "loc": "https://x.test/handbook",
        "mode": "extracted",
        "meta": "hashed",
        "sha": sha,
        "title_h": title_hash("Oncall"),
        "terms": {_h("rollback"): [2, 1]},
        "flen": [12],
        "edges": [],
    }
    write_index(tmp_path, [hashed])
    assert headings_for(hashed, "rollback") == []


# -- the rendered surfaces ------------------------------------------------


def test_ask_text_prints_matched_headings_under_the_citation(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_args()) == 0
    lines = capsys.readouterr().out.splitlines()

    assert lines[0].endswith("(docs/mesh.md)"), "the citation line is unchanged"
    assert TITLE in lines[0]
    assert "§" not in lines[0], "a heading never joins the locator a reader copies"
    assert lines[1] == "        § Rollback procedure"


def test_ask_text_prints_no_heading_lines_when_none_match(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    record = _record(phrases=["Overview", "Deploying the mesh"])
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path, record))
    assert cmd_ask(_args()) == 0
    assert capsys.readouterr().out.count("\n") == 1


def test_ask_json_carries_headings(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_args(json=True)) == 0
    result = json_mod.loads(capsys.readouterr().out)["results"][0]
    assert result["headings"] == [
        "Rollback procedure",
        "Rollback and recovery",
        "A rollback rollback rollback story",
    ]
    assert result["loc"] == "docs/mesh.md", "the locator stays a bare document path"


def test_the_headings_key_is_present_even_when_empty(tmp_path, monkeypatch, capsys):
    """An absent key is a trap, not a signal (W-48): a caller cannot tell
    'nothing matched' from 'this fux does not do headings'."""
    record = _record(phrases=["Overview"])
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path, record))
    assert cmd_ask(_args(json=True)) == 0
    assert json_mod.loads(capsys.readouterr().out)["results"][0]["headings"] == []


def test_find_stdout_is_untouched(tmp_path, monkeypatch, capsys):
    """`find` exists to be piped. A `§` line on its stdout would be read as a
    filename — the same argument ADR-DIR-LIST decision 12 made for the
    archived marker."""
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_find(_args()) == 0
    assert capsys.readouterr().out == "docs/mesh.md\n"


def test_find_json_carries_headings_because_it_shares_as_dict(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_find(_args(json=True)) == 0
    payload = json_mod.loads(capsys.readouterr().out)
    assert payload["results"][0]["headings"] == [
        "Rollback procedure",
        "Rollback and recovery",
        "A rollback rollback rollback story",
    ]


# -- the law this must not break -----------------------------------------


def test_headings_do_not_change_the_ranking(tmp_path, monkeypatch, capsys):
    """The scores and the order are identical with headings present and with
    them removed. That is the whole claim: this is display, applied after
    `run_query` returns, on a list both candidate generators already agree on.
    """
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_args(json=True)) == 0
    with_headings = json_mod.loads(capsys.readouterr().out)["results"]

    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path, _record(phrases=[])))
    assert cmd_ask(_args(json=True)) == 0
    without = json_mod.loads(capsys.readouterr().out)["results"]

    strip = lambda rs: [{k: v for k, v in r.items() if k != "headings"} for r in rs]  # noqa: E731
    assert strip(with_headings) == strip(without)
