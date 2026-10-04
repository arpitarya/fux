"""The Python fux ships or vendors out of a dotdir at least compiles.

**What this enforces:** W-246 (B-079). Two places hold Python that no tool sees by
default because the path is hidden or the suffix is `.txt`: the shipped templates
(`src/fux/templates/*.py.txt`, which `fux setup` writes into a consumer's
`.fux/fetchers/`) and this repo's own consumer copies under
`.fux/{fetchers,decoders}/*.py`. A syntax error in either is invisible to
`compileall`, to coverage and to a glob-based linter until a consumer's run hits
it. Each file is `ast.parse`d and `compile`d. Stdlib only: ruff is NOT a dev
dependency, so `pyproject.toml`'s `[tool.ruff] extend-include` is only a courtesy
to whoever runs it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted(
    [*(ROOT / "src" / "fux" / "templates").glob("*.py.txt")]
    + [*(ROOT / ".fux" / "fetchers").glob("*.py")]
    + [*(ROOT / ".fux" / "decoders").glob("*.py")]
)


def test_the_dotdir_python_is_found() -> None:
    assert any(p.name.endswith(".py.txt") for p in FILES)
    assert any(p.parent.name == "fetchers" for p in FILES)
    assert any(p.parent.name == "decoders" for p in FILES)


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_it_parses_and_compiles(path: Path) -> None:
    src = path.read_text(encoding="utf-8")
    compile(ast.parse(src, filename=str(path)), str(path), "exec")


def test_ruff_is_told_about_the_dotdirs() -> None:
    import tomllib

    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["ruff"]
    assert any(".fux/fetchers" in g for g in cfg["extend-include"])
    assert any(".fux/decoders" in g for g in cfg["extend-include"])
