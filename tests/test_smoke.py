"""Smoke tests for the rebuilt package skeleton."""

from __future__ import annotations

import fux
from fux.cli import main
from fux.errors import FuxError


def test_version_is_set():
    assert fux.__version__ == "0.22.1"


def test_cli_version(capsys):
    # argparse's version action exits 0 after printing.
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "0.22.1" in out


def test_cli_no_args_prints_help():
    assert main([]) == 0


def test_fux_error_carries_exit_code():
    err = FuxError("boom", exit_code=2)
    assert err.exit_code == 2
    assert str(err) == "boom"
