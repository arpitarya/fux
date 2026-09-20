"""The committed register — `.fux/index/REGISTER` (W-199 D4).

🔴 **The one property that makes a derived file safe to commit is byte-identity
across runs**, and it is the property a reviewer cannot see. Everything else
here is shape; `test_two_ingests_write_the_register_once` is the rule.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from fux.ingest import register


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A\n\nthe rota hands over Monday\n", encoding="utf-8")
    (docs / "b.md").write_text("# B\n\nthe dock closes at six\n", encoding="utf-8")
    return tmp_path


def _ingest(root: Path) -> None:
    from fux.ingest.run import run

    run(root)


# --- the rule ---------------------------------------------------------------

def test_two_ingests_write_the_register_once(tmp_path):
    """🔴 L3, and the whole argument for committing this file.

    The first run indexes every document and the second reuses every one — from
    identical sources. If any run-shaped value reached the file, these bytes
    would differ and the register would be a file that changes for no reason
    anybody can explain from the corpus.

    ⚠ **This is exactly why the ruling's `outcome` column is not here.**
    `indexed` then `reused` is what that column would have said on these two
    runs. See `ingest/register.py`'s docstring.
    """
    root = _repo(tmp_path)
    _ingest(root)
    first = register.path_for(root).read_bytes()
    _ingest(root)
    assert register.path_for(root).read_bytes() == first


def test_it_is_sorted_by_loc_whatever_order_the_records_arrive_in():
    rows = [
        register.Row(loc="z.md", kind="file", sha="s3", decoder="md@1"),
        register.Row(loc="a.md", kind="file", sha="s1", decoder="md@1"),
        register.Row(loc="m.md", kind="file", sha="s2", decoder="md@1"),
    ]
    body = register.render(rows).splitlines()[1:]
    assert [line.split("\t")[0] for line in body] == ["a.md", "m.md", "z.md"]
    assert register.render(rows) == register.render(list(reversed(rows)))


def test_the_header_is_part_of_the_bytes():
    """A reader must be able to name the columns without this module."""
    assert register.render([]).startswith(register.HEADER)


# --- what it holds, and what it must never hold -----------------------------

def test_it_names_every_indexed_document_and_nothing_else(tmp_path):
    root = _repo(tmp_path)
    _ingest(root)
    rows = register.read(root)
    assert set(rows) == {"docs/a.md", "docs/b.md"}
    assert all(r.kind == "file" for r in rows.values())
    assert all(r.sha for r in rows.values())


def test_it_carries_no_clock_and_no_run_id(tmp_path):
    """L3, asserted on the bytes rather than on the writer's intentions."""
    root = _repo(tmp_path)
    _ingest(root)
    text = register.path_for(root).read_text(encoding="utf-8")
    for forbidden in ("run_seq", "20", "T00:", "timestamp", "mtime"):
        if forbidden == "20":  # a sha may legitimately contain digits
            continue
        assert forbidden not in text


def test_it_never_grows_a_query_field():
    """🔴 [L8](../../records/0010_LAW-8-use-record.md) is the reason this file may
    be committed at all: it records what the CORPUS is, never who went looking.

    The moment a column names a question, a query or a reader, a committed path
    is carrying a use record — the one thing L8 forbids. The field list is
    asserted here so that adding one is a deliberate act with a failing test in
    front of it.
    """
    assert [f for f in register.Row.__dataclass_fields__] == [
        "loc", "kind", "sha", "decoder", "fetcher",
    ]


def test_a_url_row_carries_its_fetcher_and_a_file_row_does_not():
    rows = register.rows_from(
        [
            {"id": "url:https://x.test/a", "loc": "https://x.test/a", "sha": "s1", "src": "url"},
            {"id": "file:docs/a.md", "loc": "docs/a.md", "sha": "s2"},
        ],
        {"url:https://x.test/a": ("prose", "http@sha:abc"), "file:docs/a.md": ("md@1", None)},
    )
    by_loc = {r.loc: r for r in rows}
    assert by_loc["https://x.test/a"].fetcher == "http@sha:abc"
    assert by_loc["docs/a.md"].fetcher is None
    # `-` on the wire: absent and unknown are different, and the file says which.
    assert by_loc["docs/a.md"].rendered().endswith("\t-")


# --- it must never be able to fail a run ------------------------------------

def test_a_write_that_cannot_happen_is_swallowed(tmp_path, monkeypatch):
    """A register that can fail an ingest is worse than one that is a run
    behind — `fux doctor`'s `register` row reports the second, and nothing can
    report the first."""
    root = _repo(tmp_path)
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: (_ for _ in ()).throw(OSError("full")))
    register.write(root, [register.Row(loc="a", kind="file", sha="s", decoder="d")])


def test_a_truncated_register_reads_as_absent_not_as_a_failure(tmp_path):
    root = _repo(tmp_path)
    (root / ".fux" / "index").mkdir(parents=True, exist_ok=True)
    register.path_for(root).write_text("# loc\tkind\nnot\tenough\n", encoding="utf-8")
    assert register.read(root) == {}
