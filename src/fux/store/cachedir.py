"""`CACHEDIR.TAG` — a derived `.fux/` directory marked disposable.

**Owned by [SR-CACHEDIR-TAG](../../../records/0121_cachedir-tag.md)** since
2026-10-05 (W-261, Arpit's ruling that every `kind: component` record owns a
file). A pure move out of `store/fuxdir.py`, which keeps the `.fux/` layout
(SR-DOTFUX's) and imports `derived_dir` from here, so every caller of
`fuxdir.derived_dir` is unchanged.

**Byte-exact per [the spec](https://bford.info/cachedir/)**: the first line is a
fixed signature, the body is `templates/cachedir-tag.txt`, and the tag is written
once and never overwritten. Its Node twin is `node/src/store/cachedir.mjs`.

⚠ **Self-contained on purpose.** It reads the `.fux/` name and the template
itself rather than importing `fuxdir`, because `fuxdir` imports it.
"""

from __future__ import annotations

from pathlib import Path

from ..constants import fixed

__all__ = ["CACHEDIR_SIGNATURE", "CACHEDIR_TAG", "derived_dir"]

_FUX_DIR = fixed("fuxdir", "dir")

# CACHEDIR.TAG's first line is a fixed signature — byte-exact, per the spec.
CACHEDIR_SIGNATURE = fixed("fuxdir", "cachedir_signature")


def _cachedir_tag() -> str:
    """The template with the spec'd signature in place — `src/fux/templates/`,
    the home of bytes fux writes (SR-LAW-12 decision 6b, R13)."""
    template = Path(__file__).parent.parent / "templates" / fixed("templates", "cachedir_tag")
    return template.read_text(encoding="utf-8").replace("{signature}", CACHEDIR_SIGNATURE)


CACHEDIR_TAG = _cachedir_tag()


def derived_dir(root: Path, name: str) -> Path:
    """Return `.fux/<name>/`, created and tagged as a cache directory.

    For M2 to call when it materializes `runtime/` (M4's fetch cache nests
    inside it, at `runtime/fetch-cache/`, and does not call this directly).
    The tag is written once and never overwritten.
    """
    path = root / _FUX_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    tag = path / "CACHEDIR.TAG"
    if not tag.exists():
        tag.write_bytes(CACHEDIR_TAG.encode("ascii"))
    return path
