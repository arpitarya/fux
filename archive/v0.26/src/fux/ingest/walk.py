"""Source discovery: deterministic, sorted walks of the configured folders."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from .. import debug
from ..config import SOURCE_TYPES, Config

# Extension → conversion kind, per source type. A dir configured under a type is
# scanned only for that type's extensions (the config maps file types → dirs).
EXTENSIONS: dict[str, dict[str, str]] = {
    "docs": {
        ".md": "md",
        ".markdown": "md",
        ".txt": "txt",
        ".docx": "office",
        ".pptx": "office",
        ".xlsx": "office",
        ".pdf": "office",
    },
    "code": {},  # filled from CODE_LANGS below
    "data": {".json": "json", ".yaml": "yaml", ".yml": "yaml"},
    "images": {".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image"},
}

CODE_LANGS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".sh": "bash",
    ".sql": "sql",
    ".swift": "swift",
    ".kt": "kotlin",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
}
EXTENSIONS["code"] = {ext: "code" for ext in CODE_LANGS}


@dataclass(frozen=True)
class SourceFile:
    rel: str  # POSIX path relative to the project root (or _external/…)
    abspath: Path
    stype: str  # docs | code | data | images
    kind: str  # md | txt | code | json | yaml | image | office
    lang: str = ""  # code only


@dataclass
class WalkResult:
    files: list[SourceFile]
    unknown: list[str]  # recognized dirs, unrecognized extensions
    missing_dirs: list[str]  # configured dirs that don't exist


def walk(config: Config) -> WalkResult:
    root = config.root.resolve()
    exclude = set(config.ingest.exclude)
    seen: dict[str, SourceFile] = {}
    unknown: list[str] = []
    missing: list[str] = []

    with debug.timer("walk", "walk sources"):
        for stype in SOURCE_TYPES:
            ext_map = EXTENSIONS[stype]
            for src_dir in config.sources.get(stype, ()):
                base = (root / src_dir).resolve() if not os.path.isabs(src_dir) else Path(src_dir)
                if not base.is_dir():
                    missing.append(src_dir)
                    debug.dbg("walk", "debug", "source dir missing", type=stype, dir=src_dir)
                    continue
                before = len(seen)
                for dirpath, dirnames, filenames in os.walk(base):
                    dirnames[:] = sorted(
                        d for d in dirnames if d not in exclude and not d.startswith(".")
                    )
                    for name in sorted(filenames):
                        if name.startswith("."):
                            continue
                        path = Path(dirpath) / name
                        rel = _rel_to_root(path, base, root)
                        ext = path.suffix.lower()
                        kind = ext_map.get(ext)
                        if kind is None:
                            if not any(ext in EXTENSIONS[t] for t in SOURCE_TYPES):
                                unknown.append(rel)
                            continue
                        if rel not in seen:
                            seen[rel] = SourceFile(
                                rel=rel,
                                abspath=path,
                                stype=stype,
                                kind=kind,
                                lang=CODE_LANGS.get(ext, "") if kind == "code" else "",
                            )
                matched = len(seen) - before
                debug.dbg(
                    "walk", "debug", "source dir scanned",
                    type=stype, dir=src_dir, matched=matched,
                )
                if matched == 0:
                    # The #1 silent misconfig (handoff §C) — a glob/dir that
                    # resolves to zero files never surfaces otherwise.
                    debug.dbg(
                        "walk", "info", "source dir matched zero files",
                        type=stype, dir=src_dir,
                    )

    files = [seen[r] for r in sorted(seen)]
    result = WalkResult(files=files, unknown=sorted(set(unknown)), missing_dirs=missing)
    debug.dbg(
        "walk", "info", "walk complete",
        files=len(result.files), unknown=len(result.unknown), missing=len(result.missing_dirs),
    )
    return result


def _rel_to_root(path: Path, base: Path, root: Path) -> str:
    """POSIX path relative to root; sources outside root land under _external/."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        tag = hashlib.sha256(str(base).encode("utf-8")).hexdigest()[:8]
        return f"_external/{tag}/{path.relative_to(base).as_posix()}"
