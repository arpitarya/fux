"""Every Node module names a Python twin, and the map is DERIVED (W-107 R4).

R4's rule is *"same relative path, same stem, one Node file per Python
module — then the twin map is derived, not hand-maintained"*, with the
exemption list as the only hand-written part. This is that test, and it was
the last thing W-107 owed after the `fux doctor` PATH row.

**Why it is worth a file.** `node/` is a ~5 000-line transcription of `src/fux/`
held equal by the differential arm. The arm answers *"do the two disagree on
this corpus?"* — it cannot answer *"did somebody change the Python half and
forget the Node half exists?"*, because a Node module that was never updated
still agrees with itself. A corpus that happens not to exercise the changed
branch makes that silent. This test is the structural half of the same
guarantee, in the shape `test_adr_freshness.py` uses for records.

Three ways a Node module may be accounted for, in order:

1. **Derived** — `node/src/x/y.mjs` -> `src/fux/x/y.py`, or `src/fux/x/_y.py`
   for a private module. No hand-maintenance at all.
2. **Declared** — the module's own header names its twin as a `src/fux/...py`
   path. `config/root.mjs` (a `find_root`-only slice of `config.py`),
   `index.mjs` (`api.py`), `query/run.mjs` and `verbs/*.mjs` (the deliberate
   one-to-many off `query/__init__.py`) are all in this class. **The file
   declares itself; this test only checks the declaration resolves.**
3. **Exempt** — no Python twin exists by design. Two files, listed below.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_SRC = ROOT / "node" / "src"
PY_SRC = ROOT / "src" / "fux"

#: The ONLY hand-maintained part. Both are declared exempt by W-107 R4 — they
#: have no Python twin because they exist to reproduce behaviour the Python
#: half gets from its own runtime, and that is exactly where the divergence
#: risk concentrates. Naming them is the point; letting them be an unexplained
#: gap is what R4 refused.
EXEMPT = {
    "compat/pyfloat.mjs",  # Python's repr layout + round-half-even; CPython IS the twin
    "hash/blake2b.mjs",  # RFC 7693 by hand, because hashlib is not there
}

_DECLARED = re.compile(r"`?(src/fux/[A-Za-z0-9_/]+\.py)`?")


def _node_modules() -> list[str]:
    return sorted(p.relative_to(NODE_SRC).as_posix() for p in NODE_SRC.rglob("*.mjs"))


def _derived(rel: str) -> str | None:
    """`x/y.mjs` -> `src/fux/x/y.py`, or `src/fux/x/_y.py` for a private module."""
    stem = Path(rel).with_suffix(".py")
    for candidate in (stem, stem.with_name("_" + stem.name)):
        if (PY_SRC / candidate).is_file():
            return (Path("src/fux") / candidate).as_posix()
    return None


def _declared(rel: str) -> str | None:
    """The twin the module names in its own header, if it names one."""
    head = "".join((NODE_SRC / rel).read_text(encoding="utf-8").splitlines(keepends=True)[:14])
    m = _DECLARED.search(head)
    return m.group(1) if m else None


def twin_map() -> dict[str, str | None]:
    """Every Node module -> its Python twin, or None when exempt."""
    out: dict[str, str | None] = {}
    for rel in _node_modules():
        out[rel] = None if rel in EXEMPT else (_derived(rel) or _declared(rel))
    return out


def test_the_tree_is_not_empty():
    """A map derived from a glob is green when the glob finds nothing."""
    assert len(_node_modules()) > 20, "node/src looks empty — the path rule moved"


def test_every_node_module_is_derived_declared_or_exempt():
    unaccounted = [rel for rel, twin in twin_map().items() if twin is None and rel not in EXEMPT]
    assert not unaccounted, (
        "these Node modules name no Python twin and are not exempt:\n  "
        + "\n  ".join(unaccounted)
        + "\n\nEither put the module at its twin's relative path, name the twin as a "
        "`src/fux/....py` path in the module's header comment, or add it to EXEMPT "
        "with the reason it has no twin."
    )


def test_every_declared_twin_actually_exists():
    broken = [
        f"{rel} -> {twin}"
        for rel, twin in twin_map().items()
        if twin is not None and not (ROOT / twin).is_file()
    ]
    assert not broken, (
        "these Node modules name a Python twin that is not there — the Python half "
        "moved or was renamed and the header still points at the old path:\n  "
        + "\n  ".join(broken)
    )


def test_no_exemption_hides_a_real_twin():
    """An exemption is a claim that no twin exists. Check the claim."""
    wrong = [rel for rel in sorted(EXEMPT) if _derived(rel)]
    assert not wrong, (
        "these files are in EXEMPT but a Python twin DOES exist at the derived path:\n  "
        + "\n  ".join(f"{rel} -> {_derived(rel)}" for rel in wrong)
        + "\n\nAn exemption that hides a twin turns this test off for that file."
    )


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
        env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"},
    ).stdout


def test_working_tree_does_not_change_a_python_module_behind_its_node_twin():
    """The freshness half — the same shape `test_adr_freshness` uses for records.

    The differential arm cannot catch this: a Node module nobody updated still
    agrees with itself, and it only disagrees with Python on a corpus that
    exercises the changed branch. Heard here, it costs a minute.
    """
    try:
        changed = set(_git("diff", "--name-only", "HEAD").split())
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout — nothing to audit")
    if not changed:
        return

    behind = [
        f"{twin} changed, node/src/{rel} did not"
        for rel, twin in twin_map().items()
        if twin in changed and f"node/src/{rel}" not in changed
    ]
    assert not behind, (
        "the Python half moved and its Node twin did not:\n  "
        + "\n  ".join(behind)
        + "\n\nPort the change, or say in the commit message why the twin is unaffected. "
        "The differential arm will NOT catch this on a corpus that misses the branch."
    )
