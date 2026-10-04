"""No test walks the repo root into `work/golden/` — the W-244 gate.

**Two strikes, so a gate** (SR-WORK-SESSION decision 13; W-223/W-230 were the
first walk, W-244 the second). L11 decision 9: a recursive walk over `work/`
excludes `work/golden/` in every state, and filtering the output after the walk
does not count, because the walk has already listed the directory. Every test
that walks from the root goes through `walk_lib`, which never enters it.

1. **Mechanical:** no file under `tests/` calls `rglob` or `os.walk` on the
   repository root (`ROOT`, `ENGINE`, `REPO`, alone or joined to a subpath).
2. **Behavioural:** `walk_lib` never scans `work/golden`, proved by a spy on
   `os.scandir`, which `os.walk` lists through.

The same rule binds `fux ingest`; `tests/ingest/test_source_filters.py` holds it.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import walk_lib

TESTS = Path(__file__).resolve().parent
EXEMPT = {"walk_lib.py", "test_walks_skip_golden.py"}

#: A root-anchored walk: `ROOT.rglob(`, `(ROOT / x).rglob(`, `os.walk(ROOT…`.
_ROOT_WALK = re.compile(
    r"\b(?:ROOT|ENGINE|REPO)\b[^\n#]{0,40}?\)?\.rglob\(|os\.walk\([^)\n]*\b(?:ROOT|ENGINE|REPO)\b"
)
#: A walk that starts in one of these quoted top-level directories cannot reach
#: `work/golden/`. A bare root, `"work"`, or a variable segment is not safe.
_SAFE_FIRST = {"src", "node", "tests", "tools", "scripts", "records", "docs", "archive"}
_FIRST_SEGMENT = re.compile(r"\b(?:ROOT|ENGINE|REPO)\s*/\s*[\"']([^\"']+)[\"']")


def _is_root_walk(line: str) -> bool:
    if not _ROOT_WALK.search(line):
        return False
    first = _FIRST_SEGMENT.search(line)
    return first is None or first.group(1).split("/")[0] not in _SAFE_FIRST


def test_no_test_walks_the_root_except_through_walk_lib():
    offenders = []
    for path in sorted(TESTS.rglob("*.py")):
        if path.name in EXEMPT or "__pycache__" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _is_root_walk(line):
                offenders.append(f"{path.relative_to(TESTS)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "these walk the repository root without pruning work/golden/ (L11 decision 9, W-244). "
        "Use walk_lib.repo_files / repo_dirs:\n  " + "\n  ".join(offenders)
    )


def test_walk_lib_never_scans_work_golden(tmp_path, monkeypatch):
    (tmp_path / "work" / "golden" / "inner").mkdir(parents=True)
    (tmp_path / "work" / "golden" / "inner" / "x.md").write_text("# X\n", encoding="utf-8")
    (tmp_path / "work" / "open").mkdir(parents=True)
    (tmp_path / "work" / "open" / "a.md").write_text("# A\n", encoding="utf-8")
    scanned = []
    real = os.scandir

    def spy(path="."):
        scanned.append(Path(os.fspath(path)).as_posix())
        return real(path)

    monkeypatch.setattr(os, "scandir", spy)
    found = [p.relative_to(tmp_path).as_posix() for p in walk_lib.repo_files(tmp_path)]
    found += [p.relative_to(tmp_path).as_posix() for p in walk_lib.repo_files(tmp_path, start="work")]
    assert found == ["work/open/a.md", "work/open/a.md"]
    assert not any("/work/golden" in p for p in scanned), scanned
