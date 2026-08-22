"""The ingest plane — git-dir adapter, consumer URL fetcher, `extracted`-mode
extractors, and the `fux ingest` CLI handler. See `run.py` for the orchestration."""

from __future__ import annotations

import sys

from ..config import find_root, load as load_config
from ..errors import FuxError
from .gitdir import read_types, source_dirs, source_excludes, walk_sources
from .run import run


def _report_takeover(result: str, root, *, halting: bool) -> int:
    """Render what `runner.request_stop` found. ASCII only — Windows consoles.

    `halting` distinguishes `fux ingest --stop` (the takeover *is* the whole
    command) from a takeover on the way into a real run, which stays quiet
    unless something was actually stopped.
    """
    from ..maintain import runner as runner_mod

    if result == "wedged":
        raise FuxError(
            "a background re-index is running and did not stop when asked. Nothing was "
            f"written. Its lock is {runner_mod.lock_path(root)} - if you are certain the "
            "process is gone, delete that file and re-run"
        )
    if halting:
        print(
            {
                "idle": "no background re-index was running",
                "stopped": "stopped the background re-index",
                "stale": "cleared a stale lock; no process was running",
            }[result]
        )
    elif result in ("stopped", "stale"):
        print(
            "stopped the background re-index"
            if result == "stopped"
            else "cleared a stale lock left by a killed re-index",
            file=sys.stderr,
        )
    return 0


def cmd_ingest(args) -> int:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")

    from ..maintain import runner as runner_mod

    if getattr(args, "runner", False):
        # We *are* the detached background re-index (W-66 Phase 2). Losing the
        # race for the lock is success, not failure: the live runner re-reads
        # the dirty list, which is a union, so nothing is dropped by exiting.
        runner_mod.run_once(root)
        return 0

    if getattr(args, "spawn_runner", False):
        # The hook's whole job. Constant time in the corpus — one dirty-list
        # write plus one spawn — which is ADR-MAINTENANCE veto condition 5.
        pending = runner_mod.record_head(root)
        if runner_mod.spawn(root):
            print(f"fux: re-indexing in the background ({pending} changed path(s) pending)", file=sys.stderr)
        else:
            print(f"fux: a re-index is already running ({pending} changed path(s) pending)", file=sys.stderr)
        return 0

    if getattr(args, "stop", False):
        # `--stop` with nothing running is SUCCESS (ADR-CLI, 2026-08-22): a
        # command whose job is "make sure it is not running" has done its job.
        return _report_takeover(runner_mod.request_stop(root), root, halting=True)

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

    **The takeover lives here, not in `cmd_ingest`** (W-66 Phase 2,
    ADR-MAINTENANCE decision 1d). Every verb that reaches this function is
    about to write the index, so every one of them has to stop a background
    runner first — putting it on the one shared seam is the same argument that
    put the printing here.
    """
    from ..maintain import runner as runner_mod

    progress = getattr(args, "progress", None)
    _report_takeover(runner_mod.take_over(args_root), args_root, halting=False)
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
