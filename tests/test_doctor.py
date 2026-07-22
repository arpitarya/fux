"""Unit suite for `fux doctor` (handoff 0005 §C)."""

from __future__ import annotations

import json

import pytest

from fux import doctor
from fux.config import CONFIG_NAME


def write_toml(root, text):
    (root / CONFIG_NAME).write_text(text, encoding="utf-8")


def test_no_config_reports_failing_config_group(tmp_path):
    groups = doctor.run(tmp_path)
    names = [g.name for g in groups]
    assert names == ["environment", "capabilities", "config"]
    config = next(g for g in groups if g.name == "config")
    assert not config.ok
    check = config.checks[0]
    assert check.name == "fux.toml"
    assert not check.ok
    assert "fux setup" in check.fix


def test_environment_group_reports_version_and_python(tmp_path):
    groups = doctor.run(tmp_path)
    env = groups[0]
    assert env.ok
    names = {c.name for c in env.checks}
    assert {"fux version", "python version", "install path", "bundled model"} <= names


def test_capabilities_never_fail_health(tmp_path):
    groups = doctor.run(tmp_path)
    caps = groups[1]
    assert caps.ok  # optional deps never make doctor unhealthy
    assert all(c.ok for c in caps.checks)


def test_zero_match_source_glob_flagged(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a\ncontent\n", encoding="utf-8")
    (tmp_path / "empty").mkdir()
    write_toml(tmp_path, '[sources]\ndocs = ["docs", "empty"]\n')
    groups = doctor.run(tmp_path)
    config = next(g for g in groups if g.name == "config")
    assert not config.ok
    bad = next(c for c in config.checks if "empty" in c.name)
    assert not bad.ok
    assert "0 files" in bad.detail
    assert "fux.toml" in bad.fix


def test_missing_source_dir_flagged(tmp_path):
    write_toml(tmp_path, '[sources]\ndocs = ["does-not-exist"]\n')
    groups = doctor.run(tmp_path)
    config = next(g for g in groups if g.name == "config")
    assert not config.ok
    bad = next(c for c in config.checks if "does-not-exist" in c.name)
    assert not bad.ok
    assert "does not exist" in bad.detail


def test_no_sources_configured_flagged(tmp_path):
    write_toml(tmp_path, "[sources]\n")
    groups = doctor.run(tmp_path)
    config = next(g for g in groups if g.name == "config")
    assert not config.ok
    assert any(c.name == "[sources]" and not c.ok for c in config.checks)


def _ingested(tmp_path, run_fux_lib):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# Hi\nwidget content\n", encoding="utf-8")
    write_toml(tmp_path, '[sources]\ndocs = ["docs"]\n')
    from fux.config import load
    from fux.ingest import ingest_paths

    ingest_paths(load(tmp_path))


def test_healthy_ingested_corpus(tmp_path):
    _ingested(tmp_path, None)
    groups = doctor.run(tmp_path)
    assert all(g.ok for g in groups)
    names = [g.name for g in groups]
    assert names == [
        "environment", "capabilities", "config", "corpus",
        "consistency", "agent surface", "self-test",
    ]


def test_drift_detected(tmp_path):
    _ingested(tmp_path, None)
    (tmp_path / "docs" / "a.md").write_text("# Hi\nchanged content\n", encoding="utf-8")
    groups = doctor.run(tmp_path)
    consistency = next(g for g in groups if g.name == "consistency")
    assert not consistency.ok
    drift = next(c for c in consistency.checks if c.name.startswith("drift"))
    assert not drift.ok
    assert "1 drifted" in drift.detail


def test_missing_lock_flagged(tmp_path):
    _ingested(tmp_path, None)
    (tmp_path / "fux.lock").unlink()
    groups = doctor.run(tmp_path)
    corpus = next(g for g in groups if g.name == "corpus")
    assert not corpus.ok
    lock_check = next(c for c in corpus.checks if c.name == "fux.lock")
    assert not lock_check.ok


def test_missing_model_bundle_is_not_a_failure(tmp_path, monkeypatch):
    from fux.embed import model as model_mod

    monkeypatch.setattr(model_mod, "DATA_PATH", tmp_path / "no-such-model.bin")
    check = doctor._bundled_model_check()
    assert check.ok
    assert "not bundled" in check.detail


def test_corrupt_model_bundle_sha_mismatch_flagged(tmp_path, monkeypatch):
    import json as jsonlib

    from fux.embed import model as model_mod

    bin_path = tmp_path / "model.bin"
    bin_path.write_bytes(b"not the real model bytes")
    (tmp_path / "model.json").write_text(
        jsonlib.dumps({"sha256": "0" * 64}), encoding="utf-8"
    )
    monkeypatch.setattr(model_mod, "DATA_PATH", bin_path)
    check = doctor._bundled_model_check()
    assert not check.ok
    assert "tools/distill" in check.fix


def test_self_test_passes_on_healthy_corpus(tmp_path):
    _ingested(tmp_path, None)
    groups = doctor.run(tmp_path)
    self_test = next(g for g in groups if g.name == "self-test")
    assert self_test.ok


# -- CLI: cmd_doctor / --json / exit codes ------------------------------------


class _Args:
    def __init__(self, json_out=False):
        self.json = json_out


def test_cmd_doctor_exit_codes(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert doctor.cmd_doctor(_Args()) == 1  # no fux.toml
    out, _ = capsys.readouterr()
    assert "FAIL" in out

    _ingested(tmp_path, None)
    assert doctor.cmd_doctor(_Args()) == 0
    out, _ = capsys.readouterr()
    assert "healthy" in out


def test_cmd_doctor_json_shape(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _ingested(tmp_path, None)
    code = doctor.cmd_doctor(_Args(json_out=True))
    assert code == 0
    out, err = capsys.readouterr()
    assert err == ""
    payload = json.loads(out)
    assert payload["healthy"] is True
    assert {g["name"] for g in payload["groups"]} == {
        "environment", "capabilities", "config", "corpus",
        "consistency", "agent surface", "self-test",
    }
