"""Ingest, inferred tier: configured sources → OKF cache + manifest + index.

Library-first (the CLI wraps this): :func:`ingest_paths` is the public API, with
:func:`check_drift` and :func:`list_inferred` beside it. Determinism is a hard
requirement — sorted walks, stable serialization, POSIX relative paths, and
`converted_at` derived from ``SOURCE_DATE_EPOCH``/source mtime (never wall
clock), so two runs over the same sources are byte-identical.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__
from ..config import Config, find_root, load
from ..frontmatter import dumps as fm_dumps
from .convert import ConvertResult, convert
from .manifest import Drift, check_drift, quick_drift, read as manifest_read, sha256_bytes
from .manifest import write as manifest_write
from .walk import SourceFile, WalkResult, walk

__all__ = ["ingest_paths", "check_drift", "quick_drift", "list_inferred", "cmd_ingest"]

CACHE_REL = ".fux/cache"

# Frontmatter keys the engine owns; a source doc's other keys are preserved.
_RESERVED = {
    "type", "title", "description", "timestamp", "source", "source_sha256",
    "origin", "fidelity", "converter", "converted_at", "fux_version", "truncated",
}


@dataclass
class IngestReport:
    entries: list[dict] = field(default_factory=list)
    new: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: list[tuple[str, str]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chunk_count: int = 0

    @property
    def total(self) -> int:
        return self.new + self.updated + self.unchanged


def ingest_paths(config: Config, *, build_index: bool = True) -> IngestReport:
    root = config.root
    cache_root = root / CACHE_REL
    report = IngestReport()
    result = walk(config)
    report.warnings.extend(f"source folder not found: {d}" for d in result.missing_dirs)
    prev = manifest_read(root)

    walked_rels = set()
    for sf in result.files:
        walked_rels.add(sf.rel)
        data = sf.abspath.read_bytes()
        sha = sha256_bytes(data)
        entry = prev.get(sf.rel)
        cache_rel = _cache_rel(sf.rel)
        cache_path = root / cache_rel
        if entry and entry.get("sha256") == sha and cache_path.is_file():
            report.entries.append(entry)
            report.unchanged += 1
            continue
        conv = convert(sf, data, config.ingest.max_kb)
        report.warnings.extend(conv.warnings)
        if conv.skipped:
            report.skipped.append((sf.rel, conv.skipped))
            if entry:  # was ingested before, no longer can be
                cache_path.unlink(missing_ok=True)
                report.removed.append(sf.rel)
            continue
        meta, title = _build_meta(sf, conv, sha)
        text = fm_dumps(meta, conv.body)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if not cache_path.is_file() or cache_path.read_text(encoding="utf-8") != text:
            cache_path.write_text(text, encoding="utf-8")
        report.entries.append(_manifest_entry(sf, conv, sha, len(data), cache_rel, title))
        report.updated += 1 if entry else 0
        report.new += 0 if entry else 1

    for rel in sorted(set(prev) - walked_rels):
        (root / _cache_rel(rel)).unlink(missing_ok=True)
        report.removed.append(rel)

    if cache_root.is_dir() or report.entries:
        _write_dir_indexes(cache_root, report.entries)
    manifest_write(root, report.entries)

    if build_index and report.entries:
        from ..index import build_index as _build

        report.chunk_count = _build(config, report.entries)
    return report


def list_inferred(config: Config) -> list[dict]:
    return [
        e for e in manifest_read(config.root).values() if e.get("fidelity") == "inferred"
    ]


def _cache_rel(source_rel: str) -> str:
    suffix = "" if source_rel.lower().endswith(".md") else ".md"
    return f"{CACHE_REL}/{source_rel}{suffix}"


def _converted_at(sf: SourceFile) -> str:
    # Deterministic by design: SOURCE_DATE_EPOCH (reproducible-builds convention)
    # or the source's mtime — never "now", or byte-identical re-ingest is impossible.
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "")
    ts = int(epoch) if epoch.isdigit() else int(sf.abspath.stat().st_mtime)
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_meta(sf: SourceFile, conv: ConvertResult, sha: str) -> tuple[dict, str]:
    title = conv.source_meta.get("title")
    if not isinstance(title, str) or not title:
        title = _first_heading(conv.body) or Path(sf.rel).stem
    description = conv.source_meta.get("description")
    if not isinstance(description, str) or not description:
        description = f"Ingested from {sf.rel} ({sf.kind})"
    converted_at = _converted_at(sf)
    meta = {
        "type": "Ingested Document",
        "title": title,
        "description": description,
        "timestamp": converted_at,
        "source": sf.rel,
        "source_sha256": sha,
        "origin": "local",
        "fidelity": "inferred",
        "converter": conv.converter,
        "converted_at": converted_at,
        "fux_version": __version__,
    }
    if conv.truncated:
        meta["truncated"] = True
    for key, value in conv.source_meta.items():
        if key not in _RESERVED:
            meta[key] = value
    return meta, title


def _first_heading(body: str) -> str | None:
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


def _manifest_entry(
    sf: SourceFile, conv: ConvertResult, sha: str, size: int, cache_rel: str, title: str
) -> dict:
    entry = {
        "source": sf.rel,
        "cache": cache_rel,
        "type": sf.stype,
        "kind": sf.kind,
        "sha256": sha,
        "size": size,
        "fidelity": "inferred",
        "converter": conv.converter,
        "converted_at": _converted_at(sf),
        "line_offset": conv.line_offset,
        "fux_version": __version__,
        "title": title,
    }
    if sf.lang:
        entry["lang"] = sf.lang
    if sf.rel.startswith("_external/"):
        entry["abs"] = str(sf.abspath)
    return entry


def _write_dir_indexes(cache_root: Path, entries: list[dict]) -> None:
    """Per-directory OKF `index.md` (progressive disclosure) + prune empty dirs."""
    dirs: dict[str, dict] = {"": {"files": [], "subdirs": set()}}
    for entry in entries:
        rel = Path(entry["cache"]).relative_to(CACHE_REL).as_posix()
        parent = str(Path(rel).parent).replace("\\", "/")
        parent = "" if parent == "." else parent
        cur = parent
        while True:
            dirs.setdefault(cur, {"files": [], "subdirs": set()})
            if cur == "":
                break
            up = str(Path(cur).parent).replace("\\", "/")
            up = "" if up == "." else up
            dirs.setdefault(up, {"files": [], "subdirs": set()})
            dirs[up]["subdirs"].add(Path(cur).name)
            cur = up
        dirs[parent]["files"].append((Path(rel).name, entry.get("title", "")))

    # Drop index.md files + empty dirs that no longer correspond to entries.
    if cache_root.is_dir():
        for dirpath, dirnames, filenames in os.walk(cache_root, topdown=False):
            rel = Path(dirpath).relative_to(cache_root).as_posix()
            rel = "" if rel == "." else rel
            if rel not in dirs:
                idx = Path(dirpath) / "index.md"
                idx.unlink(missing_ok=True)
                try:
                    Path(dirpath).rmdir()
                except OSError:
                    pass

    for rel, info in dirs.items():
        label = f"{CACHE_REL}/{rel}" if rel else CACHE_REL
        lines = ["---", "type: Index", f"title: {label}", "---", "", f"# `{label}`", ""]
        for sub in sorted(info["subdirs"]):
            lines.append(f"- [{sub}/]({sub}/index.md)")
        for name, title in sorted(info["files"]):
            lines.append(f"- [{name}]({name}) — {title}" if title else f"- [{name}]({name})")
        text = "\n".join(lines) + "\n"
        path = cache_root / rel / "index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")


# -- CLI handler -----------------------------------------------------------


def cmd_ingest(args) -> int:
    root = find_root()
    config = load(root)

    if args.check:
        drift = check_drift(config)
        if drift.clean:
            print(f"cache is fresh ({len(manifest_read(root))} files tracked)")
            return 0
        for rel in drift.changed:
            print(f"changed  {rel}")
        for rel in drift.new:
            print(f"new      {rel}")
        for rel in drift.missing:
            print(f"missing  {rel}  (source deleted; cache entry is an orphan)")
        print("run `fux ingest` to refresh")
        return 1

    if args.list_inferred:
        for entry in sorted(list_inferred(config), key=lambda e: e["source"]):
            print(f"{entry['source']}  ({entry['converter']})")
        return 0

    if args.list_skipped:
        for rel, reason in _detect_skips(config):
            print(f"{rel}  — {reason}")
        return 0

    report = ingest_paths(config)
    if report.total == 0 and not report.skipped:
        print("no source files found in the configured folders — check [sources] in fux.toml")
        for warning in report.warnings:
            print(f"warning: {warning}")
        return 0
    print(
        f"ingested {report.total} files ({report.new} new, {report.updated} updated, "
        f"{report.unchanged} unchanged) → {CACHE_REL} ({report.chunk_count} chunks indexed)"
    )
    if report.skipped:
        print(f"skipped {len(report.skipped)} (see `fux ingest --list-skipped`)")
    if report.removed:
        print(f"removed {len(report.removed)} stale cache entries")
    for warning in report.warnings:
        print(f"warning: {warning}")
    return 0


def _detect_skips(config: Config) -> list[tuple[str, str]]:
    """Recompute skip reasons without writing (extension, extras, binary sniff)."""
    result = walk(config)
    out = [(rel, "unrecognized extension") for rel in result.unknown]
    for sf in result.files:
        conv = convert(sf, sf.abspath.read_bytes(), config.ingest.max_kb)
        if conv.skipped:
            out.append((sf.rel, conv.skipped))
    return sorted(out)
