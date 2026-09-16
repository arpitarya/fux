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
guarantee, in the shape `test_sr_freshness.py` uses for records.

Three ways a Node module may be accounted for, in order:

1. **Derived** — `node/src/x/y.mjs` -> `src/fux/x/y.py`, or `src/fux/x/_y.py`
   for a private module. No hand-maintenance at all.
2. **Declared** — the module's own header names its twin as a `src/fux/...py`
   path. `config/root.mjs` (a `find_root`-only slice of `config.py`),
   `index.mjs` (`api.py`), `query/run.mjs` and `verbs/*.mjs` (the deliberate
   one-to-many off `query/__init__.py`) are all in this class. **The file
   declares itself; this test only checks the declaration resolves.**
3. **Exempt** — no Python twin exists by design. Three files, listed below;
   each reproduces something CPython supplies from its runtime or stdlib.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_SRC = ROOT / "node" / "src"
PY_SRC = ROOT / "src" / "fux"

#: The ONLY hand-maintained part. All three are declared exempt by W-107 R4 —
#: they have no Python twin because they exist to reproduce behaviour the
#: Python half gets **from its own runtime or standard library**, and that is
#: exactly where the divergence risk concentrates. Naming them is the point;
#: letting them be an unexplained gap is what R4 refused.
EXEMPT = {
    "compat/pyfloat.mjs",  # Python's repr layout + round-half-even; CPython IS the twin
    "hash/blake2b.mjs",  # RFC 7693 by hand, because hashlib is not there
    "config/toml.mjs",  # CPython's `tomllib` IS the twin, and it is stdlib (W-107 R4)
}

#: NARROWED twins — the Node file mirrors ONE symbol of a much larger Python
#: module, so "the twin file changed" is the wrong freshness question for it.
#: `config.py` is the case: `root.mjs` is a `find_root`-only slice (W-107 R4),
#: and `config.py` moves constantly for reasons `find_root` never sees. The
#: freshness check narrows to the named symbol using git's own hunk context —
#: the same narrowing `records/README.md`'s `describes` table applies to
#: records. **The twin must still EXIST**; only the freshness half narrows.
NARROWED = {
    "config/root.mjs": "find_root",
    # `gitdir.py` is the git-backed WALK — what ingest visits, what it excludes,
    # a document's `mtime`. Node does not ingest; what crosses is the pair of
    # functions the QUERY plane calls, and the walk moves constantly for
    # reasons `archived_dirs` never sees.
    "ingest/gitdir.mjs": "archived_dirs",
    # `priors.py` carries the git half (`git_commit_times`) as well, which is
    # an ingest concern with no Node twin. `recency_multiplier` was the narrowed
    # symbol until 2026-09-13, when it was deleted with the knob it served
    # (W-152); `superseded_ids` is what is left on both sides.
    "ingest/priors.mjs": "superseded_ids",
    # `query/__init__.py` is a one-to-many twin and `run.mjs` is the narrow end
    # of it: its own header says "twin of the PURE half", and `verbs/ask.mjs`,
    # `verbs/find.mjs` and `verbs/answer.mjs` each declare the same Python file
    # for the half they project. So a change to what a verb PRINTS moves the
    # Python module without touching anything `runQuery` mirrors, and before
    # 2026-09-14 that reported `run.mjs` as behind while the three files that
    # actually carry the change sat updated beside it (W-165 fix 2).
    #
    # ⚠ **This narrows `run.mjs` and nothing else.** The three verb modules stay
    # unnarrowed — the whole file is the twin there — so a ranking change in
    # `run_query` is still caught by this row, and a printing change is still
    # caught by theirs. Narrowing the verbs too would leave the pair unguarded.
    "query/run.mjs": "run_query",
    # `sourcelist.py` parses BOTH committed source lists; `sourcelist.mjs` is
    # the **`dirs` half only**, and its own header says so — Node never fetches
    # ([SR-NODE-SEARCH](../records/0153_node-search.md) decision 3), so `fetch`,
    # `meta`, `keep`, `ttl` and `update` decide nothing on that side. The one
    # fact that crosses is which directories are declared `archived=true`.
    #
    # ⚠ **Added 2026-09-15 by W-178**, which made `fetch=` a typed attribute:
    # a change entirely inside the `URLS` spec reported `sourcelist.mjs` as
    # behind, and porting it would have meant teaching the Node reader a
    # grammar for a list it does not read. Same shape as `ingest/gitdir.mjs`
    # above, for the same reason.
    #
    # 🔴 **Narrowed to `parse`, and that leaves a gap this mechanism cannot
    # close.** The Node side also mirrors the `dirs` **attribute tuple**
    # (`DIRS_ATTRIBUTES`), which lives at module level — and narrowing works off
    # git's hunk-context header, which names an enclosing `def`. A constant has
    # none. So that half is covered by a **parity** test instead:
    # `test_node_config_parity.py::test_the_dirs_attribute_set_is_the_python_one`
    # holds the two tuples equal, which is the stronger check anyway — it
    # asserts the fact rather than asserting that somebody edited a file.
    "ingest/sourcelist.mjs": "parse",
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


def test_every_narrowed_twin_names_a_real_module():
    """A narrowing is only honest if the module and the symbol both exist."""
    for rel, symbol in NARROWED.items():
        twin = twin_map().get(rel)
        assert twin, f"{rel} is NARROWED but has no twin at all"
        src = (ROOT / twin).read_text(encoding="utf-8")
        assert f"def {symbol}" in src, f"{twin} has no `def {symbol}` — the narrowing is stale"


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
        encoding="utf-8",
        check=True,
        env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"},
    ).stdout


def _symbol_touched(py_path: str, symbol: str | None) -> bool:
    """For a narrowed twin, did the change actually reach the mirrored symbol?

    Uses git's hunk-context header (`@@ ... @@ def find_root(`), which names the
    enclosing definition. A module-level or other-function change reports a
    different context and is correctly ignored. Unnarrowed twins always answer
    True — the whole file is the twin.
    """
    if symbol is None:
        return True
    try:
        diff = _git("diff", "-U0", "HEAD", "--", py_path)
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return True  # cannot narrow -> do not silently pass
    return any(
        symbol in line
        for line in diff.splitlines()
        if line.startswith("@@") or line.startswith(("+", "-"))
    )


def test_working_tree_does_not_change_a_python_module_behind_its_node_twin():
    """The freshness half — the same shape `test_sr_freshness` uses for records.

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
        if twin in changed
        and f"node/src/{rel}" not in changed
        and _symbol_touched(twin, NARROWED.get(rel))
    ]
    assert not behind, (
        "the Python half moved and its Node twin did not:\n  "
        + "\n  ".join(behind)
        + "\n\nPort the change, or say in the commit message why the twin is unaffected. "
        "The differential arm will NOT catch this on a corpus that misses the branch."
    )
