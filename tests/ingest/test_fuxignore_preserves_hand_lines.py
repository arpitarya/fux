"""`.fux/.fuxignore` is COMMITTED and machine-edited. Hand lines must survive.

⚠ **Written after a real loss.** Two hand-written lines (`__pycache__/`,
`*.py[cod]`) vanished from this repo's own `.fuxignore` on 2026-08-27. Both
code paths were then tested and **both are clean** — so the cause was outside
the engine (a full-file write from a stale staged copy, which is what an mtime
guard exists to reject). These tests exist so the *engine* can never acquire
the bug it was suspected of.
"""

from __future__ import annotations

from fux import setup as setup_mod
from fux.ingest import fuxignore

HAND = "# mine\n__pycache__/\n*.py[cod]\n"


def _repo(tmp_path):
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    return tmp_path


def test_setup_keeps_a_hand_authored_file(tmp_path):
    """Write-if-missing means MISSING. An existing file is reported `kept`."""
    root = _repo(tmp_path)
    path = root / fuxignore.IGNORE_FILE
    path.write_text(HAND, encoding="utf-8")

    report = setup_mod.run(root, agents=False)

    assert path.read_text(encoding="utf-8") == HAND, "setup rewrote a file it did not create"
    assert fuxignore.IGNORE_FILE in report.kept


def test_generated_blocks_never_eat_the_remainder(tmp_path):
    """The blocks are rewritten whole; everything outside them is untouched."""
    root = _repo(tmp_path)
    path = root / fuxignore.IGNORE_FILE

    fuxignore.write_blocks(root, not_indexed=[("a.bin", "not an indexed file type")], skipped=[])
    path.write_text(path.read_text(encoding="utf-8") + "\n" + HAND, encoding="utf-8")

    # a second run, with a DIFFERENT generated set — the block must change and
    # the hand lines must not.
    fuxignore.write_blocks(root, not_indexed=[("b.bin", "not an indexed file type")], skipped=[])

    after = path.read_text(encoding="utf-8")
    for line in ("# mine", "__pycache__/", "*.py[cod]"):
        assert line in after, f"a second run dropped {line!r}"
    assert "b.bin" in after and "a.bin" not in after, "the block itself must be replaced"


def test_an_empty_generated_set_does_not_truncate(tmp_path):
    """Nothing to record must not mean nothing to keep."""
    root = _repo(tmp_path)
    path = root / fuxignore.IGNORE_FILE
    path.write_text(HAND, encoding="utf-8")

    fuxignore.write_blocks(root, not_indexed=[], skipped=[])

    assert path.read_text(encoding="utf-8") == HAND


def test_a_noop_rewrite_does_not_touch_the_file(tmp_path):
    """`git status` must stay quiet, and an unchanged mtime is also what keeps a
    concurrent session's stale-copy guard meaningful."""
    root = _repo(tmp_path)
    path = root / fuxignore.IGNORE_FILE
    fuxignore.write_blocks(root, not_indexed=[("a.bin", "not an indexed file type")], skipped=[])
    before = path.stat().st_mtime_ns

    fuxignore.write_blocks(root, not_indexed=[("a.bin", "not an indexed file type")], skipped=[])

    assert path.stat().st_mtime_ns == before, "a no-op rewrote the file"


def test_the_blocks_go_first_so_a_hand_written_bang_still_wins(tmp_path):
    """⚠ Last match wins in `.gitignore` grammar.

    A generated block written LAST would silently beat a `!` a human wrote —
    the one real hazard of letting a machine edit this file.
    """
    root = _repo(tmp_path)
    path = root / fuxignore.IGNORE_FILE
    path.write_text("!keep.bin\n", encoding="utf-8")

    fuxignore.write_blocks(root, not_indexed=[("keep.bin", "not an indexed file type")], skipped=[])

    text = path.read_text(encoding="utf-8")
    assert text.index("keep.bin") < text.index("!keep.bin"), (
        "the generated block must come FIRST, or it outranks the human"
    )
