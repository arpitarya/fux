"""W-225 stage 3b — `fux.toml` is required key by key (SR-CONFIG decision 17).

What these hold that no other file does: the writer's two table rules. `fux
doctor --fix` must never ADD `[sources.url]` — its presence switches fetching on
— and must never touch `[sources.url.config]`, which belongs to the consumer's
fetchers. And the loader names every missing key in one pass, so a consumer
upgrading an old file runs one command, not one per key.
"""

from __future__ import annotations

import re
import tomllib

import pytest

from fux import setup as setup_mod
from fux.config import load
from fux.errors import FuxError


def _without_url_tables(text: str) -> str:
    """The template with every `[sources.url…]` table removed."""
    return re.sub(r"(?ms)^\[sources\.url[^\n]*\n.*?(?=^\[(?!sources\.url))", "", text)


def test_the_fixer_never_switches_fetching_on(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    changed = setup_mod.fill_missing(tmp_path)
    text = (tmp_path / "fux.toml").read_text(encoding="utf-8")
    assert "[sources.url" not in text
    assert not any("sources.url" in line for line in changed)
    assert load(tmp_path).url is None


def test_the_fixer_fills_a_present_url_table_and_leaves_the_fetchers_map_alone(tmp_path):
    (tmp_path / "fux.toml").write_text(
        "[sources]\n[sources.url]\nmax_parallel = 2\n\n[sources.url.config.http]\ntimeout_s = 5.0\n",
        encoding="utf-8",
    )
    setup_mod.fill_missing(tmp_path)
    data = tomllib.loads((tmp_path / "fux.toml").read_text(encoding="utf-8"))
    shipped = setup_mod.template_config()["sources"]["url"]
    assert data["sources"]["url"]["max_parallel"] == 2, "a key the consumer set is never changed"
    for key in ("keep", "ttl", "sweep_minutes", "acquired_max_bytes"):
        assert data["sources"]["url"][key] == shipped[key]
    assert data["sources"]["url"]["config"] == {"http": {"timeout_s": 5.0}}
    assert "cdp" not in data["sources"]["url"]["config"], "the fetcher tables are never written into"


def test_a_missing_key_lands_after_its_tables_last_key_not_in_the_next_tables_prose(tmp_path):
    """The comment above `[sources.url.config]` belongs to that header; inserting
    above the header put `[sources.url]` keys inside it (found on this repo)."""
    (tmp_path / "fux.toml").write_text(
        "[sources.url]\nmax_parallel = 2\n\n# about the next table\n[sources.url.config]\n",
        encoding="utf-8",
    )
    setup_mod.fill_missing(tmp_path)
    text = (tmp_path / "fux.toml").read_text(encoding="utf-8")
    assert text.index("sweep_minutes") < text.index("# about the next table")


def test_every_missing_key_is_named_in_one_error(tmp_path):
    (tmp_path / "fux.toml").write_text(_without_url_tables(setup_mod.config_text()).replace(
        "[observe]\nmax_ms = 50\n", ""
    ).replace("urls_file", "#urls_file"), encoding="utf-8")
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    message = str(exc.value)
    assert "[sources] urls_file is missing" in message
    assert "[observe] max_ms is missing" in message
    assert "fux doctor --fix" in message


def test_the_template_is_the_one_home_of_every_value(tmp_path):
    """No `{default}` substitution is left: every value is typed in the template,
    and a fresh repo loads exactly what it states."""
    shipped = setup_mod.template_bytes(setup_mod.CONFIG_TEMPLATE).decode("utf-8")
    assert "{default}" not in shipped
    (tmp_path / "fux.toml").write_text(setup_mod.config_text(), encoding="utf-8")
    config = load(tmp_path)
    url = setup_mod.template_config()["sources"]["url"]
    assert (config.url.max_parallel, config.url.sweep_minutes, config.url.acquired_max_bytes) == (
        url["max_parallel"],
        url["sweep_minutes"],
        url["acquired_max_bytes"],
    )
