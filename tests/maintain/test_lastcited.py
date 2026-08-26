"""W-82 §3.4 — *"nothing has changed since you last asked."*

A report, not a memo. These tests pin the property that makes it safe: **no
answer is ever stored**, so the failure mode the withdrawn `--memo` carried —
replaying an answer on bytes nobody confirmed while reporting `current` — has
nothing to replay.
"""

from __future__ import annotations

import json

import pytest

from fux.maintain import lastcited


@pytest.fixture
def root(tmp_path):
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    return tmp_path


def test_first_ask_says_nothing(root):
    """Silence is correct on a first ask — there is nothing to compare against,
    and a line saying so would be noise on every new question."""
    change = lastcited.compare(root, "why helix", {"a.md": "sha1"})
    assert change.first_time
    assert change.line() == ""


def test_unchanged_repeat_says_so(root):
    lastcited.remember(root, "why helix", {"a.md": "sha1"})
    change = lastcited.compare(root, "why helix", {"a.md": "sha1"})
    assert not change.anything_changed
    assert change.line() == "note: nothing has changed since you last asked this."


def test_a_changed_sha_is_named(root):
    lastcited.remember(root, "why helix", {"a.md": "sha1"})
    change = lastcited.compare(root, "why helix", {"a.md": "sha2"})
    assert change.changed == ("a.md",)
    assert "a.md" in change.line()


def test_added_and_removed_citations_are_reported(root):
    lastcited.remember(root, "q", {"a.md": "s", "b.md": "s"})
    change = lastcited.compare(root, "q", {"a.md": "s", "c.md": "s"})
    assert change.added == ("c.md",)
    assert change.removed == ("b.md",)
    assert change.anything_changed


def test_whitespace_and_case_do_not_make_a_different_question(root):
    lastcited.remember(root, "Why  Helix?", {"a.md": "sha1"})
    change = lastcited.compare(root, "why helix?", {"a.md": "sha1"})
    assert not change.first_time
    assert not change.anything_changed


def test_a_different_question_is_a_different_question(root):
    lastcited.remember(root, "why helix", {"a.md": "sha1"})
    assert lastcited.compare(root, "why mesh", {"a.md": "sha1"}).first_time


# -- the properties that make it safe ----------------------------------------


def test_no_answer_text_is_ever_stored(root):
    """The whole reason this is a report and not a memo.

    If nothing is stored, nothing can be replayed, and the TTL-validated-replay
    hazard that withdrew `answer --memo` (W-82 §6.0) has no surface here.
    """
    lastcited.remember(root, "why helix", {"a.md": "sha1"})
    raw = (root / ".fux" / "runtime" / lastcited.LOG_NAME).read_text(encoding="utf-8")
    stored = json.loads(raw)
    for entry in stored.values():
        assert all(isinstance(v, str) for v in entry.values())
        assert set(entry) == {"a.md"}  # locators and shas, nothing else


def test_the_query_text_is_not_written_to_disk(root):
    lastcited.remember(root, "a very distinctive secret question", {"a.md": "s"})
    raw = (root / ".fux" / "runtime" / lastcited.LOG_NAME).read_text(encoding="utf-8")
    assert "distinctive" not in raw


def test_every_corrupt_state_degrades_to_first_time(root):
    directory = root / ".fux" / "runtime"
    directory.mkdir(parents=True)
    for bad in ("{not json", "[]", '{"k": "not a dict"}', ""):
        (directory / lastcited.LOG_NAME).write_text(bad, encoding="utf-8")
        assert lastcited.compare(root, "q", {"a.md": "s"}).first_time


def test_remember_never_raises_on_an_unwritable_root(root, monkeypatch):
    from fux.store import fuxdir

    def boom(*_a, **_k):
        raise OSError("read-only file system")

    monkeypatch.setattr(fuxdir, "derived_dir", boom)
    lastcited.remember(root, "q", {"a.md": "s"})  # no raise


def test_the_store_is_bounded(root):
    for n in range(lastcited.MAX_QUESTIONS + 20):
        lastcited.remember(root, f"question {n}", {"a.md": "s"})
    stored = json.loads((root / ".fux" / "runtime" / lastcited.LOG_NAME).read_text(encoding="utf-8"))
    assert len(stored) <= lastcited.MAX_QUESTIONS


def test_the_line_is_ascii_in_every_branch(root):
    """ADR-CLI veto 7: these bytes reach a Windows console, whose default
    codepage crashes `print()` on a non-encodable character rather than
    degrading. Shipped twice as a real defect."""
    cases = [
        lastcited.Change(True, (), (), ()),
        lastcited.Change(False, (), (), ()),
        lastcited.Change(False, ("a.md",), ("b.md",), ("c.md",)),
        lastcited.Change(False, ("a.md", "b.md", "c.md", "d.md"), (), ()),
    ]
    for change in cases:
        change.line().encode("ascii")  # raises if a non-ASCII byte crept in
