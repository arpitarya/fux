"""Fux command-line entry point.

This is a boundary: it is the *only* place (besides hook entrypoints) that
catches and renders `FuxError`. Internals raise; `main` translates to an exit
code (0 ok · 1 error · 2 blocking · 130 interrupted). Handlers import their
modules lazily so `fux --version` stays instant.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import timedelta
from pathlib import Path

from . import __version__
from .constants import fixed
from .errors import FuxError
from .stdio import stdio_utf8 as _stdio_utf8


#: **Which module runs each verb, and which layer that module ships in** (W-282).
#: `cli.py` is core — it ships with every install — so it imports no verb
#: module by name: a verb runs through this table, and a verb whose layer is not
#: installed is left out of the parser and refused by name (`fux ingest` on a
#: reader-only install names fux-writer). `doctor` has a candidate per layer:
#: the engine's runs every row, a role package's runs its own and core's.
#: `tests/test_package_layers.py` holds every row to the layer map. `tune` and
#: `output` are core and run inline below.
VERBS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "setup": (('writer', 'fux.setup', 'cmd_setup'),),
    "doctor": (('engine', 'fux.doctor', 'cmd_doctor'), ('reader', 'fux.query.health', 'cmd_doctor'), ('writer', 'fux.ingest.health', 'cmd_doctor'),),
    "identifiers": (('engine', 'fux.identifiers_cmd', 'cmd_identifiers'),),
    "inspect": (('engine', 'fux.inspect', 'cmd_inspect'),),
    "register": (('writer', 'fux.ingest.register', 'cmd_register'),),
    "ingest": (('writer', 'fux.ingest', 'cmd_ingest'),),
    "ask": (('reader', 'fux.query', 'cmd_ask'),),
    "lexical": (('reader', 'fux.query', 'cmd_lexical'),),
    "find": (('reader', 'fux.query.find', 'cmd_find'),),
    "answer": (('reader', 'fux.query', 'cmd_answer'),),
    "add": (('writer', 'fux.sources', 'cmd_add'),),
    "remove": (('writer', 'fux.sources', 'cmd_remove'),),
    "build": (('reader', 'fux.derive', 'cmd_build'),),
    "correct": (('writer', 'fux.correct', 'cmd_correct'),),
    "enrich": (('writer', 'fux.enrich', 'cmd_enrich'),),
    "serve": (('engine', 'fux.serve', 'cmd_serve'),),
    "mcp": (('reader', 'fux.mcp', 'cmd_mcp'),),
    "lsp": (('reader', 'fux.lsp', 'cmd_lsp'),),
    "llms": (('reader', 'fux.llms', 'cmd_llms'),),
    "hooks": (('writer', 'fux.maintain', 'cmd_hooks'),),
    "daemon": (('writer', 'fux.maintain', 'cmd_daemon'),),
    "verify": (('reader', 'fux.query', 'cmd_verify'),),
    "explain": (('reader', 'fux.graph', 'cmd_explain'),),
    "graph": (('reader', 'fux.graph', 'cmd_graph'),),
    "path": (('reader', 'fux.graph', 'cmd_path'),),
}

def _installed(module: str) -> bool:
    """Is this module on this install? A spec lookup — nothing is imported."""
    from importlib.util import find_spec

    try:
        return find_spec(module) is not None
    except ModuleNotFoundError:  # its package is not installed at all
        return False


def available(verb: str) -> bool:
    """Can this install run `verb`? Core verbs always can."""
    return verb not in VERBS or any(_installed(module) for _layer, module, _fn in VERBS[verb])


def _refusal(verb: str) -> FuxError:
    # The distribution each layer ships in — what the refusal tells you to install.
    owners = sorted({fixed("distributions", layer) for layer, _m, _f in VERBS[verb]})
    return FuxError(
        f"`fux {verb}` is {' or '.join(owners)}'s, which is not installed here — "
        f"install {fixed('distributions', 'engine')} (everything) or {' or '.join(owners)}"
    )


def _run_verb(verb: str, args) -> int:
    from importlib import import_module

    for _layer, module, function in VERBS[verb]:
        if _installed(module):
            return getattr(import_module(module), function)(args)
    raise _refusal(verb)


def _dispatch(args) -> int:
    """Every table verb's handler: run `args.command` from the module `VERBS` names."""
    return _run_verb(args.command, args)


def _cmd_tune(args) -> int:
    # **Prints, never writes** — SR-TUNE decision 3b. `tomllib` reads and
    # nothing in the stdlib writes TOML, so a writer would mean either a
    # third-party dependency (L2) or fux round-tripping a commented file it
    # promised never to rewrite. The human pastes; the file stays theirs.
    from .tune import specimen

    print(specimen())
    return 0


#: The write verbs — the only ones that construct a `Progress` in `main`
#: (W-64). `add`/`remove` joined it in W-63: they end in `ingest.run()`, so
#: they inherit the bar from that seam rather than growing one of their own.
#: ⚠ **`update` was here until W-177 deleted the verb**; its row is not
#: missing, it is `ingest`'s now.
#: `inspect` joins these because its retrieval half is one full query per
#: sampled document and its dictionary half re-tokenises the whole corpus —
#: both are long enough that silence reads as a hang.
#: `identifiers`, `doctor` and `enrich` joined in W-238 (2026-09-29), each
#: MEASURED silent long enough to notice at `rung-10000` and on this repo:
#: `identifiers` and `doctor` both re-read every document to detect identifier
#: families (13 s and 14 s here), and `enrich --check` ranks one query per
#: enrichment question (105 s for 300 files). The read verbs measured under
#: 0.7 s there, and a bar that flashes is noise — they get none.
_PROGRESS_COMMANDS = ("ingest", "build", "add", "remove", "inspect", "identifiers", "doctor", "enrich")


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
    """`--top`'s help, naming the value the template ships.

    Decision 6: **one source for every value.** The number is read from the
    packaged `output.toml` template — the file `fux setup` writes — so the help
    text and the resolver cannot disagree (L12).
    """
    from .output_config import template

    return f"max results ({template().resolve('ask', 'top', as_json=False)} as shipped; .fux/output.toml sets it)"


def _hops_help() -> str:
    from .output_config import template

    return f"max edges in a route ({template().resolve('path', 'hops', as_json=False)} as shipped; .fux/output.toml sets it)"


def _apply_output_defaults(args) -> None:
    """Resolve every gated flag through `.fux/output.toml`, ONCE — SR-OUTPUT.

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
    outside a fux repo read the packaged template, as `--no-output-config`
    does. In a repo the file is the sole source of truth for every key a verb
    resolves (L12): a missing file, a malformed one, or one that never set a
    key this verb needs all raise, with `fux doctor --fix` named as the fix.

    **Every key the verb declares is resolved, flag or not.** A key with no
    flag (`max_headings`, `progress_threshold`, `candidates`, ...) still lands
    on `args`, so downstream code reads one plain value and never a default.
    """
    from .output_config import CLI_VERBS, load as load_output

    verb = getattr(args, "command", None)
    keys = CLI_VERBS.get(verb)
    if keys is None:
        return

    from .config import find_root

    no_output_config = getattr(args, "no_output_config", False)
    root = None if no_output_config else find_root()
    try:
        cfg = load_output(root, enabled=not no_output_config)
    except FuxError:
        if verb != "doctor":
            raise
        # 🔴 **`doctor` is the one verb that may not refuse to start because
        # this file is missing or broken** (SR-OUTPUT decision 20's surviving
        # half): it is the verb that REPORTS that fault, as an error row, and
        # `doctor --fix` is the one that writes the file back. It renders from
        # the template meanwhile — every other verb still refuses.
        from .output_config import template

        cfg = template()

    def resolved(resolve):
        """One key through `cfg` — and, for `doctor` alone, through the template
        when the file loaded but never set it (SR-OUTPUT decision 20b, W-241):
        `--fix` is what writes that key, so the verb may not need it to start."""
        try:
            return resolve(cfg)
        except FuxError:
            if verb != "doctor":
                raise
            from .output_config import template

            return resolve(template())

    if hasattr(args, "json"):
        # ⚠ **A rendering default may never change WHAT a command does**, and
        # on one verb it did (W-140 row 10, 2026-09-11). `fux hooks` selected
        # report-instead-of-install from `args.json`, so a repo with
        # `[cli.json] enabled = true` had a `fux hooks` that installed nothing
        # and said so in JSON — a true report of a state nobody had changed.
        # The flag as TYPED is kept here, before the file fills it, so a verb
        # that must distinguish *the user asked for JSON* from *this repo
        # renders JSON* can. Nothing else needs it, and nothing else should:
        # this docstring's own promise is that a rendering config's blast
        # radius is this function.
        args.json_explicit = args.json is True
        args.json = resolved(lambda c: c.resolve_json(verb, args.json))
    as_json = bool(getattr(args, "json", False))

    for key in keys:
        value = getattr(args, key, None)
        setattr(args, key, resolved(lambda c: c.resolve(verb, key, value, as_json=as_json)))


def _add_tune_flag(parser: argparse.ArgumentParser) -> None:
    """`--no-tune` on every verb that reads `.fux/tune.toml` (SR-TUNE decision 11).

    A flag rather than a verb, per SR-CLI veto 1 — and one flag rather than a
    knob per table, because the question it answers is *"is it me or the
    config?"*. Bisecting that with six flags is an experiment; with one it is a
    single re-run, which is the whole reason the tune file is one file.
    """
    parser.add_argument(
        "--no-tune",
        action="store_true",
        help="ignore .fux/tune.toml and use the template `fux setup` writes",
    )


def _cmd_output(args) -> int:
    from .output_config import specimen

    print(specimen(), end="")
    return 0


def _add_output_flags(parser: argparse.ArgumentParser, *, band: bool) -> None:
    """`--no-output-config`, and `--band` where the verb has a band.

    ⚠ **Every flag `.fux/output.toml` can default is declared `default=None`,
    not `default=False`** — SR-OUTPUT decision 10. At `default=False` an
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
        help="ignore .fux/output.toml and use the template `fux setup` writes",
    )
    if band:
        parser.add_argument(
            "--band",
            action="store_true",
            default=None,
            help="emit the confidence block (SR-CONFIDENCE); always on over MCP",
        )


def _verb_adder(sub):
    """`sub.add_parser`, except a verb this install cannot run is built on a
    parser nothing reaches — so it is absent from `--help` and from the choice
    list, and `main` refuses it by name instead of argparse calling it unknown."""

    def add(name: str, **kwargs) -> argparse.ArgumentParser:
        if available(name):
            return sub.add_parser(name, **kwargs)
        return argparse.ArgumentParser(prog=f"fux {name}", add_help=False)

    return add


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fux", description="rank, fetch, verify — an index over the systems that own your docs")
    parser.add_argument("--version", action="version", version=f"fux {__version__}")
    sub = parser.add_subparsers(dest="command")
    _verb = _verb_adder(sub)

    p_setup = _verb(
        "setup", help="write the consumer-owned files into .fux/ (write-if-missing)"
    )
    # W-68 / SR-AGENT-POLICY decisions 5 and 6. The agent policy installs by
    # default, so this is a user's one-shot escape; `[agents] install = []` in
    # `fux.toml` is its durable form. A flag rather than a verb — SR-CLI veto 1.
    p_setup.add_argument(
        "--no-agents",
        action="store_true",
        help="do not write the agent policy files outside .fux/ (.claude/, .github/, .kiro/)",
    )
    # W-289, SR-PLUGINS P4/P6: re-pin every `.fux/plugins.toml` row from what
    # is installed — the one deliberate act after an upgrade, never implicit.
    p_setup.add_argument(
        "--pin",
        action="store_true",
        help="re-pin every package in .fux/plugins.toml to the installed version and digest",
    )
    p_setup.set_defaults(func=_dispatch)

    p_doctor = _verb("doctor", help="check environment and repo health")
    # W-66 Phase 4. `doctor` is where the detached runner becomes visible, and
    # an agent reading that needs a parse rather than a sentence (SR-CLI,
    # 2026-08-22). Promotion to a `fux status` verb has a written condition in
    # SR-CLI; it is not a matter of feeling crowded.
    p_doctor.add_argument("--json", action="store_true", default=None, help="machine-readable report")
    # L12 decision 3: the one writer of a missing config key besides `fux setup`.
    # It writes ONLY what is missing, from the packaged template, and never
    # touches a line the consumer wrote.
    p_doctor.add_argument(
        "--fix",
        action="store_true",
        default=None,
        help="write every missing config file and key from its template, then check",
    )
    _add_progress_flags(p_doctor)
    _add_output_flags(p_doctor, band=False)
    p_doctor.set_defaults(func=_dispatch)

    # `register` prints the committed register's rows FROM THE INDEX -- the
    # records, the decoder digest table and the URL list -- so a program reads
    # what the file would say without parsing the file, and the file stays the
    # one committed copy (SR-INGEST decision 22d, W-279). Read-only, offline,
    # no lock: `fux register | diff - .fux/index/REGISTER` is the drift check.
    p_register = _verb(
        "register", help="print the register (one line per indexed document) from the index; --json for machines"
    )
    p_register.add_argument("--json", action="store_true", default=None, help="one JSON object per document")
    _add_output_flags(p_register, band=False)
    p_register.set_defaults(func=_dispatch)

    # `inspect` reads the INDEX; `doctor` checks the ENVIRONMENT (SR-INSPECT
    # decision 1). A flag on `doctor` would have made one command answer two
    # questions with two different remedies — a config edit versus a change to
    # the corpus — and the two lists would have been read as one.
    p_inspect = _verb(
        "inspect", help="what the index looks like: boilerplate, unfindable documents, duplicates"
    )
    p_inspect.add_argument("--json", action="store_true", default=None, help="machine-readable report")
    p_inspect.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="how many rows each named list shows (the counts beside them are never truncated); "
        "default: .fux/inspect.toml [report] top",
    )
    p_inspect.add_argument(
        "--retrieval-sample",
        type=int,
        default=None,
        metavar="N",
        help="documents to test by retrieval; 0 means every one of them (one full query each)",
    )
    p_inspect.add_argument(
        "--probe-sample",
        type=int,
        default=None,
        metavar="N",
        help="documents to probe by their own title and headings (one `ask` each); 0 means every one",
    )
    p_inspect.add_argument(
        "--all",
        action="store_true",
        help="probe every document, not an evenly spaced sample (same as --probe-sample 0)",
    )
    p_inspect.add_argument(
        "--diff",
        nargs=len(("A", "B")),
        metavar=("A", "B"),
        default=None,
        help="compare two report.json files per document; edge loss is always an alert. Writes nothing",
    )
    p_inspect.add_argument(
        "--rebuild-dictionary",
        action="store_true",
        help="re-tokenise the sources even when the cached hash-to-word dictionary is current",
    )
    _add_progress_flags(p_inspect)
    _add_output_flags(p_inspect, band=False)
    p_inspect.set_defaults(func=_dispatch)

    # **The one verb over the corpus** (W-177, Arpit 2026-09-15). `fux update`
    # is deleted and its whole surface is here: the first ingest and every
    # re-ingest are the same command, for directories and URLs alike.
    #
    # ⚠ **A bare `fux ingest` now goes to the network**, which is the ruling
    # that moves the L5 fence onto the default verb. Narrow-by-default survives
    # the move untouched — W-82 ruling 3 is about *which* URLs, never which
    # verb — so the bare form fetches the ones known to be stale and says so.
    # `--no-fetch` is the offline form, and it is what `fux hooks` writes.
    p_ingest = _verb(
        "ingest",
        help="walk configured sources into the committed index, re-fetching stale URLs",
    )
    p_ingest.add_argument(
        "entry", nargs="?", help="one listed entry; omit for every configured source"
    )
    p_ingest.add_argument("--list-skipped", action="store_true", help="print skipped files and why, then exit")
    # ⚠ **`--check` and `--list-skipped` are two exit-early flags on one verb**
    # now (W-177 DoD 3), and argparse has no opinion about which wins. SR-INGEST
    # decision 21 rules `--check`: it is the whole-corpus freshness question,
    # it is the one with a `--json` form, and it is the one a pipeline gates
    # on. `--list-skipped` reports on a walk this invocation is not going to do.
    p_ingest.add_argument(
        "--check",
        action="store_true",
        help="read-only: report what has drifted, then exit 0. Offline; does not fetch",
    )
    # ⚠ **`--check` had no machine-readable output at all** (W-140 row 14,
    # 2026-09-11), and it is the one form whose whole purpose is being read by
    # something else: it exits **0 whether or not anything drifted** —
    # deliberately, because drift is a fact and a non-zero exit would make *your
    # docs changed* look like a broken command to every script that checks
    # status. With no `--json`, the only way to act on the answer was to parse
    # a table meant for a person.
    p_ingest.add_argument(
        "--json", action="store_true", default=None, help="machine-readable drift report (with --check)"
    )
    # W-82 ruling 3: narrow is the DEFAULT and this overrides it. There is
    # deliberately no `--dirty`/`--stale`/`--changed` — if the dirty list is the
    # right thing to refresh, it should not have to be asked for.
    #
    # ⚠ **Named `--all` on `fux update`, where it sat alone** (W-177 ruling 3).
    # Beside `--full` it would read as its synonym, and the two are unrelated:
    # `--full` re-extracts every *document*, `--refetch-all` fetches every
    # *URL*. One of them touches the network and the other cannot.
    p_ingest.add_argument(
        "--refetch-all",
        action="store_true",
        help="fetch every listed URL, not just the ones known to be stale",
    )
    # SR-URL-FRESHNESS. A flag on the networked verb, never a new one: `fux
    # retry` would be a second way to do what this already does, and SR-CLI
    # decision 1 refuses that. The selector is url-state's own `fail_streak > 0`,
    # which is the number that file exists to report.
    p_ingest.add_argument(
        "--failed",
        action="store_true",
        help="fetch only the URLs whose last run failed (fail_streak > 0)",
    )
    # The offline form, and the same flag with the same meaning `fux add`
    # carries (W-177 open question 1, ruled (b)). It is public surface on
    # purpose: CI and an air-gapped clone have to be able to ask for an offline
    # ingest by hand. `fux hooks` writes it; `fux daemon` writes the bare verb.
    # There is no `--offline` alias.
    p_ingest.add_argument(
        "--no-fetch",
        action="store_true",
        help="do not open the network; re-read what is on disk (what the git hooks run)",
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
    # W-66 Phase 2 / SR-MAINTENANCE decision 1d. `--stop` is the takeover
    # without the run; a plain `fux ingest` takes over and then runs. It sits
    # on `ingest` rather than becoming a verb because SR-CLI veto 1 forbids
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
    # SR-OUTPUT decision 15: a verb that reads `.fux/output.toml` must be able
    # to ignore it. This arrived with `--check --json` (W-140 row 14) on the
    # verb that used to own it, and moved here whole with W-177 — the escape
    # hatch is how *is it me or the config?* stays one flag rather than an
    # experiment.
    _add_output_flags(p_ingest, band=False)
    p_ingest.set_defaults(func=_dispatch)

    p_build = _verb(
        "build", help="rebuild the derived accelerator from the committed index"
    )
    _add_progress_flags(p_build)
    # L12: `[cli] progress_threshold` is read from .fux/output.toml, so this
    # verb can bisect the file like every other verb that reads it (decision 15).
    _add_output_flags(p_build, band=False)
    p_build.set_defaults(func=_dispatch)

    # The source group. Flat verbs over all three lists, dispatching on the
    # entry — `fux source add` is the subcommand tree SR-CLI decision 1
    # refuses, and it is the shape this replaced `fux url` to avoid growing.
    def _entry_flags(p: argparse.ArgumentParser) -> None:
        """The attribute flags. Each is checked against the list the entry
        dispatched to, so `--cdp` on a directory is an error, not a no-op."""
        p.add_argument("--types", action="store_true", help="the entry is a file-type pattern (.fux/formats.toml)")
        # 🔴 **`--fetch <stem>` is the general form; `--cdp`/`--http` are the two
        # aliases that predate it** (W-199 D1). There is no default fetcher, so
        # `fux add <url>` with none of these RESOLVES a stem from
        # `[sources.url.routes]` and the modules' `ROUTES` claims — and refuses
        # when nothing matches, naming the host and the stems on disk.
        p.add_argument("--fetch", metavar="STEM", help="URLs: record fetch=STEM - a file in .fux/fetchers/. Without it, the routes table and the modules' ROUTES claims decide, and nothing matching refuses")
        p.add_argument("--cdp", action="store_true", help="URLs: record fetch=cdp (alias for --fetch cdp)")
        p.add_argument("--http", action="store_true", help="URLs: record fetch=http (alias for --fetch http)")
        # 🔴 **The other half of the pipe** (the pipe ruling, 2026-09-18). A URL
        # line states `decoder=` as well as `fetch=`, and there is no default:
        # without this flag `fux add <url>` OBSERVES the type on the one fetch it
        # already performs and writes what it observed — and refuses when nothing
        # maps, rather than writing a line it cannot ingest. Required with
        # `--no-fetch`, which observes nothing.
        p.add_argument("--decoder", metavar="STEM", help="URLs and types: record decoder=STEM - a built-in, `prose` for bytes that are already text, or a file in .fux/decoders/. For a URL, without it `fux add` writes the decoder it observed on its one fetch, and refuses if nothing maps")
        p.add_argument("--archived", action="store_true", help="dirs: record archived=true")
        p.add_argument("--keep", action="store_true", help="URLs: record keep=true - retain the fetched bytes in .fux/acquired/ (the default)")
        p.add_argument("--no-keep", action="store_true", help="URLs: record keep=false - do not retain the fetched bytes")
        p.add_argument(
            "--no-update",
            action="store_true",
            help=(
                "URLs: record update=never - pin this document. `fux ingest` will not "
                "fetch it again, not even under --refetch-all. NOTE this add still fetches "
                "ONCE, which is what makes the line ingestable; the flag governs every run after"
            ),
        )
        p.add_argument("--ttl", metavar="D", help="URLs: record ttl=D - how long a citation may go unchecked at ask time (0, 30s, 15m, 1h, 7d)")
        p.add_argument("--dry-run", action="store_true", help="print the line and the plan; write nothing")

    p_add = _verb(
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
    _add_output_flags(p_add, band=False)
    p_add.set_defaults(func=_dispatch)

    p_remove = _verb(
        "remove", help="take an entry out of the corpus — deletes its line, or excludes it if an ancestor is listed"
    )
    p_remove.add_argument("entry", help="a path, a single file, or an http(s) URL")
    p_remove.add_argument("--types", action="store_true", help="the entry is a file-type pattern")
    p_remove.add_argument("--dry-run", action="store_true", help="say which branch it would take; write nothing")
    p_remove.add_argument("--no-ingest", action="store_true", help="edit the line only; do not re-ingest")
    _add_progress_flags(p_remove)
    _add_output_flags(p_remove, band=False)
    p_remove.set_defaults(func=_dispatch)


    def _query_parser(name: str, help_text: str):
        p = _verb(name, help=help_text)
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
        # W-109. **`--expand` is a TERM SLOT, not a second question.** The
        # caller — usually a model — hands over the words it expects the
        # document to use; fux analyzes them with the same analyzer the index
        # was built with and scores them at `[ranking] expand_weight`. Fux
        # never writes one (L4), and a document matching ONLY expansion terms
        # is dropped by `rank()` rather than returned.
        p.add_argument(
            "--expand", metavar="TEXT", default=None,
            help="extra terms the document probably uses, scored at [ranking] expand_weight",
        )
        _add_tune_flag(p)
        _add_output_flags(p, band=True)
        return p

    def _ask_shaped_parser(name: str, help_text: str):
        """`ask`'s whole flag surface, for the two verbs that must share it.

        ⚠ **A factory rather than two blocks, because `fux lexical` is FROZEN
        to `ask`'s output shape** (SR-CLI decision 12, W-160). Two hand-kept
        copies of this list would drift the moment one verb gained a flag, and
        the drift would be invisible: both parsers would work, and the frozen
        verb would quietly stop accepting what its own contract says it takes.
        `tests/test_cli.py::test_lexical_takes_exactly_the_flags_ask_takes` is
        the gate; this factory is what makes it pass by construction.
        """
        p = _query_parser(name, help_text)
        p.add_argument("--top", type=int, default=None, metavar="N", help=_top_help())
        p.add_argument("--explain", action="store_true", default=None, help="report which path answered")
        # W-84's matched `§ heading` lines. ⚠ **A pair, not a `store_true`** — the
        # lines are ON by default, so a `store_true` could only ever turn them on
        # again and `.fux/output.toml` could never turn them off from the command
        # line. `default=None` on BOTH halves is SR-OUTPUT decision 10: an absent
        # flag has to be distinguishable from an explicit one, or the file's value
        # is unreachable and nothing fails to say so.
        sections = p.add_mutually_exclusive_group()
        sections.add_argument(
            "--sections", dest="sections", action="store_true", default=None,
            help="show the matched section headings under each hit (default)",
        )
        sections.add_argument(
            "--no-sections", dest="sections", action="store_false", default=None,
            help="omit the matched section headings, in text and in --json alike",
        )
        # W-161's Tier B opt-out. **A pair, like `--sections`**, so that both
        # directions are reachable from the command line and an absent flag stays
        # distinguishable from an explicit one.
        #
        # 🔴 **It is NOT backed by a key in `.fux/output.toml`, deliberately.**
        # `[graph] ask_related` already states *do I want the related tier?* for
        # this repository; a second statement in the rendering file would be the
        # restatement [SR-LAW-0](../records/0002_LAW-0-authority.md) forbids —
        # the two could disagree while both looked correct — and, because an
        # unset output key is a hard error (SR-OUTPUT decision 19), it would
        # **break every consumer's committed `output.toml` on upgrade** to add a
        # knob that duplicates one they already have. `None` here means *the
        # tune decides*, which is `--no-tune`'s own shape.
        #
        # ⚠ **It reaches `lexical` too, and is INERT there.** This factory is the
        # single source of both parsers precisely so the two cannot drift
        # (SR-CLI decision 12), and `fux lexical` has no graph tier **by
        # definition** — it is the lexical core, frozen. So the flag parses and
        # changes nothing there. The alternative was giving `lexical` its own
        # parser, which is the drift this factory exists to prevent, to remove a
        # flag that already does nothing.
        related = p.add_mutually_exclusive_group()
        related.add_argument(
            "--related", dest="related", action="store_true", default=None,
            help="show documents the answers link to but no query word matched (default)",
        )
        related.add_argument(
            "--no-related", dest="related", action="store_false", default=None,
            help="omit the related tier, in text and in --json alike",
        )
        # SR-PROVENANCE. A separate flag from `--explain`, not an extension of it:
        # `--explain` answers "which code path ran" and `--why` answers "why this
        # document" — different questions, different costs. `--why` runs a second
        # query when a tune file exists, and folding that cost into a flag people
        # already pass for latency debugging would be a surprise.
        p.add_argument(
            "--why", action="store_true",
            help="how the ranking got here: matched terms, the cut line, rerank and tune deltas",
        )
        # W-109. **Repeatable, and fused in RANK space** — each phrasing is ranked
        # on its own and the lists are combined by RRF (k = 60). `dest="also"`
        # because `query` is already the positional: the first question is
        # syntactically primary, which is what lets `--band` name one query.
        p.add_argument(
            "-q", "--query", dest="also", action="append", metavar="TEXT",
            help="another phrasing of the same question; results are fused by RRF (repeatable)",
        )
        return p

    p_ask = _ask_shaped_parser("ask", "answer a question from the committed index, with citations")
    p_ask.set_defaults(func=_dispatch)

    # **W-160's first atom: BM25F alone, named and FROZEN.** `ask --scan`
    # already *is* the lexical core; this makes it a contract — the baseline
    # arm for every ranking verdict and for the Python/Node differential law.
    # It exists so that when `ask` grows a graph tier (W-161) there is still a
    # verb whose answer is *only* what the words say, and a test can hold the
    # two apart. **A future component added to the lexical core is a new verb
    # or a tunable, never a change to this one** (SR-CLI decision 12).
    p_lexical = _ask_shaped_parser(
        "lexical", "rank on the words alone — BM25F, frozen; the baseline `ask` is measured against"
    )
    p_lexical.set_defaults(func=_dispatch)

    p_find = _query_parser("find", "ranked document locations, one per line")
    p_find.add_argument("--top", type=int, default=None, metavar="N", help=_top_help())
    p_find.add_argument(
        "-q", "--query", dest="also", action="append", metavar="TEXT",
        help="another phrasing of the same question; results are fused by RRF (repeatable)",
    )
    # W-111 — precision controls, not ranking cleverness. Each one REMOVES
    # results from what the ranking already produced; none of them retrieves
    # anything new. `find` is the verb that gets piped, and a pipe wants a
    # narrower list, not a cleverer one.
    p_find.add_argument(
        "--phrase", metavar="TEXT", default=None,
        help="keep only documents whose local text contains this phrase, words adjacent and in order",
    )
    p_find.add_argument(
        "--under", metavar="PREFIX", default=None,
        help="keep only documents whose loc starts with this path prefix",
    )
    p_find.add_argument(
        "--all", dest="require_all", action="store_true",
        help="keep only documents carrying EVERY query term (grep's AND)",
    )
    p_find.add_argument(
        "--no-archived", dest="no_archived", action="store_true",
        help="drop documents declared archived (archived=true, or the record's own flag); "
        "the confidence band still describes the unfiltered ranking",
    )
    p_find.set_defaults(func=_dispatch)

    p_answer = _query_parser(
        "answer", "the single best answer — a fetched, re-scored passage when the source is reachable"
    )
    p_answer.add_argument(
        "--no-refer",
        action="store_true",
        default=None,
        help="skip the refer plane; answer from the index's own structure alone",
    )
    # ⚠ **The only way to ask for caching, and until 2026-09-11 there was none**
    # (W-140 row 6). [SR-URL-FRESHNESS](records/0147_url-freshness.md)
    # decision 11 resolves the interval as `min(policy, line)` -- *a line may
    # narrow it and can never widen it* -- and `answer` built its policy with
    # the default `0`. `min(0, anything)` is `0`, so every `ttl=` in every repo
    # was dead at ask time and the `cached` verdict was unreachable by
    # construction. The arithmetic was right; nothing could set the left operand.
    #
    # A FLAG, not a config key: SR-OUTPUT's `[cli.*]` chooses rendering and may
    # never change what a verb does, which is the defect row 10 closed the same
    # day. Default stays `0`, so a caller who does not ask still cannot be
    # served a cached byte (W-60 verdict F).
    p_answer.add_argument(
        "--cache-ttl",
        metavar="DURATION",
        default=None,
        help=(
            "serve a previously fetched copy for this long instead of re-fetching "
            "(e.g. 15m, 1h, 0 = off, the default). A URL line's own `ttl=` can "
            "only narrow this, never widen it"
        ),
    )
    # SR-PROVENANCE. Three flags rather than one, because they are three
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
    p_answer.set_defaults(func=_dispatch)

    # SR-PROVENANCE. A verb, not a flag: it takes a FILE rather than a query,
    # so it does not belong on the query parser at all — every flag there
    # assumes a `query` positional this command has no use for.
    p_verify = _verb(
        "verify", help="re-run a receipt against this tree: reproduced | drifted | unverifiable"
    )
    p_verify.add_argument("receipt", help="path to a receipt written by `fux answer --receipt`")
    p_verify.add_argument("--json", action="store_true", help="machine-readable verdict")
    p_verify.add_argument(
        "--rerun", action="store_true",
        help="re-answer the question too; without it only the INPUTS are checked",
    )
    p_verify.set_defaults(func=_dispatch)

    # W-76 Phase 8. **No `--model` flag, and that is the design**: fux never
    # calls a model, so there is no networked path to fence. Generation is the
    # `fux-enrich` agent skill; these two flags are the deterministic halves.
    p_enrich = _verb(
        "enrich", help="plan and validate the enrichment an agent skill generates"
    )
    enrich_mode = p_enrich.add_mutually_exclusive_group()
    enrich_mode.add_argument(
        "--plan", action="store_true", help="print the worklist (the default)"
    )
    enrich_mode.add_argument(
        "--check", action="store_true", help="validate what exists and report coverage"
    )
    # W-104. 🔴 **This FILTERS the report; it never widens scope.** A document
    # no `enrich=true` line reaches is not plannable and naming it here does not
    # make it so -- which directories get enriched stays a human's declaration
    # (SR-ENRICH decision 4). Matching is exact rather than a prefix or a glob,
    # because a selector that silently matches two documents is how a
    # one-document request becomes a bulk run.
    p_enrich.add_argument(
        "target",
        nargs="?",
        metavar="TARGET",
        help="one loc or URL, exactly as the index spells it; without it, every "
             "declared scope",
    )
    # W-238: `--check` paints a bar — one ranked query per question.
    _add_progress_flags(p_enrich)
    _add_output_flags(p_enrich, band=False)
    p_enrich.set_defaults(func=_dispatch)

    # W-76 Phase 5. A verb rather than a flag on `ask`: it is a long-running
    # server, not a query, and SR-CLI's four groups gain a fifth consumer-facing
    # one rather than overloading the read verbs.
    # **W-162.** A verb rather than a flag on `enrich`, and the reason is the
    # author: `enrich` plans and validates text a MODEL wrote; this writes a
    # line a PERSON typed, and the two have different provenance, different
    # survival rules under regeneration, and different `--check` treatment.
    # Folding them would make one command answer to two authors.
    p_correct = _verb(
        "correct",
        help="add the words people ASK with to the document that answers — one human question line",
    )
    p_correct.add_argument("question", nargs="?", help="the question somebody would type")
    p_correct.add_argument("doc", nargs="?", help="the document that answers it — a `loc` or an id")
    p_correct.add_argument(
        "--pin",
        action="store_true",
        help="also force this document to #1 for this EXACT question. Rare, and suspended when the document changes",
    )
    p_correct.add_argument(
        "--no-pin",
        action="store_true",
        help="drop an existing pin for this question while keeping the correction",
    )
    p_correct.add_argument(
        "--reaffirm",
        action="store_true",
        help="re-file an existing correction against the document as it is now, releasing a suspended pin",
    )
    p_correct.add_argument("--list", action="store_true", help="every filed correction, and any suspended pin")
    p_correct.add_argument("--json", action="store_true", default=None, help="machine-readable output")
    _add_output_flags(p_correct, band=False)
    p_correct.set_defaults(func=_dispatch)

    p_mcp = _verb(
        "mcp", help="serve the index over MCP on stdio, for coding agents"
    )
    # SR-OUTPUT decision 15: on EVERY verb that reads .fux/output.toml,
    # `mcp` included — read directly in `cmd_mcp` rather than folded into
    # `_apply_output_defaults`, because `mcp` carries no `CLI_VERBS` keys of
    # its own (its only knob, `[mcp] top`, is not a CLI flag at all).
    p_mcp.add_argument(
        "--no-output-config",
        action="store_true",
        help="ignore .fux/output.toml and use the template `fux setup` writes",
    )
    p_mcp.set_defaults(func=_dispatch)

    # W-285. A verb, like `mcp`, for `mcp`'s reason: a long-running stdio
    # server an editor spawns, not a query. SR-LSP.
    p_lsp = _verb(
        "lsp", help="serve the index over the Language Server Protocol on stdio, for editors"
    )
    p_lsp.add_argument(
        "--no-output-config",
        action="store_true",
        help="ignore .fux/output.toml and use the template `fux setup` writes",
    )
    p_lsp.set_defaults(func=_dispatch)

    # W-284. A verb rather than a flag on `find`: its output is a document in
    # someone else's format (llms.txt), not a result list. SR-LLMS.
    p_llms = _verb(
        "llms", help="print an llms.txt (or, with --full, an llms-full.txt) from the index"
    )
    p_llms.add_argument(
        "--in", dest="prefixes", action="append", metavar="PREFIX",
        help="only documents whose loc starts with PREFIX (repeatable; default: every document)",
    )
    p_llms.add_argument(
        "--full", action="store_true",
        help="append each prose document's text, read off disk -- the llms-full.txt convention",
    )
    p_llms.add_argument("--title", help="the H1 (default: the repository's directory name)")
    p_llms.add_argument("--summary", help="the blockquote under the H1 (default: none)")
    p_llms.add_argument(
        "--base-url", metavar="URL",
        help="prefix every file link with URL (default: links are repo-relative)",
    )
    p_llms.set_defaults(func=_dispatch)

    # W-210 — the explorer. A LOCAL page over the real `ask`, and the verb
    # carries no `--host`: `serve.HOST` is the contract, not a default, and a
    # flag would turn a refusal into a preference. See `serve/__init__.py`.
    p_serve = _verb(
        "serve", help="a local page that shows why each document ranked, over the real `ask`"
    )
    p_serve.add_argument(
        "--port", type=int, default=None, metavar="N",
        help="port on 127.0.0.1 (.fux/output.toml [cli.serve] port; 0 asks the OS for a free one)",
    )
    p_serve.add_argument(
        "--open", action="store_true", help="open the page in a browser once the server is up"
    )
    _add_output_flags(p_serve, band=False)
    p_serve.set_defaults(func=_dispatch)

    p_hooks = _verb("hooks", help="install the git hooks and the index merge driver")
    p_hooks.add_argument("--install", action="store_true", help="write them (the default)")
    p_hooks.add_argument("--status", action="store_true", help="report what is wired")
    p_hooks.add_argument("--uninstall", action="store_true", help="remove only what fux wrote")
    p_hooks.add_argument("--json", action="store_true", default=None, help="machine-readable status")
    _add_output_flags(p_hooks, band=False)
    p_hooks.set_defaults(func=_dispatch)

    # W-82 ruling 10 (Arpit, 2026-08-27). A verb, like `mcp`, for the same
    # reason: it is a long-running process rather than a query, and flat rather
    # than a subcommand tree because "no subcommand tree" is SR-CLI's
    # constraint. `start`/`stop`/`status` are POSITIONAL, not flags, because
    # they are mutually exclusive states and `fux daemon --start --stop` should
    # not parse.
    p_daemon = _verb(
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
    _add_output_flags(p_daemon, band=False)
    p_daemon.set_defaults(func=_dispatch)

    # The graph group. Flat, like every other verb — `fux graph path` would be
    # the first subcommand tree on this surface, and "no subcommand tree" is
    # the constraint SR-CLI keeps.
    p_explain = _verb("explain", help="one document's outbound edges and its community")
    p_explain.add_argument("doc", help="a doc id or the loc `find` printed")
    p_explain.add_argument("--json", action="store_true", default=None, help="machine-readable output")
    _add_output_flags(p_explain, band=False)
    p_explain.set_defaults(func=_dispatch)

    p_graph = _verb(
        "graph", help="the neighbourhood around a query's best answers, or around documents you name"
    )
    # **W-160's second atom.** The walk gets a life without a query. `query`
    # becomes optional and `--seed` is its alternative — and the query form is
    # now DEFINED as `--seed` over `lexical`'s top-k, which is what
    # `tests_e2e/test_relational.py::test_graph_query_equals_graph_over_lexical_seeds`
    # asserts rather than assumes.
    #
    # ⚠ **Not mutually exclusive via argparse, because one of them is
    # REQUIRED and argparse cannot say both.** A mutually-exclusive group with
    # `required=True` refuses a positional, so the check is in `cmd_graph`,
    # where it can name which of the two mistakes was made.
    p_graph.add_argument(
        "query", nargs="?", help="natural-language question; omit it and pass --seed instead"
    )
    p_graph.add_argument(
        "--seed",
        action="append",
        metavar="ID",
        help="walk from these documents instead of from a query's best answers. "
        "Mass follows ARGUMENT ORDER, the same rank-mass rule the query form applies to top-k (repeatable)",
    )
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
    # **Exposed and INERT at their defaults** (W-160 DoD 4). They exist on
    # `graph` so the mechanism W-161 needs can be driven and measured before
    # `ask` composes it — landing the mechanism and the composition together
    # would make one diff nobody can attribute a delta to.
    p_graph.add_argument(
        "--kinds",
        metavar="KIND[,KIND]",
        default=None,
        help="walk only these edge kinds (ref, tag, code, supersedes). Default: all of them",
    )
    p_graph.add_argument(
        "--link-idf",
        action="store_true",
        help="discount an edge by how many documents point at its target, so a hub does not dominate. Off by default and measured by nobody yet",
    )
    p_graph.add_argument(
        "--max-hops",
        type=int,
        default=None,
        metavar="N",
        help="refuse mass to a node further than N hops from any seed. Default: unbounded (the walk's own iteration count already reaches three)",
    )
    _add_tune_flag(p_graph)
    _add_output_flags(p_graph, band=False)
    p_graph.set_defaults(func=_dispatch)

    p_path = _verb("path", help="how two documents are connected, most reliable route first")
    p_path.add_argument("src", metavar="FROM", help="the document the route starts at")
    p_path.add_argument("dst", metavar="TO", help="the document the route ends at")
    p_path.add_argument("--hops", type=int, default=None, metavar="N", help=_hops_help())
    p_path.add_argument("--json", action="store_true", default=None, help="machine-readable output")
    _add_tune_flag(p_path)
    _add_output_flags(p_path, band=False)
    p_path.set_defaults(func=_dispatch)

    # W-233 (F1): proposes identifier families; `--write` replaces only the
    # [detected] table of .fux/identifiers.toml. [user] is never touched.
    p_ids = _verb(
        "identifiers",
        help="propose identifier families (RF-{n}) from the index; --write records them",
    )
    p_ids.add_argument("--write", action="store_true",
                       help="rewrite .fux/identifiers.toml [detected]; [user] is kept byte for byte")
    p_ids.add_argument("--json", action="store_true", default=None, help="machine-readable output")
    _add_progress_flags(p_ids)
    _add_output_flags(p_ids, band=False)
    p_ids.set_defaults(func=_dispatch)

    # A flat verb with no arguments at all: it neither reads the repo nor
    # writes it, so it works before `fux setup` has run and outside a root.
    # Printing is the whole feature — see `_cmd_tune`.
    p_tune = _verb(
        "tune", help="print the tunables file for you to paste into .fux/tune.toml"
    )
    p_tune.set_defaults(func=_cmd_tune)

    # SR-OUTPUT: prints, never writes. `tomllib` reads and the stdlib does not
    # write TOML, and a writer would mean fux editing a file it promised was
    # yours — the same refusal `fux tune` makes.
    p_output = _verb(
        "output", help="print the output-defaults file for you to paste into .fux/output.toml"
    )
    p_output.set_defaults(func=_cmd_output)

    return parser


#: The verbs `main` runs without `.fux/pii.toml` -- SR-PII decision 17's table
#: and nothing else. `setup` writes the file; `tune` and `output` print a
#: specimen and read no repository; `doctor` runs so it can report the missing
#: file as an error row. **Every other verb is gated, including one added
#: later** -- `tests/test_cli.py` walks the parser and fails on a new exemption.
PII_EXEMPT = frozenset({"setup", "tune", "output", "doctor"})

#: `pii.rules_path()`'s location, spelled here so the gate costs a stat call and
#: not an import of `fux.ingest` (~70 ms of decoders on every `ask` and `find`).
#: `tests/test_cli.py` holds the two equal; the refusal's wording stays in `pii`.
#: `.fux/pii.toml`, from `constants.toml [files]` -- the one home of the name.
_PII_RULES = (fixed("fuxdir", "dir"), fixed("files", "pii_name"))


def _require_pii_rules(command: str) -> None:
    """SR-PII decision 17: no `.fux/pii.toml`, no command.

    Outside any root there is no repository to hold the file, so the gate does
    not fire and the verb fails, or does not, on its own terms.
    """
    if command in PII_EXEMPT:
        return
    from .config import find_root

    root = find_root()
    if root is None or root.joinpath(*_PII_RULES).is_file():
        return
    from .acquire import pii

    pii.require(root)


#: SR-PLUGINS P4: the verbs that still run while a declared package is missing
#: or drifted — the two that diagnose and repair the declaration, and the ones
#: that neither read the index nor decode a byte. Every other verb refuses.
PLUGINS_EXEMPT = frozenset({"setup", "doctor", "tune", "output", "hooks", "daemon"})


def _require_plugins(command: str) -> None:
    """SR-PLUGINS P4: a declared package missing or drifted, no command.

    🔴 **A missing `.fux/plugins.toml` is NOT this refusal** — it means prose
    only, and `fux ingest` and `fux doctor` say so (W-289's decision). What
    refuses is a declaration this machine cannot honour: two machines on one
    repository must never build or read different indexes. Outside any root
    there is no declaration and the gate does not fire.
    """
    if command in PLUGINS_EXEMPT:
        return
    from .config import find_root

    root = find_root()
    if root is None:
        return
    from . import plugins

    if plugins.exists(root):
        plugins.require(root)


def main(argv: list[str] | None = None) -> int:
    _stdio_utf8()
    words = list(sys.argv[1:] if argv is None else argv)
    verb = next((w for w in words if not w.startswith("-")), None)
    if verb in VERBS and not available(verb):
        exc = _refusal(verb)
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    # SR-PII decision 17, placed by SR-CLI decision 4: before dispatch and
    # before anything else reads the repository, so no handler has to remember.
    try:
        _require_pii_rules(args.command)
        # SR-PLUGINS P4, at the same boundary for the same reason: before
        # anything reads the repository, so no handler has to remember.
        _require_plugins(args.command)
    except FuxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    # SR-OUTPUT decision 3. Before dispatch and before the progress plane, so
    # every `args` a command sees is already resolved.
    try:
        _apply_output_defaults(args)
    except FuxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    if args.command in _PROGRESS_COMMANDS:
        # Imported here, not at module level — SR-CLI decision 7, `--version`
        # stays instant. One `Progress` for the whole invocation (W-64): an
        # `ingest` that also builds the accelerator is one continuous
        # sequence, not two bars fighting over the same terminal line.
        from .progress import Progress

        args.progress = Progress(
            no_progress=args.no_progress,
            force=args.force_progress,
            threshold=args.progress_threshold,
        )
    # W-170 — the observer hook's dispatch point, and there is exactly one.
    #
    # 🔴 **After the verb has fully rendered and its exit code is fixed**, which
    # is what makes *observe-only* structural rather than a rule somebody has to
    # keep: there is nothing left for consumer code to influence. `code` is
    # computed first, stdout is flushed, and only then does anything in
    # `.fux/observers/` run — and its return value is discarded.
    #
    # ⚠ **`fux mcp` and `fux lsp` are excluded by name.** A long-lived server calling consumer
    # code once per request is a different decision with a different blast
    # radius, and SR-OBSERVE does not make it.
    started = time.monotonic()
    try:
        code = args.func(args)
    except FuxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        code = exc.exit_code
    except KeyboardInterrupt:
        return fixed("exit", "interrupted")
    _observe(args, argv, int(timedelta(seconds=time.monotonic() - started) / timedelta(milliseconds=1)))
    return code


def _observe(args, argv: list[str] | None, ms: int) -> None:
    """Hand this run's counts to `.fux/observers/`. **Never raises.**

    ⚠ **A repo with no `.fux/observers/` pays one `stat`** and nothing else —
    the same shape `_apply_pin` takes for an unpinned query. The import is
    local so `--version` stays instant (SR-CLI decision 7).
    """
    if args.command in ("mcp", "lsp"):
        return
    try:
        sys.stdout.flush()
    except Exception:  # pragma: no cover - a hook must not fail a verb
        pass
    try:
        from . import __version__, observe
        from .config import find_root

        root = find_root(Path.cwd())
        if root is None:
            return
        try:
            from .config import load as load_config

            cfg_max_ms = load_config(root).observe_max_ms
        except Exception:
            # A malformed `fux.toml` already failed the verb if the verb needed
            # it, and it must not additionally fail the hook. ⚠ **Until W-225
            # stage 3b this ran the observers on a bound of 50 held in code**;
            # SR-LAW-12 leaves no bound to run them on, so they do not run.
            return
        record = observe._record_from(
            args.command, list(argv if argv is not None else sys.argv[1:]), ms, __version__
        )
        observe.dispatch(root, record, max_ms=cfg_max_ms)
    except Exception:  # pragma: no cover - a hook must not fail a verb
        pass


if __name__ == "__main__":
    sys.exit(main())
