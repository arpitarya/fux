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


# -- the ranking keys left this file (ADR-TUNE decision 7) ------------------
#
# `[ranking]` and `[dense]` moved to `.fux/tune.toml` on 2026-08-24. Their
# validation moved with them (`tests/test_tune.py`); what stays here is the
# refusal, because a silently ignored key is worse than one that errors — the
# reader believes their setting is in force. Same shape as the
# `middleware` -> `fetcher` rename below.


def test_a_retired_ranking_table_names_its_new_home(tmp_path):
    _write(tmp_path, "[sources]\n[ranking]\narchived_weight = 0.5\n")
    with pytest.raises(FuxError, match=r"\[ranking\] moved to \.fux/tune\.toml"):
        load(tmp_path)


def test_a_dense_table_names_its_REMOVAL_not_a_forwarding_address(tmp_path):
    """`[dense]` was retired twice, and the second time it stopped existing.

    2026-08-24 moved it to `tune.toml`; 2026-08-25 deleted the lane outright.
    A `fux.toml` old enough to still carry it would otherwise be forwarded to a
    table that is also gone, which is a worse answer than no answer.
    """
    _write(tmp_path, '[sources]\n[dense]\nmode = "gated"\n')
    with pytest.raises(FuxError, match="REMOVED on 2026-08-25"):
        load(tmp_path)


def test_an_empty_retired_table_is_refused_too(tmp_path):
    """An empty `[ranking]` is still a reader believing this file ranks.

    Refusing only tables that carry keys would let `[ranking]` sit in a
    consumer's config forever, silently doing nothing, which is the exact
    outcome the retirement exists to prevent.
    """
    _write(tmp_path, "[sources]\n[ranking]\n")
    with pytest.raises(FuxError, match=r"\[ranking\] moved to \.fux/tune\.toml"):
        load(tmp_path)


def test_config_no_longer_carries_the_ranking_fields(tmp_path):
    """The fields are gone, not merely unread — two homes is decision 1's rot."""
    _write(tmp_path, "[sources]\n")
    config = load(tmp_path)
    for gone in ("archived_weight", "superseded_weight", "dense_mode", "rerank_weight"):
        assert not hasattr(config, gone), f"{gone} should have moved to tune.toml"


# -- the archived directory set (ADR-ARCHIVED-CONTENT decision 6's input) ---------


def test_archived_dirs_is_only_the_declared_ones(tmp_path):
    from fux.ingest.gitdir import archived_dirs

    _write_dirs(tmp_path, ["docs", "old/frozen-docs archived=true"])
    assert archived_dirs(tmp_path, ".fux/sources/dirs") == ["old/frozen-docs"]


def test_archived_dirs_excludes_exclusion_lines(tmp_path):
    from fux.ingest.gitdir import archived_dirs

    _write_dirs(tmp_path, ["old archived=true", "!old/keep"])
    assert archived_dirs(tmp_path, ".fux/sources/dirs") == ["old"]


# -- [sources.url] acquired_max_bytes (ADR-CONFIG decision 12) --------------
#
# ⚠ **This key was DOCUMENTED before it was parsed.** ADR-ACQUIRED decision 8
# named it and the ownership table gave it to `config.py`, while `config.py`
# never read it and `urlsrc.fetch_all` reached for it through an undefined
# name -- a `NameError` on every retaining fetch. These tests are the gate on
# the parse half; `tests/ingest/test_urlsrc.py` covers the use half.

_URL_SOURCE = '[sources]\n[sources.url]\nmax_parallel = 4\n'


def test_acquired_max_bytes_defaults_to_none_not_to_a_number(tmp_path):
    """`None` defers to the store's own default rather than freezing today's
    constant into every repo that never thought about the question."""
    _write(tmp_path, _URL_SOURCE)
    assert load(tmp_path).url.acquired_max_bytes is None


def test_acquired_max_bytes_is_read_when_stated(tmp_path):
    _write(tmp_path, _URL_SOURCE + "acquired_max_bytes = 1048576\n")
    assert load(tmp_path).url.acquired_max_bytes == 1048576


def test_acquired_max_bytes_refuses_a_bool_and_a_non_integer(tmp_path):
    # `bool` is an `int` subclass, so `true` would otherwise parse as 1 -- a
    # one-byte cap that evicts the entire store. Same trap as decision 11.
    _write(tmp_path, _URL_SOURCE + "acquired_max_bytes = true\n")
    with pytest.raises(FuxError, match="acquired_max_bytes must be an integer"):
        load(tmp_path)
    _write(tmp_path, _URL_SOURCE + 'acquired_max_bytes = "2GB"\n')
    with pytest.raises(FuxError, match="acquired_max_bytes must be an integer"):
        load(tmp_path)


def test_acquired_max_bytes_refuses_zero_and_points_at_the_real_knob(tmp_path):
    """Retaining nothing is `keep = false`, not a zero-byte store."""
    _write(tmp_path, _URL_SOURCE + "acquired_max_bytes = 0\n")
    with pytest.raises(FuxError, match="keep = false"):
        load(tmp_path)
