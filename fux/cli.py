"""`fux` CLI — argparse dispatch over the deterministic command surface (plan §9).

Top-level `--help` and per-command help are rendered from the single command
registry (``fux/registry.py``) via ``clihelp`` — the same table that powers
``fux how`` and the generated ``docs/cli.md``, so help can never drift (plan §20).
"""
from __future__ import annotations

import argparse

from fux import __version__, clicmds, cliconstitution, cligraph, clihelp, cliquery, hooks, registry


class _GroupedHelp(argparse.ArgumentParser):
    """Top-level parser whose `--help`/usage prints the registry-grouped view."""

    def format_help(self) -> str:        # noqa: D401 — argparse override
        return clihelp.grouped_help() + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = _GroupedHelp(prog="fux", description="Fux knowledge engine ($0, deterministic).")
    p.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    hp = sub.add_parser("help", help="show grouped help, or detail for one command")
    hp.add_argument("topic", nargs="?", help="a command name (omit for the grouped list)")
    hp.set_defaults(fn=cmd_help)

    init = sub.add_parser("init", help="scaffold .fux/ + wire hooks in this project")
    init.add_argument("--recall", action="store_true", help="also wire the UserPromptSubmit recall hook")
    init.set_defaults(fn=clicmds.cmd_init)

    bld = sub.add_parser("build", help="regenerate INDEX + rules.json + graph ($0)")
    bld.add_argument("--full", action="store_true", help="graph every non-ignored file (whole-repo)")
    bld.add_argument("--profile", action="store_true", help="print a per-phase build timing breakdown")
    bld.add_argument("--no-xref", action="store_true",
                     help="skip the loose references pass (opt-in mode; drops INFERRED edges)")
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
    rc.add_argument("--self", action="store_true", help="query fux's own bundled rules instead of the project")
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
    rt.add_argument("--no-pr", action="store_true",
                    help="ratify in place without opening a branch+PR (local/offline; by default a "
                         "ratification on the protected branch is routed through a new branch + gated PR)")
    rt.set_defaults(fn=cliconstitution.cmd_ratify)

    cd = sub.add_parser("capture-decision",
                        help="capture a concluded debate/council as a routed, tamper-evident ADR (no LLM)")
    cd.add_argument("id")
    cd.add_argument("--route", choices=["fux", "anton", "elgar"], required=True,
                    help="store by content: world/code→fux, app→anton, money→elgar (link-only)")
    cd.add_argument("--method", choices=["debate", "decision-council"], default="debate")
    cd.add_argument("--by", help="named human decider (default: git user.name)")
    cd.add_argument("--date", help="ISO decision date (default: today)")
    cd.add_argument("--from", dest="from_file", metavar="FILE",
                    help="JSON verdict: {title, decision, why, crux, strongest_dissent, what_would_reverse}")
    cd.add_argument("--debate", metavar="FILE",
                    help="debate transcript to hash into ratification.debate_hash")
    cd.add_argument("--yes", action="store_true",
                    help="confirm a MONEY/elgar route (mandatory; fux stores only the elgar:// link)")
    cd.set_defaults(fn=cliconstitution.cmd_capture_decision)

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

    pr = sub.add_parser("propose-rules",
                        help="propose draft rules → .fux/CANDIDATES.md (forward skill / --retro $0)")
    pr.add_argument("--retro", action="store_true",
                    help="$0 retro pass: fux mine + git-history why-extraction (capped, deduped)")
    pr.add_argument("--from", dest="from_file", metavar="FILE",
                    help="file the agent's drafted candidates (JSON list; '-' = stdin)")
    pr.set_defaults(fn=cliquery.cmd_propose_rules)

    cn = sub.add_parser("candidates", help="review/triage the candidate rules surface (.fux/CANDIDATES.md)")
    cn.add_argument("action", nargs="?", choices=["accept", "reject"],
                    help="accept → active rule (human ratify); reject → drop (not re-proposed)")
    cn.add_argument("id", nargs="?", help="candidate id (for accept/reject)")
    cn.add_argument("--pending", action="store_true", help="show only pending candidates")
    cn.add_argument("--why-todo", dest="why_todo", action="store_true",
                    help="show only candidates flagged why: TODO")
    cn.set_defaults(fn=cliquery.cmd_candidates)

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

    q = sub.add_parser("query", help="traverse the graph from rules matching a question")
    q.add_argument("query")
    q.add_argument("--depth", type=int, default=1)
    q.add_argument("--budget", type=int, default=1200,
                   help="approx token cap on output (keeps Claude's context cost bounded)")
    q.add_argument("--self", action="store_true", help="traverse fux's own architecture (the bundled self graph)")
    q.set_defaults(fn=cligraph.cmd_query)

    pa = sub.add_parser("path", help="shortest path between two graph nodes")
    pa.add_argument("a")
    pa.add_argument("b")
    pa.add_argument("--self", action="store_true", help="traverse fux's own architecture (the bundled self graph)")
    pa.set_defaults(fn=cligraph.cmd_path)

    ex = sub.add_parser("explain", help="explain a graph node + its neighbors")
    ex.add_argument("term")
    ex.add_argument("--self", action="store_true", help="explain a node in fux's own architecture (the bundled self graph)")
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

    sub.add_parser("self-build", help="regenerate fux's self-knowledge bundle from its own source ($0, AST-only)").set_defaults(fn=clicmds.cmd_self_build)

    ps = sub.add_parser("pii-scan", help="scan non-plan .py/.md for hard PII identifiers (PAN/Aadhaar/account); exit 2 blocks the gate")
    ps.add_argument("paths", nargs="*", help="files to scan (default: all git-tracked .py + .md)")
    ps.set_defaults(fn=clicmds.cmd_pii_scan)

    fr = sub.add_parser("fetch-rules", help="fetch plain text from a URL / file / PDF for rule extraction")
    fr.add_argument("source", help="http(s):// URL, local .txt/.md, or .pdf path")
    fr.add_argument("--raw", action="store_true", help="omit the header line (pure text output)")
    fr.set_defaults(fn=cliquery.cmd_fetch_rules)

    ho = sub.add_parser("how", help="fux explains fux: a question → the exact command ($0)")
    ho.add_argument("question", help="what you're trying to do, in plain words")
    ho.add_argument("--top", type=int, default=3, help="how many candidate commands to show")
    ho.add_argument("--explain", action="store_true",
                    help="emit a host-agent prompt for a richer NL answer (opt-in; not on the $0 path)")
    ho.set_defaults(fn=cliquery.cmd_how)

    for name, fn in (("ingest", cliquery.cmd_ingest),
                     ("scrape", cliquery.cmd_scrape_deprecated)):
        # `scrape` is a deprecated alias for `ingest` (one release after the rename).
        h = ("agent-driven batch URL/PDF/Excel/Word/TXT/image/JSON/YAML/Swagger → "
             "draft rules (skill); --recheck re-verifies a source") if name == "ingest" \
            else "deprecated alias for 'ingest' — use 'ingest' instead"
        ig = sub.add_parser(name, help=h)
        ig.add_argument("targets", nargs="*",
                        help="URLs/files/globs to ingest (skill) or one rule id to --recheck")
        ig.add_argument("--recheck", action="store_true",
                        help="re-read a rule's source + flag source-drift (opt-in; needs the [scrape] extra)")
        ig.add_argument("--queue", action="store_true",
                        help="show the draft review queue (.fux/ingest/queue.md) and exit")
        ig.add_argument("--follow-links", action="store_true",
                        help="opt-in: discover the documents an HTML page links (depth-1, bounded)")
        ig.add_argument("--cross-origin", action="store_true",
                        help="with --follow-links, allow off-origin document links (default same-origin)")
        ig.add_argument("--max", type=int, default=20, dest="max",
                        help="with --follow-links, cap on discovered documents (default 20)")
        ig.add_argument("--yes", action="store_true",
                        help="with --follow-links, take all discovered docs up to --max (skip confirm)")
        ig.add_argument("--full", action="store_true",
                        help="bypass reduce-before-draft; feed the whole extract (high-stakes regulatory)")
        ig.add_argument("--connector", choices=["github", "jira", "confluence"],
                        help="ingest from a connector (agent pulls via MCP/API; --query is mandatory)")
        ig.add_argument("--query", help="server-side filter for --connector (JQL / GitHub query / space); refuses 'everything'")
        ig.add_argument("--since", help="with --connector, only items changed since this cursor/date (delta ingest)")
        ig.add_argument("--cdp-port", type=int, help="CDP port for the ingest skill's render escalation")
        ig.add_argument("--cdp-host", help="CDP host for the ingest skill's render escalation")
        ig.set_defaults(fn=fn)

    # Internal hook entrypoints (wired by `fux init`, not for direct use).
    sub.add_parser("hook-touch").set_defaults(fn=lambda a: hooks.post_tool_use())
    sub.add_parser("hook-check").set_defaults(fn=lambda a: hooks.stop())
    sub.add_parser("hook-recall").set_defaults(fn=lambda a: hooks.user_prompt_recall())
    sub.add_parser("hook-propose").set_defaults(fn=lambda a: hooks.session_end_propose())

    # `fux <cmd> --help` shows the registry detail (desc + usage + example + related).
    for name, parser in sub.choices.items():
        if registry.get(name) is not None:
            parser.format_help = (lambda n: lambda: clihelp.command_help(n) + "\n")(name)
    return p


def cmd_help(args) -> int:
    if getattr(args, "topic", None):
        print(clihelp.command_help(args.topic), end="")
    else:
        print(clihelp.grouped_help())
    return 0


def main(argv: list[str] | None = None) -> int:
    """Top-level dispatch + the CLI's single error boundary (plan §error contract).

    Exit codes: 0 ok · 1 error (FuxError / unexpected) · 2 blocking (strict gate/
    stop, returned by the command) · 130 interrupted. A raw traceback is shown only
    under `FUX_DEBUG=1`; expected failures raise `FuxError` and render terse.
    """
    import os
    import sys
    import traceback

    from fux.errors import FuxError

    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        print("\naborted.", file=sys.stderr)
        return 130
    except FuxError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 — top-level CLI guard: render, don't dump a traceback
        if os.environ.get("FUX_DEBUG") == "1":
            traceback.print_exc()
        else:
            print(f"error: {e}\n(re-run with FUX_DEBUG=1 for the full traceback)", file=sys.stderr)
        return 1
