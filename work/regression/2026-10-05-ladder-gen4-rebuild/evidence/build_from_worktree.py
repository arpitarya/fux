#!/usr/bin/env python3
"""Run fux-lab's UNMODIFIED `build_golden_rung.py` against a clean fux worktree — generation 4.

The 2026-09-27 driver (`../../2026-09-27-ladder-gen3-rebuild/evidence/build_from_worktree.py`)
plus TWO changes, both forced by `rung-00100` holding only 6 ext documents.

Change 2 (below `run`): the builder's generator subprocess is pointed at
`make_golden_ext_gen4.py`, which emits the same documents with each retired
authored document immediately before its successor — see that file.

Change 1: with 94 seed documents, `rung-00100` holds only 6 generated
documents and none of them is archived, so `ext/archive/` does not exist. The
builder writes the `ext/archive archived=true` source line whenever there is
any ext at all, and a source line naming a missing directory is a hard ingest
error. So this driver wraps the builder's `run()` and, just before `.fux/` is
first staged, removes that one line when — and only when — the directory is
absent. Every rung that has `ext/archive/` gets byte-identical config.

    python3 build_from_worktree.py <worktree> <rung> <count>

Reads `seed/`, `seed-dates.tsv`, `seed-history.tsv` and `seed-history/` only,
through the builder. Never `questions/`, never a key.
"""
import subprocess
import sys
from pathlib import Path

wt, rung, count = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
sys.path.insert(0, str(wt / "tools" / "golden-history"))
import replay  # noqa: E402,F401 — cached first, so the builder's own import gets the worktree's
sys.path.insert(0, str(Path.home() / "my_programs/fux-lab/shared/generate"))
import build_golden_rung as b  # noqa: E402

b.FUX_REPO = wt
b.GOLDEN = wt / "work" / "golden"
b.LADDER = b.GOLDEN / "ladder"
b.FUX = wt / ".venv" / "bin" / "fux"
assert Path(b.replay.__file__).resolve().is_relative_to(wt), b.replay.__file__

_run = b.run
ARCHIVE_LINE = "ext/archive         archived=true\n"
assert ARCHIVE_LINE in b.EXT_SOURCES, b.EXT_SOURCES


GEN4 = Path(__file__).resolve().parent / "make_golden_ext_gen4.py"


def run(cmd, cwd, env=None, check=True, capture=True):
    if len(cmd) > 1 and cmd[1].endswith("/make_golden_ext.py"):
        cmd = [cmd[0], str(GEN4)] + cmd[2:]  # change 2: pair-ordered authored docs
    if cmd[:3] == ["git", "add", "-A"] and cmd[-1] == ".fux":
        dirs = Path(cwd) / ".fux" / "sources" / "dirs"
        text = dirs.read_text(encoding="utf-8")
        if ARCHIVE_LINE in text and not (Path(cwd) / "ext" / "archive").is_dir():
            dirs.write_text(text.replace(ARCHIVE_LINE, ""), encoding="utf-8")
            print(f"{rung}: no ext/archive/ in this rung — its source line dropped")
    return _run(cmd, cwd, env=env, check=check, capture=capture)


b.run = run
sys.argv = ["build_golden_rung.py", "--rung", rung, "--count", count]
rc = b.main()
commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=wt, text=True,
                        capture_output=True, check=True).stdout.strip()
idx = b.LADDER / f"{rung}.index"
lines = idx.read_text().splitlines()
lines.insert(1, f"engine_commit: {commit}")
idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
raise SystemExit(rc)
