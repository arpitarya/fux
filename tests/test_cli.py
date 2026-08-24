from __future__ import annotations

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
        "ask",
        "find",
        "answer",
        "enrich",
        "mcp",
        "explain",
        "graph",
        "path",
        "hooks",
    }


def test_no_verb_grows_a_subcommand_tree():
    """Flat verbs, however many there are — that is the constraint that survives."""
    parser = build_parser()
    (command,) = [a for a in parser._subparsers._group_actions if a.dest == "command"]
    for name, sub in command.choices.items():
        nested = [a for a in sub._subparsers._group_actions] if sub._subparsers else []
        assert not nested, f"`fux {name}` grew a subcommand tree"
