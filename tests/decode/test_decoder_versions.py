"""W-166 DoD 1 — every built-in decoder carries a `VERSION`, and it is the key.

**Why a constant and not a file sha.** `binding_digests` explains the split: fux
owns this tree and can require a hand bump, and a constant does not move on a
comment. The price is that a constant nobody is made to bump stops being true —
so the discipline is a test, not a note.

⚠ **The freshness half checks the WORKING TREE against `HEAD`**, which CLAUDE.md
names as a hazard: CI reads commits, so a red here is invisible until somebody
commits. Every other test in this file needs no git and cannot go unseen.

**W-288 — decoder extensions (SR-DECODE decision 24)** adds the three gates
E4 names, one layer down: every `decode/ext/*.py` declares a `VERSION`; a
built-in decoder's `USES` is exactly the closure of the extensions it imports
(the ONE place the import graph is walked — to catch a missing declaration,
never to build the key); and a changed extension touched its `VERSION` line.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from fux import decode
from fux.acquire import decoderdigest
from fux.decode import ext as ext_pkg
from fux.constants import fixed
from fux.errors import FuxError

ROOT = Path(__file__).resolve().parents[2]
DECODE_DIR = "src/fux/decode"
EXT_DIR = f"{DECODE_DIR}/ext"
#: The pre-4.2 helper names, kept as `sys.modules` aliases for consumer copies.
ALIASES = tuple(f"_{n}" for n in fixed("decoders", "legacy_helpers"))


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"},
    ).stdout


def test_every_builtin_module_declares_a_version():
    missing = []
    for name in decode.BUILTIN_MODULES:
        module = __import__(f"fux.decode.{name}", fromlist=["VERSION"])
        version = getattr(module, "VERSION", None)
        if not isinstance(version, int) or version < 1:
            missing.append(name)
    assert not missing, (
        "these built-in decoders declare no integer `VERSION >= 1`:\n  "
        + "\n  ".join(missing)
        + "\n\nIt is what the reuse key compares; without it the decoder's "
        "digest is `<name>@0` and every version of that decoder looks alike."
    )


def test_every_binding_has_a_digest_naming_its_decoder():
    for ext, digest in decoderdigest.binding_digests().items():
        assert "@" in digest, ext
        name, _, version = digest.partition("@")
        assert name and version, ext
        assert decode.registry()[ext].name == name, ext


def test_a_version_bump_changes_only_its_own_bindings(monkeypatch):
    """The design claim, asserted rather than described.

    A corpus-wide digest would re-extract the markdown corpus for a `.pptx` fix.
    Keyed by extension, the blast radius is the extensions that decoder claims —
    **all of them**, which is why this checks a multi-extension decoder.
    """
    import fux.decode.csv as csv_mod

    before = decoderdigest.binding_digests()
    monkeypatch.setattr(csv_mod, "VERSION", csv_mod.VERSION + 1)
    decode.registry.cache_clear() if hasattr(decode.registry, "cache_clear") else None
    after = decoderdigest.binding_digests()

    moved = {ext for ext in set(before) | set(after) if before.get(ext) != after.get(ext)}
    assert moved == {".csv", ".tsv"}, moved


def test_a_changed_builtin_decoder_bumped_its_version():
    """The freshness half — the same shape `test_sr_freshness` uses for records."""
    try:
        changed = set(_git("diff", "--name-only", "HEAD").split())
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout — nothing to audit")

    behind = []
    for name in decode.BUILTIN_MODULES:
        rel = f"{DECODE_DIR}/{name}.py"
        if rel not in changed:
            continue
        diff = _git("diff", "-U0", "HEAD", "--", rel)
        if not any(
            line.startswith(("+", "-")) and "VERSION" in line for line in diff.splitlines()
        ):
            behind.append(rel)

    assert not behind, (
        "these decoders changed and their `VERSION` did not:\n  "
        + "\n  ".join(behind)
        + "\n\nBump it if the edit can change what `decode()` RETURNS — the next "
        "`fux ingest` then re-extracts the documents bound to this decoder and no "
        "others. Leave it alone only for an edit that provably cannot move a byte "
        "of output, and touch the line in the same change either way so this check "
        "sees a decision rather than an omission."
    )


# -- W-288: decoder extensions (SR-DECODE decision 24) ------------------------


def _ext_files() -> list[str]:
    return sorted(p.stem for p in (ROOT / EXT_DIR).glob("*.py") if p.stem != "__init__")


def test_every_extension_declares_a_version():
    """E4, gate 1 — and the module list and `[extensions.*]` are one list."""
    assert _ext_files() == list(ext_pkg.NAMES), (
        "the files under decode/ext/ and constants.toml [extensions.*] disagree: "
        f"files {_ext_files()}, tables {list(ext_pkg.NAMES)}"
    )
    missing = []
    for name in ext_pkg.NAMES:
        version = ext_pkg.version(name)
        if not isinstance(version, int) or version < 1:
            missing.append(name)
    assert not missing, (
        "these decoder extensions declare no integer `VERSION >= 1`:\n  " + "\n  ".join(missing)
    )


def _imports(path: Path) -> list[tuple[str, tuple[str, ...]]]:
    """`(module, names)` for every `import`/`from … import` in a file, nested ones too."""
    out: list[tuple[str, tuple[str, ...]]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out.extend((alias.name, ()) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.append((node.module, tuple(alias.name for alias in node.names)))
    return out


def _reached(module: str, names: tuple[str, ...]) -> list[str]:
    """The `fux.decode` modules one import statement reaches, as dotted names."""
    if module == "fux.decode" or module == "fux.decode.ext":
        return [f"{module}.{n}" for n in names]
    return [module] if module.startswith("fux.decode.") else []


def _path_of(module: str) -> Path | None:
    rel = module.removeprefix("fux.").replace(".", "/")
    for candidate in (ROOT / "src/fux" / f"{rel}.py",):
        if candidate.is_file():
            return candidate
    return None


def _closure(decoder: str) -> set[str]:
    """Every decoder extension a built-in decoder reaches through its imports —
    directly, through another extension, or through another decoder."""
    seen: set[str] = set()
    found: set[str] = set()
    todo = [f"fux.decode.{decoder}"]
    while todo:
        module = todo.pop()
        if module in seen:
            continue
        seen.add(module)
        path = _path_of(module)
        if path is None:
            continue
        for imported, names in _imports(path):
            for target in _reached(imported, names):
                if target.startswith("fux.decode.ext."):
                    found.add(target.rsplit(".", 1)[1])
                todo.append(target)
    return found


@pytest.mark.parametrize("name", decode.BUILTIN_MODULES)
def test_a_decoders_uses_is_the_closure_of_what_it_imports(name):
    """E4, gate 2 — a missing `USES` entry is the trap W-288 closes, back again.

    **Exactly the closure, not a superset**: a name declared and never called
    re-extracts a format for an edit that cannot touch it.
    """
    module = __import__(f"fux.decode.{name}", fromlist=["USES"])
    declared = getattr(module, "USES", None)
    assert isinstance(declared, tuple), f"{name} declares no USES tuple"
    assert len(set(declared)) == len(declared), f"{name}: USES repeats a name"
    reached = _closure(name)
    assert set(declared) == reached, (
        f"{name}: USES = {declared}, but its imports reach the decoder extensions "
        f"{sorted(reached)}. A decoder declares every extension it calls, through "
        "another extension or another decoder too — constants.toml "
        f"[decoders.{name}] uses."
    )


@pytest.mark.parametrize("name", decode.BUILTIN_MODULES)
def test_a_builtin_decoder_imports_extensions_by_their_ext_name(name):
    """The pre-4.2 names are aliases for consumer copies, never for the built-ins."""
    path = ROOT / DECODE_DIR / f"{name}.py"
    old = [
        target
        for imported, names in _imports(path)
        for target in _reached(imported, names)
        if target.rsplit(".", 1)[1] in ALIASES
    ]
    assert not old, f"{name} imports {old}; import fux.decode.ext.<name> instead"


@pytest.mark.parametrize("alias", ALIASES)
def test_an_old_helper_name_is_the_extension_itself(alias):
    """An alias, never a copy: one module object, one `ContextVar`, one cache."""
    import importlib

    old = importlib.import_module(f"fux.decode.{alias}")
    new = importlib.import_module(f"fux.decode.ext.{alias.lstrip('_')}")
    assert old is new


def test_an_extension_bump_moves_exactly_the_decoders_that_use_it(monkeypatch):
    """E3 — the blast radius stays per suffix, one layer down."""
    import fux.decode.ext.table as table_mod

    before = decoderdigest.binding_digests()
    monkeypatch.setattr(table_mod, "VERSION", table_mod.VERSION + 1)
    after = decoderdigest.binding_digests()
    moved = {ext for ext in before if before[ext] != after[ext]}
    expected = {
        ext
        for ext, decoder in decode.registry().items()
        if "table" in decoder.uses
    }
    assert moved == expected
    assert {".csv", ".tsv", ".docx", ".html", ".xlsx", ".eml"} <= moved
    assert not moved & {".pdf", ".pptx", ".json", ".svg"}


def test_the_digest_composes_in_declared_order():
    """E3's shape: `<decoder>@<v>+<ext>@<v>+…`, extensions in `USES` order."""
    import fux.decode.docx as docx_mod

    digest = decoderdigest.binding_digests()[".docx"]
    expected = f"docx@{docx_mod.VERSION}" + "".join(
        f"+{n}@{ext_pkg.version(n)}" for n in docx_mod.USES
    )
    assert digest == expected


def _consumer(tmp_path: Path, body: str) -> Path:
    (tmp_path / ".git").mkdir()
    folder = tmp_path / ".fux" / "decoders"
    folder.mkdir(parents=True)
    (folder / "logdoc.py").write_text(body, encoding="utf-8")
    return tmp_path


def test_a_consumer_decoder_carries_its_uses_in_the_key(tmp_path):
    """A seeded copy imports `fux.decode.ext` from the installed engine, so an
    upgrade moves its output while its sha stands still — the tail is what
    reaches it."""
    root = _consumer(
        tmp_path,
        'EXTENSIONS = (".logdoc",)\nUSES = ("table",)\n'
        "def decode(raw, rel_path):\n    return raw.decode()\n",
    )
    decoder = decode.decoder_named("logdoc", root)
    digest = decoderdigest.of(decoder)
    assert digest.startswith("logdoc@sha:")
    assert digest.endswith(f"+table@{ext_pkg.version('table')}")


@pytest.mark.parametrize(
    "uses",
    ['"table"', '("tabel",)', '("table", "table")', "(1,)"],
)
def test_a_bad_uses_is_a_hard_error_naming_the_file(tmp_path, uses):
    root = _consumer(
        tmp_path,
        f'EXTENSIONS = (".logdoc",)\nUSES = {uses}\n'
        "def decode(raw, rel_path):\n    return raw.decode()\n",
    )
    with pytest.raises(FuxError, match="logdoc.py"):
        decode.decoder_named("logdoc", root)


def test_a_changed_extension_bumped_its_version():
    """E4, gate 3 — `test_a_changed_builtin_decoder_bumped_its_version`, one layer down."""
    try:
        changed = set(_git("diff", "--name-only", "HEAD").split())
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout — nothing to audit")

    behind = []
    for name in ext_pkg.NAMES:
        rel = f"{EXT_DIR}/{name}.py"
        if rel not in changed:
            continue
        diff = _git("diff", "-U0", "HEAD", "--", rel)
        if not any(
            line.startswith(("+", "-")) and "VERSION" in line for line in diff.splitlines()
        ):
            behind.append(rel)

    assert not behind, (
        "these decoder extensions changed and their `VERSION` did not:\n  "
        + "\n  ".join(behind)
        + "\n\nBump `constants.toml [extensions.<name>] version` if the edit can change "
        "what a decoder using it RETURNS — the next `fux ingest` then re-extracts the "
        "documents of every decoder whose USES names it, and no others. Either way, "
        "touch the `VERSION` line's comment so this check sees a decision rather than "
        "an omission."
    )
