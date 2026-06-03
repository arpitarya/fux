"""`fux` CLI — argparse dispatch over the deterministic command surface (plan §9)."""
from __future__ import annotations

import argparse

from fux import __version__, clicmds, cligraph, cliquery, hooks


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

    sv = sub.add_parser("savings", help="estimate the token-cost win of Fux ($0)")
    sv.add_argument("query", nargs="?", help="optional: cost a specific lookup")
    sv.add_argument("--top", type=int, default=3)
    sv.set_defaults(fn=cliquery.cmd_savings)

    lt = sub.add_parser("lint", help="rule-quality checks (why/code_refs/edges/provenance)")
    lt.add_argument("--strict", action="store_true", help="exit 1 if any finding")
    lt.set_defaults(fn=cliquery.cmd_lint)

    sub.add_parser("stats", help="project knowledge-health dashboard + score").set_defaults(fn=cliquery.cmd_stats)

    gt = sub.add_parser("gate", help="CI / pre-commit enforcement (exit 2 on blocking)")
    gt.add_argument("--install", action="store_true", help="install a git pre-commit hook")
    gt.add_argument("--strict-lint", action="store_true", help="treat lint findings as blocking")
    gt.set_defaults(fn=clicmds.cmd_gate)

    sub.add_parser("mcp", help="serve the substrate over MCP (stdio JSON-RPC)").set_defaults(fn=clicmds.cmd_mcp)

    q = sub.add_parser("query", help="traverse the graph from rules matching a question")
    q.add_argument("query")
    q.add_argument("--depth", type=int, default=1)
    q.set_defaults(fn=cligraph.cmd_query)

    pa = sub.add_parser("path", help="shortest path between two graph nodes")
    pa.add_argument("a")
    pa.add_argument("b")
    pa.set_defaults(fn=cligraph.cmd_path)

    ex = sub.add_parser("explain", help="explain a graph node + its neighbors")
    ex.add_argument("term")
    ex.set_defaults(fn=cligraph.cmd_explain)

    sub.add_parser("report", help="write GRAPH_REPORT.md (god nodes + communities)").set_defaults(fn=cligraph.cmd_report)

    # Internal hook entrypoints (wired by `fux init`, not for direct use).
    sub.add_parser("hook-touch").set_defaults(fn=lambda a: hooks.post_tool_use())
    sub.add_parser("hook-check").set_defaults(fn=lambda a: hooks.stop())
    sub.add_parser("hook-recall").set_defaults(fn=lambda a: hooks.user_prompt_recall())
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
