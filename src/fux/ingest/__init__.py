"""The ingest plane — git-dir adapter, consumer URL middleware, `extracted`-mode
extractors, and the `fux ingest` CLI handler. See `run.py` for the orchestration."""

from __future__ import annotations

from ..config import find_root, load as load_config
from ..errors import FuxError
from .gitdir import walk_sources
from .run import run


def cmd_ingest(args) -> int:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")

    if getattr(args, "list_skipped", False):
        config = load_config(root)
        _, skipped = walk_sources(root, config.source_dirs)
        for s in skipped:
            print(f"{s.rel_path}: {s.reason}")
        return 0

    report = run(root, refresh_urls=getattr(args, "refresh_urls", False))
    print(
        f"ingested {report.doc_count} docs ({report.changed_count} changed), "
        f"{len(report.skipped)} skipped, {len(report.written_shards)} shards written"
    )
    for s in report.skipped:
        print(f"  skip {s.rel_path}: {s.reason}")

    # Build the derived accelerator here, where the committed shards were just
    # written: `ask` should never pay for a build, and a stale accelerator that
    # silently falls back to scan would hide a real slowdown.
    if not getattr(args, "no_accelerator", False):
        from ..derive import build as build_accelerator

        accel_report = build_accelerator(root)
        print(
            f"accelerator: {accel_report.terms} terms, {accel_report.blocks} blocks, "
            f"{accel_report.postings} postings (derived, not committed)"
        )
    return 0


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

    report = build_accelerator(root)
    print(
        f"accelerator rebuilt from the committed index: {report.docs} docs, "
        f"{report.terms} terms, {report.blocks} blocks, {report.postings} postings"
    )
    return 0
