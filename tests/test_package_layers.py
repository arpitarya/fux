"""The layer map holds: reader and writer never import each other (W-282).

`records/README.md` §"The layer map" places every file under `src/fux/` in
one of four layers — core, reader, writer, engine — and lists the few
cross-layer imports that are permitted, each guarded so the importing package
still works where the other layer is not installed. **This test reads both
tables from that file and states no layer of its own**, so the record and the
check cannot disagree while both look right (SR-LAW-0 decision 5).

What it fails on:

1. a file under `src/fux/` that no row places;
2. a sub-package whose files do not all share the package directory's layer
   — the packaging step ships a directory whole;
3. an import, anywhere in a module (inside a function too), that crosses
   the map — counting the package `__init__.py` an import runs;
4. a cross-layer import in the guarded form that the second table does not
   list, or a listed one that is not written in that form;
5. a row of the second table that no longer matches any import.

⚠ **An import walk sees imports.** A subprocess relaunch (`python -m
fux.cli`) and a data file read by path are not imports; the record names the
ones it knows about.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "fux"
README = ROOT / "records" / "README.md"

ALLOWED = {
    "core": {"core"},
    "reader": {"core", "reader"},
    "writer": {"core", "writer"},
    "engine": {"core", "reader", "writer", "engine"},
}

_ROW = re.compile(r"^\| `([^`]+)` \| `?([^|`]+?)`? \|(.*)$")


def _block() -> str:
    text = README.read_text(encoding="utf-8")
    start = text.index("<!-- LAYER-MAP-START -->")
    end = text.index("<!-- LAYER-MAP-END -->")
    return text[start:end]


def layer_rows() -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in _block().splitlines():
        m = _ROW.match(line)
        if m and m.group(2).strip() in ALLOWED:
            rows[m.group(1)] = m.group(2).strip()
    return rows


def guarded_rows() -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for line in _block().splitlines():
        m = _ROW.match(line)
        if m and m.group(2).strip().startswith("fux."):
            out.add((m.group(1), m.group(2).strip()))
    return out


def _files() -> list[Path]:
    return sorted(
        p for p in PKG.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        and p.name != ".DS_Store"
    )


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def layer_of(rel: str, rows: dict[str, str]) -> str | None:
    best = None
    for path, layer in rows.items():
        hit = rel == path or (path.endswith("/") and rel.startswith(path))
        if hit and (best is None or len(path) > len(best[0])):
            best = (path, layer)
    return best[1] if best else None


# -- module resolution --------------------------------------------------------


def _module_of(p: Path) -> tuple[str, bool]:
    parts = list(p.relative_to(SRC).with_suffix("").parts)
    is_pkg = parts[-1] == "__init__"
    if is_pkg:
        parts = parts[:-1]
    return ".".join(parts), is_pkg


def _modules() -> dict[str, Path]:
    return {_module_of(p)[0]: p for p in _files() if p.suffix == ".py"}


def _guarded(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    """Inside a `try:` body whose handlers name ImportError (or its subclass)."""
    child, cur = node, parents.get(id(node))
    while cur is not None:
        if isinstance(cur, ast.Try) and child in cur.body:
            for handler in cur.handlers:
                names = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
                if any(isinstance(n, ast.Name) and n.id in ("ImportError", "ModuleNotFoundError")
                       for n in names):
                    return True
        child, cur = cur, parents.get(id(cur))
    return False


def edges() -> list[tuple[str, str, int, bool]]:
    """`(importer file, target module, line, guarded)` for every fux import."""
    mods = _modules()
    out = []
    for mod, path in sorted(mods.items()):
        is_pkg = path.name == "__init__.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {id(c): n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names if a.name.split(".")[0] == "fux"]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    pkg = mod.split(".") if is_pkg else mod.split(".")[:-1]
                    pkg = pkg[: len(pkg) - (node.level - 1)]
                    base = ".".join(pkg + ([node.module] if node.module else []))
                elif node.module and node.module.split(".")[0] == "fux":
                    base = node.module
                else:
                    continue
                targets = [f"{base}.{a.name}" if f"{base}.{a.name}" in mods else base
                           for a in node.names]
            for target in targets:
                while target not in mods and "." in target:
                    target = target.rsplit(".", 1)[0]
                if target == mod:
                    continue
                guarded = _guarded(node, parents)
                # importing fux.a.b runs fux/a/__init__.py too
                parts = target.split(".")
                for i in range(1, len(parts) + 1):
                    hop = ".".join(parts[:i])
                    if hop in mods and hop != mod:
                        out.append((_rel(path), hop, node.lineno, guarded))
    return out


# -- the tests ----------------------------------------------------------------


def test_the_map_is_readable():
    rows = layer_rows()
    assert len(rows) > 20, "the layer map table was not found in records/README.md"
    assert set(rows.values()) == set(ALLOWED), "every layer should place something"
    for path in rows:
        assert (ROOT / path).exists(), f"the layer map names a path that does not exist: {path}"


def test_every_file_is_placed():
    rows = layer_rows()
    missing = [_rel(p) for p in _files() if layer_of(_rel(p), rows) is None]
    assert not missing, (
        "files under src/fux/ that no row of the layer map places — add a row to "
        "records/README.md §The layer map:\n  " + "\n  ".join(missing)
    )


def test_a_sub_package_is_one_layer():
    rows = layer_rows()
    mixed = []
    for p in _files():
        rel_parts = p.relative_to(PKG).parts
        if len(rel_parts) < 2:
            continue  # root-level modules are placed one by one
        package = f"src/fux/{rel_parts[0]}/"
        if layer_of(_rel(p), rows) != layer_of(package, rows):
            mixed.append(f"{_rel(p)} is {layer_of(_rel(p), rows)}, {package} is {layer_of(package, rows)}")
    assert not mixed, (
        "a package directory ships whole, so every file in it shares its layer:\n  "
        + "\n  ".join(mixed)
    )


def test_no_import_crosses_the_map():
    rows = layer_rows()
    mods = _modules()
    listed = guarded_rows()
    crossings = []
    for importer, target, line, guarded in edges():
        mine = layer_of(importer, rows)
        theirs = layer_of(_rel(mods[target]), rows)
        if theirs in ALLOWED[mine]:
            continue
        declared = any(importer == row and (target == t or target.startswith(t + "."))
                       for row, t in listed)
        if declared and guarded:
            continue
        why = ("listed, but not inside try/except ImportError" if declared
               else "guarded, but not listed" if guarded else "not permitted")
        crossings.append(f"{importer}:{line} ({mine}) imports {target} ({theirs}) — {why}")
    assert not crossings, (
        "imports that cross the layer map (records/README.md §The layer map):\n  "
        + "\n  ".join(crossings)
        + "\n\nMove the shared piece into core, or — only where the importing package "
        "works without the other layer — guard the import and list it in the record."
    )


def test_every_guarded_row_still_matches_an_import():
    found = {(importer, target) for importer, target, _line, guarded in edges() if guarded}
    stale = [
        f"{row} -> {t}" for row, t in sorted(guarded_rows())
        if not any(i == row and (tg == t or tg.startswith(t + ".")) for i, tg in found)
    ]
    assert not stale, (
        "rows of the guarded-import table that no guarded import matches any more — "
        "delete them:\n  " + "\n  ".join(stale)
    )
