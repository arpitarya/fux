"""The consumer's policy files live in `.fux/config/` (W-295, SR-DOTFUX).

Eight files -- `formats identifiers inspect output pii plugins refusals tune`,
each `<name>.toml` -- moved from `.fux/<name>.toml` to `.fux/config/<name>.toml`.
Every address is a `constants.toml [files]` key (L12); this module is the one
place that knows the *old* address and what to do about a file still there.

**Breaking, with no fallback reader** (the W-177 / W-199 / W-294 stance). Two
things only: `fux setup` MOVES the files (`migrate`), and every other verb that
finds one at the old address stops with `moved_error` -- a repository half-way
through the move must never read as a repository with no policy.

Imports only `constants` and `errors`: the CLI gate that calls it runs before
every verb and must cost a few stat calls, not an import of `fux.ingest`.
"""

from __future__ import annotations

import os
from pathlib import Path

from .constants import fixed
from .errors import FuxError

__all__ = ["names", "path", "old_path", "at_old_address", "moved_error", "require_moved", "migrate"]


def names() -> tuple[str, ...]:
    """The eight policy files, by stem, sorted -- `constants.toml [files] config_names`."""
    return tuple(sorted(fixed("files", "config_names")))


def path(root: Path, name: str) -> Path:
    """`.fux/config/<name>.toml` under `root`."""
    return root / fixed("files", name)


def old_path(root: Path, name: str) -> Path:
    """The pre-W-295 address, `.fux/<name>.toml` -- named only to detect and move it."""
    return root / fixed("fuxdir", "dir") / Path(fixed("files", name)).name


def at_old_address(root: Path) -> list[str]:
    """Stems of the files still at the pre-W-295 address, sorted."""
    return [n for n in names() if old_path(root, n).is_file()]


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def moved_error(root: Path, stems: "list[str] | None" = None) -> "FuxError | None":
    """The loud refusal for files at the old address, or `None` when there are none."""
    stems = at_old_address(root) if stems is None else stems
    if not stems:
        return None
    parts = ", ".join(
        f"`{_rel(root, old_path(root, n))}` moved to `{_rel(root, path(root, n))}`" for n in stems
    )
    return FuxError(f"{parts} — run `fux setup`")


def require_moved(root: Path) -> None:
    """Raise `moved_error` when any policy file is still at the old address."""
    exc = moved_error(root)
    if exc is not None:
        raise exc


def migrate(root: Path) -> list[str]:
    """Move every file at the old address to the new one; return the new repo-relative paths.

    **Byte-for-byte**: a rename on one filesystem keeps content, comments and
    mode, and nothing is read or rewritten. **All-or-nothing on the refusal**:
    a stem present at BOTH addresses is a decision only a person can make, so
    the call names both and touches neither -- and it checks every stem before
    it moves any, so a refusal never leaves a half-moved directory.
    """
    stems = at_old_address(root)
    clashes = [n for n in stems if path(root, n).exists()]
    if clashes:
        both = "; ".join(
            f"`{_rel(root, old_path(root, n))}` and `{_rel(root, path(root, n))}`" for n in clashes
        )
        raise FuxError(
            f"{both} both exist -- `fux setup` will not choose between them (W-295). "
            "Keep the one you want at the new address, delete the other, and run `fux setup` again."
        )
    moved: list[str] = []
    for n in stems:
        target = path(root, n)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(old_path(root, n), target)
        moved.append(_rel(root, target))
    return moved
