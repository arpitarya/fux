"""Ingest, inferred tier: configured sources → OKF cache + manifest + index.

Library-first (the CLI wraps this): :func:`ingest_paths` is the public API, with
:func:`check_drift` and :func:`list_inferred` beside it. Determinism is a hard
requirement — sorted walks, stable serialization, POSIX relative paths, and
`converted_at` derived from ``SOURCE_DATE_EPOCH``/source mtime (never wall
clock), so two runs over the same sources are byte-identical.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__
from ..config import Config, find_root, load
from ..errors import FuxError
from ..frontmatter import dumps as fm_dumps
from .convert import ConvertResult, convert
from .lock import LOCK_NAME, Status, check
from .lock import records_from_entries, write as lock_write
from .manifest import Drift, quick_drift, read as manifest_read
from .manifest import sha256_bytes, write as manifest_write
from .walk import SourceFile, WalkResult, walk

__all__ = ["ingest_paths", "check", "quick_drift", "list_inferred", "cmd_ingest"]

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
    converted_by_kind: Counter = field(default_factory=Counter)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    web_skipped: list[tuple[str, str]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chunk_count: int = 0
    embedded: int = 0
    state_docs: int = 0
    source_roots: int = 0

    @property
    def total(self) -> int:
        return self.new + self.updated + self.unchanged


def ingest_paths(config: Config, *, build_index: bool = True, web: bool = False) -> IngestReport:
    root = config.root
    cache_root = root / CACHE_REL
    report = IngestReport()
    bulk_text: dict[str, str] = {}  # mirror-tier docs: text goes to fux.db, not disk
    result = walk(config)
    configured = [d for dirs in config.sources.values() for d in dirs]
    report.source_roots = len(configured) - len(result.missing_dirs)
    report.warnings.extend(f"source folder not found: {d}" for d in result.missing_dirs)
    all_prev = manifest_read(root)
    prev = {k: e for k, e in all_prev.items() if e.get("origin") not in ("url", "attachment")}
    prev_web = {k: e for k, e in all_prev.items() if e.get("origin") in ("url", "attachment")}

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
        report.converted_by_kind[sf.kind] += 1
        report.updated += 1 if entry else 0
        report.new += 0 if entry else 1

    for rel in sorted(set(prev) - walked_rels):
        (root / prev[rel]["cache"]).unlink(missing_ok=True)
        report.removed.append(rel)

    if web and config.web.urls:
        _ingest_web(config, prev_web, report, bulk_text)
    else:
        # web entries persist across local-only runs — refreshing them needs --web
        for url in sorted(prev_web):
            report.entries.append(prev_web[url])
            report.unchanged += 1
            # Mirror-tier text exists only as db rows, and the index rewrite
            # replaces that table wholesale: carry it forward, or a plain
            # `fux ingest` would quietly delete the crawled corpus.
            _carry_bulk_text(config, url, bulk_text)

    if cache_root.is_dir() or report.entries:
        _write_dir_indexes(cache_root, report.entries)
    # Lock (committed) and manifest (runtime) are written together, in one scope,
    # so the recipe and the state they describe can never drift apart.
    manifest_write(root, report.entries)
    lock_write(
        root, records_from_entries(report.entries, max_age_days=config.web.max_age_days)
    )

    if build_index and report.entries:
        from ..index import build_index as _build

        report.chunk_count = _build(config, report.entries, bulk_text)
        try:
            from ..embed.store import build_vectors

            report.embedded = build_vectors(config)
        except FuxError as exc:  # a broken bundle must not block lexical ingest
            report.warnings.append(f"semantic vectors skipped: {exc}")
        report.state_docs = _write_state_plane(config, report.entries)
    return report


def _write_state_plane(config: Config, entries: list[dict]) -> int:
    """Rewrite `.fux/state/` from the freshly built index — same scope as the lock.

    Doing this here, rather than in a separate pass, is what makes the
    three-way `--check` meaningful: state, lock and sources are written from
    one view of the corpus, so a disagreement can only mean a stale commit.
    """
    from ..embed.fuxvec import doc_code
    from ..embed.store import load_vectors
    from ..index import backend_for
    from ..index.bm25f import path_tokens, tokenize
    from ..state import DocState, bloom, write_state

    files = backend_for(config).load(config.root)
    vectors = load_vectors(config.root)
    by_source = {e["source"]: e for e in entries}
    docs = []
    for doc_id in sorted(files):
        meta = files[doc_id]
        terms = set(path_tokens(doc_id)) | set(tokenize(meta.get("title", "")))
        for chunk in meta["chunks"]:
            terms |= set(tokenize(chunk["heading"])) | set(tokenize(chunk["text"]))
        entry = by_source.get(doc_id, {})
        flags = [meta.get("fidelity", "inferred")]
        if entry.get("origin") in ("url", "attachment"):
            flags.append("web")
        vecs = (vectors.get(doc_id) or {}).get("vecs", [])
        docs.append(
            DocState(
                doc_id=doc_id,
                sha12=meta["sha256"][:12],
                title=meta.get("title", ""),
                flags=flags,
                code=doc_code(vecs),
                sig=bloom.build(terms),
            )
        )
    return write_state(config.root, docs)


def _ingest_web(
    config: Config, prev_web: dict[str, dict], report: IngestReport, bulk_text: dict[str, str]
) -> None:
    from . import web as webmod

    mirror = config.web.tier == "mirror"
    renderer = None
    if config.web.render == "cdp":
        from .cdp import make_renderer

        renderer = make_renderer(config.web)
    crawl_report = webmod.crawl(config.web, renderer=renderer)
    report.web_skipped = list(crawl_report.skipped)
    seen_urls = set()
    for art in crawl_report.artifacts:
        if art.url in seen_urls:
            continue
        seen_urls.add(art.url)
        entry = prev_web.get(art.url)
        cache_rel_prev = entry.get("cache") if entry else webmod.cache_rel_for_url(art.url)
        cache_path = config.root / cache_rel_prev if cache_rel_prev else None
        if entry and entry.get("sha256") == art.sha256 and (
            mirror or not entry.get("cache") or (cache_path and cache_path.is_file())
        ):
            report.entries.append(entry)  # unchanged page: byte-stable no-op
            report.unchanged += 1
            if mirror:
                # Text lives only in fux.db, and save() rewrites that table
                # wholesale — carry the unchanged rows forward or they vanish.
                _carry_bulk_text(config, art.url, bulk_text)
            continue
        fetched_at = webmod.fetched_at_now()
        if art.duplicate_of:
            report.entries.append(_web_entry(art, "", "dedup", art.title, fetched_at))
            report.converted_by_kind["web"] += 1
            report.new += 0 if entry else 1
            report.updated += 1 if entry else 0
            continue
        conv = webmod.convert_artifact(art, config.ingest.max_kb)
        report.warnings.extend(conv.warnings)
        if conv.skipped:
            report.web_skipped.append((art.url, conv.skipped))
            continue
        meta = _web_meta(art, conv, fetched_at)
        if mirror:
            # Bulk tier: no file on disk at any corpus size — commit the recipe,
            # never the warehouse. The text becomes a docs_text row.
            from ..index import doc_id_for

            cache_rel = ""
            bulk_text[doc_id_for(_web_entry(art, "", conv.converter, meta["title"], fetched_at))] = (
                conv.body
            )
        else:
            cache_rel = webmod.cache_rel_for_url(art.url)
            text = fm_dumps(meta, conv.body)
            target = config.root / cache_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.is_file() or target.read_text(encoding="utf-8") != text:
                target.write_text(text, encoding="utf-8")
        report.entries.append(_web_entry(art, cache_rel, conv.converter, meta["title"], fetched_at))
        report.converted_by_kind["web"] += 1
        report.updated += 1 if entry else 0
        report.new += 0 if entry else 1
    for url in sorted(set(prev_web) - seen_urls):
        if prev_web[url].get("cache"):
            (config.root / prev_web[url]["cache"]).unlink(missing_ok=True)
        report.removed.append(url)
    webmod.write_web_skips(config.root, report.web_skipped)


def _carry_bulk_text(config: Config, url: str, bulk_text: dict[str, str]) -> None:
    from ..index import sqlstore
    from .lock import web_doc_id

    doc_id = web_doc_id(url)
    stored = sqlstore.load_text(config.root, doc_id)
    if stored is not None:
        bulk_text[doc_id] = stored


def _web_meta(art, conv, fetched_at: str) -> dict:
    title = art.title or Path(urlsplit_path(art.url)).stem or art.url
    meta = {
        "type": "Ingested Document",
        "title": title,
        "description": f"Ingested from {art.url} ({art.kind})",
        "timestamp": fetched_at,
        "source": art.url,
        "source_sha256": art.sha256,
        "origin": art.origin,
        "fidelity": "inferred",
        "converter": conv.converter,
        "converted_at": fetched_at,
        "fux_version": __version__,
        "url": art.url,
        "depth": art.depth,
        "fetched_at": fetched_at,
    }
    if art.parent:
        meta["parent"] = art.parent
    if art.renderer:
        meta["renderer"] = art.renderer
    if conv.truncated:
        meta["truncated"] = True
    return meta


def urlsplit_path(url: str) -> str:
    from urllib.parse import urlsplit

    return urlsplit(url).path


def _web_entry(art, cache_rel: str, converter: str, title: str, fetched_at: str) -> dict:
    entry = {
        "source": art.url,
        "cache": cache_rel,
        "type": "web",
        "kind": art.kind,
        "sha256": art.sha256,
        "size": len(art.data),
        "fidelity": "inferred",
        "converter": converter,
        "converted_at": fetched_at,
        "fetched_at": fetched_at,
        "line_offset": None,
        "fux_version": __version__,
        "title": title,
        "origin": art.origin,
        "url": art.url,
        "depth": art.depth,
    }
    if art.parent:
        entry["parent"] = art.parent
    if art.renderer:
        entry["renderer"] = art.renderer
    if art.duplicate_of:
        entry["duplicate_of"] = art.duplicate_of
    return entry


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
        if not entry.get("cache"):
            continue  # sha-deduped web entry: provenance only, no cache file
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
    started = time.perf_counter()
    root = find_root()
    config = load(root)

    if args.check:
        # Three-way: committed state ↔ fux.lock ↔ sources. Reads the lock only,
        # so this works on a fresh clone before anything has been built.
        status = check(config)
        if status.clean:
            print(f"cache is fresh ({status.tracked} sources tracked)")
            return 0
        for label, rows in (
            ("DRIFT", status.drift), ("STALE", status.stale), ("STATE-DESYNC", status.desync)
        ):
            for doc_id, reason in rows:
                print(f"  {label}  {doc_id}  ({reason})")
        print(f"{status.count} stale of {status.tracked} · run `fux ingest` to refresh")
        # advisory by default; --strict makes drift blocking (exit 2, per contract)
        return 2 if args.strict else 0

    if getattr(args, "advanced", None):
        from .advanced import upgrade

        print(upgrade(config, args.advanced))
        return 0

    if args.list_inferred:
        for entry in sorted(list_inferred(config), key=lambda e: e["source"]):
            print(f"{entry['source']}  ({entry['converter']})")
        return 0

    if args.list_skipped:
        from .web import read_web_skips

        for rel, reason in _detect_skips(config):
            print(f"{rel}  — {reason}")
        for url, reason in read_web_skips(root):
            print(f"{url}  — {reason}")
        return 0

    if args.web and not config.web.urls:
        print("no [sources.web] urls configured in fux.toml — nothing to crawl")
    report = ingest_paths(config, web=args.web)
    if report.total == 0 and not report.skipped:
        print("no source files found in the configured folders — check [sources] in fux.toml")
        for warning in report.warnings:
            print(f"warning: {warning}")
        return 0
    _print_summary(report, started)
    return 0


_KIND_LABELS = {
    "md": ("markdown", "native"),
    "txt": ("text", "native"),
    "code": ("code", "fenced"),
    "json": ("json", "flattened, stdlib"),
    "yaml": ("yaml", "fenced text"),
    "image": ("images", "metadata only — upgrade with --advanced"),
    "office": ("office", "markitdown extra"),
    "web": ("web", "fenced network — html→md + attachments"),
}


def _print_summary(report: IngestReport, started: float) -> None:
    plural = "root" if report.source_roots == 1 else "roots"
    print(f"Scanning {report.source_roots} source {plural}…")
    for kind, (label, how) in _KIND_LABELS.items():
        count = report.converted_by_kind.get(kind, 0)
        if count:
            verb = "stubbed" if kind == "image" else "converted"
            print(f"  {verb:<9}{count:>4} {label:<10} ({how})")
    if report.unchanged:
        print(f"  unchanged{report.unchanged:>4}            (cache reuse)")
    skipped_total = len(report.skipped) + len(report.web_skipped)
    if skipped_total:
        print(f"  skipped  {skipped_total:>4}            (see `fux ingest --list-skipped`)")
    if report.removed:
        print(f"  removed  {len(report.removed):>4}            (sources gone; cache pruned)")
    print(
        f"Cache: {CACHE_REL}  ({report.total} files, OKF bundle)   Lock: {LOCK_NAME}"
    )
    elapsed = time.perf_counter() - started
    vectors = f" · {report.embedded} chunks embedded" if report.embedded else ""
    print(f"Index: {report.chunk_count} chunks (BM25F){vectors}   Elapsed: {elapsed:.1f}s")
    for warning in report.warnings:
        print(f"warning: {warning}")


def _detect_skips(config: Config) -> list[tuple[str, str]]:
    """Recompute skip reasons without writing (extension, extras, binary sniff)."""
    result = walk(config)
    out = [(rel, "unrecognized extension") for rel in result.unknown]
    for sf in result.files:
        conv = convert(sf, sf.abspath.read_bytes(), config.ingest.max_kb)
        if conv.skipped:
            out.append((sf.rel, conv.skipped))
    return sorted(out)
