"""The Node read plane's bundler — one artefact per plane, built at publish.

**Why this file exists.** [L10](../../../records/0011_LAW-10-bundled-output.md)
says the consumer is served build output, never source: what `fux setup` writes
into `.fux/node/` and what the npm tarball exports is ONE generated `.mjs`,
never a copy of `node/src/**`. This is the thing that generates it.

⚠ **Carved out of `store/`'s claim for a different DECISION, not a different
concern** (`records/README.md` §Ownership) — everything else under `store/` is
the committed index; this is a build-time tool that never touches one.

**Deterministic, and that is a promise adopted voluntarily.** Same sources →
byte-identical bundle. [L3](../../../records/0005_LAW-3-deterministic.md)
binds the *index*, not a build artefact, so nobody should later cite the wrong
authority for it — SR-NODE-SEARCH decision 14 says so out loud. What makes it
hold: modules are emitted in a topological order with a path tie-break, no
clock is read, and nothing is derived from a set or a dict iteration whose order
is not already fixed by sorting.

**Zero-dependency, in-repo, and NOT a parser.** It is a module concatenator
with one structural trick: each module becomes an IIFE returning its exports,
so nothing has to be renamed and no scope analysis is needed.

    const __m_src_errors = (() => {
      class FuxError extends Error { ... }
      return { FuxError };
    })();

The trick is what keeps it honest at this size. A flat concatenation would have
to rename — `signals`, `isArchivedLoc`, `STOPWORDS`, `DEPTH` and `K` are each
exported by two different modules — and a renaming bundler without a real JS
parser is a silent-wrong-answer machine. **Every unsupported form raises**
(`FuxError`) rather than being skipped: a bundle missing a statement compiles
and answers differently, which is the one failure mode a build step may never
have.

What it supports, because it is all this tree uses (asserted by
`tests/test_node_bundle.py`):

| form | becomes |
|---|---|
| `import { a, b as c } from "./x.mjs"` | `const { a, b: c } = __m_x;` |
| `import * as ns from "./x.mjs"` | `const ns = __m_x;` |
| `import { readFileSync } from "node:fs"` | hoisted to the bundle's real top |
| `export function f()` / `const` / `class` | the `export` keyword stripped |
| `export { a, b as c }` | folded into the module's returned object |

Anything else — `export default`, `export … from`, a bare side-effect
`import "x"` — raises. When one lands in `node/`, teach this file about it in
the same change.
"""

from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path

from ..errors import FuxError

#: The one entry point. `fux.mjs` is both the CLI and — since the bundle is the
#: npm package's `exports` target too — the library surface, which it
#: re-exports from `src/index.mjs`. One entry, one artefact (L10 decision 1).
ENTRY = "fux.mjs"

#: What ships beside the bundle. The manifest and the tool descriptions are
#: DATA, not code, so L10 does not reach them: `mcp-tools.json` is the file
#: both runtimes read so two hand-maintained copies cannot drift
#: (SR-MCP decision 11), and a `package.json` is what makes the directory a
#: package at all.
SIDECARS = ("package.json", "mcp-tools.json", "README.md")

_IMPORT_NAMED = re.compile(r'^import\s*\{(?P<names>[^}]*)\}\s*from\s*"(?P<spec>[^"]+)"\s*;?\s*$', re.S)
_IMPORT_STAR = re.compile(r'^import\s*\*\s*as\s+(?P<ns>\w+)\s*from\s*"(?P<spec>[^"]+)"\s*;?\s*$', re.S)
_EXPORT_LIST = re.compile(r"^export\s*\{(?P<names>[^}]*)\}\s*;?\s*$", re.S)
_EXPORT_DECL = re.compile(
    r"^export\s+(?:async\s+)?(?:function\s*\*?|const|let|var|class)\s+(?P<name>\w+)"
)


def _module_var(rel: str) -> str:
    """`src/query/rank.mjs` -> `__m_src_query_rank`. Stable, and collision-free
    because it is derived from a path that is unique by construction."""
    stem = rel[: -len(".mjs")] if rel.endswith(".mjs") else rel
    return "__m_" + re.sub(r"[^0-9A-Za-z]+", "_", stem)


def _split_bindings(names: str) -> "list[tuple[str, str]]":
    """`a, b as c` -> `[("a", "a"), ("b", "c")]`, in source order."""
    out: list[tuple[str, str]] = []
    for chunk in names.split(","):
        piece = chunk.strip()
        if not piece:
            continue
        if " as " in piece:
            src, _, dst = piece.partition(" as ")
            out.append((src.strip(), dst.strip()))
        else:
            out.append((piece, piece))
    return out


def _statements(text: str, rel: str) -> "list[str]":
    """Top-level lines, with a multi-line `import`/`export {}` joined into one.

    Line-based on purpose: every statement this bundler rewrites begins in
    column 1, and a brace-counting scanner would be a parser with none of a
    parser's guarantees.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(("import", "export {")) and not line.rstrip().endswith((";", "}")):
            buf = [line]
            while i + 1 < len(lines) and not buf[-1].rstrip().endswith((";", '"', "}")):
                i += 1
                buf.append(lines[i])
            out.append("\n".join(buf))
        else:
            out.append(line)
        i += 1
    return out


class _Module:
    """One parsed `.mjs` file: its local dependencies, its exports, its body."""

    def __init__(self, rel: str, text: str, node_dir: Path) -> None:
        self.rel = rel
        self.deps: list[str] = []
        self.builtins: list[tuple[str, str, str]] = []  # (specifier, imported, local)
        self.exports: list[tuple[str, str]] = []  # (local name, exported name)
        self.prologue: list[str] = []
        self.body: list[str] = []
        #: The entry's `#!/usr/bin/env node`, if it has one. It has to move to
        #: line 1 of the BUNDLE — `bin` points at that file, and a shebang
        #: anywhere else is a syntax error rather than a comment.
        self.shebang: str | None = None
        self._parse(text)

    # -- parsing -----------------------------------------------------------

    def _resolve(self, spec: str) -> str:
        if not spec.startswith("."):
            raise FuxError(
                f"{self.rel}: `{spec}` is a bare package import. The Node read plane has no "
                "dependencies (L1) and the bundler cannot resolve one."
            )
        return posixpath.normpath(posixpath.join(posixpath.dirname(self.rel), spec))

    def _parse(self, text: str) -> None:
        if text.startswith("#!"):
            first, _, rest = text.partition("\n")
            self.shebang = first
            text = rest
        for stmt in _statements(text, self.rel):
            if stmt.startswith("import"):
                self._import(stmt)
            elif stmt.startswith("export"):
                self._export(stmt)
            else:
                self.body.append(stmt)

    def _import(self, stmt: str) -> None:
        named = _IMPORT_NAMED.match(stmt)
        star = _IMPORT_STAR.match(stmt)
        if named is None and star is None:
            raise FuxError(
                f"{self.rel}: the bundler does not understand this import — teach it, do not "
                f"skip it:\n    {stmt.strip()}"
            )
        spec = (named or star).group("spec")
        if spec.startswith("node:"):
            if star is not None:
                raise FuxError(
                    f"{self.rel}: `import * as` from a builtin is not supported yet:\n"
                    f"    {stmt.strip()}"
                )
            for imported, local in _split_bindings(named.group("names")):
                self.builtins.append((spec, imported, local))
            return
        target = self._resolve(spec)
        self.deps.append(target)
        var = _module_var(target)
        if star is not None:
            self.prologue.append(f"const {star.group('ns')} = {var};")
            return
        pairs = ", ".join(
            local if imported == local else f"{imported}: {local}"
            for imported, local in _split_bindings(named.group("names"))
        )
        self.prologue.append(f"const {{ {pairs} }} = {var};")

    def _export(self, stmt: str) -> None:
        listed = _EXPORT_LIST.match(stmt)
        if listed is not None:
            self.exports.extend(
                (local, exported) for local, exported in _split_bindings(listed.group("names"))
            )
            return
        decl = _EXPORT_DECL.match(stmt)
        if decl is None:
            raise FuxError(
                f"{self.rel}: the bundler does not understand this export — `export default` "
                f"and `export … from` are unsupported by decision:\n    {stmt.strip()}"
            )
        name = decl.group("name")
        self.exports.append((name, name))
        self.body.append(stmt[len("export ") :])

    # -- emitting ----------------------------------------------------------

    def render(self) -> str:
        var = _module_var(self.rel)
        returned = ", ".join(
            local if local == exported else f"{exported}: {local}"
            for local, exported in self.exports
        )
        lines = [f"// ── {self.rel} " + "─" * max(0, 68 - len(self.rel)), f"const {var} = (() => {{"]
        lines += [f"  {line}" if line else "" for line in self.prologue]
        if self.prologue:
            lines.append("")
        lines += [f"  {line}" if line.strip() else "" for line in self.body]
        lines.append(f"  return {{ {returned} }};")
        lines.append("})();")
        return "\n".join(lines).rstrip() + "\n"


def _read_modules(node_dir: Path) -> "dict[str, _Module]":
    """Every module reachable from `ENTRY`, parsed. Nothing else is bundled."""
    mods: dict[str, _Module] = {}
    pending = [ENTRY]
    while pending:
        rel = pending.pop()
        if rel in mods:
            continue
        path = node_dir / rel
        if not path.is_file():
            raise FuxError(f"the Node reader is incomplete: {rel} is imported but absent")
        mod = _Module(rel, path.read_text(encoding="utf-8"), node_dir)
        mods[rel] = mod
        pending.extend(sorted(mod.deps, reverse=True))
    return mods


def _order(mods: "dict[str, _Module]") -> "list[str]":
    """Topological, with a path tie-break so the order is a function of the
    sources and of nothing else — the determinism promise, mechanically.

    A cycle raises. The IIFE shape cannot express one, and an ESM cycle that
    works by hoisting would become a `ReferenceError` in the bundle — silently,
    at whichever call site runs first.
    """
    order: list[str] = []
    state: dict[str, int] = {}

    def visit(rel: str, stack: "list[str]") -> None:
        mark = state.get(rel, 0)
        if mark == 2:
            return
        if mark == 1:
            cycle = " -> ".join([*stack, rel])
            raise FuxError(f"the Node reader has an import cycle, which cannot be bundled: {cycle}")
        state[rel] = 1
        for dep in sorted(set(mods[rel].deps)):
            visit(dep, [*stack, rel])
        state[rel] = 2
        order.append(rel)

    for rel in sorted(mods):
        visit(rel, [])
    return order


def _builtin_imports(mods: "dict[str, _Module]") -> "list[str]":
    """The `node:` imports, hoisted, deduplicated, and CHECKED for a collision.

    A module body sits inside an IIFE, so it closes over these names. Two
    modules binding the same local name to two different builtin symbols would
    make one of them silently wrong, so that case raises instead.
    """
    bound: dict[str, tuple[str, str]] = {}
    for rel in sorted(mods):
        for spec, imported, local in mods[rel].builtins:
            prior = bound.get(local)
            if prior is not None and prior != (spec, imported):
                raise FuxError(
                    f"two builtin imports bind `{local}` differently — "
                    f"{prior[0]}.{prior[1]} and {spec}.{imported} (in {rel}). "
                    "Rename one at its source; the bundler will not guess."
                )
            bound[local] = (spec, imported)

    by_spec: dict[str, list[str]] = {}
    for local, (spec, imported) in sorted(bound.items()):
        piece = imported if imported == local else f"{imported} as {local}"
        by_spec.setdefault(spec, []).append(piece)
    return [f'import {{ {", ".join(names)} }} from "{spec}";' for spec, names in sorted(by_spec.items())]


def version(node_dir: Path) -> str:
    """The version the bundle will carry — derived, never hand-written.

    Read from `package.json`, which is the file npm reads too, so the bundle
    cannot be a fifth version site (`scripts/check-version-parity.py`).
    """
    meta = json.loads((node_dir / "package.json").read_text(encoding="utf-8"))
    got = meta.get("version")
    if not isinstance(got, str) or not got:
        raise FuxError(f"{node_dir / 'package.json'} carries no version string")
    return got


def bundle(node_dir: Path) -> str:
    """The one `.mjs` a consumer gets. Same sources → byte-identical output."""
    mods = _read_modules(node_dir)
    order = _order(mods)
    head = [
        *( [mods[ENTRY].shebang] if mods[ENTRY].shebang else [] ),
        "// fux-engine " + version(node_dir) + " — the Node read plane, bundled.",
        "//",
        "// 🔴 GENERATED. Do not edit: every `fux setup` at a different engine version",
        "// overwrites this file. The sources are `node/fux.mjs` and `node/src/**` in",
        "// the fux repository; `python -m fux.store.nodebundle <node dir>` regenerates",
        "// it byte for byte from a checkout of the matching tag.",
        "//",
        "// One artefact per plane — L10, records/0011_LAW-10-bundled-output.md. Each",
        "// source module is an IIFE returning its exports, so nothing is renamed and",
        "// the bundle reads as its sources in dependency order.",
        "",
        *_builtin_imports(mods),
        "",
    ]
    parts = [mods[rel].render() for rel in order]
    entry = _module_var(ENTRY)
    exported = ", ".join(exported for _, exported in mods[ENTRY].exports)
    tail = [
        "// ── the package surface " + "─" * 47,
        f"const {{ {exported} }} = {entry};",
        f"export {{ {exported} }};",
        "",
    ]
    return "\n".join(head) + "\n".join(parts) + "\n" + "\n".join(tail)


def bundle_files(node_dir: Path) -> "list[tuple[str, bytes]]":
    """`(relative path, bytes)` for the whole published payload — the bundle
    plus its sidecars, and NOTHING else. This is what the wheel carries at
    `fux/templates/node/`, what npm packs, and what `fux setup` writes."""
    out = [(ENTRY, bundle(node_dir).encode("utf-8"))]
    for name in SIDECARS:
        path = node_dir / name
        if not path.is_file():
            raise FuxError(f"the Node reader is incomplete: {name} is missing from {node_dir}")
        out.append((name, path.read_bytes()))
    return sorted(out)


def write(node_dir: Path, out_dir: Path) -> "list[Path]":
    """Write the payload into `out_dir`, creating it. Returns what was written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rel, data in bundle_files(node_dir):
        path = out_dir / rel
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        written.append(path)
    return written


def main(argv: "list[str] | None" = None) -> int:
    """`python -m fux.store.nodebundle [node dir] [out dir]` — the release step.

    Defaults are the repository's own layout, so the command in the generated
    header works from a fresh checkout with no arguments.
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    here = Path(__file__).resolve().parents[3]
    node_dir = Path(args[0]) if args else here / "node"
    out_dir = Path(args[1]) if len(args) > 1 else node_dir / "dist"
    written = write(node_dir, out_dir)
    total = sum(p.stat().st_size for p in written)
    # ASCII on purpose: this prints in the release workflow and on any console,
    # and `tests/test_windows_console_safe.py` fails a `print` cp1252 cannot
    # encode. The em-dash in the BUNDLE's own header is fine -- that is a file
    # written as UTF-8 bytes, never a stream.
    print(f"[ok] bundled {node_dir}/ -> {out_dir}/ - {len(written)} files, {total:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
