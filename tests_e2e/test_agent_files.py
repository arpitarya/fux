"""Agent-file generation through the real CLI: created once, idempotent after."""

from __future__ import annotations

import json

from conftest import run_fux


def test_generation_and_idempotency(project):
    first = run_fux(project, "setup", "-y", "--agents", "--skills", "--hooks").stdout
    assert "created" in first
    for rel in (
        "AGENTS.md",
        ".claude/skills/fux-query/SKILL.md",
        ".claude/skills/fux-ingest/SKILL.md",
        ".claude/settings.json",
        ".kiro/hooks/fux-query.kiro.hook",
    ):
        assert (project / rel).is_file(), rel

    second = run_fux(project, "setup", "-y", "--agents", "--skills", "--hooks").stdout
    assert "created" not in second and "updated" not in second

    settings = json.loads((project / ".claude/settings.json").read_text(encoding="utf-8"))
    commands = [
        h["command"]
        for event in settings["hooks"].values()
        for entry in event
        for h in entry["hooks"]
    ]
    assert "fux hook prompt-submit" in commands and "fux hook session-end" in commands


def test_hook_prompt_submit_end_to_end(ingested):
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "fux", "hook", "prompt-submit"],
        cwd=ingested,
        input=json.dumps({"prompt": "how do I install the widget service"}),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "docs/guide.md" in payload["hookSpecificOutput"]["additionalContext"]
