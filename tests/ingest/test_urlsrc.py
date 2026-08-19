"""URL source (ADR-URL-INGEST, relocated by ADR-DOTFUX): the consumer-fetcher
contract, the committed line-oriented URL list, the opaque config table,
offline-by-default carry-forward, hashed-meta default, and determinism. No
test here touches the network — the fetcher under test is a fake written
into the tmp repo, which is exactly the trust boundary the design draws."""

from __future__ import annotations

import pytest

from fux import store
from fux.config import load as load_config
from fux.errors import FuxError
from fux.ingest.run import run
from fux.ingest.urlsrc import UrlEntry, fetch_all, load_fetcher, read_urls
from fux.store.format import term_hash

FAKE_FETCHER = '''\
CALLS = {"connect": 0, "close": 0, "fetch": []}

def connect():
    CALLS["connect"] += 1

def close():
    CALLS["close"] += 1

def fetch(url):
    CALLS["fetch"].append(url)
    if "boom" in url:
        raise RuntimeError("no such page")
    name = url.rsplit("/", 1)[-1]
    return f"# Page {name}\\n\\nrendered body about {name}\\n"
'''

URLS_FILE = ".fux/sources/urls"


def _urls(tmp_path, rel=URLS_FILE):
    """The URL strings a list parses to — the entries carry attributes now."""
    return [e.value for e in read_urls(tmp_path, rel)]


def _entries(urls, fetcher="mw.py", meta="hashed"):
    """Hand-resolved entries, so `fetch_all` can be exercised without a config."""
    return [UrlEntry(url=u, fetch="mw", meta=meta, fetcher_path=fetcher) for u in urls]


def _write_toml(tmp_path, text, dirs=("docs",)):
    """Write `fux.toml` and the committed directory list it now implies."""
    (tmp_path / "fux.toml").write_text(text, encoding="utf-8")
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("".join(f"{d}{chr(10)}" for d in dirs), encoding="utf-8")


def _write_urls(tmp_path, lines):
    path = tmp_path / URLS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def _init(tmp_path, *, urls, meta=None, files=None, fetcher=FAKE_FETCHER, config=None):
    files = files if files is not None else {"docs/a.md": "# Doc A\n\nrepo body\n"}
    url_lines = '[sources.url]\nfetcher = "mw.py"\n'
    if meta is not None:
        url_lines += f'meta = "{meta}"\n'
    if config is not None:
        url_lines += "[sources.url.config]\n" + config
    _write_toml(tmp_path, "[sources]\n" + url_lines)
    (tmp_path / "mw.py").write_text(fetcher, encoding="utf-8")
    _write_urls(tmp_path, urls)
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


# -- config ----------------------------------------------------------------


def test_config_parses_url_source(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"], meta="plain")
    cfg = load_config(tmp_path)
    assert cfg.url.fetcher == "mw.py"
    assert cfg.url.urls_file == ".fux/sources/urls"
    assert cfg.url.meta == "plain"
    assert cfg.url.config == {}


def test_config_meta_defaults_to_hashed(tmp_path):
    _init(tmp_path, urls=[])
    assert load_config(tmp_path).url.meta == "hashed"


def test_config_paths_default_into_the_fux_dir(tmp_path):
    _write_toml(tmp_path, "[sources]\n[sources.url]\n")
    cfg = load_config(tmp_path)
    # The default is the plain-GET fetcher: a line with no `fetch=` means
    # `fetch=http` (ADR-HTTP-FETCHER decision 1), and this key is the
    # source-wide setting for that attribute.
    assert cfg.url.fetcher == ".fux/fetchers/http.py"
    assert cfg.url.urls_file == ".fux/sources/urls"


def test_config_rejects_bad_meta(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nfetcher = "mw.py"\nmeta = "cleartext"\n'
    )
    with pytest.raises(FuxError, match="meta must be"):
        load_config(tmp_path)


def test_config_rejects_an_inline_urls_list_and_names_the_file(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nurls = ["https://x.test/a"]\n'
    )
    with pytest.raises(FuxError, match=r"\.fux/sources/urls"):
        load_config(tmp_path)


def test_config_table_is_opaque_but_must_be_a_table(tmp_path):
    _init(tmp_path, urls=[], config='cdp_port = 9333\nanything_at_all = "fux never reads this"\n')
    assert load_config(tmp_path).url.config == {"cdp_port": 9333, "anything_at_all": "fux never reads this"}

    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nfetcher = "mw.py"\nconfig = 9222\n'
    )
    with pytest.raises(FuxError, match=r"\[sources.url.config\] must be a table"):
        load_config(tmp_path)


# -- the urls file ---------------------------------------------------------


def test_read_urls_ignores_comments_and_blanks(tmp_path):
    _write_urls(
        tmp_path,
        ["# a heading comment", "", "https://x.test/a  ", "   ", "https://x.test/b # trailing note", "# end"],
    )
    assert _urls(tmp_path) == ["https://x.test/a", "https://x.test/b"]


def test_read_urls_dedupes_and_sorts(tmp_path):
    _write_urls(tmp_path, ["https://x.test/b", "https://x.test/a", "https://x.test/b"])
    assert _urls(tmp_path) == ["https://x.test/a", "https://x.test/b"]


def test_read_urls_rejects_a_non_http_line_with_its_line_number(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a", "# note", "ftp://x.test/c"])
    with pytest.raises(FuxError, match=r"urls:3: not an http\(s\) URL"):
        read_urls(tmp_path, URLS_FILE)


def test_read_urls_empty_file_is_a_valid_zero_url_state(tmp_path):
    _write_urls(tmp_path, [])
    assert _urls(tmp_path) == []


def test_read_urls_missing_file_fails_loudly(tmp_path):
    with pytest.raises(FuxError, match=r"\.fux/sources/urls not found"):
        read_urls(tmp_path, URLS_FILE)


def test_missing_urls_file_only_matters_on_refresh(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    (tmp_path / URLS_FILE).unlink()
    run(tmp_path)  # offline ingest must not care that the list is gone
    with pytest.raises(FuxError, match=r"\.fux/sources/urls not found"):
        run(tmp_path, refresh_urls=True)


# -- fetcher loading ----------------------------------------------------


def test_missing_fetcher_file_fails_loudly(tmp_path):
    with pytest.raises(FuxError, match="fetcher not found"):
        load_fetcher(tmp_path, "nope.py")


def test_fetcher_without_fetch_fails_loudly(tmp_path):
    (tmp_path / "mw.py").write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(FuxError, match="no fetch"):
        load_fetcher(tmp_path, "mw.py")


def test_fetch_all_calls_hooks_once_and_skips_failures(tmp_path):
    (tmp_path / "mw.py").write_text(FAKE_FETCHER, encoding="utf-8")
    fetched, skipped = fetch_all(
        tmp_path, _entries(["https://x.test/b", "https://x.test/boom", "https://x.test/a"])
    )
    assert [f.url for f in fetched] == ["https://x.test/a", "https://x.test/b"]  # sorted, deterministic
    assert [s.rel_path for s in skipped] == ["https://x.test/boom"]
    assert "no such page" in skipped[0].reason
    module = load_fetcher(tmp_path, "mw.py")  # fresh module: counters reset
    assert callable(module.connect) and callable(module.close)


# A fake fetcher records what it saw next to itself — `fetch_all` imports
# the module privately, so its state is only observable through the filesystem.
_RECORDER = 'import pathlib\n_LOG = pathlib.Path(__file__).with_name("log.txt")\n'


def test_config_table_reaches_configure_verbatim(tmp_path):
    (tmp_path / "mw.py").write_text(
        _RECORDER
        + 'def configure(config):\n'
        '    _LOG.write_text(repr(sorted(config.items())))\n'
        'def fetch(url):\n'
        '    return "# T\\n\\nbody\\n"\n',
        encoding="utf-8",
    )
    table = {"cdp_port": 9333, "nested": {"deep": [1, 2]}, "flag": True}
    fetch_all(tmp_path, _entries(["https://x.test/a"]), table)
    assert (tmp_path / "log.txt").read_text(encoding="utf-8") == repr(sorted(table.items()))


def test_configure_is_optional_and_absent_table_is_empty(tmp_path):
    (tmp_path / "mw.py").write_text(
        _RECORDER
        + 'def configure(config):\n'
        '    _LOG.write_text(repr(config))\n'
        'def fetch(url):\n'
        '    return "# T\\n\\nbody\\n"\n',
        encoding="utf-8",
    )
    fetch_all(tmp_path, _entries(["https://x.test/a"]))  # no table passed at all
    assert (tmp_path / "log.txt").read_text(encoding="utf-8") == "{}"

    (tmp_path / "mw.py").write_text('def fetch(url):\n    return "# T\\n\\nbody\\n"\n', encoding="utf-8")
    fetched, _ = fetch_all(tmp_path, _entries(["https://x.test/a"]), {"k": 1})  # no configure defined
    assert len(fetched) == 1


def test_configure_runs_before_connect(tmp_path):
    (tmp_path / "mw.py").write_text(
        _RECORDER
        + 'ORDER = []\n'
        'def configure(config):\n'
        '    ORDER.append("configure")\n'
        'def connect():\n'
        '    ORDER.append("connect")\n'
        'def fetch(url):\n'
        '    _LOG.write_text(",".join(ORDER))\n'
        '    return "# T\\n\\nbody\\n"\n',
        encoding="utf-8",
    )
    fetch_all(tmp_path, _entries(["https://x.test/a"]), {})
    assert (tmp_path / "log.txt").read_text(encoding="utf-8") == "configure,connect"


def test_configure_raising_is_a_loud_failure_not_a_skip(tmp_path):
    (tmp_path / "mw.py").write_text(
        'def configure(config):\n    raise ValueError("unknown key: prot")\n'
        'def fetch(url):\n    return "# T\\n\\nbody\\n"\n',
        encoding="utf-8",
    )
    with pytest.raises(FuxError, match="configure\\(\\) failed: unknown key"):
        fetch_all(tmp_path, _entries(["https://x.test/a"]), {"prot": 1})


def test_fetch_all_sanitizes_hostile_line_separators(tmp_path):
    (tmp_path / "mw.py").write_text(
        'def fetch(url):\n    return "# T\\n\\nbefore\\u2028after \\u2029 \\u0085 end\\n"\n',
        encoding="utf-8",
    )
    fetched, skipped = fetch_all(tmp_path, _entries(["https://x.test/a"]))
    assert skipped == []
    assert b"\xe2\x80\xa8" not in fetched[0].content  # U+2028 gone before the canonical writer


# -- ingest wiring ---------------------------------------------------------


def test_refresh_ingests_urls_with_hashed_meta_default(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    report = run(tmp_path, refresh_urls=True)
    assert report.doc_count == 2
    record = store.read_index(tmp_path)["url:https://x.test/a"]
    assert record["src"] == "url"
    assert record["loc"] == "https://x.test/a"
    assert record["meta"] == "hashed"
    assert record["title_h"] == term_hash("Page a")
    assert "title" not in record and "phrases" not in record  # no display text leaks
    assert term_hash("rendered") in record["terms"]


def test_plain_meta_is_an_explicit_opt_in(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"], meta="plain")
    run(tmp_path, refresh_urls=True)
    record = store.read_index(tmp_path)["url:https://x.test/a"]
    assert record["meta"] == "plain"
    assert record["title"] == "Page a"
    assert record["phrases"] == ["Page a"]


def test_plain_ingest_is_offline_and_carries_urls_forward(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    before = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}

    (tmp_path / "mw.py").write_text("def fetch(url):\n    raise AssertionError('network on offline run')\n", encoding="utf-8")
    report = run(tmp_path)  # no flag: must not import or call the fetcher
    after = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}
    assert before == after
    assert report.changed_count == 0


def test_double_refresh_is_byte_identical(tmp_path):
    _init(tmp_path, urls=["https://x.test/a", "https://x.test/b"])
    run(tmp_path, refresh_urls=True)
    before = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}
    report = run(tmp_path, refresh_urls=True)
    after = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}
    assert before == after
    assert report.changed_count == 0


def test_failed_refresh_keeps_prior_record(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    prior = store.read_index(tmp_path)["url:https://x.test/a"]

    (tmp_path / "mw.py").write_text("def fetch(url):\n    raise RuntimeError('site down')\n", encoding="utf-8")
    report = run(tmp_path, refresh_urls=True)
    assert store.read_index(tmp_path)["url:https://x.test/a"] == prior
    assert any("site down" in s.reason for s in report.skipped)


def test_deconfigured_url_disappears_on_refresh_only(tmp_path):
    _init(tmp_path, urls=["https://x.test/a", "https://x.test/b"])
    run(tmp_path, refresh_urls=True)

    _init(tmp_path, urls=["https://x.test/a"])  # b removed from config
    run(tmp_path)  # offline run: b survives
    assert "url:https://x.test/b" in store.read_index(tmp_path)
    run(tmp_path, refresh_urls=True)  # reconciling run: b is gone
    assert "url:https://x.test/b" not in store.read_index(tmp_path)


def test_ver_bumps_when_fetched_content_changes(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    assert store.read_index(tmp_path)["url:https://x.test/a"]["ver"] == 1

    (tmp_path / "mw.py").write_text('def fetch(url):\n    return "# Page a\\n\\nnew body\\n"\n', encoding="utf-8")
    run(tmp_path, refresh_urls=True)
    assert store.read_index(tmp_path)["url:https://x.test/a"]["ver"] == 2


def test_refresh_without_url_config_fails_loudly(tmp_path):
    _write_toml(tmp_path, "[sources]\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    with pytest.raises(FuxError, match="no \\[sources.url\\]"):
        run(tmp_path, refresh_urls=True)


def test_file_doc_gets_ref_edge_to_ingested_url(tmp_path):
    _init(
        tmp_path,
        urls=["https://x.test/a"],
        files={"docs/a.md": "# Doc A\n\nsee [the page](https://x.test/a) and [gone](https://x.test/other)\n"},
    )
    run(tmp_path, refresh_urls=True)
    edges = store.read_index(tmp_path)["file:docs/a.md"]["edges"]
    assert {"kind": "ref", "dst": "url:https://x.test/a", "grade": 10} in edges
    assert not any(e["dst"] == "url:https://x.test/other" for e in edges)  # dangling stays dropped


# -- the attribute grammar, per URL (ADR-URL-LIST decisions 7-13) ----------


def test_a_fragment_survives_the_round_trip(tmp_path):
    """W-49: `#` is a comment only at line start or after whitespace."""
    _write_urls(tmp_path, ["https://x.test/page#section"])
    assert _urls(tmp_path) == ["https://x.test/page#section"]


def test_two_urls_differing_only_by_fragment_are_two_entries(tmp_path):
    _write_urls(tmp_path, ["https://x.test/p#a", "https://x.test/p#b", "https://x.test/p"])
    assert _urls(tmp_path) == ["https://x.test/p", "https://x.test/p#a", "https://x.test/p#b"]


def test_a_fragment_bearing_line_can_still_carry_attributes(tmp_path):
    _write_urls(tmp_path, ["https://x.test/p#frag meta=plain  # public"])
    (entry,) = read_urls(tmp_path, URLS_FILE)
    assert entry.value == "https://x.test/p#frag"
    assert entry.attrs["meta"] == "plain"


def test_an_unknown_attribute_errors_at_file_lineno(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a", "https://x.test/b mata=plain"])
    with pytest.raises(FuxError, match=r"urls:2: unknown attribute 'mata'"):
        read_urls(tmp_path, URLS_FILE)


def test_an_unknown_attribute_value_errors_at_file_lineno(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a meta=cleartext"])
    with pytest.raises(FuxError, match=r"urls:1: meta='cleartext' is not one of"):
        read_urls(tmp_path, URLS_FILE)


def test_a_duplicate_with_conflicting_attributes_names_both_lines(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a meta=plain", "# note", "https://x.test/a fetch=cdp"])
    with pytest.raises(FuxError, match=r"urls:1 and .*urls:3"):
        read_urls(tmp_path, URLS_FILE)


def test_a_duplicate_that_agrees_is_a_merge_artefact_not_an_error(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a meta=hashed", "https://x.test/a"])
    (entry,) = read_urls(tmp_path, URLS_FILE)
    assert entry.attrs["meta"] == "hashed"  # absent means the default; they agree


def test_file_order_does_not_change_the_parsed_set(tmp_path):
    lines = ["https://x.test/c fetch=cdp", "https://x.test/a", "https://x.test/b meta=plain"]
    _write_urls(tmp_path, lines)
    forward = read_urls(tmp_path, URLS_FILE)
    _write_urls(tmp_path, list(reversed(lines)))
    assert [(e.value, e.attrs) for e in forward] == [
        (e.value, e.attrs) for e in read_urls(tmp_path, URLS_FILE)
    ]


def test_a_line_attribute_beats_the_source_wide_setting(tmp_path):
    """Decision 10: `meta` only ever loosens, and only for its own URL."""
    _init(tmp_path, urls=["https://x.test/a meta=plain", "https://x.test/b"])
    run(tmp_path, refresh_urls=True)
    index = store.read_index(tmp_path)
    assert index["url:https://x.test/a"]["meta"] == "plain"
    assert index["url:https://x.test/a"]["title"] == "Page a"
    assert index["url:https://x.test/b"]["meta"] == "hashed"  # the source-wide floor holds

CDP_FETCHER = """
def fetch(url):
    return "# Rendered" + chr(10) * 2 + "browser fetcher body" + chr(10)
"""


def test_fetch_routes_per_line_and_only_loads_what_it_needs(tmp_path):
    """`fetch=` picks a file in the fetcher directory; nothing else is imported."""
    _init(tmp_path, urls=["https://x.test/a", "https://x.test/b fetch=cdp"])
    (tmp_path / "cdp.py").write_text(CDP_FETCHER, encoding="utf-8")
    (tmp_path / "http.py").write_text(  # named by no line: must never be imported
        "raise AssertionError('a fetcher no line names must never be imported')",
        encoding="utf-8",
    )
    run(tmp_path, refresh_urls=True)
    index = store.read_index(tmp_path)
    assert index["url:https://x.test/a"]["title_h"] == term_hash("Page a")
    assert index["url:https://x.test/b"]["title_h"] == term_hash("Rendered")


def test_a_missing_fetcher_names_setup(tmp_path):
    _init(tmp_path, urls=["https://x.test/a fetch=cdp"])
    with pytest.raises(FuxError, match=r"fetcher not found: cdp\.py.*fux setup"):
        run(tmp_path, refresh_urls=True)
