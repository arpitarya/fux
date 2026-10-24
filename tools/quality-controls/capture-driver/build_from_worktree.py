#!/usr/bin/env python3
"""Run fux-lab's UNMODIFIED `build_golden_rung.py` against a clean fux worktree.

TEMPLATE (W-281): copy this directory into the next ladder run's `evidence/`.
It is generation 6's driver plus ONE change, **change 3 (W-281 DoD 1): every
`git commit` the builder runs gets `-c commit.gpgsign=false`.** A rung is lab
data and is never pushed; signing blocked on gpg for 12 h on 2026-10-13
(rung-10000: 43 690 s against rung-05000's 508 s). fux-lab's builder is untouched.

Generation 6's docstring follows.

Generation 5's driver (`../../2026-10-11-ladder-gen5-rebuild/evidence/build_from_worktree.py`),
**unchanged in what it does**: change 1 (drop the `ext/archive` source line when
the rung has no `ext/archive/`) and change 2 (the pair-ordered authored list,
`make_golden_ext_gen4.py`, copied here unchanged) both still apply. Only this
docstring is new.

**What generation 6 changes is a count, not a driver.** The seed is 188
documents (182 in `seed/`, 6 in `seed/archive/`), again more than
`rung-00100`'s headline size. Generation 5's ruling is applied again (Arpit,
2026-10-11: *keep it at 118 docs*, i.e. the seed alone): `rung-00100` is built
with `--count 188`.

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
    if cmd[:2] == ["git", "commit"]:  # change 3: never sign a lab rung (W-281)
        cmd = ["git", "-c", "commit.gpgsign=false"] + cmd[1:]
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
