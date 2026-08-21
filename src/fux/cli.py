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


def _cmd_url(args) -> int:
    from .sources import cmd_url

    return cmd_url(args)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fux", description="rank, fetch, verify — an index over the systems that own your docs")
    parser.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser(
        "setup", help="write the consumer-owned files into .fux/ (write-if-missing)"
    ).set_defaults(func=_cmd_setup)

    sub.add_parser("doctor", help="check environment and repo health").set_defaults(func=_cmd_doctor)

    p_ingest = sub.add_parser("ingest", help="walk configured sources into the committed index")
    p_ingest.add_argument("--list-skipped", action="store_true", help="print skipped files and why, then exit")
    p_ingest.add_argument(
        "--refresh-urls",
        action="store_true",
        help="fetch [sources.url] urls through the consumer fetcher (the ONLY networked ingest path; off by default)",
    )
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
    p_ingest.set_defaults(func=_cmd_ingest)

    sub.add_parser(
        "build", help="rebuild the derived accelerator from the committed index"
    ).set_defaults(func=_cmd_build)

    # Flags, not a subcommand tree: `fux url add` would be the first nesting on
    # the surface, and "no subcommand tree" is the constraint ADR-CLI keeps.
    p_url = sub.add_parser("url", help="record a URL in the committed list (never fetches)")
    p_url.add_argument("url", nargs="?", help="the URL to add or update; omit to list")
    p_url.add_argument("--cdp", action="store_true", help="record fetch=cdp for this URL")
    p_url.add_argument("--http", action="store_true", help="record fetch=http (the default)")
    p_url.add_argument("--plain", action="store_true", help="record meta=plain — readable display text in the index")
    p_url.add_argument("--hashed", action="store_true", help="record meta=hashed (the default)")
    p_url.add_argument("--remove", action="store_true", help="delete this URL's line")
    p_url.set_defaults(func=_cmd_url)

    def _query_parser(name: str, help_text: str):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("query", help="natural-language question")
        p.add_argument("--json", action="store_true", help="machine-readable output")
        # The accelerator is asserted byte-identical to the scan, so this flag
        # only ever changes speed. It exists to reproduce a bug against the
        # reference path.
        p.add_argument("--scan", action="store_true", help="force the reference scan path")
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
    p_graph.add_argument("--scan", action="store_true", help="force the reference scan path for the seeds")
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
    try:
        return args.func(args)
    except FuxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
