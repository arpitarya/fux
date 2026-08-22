"""Fux command-line entry point.

This is a boundary: it is the *only* place (besides hook entrypoints) that
catches and renders `FuxError`. Internals raise; `main` translates to an exit
code (0 ok · 1 error · 2 blocking · 130 interrupted). Handlers import their
modules lazily so `fux --version` stays instant.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .errors import FuxError


def _cmd_setup(args) -> int:
    from .setup import cmd_setup

    return cmd_setup(args)


def _cmd_doctor(args) -> int:
    from .doctor import cmd_doctor

    return cmd_doctor(args)


def _cmd_ingest(args) -> int:
    from .ingest import cmd_ingest

    return cmd_ingest(args)


def _cmd_ask(args) -> int:
    from .query import cmd_ask

    return cmd_ask(args)


def _cmd_find(args) -> int:
    from .query import cmd_find

    return cmd_find(args)


def _cmd_answer(args) -> int:
    from .query import cmd_answer

    return cmd_answer(args)


def _cmd_add(args) -> int:
    from .sources import cmd_add

    return cmd_add(args)


def _cmd_remove(args) -> int:
    from .sources import cmd_remove

    return cmd_remove(args)


def _cmd_update(args) -> int:
    from .sources import cmd_update

    return cmd_update(args)


def _cmd_build(args) -> int:
    from .ingest import cmd_build

    return cmd_build(args)


def _cmd_hooks(args) -> int:
    from .maintain import cmd_hooks

    return cmd_hooks(args)


def _cmd_explain(args) -> int:
    from .graph import cmd_explain

    return cmd_explain(args)


def _cmd_graph(args) -> int:
    from .graph import cmd_graph

    return cmd_graph(args)


def _cmd_path(args) -> int:
    from .graph import cmd_path

    return cmd_path(args)


#: The write verbs — the only ones that construct a `Progress` in `main`
#: (W-64). `add`/`remove`/`update` joined it in W-63: they end in
#: `ingest.run()`, so they inherit the bar from that seam rather than growing
#: one of their own.
_PROGRESS_COMMANDS = ("ingest", "build", "add", "remove", "update")


def _add_progress_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--no-progress",
        action="store_true",
        help="never paint the progress bar, even on a TTY",
    )
    group.add_argument(
        "--progress",
        dest="force_progress",
        action="store_true",
        help="paint the progress bar even off a TTY, overriding FUX_NO_PROGRESS too",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fux", description="rank, fetch, verify — an index over the systems that own your docs")
    parser.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_setup = sub.add_parser(
        "setup", help="write the consumer-owned files into .fux/ (write-if-missing)"
    )
    # W-68 / ADR-AGENT-POLICY decisions 5 and 6. The agent policy installs by
    # default, so this is a user's one-shot escape; `[agents] install = []` in
    # `fux.toml` is its durable form. A flag rather than a verb — ADR-CLI veto 1.
    p_setup.add_argument(
        "--no-agents",
        action="store_true",
        help="do not write the agent policy files outside .fux/ (.claude/, .github/, .kiro/)",
    )
    p_setup.set_defaults(func=_cmd_setup)

    p_doctor = sub.add_parser("doctor", help="check environment and repo health")
    # W-66 Phase 4. `doctor` is where the detached runner becomes visible, and
    # an agent reading that needs a parse rather than a sentence (ADR-CLI,
    # 2026-08-22). Promotion to a `fux status` verb has a written condition in
    # ADR-CLI; it is not a matter of feeling crowded.
    p_doctor.add_argument("--json", action="store_true", help="machine-readable report")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_ingest = sub.add_parser("ingest", help="walk configured sources into the committed index")
    p_ingest.add_argument("--list-skipped", action="store_true", help="print skipped files and why, then exit")
    # Retired into `fux update` (W-63). Kept for one release as a hidden
    # alias — it is a flag rather than a verb, it is older than `fux url` and
    # more likely to be in someone's CI, and leaving it in costs nothing.
    # `fux url` was deleted outright; this was not.
    p_ingest.add_argument("--refresh-urls", action="store_true", help=argparse.SUPPRESS)
    p_ingest.add_argument(
        "--full",
        action="store_true",
        help="re-extract every document instead of carrying unchanged ones forward (same bytes, slower; the complete term-collision check)",
    )
    p_ingest.add_argument(
        "--no-accelerator",
        action="store_true",
        help="skip building the derived accelerator (results are unaffected either way)",
    )
    # W-66 Phase 2 / ADR-MAINTENANCE decision 1d. `--stop` is the takeover
    # without the run; a plain `fux ingest` takes over and then runs. It sits
    # on `ingest` rather than becoming a verb because ADR-CLI veto 1 forbids
    # `fux <verb> <subverb>` and `ingest` already owns the re-index.
    p_ingest.add_argument(
        "--stop",
        action="store_true",
        help="stop a background re-index and do not run one (exit 0 if none was running)",
    )
    # The two halves of the deferred hook. Not surface: one is what the hook
    # calls, the other is what the hook spawned. Neither is for a person.
    p_ingest.add_argument("--spawn-runner", action="store_true", help=argparse.SUPPRESS)
    p_ingest.add_argument("--runner", action="store_true", help=argparse.SUPPRESS)
    _add_progress_flags(p_ingest)
    p_ingest.set_defaults(func=_cmd_ingest)

    p_build = sub.add_parser(
        "build", help="rebuild the derived accelerator from the committed index"
    )
    _add_progress_flags(p_build)
    p_build.set_defaults(func=_cmd_build)

    # The source group. Flat verbs over all three lists, dispatching on the
    # entry — `fux source add` is the subcommand tree ADR-CLI decision 1
    # refuses, and it is the shape this replaced `fux url` to avoid growing.
    def _entry_flags(p: argparse.ArgumentParser) -> None:
        """The attribute flags. Each is checked against the list the entry
        dispatched to, so `--cdp` on a directory is an error, not a no-op."""
        p.add_argument("--types", action="store_true", help="the entry is a file-type pattern (.fux/sources/types)")
        p.add_argument("--cdp", action="store_true", help="URLs: record fetch=cdp")
        p.add_argument("--http", action="store_true", help="URLs: record fetch=http (the default)")
        p.add_argument("--plain", action="store_true", help="URLs: record meta=plain — readable display text in the index")
        p.add_argument("--hashed", action="store_true", help="URLs: record meta=hashed (the default)")
        p.add_argument("--archived", action="store_true", help="dirs: record archived=true")
        p.add_argument("--dry-run", action="store_true", help="print the line and the plan; write nothing")

    p_add = sub.add_parser(
        "add", help="list a directory, a document or a URL, and ingest it (omit the entry to list everything)"
    )
    p_add.add_argument("entry", nargs="?", help="a path, a single file, or an http(s) URL")
    _entry_flags(p_add)
    p_add.add_argument("--no-ingest", action="store_true", help="record the line only; do not ingest")
    p_add.add_argument(
        "--no-fetch",
        action="store_true",
        help="URLs: record the line and ingest offline, without fetching this URL",
    )
    _add_progress_flags(p_add)
    p_add.set_defaults(func=_cmd_add)

    p_remove = sub.add_parser(
        "remove", help="take an entry out of the corpus — deletes its line, or excludes it if an ancestor is listed"
    )
    p_remove.add_argument("entry", help="a path, a single file, or an http(s) URL")
    p_remove.add_argument("--types", action="store_true", help="the entry is a file-type pattern")
    p_remove.add_argument("--dry-run", action="store_true", help="say which branch it would take; write nothing")
    p_remove.add_argument("--no-ingest", action="store_true", help="edit the line only; do not re-ingest")
    _add_progress_flags(p_remove)
    p_remove.set_defaults(func=_cmd_remove)

    p_update = sub.add_parser(
        "update", help="re-read what is already listed, re-fetching URLs (replaces `ingest --refresh-urls`)"
    )
    p_update.add_argument("entry", nargs="?", help="one listed entry; omit for all of them")
    p_update.add_argument(
        "--check",
        action="store_true",
        help="read-only: report what has drifted. Offline for files; does not fetch URLs",
    )
    _add_progress_flags(p_update)
    p_update.set_defaults(func=_cmd_update)

    def _query_parser(name: str, help_text: str):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("query", help="natural-language question")
        p.add_argument("--json", action="store_true", help="machine-readable output")
        # The accelerator is asserted byte-identical to the scan, so either
        # flag only ever changes speed. Scan-by-default (Arpit, 2026-08-21)
        # needs no build step; `--fast` opts into the derived accelerator
        # when one exists. `--scan` is kept, now redundant with the default,
        # because it is what a bug report reproduces against explicitly.
        path_group = p.add_mutually_exclusive_group()
        path_group.add_argument(
            "--fast",
            action="store_true",
            help="use the derived accelerator when it exists and is fresh (same results, faster)",
        )
        path_group.add_argument(
            "--scan",
            action="store_true",
            help="force the reference scan path (the default; kept for explicit bug reproduction)",
        )
        return p

    p_ask = _query_parser("ask", "answer a question from the committed index, with citations")
    p_ask.add_argument("--top", type=int, default=5, metavar="N", help="max results (default 5)")
    p_ask.add_argument("--explain", action="store_true", help="report which path answered")
    p_ask.add_argument(
        "--hybrid",
        action="store_true",
        help="fuse the dense lane in via RRF (OFF by default: it changes rankings, "
        "and on this repo's frozen R2 questions it makes them worse)",
    )
    p_ask.set_defaults(func=_cmd_ask)

    p_find = _query_parser("find", "ranked document locations, one per line")
    p_find.add_argument("--top", type=int, default=5, metavar="N", help="max results (default 5)")
    p_find.set_defaults(func=_cmd_find)

    p_answer = _query_parser(
        "answer", "the single best answer — a fetched, re-scored passage when the source is reachable"
    )
    p_answer.add_argument(
        "--no-refer",
        action="store_true",
        help="skip the refer plane; answer from the index's own structure alone",
    )
    p_answer.set_defaults(func=_cmd_answer)

    p_hooks = sub.add_parser("hooks", help="install the git hooks and the index merge driver")
    p_hooks.add_argument("--install", action="store_true", help="write them (the default)")
    p_hooks.add_argument("--status", action="store_true", help="report what is wired")
    p_hooks.add_argument("--uninstall", action="store_true", help="remove only what fux wrote")
    p_hooks.add_argument("--json", action="store_true", help="machine-readable status")
    p_hooks.set_defaults(func=_cmd_hooks)

    # The graph group. Flat, like every other verb — `fux graph path` would be
    # the first subcommand tree on this surface, and "no subcommand tree" is
    # the constraint ADR-CLI keeps.
    p_explain = sub.add_parser("explain", help="one document's outbound edges and its community")
    p_explain.add_argument("doc", help="a doc id or the loc `find` printed")
    p_explain.add_argument("--json", action="store_true", help="machine-readable output")
    p_explain.set_defaults(func=_cmd_explain)

    p_graph = sub.add_parser("graph", help="the neighbourhood around a query's best answers")
    p_graph.add_argument("query", help="natural-language question")
    p_graph.add_argument("--json", action="store_true", help="machine-readable output")
    graph_path_group = p_graph.add_mutually_exclusive_group()
    graph_path_group.add_argument(
        "--fast",
        action="store_true",
        help="use the derived accelerator for the seed query (same results, faster)",
    )
    graph_path_group.add_argument(
        "--scan",
        action="store_true",
        help="force the reference scan path for the seeds (the default)",
    )
    p_graph.set_defaults(func=_cmd_graph)

    p_path = sub.add_parser("path", help="how two documents are connected, most reliable route first")
    p_path.add_argument("src", metavar="FROM", help="the document the route starts at")
    p_path.add_argument("dst", metavar="TO", help="the document the route ends at")
    p_path.add_argument("--hops", type=int, default=2, metavar="N", help="max edges in a route (default 2)")
    p_path.add_argument("--json", action="store_true", help="machine-readable output")
    p_path.set_defaults(func=_cmd_path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    if args.command in _PROGRESS_COMMANDS:
        # Imported here, not at module level — ADR-CLI decision 7, `--version`
        # stays instant. One `Progress` for the whole invocation (W-64): an
        # `ingest` that also builds the accelerator is one continuous
        # sequence, not two bars fighting over the same terminal line.
        from .progress import Progress

        args.progress = Progress(no_progress=args.no_progress, force=args.force_progress)
    try:
        return args.func(args)
    except FuxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
