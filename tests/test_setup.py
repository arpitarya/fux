"""Unit suite for `fux setup` (wizard + flags + idempotency)."""

from __future__ import annotations

import tomllib

from fux.cli import main


def run_setup(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(["setup", *argv])


def read_toml(tmp_path):
    return tomllib.loads((tmp_path / "fux.toml").read_text(encoding="utf-8"))


def test_yes_writes_defaults(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    assert run_setup(tmp_path, monkeypatch, "-y") == 0
    data = read_toml(tmp_path)
    assert data["sources"]["docs"] == ["docs"]
    assert data["sources"]["code"] == []
    assert data["engine"]["bm25f"]["heading"] == 3.0
    assert data["ingest"]["max_kb"] == 256
    assert "wrote fux.toml" in capsys.readouterr().out


def test_flags_override_and_comma_split(tmp_path, monkeypatch):
    assert run_setup(tmp_path, monkeypatch, "--docs", "a,b", "--code", "src", "-y") == 0
    data = read_toml(tmp_path)
    assert data["sources"]["docs"] == ["a", "b"]
    assert data["sources"]["code"] == ["src"]


def test_rerun_is_idempotent(tmp_path, monkeypatch, capsys):
    run_setup(tmp_path, monkeypatch, "--docs", "d", "-y")
    first = (tmp_path / "fux.toml").read_bytes()
    capsys.readouterr()
    assert run_setup(tmp_path, monkeypatch, "-y") == 0
    assert (tmp_path / "fux.toml").read_bytes() == first
    assert "unchanged fux.toml" in capsys.readouterr().out


def test_rerun_preserves_user_edits(tmp_path, monkeypatch):
    run_setup(tmp_path, monkeypatch, "--docs", "d", "-y")
    path = tmp_path / "fux.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("max_kb = 256", "max_kb = 32") + "\n[custom]\nmine = true\n",
        encoding="utf-8",
    )
    run_setup(tmp_path, monkeypatch, "-y")
    data = read_toml(tmp_path)
    assert data["ingest"]["max_kb"] == 32  # user tweak survives
    assert data["custom"] == {"mine": True}  # unknown section survives
    assert data["sources"]["docs"] == ["d"]  # prior answers become defaults


def test_wizard_prompts_have_defaults(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    answers = iter(["", "src", "none", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert run_setup(tmp_path, monkeypatch) == 0
    data = read_toml(tmp_path)
    assert data["sources"]["docs"] == ["docs"]  # accepted default
    assert data["sources"]["code"] == ["src"]
    assert data["sources"]["data"] == []  # explicit "none"


def test_non_interactive_stdin_behaves_like_yes(tmp_path, monkeypatch):
    def eof(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert run_setup(tmp_path, monkeypatch) == 0
    assert (tmp_path / "fux.toml").is_file()


# -- .gitignore management (handoff 0004: derived plane never gets committed) --


def test_setup_gitignores_the_runtime_plane(tmp_path, monkeypatch):
    run_setup(tmp_path, monkeypatch, "-y")
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".fux/index/" in text
    # the committed pair must NOT be ignored — git carries recipe and state
    assert "fux.lock" not in text
    assert ".fux/state" not in text


def test_gitignore_write_is_idempotent(tmp_path, monkeypatch):
    run_setup(tmp_path, monkeypatch, "-y")
    first = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    run_setup(tmp_path, monkeypatch, "-y")
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == first


def test_gitignore_appends_and_preserves_user_rules(tmp_path, monkeypatch):
    (tmp_path / ".gitignore").write_text("*.log\nbuild/\n", encoding="utf-8")
    run_setup(tmp_path, monkeypatch, "-y")
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("*.log\nbuild/\n")
    assert ".fux/index/" in text


def test_gitignore_respects_a_broader_existing_rule(tmp_path, monkeypatch):
    (tmp_path / ".gitignore").write_text(".fux/\n", encoding="utf-8")
    run_setup(tmp_path, monkeypatch, "-y")
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == ".fux/\n"
