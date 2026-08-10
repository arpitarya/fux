from __future__ import annotations

import pytest

from fux.config import load
from fux.errors import FuxError


def _write(tmp_path, text):
    (tmp_path / "fux.toml").write_text(text, encoding="utf-8")


def test_loads_minimal_config(tmp_path):
    _write(tmp_path, '[sources]\ndirs = ["docs", "README.md"]\n')
    config = load(tmp_path)
    assert config.source_dirs == ["docs", "README.md"]
    assert config.shards == 256


def test_shards_defaults_when_omitted(tmp_path):
    _write(tmp_path, '[sources]\ndirs = ["docs"]\n')
    assert load(tmp_path).shards == 256


def test_explicit_matching_shards_ok(tmp_path):
    _write(tmp_path, '[sources]\ndirs = ["docs"]\n[index]\nshards = 256\n')
    assert load(tmp_path).shards == 256


def test_non_256_shards_rejected(tmp_path):
    _write(tmp_path, '[sources]\ndirs = ["docs"]\n[index]\nshards = 16\n')
    with pytest.raises(FuxError, match="must be 256"):
        load(tmp_path)


def test_missing_config_file(tmp_path):
    with pytest.raises(FuxError, match="no fux.toml"):
        load(tmp_path)


def test_missing_sources_dirs(tmp_path):
    _write(tmp_path, "[index]\nshards = 256\n")
    with pytest.raises(FuxError, match="dirs must be"):
        load(tmp_path)


def test_empty_sources_dirs_rejected(tmp_path):
    _write(tmp_path, "[sources]\ndirs = []\n")
    with pytest.raises(FuxError, match="dirs must be"):
        load(tmp_path)


def test_invalid_toml(tmp_path):
    _write(tmp_path, "not valid [[[ toml")
    with pytest.raises(FuxError, match="invalid TOML"):
        load(tmp_path)
