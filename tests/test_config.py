"""Unit suite for fux.toml loading/validation."""

from __future__ import annotations

import pytest

from fux.config import CONFIG_NAME, Config, find_root, load
from fux.errors import FuxError


def write(tmp_path, text):
    (tmp_path / CONFIG_NAME).write_text(text, encoding="utf-8")


def test_missing_config_points_to_setup(tmp_path):
    with pytest.raises(FuxError, match="fux setup"):
        load(tmp_path)


def test_find_root_walks_up(tmp_path):
    write(tmp_path, "[sources]\ndocs = []\n")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert find_root(nested) == tmp_path.resolve()


def test_find_root_missing_mentions_setup(tmp_path):
    with pytest.raises(FuxError, match="fux setup"):
        find_root(tmp_path)


def test_defaults(tmp_path):
    write(tmp_path, '[sources]\ndocs = ["docs"]\n')
    cfg = load(tmp_path)
    assert cfg.sources == {"docs": ("docs",)}
    assert cfg.bm25f.heading == 3.0 and cfg.bm25f.k1 == 1.2 and cfg.bm25f.b == 0.75
    assert cfg.ingest.max_kb == 256
    assert cfg.answer.max_sentences == 5


def test_overrides(tmp_path):
    write(
        tmp_path,
        '[sources]\ndocs = ["d1", "d2"]\ncode = ["src"]\n'
        "[ingest]\nmax_kb = 64\n"
        "[engine.bm25f]\nheading = 5.0\nb = 0.5\n"
        "[answer]\nmax_sentences = 3\n",
    )
    cfg = load(tmp_path)
    assert cfg.sources["docs"] == ("d1", "d2")
    assert cfg.bm25f.heading == 5.0 and cfg.bm25f.b == 0.5
    assert cfg.ingest.max_kb == 64
    assert cfg.answer.max_sentences == 3


def test_unknown_source_type_rejected(tmp_path):
    write(tmp_path, '[sources]\nvideos = ["v"]\n')
    with pytest.raises(FuxError, match="unknown source type 'videos'"):
        load(tmp_path)


@pytest.mark.parametrize(
    "body, match",
    [
        ('[sources]\ndocs = "not-a-list"\n', "list of directory"),
        ("[ingest]\nmax_kb = 0\n", "max_kb"),
        ("[ingest]\nmax_kb = true\n", "max_kb"),
        ("[engine.bm25f]\nk1 = -1\n", "k1"),
        ("[engine.bm25f]\nb = 2.0\n", "b must be between"),
        ("[answer]\nmax_sentences = 0\n", "max_sentences"),
    ],
)
def test_invalid_values_rejected(tmp_path, body, match):
    write(tmp_path, body)
    with pytest.raises(FuxError, match=match):
        load(tmp_path)


def test_invalid_toml_rendered_clearly(tmp_path):
    write(tmp_path, "not toml ===")
    with pytest.raises(FuxError, match="not valid TOML"):
        load(tmp_path)


def test_unknown_tables_ignored(tmp_path):
    write(tmp_path, "[sources]\ndocs = []\n[future_section]\nx = 1\n")
    cfg = load(tmp_path)
    assert isinstance(cfg, Config)
    assert cfg.raw["future_section"] == {"x": 1}
