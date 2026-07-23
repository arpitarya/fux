"""`[answer] min_confidence` — the absolute honest-decline floor (handoff 0006 M4).

The floor sits above the pre-existing empty-pool early return (which stays —
see CLAUDE.md's phase-4 note): it catches a *non-empty but weak* pool, the
shape of a fluent out-of-scope question that shares just enough vocabulary to
survive relative admission.
"""

from __future__ import annotations

import json

import pytest

from fux.cli import main
from fux.config import load
from fux.errors import FuxError


def make_corpus(tmp_path, min_confidence: float | None = None):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "deploy.md").write_text(
        "# Deploy\n\n## Rollout\n\n"
        "The deploy uses a blue-green rollout with health checks before cutover.\n"
        "Rollbacks complete within two minutes when checks fail.\n",
        encoding="utf-8",
    )
    toml = '[sources]\ndocs = ["docs"]\n'
    if min_confidence is not None:
        toml += f"\n[answer]\nmin_confidence = {min_confidence}\n"
    (tmp_path / "fux.toml").write_text(toml, encoding="utf-8")


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(list(argv))


# -- config validation ------------------------------------------------------


def test_default_is_disabled(tmp_path):
    make_corpus(tmp_path)
    assert load(tmp_path).answer.min_confidence == 0.0


def test_configured_value_is_read(tmp_path):
    make_corpus(tmp_path, min_confidence=0.3)
    assert load(tmp_path).answer.min_confidence == 0.3


def test_negative_value_rejected(tmp_path):
    make_corpus(tmp_path, min_confidence=-0.1)
    with pytest.raises(FuxError, match="min_confidence"):
        load(tmp_path)


def test_value_above_one_rejected(tmp_path):
    make_corpus(tmp_path, min_confidence=1.5)
    with pytest.raises(FuxError, match="min_confidence"):
        load(tmp_path)


def test_non_numeric_value_rejected(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\ntext\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n\n[answer]\nmin_confidence = "high"\n', encoding="utf-8",
    )
    with pytest.raises(FuxError, match="min_confidence"):
        load(tmp_path)


# -- decline behavior --------------------------------------------------------


def test_disabled_floor_does_not_change_a_correct_answer(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)  # min_confidence unset -> 0.0 -> disabled
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "answer", "how fast are rollbacks") == 0
    assert "two minutes" in capsys.readouterr().out


def test_absurdly_high_floor_declines_everything(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path, min_confidence=0.999)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "answer", "how fast are rollbacks") == 0
    out = capsys.readouterr().out
    assert "No confident answer" in out


def test_absurdly_high_floor_declines_in_json_too(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path, min_confidence=0.999)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "answer", "how fast are rollbacks", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["answer"] is None
    assert payload["sentences"] == [] and payload["sources"] == []


def test_zero_floor_never_declines_beyond_the_empty_pool_case(tmp_path, monkeypatch, capsys):
    """0.0 is the disabled sentinel: it must never trigger the new decline path
    (the `floor > 0.0` guard), only the pre-existing empty-candidate one."""
    make_corpus(tmp_path, min_confidence=0.0)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "answer", "how fast are rollbacks") == 0
    assert "two minutes" in capsys.readouterr().out
