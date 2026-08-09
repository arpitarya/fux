"""Error-handling contract: CLI exit codes, fail-open hooks, FUX_DEBUG tracing.

Covers the boundary discipline (plan §error contract): `main()` renders
FuxError/KeyboardInterrupt/unexpected as 1/130/1 (traceback only under FUX_DEBUG);
every hook entrypoint is fail-open (returns 0 when its core raises) EXCEPT the
strict-mode `return 2`, which must still fire; swallowed hook exceptions surface
under FUX_DEBUG (fail-open ≠ fail-silent); a read command with no `.fux/` exits 1
with a terse `error:` line; MCP reports `isError` on malformed input.
"""
from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from fux import cli, hooks, mcpserver
from fux.errors import FuxError
from fux.findings import Finding


# ── main() exit-code mapping ────────────────────────────────────────────────
def _patch_main_fn(monkeypatch, exc: BaseException) -> None:
    """Make `cli.main([])` dispatch to a fn that raises `exc`."""
    def _fake_parser() -> argparse.ArgumentParser:
        p = argparse.ArgumentParser()

        def fn(_args):
            raise exc
        p.set_defaults(fn=fn)
        return p
    monkeypatch.setattr(cli, "build_parser", _fake_parser)


def test_main_fuxerror_exits_1_terse(monkeypatch, capsys):
    _patch_main_fn(monkeypatch, FuxError("boom"))
    rc = cli.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert err.strip() == "error: boom"          # terse, no hint, no traceback
    assert "Traceback" not in err


def test_main_keyboardinterrupt_exits_130(monkeypatch, capsys):
    _patch_main_fn(monkeypatch, KeyboardInterrupt())
    rc = cli.main([])
    assert rc == 130
    assert "aborted." in capsys.readouterr().err


def test_main_unexpected_exits_1_with_hint_not_traceback(monkeypatch, capsys):
    monkeypatch.delenv("FUX_DEBUG", raising=False)
    _patch_main_fn(monkeypatch, ValueError("kaboom"))
    rc = cli.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "error: kaboom" in err
    assert "FUX_DEBUG=1" in err                   # the hint
    assert "Traceback" not in err                 # but NOT the raw traceback


def test_main_unexpected_traceback_only_under_debug(monkeypatch, capsys):
    monkeypatch.setenv("FUX_DEBUG", "1")
    _patch_main_fn(monkeypatch, ValueError("kaboom"))
    rc = cli.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "Traceback" in err and "ValueError" in err


# ── read command with no .fux/ → FuxError → clean exit 1 ────────────────────
def test_read_command_without_footprint_exits_1_clean(tmp_path, monkeypatch, capsys):
    empty = tmp_path / "no_fux"
    empty.mkdir()
    monkeypatch.chdir(empty)
    monkeypatch.delenv("FUX_DEBUG", raising=False)
    rc = cli.main(["stats"])
    err = capsys.readouterr().err
    assert rc == 1
    assert err.startswith("error:") and "no .fux/" in err
    assert "Traceback" not in err


def test_why_unknown_rule_is_terse_error_on_stderr(project, monkeypatch, capsys):
    """`fux why <unknown>` raises FuxError → terse `error:` on *stderr*, exit 1 —
    not a `fux: …` line on stdout (fux-lab finding)."""
    monkeypatch.chdir(project)
    monkeypatch.delenv("FUX_DEBUG", raising=False)
    rc = cli.main(["why", "no-such-rule-xyz"])
    cap = capsys.readouterr()
    assert rc == 1
    assert cap.out == ""                                   # nothing on stdout
    assert cap.err.strip() == "error: no rule 'no-such-rule-xyz'"
    assert "Traceback" not in cap.err


@pytest.mark.parametrize("argv, needle", [
    (["explain", "zzz-nonexistent-node"], "no node matches"),
    (["query", "zzzznothingmatches"], "nothing in the graph matches"),
    (["seal"], "pass rule ids or --all"),
    (["candidates", "accept"], "needs a candidate id"),
    (["candidates", "reject", "no-such-candidate"], "no candidate"),
])
def test_expected_failures_are_terse_error_on_stderr(argv, needle, project, monkeypatch, capsys):
    """Named-lookup / usage failures across commands must all obey the contract —
    terse `error:` on stderr, exit 1, nothing on stdout (fux-lab Cycle-1 finding:
    the `why` inconsistency was systemic across path/explain/query/seal/candidates)."""
    monkeypatch.chdir(project)
    monkeypatch.delenv("FUX_DEBUG", raising=False)
    cli.main(["build"])
    capsys.readouterr()
    rc = cli.main(argv)
    cap = capsys.readouterr()
    assert rc == 1, f"{argv} exited {rc}, want 1"
    assert cap.out == "", f"{argv} wrote to stdout: {cap.out!r}"
    assert cap.err.startswith("error: ") and needle in cap.err
    assert "Traceback" not in cap.err


# ── hooks are fail-open (return 0 when the core raises) ─────────────────────
def _no_stdin(monkeypatch):
    """Avoid reading pytest's captured stdin; hand each hook a fixed event."""
    monkeypatch.setattr(hooks, "event", lambda: {})
    monkeypatch.delenv("FUX_DEBUG", raising=False)


def test_session_start_fail_open(project, monkeypatch, capsys):
    _no_stdin(monkeypatch)
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks.context, "run", lambda root: (_ for _ in ()).throw(RuntimeError("x")))
    assert hooks.session_start() == 0
    assert capsys.readouterr().err == ""          # silent to the user without debug


def test_post_tool_use_fail_open(project, monkeypatch):
    _no_stdin(monkeypatch)
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks, "mode_of", lambda root: (_ for _ in ()).throw(RuntimeError("x")))
    assert hooks.post_tool_use() == 0


def test_stop_fail_open(project, monkeypatch):
    _no_stdin(monkeypatch)
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks.config, "load", lambda p: (_ for _ in ()).throw(RuntimeError("x")))
    assert hooks.stop() == 0


def test_session_end_propose_fail_open(project, monkeypatch):
    _no_stdin(monkeypatch)
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks.config, "load", lambda p: (_ for _ in ()).throw(RuntimeError("x")))
    assert hooks.session_end_propose() == 0


def test_user_prompt_recall_fail_open(project, monkeypatch):
    monkeypatch.setattr(hooks, "event", lambda: {"prompt": "hello"})
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks.recall, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.delenv("FUX_DEBUG", raising=False)
    assert hooks.user_prompt_recall() == 0


# ── strict-mode return 2 is NOT swallowed by the fail-open wrapper ──────────
def test_stop_strict_still_returns_2(project, monkeypatch, capsys):
    monkeypatch.setattr(hooks, "event", lambda: {})
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks.config, "load", lambda p: {"mode": "strict"})
    monkeypatch.setattr(hooks.checkmod, "run",
                        lambda root: [Finding("schema", "r1", "bad frontmatter")])
    assert hooks.stop() == 2                       # blocking finding still hard-blocks
    assert "strict" in capsys.readouterr().err


# ── fail-open ≠ fail-silent: FUX_DEBUG surfaces the swallowed exception ─────
def test_fux_debug_surfaces_swallowed_hook_exception(project, monkeypatch, capsys):
    monkeypatch.setattr(hooks, "event", lambda: {})
    monkeypatch.setattr(hooks, "root_of", lambda ev: project)
    monkeypatch.setattr(hooks.context, "run",
                        lambda root: (_ for _ in ()).throw(ValueError("boom")))
    monkeypatch.setenv("FUX_DEBUG", "1")
    assert hooks.session_start() == 0
    err = capsys.readouterr().err
    assert "session_start" in err and "boom" in err and "Traceback" in err


# ── MCP reports isError on malformed input rather than crashing ────────────
def test_mcp_tools_call_malformed_is_error(project):
    # known tool, but the required `id` argument is missing → KeyError inside _call.
    msg = {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
           "params": {"name": "fux_why", "arguments": {}}}
    out = mcpserver._handle(msg)
    assert out["result"]["isError"]
    assert "error" in out["result"]["content"][0]["text"]
