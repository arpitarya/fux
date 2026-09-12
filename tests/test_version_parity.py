"""The version string agrees across every file that carries it.

The executable twin of `scripts/check-version-parity.py`, in the shape
`tests/test_claude_md_laws.py` uses for `scripts/gen-laws.py`: the script is
the implementation, this is what makes it run on every push rather than only
at release time.

**Why it exists.** `CLAUDE.md` §Package identity claimed one source of truth
for the version. W-107's Node read plane added three more hand-written copies
— `node/package.json`, `node/fux.mjs`, `node/src/verbs/mcp.mjs` — and a bump
that missed one would publish a PyPI wheel and an npm tarball naming different
releases, with `fux --version` (the one line R1a calls the highest-value in the
whole item) telling a bug reporter the wrong thing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "check_version_parity", ROOT / "scripts" / "check-version-parity.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)


def test_every_version_site_agrees():
    problems = _mod.check(ROOT)
    assert not problems, "version parity broken:\n  " + "\n  ".join(problems)


def test_the_check_actually_fails_on_a_mismatch(tmp_path):
    """A parity check that cannot fail is not a check.

    Copy the four sites into a tmp tree, perturb one, and assert the checker
    notices — otherwise a regex that silently stops matching reads as green.
    """
    for name in _mod.SITES:
        dst = tmp_path / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")

    assert not _mod.check(tmp_path), "the copied tree should start clean"

    pkg = tmp_path / "node/package.json"
    pkg.write_text(
        pkg.read_text(encoding="utf-8").replace('"version": "', '"version": "9.9.9-not-', 1),
        encoding="utf-8",
    )
    problems = _mod.check(tmp_path)
    assert problems, "a mismatched node/package.json was not detected"
    assert any("node/package.json" in p for p in problems)
