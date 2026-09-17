from __future__ import annotations

from fux.ingest.edges import basename_index, resolve, scan
from fux.ingest.parse import parse
from fux.store import term_hash


def _bare(edges):
    """Edges with W-168's anchor keys stripped.

    Every test below this line is about *resolution* — which target a link
    reaches, which are dropped, what order they come out in — and none of it
    moved when the anchor keys arrived. Stripping them here keeps those
    assertions saying what they were written to say; the anchor keys have
    their own tests at the bottom of the file.
    """
    return [{k: v for k, v in e.items() if k not in ("at", "al")} for e in edges]


def test_scan_extracts_links_code_spans_and_tags():
    doc = parse(
        b'---\ntags: [alpha, Beta]\n---\n'
        b"See [the guide](../guide.md) and `tools/run.py`.\n"
    )
    s = scan(doc)
    assert s.links == [("the guide", "../guide.md")]
    assert s.code_spans == ["tools/run.py"]
    assert s.tags == ["alpha", "beta"]


def test_resolve_ref_relative_link():
    known = {"file:docs/a.md", "file:docs/guide.md"}
    doc = parse(b"See [it](guide.md).\n")
    s = scan(doc)
    edges = _bare(resolve("file:docs/a.md", s, known, basename_index(known), term_hash))
    assert {"kind": "ref", "dst": "file:docs/guide.md", "grade": 10} in edges


def test_resolve_ref_dotdot_relative_link():
    known = {"file:docs/sub/a.md", "file:docs/guide.md"}
    doc = parse(b"See [it](../guide.md).\n")
    s = scan(doc)
    edges = _bare(resolve("file:docs/sub/a.md", s, known, basename_index(known), term_hash))
    assert {"kind": "ref", "dst": "file:docs/guide.md", "grade": 10} in edges


def test_dangling_ref_is_dropped():
    known = {"file:docs/a.md"}
    doc = parse(b"See [it](nowhere.md).\n")
    s = scan(doc)
    edges = _bare(resolve("file:docs/a.md", s, known, basename_index(known), term_hash))
    assert edges == []


def test_self_link_is_dropped():
    known = {"file:docs/a.md"}
    doc = parse(b"See [it](a.md).\n")
    s = scan(doc)
    edges = _bare(resolve("file:docs/a.md", s, known, basename_index(known), term_hash))
    assert edges == []


def test_external_link_is_ignored():
    known = {"file:docs/a.md"}
    doc = parse(b"See [it](https://example.com/x).\n")
    s = scan(doc)
    edges = _bare(resolve("file:docs/a.md", s, known, basename_index(known), term_hash))
    assert edges == []


def test_tag_edge():
    known = {"file:a.md"}
    doc = parse(b"---\ntags: [pruning]\n---\nbody\n")
    s = scan(doc)
    edges = _bare(resolve("file:a.md", s, known, basename_index(known), term_hash))
    assert edges == [{"kind": "tag", "dst": "tag:pruning", "grade": 10}]


def test_code_edge_exact_path_match():
    known = {"file:a.md", "file:tools/run.py"}
    doc = parse(b"See `tools/run.py`.\n")
    s = scan(doc)
    edges = _bare(resolve("file:a.md", s, known, basename_index(known), term_hash))
    assert {"kind": "code", "dst": "file:tools/run.py", "grade": 10} in edges


def test_code_edge_ambiguous_basename_match():
    known = {"file:a.md", "file:tools/run.py"}
    doc = parse(b"See `run.py`.\n")
    s = scan(doc)
    edges = _bare(resolve("file:a.md", s, known, basename_index(known), term_hash))
    assert {"kind": "code", "dst": "file:tools/run.py", "grade": 8} in edges


def test_code_edge_multiple_basename_matches_dropped():
    known = {"file:a.md", "file:tools/run.py", "file:other/run.py"}
    doc = parse(b"See `run.py`.\n")
    s = scan(doc)
    edges = _bare(resolve("file:a.md", s, known, basename_index(known), term_hash))
    assert edges == []


def test_index_md_readme_fallback_resolution():
    known = {"file:docs/sub/index.md", "file:a.md"}
    doc = parse(b"See [it](sub/).\n")
    s = scan(doc)
    edges = _bare(resolve("file:docs/a.md", s, known, basename_index(known), term_hash))
    assert {"kind": "ref", "dst": "file:docs/sub/index.md", "grade": 10} in edges


def test_resolve_is_deterministic_and_sorted():
    known = {"file:b.md", "file:a.md"}
    doc = parse(b"[a](a.md) [b](b.md)\n---\ntags: [z, a]\n")
    s = scan(doc)
    edges = _bare(resolve("file:x.md", s, known, basename_index(known), term_hash))
    assert edges == sorted(edges, key=lambda e: (e["kind"], e["dst"]))


def test_edges_have_no_duplicates_for_repeated_links():
    known = {"file:a.md", "file:b.md"}
    doc = parse(b"[x](b.md) and again [y](b.md)\n")
    s = scan(doc)
    edges = _bare(resolve("file:a.md", s, known, basename_index(known), term_hash))
    assert edges == [{"kind": "ref", "dst": "file:b.md", "grade": 10}]


# -- W-168 step 1: the anchor keys ------------------------------------------
#
# Option (c) of the three put to Arpit on 2026-09-15, and the one he took: the
# anchor words ride the EDGE, on the committed record of the document that
# WROTE them, and the per-target fold ranking needs is rebuilt at read time.


def test_anchor_text_is_captured():
    """The link's words survive `_LINK_RE` and reach the edge as hashed terms.

    They used to be discarded — group 1 was a non-capturing class — which is
    why the proposal's *"cost: small, edges are already extracted"* was half
    true: the edges were, the words were not.
    """
    known = {"file:a.md", "file:docs/ranking.md"}
    doc = parse(b"See [the ranking record](docs/ranking.md).\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known), term_hash)
    (edge,) = edges
    assert edge["dst"] == "file:docs/ranking.md"
    assert edge["at"] == {term_hash("rank"): 1, term_hash("record"): 1}
    assert edge["al"] == 2  # "the" is a stopword; "ranking" stems to "rank"


def test_repeated_links_merge_their_words_into_one_bag():
    """Two links B -> A are ONE edge, so their words are one bag.

    `edges` has always been deduplicated by `(kind, dst)`. If the anchor terms
    were not merged the same way, the second link's words would be silently
    dropped — the surviving edge would carry whichever text happened to come
    last in the document.
    """
    known = {"file:a.md", "file:b.md"}
    doc = parse(b"[alpha thing](b.md) and later [alpha other](b.md)\n")
    s = scan(doc)
    (edge,) = resolve("file:a.md", s, known, basename_index(known), term_hash)
    assert edge["at"] == {
        term_hash("alpha"): 2,
        term_hash("thing"): 1,
        term_hash("other"): 1,
    }
    assert edge["al"] == 4


def test_a_link_with_no_indexable_words_keeps_the_pre_anchor_shape():
    """Empty, punctuation-only or all-stopword text adds no keys at all.

    Absent rather than `{}`/`0`, for the reason `omit_when` exists one level
    up: a record's shape stays what it was, so nothing downstream has to learn
    a new empty case.
    """
    known = {"file:a.md", "file:b.md"}
    doc = parse(b"[](b.md)\n")
    s = scan(doc)
    (edge,) = resolve("file:a.md", s, known, basename_index(known), term_hash)
    assert edge == {"kind": "ref", "dst": "file:b.md", "grade": 10}


def test_only_ref_edges_carry_anchor_words():
    """A `tag`, `code` or `supersedes` edge has no link text and never gains a
    key — there is no anchor to take."""
    known = {"file:a.md", "file:tools/run.py"}
    doc = parse(b"---\ntags: [ops]\n---\nSee `tools/run.py`.\n")
    s = scan(doc)
    edges = resolve("file:a.md", s, known, basename_index(known), term_hash)
    assert edges, "the fixture must produce edges or this asserts nothing"
    for edge in edges:
        assert "at" not in edge and "al" not in edge, edge


def test_al_is_always_the_sum_of_at():
    """The redundancy `derive/_build.py` asserts, asserted at the source too.

    `al` exists only so `query/scan.py` can read a document's anchor length off
    raw bytes with one integer capture. Redundancy nothing checks is redundancy
    that drifts — and this one would drift into `avg_wlen`, a corpus-wide
    denominator, on the scan path alone.
    """
    known = {"file:a.md", "file:b.md", "file:c.md"}
    doc = parse(b"[one two three](b.md) [two](c.md) [two](b.md)\n")
    s = scan(doc)
    for edge in resolve("file:a.md", s, known, basename_index(known), term_hash):
        assert edge["al"] == sum(edge["at"].values())
