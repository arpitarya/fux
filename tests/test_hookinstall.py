"""`fux hooks install` wires git + claude + codex + copilot from one command,
always pointing at packaged scripts, idempotent, with status/uninstall mirrors."""
from __future__ import annotations

import json
import subprocess

from fux import hookinstall, settings


def _git_init(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)


def test_install_wires_all_three_agents(project):
    out = hookinstall.install(project, ["claude", "codex", "copilot"])
    for agent, rel in settings.AGENT_FILES.items():
        path = project / rel
        assert path.exists(), f"{agent} settings not written"
        hooks = json.loads(path.read_text())["hooks"]
        cmds = [h["command"] for evs in hooks.values() for e in evs for h in e["hooks"]]
        assert any("fux" in c for c in cmds), f"{agent} has no fux hook"
    assert set(out) == {"claude", "codex", "copilot"}


def test_install_is_idempotent(project):
    hookinstall.install(project, ["claude"])
    hookinstall.install(project, ["claude"])
    hooks = json.loads((project / ".claude/settings.json").read_text())["hooks"]
    # SessionStart wired exactly once, not duplicated on a second install.
    assert len(hooks["SessionStart"]) == 1


def test_git_install_writes_executable_precommit_shim(project):
    _git_init(project)
    out = hookinstall.install(project, ["git"])
    hook = project / ".git" / "hooks" / "pre-commit"
    assert hook.exists() and hook.stat().st_mode & 0o111, "pre-commit not executable"
    body = hook.read_text()
    assert "fux-hook" in body                       # our marker
    assert "pre_commit.sh" in body                  # delegates to the packaged script
    assert str(hook) in out["git"]


def test_git_install_backs_up_foreign_precommit(project):
    _git_init(project)
    hook = project / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho mine\n")
    hookinstall.install(project, ["git"])
    assert (project / ".git" / "hooks" / "pre-commit.pre-fux").exists()
    assert "fux-hook" in hook.read_text()


def test_status_and_uninstall_roundtrip(project):
    _git_init(project)
    hookinstall.install(project)
    st = hookinstall.status(project)
    assert all(st.values()), st
    hookinstall.uninstall(project)
    st2 = hookinstall.status(project)
    assert not any(st2.values()), st2


def test_uninstall_leaves_foreign_hooks(project):
    settings.wire_file(project / ".claude/settings.json")
    data = json.loads((project / ".claude/settings.json").read_text())
    data["hooks"].setdefault("SessionStart", [])[0]  # fux entry exists
    data["hooks"]["Stop"].append({"hooks": [{"type": "command", "command": "echo other"}]})
    (project / ".claude/settings.json").write_text(json.dumps(data))
    hookinstall.uninstall(project, ["claude"])
    hooks = json.loads((project / ".claude/settings.json").read_text())["hooks"]
    cmds = [h["command"] for evs in hooks.values() for e in evs for h in e["hooks"]]
    assert "echo other" in cmds and not any("fux" in c for c in cmds)
