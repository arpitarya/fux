"""`fux` CLI — argparse dispatch over the deterministic command surface (plan §9)."""
from __future__ import annotations

import argparse

from fux import __version__, clicmds, cliquery, hooks


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fux", description="Fux knowledge engine ($0, deterministic).")
    p.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="scaffold .fux/ + wire hooks in this project")
    init.add_argument("--recall", action="store_true", help="also wire the UserPromptSubmit recall hook")
    init.set_defaults(fn=clicmds.cmd_init)

    sub.add_parser("build", help="regenerate INDEX + rules.json + graph ($0)").set_defaults(fn=clicmds.cmd_build)
    chk = sub.add_parser("check", help="validate schema/refs/staleness/conflicts")
    chk.add_argument("--fix", action="store_true", help="apply mechanical $0 repairs")
    chk.set_defaults(fn=clicmds.cmd_check)

    sub.add_parser("context", help="emit the compact INDEX (SessionStart hook)").set_defaults(fn=clicmds.cmd_context)

    rc = sub.add_parser("recall", help="keyword-retrieve relevant rules")
    rc.add_argument("query")
    rc.add_argument("--top", type=int, default=6)
    rc.set_defaults(fn=cliquery.cmd_recall)

    why = sub.add_parser("why", help="explain a rule + rationale + linked code")
    why.add_argument("id")
    why.set_defaults(fn=cliquery.cmd_why)

    refs = sub.add_parser("refs", help="reverse lookup: which rules govern this file")
    refs.add_argument("file")
    refs.set_defaults(fn=cliquery.cmd_refs)

    new = sub.add_parser("new", help="scaffold a rule from a template")
    new.add_argument("type")
    new.add_argument("id")
    new.add_argument("--domain", default="general")
    new.set_defaults(fn=cliquery.cmd_new)

    sub.add_parser("coverage", help="%% of important files with a governing rule").set_defaults(fn=cliquery.cmd_coverage)
    sub.add_parser("verify", help="run invariant/example checks").set_defaults(fn=cliquery.cmd_verify)
    sub.add_parser("tour", help="emit an ordered ONBOARDING.md").set_defaults(fn=cliquery.cmd_tour)

    # Internal hook entrypoints (wired by `fux init`, not for direct use).
    sub.add_parser("hook-touch").set_defaults(fn=lambda a: hooks.post_tool_use())
    sub.add_parser("hook-check").set_defaults(fn=lambda a: hooks.stop())
    sub.add_parser("hook-recall").set_defaults(fn=lambda a: hooks.user_prompt_recall())
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
