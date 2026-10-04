"""The differential arms import, and `adversarial_corpus.py` refuses a live tree.

**What this enforces:** [SR-T1-ACCELERATOR](../records/0110_accelerator.md)
Consequences -- `graph_arm.py`, `goldens_grade.py` and `adversarial_corpus.py` were
not exercised by any suite, so a rename in the engine broke them silently until CI
reached them. Importing each is the cheapest proof they still resolve their
engine imports. (A required check on `main` is Arpit's, W-251 §3 #22; this is only
the test.) And B-077: `adversarial_corpus.py` REWRITES `.fux/index/`, so its root
argument is required and it refuses the engine tree, or any root holding a `.git`,
unless `CI` is set. W-246 (B-076, B-077).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIFF = ROOT / "tools" / "differential"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"_diff_{name}", DIFF / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # a dataclass resolves its own module by name
    sys.path.insert(0, str(DIFF))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(DIFF))
    return mod


@pytest.mark.parametrize("arm", ["graph_arm", "goldens_grade", "adversarial_corpus"])
def test_the_arm_imports(arm: str) -> None:
    """SR-T1-ACCELERATOR Consequences: the arm resolves every engine import it names."""
    assert _load(arm) is not None


def test_the_root_argument_is_required() -> None:
    """B-077: no argument is a usage error, never an implicit `.`."""
    r = subprocess.run(
        [sys.executable, str(DIFF / "adversarial_corpus.py")], capture_output=True, text=True, cwd=ROOT
    )
    assert r.returncode == 2 and "root" in r.stderr


def test_it_refuses_the_engine_tree_and_a_git_root_without_ci(tmp_path) -> None:
    """B-077: the engine checkout, or a root with a `.git`, is refused unless `CI` is set."""
    mod = _load("adversarial_corpus")
    assert mod.refusal(ROOT, {}) and "engine" in mod.refusal(ROOT, {})
    (tmp_path / ".git").mkdir()
    assert mod.refusal(tmp_path, {}) and ".git" in mod.refusal(tmp_path, {})
    assert mod.refusal(ROOT, {"CI": "true"}) is None
    assert mod.refusal(tmp_path, {"CI": "true"}) is None


def test_it_writes_into_a_plain_copy_and_not_a_live_tree(tmp_path, monkeypatch) -> None:
    """B-077: a throwaway root is written; the engine tree is left untouched on refusal."""
    mod = _load("adversarial_corpus")
    monkeypatch.delenv("CI", raising=False)
    (tmp_path / ".fux" / "index").mkdir(parents=True)
    assert mod.refusal(tmp_path, {}) is None
    assert mod.main([str(tmp_path)]) == 0
    assert any((tmp_path / ".fux" / "index").iterdir())
    assert mod.main([str(ROOT)]) == 1
