"""Build one distribution's wheel from its layer of the shared tree (W-282).

Fux is one source tree, `src/fux/`, and four distributions: `fux-core`,
`fux-reader`, `fux-writer` and `fux-engine`. **Which file ships in which is
not decided here** — it is read from `records/README.md` §The layer map, the
same table `tests/test_package_layers.py` holds the imports to, so the wheels
and the layering cannot disagree while both look right (SR-LAW-0 decision 5).

Each distribution's `pyproject.toml` names this hook and its layer::

    [tool.hatch.build.targets.wheel.hooks.custom]
    path = "../layer_hook.py"      # "packages/layer_hook.py" from the root
    layer = "reader"

and the hook force-includes every file of that layer at `fux/<path>`. The
writer's wheel also carries the Node reader's bundle at `fux/templates/node/`,
because `fux setup` — the writer's verb — vendors it (SR-NODE-SEARCH decision
13; L10: the bundle, never the module tree).

**An editable install selects nothing**: `dev-mode-dirs` puts the whole
`src/` on the path, which is what a developer working on every layer wants.

⚠ **`python -m build` isolates the build**, so this file imports nothing but
the standard library and hatchling, and reaches the bundler by path.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

LAYERS = ("core", "reader", "writer", "engine")
_ROW = re.compile(r"^\| `(src/fux/[^`]*)` \| (core|reader|writer|engine) \|")
_SKIP = {"__pycache__", ".DS_Store"}


def repo_root(start: Path) -> Path:
    """The checkout this project sits in: the nearest parent with `src/fux/`."""
    for candidate in (start, *start.parents):
        if (candidate / "src" / "fux").is_dir() and (candidate / "records" / "README.md").is_file():
            return candidate
    raise RuntimeError(f"no fux checkout above {start}: a role wheel is built from the repository")


def layer_map(root: Path) -> dict[str, str]:
    text = (root / "records" / "README.md").read_text(encoding="utf-8")
    block = text[text.index("<!-- LAYER-MAP-START -->"): text.index("<!-- LAYER-MAP-END -->")]
    return {m.group(1): m.group(2) for m in map(_ROW.match, block.splitlines()) if m}


def layer_of(rel: str, rows: dict[str, str]) -> str | None:
    best = None
    for path, layer in rows.items():
        if rel == path or (path.endswith("/") and rel.startswith(path)):
            if best is None or len(path) > len(best[0]):
                best = (path, layer)
    return best[1] if best else None


def layer_files(root: Path, layer: str) -> list[Path]:
    """Every file under `src/fux/` the layer map places in `layer`, sorted."""
    rows = layer_map(root)
    out = []
    for path in sorted((root / "src" / "fux").rglob("*")):
        if not path.is_file() or _SKIP & set(path.parts) or path.suffix == ".pyc":
            continue
        rel = path.relative_to(root).as_posix()
        found = layer_of(rel, rows)
        if found is None:
            raise RuntimeError(f"{rel} is in no row of records/README.md §The layer map")
        if found == layer:
            out.append(path)
    return out


def _node_bundle(root: Path) -> list[Path]:
    """Build the Node reader's bundle into a temporary directory (L10)."""
    if str(root / "src") not in sys.path:
        sys.path.insert(0, str(root / "src"))
    spec = importlib.util.find_spec("fux.store.nodebundle")
    if spec is None:  # pragma: no cover - a tree without the module cannot build
        raise RuntimeError("src/fux/store/nodebundle.py is missing; cannot bundle the Node reader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out = Path(tempfile.mkdtemp(prefix="fux-node-bundle-"))
    return list(module.write(root / "node", out))


class LayerHook(BuildHookInterface):
    PLUGIN_NAME = "fux-layer"

    def initialize(self, version: str, build_data: dict) -> None:
        if version == "editable":
            return
        layer = self.config.get("layer")
        if layer not in LAYERS:
            raise RuntimeError(f"[tool.hatch.build.targets.wheel.hooks.custom] layer must be one of {LAYERS}")
        root = repo_root(Path(self.root))
        for path in layer_files(root, layer):
            build_data["force_include"][str(path)] = path.relative_to(root / "src").as_posix()
        if layer == "writer":
            for path in _node_bundle(root):
                build_data["force_include"][str(path)] = f"fux/templates/node/{path.name}"
