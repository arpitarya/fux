"""The ingest plane — git-dir adapter, consumer URL fetcher, `extracted`-mode
extractors, and the `fux ingest` CLI handler. See `run.py` for the orchestration."""

from __future__ import annotations

from ..config import find_root, load as load_config
from ..errors import FuxError
from .gitdir import read_types, source_dirs, source_excludes, walk_sources
from .run import run


def cmd_ingest(args) -> int:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")

    if getattr(args, "list_skipped", False):
        config = load_config(root)
        _, skipped = walk_sources(
            root,
            source_dirs(root, config.dirs_file),
            excludes=source_excludes(root, config.dirs_file),
            types=read_types(root),
        )
        for s in skipped:
            print(f"{s.rel_path}: {s.reason}")
        return 0

    ingest_and_report(root, args, refresh_urls=getattr(args, "refresh_urls", False))
    return 0


def ingest_and_report(args_root, args, *, refresh_urls: bool = False, only_urls=None):
    """Run one ingest and print its summary. **The only ingest the verbs call.**

    `fux add`, `fux remove` and `fux update` all end here rather than each
    printing their own version of the same three numbers — one format, so a
    person reading two different verbs' output is reading the same thing, and
    one write path into the index, which is what L3 needs (W-63).
    """
    progress = getattr(args, "progress", None)
    report = run(
        args_root,
        refresh_urls=refresh_urls,
        only_urls=only_urls,
        full=getattr(args, "full", False),
        progress=progress,
    )
    print(
        f"ingested {report.doc_count} docs ({report.changed_count} changed, "
        f"{report.reused_count} carried forward), "
        f"{len(report.skipped)} skipped, {len(report.written_shards)} shards written"
    )
    for s in report.skipped:
        print(f"  skip {s.rel_path}: {s.reason}")

    # Build the derived accelerator here, where the committed shards were just
    # written: `ask` should never pay for a build, and a stale accelerator that
    # silently falls back to scan would hide a real slowdown.
    if not getattr(args, "no_accelerator", False):
        from ..derive import build as build_accelerator

        accel_report = build_accelerator(args_root, progress=progress)
        print(
            f"accelerator: {accel_report.terms} terms, {accel_report.blocks} blocks, "
            f"{accel_report.postings} postings (derived, not committed)"
        )
    return report


def cmd_build(args) -> int:
    """`fux build` — rebuild the derived accelerator from the committed index.

    Exists because the derived plane is disposable by design: deleting
    `.fux/runtime/` must always be safe, and this is how it comes back without
    re-walking the source tree.
    """
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")

    from ..derive import build as build_accelerator

    report = build_accelerator(root, progress=getattr(args, "progress", None))
    print(
        f"accelerator rebuilt from the committed index: {report.docs} docs, "
        f"{report.terms} terms, {report.blocks} blocks, {report.postings} postings"
    )
    return 0
