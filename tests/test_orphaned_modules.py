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
| `fux.cli`, `fux.maintain.mergedriver` | `[project.scripts]` in `packages/*/pyproject.toml` (and the root's) | console scripts; git invokes the merge driver as a bare command |
| `fux.__main__` | `python -m fux` | rung 4 of the invocation ladder in `AGENTS.md` |
| every first-party decoder module | `constants.toml [plugins.packages.*] modules` | since W-289 phase 2 each lives in a `fux-decoder-*` package and is imported by NAME, only when declared (SR-PLUGINS P7) |
| `fux.schemas` | `constants.toml` `[schema_files] package` | a data package: `schema.load` resolves it by name through `importlib.resources` (W-226) |
| every verb module | `cli.VERBS` | `cli.py` is core and runs a verb by module NAME, so a missing layer is refused rather than imported (W-282) |
| every `python -m fux.<module>` in `.github/workflows/*.yml` | the release and CI workflows | a build-time tool the release runs by module name — `fux.store.nodebundle`, which builds npm's bundle and, since W-292, is imported by nothing that ships |

**All four are read from the repository**, so adding a decoder or an entry
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
#: W-289 phase 2: the decoder and extension packages are engine code built from
#: this tree. Walked too, so the decoder SDK in `decode/ext/` — reached only from
#: a decoder module now — is still seen as live, and a dead module in a package
#: is still caught.
PLUGIN_SRCS = sorted(
    p for p in (ROOT / "packages").glob("fux-*/src") if not p.parent.name.startswith("fux-fetcher-")
    and p.parent.name not in ("fux-core", "fux-reader", "fux-writer")
)

#: module -> the reason it is reachable in a way this walk cannot see.
#: **Empty on purpose.** See the module docstring.
DECLARED_EXCEPTIONS: dict[str, str] = {}


# -- the graph --------------------------------------------------------------


def _module_name(path: Path) -> str:
    base = next((s for s in PLUGIN_SRCS if s in path.parents), ROOT / "src")
    parts = list(path.relative_to(base).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _modules() -> dict[str, Path]:
    files = sorted(SRC.rglob("*.py"))
    for src in PLUGIN_SRCS:
        files += sorted(p for p in src.rglob("*.py") if "__pycache__" not in p.parts)
    return {_module_name(p): p for p in files}


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
    """Every distribution's scripts — since W-282 `fux` is fux-core's and
    `fux-merge-index` fux-writer's, and the root (fux-engine) declares none."""
    out: set[str] = set()
    for pyproject in [ROOT / "pyproject.toml", *sorted((ROOT / "packages").glob("*/pyproject.toml"))]:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        out |= {spec.split(":")[0] for spec in data.get("project", {}).get("scripts", {}).values()}
    return out


def _builtin_decoders() -> set[str]:
    """Read `[decoders] builtin` from `src/fux/constants.toml` rather than importing it.

    Importing would be simpler and would also mean the check's own answer
    depended on import side effects. Since L12 (W-225) the list lives in the
    constants file `decode.BUILTIN_MODULES` reads; parse the file.
    """
    data = tomllib.loads((SRC / "constants.toml").read_text(encoding="utf-8"))
    names = data.get("decoders", {}).get("builtin")
    assert isinstance(names, list) and names, "constants.toml carries no [decoders] builtin list"
    # W-289 phase 2: `fux_decoder_<subject>.<module>`, from the package table.
    out = set()
    for dist, row in data["plugins"]["packages"].items():
        if row["kind"] == "decoder":
            top = "fux_decoder_" + dist.removeprefix("fux-decoder-").replace("-", "_")
            out |= {f"{top}.{m}" for m in row["modules"]}
    assert {n.rsplit(".", 1)[1] for n in out} == set(names), "a builtin module no package carries"
    # Importing `fux_decoder_x.y` runs `fux_decoder_x` first.
    return out | {n.rsplit(".", 1)[0] for n in out}


def _schema_package() -> set[str]:
    """`[schema_files] package` — the one data package `schema.load` resolves
    by name (W-226). Read, not imported, for the reason the decoders are."""
    data = tomllib.loads((SRC / "constants.toml").read_text(encoding="utf-8"))
    name = data.get("schema_files", {}).get("package")
    assert isinstance(name, str) and name, "constants.toml carries no [schema_files] package"
    return {name}


def _verb_modules() -> set[str]:
    """Every module `cli.VERBS` runs a verb from (W-282). `cli.py` imports them
    by NAME so a missing layer can be refused, which hides them from the walk;
    read the table from the file, for the reason the decoders are read."""
    tree = ast.parse((SRC / "cli.py").read_text(encoding="utf-8"))
    for node in tree.body:
        target = getattr(node, "target", None) or (node.targets[0] if isinstance(node, ast.Assign) else None)
        if getattr(target, "id", None) == "VERBS":
            names = {c.value for c in ast.walk(node.value)
                     if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value.startswith("fux.")}
            assert names, "cli.VERBS names no module"
            return names
    raise AssertionError("cli.py carries no VERBS table")


def _workflow_modules() -> set[str]:
    """Every `python -m fux.<module>` a workflow runs (W-292). The release
    builds npm's bundle with `python -m fux.store.nodebundle`; since no wheel
    carries the bundle, nothing that ships imports the bundler, and the
    workflow is where its caller is declared."""
    import re

    found: set[str] = set()
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        found |= set(re.findall(r"python3? -m (fux(?:\.\w+)+)", workflow.read_text(encoding="utf-8")))
    return found


def _roots() -> set[str]:
    return (_console_scripts() | {"fux.__main__"} | _builtin_decoders() | _schema_package()
            | _verb_modules() | _workflow_modules())


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

    ⚠ **The synthetic names are NOT the historical ones any more.**
    `query/fuse.py` came back on 2026-09-05 as W-109's rank-space RRF — a live
    module with a real importer — so seeding a fake `fux.query.fuse` here made
    the self-check assert that a *reachable* module was an orphan, and it
    failed. The names below are deliberately unbuildable so this can never
    collide with a real module again; the pair the check is *about* is named in
    the prose, where a rename cannot break it.
    """
    modules = _modules()
    edges = _edges(modules)

    # The historical pair's SHAPE, under names nothing can ever claim.
    modules["fux.query.__orphan_a"] = tmp_path / "__orphan_a.py"
    modules["fux.query.__orphan_b"] = tmp_path / "__orphan_b.py"
    edges["fux.query.__orphan_a"] = {"fux.query.__orphan_b"}
    edges["fux.query.__orphan_b"] = {"fux.query.__orphan_a"}

    seen: set[str] = set()
    stack = [r for r in _roots() if r in modules]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))

    orphans = set(modules) - seen
    assert orphans == {"fux.query.__orphan_a", "fux.query.__orphan_b"}, (
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

    assert all(root.startswith(("fux.", "fux_decoder_")) for root in _roots())
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
    modules = _modules()
    for name in decoders:
        assert name in modules, f"{name} is registered in BUILTIN_MODULES but has no module"


def test_the_exception_list_is_auditable():
    """Every exception carries a reason, and there are none today."""
    for module, reason in DECLARED_EXCEPTIONS.items():
        assert reason.strip(), f"{module} is excepted with no reason given"
