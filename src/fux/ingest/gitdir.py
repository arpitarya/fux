"""Git-dir source adapter — a sorted walk of the configured `[sources] dirs`.

Each entry is a directory (walked recursively) or a single file, relative to
the repo root. Reads raw bytes directly off the filesystem (no git plumbing —
"git-dir" names the fact that these are files living in a git checkout, not a
dependency on git object hashes). Binary, non-UTF8, and empty files are
skipped with a reason, never a crash (handoff §8); a configured source that
doesn't exist on disk is a misconfiguration and fails loudly instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..errors import FuxError


@dataclass(frozen=True)
class WalkedFile:
    rel_path: str  # posix, relative to root
    content: bytes


@dataclass(frozen=True)
class Skipped:
    rel_path: str
    reason: str


def walk_sources(root: Path, dirs: list[str]) -> tuple[list[WalkedFile], list[Skipped]]:
    files: dict[str, bytes] = {}
    skipped: dict[str, str] = {}
    for entry in dirs:
        base = root / entry
        if not base.exists():
            raise FuxError(f"configured source not found: {entry!r} (looked in {base})")
        for path in _candidate_paths(base):
            rel = path.relative_to(root).as_posix()
            if rel in files or rel in skipped:
                continue  # already covered by an earlier, overlapping entry
            content = path.read_bytes()
            reason = _skip_reason(content)
            if reason:
                skipped[rel] = reason
            else:
                files[rel] = content

    walked = sorted((WalkedFile(rel, content) for rel, content in files.items()), key=lambda f: f.rel_path)
    skips = sorted((Skipped(rel, reason) for rel, reason in skipped.items()), key=lambda s: s.rel_path)
    return walked, skips


def _candidate_paths(base: Path):
    if base.is_file():
        yield base
        return
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(base).parts):
            continue  # dotfiles/dotdirs (.git, .DS_Store, …) are never doc content
        yield path


def _skip_reason(content: bytes) -> str | None:
    if not content:
        return "empty"
    if b"\x00" in content:
        return "binary"
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return "non-utf8"
    return None
