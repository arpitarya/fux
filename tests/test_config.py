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


# -- the config doc is a contract, not prose -------------------------------


def test_documented_config_parses_and_matches_shipped_defaults(tmp_path):
    """`docs/example/TOML.md` claims to show every shipped key with its default.

    Parse the doc's own example and check it against the dataclass defaults, so
    the file cannot quietly drift from the parser it documents.
    """
    from pathlib import Path

    from fux.config import (
        AnswerParams, BM25FParams, GitParams, GraphParams, HybridParams,
        IndexParams, WebParams, load,
    )

    doc = (Path(__file__).parent.parent / "docs" / "example" / "TOML.md").read_text(encoding="utf-8")
    section = doc.split("## Complete as-shipped example")[1]
    block = section.split("```toml", 1)[1].split("```", 1)[0]
    (tmp_path / "fux.toml").write_text(block, encoding="utf-8")

    config = load(tmp_path)
    assert config.bm25f == BM25FParams()
    assert config.answer == AnswerParams()
    assert config.hybrid == HybridParams()
    assert config.graph == GraphParams()
    assert config.index == IndexParams()
    assert config.git == GitParams()
    defaults = WebParams()
    for field in ("max_depth", "same_domain", "attachments", "budget", "delay_s",
                  "max_fetch_kb", "render", "cdp_port", "settle_ms",
                  "max_age_days", "tier"):
        assert getattr(config.web, field) == getattr(defaults, field), field


def test_shipped_keys_are_not_still_in_the_proposed_fence():
    """Keys that ship must sit above the "NOT yet shipped" line, or the doc lies."""
    from pathlib import Path

    doc = (Path(__file__).parent.parent / "docs" / "example" / "TOML.md").read_text(encoding="utf-8")
    # The fenced *example*, not the prose around it — the prose legitimately
    # names shipped tables when explaining that they moved out of the fence.
    section = doc.split("## Proposed extensions — NOT yet shipped")[1]
    example = section.split("```toml", 1)[1].split("```", 1)[0]
    for shipped in ("[index]", "[engine.graph]", "[git]", "format =", "profile ="):
        assert shipped not in example, f"{shipped} ships but is still fenced as proposed"
