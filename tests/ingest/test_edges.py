from __future__ import annotations

from fux.ingest.edges import basename_index, resolve, scan
from fux.ingest.parse import parse


def test_scan_extracts_links_code_spans_and_tags():
    doc = parse(
        b'---\ntags: [alpha, Beta]\n---\n'
        b"See [the guide](../guide.md) and `tools/run.py`.\n"
    )
    s = scan(doc)
    assert s.links == ["../guide.md"]
    assert s.code_spans == ["tools/run.py"]
    assert s.tags == ["alpha", "beta"]


def test_resolve_ref_relative_link():
    known = {"file:docs/a.md", "file:docs/guide.md"}
    doc = parse(b"See [it](guide.md).\n")
    s = scan(doc)
    edges = resolve("file:docs/a.md", s, known, basename_index(known))
    assert {"kind": "ref", "dst": "file:docs/guide.md", "grade": 10} in edges


def test_resolve_ref_dotdot_relative_link():
    known = {"file:docs/sub/a.md", "file:docs/guide.md"}
    doc = parse(b"See [it](../guide.md).\n")
    s = scan(doc)
    edges = resolve("file:docs/sub/a.md", s, known, basename_index(known))
    assert {"kind": "ref", "dst": "file:docs/guide.md", "grade": 10} in edges


def test_dangling_ref_is_dropped():
    known = {"file:docs/a.md"}
    doc = parse(b"See [it](nowhere.md).\n")
    s = scan(doc)
    edges = resolve("file:docs/a.md", s, known, basename_index(known))
    assert edges == []


def test_self_link_is_dropped():
    known = {"file:docs/a.md"}
    doc = parse(b"See [it](a.md).\n")
    s = scan(doc)
    edges = resolve("file:docs/a.md", s, known, basename_index(known))
    assert edges == []


def test_external_link_is_ignored():
    known = {"file:docs/a.md"}
    doc = parse(b"See [it](https://example.com/x).\n")
    s = scan(doc)
    edges = resolve("file:docs/a.md", s, known, basename_index(known))
    assert edges == []


def test_tag_edge():
    known = {"file:a.md"}
    doc = parse(b"---\ntags: [pruning]\n---\nbody\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known))
    assert edges == [{"kind": "tag", "dst": "tag:pruning", "grade": 10}]


def test_code_edge_exact_path_match():
    known = {"file:a.md", "file:tools/run.py"}
    doc = parse(b"See `tools/run.py`.\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known))
    assert {"kind": "code", "dst": "file:tools/run.py", "grade": 10} in edges


def test_code_edge_ambiguous_basename_match():
    known = {"file:a.md", "file:tools/run.py"}
    doc = parse(b"See `run.py`.\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known))
    assert {"kind": "code", "dst": "file:tools/run.py", "grade": 8} in edges


def test_code_edge_multiple_basename_matches_dropped():
    known = {"file:a.md", "file:tools/run.py", "file:other/run.py"}
    doc = parse(b"See `run.py`.\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known))
    assert edges == []


def test_index_md_readme_fallback_resolution():
    known = {"file:docs/sub/index.md", "file:a.md"}
    doc = parse(b"See [it](sub/).\n")
    s = scan(doc)
    edges = resolve("file:docs/a.md", s, known, basename_index(known))
    assert {"kind": "ref", "dst": "file:docs/sub/index.md", "grade": 10} in edges


def test_resolve_is_deterministic_and_sorted():
    known = {"file:b.md", "file:a.md"}
    doc = parse(b"[a](a.md) [b](b.md)\n---\ntags: [z, a]\n")
    s = scan(doc)
    edges = resolve("file:x.md", s, known, basename_index(known))
    assert edges == sorted(edges, key=lambda e: (e["kind"], e["dst"]))


def test_edges_have_no_duplicates_for_repeated_links():
    known = {"file:a.md", "file:b.md"}
    doc = parse(b"[x](b.md) and again [y](b.md)\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known))
    assert edges == [{"kind": "ref", "dst": "file:b.md", "grade": 10}]
