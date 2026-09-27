#!/usr/bin/env python3
"""Run fux-lab's UNMODIFIED `build_golden_rung.py` against a clean fux worktree.

The builder names the fux repo as a constant and uses its `.venv` engine. On
2026-09-27 the main tree carried another session's staged, uncommitted W-225
change, and a rung stamped with a commit its engine did not match would be
the W-186 defect again. So this driver points the builder's four constants at
a worktree checked out at one commit, runs it, and adds the `engine_commit:`
line the builder does not write (W-186) — nothing else.

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

sys.argv = ["build_golden_rung.py", "--rung", rung, "--count", count]
rc = b.main()
commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=wt, text=True,
                        capture_output=True, check=True).stdout.strip()
idx = b.LADDER / f"{rung}.index"
lines = idx.read_text().splitlines()
lines.insert(1, f"engine_commit: {commit}")
idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
raise SystemExit(rc)
