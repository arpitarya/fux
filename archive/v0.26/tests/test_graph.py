"""Edge extraction and node payloads — deterministic, no model, no invention."""

from __future__ import annotations

import sqlite3

from fux.graph import Edge, edges_from_scans, scan_document
from fux.graph.extract import EXTRACTED
from fux.index import sqlstore

from test_ingest import make_project, run


def scan(body: str, meta: dict | None = None, entry: dict | None = None) -> dict:
    return scan_document(body, meta or {}, entry or {})


def kinds(edges, kind):
    return sorted((e.src, e.dst) for e in edges if e.kind == kind)


# -- references ------------------------------------------------------------


def test_relative_links_become_references():
    scans = {
        "docs/a.md": scan("See [b](b.md) and [deep](sub/c.md)."),
        "docs/b.md": scan("# B"),
        "docs/sub/c.md": scan("# C"),
    }
    assert kinds(edges_from_scans(scans), "references") == [
        ("docs/a.md", "docs/b.md"), ("docs/a.md", "docs/sub/c.md")
    ]


def test_parent_traversal_resolves():
    scans = {"docs/sub/a.md": scan("[up](../b.md)"), "docs/b.md": scan("# B")}
    assert kinds(edges_from_scans(scans), "references") == [("docs/sub/a.md", "docs/b.md")]


def test_root_relative_links_resolve():
    scans = {"docs/a.md": scan("[x](/notes/x.md)"), "notes/x.md": scan("# X")}
    assert kinds(edges_from_scans(scans), "references") == [("docs/a.md", "notes/x.md")]


def test_directory_links_resolve_to_the_index():
    scans = {"docs/a.md": scan("[dir](sub/)"), "docs/sub/index.md": scan("# Index")}
    assert kinds(edges_from_scans(scans), "references") == [
        ("docs/a.md", "docs/sub/index.md")
    ]


def test_dangling_links_create_no_edge_and_no_node():
    """A link to nothing is a fact about the source, not a relationship."""
    edges = edges_from_scans({"docs/a.md": scan("[gone](nowhere.md)")})
    assert edges == []


def test_external_links_are_ignored_unless_crawled():
    scans = {"docs/a.md": scan("[ext](https://example.com/page) [mail](mailto:x@y.z)")}
    assert edges_from_scans(scans) == []

    scans["web:example.com/page"] = scan("# Page", entry={"url": "https://example.com/page"})
    assert kinds(edges_from_scans(scans), "references") == [
        ("docs/a.md", "web:example.com/page")
    ]


def test_anchors_and_self_links_are_dropped():
    scans = {"docs/a.md": scan("[here](#section) and [self](a.md)")}
    assert edges_from_scans(scans) == []


def test_link_titles_do_not_break_parsing():
    scans = {"docs/a.md": scan('[b](b.md "the title")'), "docs/b.md": scan("# B")}
    assert kinds(edges_from_scans(scans), "references") == [("docs/a.md", "docs/b.md")]


# -- cites -----------------------------------------------------------------


def test_links_under_a_citations_heading_become_cites():
    body = "# A\n\nSee [b](b.md).\n\n## Citations\n\n- [c](c.md)\n"
    scans = {"docs/a.md": scan(body), "docs/b.md": scan("# B"), "docs/c.md": scan("# C")}
    edges = edges_from_scans(scans)
    assert kinds(edges, "references") == [("docs/a.md", "docs/b.md")]
    assert kinds(edges, "cites") == [("docs/a.md", "docs/c.md")]


def test_citation_section_ends_at_the_next_peer_heading():
    body = "## Citations\n\n[c](c.md)\n\n## Notes\n\n[b](b.md)\n"
    scans = {"docs/a.md": scan(body), "docs/b.md": scan("# B"), "docs/c.md": scan("# C")}
    edges = edges_from_scans(scans)
    assert kinds(edges, "cites") == [("docs/a.md", "docs/c.md")]
    assert kinds(edges, "references") == [("docs/a.md", "docs/b.md")]


def test_references_and_sources_headings_also_count():
    for heading in ("## References", "# Sources", "### citations"):
        scans = {"docs/a.md": scan(f"{heading}\n\n[b](b.md)\n"), "docs/b.md": scan("# B")}
        assert kinds(edges_from_scans(scans), "cites") == [("docs/a.md", "docs/b.md")]


# -- crawled_from and tagged ----------------------------------------------


def test_crawl_parentage_becomes_an_edge():
    scans = {
        "web:x.test/root": scan("# Root", entry={"url": "https://x.test/root"}),
        "web:x.test/child": scan(
            "# Child", entry={"url": "https://x.test/child", "parent": "https://x.test/root"}
        ),
    }
    assert kinds(edges_from_scans(scans), "crawled_from") == [
        ("web:x.test/child", "web:x.test/root")
    ]


def test_tags_become_tag_nodes_not_pairwise_edges():
    """N docs sharing a tag cost N edges, not N² — and still connect in two hops."""
    scans = {
        f"docs/{i}.md": scan("# D", meta={"tags": ["Alpha", "beta"]}) for i in range(5)
    }
    edges = edges_from_scans(scans)
    tagged = kinds(edges, "tagged")
    assert len(tagged) == 10  # 5 docs × 2 tags, not 5×4 doc-pairs
    assert ("docs/0.md", "tag:alpha") in tagged  # normalized to lowercase


def test_comma_separated_tags_are_accepted():
    scans = {"docs/a.md": scan("# A", meta={"tags": "one, two"})}
    assert kinds(edges_from_scans(scans), "tagged") == [
        ("docs/a.md", "tag:one"), ("docs/a.md", "tag:two")
    ]


# -- determinism and grade -------------------------------------------------


def test_edges_are_sorted_deduped_and_extracted_grade():
    scans = {"docs/a.md": scan("[b](b.md) [b again](b.md)"), "docs/b.md": scan("# B")}
    edges = edges_from_scans(scans)
    assert edges == [Edge("docs/a.md", "references", "docs/b.md", EXTRACTED)]
    assert edges == sorted(edges)


def test_extraction_is_order_independent():
    body = "[b](b.md)"
    forward = edges_from_scans({"docs/a.md": scan(body), "docs/b.md": scan("# B")})
    reverse = edges_from_scans({"docs/b.md": scan("# B"), "docs/a.md": scan(body)})
    assert forward == reverse


# -- node payloads ---------------------------------------------------------


def test_outline_lists_headings_in_order():
    out = scan("# Top\n\ntext\n\n## One\n\nmore\n\n### Deep\n")["outline"]
    assert out == "Top › One › Deep"


def test_top_terms_drop_stopwords_and_tie_break_alphabetically():
    terms = scan("# T\n\nzebra zebra apple apple the the the of of")["top_terms"].split()
    assert terms[:2] == ["apple", "zebra"]  # equal counts → alphabetical
    assert "the" not in terms and "of" not in terms


def test_empty_document_yields_empty_payload():
    payload = scan("")
    assert payload["outline"] == "" and payload["top_terms"] == ""


# -- persistence -----------------------------------------------------------


def test_ingest_persists_edges_and_payloads(tmp_path, monkeypatch):
    make_project(tmp_path)
    (tmp_path / "docs" / "guide.md").write_text(
        "---\ntitle: The Guide\ntags: [howto]\n---\n"
        "# Guide\n\nSee [notes](sub/notes.txt).\n\n## Citations\n\n- [cfg](../data/cfg.json)\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8") + '\n[index]\nformat = "sqlite"\n',
        encoding="utf-8",
    )
    run(tmp_path, monkeypatch, "ingest")

    conn = sqlite3.connect(sqlstore.db_path(tmp_path))
    try:
        edges = {(r[0], r[1], r[2]) for r in conn.execute("SELECT src, kind, dst FROM edges")}
        assert ("docs/guide.md", "references", "docs/sub/notes.txt") in edges
        assert ("docs/guide.md", "cites", "data/cfg.json") in edges
        assert ("docs/guide.md", "tagged", "tag:howto") in edges
        assert all(r[0] == EXTRACTED for r in conn.execute("SELECT grade FROM edges"))

        outline, top_terms = conn.execute(
            "SELECT outline, top_terms FROM docs WHERE doc_id='docs/guide.md'"
        ).fetchone()
        assert "Guide" in outline and top_terms
    finally:
        conn.close()


def test_edges_survive_an_unchanged_reingest(tmp_path, monkeypatch):
    make_project(tmp_path)
    (tmp_path / "docs" / "guide.md").write_text(
        "# Guide\n\n[notes](sub/notes.txt)\n", encoding="utf-8"
    )
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8") + '\n[index]\nformat = "sqlite"\n',
        encoding="utf-8",
    )
    run(tmp_path, monkeypatch, "ingest")
    before = sqlstore.load_edges(tmp_path)
    run(tmp_path, monkeypatch, "ingest")  # everything unchanged: reuse path
    assert sqlstore.load_edges(tmp_path) == before
    assert before, "the reuse path must not silently drop the graph"


def test_a_new_document_resolves_a_previously_dangling_link(tmp_path, monkeypatch):
    """Why scans are re-resolved every run rather than cached per doc."""
    make_project(tmp_path)
    (tmp_path / "docs" / "guide.md").write_text(
        "# Guide\n\n[later](later.md)\n", encoding="utf-8"
    )
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8") + '\n[index]\nformat = "sqlite"\n',
        encoding="utf-8",
    )
    run(tmp_path, monkeypatch, "ingest")
    assert sqlstore.load_edges(tmp_path) == []

    (tmp_path / "docs" / "later.md").write_text("# Later\n", encoding="utf-8")
    run(tmp_path, monkeypatch, "ingest")
    assert ("docs/guide.md", "references", "docs/later.md", EXTRACTED) in sqlstore.load_edges(
        tmp_path
    )
