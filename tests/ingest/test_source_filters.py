"""The two filters that decide what is a document: `!` exclusions and types.

W-45 (verdict E) and W-55 (verdict G), which landed as one grammar change
because they modify one file's grammar. The property that matters most is
**visibility**: every file the walker declines is reported with a reason, since
an invisible filter is the failure both items were opened about.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest.gitdir import (
    DEFAULT_TYPES,
    TypeFilter,
    read_types,
    source_dirs,
    source_excludes,
    walk_sources,
)
from fux.ingest.sourcelist import DIRS, TYPES, URLS, glob_match, parse


# -- the glob matcher ------------------------------------------------------


@pytest.mark.parametrize(
    "pattern,path,expected",
    [
        ("work/regression/*/evidence", "work/regression/r1/evidence", True),
        # `*` must NOT cross a slash — this is why fnmatch is not used.
        ("work/regression/*/evidence", "work/regression/a/b/evidence", False),
        ("work/regression/**/evidence", "work/regression/a/b/evidence", True),
        ("*.md", "docs/deep/a.md", True),       # no slash -> matches the basename
        ("*.md", "docs/a.json", False),
        ("docs/*.md", "docs/a.md", True),
        ("docs/*.md", "other/a.md", False),     # a slash -> anchored at the root
        ("*.min.md", "a.min.md", True),
        ("a?.md", "ab.md", True),
        ("a?.md", "a/b.md", False),             # `?` does not cross a slash either
    ],
)
def test_glob_semantics(pattern, path, expected):
    assert glob_match(pattern, path) is expected


# -- the `!` grammar -------------------------------------------------------


def test_an_exclusion_parses_with_its_prefix_stripped():
    (entry,) = [e for e in parse("docs\n!docs/gen\n", DIRS, origin="t") if e.exclude]
    assert entry.value == "docs/gen"


def test_exclusions_sort_after_includes_so_file_order_cannot_matter():
    """L3 applied to config: the same set in any order is the same result."""
    a = parse("docs\n!docs/gen\nwork\n", DIRS, origin="t")
    b = parse("!docs/gen\nwork\ndocs\n", DIRS, origin="t")
    assert [(e.exclude, e.value) for e in a] == [(e.exclude, e.value) for e in b]


def test_an_exclusion_carries_no_attributes():
    """`archived=true` describes a directory being indexed; this removes one."""
    with pytest.raises(FuxError, match="exclusion carries no attributes"):
        parse("!docs/gen archived=true\n", DIRS, origin="t")


def test_there_is_no_un_exclude():
    with pytest.raises(FuxError, match="not an un-exclude"):
        parse("!!docs/gen\n", DIRS, origin="t")


def test_a_bare_bang_is_an_error():
    with pytest.raises(FuxError, match="no pattern after it"):
        parse("!\n", DIRS, origin="t")


def test_the_url_list_has_no_exclusions_because_there_is_nothing_to_subtract():
    with pytest.raises(FuxError, match="means nothing in `urls`"):
        parse("!https://x.test/a\n", URLS, origin="t")


def test_an_include_and_its_exclusion_do_not_collapse_into_one_entry():
    """`docs` and `!docs` contradict; collapsing them would pick a winner."""
    entries = parse("docs\n!docs\n", DIRS, origin="t")
    assert sorted((e.exclude, e.value) for e in entries) == [(False, "docs"), (True, "docs")]


# -- the type list ---------------------------------------------------------


def test_types_take_no_attributes_at_all():
    with pytest.raises(FuxError, match="unknown attribute"):
        parse("*.md archived=true\n", TYPES, origin="t")


def test_a_trailing_slash_in_types_is_refused():
    """Almost certainly someone reaching for `dirs`; matching nothing is worse."""
    with pytest.raises(FuxError, match="use `dirs` for a tree"):
        parse("docs/\n", TYPES, origin="t")


def test_an_absent_types_file_means_the_built_in_default(tmp_path):
    """Not 'everything' — that was the defect — and not 'nothing' either."""
    types = read_types(tmp_path)
    assert types.default and types.allow == DEFAULT_TYPES


def test_the_default_admits_prose_and_every_decodable_format():
    """⚠ **Widened 2026-08-26 on Arpit's ruling** — *"all the ones which have a
    decoder"*. The default was six prose globs; it is now those plus every
    extension a **built-in** decoder claims.

    ⚠ **`.svg`, `.png`, `.jpg`/`.jpeg`, `.gif` and `.jsonl` moved from the
    "stays out" list to the "admitted" one on 2026-08-29** — `svgdoc`,
    `imagedoc` and `jsonldoc` shipped as built-ins the same day, reversing the
    SVG half of ADR-TYPES decision 5 (see `docs/adr/0031_types-list.md`).

    What still stays out is the point of the assertion below: source code,
    shell scripts and extensionless files have no decoder, so they remain
    exactly as far outside the default as ADR-TYPES verdict G left them.
    """
    types = TypeFilter(allow=DEFAULT_TYPES)
    for name in ("a.md", "a.markdown", "a.txt", "a.rst", "a.adoc", "a.org"):
        assert types.accepts(f"docs/{name}"), name
    for name in ("a.json", "a.html", "a.docx", "a.pdf", "a.yaml", "a.eml", "a.ipynb"):
        assert types.accepts(f"docs/{name}"), name
    for name in ("a.svg", "a.png", "a.jpg", "a.jpeg", "a.gif", "a.jsonl"):
        assert types.accepts(f"docs/{name}"), name
    for name in ("a.sh", "a.py", "a.mermaid", "LICENSE", "Makefile"):
        assert not types.accepts(f"docs/{name}"), name


def test_the_default_never_grows_from_a_consumer_decoder(tmp_path):
    """A default derived from the live registry would mean **adding a decoder
    silently starts indexing a new file type**. What counts as a document has
    to stay a committed line a human wrote in `.fux/sources/types`.
    """
    decoders = tmp_path / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    (decoders / "logdoc.py").write_text(
        "EXTENSIONS = ('.log',)\ndef decode(raw, rel_path):\n    return '# log'\n"
    )
    assert "*.log" not in DEFAULT_TYPES
    assert not TypeFilter(allow=DEFAULT_TYPES).accepts("app.log")


def test_a_types_file_replaces_the_default_rather_than_extending_it(tmp_path):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "types").write_text("*.rst\n", encoding="utf-8")
    types = read_types(tmp_path)
    assert not types.default
    assert types.accepts("a.rst") and not types.accepts("a.md")


def test_a_bang_line_subtracts_from_the_allowlist(tmp_path):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "types").write_text("*.md\n!*.gen.md\n", encoding="utf-8")
    types = read_types(tmp_path)
    assert types.accepts("a.md") and not types.accepts("a.gen.md")


def test_a_types_file_with_no_positive_pattern_is_refused(tmp_path):
    """An empty index looks like a broken engine, so say so instead."""
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "types").write_text("# nothing\n!*.md\n", encoding="utf-8")
    with pytest.raises(FuxError, match="nothing would be indexed"):
        read_types(tmp_path)


# -- the walk: three conditions, and every rejection is visible ------------


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "docs" / "data.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "work" / "regression" / "r1" / "evidence").mkdir(parents=True)
    (tmp_path / "work" / "regression" / "r1" / "report.md").write_text("# R\n", encoding="utf-8")
    (tmp_path / "work" / "regression" / "r1" / "evidence" / "n.md").write_text("# N\n", encoding="utf-8")
    return tmp_path


def test_all_three_conditions_apply_together(tree):
    walked, skipped = walk_sources(
        tree,
        ["docs", "work"],
        excludes=["work/regression/*/evidence"],
        types=TypeFilter(allow=DEFAULT_TYPES),
    )
    # `docs/data.json` is now WALKED, not skipped — the 2026-08-26 widening.
    assert [w.rel_path for w in walked] == [
        "docs/a.md",
        "docs/data.json",
        "work/regression/r1/report.md",
    ]
    assert {s.rel_path: s.reason for s in skipped} == {
        "work/regression/r1/evidence/n.md": "excluded by !work/regression/*/evidence",
    }


def test_an_exclusion_removes_a_whole_tree_not_just_a_matching_file(tree):
    """One line excludes a directory and everything under it — the only reading
    under which excluding a tree is one line rather than one line per file."""
    (tree / "work" / "regression" / "r1" / "evidence" / "deep").mkdir()
    (tree / "work" / "regression" / "r1" / "evidence" / "deep" / "x.md").write_text("# X\n")
    walked, _ = walk_sources(tree, ["work"], excludes=["work/regression/*/evidence"])
    assert not any("evidence" in w.rel_path for w in walked)


def test_every_rejection_is_reported_with_a_reason(tree):
    """The property both items were opened about: no invisible filtering."""
    _, skipped = walk_sources(
        tree, ["docs", "work"],
        excludes=["work/regression/*/evidence"],
        types=TypeFilter(allow=DEFAULT_TYPES),
    )
    assert all(s.reason for s in skipped)


def test_no_filters_means_the_old_behaviour(tree):
    """The defaults are 'nothing excluded, everything allowed', so a caller
    exercising one condition is not silently subject to the other."""
    walked, skipped = walk_sources(tree, ["docs", "work"])
    assert len(walked) == 4 and skipped == []


def test_the_accessors_split_includes_from_exclusions(tmp_path):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "dirs").write_text(
        "docs\nwork\n!work/regression/*/evidence\n", encoding="utf-8"
    )
    rel = ".fux/sources/dirs"
    assert source_dirs(tmp_path, rel) == ["docs", "work"]
    assert source_excludes(tmp_path, rel) == ["work/regression/*/evidence"]
