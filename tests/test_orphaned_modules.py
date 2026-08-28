"""No module in `src/` may be unreachable from a declared entry point.

**W-87 P1's orphaned-module check.** Three modules were deleted by hand in two
days for having no caller — `query/hybrid.py`, `query/fuse.py`,
`embed/fuxvec.py` — **all three with passing tests the whole time**, which is
exactly why none was noticed. *A tested module looks alive.* `fuxvec.py` had
been dead since 2026-08-23 with a green suite; nothing would have caught the
fourth.

## Why reachability, and not "has an importer"

The obvious check — *flag a module nothing imports* — is both too weak and too
strong. Too weak, because a dead module imported only by another dead module
looks alive: `hybrid.py` and `fuse.py` propped each other up. Too strong,
because almost every module here is imported only by its own package's
`__init__`, which is the normal and correct shape.

**So the question is reachability from an entry point**, walked transitively.
A module is live if you can get to it by starting a shipped command.

## The entry points are DECLARED, never guessed

⚠ **This is what stops the check needing a hand-maintained exception list** —
and an exception list is how this kind of check dies, because the list grows
until it is the answer.

| root | where it is declared | why it is not statically imported |
|---|---|---|
| `fux.cli`, `fux.maintain.mergedriver` | `[project.scripts]` in `pyproject.toml` | console scripts; git invokes the merge driver as a bare command |
| `fux.__main__` | `python -m fux` | rung 4 of the invocation ladder in `AGENTS.md` |
| every `fux.decode.*doc` | `decode.BUILTIN_MODULES` | loaded by `importlib.import_module` from that tuple |

**All three are read from the repository**, so adding a decoder or an entry
point keeps the check honest with no edit here. The decoders are the case that
would otherwise have needed fourteen exception rows.

⚠ **`DECLARED_EXCEPTIONS` is empty and should stay that way.** A module that
needs a row is usually a module that needs a caller. If one is ever added it
carries its reason in the same dict, because an unauditable exception list is
indistinguishable from a disabled check.
"""

from __future__ import annotations

import ast
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fux"

#: module -> the reason it is reachable in a way this walk cannot see.
#: **Empty on purpose.** See the module docstring.
DECLARED_EXCEPTIONS: dict[str, str] = {}


# -- the graph --------------------------------------------------------------


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT / "src").with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _modules() -> dict[str, Path]:
    return {_module_name(p): p for p in sorted(SRC.rglob("*.py"))}


def _imports(path: Path, own: str) -> set[str]:
    """Every module name this file names, static or by `import_module`.

    ⚠ **`import_module("literal")` is followed.** Half of fux's plane loading is
    dynamic and a walk that ignored it would call every decoder dead — the
    check would be so loud on day one that someone would switch it off.
    """
    found: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    base = own if path.name == "__init__.py" else own.rsplit(".", 1)[0]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative: resolve against this file's package
                parts = base.split(".")
                up = node.level - 1
                anchor = ".".join(parts[: len(parts) - up]) if up else base
                target = f"{anchor}.{node.module}" if node.module else anchor
            else:
                target = node.module or ""
            found.add(target)
            # `from x import y` may name a submodule rather than an attribute.
            found.update(f"{target}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
            if name == "import_module":
                found.update(
                    a.value
                    for a in node.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)
                )
    return found


def _edges(modules: dict[str, Path]) -> dict[str, set[str]]:
    edges = {n: {t for t in _imports(p, n) if t in modules} for n, p in modules.items()}
    # Importing `a.b.c` runs `a.b`, so a package is reachable through its child.
    extra: dict[str, set[str]] = defaultdict(set)
    for name, targets in edges.items():
        for target in targets:
            parts = target.split(".")
            for i in range(2, len(parts)):
                ancestor = ".".join(parts[:i])
                if ancestor in modules:
                    extra[name].add(ancestor)
    for name, more in extra.items():
        edges[name] |= more
    return edges


# -- the declared roots -----------------------------------------------------


def _console_scripts() -> set[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return {
        spec.split(":")[0]
        for spec in data.get("project", {}).get("scripts", {}).values()
    }


def _builtin_decoders() -> set[str]:
    """Read `BUILTIN_MODULES` from source rather than importing it.

    Importing would be simpler and would also mean the check's own answer
    depended on import side effects. The tuple is a literal; parse the literal.
    """
    tree = ast.parse((SRC / "decode" / "__init__.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        target = getattr(node, "target", None)
        named = getattr(target, "id", None) if target is not None else None
        if named == "BUILTIN_MODULES" and isinstance(node.value, ast.Tuple):
            return {f"fux.decode.{e.value}" for e in node.value.elts}
    raise AssertionError("decode.BUILTIN_MODULES is no longer a literal tuple")


def _roots() -> set[str]:
    return _console_scripts() | {"fux.__main__"} | _builtin_decoders()


def _reachable(modules: dict[str, Path]) -> set[str]:
    edges = _edges(modules)
    seen: set[str] = set()
    stack = [r for r in _roots() if r in modules]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))
    return seen


# -- the check itself -------------------------------------------------------


def test_no_src_module_is_unreachable_from_a_declared_entry_point():
    """The check. Green as of 2026-08-27, with an empty exception list."""
    modules = _modules()
    orphans = sorted(set(modules) - _reachable(modules) - set(DECLARED_EXCEPTIONS))

    assert not orphans, (
        "these modules cannot be reached from any shipped command:\n  "
        + "\n  ".join(orphans)
        + "\n\nEither give one a caller, delete it, or add it to "
        "DECLARED_EXCEPTIONS with the reason it is reachable another way."
    )


def test_the_check_would_actually_catch_a_dead_module(tmp_path):
    """⚠ **Not optional.** The test above passes on a repo with no modules at
    all, so on its own it proves nothing — and a vacuous pass is the exact
    failure mode this repo has now recorded twice.

    Reconstruct the shape that got past everyone: two modules that import each
    other and nothing else, which is what `hybrid.py` and `fuse.py` were.
    """
    modules = _modules()
    edges = _edges(modules)

    # The historical pair, in miniature.
    modules["fux.query.hybrid"] = tmp_path / "hybrid.py"
    modules["fux.query.fuse"] = tmp_path / "fuse.py"
    edges["fux.query.hybrid"] = {"fux.query.fuse"}
    edges["fux.query.fuse"] = {"fux.query.hybrid"}

    seen: set[str] = set()
    stack = [r for r in _roots() if r in modules]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))

    orphans = set(modules) - seen
    assert orphans == {"fux.query.hybrid", "fux.query.fuse"}, (
        "the mutually-importing dead pair was not flagged — this is precisely "
        "the case a naive has-an-importer check misses"
    )


def test_a_module_kept_alive_only_by_its_own_tests_is_still_dead():
    """The other half of the historical failure: *a tested module looks alive.*

    The walk starts at entry points and never looks at `tests/`, so importing
    something from a test cannot resurrect it. Asserted structurally, on the
    walk's own inputs, rather than by planting a file.
    """
    for name, path in _modules().items():
        assert "tests" not in path.parts, f"{name} is not under src/"

    assert all(root.startswith("fux.") for root in _roots())
    source = Path(__file__).read_text(encoding="utf-8")
    assert 'rglob("*.py")' in source and "SRC.rglob" in source, (
        "the module walk must be rooted at SRC; a walk that reached tests/ "
        "would count a test as a caller and reopen the whole defect"
    )


def test_every_declared_root_actually_exists():
    """A root naming a deleted module would silently shrink the graph and turn
    this check green by making everything downstream unreachable-but-unwalked.
    """
    modules = _modules()
    missing = sorted(r for r in _roots() if r not in modules)
    assert not missing, f"declared entry points name modules that do not exist: {missing}"


def test_the_decoder_roots_come_from_the_declared_tuple():
    """If `BUILTIN_MODULES` stops being the source, fourteen exception rows are
    owed the same day — so the coupling is asserted rather than assumed."""
    decoders = _builtin_decoders()

    assert len(decoders) >= 14, "the decoder registry shrank unexpectedly"
    for name in decoders:
        assert (SRC / "decode" / f"{name.rsplit('.', 1)[1]}.py").is_file(), (
            f"{name} is registered in BUILTIN_MODULES but has no module"
        )


def test_the_exception_list_is_auditable():
    """Every exception carries a reason, and there are none today."""
    for module, reason in DECLARED_EXCEPTIONS.items():
        assert reason.strip(), f"{module} is excepted with no reason given"
