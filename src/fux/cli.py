"""Fux command-line entry point.

This is a boundary: it is the *only* place (besides hook entrypoints) that catches
and renders `FuxError`. Internals raise; `main` translates to an exit code.
Command implementations land here as the rebuild proceeds — see docs/fux-plan.md.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .errors import FuxError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fux",
        description="Fux — rules bound to code, checked deterministically.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"fux {__version__}",
    )
    # Subcommands (check, fix, ...) are added as the rebuild proceeds.
    parser.set_defaults(_handler=None)
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
