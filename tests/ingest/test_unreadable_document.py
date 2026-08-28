"""One unreadable document must not end the ingest.

**Found by RUNNING `tests_e2e/` on a real 3.11 install** (W-87 P5), so it is
gated here — CLAUDE.md's two-strikes rule. The unit suite had proved every
*part* of the W-86 P6 drop-rather-than-raise path: the decoder returns `None`,
the file is written to the committed queue with its reason, and `file_shas`
deliberately skips it. What nothing covered was the record loop, which still
iterated **every walked file** and reached `file_shas[doc_id]` for the one
document the parse plane had just dropped.

The result was the exact failure P6 exists to prevent, inverted: a single
`.pdf` nothing could decode raised `KeyError` and killed the whole run.
"""

from __future__ import annotations

from pathlib import Path

from importlib import import_module

from fux.ingest.queue import read as read_queue

# ⚠ `from fux.ingest import run` binds the re-exported FUNCTION, not the module
# -- a trap this repo has now hit twice. Import the module by name.
run_mod = import_module("fux.ingest.run")
from fux.store import read_index


def _corpus(root: Path) -> None:
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    (docs / "pruning.md").write_text(
        "# Why pruning failed\n\nThe gate measured static pruning twice.\n", encoding="utf-8"
    )


def _unreadable(root: Path, name: str = "architecture.pdf") -> None:
    """An allowed TYPE that no decoder can read.

    ⚠ `.pdf` is in `DEFAULT_TYPES`, so the walker admits it and the *content*
    skips (`empty`, `binary`, `non-utf8`) do not catch it — this text decodes
    as UTF-8 perfectly well. It is only the decoder that says no, which is why
    this case reaches the record loop at all.
    """
    (root / "docs" / name).write_bytes(b"%PDF-1.4 not really a pdf\n")


def test_an_undecodable_document_does_not_end_the_ingest(tmp_path):
    _corpus(tmp_path)
    _unreadable(tmp_path)

    report = run_mod.run(tmp_path)

    assert report is not None, "the run completed rather than raising"
    assert report.doc_count == 1, "the readable document is still indexed"


def test_the_undecodable_document_gets_no_record(tmp_path):
    """Not merely 'does not crash' — it must not appear as a document either.

    A record with no extraction behind it would rank on its filename alone,
    which is the W-55 defect arriving through the decoder plane.
    """
    _corpus(tmp_path)
    _unreadable(tmp_path)
    run_mod.run(tmp_path)

    ids = _indexed_ids(tmp_path)
    assert "file:docs/pruning.md" in ids
    assert "file:docs/architecture.pdf" not in ids


def test_it_is_written_to_the_queue_instead(tmp_path):
    """Dropped, not forgotten. The queue is the record that a model is owed."""
    _corpus(tmp_path)
    _unreadable(tmp_path)
    run_mod.run(tmp_path)

    entries = {entry.doc_id: entry for entry in read_queue(tmp_path)}
    assert "file:docs/architecture.pdf" in entries
    assert entries["file:docs/architecture.pdf"].reason, "the reason is not blank"


def test_a_corpus_that_is_ENTIRELY_unreadable_still_completes(tmp_path):
    """The degenerate end of the same bug.

    With no readable document at all there is no `parsed` entry to mask the
    defect, and every walked file takes the missing branch.
    """
    _corpus(tmp_path)
    (tmp_path / "docs" / "pruning.md").unlink()
    _unreadable(tmp_path, "a.pdf")
    _unreadable(tmp_path, "b.pdf")

    report = run_mod.run(tmp_path)

    assert report is not None
    assert report.doc_count == 0
    assert len(list(read_queue(tmp_path))) == 2


def test_the_record_loop_never_indexes_more_than_the_parse_plane_kept(tmp_path):
    """The invariant, stated where a future edit would break it.

    `file_shas`, `extracted`, `scans` and the record loop are four collections
    keyed by doc id, and three of them are already narrowed to `parsed`. This
    asserts the fourth agrees rather than asserting the symptom, so widening
    the walker to another undecodable type cannot silently reopen it.
    """
    _corpus(tmp_path)
    for n in range(3):
        _unreadable(tmp_path, f"scan{n}.pdf")
    run_mod.run(tmp_path)

    assert _indexed_ids(tmp_path) == {"file:docs/pruning.md"}


def _indexed_ids(root: Path) -> set[str]:
    """Read through the shard reader, never a path guess."""
    return set(read_index(root))
