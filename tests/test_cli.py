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
    """The CLI contract: doctor/ingest/build maintain, ask/find/answer query.

    `build` is the derived accelerator's rebuild path (M2); `find` and `answer`
    complete the verb surface the archived engine established, so M4's refer
    plane upgrades `answer` rather than introducing a new command.
    """
    parser = build_parser()
    sub_actions = [a for a in parser._subparsers._group_actions if a.dest == "command"]
    assert set(sub_actions[0].choices) == {"doctor", "ingest", "build", "ask", "find", "answer"}
