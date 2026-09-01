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


def _cmd_enrich(args) -> int:
    from .enrich import cmd_enrich

    return cmd_enrich(args)


def _cmd_mcp(args) -> int:
    from .mcp import cmd_mcp

    return cmd_mcp(args)


def _cmd_hooks(args) -> int:
    from .maintain import cmd_hooks

    return cmd_hooks(args)


def _cmd_daemon(args) -> int:
    from .maintain import cmd_daemon

    return cmd_daemon(args)


def _cmd_verify(args) -> int:
    from .query import cmd_verify

    return cmd_verify(args)


def _cmd_explain(args) -> int:
    from .graph import cmd_explain

    return cmd_explain(args)


def _cmd_graph(args) -> int:
    from .graph import cmd_graph

    return cmd_graph(args)


def _cmd_path(args) -> int:
    from .graph import cmd_path

    return cmd_path(args)


def _cmd_tune(args) -> int:
    # **Prints, never writes** — ADR-TUNE decision 3b. `tomllib` reads and
    # nothing in the stdlib writes TOML, so a writer would mean either a
    # third-party dependency (L1) or fux round-tripping a commented file it
    # promised never to rewrite. The human pastes; the file stays theirs.
    from .tune import specimen

    print(specimen())
    return 0


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


def _top_help() -> str:
    """`--top`'s help, with the default read from `output_config.BUILT_IN`.

    Decision 6: **one source for every default.** A literal `5` repeated in
    `add_argument` is the drift this avoids — the help text and the resolver
    cannot disagree if only one of them holds the number.
    """
    from .output_config import BUILT_IN

    return f"max results (default {BUILT_IN['top']}; .fux/output.toml can change it)"


def _hops_help() -> str:
    from .output_config import BUILT_IN

    return f"max edges in a route (default {BUILT_IN['hops']}; .fux/output.toml can change it)"


def _apply_output_defaults(args) -> None:
    """Resolve every gated flag through `.fux/output.toml`, ONCE — ADR-OUTPUT.

    **Done here rather than at each consumer, deliberately.** Downstream code
    then reads a plain `bool`/`int` on `args` exactly as it did before this
    file existed, so the blast radius of a rendering config is this function
    and nothing else. `None` on the way in means *the flag was not passed*;
    nothing downstream ever sees a `None`.

    **Two passes, `json` first.** `json` (spelled `enabled` in the file)
    selects which chain every other key walks — `[cli.json.<verb>]` is only
    reachable once JSON rendering is already on — so it is resolved on its
    own before the loop below touches anything else.

    **`mcp` is not a `CLI_VERBS` verb at all** — its own root (`[mcp]`) has no
    CLI flags to gate, and is resolved once inside `cmd_mcp`/`serve()`
    instead. `keys is None` (not `not keys`) is the guard: `explain`,
    `doctor`, `hooks` and `daemon` legitimately declare an EMPTY key tuple —
    they still have `--json` to resolve — and only an absent entry means
    *this verb is not shaped by this file*.

    **Never raises for a missing repo.** `--help`, `--version` and a run from
    outside a fux repo must not be broken by a config file that may not
    exist. Since 2026-08-28 (Arpit) the file, once in effect, is the sole
    source of truth for every key it is asked for — a malformed file, or one
    that simply never set a key this verb needs, both raise, with the fix
    named in the message. `--no-output-config` (or no repo root) bypasses
    the file entirely rather than reading it and finding it wanting.
    """
    from .output_config import CLI_VERBS, load as load_output, DEFAULT_OUTPUT

    verb = getattr(args, "command", None)
    keys = CLI_VERBS.get(verb)
    if keys is None:
        return

    from .config import find_root

    no_output_config = getattr(args, "no_output_config", False)
    root = None if no_output_config else find_root()
    cfg = DEFAULT_OUTPUT if root is None else load_output(root, enabled=True)

    if hasattr(args, "json"):
        args.json = cfg.resolve_json(verb, args.json)
    as_json = bool(getattr(args, "json", False))

    for key in keys:
        if not hasattr(args, key):
            continue
        setattr(args, key, cfg.resolve(verb, key, getattr(args, key), as_json=as_json))


def _add_tune_flag(parser: argparse.ArgumentParser) -> None:
    """`--no-tune` on every verb that reads `.fux/tune.toml` (ADR-TUNE decision 11).

    A flag rather than a verb, per ADR-CLI veto 1 — and one flag rather than a
    knob per table, because the question it answers is *"is it me or the
    config?"*. Bisecting that with six flags is an experiment; with one it is a
    single re-run, which is the whole reason the tune file is one file.
    """
    parser.add_argument(
        "--no-tune",
        action="store_true",
        help="ignore .fux/tune.toml and use the engine defaults",
    )


def _cmd_output(args) -> int:
    from .output_config import specimen

    print(specimen(), end="")
    return 0


def _add_output_flags(parser: argparse.ArgumentParser, *, band: bool = False) -> None:
    """`--no-output-config`, and `--band` where the verb has a band.

    ⚠ **Every flag `.fux/output.toml` can default is declared `default=None`,
    not `default=False`** — ADR-OUTPUT decision 10. At `default=False` an
    absent flag and an explicit one are the same value, the file could never
    take effect, and **nothing would fail**: the loader would work, the tests
    would pass, and the feature would silently not exist.

    `--no-output-config` is per-verb rather than global for the same reason
    `--no-tune` is: a global flag has to precede the subcommand, and
    `fux --no-output-config ask "..."` is not the order anyone types.
    """
    parser.add_argument(
        "--no-output-config",
        action="store_true",
        help="ignore .fux/output.toml and use the engine defaults",
    )
    if band:
        parser.add_argument(
            "--band",
            action="store_true",
            default=None,
            help="emit the confidence block (ADR-CONFIDENCE); always on over MCP",
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
    p_doctor.add_argument("--json", action="store_true", default=None, help="machine-readable report")
    _add_output_flags(p_doctor)
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
        p.add_argument("--keep", action="store_true", help="URLs: record keep=true - retain the fetched bytes in .fux/acquired/ (the default)")
        p.add_argument("--no-keep", action="store_true", help="URLs: record keep=false - do not retain the fetched bytes")
        p.add_argument("--ttl", metavar="D", help="URLs: record ttl=D - how long a citation may go unchecked at ask time (0, 30s, 15m, 1h, 7d)")
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
    # W-82 ruling 3: narrow is the DEFAULT and this overrides it. There is
    # deliberately no `--dirty`/`--stale`/`--changed` -- if the dirty list is the
    # right thing to refresh, it should not have to be asked for.
    p_update.add_argument(
        "--all",
        action="store_true",
        help="fetch every listed URL, not just the ones known to be stale",
    )
    # ADR-URL-FRESHNESS. A flag on the existing networked verb, never a new
    # one: `fux retry` would be a second way to do what `update` already does,
    # and ADR-CLI decision 1 refuses that. The selector is url-state's own
    # `fail_streak > 0`, which is the number that file exists to report.
    p_update.add_argument(
        "--failed",
        action="store_true",
        help="fetch only the URLs whose last run failed (fail_streak > 0)",
    )
    _add_progress_flags(p_update)
    p_update.set_defaults(func=_cmd_update)

    def _query_parser(name: str, help_text: str):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("query", help="natural-language question")
        p.add_argument("--json", action="store_true", default=None, help="machine-readable output")
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
        _add_tune_flag(p)
        _add_output_flags(p, band=True)
        return p

    p_ask = _query_parser("ask", "answer a question from the committed index, with citations")
    p_ask.add_argument("--top", type=int, default=None, metavar="N", help=_top_help())
    p_ask.add_argument("--explain", action="store_true", default=None, help="report which path answered")
    # W-84's matched `§ heading` lines. ⚠ **A pair, not a `store_true`** — the
    # lines are ON by default, so a `store_true` could only ever turn them on
    # again and `.fux/output.toml` could never turn them off from the command
    # line. `default=None` on BOTH halves is ADR-OUTPUT decision 10: an absent
    # flag has to be distinguishable from an explicit one, or the file's value
    # is unreachable and nothing fails to say so.
    sections = p_ask.add_mutually_exclusive_group()
    sections.add_argument(
        "--sections", dest="sections", action="store_true", default=None,
        help="show the matched section headings under each hit (default)",
    )
    sections.add_argument(
        "--no-sections", dest="sections", action="store_false", default=None,
        help="omit the matched section headings, in text and in --json alike",
    )
    # ADR-PROVENANCE. A separate flag from `--explain`, not an extension of it:
    # `--explain` answers "which code path ran" and `--why` answers "why this
    # document" — different questions, different costs. `--why` runs a second
    # query when a tune file exists, and folding that cost into a flag people
    # already pass for latency debugging would be a surprise.
    p_ask.add_argument(
        "--why", action="store_true",
        help="how the ranking got here: matched terms, the cut line, rerank and tune deltas",
    )
    p_ask.set_defaults(func=_cmd_ask)

    p_find = _query_parser("find", "ranked document locations, one per line")
    p_find.add_argument("--top", type=int, default=None, metavar="N", help=_top_help())
    p_find.set_defaults(func=_cmd_find)

    p_answer = _query_parser(
        "answer", "the single best answer — a fetched, re-scored passage when the source is reachable"
    )
    p_answer.add_argument(
        "--no-refer",
        action="store_true",
        default=None,
        help="skip the refer plane; answer from the index's own structure alone",
    )
    # ADR-PROVENANCE. Three flags rather than one, because they are three
    # different asks and conflating them would make the strongest one
    # (`--journal`, which WRITES) reachable by accident.
    p_answer.add_argument(
        "--audit", action="store_true",
        help="emit the refer plane's own record: per-document freshness, both shas, budget spent",
    )
    p_answer.add_argument(
        "--receipt", action="store_true",
        help="emit a re-runnable receipt: index digest, tune digest, engine, cited shas",
    )
    p_answer.add_argument(
        "--journal", action="store_true", default=None,
        help="also append the receipt to .fux/runtime/ (local, gitignored, never committed)",
    )
    p_answer.set_defaults(func=_cmd_answer)

    # ADR-PROVENANCE. A verb, not a flag: it takes a FILE rather than a query,
    # so it does not belong on the query parser at all — every flag there
    # assumes a `query` positional this command has no use for.
    p_verify = sub.add_parser(
        "verify", help="re-run a receipt against this tree: reproduced | drifted | unverifiable"
    )
    p_verify.add_argument("receipt", help="path to a receipt written by `fux answer --receipt`")
    p_verify.add_argument("--json", action="store_true", help="machine-readable verdict")
    p_verify.add_argument(
        "--rerun", action="store_true",
        help="re-answer the question too; without it only the INPUTS are checked",
    )
    p_verify.set_defaults(func=_cmd_verify)

    # W-76 Phase 8. **No `--model` flag, and that is the design**: fux never
    # calls a model, so there is no networked path to fence. Generation is the
    # `fux-enrich` agent skill; these two flags are the deterministic halves.
    p_enrich = sub.add_parser(
        "enrich", help="plan and validate the enrichment an agent skill generates"
    )
    enrich_mode = p_enrich.add_mutually_exclusive_group()
    enrich_mode.add_argument(
        "--plan", action="store_true", help="print the worklist (the default)"
    )
    enrich_mode.add_argument(
        "--check", action="store_true", help="validate what exists and report coverage"
    )
    p_enrich.set_defaults(func=_cmd_enrich)

    # W-76 Phase 5. A verb rather than a flag on `ask`: it is a long-running
    # server, not a query, and ADR-CLI's four groups gain a fifth consumer-facing
    # one rather than overloading the read verbs.
    p_mcp = sub.add_parser(
        "mcp", help="serve the index over MCP on stdio, for coding agents"
    )
    # ADR-OUTPUT decision 15: on EVERY verb that reads .fux/output.toml,
    # `mcp` included — read directly in `cmd_mcp` rather than folded into
    # `_apply_output_defaults`, because `mcp` carries no `CLI_VERBS` keys of
    # its own (its only knob, `[mcp] top`, is not a CLI flag at all).
    p_mcp.add_argument(
        "--no-output-config",
        action="store_true",
        help="ignore .fux/output.toml and use the engine defaults",
    )
    p_mcp.set_defaults(func=_cmd_mcp)

    p_hooks = sub.add_parser("hooks", help="install the git hooks and the index merge driver")
    p_hooks.add_argument("--install", action="store_true", help="write them (the default)")
    p_hooks.add_argument("--status", action="store_true", help="report what is wired")
    p_hooks.add_argument("--uninstall", action="store_true", help="remove only what fux wrote")
    p_hooks.add_argument("--json", action="store_true", default=None, help="machine-readable status")
    _add_output_flags(p_hooks)
    p_hooks.set_defaults(func=_cmd_hooks)

    # W-82 ruling 10 (Arpit, 2026-08-27). A verb, like `mcp`, for the same
    # reason: it is a long-running process rather than a query, and flat rather
    # than a subcommand tree because "no subcommand tree" is ADR-CLI's
    # constraint. `start`/`stop`/`status` are POSITIONAL, not flags, because
    # they are mutually exclusive states and `fux daemon --start --stop` should
    # not parse.
    p_daemon = sub.add_parser(
        "daemon", help="run the URL freshness clock in the background (start | stop | status)"
    )
    p_daemon.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=("start", "stop", "status"),
        help="omit for status",
    )
    p_daemon.add_argument("--json", action="store_true", default=None, help="machine-readable status")
    # The child's own entry point. Hidden: nobody types this, and a documented
    # flag that runs the loop in the foreground would invite someone to wire it
    # into a supervisor, which is the global install this verb exists to avoid.
    p_daemon.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    _add_output_flags(p_daemon)
    p_daemon.set_defaults(func=_cmd_daemon)

    # The graph group. Flat, like every other verb — `fux graph path` would be
    # the first subcommand tree on this surface, and "no subcommand tree" is
    # the constraint ADR-CLI keeps.
    p_explain = sub.add_parser("explain", help="one document's outbound edges and its community")
    p_explain.add_argument("doc", help="a doc id or the loc `find` printed")
    p_explain.add_argument("--json", action="store_true", default=None, help="machine-readable output")
    _add_output_flags(p_explain)
    p_explain.set_defaults(func=_cmd_explain)

    p_graph = sub.add_parser("graph", help="the neighbourhood around a query's best answers")
    p_graph.add_argument("query", help="natural-language question")
    p_graph.add_argument("--json", action="store_true", default=None, help="machine-readable output")
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
    _add_tune_flag(p_graph)
    _add_output_flags(p_graph)
    p_graph.set_defaults(func=_cmd_graph)

    p_path = sub.add_parser("path", help="how two documents are connected, most reliable route first")
    p_path.add_argument("src", metavar="FROM", help="the document the route starts at")
    p_path.add_argument("dst", metavar="TO", help="the document the route ends at")
    p_path.add_argument("--hops", type=int, default=None, metavar="N", help=_hops_help())
    p_path.add_argument("--json", action="store_true", default=None, help="machine-readable output")
    _add_tune_flag(p_path)
    _add_output_flags(p_path)
    p_path.set_defaults(func=_cmd_path)

    # A flat verb with no arguments at all: it neither reads the repo nor
    # writes it, so it works before `fux setup` has run and outside a root.
    # Printing is the whole feature — see `_cmd_tune`.
    p_tune = sub.add_parser(
        "tune", help="print the tunables file for you to paste into .fux/tune.toml"
    )
    p_tune.set_defaults(func=_cmd_tune)

    # ADR-OUTPUT: prints, never writes. `tomllib` reads and the stdlib does not
    # write TOML, and a writer would mean fux editing a file it promised was
    # yours — the same refusal `fux tune` makes.
    p_output = sub.add_parser(
        "output", help="print the output-defaults file for you to paste into .fux/output.toml"
    )
    p_output.set_defaults(func=_cmd_output)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    # ADR-OUTPUT decision 3. Before dispatch and before the progress plane, so
    # every `args` a command sees is already resolved.
    try:
        _apply_output_defaults(args)
    except FuxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
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
