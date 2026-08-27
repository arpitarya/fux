"""The ingest plane — git-dir adapter, consumer URL fetcher, `extracted`-mode
extractors, and the `fux ingest` CLI handler. See `run.py` for the orchestration."""

from __future__ import annotations

import sys

from ..config import find_root, load as load_config
from ..errors import FuxError
from .gitdir import partition, read_types, source_dirs, source_excludes, walk_sources
# ⚠ **Aliased, and the alias is the point.** Importing this as the bare name
# `run` shadows the SUBMODULE `fux.ingest.run`, so `from fux.ingest import run`
# and `import fux.ingest.run as x` both bind this function -- and any attribute
# access on the result raises `AttributeError`. That shape cost three defects on
# 2026-08-27, one of them a daemon that reported success while indexing nothing
# for a day. The alias costs one word and removes the ambiguity at the source.
from .run import run as run_ingest


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
        from ..config import DEFAULT_TYPES_FILE
        from . import fuxignore

        config = load_config(root)
        _, skipped = walk_sources(
            root,
            source_dirs(root, config.dirs_file),
            excludes=source_excludes(root, config.dirs_file),
            types=read_types(root),
            ignores=fuxignore.read(root),
        )
        # `path: reason`, sorted, unprefixed — byte-identical to what
        # `.fux/runtime/skipped` holds, on purpose. This output is the
        # machine-readable twin of that file and things pipe it; the `skip` /
        # `not indexed` wording belongs to the *human* summary and to the
        # notice's indented prose lines, neither of which anything parses.
        for s in skipped:
            print(f"{s.rel_path}: {s.reason}")
        # The duplicate warning reaches stderr here too, not only on an ingest:
        # `--list-skipped` is the command someone runs *because* a file is
        # missing, which is precisely when a pattern stated in two places is
        # the thing they need told.
        for line in fuxignore.duplicate_warnings(
            root, dirs_file=config.dirs_file, types_file=DEFAULT_TYPES_FILE
        ):
            print(line, file=sys.stderr)
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
    # W-86 P6: every command that writes the committed index holds the write
    # lock. Evicting a background runner and then writing unprotected was the
    # gap fork C closed — two foreground ingests raced, and nothing noticed.
    with runner_mod.write_lock(args_root):
        report = run_ingest(
            args_root,
            refresh_urls=refresh_urls,
            only_urls=only_urls,
            full=getattr(args, "full", False),
            progress=progress,
        )
    # W-93: two counts, not one. `not indexed` is a committed list doing its
    # job and needs no attention; `skipped` is a file fux could not read and
    # may. One number over both populations was 598 + 1 on this repo, which
    # reads as 599 problems. ADR-INGEST decision 15.
    not_indexed, unreadable = partition(report.skipped)
    print(
        f"ingested {report.doc_count} docs ({report.changed_count} changed, "
        f"{report.reused_count} carried forward), "
        f"{len(not_indexed)} not indexed, {len(unreadable)} skipped, "
        f"{len(report.written_shards)} shards written"
    )
    # W-88: every skip is still reported — the first time it is seen. A corpus
    # of any size makes the unconditional list a wall printed on every run, and
    # a wall nobody reads defeats decision 4 as thoroughly as silence would.
    # The full list stays one command away (`--list-skipped`) and one file away
    # (`.fux/runtime/skipped`).
    from . import skipnotice

    for line in skipnotice.render(args_root, report.skipped):
        print(line)
    # W-93: a fux-written `.fuxignore` line freezes the verdict that produced
    # it, so a line that has stopped being true is an invisible filter. The
    # freeze is Arpit's call; making it loud is this.
    config = load_config(args_root)
    for line in skipnotice.stale_warnings(
        args_root,
        types=read_types(args_root),
        excludes=source_excludes(args_root, config.dirs_file),
    ):
        print(line, file=sys.stderr)
    # Advisory, and on stderr so a piped `fux ingest` is unchanged by it.
    for line in report.warnings:
        print(line, file=sys.stderr)

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
    from ..maintain import runner as runner_mod

    # The accelerator is derived, but it is written into `.fux/runtime/` while
    # a concurrent ingest may be replacing the committed shards it is derived
    # FROM. Taking the same lock is what stops a rebuild reading half of one
    # index and half of another.
    with runner_mod.write_lock(root):
        report = build_accelerator(root, progress=getattr(args, "progress", None))
    print(
        f"accelerator rebuilt from the committed index: {report.docs} docs, "
        f"{report.terms} terms, {report.blocks} blocks, {report.postings} postings"
    )
    return 0
