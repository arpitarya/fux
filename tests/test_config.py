from __future__ import annotations

import pytest

from fux.config import load
from fux.errors import FuxError
from fux.ingest.gitdir import read_dirs, source_dirs


def _write(tmp_path, text):
    (tmp_path / "fux.toml").write_text(text, encoding="utf-8")


def _write_dirs(tmp_path, lines, rel=".fux/sources/dirs"):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def test_loads_minimal_config(tmp_path):
    _write(tmp_path, "[sources]\n")
    config = load(tmp_path)
    assert config.dirs_file == ".fux/sources/dirs"
    assert config.shards == 256


def test_a_config_with_no_sources_table_at_all_is_valid(tmp_path):
    """`fux.toml` is policy: every key in it has a default."""
    _write(tmp_path, "[index]\nshards = 256\n")
    assert load(tmp_path).dirs_file == ".fux/sources/dirs"


def test_shards_defaults_when_omitted(tmp_path):
    _write(tmp_path, "[sources]\n")
    assert load(tmp_path).shards == 256


def test_explicit_matching_shards_ok(tmp_path):
    _write(tmp_path, "[sources]\n[index]\nshards = 256\n")
    assert load(tmp_path).shards == 256


def test_non_256_shards_rejected(tmp_path):
    _write(tmp_path, "[sources]\n[index]\nshards = 16\n")
    with pytest.raises(FuxError, match="must be 256"):
        load(tmp_path)


def test_missing_config_file(tmp_path):
    with pytest.raises(FuxError, match="no fux.toml"):
        load(tmp_path)


def test_invalid_toml(tmp_path):
    _write(tmp_path, "not valid [[[ toml")
    with pytest.raises(FuxError, match="invalid TOML"):
        load(tmp_path)


# -- the retired key (ADR-DIR-LIST decision 1) -----------------------------


def test_the_retired_dirs_key_errors_with_instructions(tmp_path):
    _write(tmp_path, '[sources]\ndirs = ["docs", "README.md"]\n')
    with pytest.raises(FuxError, match=r"\.fux/sources/dirs"):
        load(tmp_path)


def test_an_empty_retired_dirs_key_errors_too(tmp_path):
    """A retired key is retired whatever its value — never a silent no-op."""
    _write(tmp_path, "[sources]\ndirs = []\n")
    with pytest.raises(FuxError, match="is not a TOML key any more"):
        load(tmp_path)


def test_dirs_file_is_configurable(tmp_path):
    _write(tmp_path, '[sources]\ndirs_file = "config/sources"\n')
    assert load(tmp_path).dirs_file == "config/sources"


def test_dirs_file_must_be_a_path(tmp_path):
    _write(tmp_path, "[sources]\ndirs_file = 7\n")
    with pytest.raises(FuxError, match="dirs_file must be a path"):
        load(tmp_path)


# -- the list itself -------------------------------------------------------


def test_the_dirs_list_dedupes_and_sorts(tmp_path):
    _write_dirs(tmp_path, ["work", "# a note", "docs", "", "work"])
    assert source_dirs(tmp_path, ".fux/sources/dirs") == ["docs", "work"]


def test_a_directory_may_declare_itself_archived(tmp_path):
    _write_dirs(tmp_path, ["docs", "old/frozen-docs   archived=true  # retired 2026"])
    entries = {e.value: e.attrs["archived"] for e in read_dirs(tmp_path, ".fux/sources/dirs")}
    assert entries == {"docs": "false", "old/frozen-docs": "true"}


def test_archived_is_declared_and_never_derived_from_the_path(tmp_path):
    """ADR-DIR-LIST decision 4 — the reason it superseded its predecessor."""
    _write_dirs(tmp_path, ["archive/v0.26-docs"])
    (entry,) = read_dirs(tmp_path, ".fux/sources/dirs")
    assert entry.attrs["archived"] == "false"  # the path is a hint, not the signal


def test_a_missing_dirs_list_fails_loudly_naming_setup(tmp_path):
    _write(tmp_path, "[sources]\n")
    with pytest.raises(FuxError, match=r"\.fux/sources/dirs not found.*fux setup"):
        source_dirs(tmp_path, load(tmp_path).dirs_file)
