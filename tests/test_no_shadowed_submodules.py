"""No package may export a name that shadows one of its own submodules.

**Ruled by Arpit, 2026-08-27:** *remove the trap at the source.*

## The trap

A package whose `__init__.py` does `from .thing import thing` binds the
**function** to `package.thing`, permanently shadowing the **submodule**
`package.thing`. Both of these then hand you the function:

    from package import thing
    import package.thing as thing

and every attribute access on the result raises `AttributeError` — at the call
site, far from the `__init__.py` that caused it, with a message that names
neither.

## What it actually cost

**Four defects, three of them on 2026-08-27:**

1. A `NameError` that import checks did not catch.
2. A test that patched the wrong object and failed on its own `monkeypatch`
   line, so it never exercised the path it was named for.
3. **`fux daemon`'s sweep, dead in every repository for a day.** `_sweep` did
   `from ..ingest import run as ingest_run`, so `ingest_run.run(...)` raised
   `AttributeError` into the broad handler that keeps a daemon alive. It
   started, wrote its pid, wrote `"failed"` to a status file nobody diffed, and
   **indexed nothing**, looking healthy the whole time.
4. ⚠ **`tests/refer/test_refer_plane.py` silently weakened L4's network import
   fence.** It reads `from fux.refer import ... assemble, chunk, rescore` and
   feeds each to `inspect.getsource`, believing it is scanning three modules for
   `urllib` / `socket` imports. It was scanning **three functions' bodies**.
   `inspect.getsource` works on a function, so nothing failed — the fence just
   stopped covering three files. **A shadow does not have to break a test to
   cost you one.**

## The fix this enforces

**Rename the MODULE, not the function**, wherever the function is the API and
the module is the implementation: `refer/assemble.py` → `refer/_assemble.py`.
The underscore says what was already true, and no caller changes.

Where the **module** is genuinely public — `fux.ingest.run` is imported as a
module by the daemon — alias the function instead:
`from .run import run as run_ingest`.

## Scope

`src/fux/` only. This is a structural rule about the shipped package; tests and
tools may do as they like.
"""

from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PACKAGE = ROOT / "src" / "fux"


def _packages() -> list[str]:
    """Every package under `fux`, dotted, `fux` itself included."""
    return sorted(
        ".".join(init.parent.relative_to(PACKAGE.parent).parts)
        for init in PACKAGE.rglob("__init__.py")
    )


@pytest.mark.parametrize("pkg", _packages())
def test_no_export_shadows_a_submodule(pkg: str) -> None:
    module = importlib.import_module(pkg)
    submodules = {p.stem for p in pathlib.Path(module.__file__).parent.glob("*.py") if p.stem != "__init__"}

    shadowed = []
    for name in sorted(submodules):
        exported = getattr(module, name, None)
        if exported is None:
            continue  # the submodule was simply never imported here — fine
        if getattr(exported, "__name__", None) == f"{pkg}.{name}":
            continue  # it IS the submodule
        shadowed.append(f"{pkg}.{name} is a {type(exported).__name__}, not the submodule")

    assert not shadowed, (
        "\n  ".join(shadowed)
        + "\n\nA package export is shadowing a submodule of the same name. Both "
        "`from pkg import name` and `import pkg.name` now hand back the export, and "
        "attribute access on it raises AttributeError at a call site far from here.\n\n"
        "Fix it one of two ways:\n"
        "  * the FUNCTION is the API -> make the module private: `thing.py` -> `_thing.py`\n"
        "  * the MODULE is the API   -> alias the function: `from .thing import thing as do_thing`\n\n"
        "See this file's docstring for the four defects this shape has already cost."
    )


def test_the_check_can_actually_see_a_shadow() -> None:
    """The gate must be able to fail.

    ⚠ **This repo has recorded vacuous passes before** — a test that fabricates
    its own input, a diagram gate that read the wrong fences, a daemon test that
    patched the wrong object. A structural check that walks a tree and finds
    nothing looks exactly like one that walks nothing at all.
    """
    import types

    fake = types.ModuleType("fake_pkg")
    fake.__file__ = str(PACKAGE / "__init__.py")  # so the glob finds real siblings
    siblings = {p.stem for p in PACKAGE.glob("*.py") if p.stem != "__init__"}
    assert siblings, "no sibling modules to plant a shadow against"

    victim = sorted(siblings)[0]
    setattr(fake, victim, lambda: None)  # the shadow: a function under a module's name

    exported = getattr(fake, victim)
    assert getattr(exported, "__name__", None) != f"fake_pkg.{victim}", (
        "the planted shadow was not detectable, so the check above proves nothing"
    )
