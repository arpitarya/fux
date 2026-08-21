"""The derived graph plane — built by `fux build`, refused when stale."""

from __future__ import annotations

import json

import pytest

from fux.derive import build
from fux.derive import format as fmt
from fux.errors import FuxError
from fux.graph import plane as plane_mod
from fux.store import term_hash, write_index


def _rec(doc_id, title, terms, edges=()) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "wlen": 20,
        "edges": list(edges),
    }


@pytest.fixture
def corpus(tmp_path):
    write_index(
        tmp_path,
        [
            _rec("file:a.md", "A", {term_hash("alpha"): [1, 2]},
                 [{"kind": "ref", "dst": "file:b.md", "grade": 10}]),
            _rec("file:b.md", "B", {term_hash("alpha"): [0, 1]},
                 [{"kind": "tag", "dst": "tag:ops", "grade": 10}]),
            _rec("file:c.md", "C", {term_hash("beta"): [1, 1]}),
        ],
    )
    build(tmp_path)
    return tmp_path


def test_build_writes_the_plane(corpus):
    plane = plane_mod.load(corpus)
    assert [e.dst for e in plane.graph.out_edges("file:a.md")] == ["file:b.md"]
    assert plane.community_of("file:a.md") == plane.community_of("file:b.md")


def test_a_document_with_no_edges_is_absent_from_the_graph(corpus):
    """Honest: `file:c.md` links to nothing, so it is in no community."""
    assert plane_mod.load(corpus).community_of("file:c.md") is None


def test_the_plane_is_part_of_the_deterministic_build(corpus):
    assert plane_mod.GRAPH_NAME in fmt.DETERMINISTIC_FILES


def test_the_plane_is_written_lf_only_regardless_of_host_os(corpus):
    """`write_text`'s platform-default newline translation would commit CRLF
    on Windows and LF everywhere else — this file is asserted byte-identical
    across two builds on two machines (ADR-GRAPH), so that would break the
    one axis it is actually checked across. `newline="\\n"` disables it.
    """
    raw = (fmt.runtime_dir(corpus) / plane_mod.GRAPH_NAME).read_bytes()
    assert b"\r" not in raw
    before = (fmt.runtime_dir(corpus) / plane_mod.GRAPH_NAME).read_bytes()
    build(corpus)
    assert (fmt.runtime_dir(corpus) / plane_mod.GRAPH_NAME).read_bytes() == before


def test_a_missing_plane_names_the_command_that_creates_it(tmp_path):
    with pytest.raises(FuxError, match="fux build"):
        plane_mod.load(tmp_path)


def test_a_schema_mismatch_is_refused_rather_than_misread(corpus):
    """The derived plane is disposable, so an old shape rebuilds — never guesses."""
    path = fmt.runtime_dir(corpus) / plane_mod.GRAPH_NAME
    payload = json.loads(path.read_text())
    payload["schema"] = "fux.graph.v0"
    path.write_text(json.dumps(payload))
    with pytest.raises(FuxError, match="fux build"):
        plane_mod.load(corpus)


def test_the_plane_carries_no_content_only_relationships(corpus):
    """L2, checked: the graph plane holds ids and grades, never document text."""
    text = (fmt.runtime_dir(corpus) / plane_mod.GRAPH_NAME).read_text()
    payload = json.loads(text)
    assert set(payload) == {"schema", "edges", "communities"}
    for edge in payload["edges"]:
        assert len(edge) == 4 and isinstance(edge[3], int)
