"""Build the Node read plane's bundle into the wheel — L10, at publish time.

**Why a build hook rather than a static `force-include`.** The wheel carries
the Node reader at `fux/templates/node/` so `fux setup` can vendor it
(ADR-NODE-SEARCH decision 13). Since 2026-09-12 what it carries is **one
generated file plus its sidecars**, never `node/src/**`
([L10](docs/adr/0012_LAW-10-bundled-output.md)) — and a generated file cannot be
named in a static include list without someone having remembered to generate it
first. The hook removes the ordering question: **every wheel built from this
tree carries a bundle built from this tree.**

**Determinism is what makes this safe.** `fux.store.nodebundle` emits the same
bytes for the same sources, so the bundle the release workflow builds for npm
and the bundle this hook builds for the wheel are byte-identical — one artefact
in two registries, which is the whole of decision 14.

⚠ **`python -m build` isolates the build**, so this file may import nothing but
the standard library and hatchling. It reaches `fux.store.nodebundle` by path,
never by installing fux.

Reference: hatchling build hooks
<https://hatch.pypa.io/latest/plugins/build-hook/custom/>
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

#: Where the wheel keeps the payload. `fux setup` reads it as package data —
#: bytes, never an import — exactly as it reads `templates/*.py.txt`.
WHEEL_TARGET = "fux/templates/node"


def _load_bundler(root: Path):
    """Import `src/fux/store/nodebundle.py` without importing `fux`.

    The module is deliberately import-light (stdlib + `..errors`) so that this
    is possible: a build hook that had to install the package it is building
    would be a circular dependency wearing a helpful face.
    """
    package_root = root / "src"
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    spec = importlib.util.find_spec("fux.store.nodebundle")
    if spec is None:  # pragma: no cover - a tree without the module cannot build
        raise RuntimeError("src/fux/store/nodebundle.py is missing; cannot bundle the Node reader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NodeBundleHook(BuildHookInterface):
    PLUGIN_NAME = "node-bundle"

    def initialize(self, version: str, build_data: dict) -> None:
        root = Path(self.root)
        node_dir = root / "node"
        if not node_dir.is_dir():  # pragma: no cover - sdists carry it
            raise RuntimeError("node/ is missing; the wheel cannot carry the Node read plane")
        bundler = _load_bundler(root)
        # A temporary directory, not `node/dist/`: a build must never leave
        # artefacts in the source tree, and the release workflow's own bundle
        # step writes `node/dist/` for npm deliberately.
        out = Path(tempfile.mkdtemp(prefix="fux-node-bundle-"))
        for path in bundler.write(node_dir, out):
            build_data["force_include"][str(path)] = f"{WHEEL_TARGET}/{path.name}"
