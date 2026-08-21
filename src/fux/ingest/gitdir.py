"""Git-dir source adapter — the committed directory list, and a sorted walk of it.

The list is `.fux/sources/dirs` (ADR-DIR-LIST), read through the one shared
grammar in `sourcelist.py`: one entry per line, `#` comments, the loader
dedupes and sorts, and a line may declare `archived=true`.

Each entry is a directory (walked recursively) or a single file, relative to
the repo root. Reads raw bytes directly off the filesystem (no git plumbing —
"git-dir" names the fact that these are files living in a git checkout, not a
dependency on git object hashes). Binary, non-UTF8, and empty files are
skipped with a reason, never a crash; a configured source that doesn't exist
on disk is a misconfiguration and fails loudly instead.

**`archived` is parsed and not yet read.** The declaration is the half this
change owns; turning it into a record property and a marker in every verb is
gated on W-44's instrument (ADR-DIR-LIST decision 10). Nothing below branches
on it, and the ranking is byte-identical either way — which is decision 6.

## Three conditions, and none of them overrides another

A file is indexed **iff** all three hold:

1. it lives under an **included** `dirs` entry;
2. no `!` **exclusion** entry matches it or any of its ancestors
   (ADR-DIR-LIST, W-45's verdict E);
3. its name matches the **type allowlist** — `.fux/sources/types` if that file
   exists, otherwise the built-in `DEFAULT_TYPES` (ADR-TYPES, W-55's verdict G).

**This is a conjunction, deliberately, not a priority order.** No rule beats
another, so there is nothing to remember about precedence and nothing to get
wrong. Every file that fails one of the three is reported as *skipped with a
reason* rather than silently dropped — an invisible filter is the failure mode
both of those items were opened about.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from ..config import DEFAULT_TYPES_FILE as TYPES_FILE
from ..errors import FuxError
from . import sourcelist


@dataclass(frozen=True)
class WalkedFile:
    rel_path: str  # posix, relative to root
    content: bytes


@dataclass(frozen=True)
class Skipped:
    rel_path: str
    reason: str


def read_dirs(root: Path, rel_path: str) -> list[sourcelist.Entry]:
    """Parse the committed directory list through the one shared grammar.

    Deduped and sorted by entry, so file order is presentation only — a human
    may group by team or by system and it cannot change a committed byte.
    """
    return sourcelist.read(
        root,
        rel_path,
        sourcelist.DIRS,
        missing_hint=(
            "create it with one directory or file per line (a line may carry "
            "`archived=true`), or run `fux setup` to write a starter"
        ),
    )


def source_dirs(root: Path, rel_path: str) -> list[str]:
    """Just the **included** entry values. Exclusions are `source_excludes`."""
    return [entry.value for entry in read_dirs(root, rel_path) if not entry.exclude]


def source_excludes(root: Path, rel_path: str) -> list[str]:
    """The `!` patterns — repo-relative globs, applied to the whole walk."""
    return [entry.value for entry in read_dirs(root, rel_path) if entry.exclude]


#: What counts as a document when the consumer has not said otherwise.
#: **Prose formats only.** No `.json`, `.svg`, `.sh`, `.py` or `.mermaid`: they
#: are machine data or diagram source, and indexing them was the W-55 defect.
#: No extensionless files either — those are `LICENSE`, `Makefile` and
#: `Dockerfile` far more often than they are documents.
DEFAULT_TYPES: tuple[str, ...] = ("*.md", "*.markdown", "*.txt", "*.rst", "*.adoc", "*.org")


@dataclass(frozen=True)
class TypeFilter:
    """Which filenames are documents. `allow` is never empty by construction."""

    allow: tuple[str, ...]
    deny: tuple[str, ...] = ()
    #: True when the built-in default is in force — i.e. no types file exists.
    default: bool = True

    def accepts(self, rel_path: str) -> bool:
        if any(sourcelist.glob_match(p, rel_path) for p in self.deny):
            return False
        return any(sourcelist.glob_match(p, rel_path) for p in self.allow)


def read_types(root: Path, rel_path: str = TYPES_FILE) -> TypeFilter:
    """The type allowlist: the committed file if present, else the built-in.

    **Absent means the default applies, never "index everything".** Indexing
    everything is the behaviour W-55 was filed about; and it does not mean
    "index nothing" either, because a missing config that empties the index
    looks like a broken engine rather than a missing file.
    """
    path = root / rel_path
    if not path.is_file():
        return TypeFilter(allow=DEFAULT_TYPES)

    entries = sourcelist.parse(path.read_text(encoding="utf-8"), sourcelist.TYPES, origin=str(path))
    allow = tuple(e.value for e in entries if not e.exclude)
    deny = tuple(e.value for e in entries if e.exclude)
    if not allow:
        raise FuxError(
            f"{path}: lists no file types, so nothing would be indexed. Delete the file to take "
            f"the built-in default ({', '.join(DEFAULT_TYPES)}), or add at least one pattern"
        )
    return TypeFilter(allow=allow, deny=deny, default=False)


def walk_sources(
    root: Path,
    dirs: list[str],
    *,
    excludes: list[str] | None = None,
    types: TypeFilter | None = None,
) -> tuple[list[WalkedFile], list[Skipped]]:
    """Walk the included roots, subtract the exclusions, keep only document types.

    `excludes` and `types` default to "nothing excluded, everything allowed" so
    a caller that has not been updated keeps its old behaviour — but **no such
    caller ships**: `ingest` passes both, and the defaults exist for tests that
    are exercising one condition at a time.
    """
    excludes = excludes or []
    files: dict[str, bytes] = {}
    skipped: dict[str, str] = {}
    for entry in dirs:
        base = root / entry
        if not base.exists():
            raise FuxError(f"configured source not found: {entry!r} (looked in {base})")
        for path in _candidate_paths(base):
            # NFC, the same normalization `parse.py` applies to file content
            # (the R1/macOS-checkout hazard): a filesystem may return a path
            # in NFD even when the file was created and committed as NFC, so
            # the same document's `rel_path`/`loc` would differ by checkout
            # machine without this — a byte-identical-index guarantee (L3)
            # that a path string, not just content, has to hold too.
            rel = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
            if rel in files or rel in skipped:
                continue  # already covered by an earlier, overlapping entry

            pattern = _excluded_by(rel, excludes)
            if pattern is not None:
                skipped[rel] = f"excluded by !{pattern}"
                continue
            if types is not None and not types.accepts(rel):
                skipped[rel] = "not an indexed file type"
                continue

            content = path.read_bytes()
            reason = _skip_reason(content)
            if reason:
                skipped[rel] = reason
            else:
                files[rel] = content

    walked = sorted((WalkedFile(rel, content) for rel, content in files.items()), key=lambda f: f.rel_path)
    skips = sorted((Skipped(rel, reason) for rel, reason in skipped.items()), key=lambda s: s.rel_path)
    return walked, skips


def _excluded_by(rel: str, excludes: list[str]) -> str | None:
    """The first pattern that removes this path, or `None`.

    A pattern matches the file **or any ancestor directory**, so
    `!work/regression/*/evidence` removes the directory and everything under
    it — which is what a reader of that line expects, and the only reading
    under which excluding a tree is one line rather than one line per file.
    """
    parts = rel.split("/")
    ancestors = ["/".join(parts[: i + 1]) for i in range(len(parts))]
    for pattern in excludes:
        if any(sourcelist.glob_match(pattern, candidate) for candidate in ancestors):
            return pattern
    return None


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
