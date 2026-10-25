"""A pinned index package's runtime: `.fux/runtime/pkg/<name>@<version>/` (W-299).

[SR-PKG-INDEX](../../../records/0166_pkg-index.md) decision 8. A segment a
consumer pinned with a `kind = "index"` row is **verified first** —
`plugins.locate_index` refuses a missing, other or drifted one before a byte of
it is read — and then inflated into a directory laid out as a repository:

    .fux/runtime/pkg/<name>@<version>/
        .fux/index/*.jsonl              the verified shards, copied
        .fux/config/identifiers.toml    the rules they were built under
        .fux/runtime/                   built by `derive.build`, the repo's own builder
        pin                             the pin digest it was built from, written last

So every root-keyed reader opens a pinned package exactly as it opens a
repository, and the Node twin (`node/src/derive/segments.mjs`) writes the same
bytes from the same pin. **Rebuilt when the pin digest changes, untouched when
it does not**; a directory no pin names is removed. Everything here is derived
and gitignored: deleting it costs a rebuild and nothing else.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .. import plugins
from ..constants import fixed
from ..store.cachedir import runtime_dir

__all__ = ["inflate", "inflate_all", "is_current", "packages_dir", "root_for", "segment_dir"]


def packages_dir(root: Path) -> Path:
    """`.fux/runtime/pkg/` — every pinned segment's runtime, one child each."""
    return runtime_dir(root) / fixed("plugins.index", "runtime_child")


def segment_dir(root: Path, pin: plugins.IndexPin) -> Path:
    """`.fux/runtime/pkg/<name>@<version>/` for one pin."""
    return packages_dir(root) / f"{pin.name}@{pin.version}"


def root_for(root: Path, package: str | None) -> Path:
    """The root a hit's own record lives under (W-300): the repository for
    `None`, the pin's runtime for a package hit. Display reads only — the
    title, the headings, the `sha` — so they come from the record that was
    ranked rather than from a repository document that shares its id."""
    if package is None:
        return root
    return segment_dir(root, plugins.indexes(root)[package])


def is_current(root: Path, pin: plugins.IndexPin) -> bool:
    """Was this pin's runtime built from exactly this pin digest?"""
    stamp = segment_dir(root, pin) / fixed("plugins.index", "pin_stamp")
    try:
        return bool(pin.digest) and stamp.read_text(encoding="utf-8").strip() == pin.digest
    except OSError:
        return False


def _copy_segment(source: Path, target: Path) -> None:
    """The digest-covered files only, into the repository layout (d8)."""
    shard_suffix = fixed("index", "shard_suffix")
    index_dir = target / fixed("index", "dir")
    config_dir = target / Path(fixed("files", "identifiers")).parent
    for pattern in fixed("plugins.index", "segment"):
        destination = index_dir if pattern.endswith(shard_suffix) else config_dir
        for item in sorted(source.glob(pattern)):
            if item.is_file():
                destination.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item, destination / item.name)


def inflate(root: Path, pin: plugins.IndexPin) -> bool:
    """Verify `pin`, then build its runtime unless it is current. True if built."""
    from ._build import build_own

    source = plugins.locate_index(pin)  # refuses before anything is read
    if is_current(root, pin):
        return False
    target = segment_dir(root, pin)
    if target.exists():
        shutil.rmtree(target)
    _copy_segment(source, target)
    build_own(target)
    # bytes, so Windows writes the LF Node writes (the runtimes are byte-identical)
    (target / fixed("plugins.index", "pin_stamp")).write_bytes((pin.digest + "\n").encode("utf-8"))
    return True


def inflate_all(root: Path) -> list[str]:
    """Every pinned segment, verified and current; stale children removed.

    Returns the `<name>@<version>` directories that were (re)built, sorted.
    """
    pins = plugins.indexes(root)
    built = [segment_dir(root, pin).name for pin in pins.values() if inflate(root, pin)]
    wanted = {segment_dir(root, pin).name for pin in pins.values()}
    directory = packages_dir(root)
    if directory.is_dir():
        for child in sorted(directory.iterdir()):
            if child.is_dir() and child.name not in wanted:
                shutil.rmtree(child)
    return sorted(built)
