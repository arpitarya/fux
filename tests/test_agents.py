"""Agent-file generation + hooks: idempotency, managed blocks, fail-open."""

from __future__ import annotations

import io
import json

from fux.agents.generate import MANAGED_END, MANAGED_START, generate_agent_files
from fux.cli import main


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(list(argv))


def test_setup_generates_all_surfaces(tmp_path, monkeypatch, capsys):
    assert run(tmp_path, monkeypatch, "setup", "-y", "--agents", "--skills", "--hooks") == 0
    for rel in (
        "AGENTS.md",
        "CLAUDE.md",
        ".github/copilot-instructions.md",
        ".kiro/steering/fux.md",
        ".claude/skills/fux-query/SKILL.md",
        ".claude/skills/fux-ingest/SKILL.md",
        ".claude/settings.json",
        ".kiro/hooks/fux-query.kiro.hook",
    ):
        assert (tmp_path / rel).is_file(), rel
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert MANAGED_START in agents and 'fux ask "<question>" --json' in agents
    out = capsys.readouterr().out
    assert "created" in out


def test_second_run_all_unchanged(tmp_path, monkeypatch):
    generate_agent_files(tmp_path, agents=True, skills=True, hooks=True)
    second = generate_agent_files(tmp_path, agents=True, skills=True, hooks=True)
    assert {state for _, state in second} == {"unchanged"}


def test_user_edits_outside_block_preserved(tmp_path, monkeypatch):
    (tmp_path / "AGENTS.md").write_text("# My project\n\nMy own rules.\n", encoding="utf-8")
    generate_agent_files(tmp_path, agents=True)
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith("# My project")
    assert "My own rules." in text and MANAGED_END in text

    # mangle the managed block, keep user text; regenerate restores block only
    mangled = text.replace("fux ask", "fux ask BROKEN")
    (tmp_path / "AGENTS.md").write_text(mangled, encoding="utf-8")
    results = generate_agent_files(tmp_path, agents=True)
    assert dict(results)["AGENTS.md"] == "updated"
    restored = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "BROKEN" not in restored and "My own rules." in restored


def test_settings_json_merge_preserves_user_keys(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/settings.json").write_text(
        json.dumps({"model": "opus", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "mine"}]}]}}),
        encoding="utf-8",
    )
    generate_agent_files(tmp_path, hooks=True)
    settings = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert settings["model"] == "opus"
    stop_cmds = [
        h["command"] for entry in settings["hooks"]["Stop"] for h in entry["hooks"]
    ]
    assert "mine" in stop_cmds and "fux hook session-end" in stop_cmds
    assert any(
        h["command"] == "fux hook prompt-submit"
        for entry in settings["hooks"]["UserPromptSubmit"]
        for h in entry["hooks"]
    )


def test_hook_prompt_submit_injects_context(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/deploy.md").write_text(
        "# Deploy\n\nBlue-green rollout with health checks protects cutover.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"prompt": "how does deploy rollout work"})))
    assert run(tmp_path, monkeypatch, "hook", "prompt-submit") == 0
    payload = json.loads(capsys.readouterr().out)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "docs/deploy.md" in ctx and "Blue-green" in ctx


def test_hook_fail_open_on_garbage_stdin(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    assert run(tmp_path, monkeypatch, "hook", "prompt-submit") == 0
    assert capsys.readouterr().out == ""  # quiet, but exit 0 — session unharmed


def test_hook_quiet_without_index(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"prompt": "a long enough prompt"})))
    assert run(tmp_path, monkeypatch, "hook", "prompt-submit") == 0
    assert capsys.readouterr().out == ""


def test_session_end_nudges_when_registry_exists(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/DOC-REGISTRY.md").write_text("# registry\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    assert run(tmp_path, monkeypatch, "hook", "session-end") == 0
    assert "DOC-REGISTRY" in capsys.readouterr().out
