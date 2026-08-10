"""The ingest plane — git-dir adapter, `extracted`-mode extractors, and the
`fux ingest` CLI handler. See `run.py` for the orchestration."""

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

    report = run(root)
    print(
        f"ingested {report.doc_count} docs ({report.changed_count} changed), "
        f"{len(report.skipped)} skipped, {len(report.written_shards)} shards written"
    )
    for s in report.skipped:
        print(f"  skip {s.rel_path}: {s.reason}")
    return 0
