"""The Python fux ships or vendors out of a dotdir at least compiles.

**What this enforces:** W-246 (B-079). One place holds Python that no tool sees by
default because the path is hidden: this repo's own consumer copies under
`.fux/{fetchers,decoders}/*.py`. (The shipped fetchers were `.py.txt` templates
until W-289; they are ordinary modules in their own packages now, under
`packages/fux-fetcher-*`, and every tool sees them.) A syntax error in either is invisible to
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
    [*(ROOT / ".fux" / "fetchers").glob("*.py")]
    + [*(ROOT / ".fux" / "decoders").glob("*.py")]
)


def test_the_dotdir_python_is_found() -> None:
    # W-289 phase 2 deleted this repo's unedited twins — the declared packages
    # run (SR-PLUGINS P9) — so an EMPTY dotdir is the expected state; what this
    # still guards is that a file put back there is found and compiled.
    assert all(p.parent.name in ("decoders", "fetchers") for p in FILES)
    assert not [*(ROOT / "src" / "fux" / "templates").glob("*.py.txt")], (
        "a `.py.txt` template is Python no tool sees; W-289 moved the fetchers into packages"
    )


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_it_parses_and_compiles(path: Path) -> None:
    src = path.read_text(encoding="utf-8")
    compile(ast.parse(src, filename=str(path)), str(path), "exec")


def test_ruff_is_told_about_the_dotdirs() -> None:
    import tomllib

    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["ruff"]
    assert any(".fux/fetchers" in g for g in cfg["extend-include"])
    assert any(".fux/decoders" in g for g in cfg["extend-include"])
