"""`fux` CLI — argparse dispatch over the deterministic command surface (plan §9)."""
from __future__ import annotations

import argparse

from fux import __version__, clicmds, cliconstitution, cligraph, cliquery, hooks


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fux", description="Fux knowledge engine ($0, deterministic).")
    p.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="scaffold .fux/ + wire hooks in this project")
    init.add_argument("--recall", action="store_true", help="also wire the UserPromptSubmit recall hook")
    init.set_defaults(fn=clicmds.cmd_init)

    bld = sub.add_parser("build", help="regenerate INDEX + rules.json + graph ($0)")
    bld.add_argument("--full", action="store_true", help="graph every non-ignored file (whole-repo)")
    bld.set_defaults(fn=clicmds.cmd_build)
    chk = sub.add_parser("check", help="validate schema/refs/staleness/conflicts")
    chk.add_argument("--fix", action="store_true", help="apply mechanical $0 repairs")
    chk.add_argument("--baseline-write", metavar="FILE",
                     help="snapshot current findings for the §5b migration gate (then exit)")
    chk.set_defaults(fn=clicmds.cmd_check)

    sub.add_parser("context", help="emit the compact INDEX (SessionStart hook)").set_defaults(fn=clicmds.cmd_context)

    rc = sub.add_parser("recall", help="keyword-retrieve relevant rules")
    rc.add_argument("query")
    rc.add_argument("--top", type=int, default=6)
    rc.add_argument("--hybrid", action="store_true", help="RRF-fuse lexical + semantic + graph ($0)")
    rc.add_argument("--expand", action="store_true", help="expand query w/ glossary + graph neighbours ($0)")
    rc.set_defaults(fn=cliquery.cmd_recall)

    why = sub.add_parser("why", help="explain a rule + rationale + linked code")
    why.add_argument("id")
    why.add_argument("--history", action="store_true",
                     help="show how this rule's reasoning evolved (git, $0)")
    why.set_defaults(fn=cliquery.cmd_why)

    sl = sub.add_parser("seal", help="bind rules to an AST fingerprint of their code")
    sl.add_argument("ids", nargs="*", help="rule ids to (re)seal; omit with --all")
    sl.add_argument("--all", action="store_true", help="seal every rule with resolvable code")
    sl.set_defaults(fn=cliquery.cmd_seal)

    rt = sub.add_parser("ratify", help="ratify a constitutional rule (stamp + seal + lock; no LLM)")
    rt.add_argument("id")
    rt.add_argument("--by", help="named human ratifier (default: git user.name)")
    rt.add_argument("--date", help="ISO ratification date (default: today)")
    rt.add_argument("--debate", metavar="FILE",
                    help="debate transcript (from /fux debate) to hash into ratification.debate_hash")
    rt.set_defaults(fn=cliconstitution.cmd_ratify)

    sub.add_parser("constitution",
                   help="status view: what's constitutional, what each governs, current violations"
                   ).set_defaults(fn=cliconstitution.cmd_constitution)

    cr = sub.add_parser("critic", help="critique a proposed change against principles (deterministic pass first; $0)")
    cr.add_argument("proposal", help="the proposed change / commit message / diff summary to critique")
    cr.set_defaults(fn=cliconstitution.cmd_critic)

    refs = sub.add_parser("refs", help="reverse lookup: which rules govern this file")
    refs.add_argument("file")
    refs.set_defaults(fn=cliquery.cmd_refs)

    new = sub.add_parser("new", help="scaffold a rule from a template")
    new.add_argument("type")
    new.add_argument("id")
    new.add_argument("--domain", default="general")
    new.set_defaults(fn=cliquery.cmd_new)

    sub.add_parser("coverage", help="%% of important files with a governing rule").set_defaults(fn=cliquery.cmd_coverage)
    vf = sub.add_parser("verify", help="run invariant/example checks")
    vf.add_argument("--fuzz", action="store_true", help="boundary-fuzz examples for unguarded div-by-zero")
    vf.set_defaults(fn=cliquery.cmd_verify)
    sub.add_parser("tour", help="emit an ordered ONBOARDING.md").set_defaults(fn=cliquery.cmd_tour)

    sv = sub.add_parser("savings", help="estimate the token + dollar cost win of Fux ($0)")
    sv.add_argument("query", nargs="?", help="optional: cost a specific lookup")
    sv.add_argument("--top", type=int, default=3)
    sv.add_argument("--reset", action="store_true", help="clear the cumulative cost ledger")
    sv.set_defaults(fn=cliquery.cmd_savings)

    lt = sub.add_parser("lint", help="rule-quality checks (why/code_refs/edges/provenance)")
    lt.add_argument("--strict", action="store_true", help="exit 1 if any finding")
    lt.set_defaults(fn=cliquery.cmd_lint)

    sub.add_parser("stats", help="project knowledge-health dashboard + score").set_defaults(fn=cliquery.cmd_stats)

    mn = sub.add_parser("mine", help="surface candidate rules latent in the code (drafts)")
    mn.add_argument("--min-sites", type=int, default=3, help="min repeats to flag a magic number")
    mn.set_defaults(fn=cliquery.cmd_mine)

    cap = sub.add_parser("capture", help="session observation queue for `fux distill`")
    cap.add_argument("--list", action="store_true", help="show the pending queue without observing")
    cap.add_argument("--clear", action="store_true", help="empty the queue (after distilling)")
    cap.set_defaults(fn=cliquery.cmd_capture)

    gt = sub.add_parser("gate", help="CI / pre-commit enforcement (exit 2 on blocking)")
    gt.add_argument("--install", action="store_true", help="install a git pre-commit hook")
    gt.add_argument("--strict-lint", action="store_true", help="treat lint findings as blocking")
    gt.add_argument("--baseline", metavar="FILE",
                    help="§5b migration gate: fail only on findings new since this snapshot")
    gt.set_defaults(fn=clicmds.cmd_gate)

    sub.add_parser("mcp", help="serve the substrate over MCP (stdio JSON-RPC)").set_defaults(fn=clicmds.cmd_mcp)

    srv = sub.add_parser("serve", help="local dashboard over the generated views ($0)")
    srv.add_argument("--port", type=int, default=8765)
    srv.set_defaults(fn=clicmds.cmd_serve)

    imp = sub.add_parser("import", help="import existing markdown as narrative entries")
    imp.add_argument("paths", nargs="+", help="files or directories of .md to import")
    imp.add_argument("--type", default="narrative", help="entry type (default: narrative)")
    imp.add_argument("--domain", default="general")
    imp.add_argument("--force", action="store_true", help="overwrite existing entries")
    imp.set_defaults(fn=clicmds.cmd_import)

    impm = sub.add_parser("import-memory", help="import Claude's home-dir memory into .fux/memory")
    impm.add_argument("--scope", choices=["shared", "personal"], default="shared")
    impm.add_argument("--force", action="store_true")
    impm.set_defaults(fn=clicmds.cmd_import_memory)

    sub.add_parser("parity", help="decommission readiness vs graphify-out/docs/memory").set_defaults(fn=cliquery.cmd_parity)

    q = sub.add_parser("query", help="traverse the graph from rules matching a question")
    q.add_argument("query")
    q.add_argument("--depth", type=int, default=1)
    q.add_argument("--budget", type=int, default=1200,
                   help="approx token cap on output (keeps Claude's context cost bounded)")
    q.set_defaults(fn=cligraph.cmd_query)

    pa = sub.add_parser("path", help="shortest path between two graph nodes")
    pa.add_argument("a")
    pa.add_argument("b")
    pa.set_defaults(fn=cligraph.cmd_path)

    ex = sub.add_parser("explain", help="explain a graph node + its neighbors")
    ex.add_argument("term")
    ex.set_defaults(fn=cligraph.cmd_explain)

    imp2 = sub.add_parser("impact", help="downstream blast radius of changing a file ($0)")
    imp2.add_argument("file")
    imp2.set_defaults(fn=cligraph.cmd_impact)

    cmp = sub.add_parser("components", help="design-system registry + data-binding catalog ($0)")
    cmp.add_argument("--kind", choices=["all", "components", "hooks", "dtos"], default="all")
    cmp.add_argument("--scope", help="restrict to files under this path prefix")
    cmp.add_argument("--json", action="store_true", help="machine-readable output (for Orff)")
    cmp.set_defaults(fn=cligraph.cmd_components)

    vs = sub.add_parser("validate-spec", help="validate a generated UISpec against the registry ($0)")
    vs.add_argument("file")
    vs.add_argument("--json", action="store_true", help="emit {ok, errors} as JSON")
    vs.set_defaults(fn=cligraph.cmd_validate_spec)

    fb = sub.add_parser("feedback", help="record/summarise on-the-fly generation outcomes ($0)")
    fb.add_argument("--record", metavar="FILE", help="append one outcome from JSON ('-' = stdin)")
    fb.set_defaults(fn=cliquery.cmd_feedback)

    sub.add_parser("report", help="write GRAPH_REPORT.md (god nodes + communities)").set_defaults(fn=cligraph.cmd_report)

    hk = sub.add_parser("hooks", help="install/uninstall/status Fux hooks across git + agents")
    hk.add_argument("action", choices=["install", "uninstall", "status"], nargs="?",
                    default="install", help="default: install")
    hk.add_argument("--all", action="store_true", help="all surfaces (the default)")
    for _s in ("git", "claude", "codex", "copilot"):
        hk.add_argument(f"--{_s}", action="store_true", help=f"only the {_s} surface")
    hk.add_argument("--recall", action="store_true", help="also wire the UserPromptSubmit recall hook")
    hk.set_defaults(fn=clicmds.cmd_hooks)

    sub.add_parser("setup", help="copy bundled assets (schema, hooks, skills) to ~/.claude/fux/").set_defaults(fn=clicmds.cmd_setup)

    fr = sub.add_parser("fetch-rules", help="fetch plain text from a URL / file / PDF for rule extraction")
    fr.add_argument("source", help="http(s):// URL, local .txt/.md, or .pdf path")
    fr.add_argument("--raw", action="store_true", help="omit the header line (pure text output)")
    fr.set_defaults(fn=cliquery.cmd_fetch_rules)

    # Internal hook entrypoints (wired by `fux init`, not for direct use).
    sub.add_parser("hook-touch").set_defaults(fn=lambda a: hooks.post_tool_use())
    sub.add_parser("hook-check").set_defaults(fn=lambda a: hooks.stop())
    sub.add_parser("hook-recall").set_defaults(fn=lambda a: hooks.user_prompt_recall())
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
