"""W-76 Phase 0 — the `fux build` nudge, and the three ways it must not misfire.

The note itself is four lines of code. What is worth testing is the contract
around it, which is the same one `_declare_pending` and `_declare_archived`
already carry and which two of them were given *after* a defect:

- **stdout is untouched.** `fux find` prints bare paths so it can pipe; a note
  on stdout is read by `xargs` as a filename. `--json` is a contract.
- **it never gates.** The answer comes back either way.
- **it points at the right command.** With no index at all the answer is
  `fux ingest`, and saying `fux build` would send someone down a path that
  cannot work.
"""

from __future__ import annotations

import json

import pytest

from fux.derive import build
from fux.query import _declare_no_accelerator
from fux.store import term_hash, write_index


def _rec(doc_id, title, terms, flen=(100,)) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "flen": list(flen),
        "edges": [],
    }


@pytest.fixture
def indexed(tmp_path):
    # tf is `[body, heading]` (v2 order — `store.TF_FIELDS`).
    write_index(tmp_path, [_rec("file:a.md", "Alpha", {term_hash("alpha"): [3, 1]})])
    return tmp_path


def test_it_fires_when_shards_exist_and_no_accelerator(indexed, capsys):
    _declare_no_accelerator(indexed)
    captured = capsys.readouterr()
    assert captured.out == "", "the nudge must never touch stdout"
    assert "fux build" in captured.err
    assert "results are identical either way" in captured.err, (
        "without this clause a reader assumes building might change their answers, "
        "which is the opposite of the differential law"
    )


def test_it_is_silent_once_the_accelerator_is_built(indexed, capsys):
    build(indexed)
    capsys.readouterr()
    _declare_no_accelerator(indexed)
    captured = capsys.readouterr()
    assert captured.err == "", "a built accelerator must produce no note"
    assert captured.out == ""


def test_it_is_silent_when_there_is_no_index_at_all(tmp_path, capsys):
    """The wrong-command case.

    With no shards the answer is `fux ingest`. Telling someone to run
    `fux build` here sends them to a command that will not help, which is
    worse than saying nothing.
    """
    _declare_no_accelerator(tmp_path)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_the_note_is_ascii_only(indexed, capsys):
    """A Windows console's default codepage cannot encode a fancy dash, and the
    process crashes on `print()` rather than degrading. Learned in v0.35.0 and
    written into every declaration since."""
    _declare_no_accelerator(indexed)
    err = capsys.readouterr().err
    assert err
    err.encode("ascii")  # raises UnicodeEncodeError if a fancy character crept in


def test_json_stdout_stays_parseable_with_the_note_present(indexed, capsys, monkeypatch):
    """The whole reason the note is on stderr: `--json` is a contract."""
    from fux.query import cmd_find

    # cmd_find has no `root` argument — it resolves via find_root() off cwd,
    # so the `indexed` fixture only takes effect once we're actually inside
    # it (else this would silently query whatever repo the tests happen to
    # run from instead of the fixture's shard). find_root() needs a marker
    # to anchor on.
    (indexed / ".git").mkdir()
    monkeypatch.chdir(indexed)

    class _Args:
        query = "alpha"
        top = 5
        json = True
        fast = False
        scan = False

    capsys.readouterr()
    cmd_find(_Args())
    captured = capsys.readouterr()
    json.loads(captured.out)  # raises if the note leaked onto stdout
    assert "fux build" in captured.err
