"""The differential HARNESS itself — `tools/differential/` must run on a repo.

🔴 **The unit-suite arm covered for a dead real-corpus arm for as long as a
binary file sat in a source directory** (W-184, 2026-09-15).
`tests/derive/test_differential.py` builds its own synthetic corpora and calls
`compare()` directly, so it was green while `run.py --root .` could not reach
its first comparison: `queryset.vocabulary` decoded **every** walked file as
UTF-8, and `walk_sources` yields the PNGs under `docs/` that no decoder claims
and ingest skips.

⚠ **Two failures, one assumption, and the quiet one is worse.**
`queryset.vocabulary` raised; `bench_r3.source_vocabulary` decoded the same
bytes with `errors="replace"` and carried on, folding a page of replacement
characters into the corpus vocabulary as terms no document contains. A harness
that crashes gets fixed. A harness that invents its own query set does not.

The tests below are the gate SR-WORK-SESSION decision 13 asks for on the second
occurrence of a failure class.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "differential"))

import queryset  # noqa: E402

#: A real PNG header — `0x89` is the byte the harness died on.
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _repo(tmp_path: Path, files: dict[str, bytes]) -> Path:
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndirs_file = ".fux/sources/dirs"\n', encoding="utf-8"
    )
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".fux" / "sources").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("[rules]\n", encoding="utf-8")
    for rel, blob in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    return tmp_path


def test_a_binary_file_in_a_source_dir_does_not_kill_the_query_set(tmp_path):
    """The exact shape of W-184: a PNG beside the documents."""
    root = _repo(
        tmp_path,
        {
            "docs/one.md": b"# One\n\nthe rollback runbook explains the procedure\n",
            "docs/figures/diagram.png": PNG,
        },
    )
    vocab = queryset.vocabulary(root)
    assert vocab.terms, "the query set is empty — the walk found no decodable text"
    assert "rollback" in vocab.terms


def test_the_skip_is_counted_and_named_rather_than_silent(tmp_path):
    """A query set that quietly shrinks is a harness that quietly stops proving."""
    root = _repo(
        tmp_path,
        {
            "docs/one.md": b"# One\n\nthe rollback runbook\n",
            "docs/figures/a.png": PNG,
            "docs/figures/b.png": PNG,
        },
    )
    vocab = queryset.vocabulary(root)
    assert vocab.skipped_undecodable == 2
    assert vocab.undecodable == ("docs/figures/a.png", "docs/figures/b.png")


def test_undecodable_bytes_contribute_NO_term(tmp_path):
    """Not `errors="replace"` — that is the sibling's bug, asserted here.

    Decoding a PNG with replacement characters yields terms, and those terms
    then generate queries. The corpus below has exactly one word; anything else
    in the vocabulary came out of the image.
    """
    root = _repo(tmp_path, {"docs/one.md": b"zarquon\n", "docs/f.png": PNG})
    assert queryset.vocabulary(root).terms == ["zarquon"]


def test_a_corpus_of_only_binaries_is_empty_and_not_an_exception(tmp_path):
    """The degenerate end of the same branch: nothing decodes, nothing raises."""
    root = _repo(tmp_path, {"docs/a.png": PNG, "docs/b.png": PNG})
    vocab = queryset.vocabulary(root)
    assert vocab.terms == []
    assert vocab.skipped_undecodable == 2
    # `generate` must still produce the adversarial and frozen sets.
    queries, again = queryset.generate_with_vocabulary(root)
    assert queries, "the fixed query groups vanished with the corpus"
    assert again.skipped_undecodable == 2


def test_the_bench_arm_walks_sources_the_same_way(tmp_path):
    """`bench_r3.source_vocabulary` is the sibling that decoded with `replace`."""
    bench = pytest.importorskip("bench_r3")
    root = _repo(tmp_path, {"docs/one.md": b"zarquon\n", "docs/f.png": PNG})
    assert [t for t, _ in bench.source_vocabulary(root)] == ["zarquon"]


def test_the_harness_still_takes_a_weight_sweep_the_engine_accepts():
    """W-152 removed `archived_weight` and `run.py` kept passing it for two days.

    Every invocation raised `TypeError` before its first comparison. The check
    is cheap and mechanical: whatever `compare()` hands the two `ask`s, both
    must accept — so bind the call rather than trusting the keyword name.
    """
    import inspect

    import run as harness
    from fux.derive import accel
    from fux.query import scan

    assert harness.WEIGHTS, "the weight sweep is empty — W-73's property is unchecked"
    kw = {"archived_dirs": frozenset(), "weighting": None}
    for fn in (scan.ask, accel.ask):
        inspect.signature(fn).bind(Path("."), "q", top=5, **kw)
