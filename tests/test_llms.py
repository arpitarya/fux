"""W-284 — `fux llms` renders llms.txt and llms-full.txt from the index (SR-LLMS).

What is pinned: the llms.txt shape (H1, blockquote, H2 lists, archived under
`## Optional`), the notes coming from the document's own frontmatter, `--full`
inlining only prose `file:` documents without their frontmatter, determinism,
and the repository's own two committed files being current.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.llms import render, select

ROOT = Path(__file__).resolve().parents[1]


def _records(*rows):
    return {
        doc_id: {"id": doc_id, "loc": doc_id.split(":", 1)[1], "title": title, **extra}
        for doc_id, title, extra in rows
    }


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "---\ntype: Guide\ndescription: \"How A works.\"\n---\n\n# A\n\nbody of a\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "page.html").write_text("<p>html</p>\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("No heading here.\n", encoding="utf-8")
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "x.md").write_text("# X\n", encoding="utf-8")
    index = tmp_path / ".fux" / "index"
    index.mkdir(parents=True)
    (index / "REGISTER").write_text(
        "# fux.register.v2\trules=5\n# loc\tsha\tdecoder\t[k=v ...]\n"
        "README.md\tx\tprose\ndocs/a.md\tx\tprose\ndocs/page.html\tx\thtml@sha:1\nold/x.md\tx\tprose\tarchived=true\n",
        encoding="utf-8",
    )
    records = _records(
        ("file:README.md", "Read me", {}),
        ("file:docs/a.md", "A", {}),
        ("file:docs/page.html", "Page", {}),
        ("file:old/x.md", "X", {"archived": True}),
        ("url:https://example.com/p", "Remote", {}),
    )
    return tmp_path, records


def _render(tree, **kw):
    root, records = tree
    args = {"prefixes": [], "title": "Demo", "summary": "One line.", "base": "", "full": False} | kw
    return render(root, records, **args)


def test_llms_txt_shape(tree):
    text = _render(tree)
    assert text.startswith("# Demo\n\n> One line.\n\n## Overview\n\n- [Read me](README.md)\n")
    assert "## docs\n\n- [A](docs/a.md): How A works.\n- [Page](docs/page.html)\n" in text
    # A URL document is listed by its own URL and never fetched.
    assert "## example.com\n\n- [Remote](https://example.com/p)\n" in text
    # Archived documents are history: the spec's skippable section, last.
    assert text.rstrip().endswith("## Optional\n\n- [X](old/x.md)")


def test_base_url_prefixes_file_links_only_and_quotes_them(tree):
    root, records = tree
    records["file:docs/a b.md"] = {"id": "file:docs/a b.md", "loc": "docs/a b.md", "title": "Spaced"}
    text = render(root, records, prefixes=["docs/"], title="T", summary="", base="https://h/x/", full=False)
    assert "- [Spaced](https://h/x/docs/a%20b.md)" in text
    assert "> " not in text


def test_full_inlines_prose_file_documents_without_frontmatter(tree):
    text = _render(tree, full=True)
    assert "---\n\nSource: docs/a.md\n\n# A\n\nbody of a\n" in text
    assert "type: Guide" not in text
    # No H1 in the body: the title is supplied.
    assert "---\n\n# Read me\n\nSource: README.md\n\nNo heading here.\n" in text
    assert "<p>html</p>" not in text, "a non-prose document is listed, never inlined"
    assert "# X" not in text.split("## Optional")[-1], "an archived document is not inlined"


def test_in_selects_by_prefix_and_an_empty_selection_refuses(tree):
    root, records = tree
    assert [r["loc"] for r in select(records, ["docs/"])] == ["docs/a.md", "docs/page.html"]
    with pytest.raises(FuxError, match="no indexed document"):
        render(root, records, prefixes=["nope/"], title="T", summary="", base="", full=False)


def test_render_is_deterministic(tree):
    root, records = tree
    reversed_records = dict(reversed(list(records.items())))
    assert _render(tree, full=True) == render(
        root, reversed_records, prefixes=[], title="Demo", summary="One line.", base="", full=True
    )


def _generator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("gen_llms", ROOT / "scripts" / "gen-llms.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", ["llms.txt", "llms-full.txt"])
def test_the_repositorys_own_files_are_current(name):
    """This repo's committed pair is `just llms`'s output. Stale → run `just llms`."""
    committed = (ROOT / name).read_text(encoding="utf-8")
    assert committed == _generator().rendered()[name], f"{name} is stale — run `just llms`"


def test_the_verb_runs_end_to_end():
    out = subprocess.run(
        [sys.executable, "-m", "fux.cli", "llms", "--in", "docs/GLOSSARY.md", "--title", "G"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    assert out.startswith("# G\n\n## docs\n\n- [Glossary](docs/GLOSSARY.md): ")
