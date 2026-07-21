"""Fux command-line entry point.

This is a boundary: it is the *only* place (besides hook entrypoints) that catches
and renders `FuxError`. Internals raise; `main` translates to an exit code
(0 ok · 1 error · 2 blocking · 130 interrupted). Handlers import their modules
lazily so `fux --version` stays instant.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .errors import FuxError


def _cmd_setup(args) -> int:
    from .setup import cmd_setup

    return cmd_setup(args)


def _cmd_ingest(args) -> int:
    from .ingest import cmd_ingest

    return cmd_ingest(args)


def _cmd_query(args) -> int:
    from .query.api import cmd_query

    return cmd_query(args)


def _cmd_hook(args) -> int:
    from .hooks import cmd_hook

    return cmd_hook(args)


def _add_query_flags(sp: argparse.ArgumentParser, *, context: bool = False, answer: bool = False):
    sp.add_argument("query", help="natural-language question")
    sp.add_argument("--json", action="store_true", help="machine-readable output")
    sp.add_argument("--explain", action="store_true", help="show why each result ranked")
    sp.add_argument("--top", type=int, default=5, metavar="N", help="max results (default 5)")
    if context:
        sp.add_argument(
            "-C", "--context", type=int, default=4, metavar="N",
            help="passage lines to show (default 4; 0 = all)",
        )
    if answer:
        sp.add_argument(
            "--answer-max", type=int, default=None, metavar="N",
            help="max sentences in the answer (default: [answer] max_sentences)",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fux",
        description="Fux — a $0, deterministic knowledge engine over your own documents.",
    )
    parser.add_argument("--version", action="version", version=f"fux {__version__}")
    parser.set_defaults(_handler=None)
    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("setup", help="create or update fux.toml (wizard; -y for defaults)")
    for t, help_ in (
        ("docs", "docs source folder(s) (repeat or comma-separate)"),
        ("code", "code source folder(s)"),
        ("data", "data source folder(s) (json/yaml)"),
        ("images", "image source folder(s)"),
    ):
        sp.add_argument(f"--{t}", action="append", metavar="DIR", help=help_)
    sp.add_argument("-y", "--yes", action="store_true", help="accept defaults, no prompts")
    sp.add_argument("--agents", action="store_true", help="generate AGENTS.md + tool pointer files")
    sp.add_argument("--skills", action="store_true", help="generate fux-query/fux-ingest skills")
    sp.add_argument("--hooks", action="store_true", help="install Claude Code + Kiro hooks")
    sp.set_defaults(_handler=_cmd_setup)

    sp = sub.add_parser("ingest", help="convert configured sources into the .fux/ cache + index")
    sp.add_argument("--check", action="store_true", help="report drift vs the manifest (no writes)")
    sp.add_argument("--strict", action="store_true", help="with --check: drift exits 2 (blocking)")
    sp.add_argument("--web", action="store_true", help="also crawl [sources.web] (fenced network)")
    sp.add_argument(
        "--advanced", metavar="TARGET",
        help="upgrade one file/url to advanced fidelity (docling/tesseract)",
    )
    sp.add_argument("--list-inferred", action="store_true", help="list files at inferred fidelity")
    sp.add_argument("--list-skipped", action="store_true", help="list skipped files and why")
    sp.set_defaults(_handler=_cmd_ingest)

    sp = sub.add_parser("ask", help="ranked passages answering a question")
    _add_query_flags(sp, context=True)
    sp.set_defaults(_handler=_cmd_query, mode="ask")

    sp = sub.add_parser("find", help="ranked files matching a topic")
    _add_query_flags(sp)
    sp.set_defaults(_handler=_cmd_query, mode="find")

    sp = sub.add_parser("answer", help="extractive, cited answer to a question")
    _add_query_flags(sp, answer=True)
    sp.set_defaults(_handler=_cmd_query, mode="answer")

    sp = sub.add_parser("hook", help="agent-hook entrypoints (fail-open; internal)")
    sp.add_argument("event", choices=["prompt-submit", "session-end"])
    sp.set_defaults(_handler=_cmd_hook)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI boundary. Returns a process exit code; never raises FuxError."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "_handler", None)
    if handler is None:
        parser.print_help()
        return 0

    try:
        return handler(args)
    except FuxError as err:
        print(f"fux: {err}", file=sys.stderr)
        return err.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
