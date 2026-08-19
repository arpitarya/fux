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


def _cmd_build(args) -> int:
    from .ingest import cmd_build

    return cmd_build(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fux", description="rank, fetch, verify — an index over the systems that own your docs")
    parser.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="check environment and repo health").set_defaults(func=_cmd_doctor)

    p_ingest = sub.add_parser("ingest", help="walk configured sources into the committed index")
    p_ingest.add_argument("--list-skipped", action="store_true", help="print skipped files and why, then exit")
    p_ingest.add_argument(
        "--refresh-urls",
        action="store_true",
        help="fetch [sources.url] urls through the consumer fetcher (the ONLY networked ingest path; off by default)",
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

    _query_parser("answer", "the single best answer the index can give").set_defaults(func=_cmd_answer)

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
