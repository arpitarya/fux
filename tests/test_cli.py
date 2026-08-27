from __future__ import annotations

import subprocess
import sys

import pytest

from fux import __version__
from fux.cli import build_parser, main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"fux {__version__}"


def test_no_command_prints_help_and_exits_1(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()


def test_module_invocation_spellings_agree():
    """`python -m fux` and `python -m fux.cli` are ONE implementation.

    The ladder's last rung (ADR-AGENT-POLICY) exists so a repo with an
    inactive `.venv` still resolves to *the engine is here* rather than
    `command not found`. `fux.cli` always worked; `fux` is the spelling a
    human actually types, and Arpit ruled it supported (2026-08-27, W-82
    §3.6 fork B).

    **This test is the fence around `__main__.py` staying a delegate.** The
    moment that file grows argument handling of its own, the two spellings
    diverge and this fails — which is the point, because a second entry point
    with its own behaviour is a second thing to support forever.
    """
    runs = [
        subprocess.run(
            [sys.executable, "-m", target, "--version"],
            capture_output=True,
            text=True,
        )
        for target in ("fux", "fux.cli")
    ]
    assert runs[0].returncode == runs[1].returncode == 0
    assert runs[0].stdout == runs[1].stdout == f"fux {__version__}\n"


def test_parser_has_the_verb_surface():
    """The CLI contract, in four groups and no subcommand tree (ADR-CLI).

    lifecycle `setup`/`doctor` set the repo up and check it · write
    `ingest`/`build` — one writes the committed plane, one derives from it ·
    sources **`add`/`remove`/`update`** maintain what is indexed (W-63,
    replacing `url`) · read `ask`/`find`/`answer` differ only in how much they
    commit to · **graph `explain`/`graph`/`path` answer with relationships
    rather than with rankings** (M3) · maintenance `hooks` wires the
    repository up to keep its own index in step (M5).

    Seven groups: W-76 Phase 5 added **agent `mcp`**, Phase 8 added
    **enrichment `enrich`** — which plans and validates the text an agent skill
    generates, and has **no `--model` flag**, because fux never calls one.

    Phase 5's `mcp` — the index served to
    coding agents over stdio JSON-RPC ([ADR-MCP](../docs/adr/0039_mcp.md)). A
    verb rather than a flag on `ask`, because it is a long-running server and
    not a query.

    ADR-TUNE added **`tune`**, which prints the tunables file and exits. A verb
    rather than `setup --print-tune` because it answers a question on its own —
    *what can I change?* — and it is the one verb that touches neither the repo
    nor the network, so it works before `fux setup` has ever run.

    ADR-OUTPUT added **`output`**, the exact twin of `tune` one boundary
    further in: `tune` prints what changes WHICH documents come back, `output`
    prints what changes how they are SHOWN. Both print and neither writes.

    Six, not four, and the count was never the mental model — which is why
    adding one costs a line here and a line in ADR-CLI rather than a redesign.

    **`url` is gone, not deprecated** (W-63). It was four days old, pre-1.0,
    and its whole surface is `fux add <URL>` / `fux remove <URL>`. The flag
    `ingest --refresh-urls` was the opposite call — older, likelier to be in
    someone's CI — and survives one release as a hidden alias for
    `fux update`, which is asserted below.
    """
    parser = build_parser()
    sub_actions = [a for a in parser._subparsers._group_actions if a.dest == "command"]
    assert set(sub_actions[0].choices) == {
        "setup",
        "doctor",
        "ingest",
        "build",
        "add",
        "remove",
        "update",
        "output",
        "ask",
        "find",
        "answer",
        "enrich",
        "mcp",
        "explain",
        "graph",
        "path",
        "hooks",
        "tune",
        # W-82 ruling 10 (Arpit, 2026-08-27). A verb like `mcp`, for the same
        # reason: a long-running process, not a query. `start`/`stop`/`status`
        # are a positional ARGUMENT, not a subparser — `fux daemon start` must
        # not become the first subcommand tree on this surface.
        "daemon",
        # ADR-PROVENANCE (2026-08-27). A verb, not a flag on `answer`: it takes
        # a receipt FILE rather than a query, so every flag on the query parser
        # -- `--top`, `--fast`, `--no-tune` -- would be meaningless on it.
        "verify",
    }


def test_no_verb_grows_a_subcommand_tree():
    """Flat verbs, however many there are — that is the constraint that survives."""
    parser = build_parser()
    (command,) = [a for a in parser._subparsers._group_actions if a.dest == "command"]
    for name, sub in command.choices.items():
        nested = [a for a in sub._subparsers._group_actions] if sub._subparsers else []
        assert not nested, f"`fux {name}` grew a subcommand tree"
