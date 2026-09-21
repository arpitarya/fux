"""URL source (SR-URL-INGEST, relocated by SR-DOTFUX): the consumer-fetcher
contract, the committed line-oriented URL list, the opaque config table,
offline-by-default carry-forward, and determinism. No
test here touches the network — the fetcher under test is a fake written
into the tmp repo, which is exactly the trust boundary the design draws."""

from __future__ import annotations

import pytest

from fux import store
from fux.config import load as load_config
from fux.errors import FuxError
from fux.ingest.run import run
from fux.ingest.urlsrc import UrlEntry, fetch_all, load_fetcher, read_urls
from fux.query.tokenize import tokenize
from fux.store.format import term_hash


def _write_fetcher(root, text, name="mw.py", encoding="utf-8"):
    """Write a fixture fetcher where the resolver looks for it.

    ⚠ **`.fux/fetchers/` is the only place now.** Until 2026-09-20 a fixture
    could put a fetcher anywhere and point `[sources.url] fetcher` at it; that
    key is deleted (W-199 D2) and the directory is fixed, so the fixture creates
    it rather than relying on `fux setup` having run.
    """
    path = root / ".fux" / "fetchers" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


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


def _entries(urls, fetcher=".fux/fetchers/mw.py", decoder="prose"):
    """Hand-resolved entries, so `fetch_all` can be exercised without a config.

    ⚠ **`fetcher_path` is a PATH and `fetch` is a stem.** They were both `mw.py`
    while the fetchers directory was wherever `[sources.url] fetcher` pointed;
    since 2026-09-20 the directory is fixed at `.fux/fetchers/` and a stem
    resolves against it, so the two are different strings and the default here
    is the path `fetcher_for("mw")` would produce.
    """
    return [
        UrlEntry(url=u, fetch="mw", fetcher_path=fetcher, decoder=decoder) for u in urls
    ]


def _write_toml(tmp_path, text, dirs=("docs",)):
    """Write `fux.toml` and the committed directory list it now implies."""
    (tmp_path / "fux.toml").write_text(text, encoding="utf-8")
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("".join(f"{d}{chr(10)}" for d in dirs), encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")


def _write_urls(tmp_path, lines):
    """Write a URL list, filling in the REQUIRED attributes the case does not state.

    🔴 **Every URL line must state its fetcher since 2026-09-20** (W-199 D2;
    SR-URL-LIST decision 16) **and its decoder since 2026-09-21** (the pipe
    ruling; SR-URL-LIST decision 17) — there is no source-wide default left to
    inherit for either. Most cases here are about something else entirely, so
    the helper supplies the fixture's own `mw` fetcher and `decoder=prose`
    rather than every call site repeating both. **A case that is about either
    one states it and this leaves it alone**, which is what keeps the grammar
    cases honest.
    """
    path = tmp_path / URLS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for line in lines:
        stripped = line.strip()
        # ⚠ **A `#` inside a URL is a FRAGMENT, not a comment** — only a line
        # that STARTS with `#` is one. Splitting on the first `#` hid a
        # `fetch=` that sat after a fragment and double-appended one.
        is_comment = stripped.startswith("#") or not stripped
        if not is_comment and not stripped.startswith("!"):
            # ⚠ **Before any TRAILING comment.** Appending at the end put
            # `fetch=mw` inside `# trailing note`, so the line still had no
            # fetcher and the helper silently did nothing. A `#` that starts
            # the line is a comment; one after a URL may be a fragment, so the
            # split is on ` #` with the space.
            head, sep, tail = line.partition(" #")
            missing = "".join(
                f" {name}={value}"
                for name, value in (("fetch", "mw"), ("decoder", "prose"))
                if f"{name}=" not in stripped
            )
            if missing:
                line = f"{head.rstrip()}{missing}{(' #' + tail) if sep else ''}"
        out.append(line)
    path.write_text("".join(f"{line}\n" for line in out), encoding="utf-8")


def _init(tmp_path, *, urls, files=None, fetcher=FAKE_FETCHER, config=None):
    files = files if files is not None else {"docs/a.md": "# Doc A\n\nrepo body\n"}
    url_lines = '[sources.url]\nmax_parallel = 4\n'
    if config is not None:
        url_lines += "[sources.url.config]\n" + config
    _write_toml(tmp_path, "[sources]\n" + url_lines)
    _write_fetcher(tmp_path, fetcher)
    _write_urls(tmp_path, urls)
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


# -- config ----------------------------------------------------------------


def test_config_parses_url_source(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    cfg = load_config(tmp_path)
    assert cfg.url.routes == {}  # `fetcher` was deleted 2026-09-20 (W-199 D2)
    assert cfg.url.urls_file == ".fux/sources/urls"
    assert cfg.url.config == {}
    assert not hasattr(cfg.url, "meta"), "`meta` is deleted (W-194), not defaulted"


def test_config_paths_default_into_the_fux_dir(tmp_path):
    _write_toml(tmp_path, "[sources]\n[sources.url]\nmax_parallel = 4\n")
    cfg = load_config(tmp_path)
    # 🔴 **There is no default fetcher any more** (W-199 D2, 2026-09-20). A
    # line with no `fetch=` does not mean `fetch=http`; it fails to parse. What
    # this key's slot holds now is the routes table, empty until a repo writes
    # one, and an empty table resolves nothing rather than falling back.
    assert cfg.url.routes == {}
    assert cfg.url.urls_file == ".fux/sources/urls"


def test_config_rejects_a_meta_key_outright(tmp_path):
    """W-194: deleted, not deprecated. `meta = "plain"` is as dead as
    `meta = "cleartext"` — the key is unknown, and an unknown key in a
    committed config is a named error, never a warning or a silent ignore."""
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\nmeta = "plain"\n'
    )
    with pytest.raises(FuxError, match=r"\[sources\.url\] meta is not a fux\.toml key"):
        load_config(tmp_path)


def test_config_rejects_an_inline_urls_list_and_names_the_file(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\nurls = ["https://x.test/a"]\n'
    )
    with pytest.raises(FuxError, match=r"\.fux/sources/urls"):
        load_config(tmp_path)


def test_config_table_is_opaque_but_must_be_a_table(tmp_path):
    _init(tmp_path, urls=[], config='cdp_port = 9333\nanything_at_all = "fux never reads this"\n')
    assert load_config(tmp_path).url.config == {"cdp_port": 9333, "anything_at_all": "fux never reads this"}

    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\nconfig = 9222\n'
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


def test_a_missing_urls_file_is_ignored_while_there_is_nothing_to_reconcile(tmp_path):
    """Narrowed 2026-08-21 (W-63), and the narrowing is the point.

    This used to read "only matters on refresh" and pass because an offline
    run never looked at the list at all. It now passes for a *different*
    reason: reconciliation reads the list on every run, but only when the
    index actually holds `url:` records to reconcile — and here nothing has
    been ingested yet. The loud-error case is
    `test_an_offline_run_with_url_records_and_no_list_fails_loudly`.
    """
    _init(tmp_path, urls=["https://x.test/a"])
    (tmp_path / URLS_FILE).unlink()
    run(tmp_path)  # no url: records exist, so no list is needed or read
    with pytest.raises(FuxError, match=r"\.fux/sources/urls not found"):
        run(tmp_path, refresh_urls=True)


# -- fetcher loading ----------------------------------------------------


def test_missing_fetcher_file_fails_loudly(tmp_path):
    with pytest.raises(FuxError, match="fetcher not found"):
        load_fetcher(tmp_path, "nope.py")


def test_fetcher_without_fetch_fails_loudly(tmp_path):
    _write_fetcher(tmp_path, "x = 1\n")
    with pytest.raises(FuxError, match="no fetch"):
        load_fetcher(tmp_path, ".fux/fetchers/mw.py")


def test_fetch_all_calls_hooks_once_and_skips_failures(tmp_path):
    _write_fetcher(tmp_path, FAKE_FETCHER)
    fetched, skipped = fetch_all(
        tmp_path, _entries(["https://x.test/b", "https://x.test/boom", "https://x.test/a"])
    )
    assert [f.url for f in fetched] == ["https://x.test/a", "https://x.test/b"]  # sorted, deterministic
    assert [s.rel_path for s in skipped] == ["https://x.test/boom"]
    assert "no such page" in skipped[0].reason
    module = load_fetcher(tmp_path, ".fux/fetchers/mw.py")  # fresh module: counters reset
    assert callable(module.connect) and callable(module.close)


# A fake fetcher records what it saw next to itself — `fetch_all` imports
# the module privately, so its state is only observable through the filesystem.
_RECORDER = 'import pathlib\n_LOG = pathlib.Path(__file__).with_name("log.txt")\n'


def test_config_table_reaches_configure_verbatim(tmp_path):
    """Shared keys reach every fetcher, and anything INSIDE a fetcher's own
    table is still passed through untouched.

    ⚠ **The top level is namespaced now, and that is a real change of contract**
    (2026-09-14). A `dict` at the top level is read as a per-fetcher table and
    does **not** reach `configure()`; one level down, inside that fetcher's own
    table, nesting is verbatim exactly as before. The whole flat table used to
    go to every fetcher — which is what made a two-fetcher repo unconfigurable,
    since each `configure()` refuses the other's keys.
    """
    _init(
        tmp_path,
        urls=["https://x.test/a"],
        config='flag = true\n[sources.url.config.mw]\ncdp_port = 9333\nnested = {deep = [1, 2]}\n',
    )
    from fux.config import load

    cfg = load(tmp_path)
    got = cfg.url.config_for(".fux/fetchers/mw.py")
    assert got == {"flag": True, "cdp_port": 9333, "nested": {"deep": [1, 2]}}
    # A fetcher that is not `mw` sees the shared key and nothing else.
    assert cfg.url.config_for(".fux/fetchers/other.py") == {"flag": True}

def test_configure_is_optional_and_absent_table_is_empty(tmp_path):
    _write_fetcher(tmp_path, 
        _RECORDER
        + 'def configure(config):\n'
        '    _LOG.write_text(repr(config))\n'
        'def fetch(url):\n'
        '    return "# T\\n\\nbody\\n"\n',
        encoding="utf-8",
    )
    fetch_all(tmp_path, _entries(["https://x.test/a"]))  # no table passed at all
    assert (tmp_path / ".fux" / "fetchers" / "log.txt").read_text(encoding="utf-8") == "{}"

    _write_fetcher(tmp_path, 'def fetch(url):\n    return "# T\\n\\nbody\\n"\n', encoding="utf-8")
    fetched, _ = fetch_all(tmp_path, _entries(["https://x.test/a"]), {"k": 1})  # no configure defined
    assert len(fetched) == 1


def test_configure_runs_before_connect(tmp_path):
    _write_fetcher(tmp_path, 
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
    assert (tmp_path / ".fux" / "fetchers" / "log.txt").read_text(encoding="utf-8") == "configure,connect"


def test_configure_raising_is_a_loud_failure_not_a_skip(tmp_path):
    _write_fetcher(tmp_path, 
        'def configure(config):\n    raise ValueError("unknown key: prot")\n'
        'def fetch(url):\n    return "# T\\n\\nbody\\n"\n',
        encoding="utf-8",
    )
    with pytest.raises(FuxError, match="configure\\(\\) failed: unknown key"):
        fetch_all(tmp_path, _entries(["https://x.test/a"]), {"prot": 1})


def test_fetch_all_sanitizes_hostile_line_separators(tmp_path):
    _write_fetcher(tmp_path, 
        'def fetch(url):\n    return "# T\\n\\nbefore\\u2028after \\u2029 \\u0085 end\\n"\n',
        encoding="utf-8",
    )
    fetched, skipped = fetch_all(tmp_path, _entries(["https://x.test/a"]))
    assert skipped == []
    assert b"\xe2\x80\xa8" not in fetched[0].content  # U+2028 gone before the canonical writer


# -- ingest wiring ---------------------------------------------------------


def test_refresh_ingests_urls_with_plain_display_text(tmp_path):
    """⚠ **REWRITTEN for W-194.** This asserted the opposite: `meta == "hashed"`,
    a `title_h`, and *no display text leaks*. That was L5's default and the
    whole shape is deleted — a url record now carries `title` and `phrases`
    exactly as a git record does. **The ACL-mismatch leak it prevented is
    accepted, not closed** (SR-LAW-5, superseded)."""
    _init(tmp_path, urls=["https://x.test/a"])
    report = run(tmp_path, refresh_urls=True)
    assert report.doc_count == 2
    record = store.read_index(tmp_path)["url:https://x.test/a"]
    assert record["src"] == "url"
    assert record["loc"] == "https://x.test/a"
    assert record["title"] == "Page a"
    assert record["phrases"] == ["Page a"]
    assert "meta" not in record and "title_h" not in record
    # v2 hashes the ANALYZED term, not the raw word — "rendered" stems to "render"
    assert term_hash(tokenize("rendered")[0]) in record["terms"]


def test_plain_ingest_is_offline_and_carries_urls_forward(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    before = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}

    _write_fetcher(tmp_path, "def fetch(url):\n    raise AssertionError('network on offline run')\n", encoding="utf-8")
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

    _write_fetcher(tmp_path, "def fetch(url):\n    raise RuntimeError('site down')\n", encoding="utf-8")
    report = run(tmp_path, refresh_urls=True)
    assert store.read_index(tmp_path)["url:https://x.test/a"] == prior
    assert any("site down" in s.reason for s in report.skipped)


def test_a_delisted_url_disappears_on_an_offline_run(tmp_path):
    """W-63 defect 1. **Deletion needs no network.**

    This test asserted the opposite until 2026-08-21 — that a de-listed URL
    survived until someone ran `--refresh-urls` — and the module docstring
    stated that as the design. It was a defect either way: it made removing a
    document require the one capability removal has no use for, and it is why
    `fux remove <URL>` could not have worked offline.

    The fetcher is replaced with one that raises on call, so "offline" here is
    asserted rather than assumed.
    """
    _init(tmp_path, urls=["https://x.test/a", "https://x.test/b"])
    run(tmp_path, refresh_urls=True)
    assert "url:https://x.test/b" in store.read_index(tmp_path)

    _write_urls(tmp_path, ["https://x.test/a"])  # b de-listed; nothing else changes
    _write_fetcher(tmp_path, 
        "def fetch(url):\n    raise AssertionError('network on an offline run')\n", encoding="utf-8"
    )
    run(tmp_path)  # no flag, no fetcher call

    index = store.read_index(tmp_path)
    assert "url:https://x.test/b" not in index
    assert "url:https://x.test/a" in index  # a is still listed and untouched


def test_a_still_listed_url_whose_fetch_fails_keeps_its_record(tmp_path):
    """The other half of defect 1, and the half that must NOT change.

    Reconciliation keys on **the list**, never on whether a fetch succeeded.
    A transient network failure deleting a document is the failure mode the
    carry-forward exists to prevent, and tightening de-listing must not
    tighten this with it.
    """
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    prior = store.read_index(tmp_path)["url:https://x.test/a"]

    _write_fetcher(tmp_path, 
        "def fetch(url):\n    raise RuntimeError('site down')\n", encoding="utf-8"
    )
    run(tmp_path, refresh_urls=True)  # networked, and the fetch fails
    assert store.read_index(tmp_path)["url:https://x.test/a"] == prior

    run(tmp_path)  # offline, still listed
    assert store.read_index(tmp_path)["url:https://x.test/a"] == prior


def test_an_offline_run_with_url_records_and_no_list_fails_loudly(tmp_path):
    """A missing list is not "nothing is listed".

    Both silent readings are worse than an error: emptying every URL document
    because a file went missing, or carrying them forever, which is the defect
    above. `dirs` already fails loudly on exactly this condition.
    """
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)

    (tmp_path / URLS_FILE).unlink()
    with pytest.raises(FuxError, match="which URLs belong"):
        run(tmp_path)


def test_a_repo_with_no_url_records_never_reads_the_list(tmp_path):
    """The common case pays nothing — a corpus of directories is untouched."""
    _write_toml(tmp_path, "[sources]\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")

    run(tmp_path)  # no urls file exists at all, and none is looked for
    assert set(store.read_index(tmp_path)) == {"file:docs/a.md"}


def test_ver_bumps_when_fetched_content_changes(tmp_path):
    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    assert store.read_index(tmp_path)["url:https://x.test/a"]["ver"] == 1

    _write_fetcher(tmp_path, 'def fetch(url):\n    return "# Page a\\n\\nnew body\\n"\n', encoding="utf-8")
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
    # The anchor keys ride along on a `ref` edge (W-168 step 1); this test is
    # about which URL resolves, so they are stripped rather than asserted.
    bare = [{k: v for k, v in e.items() if k not in ("at", "al")} for e in edges]
    assert {"kind": "ref", "dst": "url:https://x.test/a", "grade": 10} in bare
    assert not any(e["dst"] == "url:https://x.test/other" for e in edges)  # dangling stays dropped


# -- the attribute grammar, per URL (SR-URL-LIST decisions 7-13) ----------


def test_a_fragment_survives_the_round_trip(tmp_path):
    """W-49: `#` is a comment only at line start or after whitespace."""
    _write_urls(tmp_path, ["https://x.test/page#section"])
    assert _urls(tmp_path) == ["https://x.test/page#section"]


def test_two_urls_differing_only_by_fragment_are_two_entries(tmp_path):
    _write_urls(tmp_path, ["https://x.test/p#a", "https://x.test/p#b", "https://x.test/p"])
    assert _urls(tmp_path) == ["https://x.test/p", "https://x.test/p#a", "https://x.test/p#b"]


def test_a_fragment_bearing_line_can_still_carry_attributes(tmp_path):
    _write_urls(tmp_path, ["https://x.test/p#frag keep=false  # public"])
    (entry,) = read_urls(tmp_path, URLS_FILE)
    assert entry.value == "https://x.test/p#frag"
    assert entry.attrs["keep"] == "false"


def test_an_unknown_attribute_errors_at_file_lineno(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a", "https://x.test/b kep=false"])
    with pytest.raises(FuxError, match=r"urls:2: unknown attribute 'kep'"):
        read_urls(tmp_path, URLS_FILE)


def test_an_unknown_attribute_value_errors_at_file_lineno(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a keep=maybe"])
    with pytest.raises(FuxError, match=r"urls:1: keep='maybe' is not one of"):
        read_urls(tmp_path, URLS_FILE)


def test_a_line_still_carrying_meta_is_a_named_error(tmp_path):
    """W-194 deleted `meta` outright, on the `fux update` precedent (W-177):
    no deprecation window and no accept-and-ignore. A repo whose committed
    list still says `meta=hashed` **fails to load, by name and line**, because
    the attribute set is closed — which is the same mechanism that would
    refuse a typo, and is why nothing extra had to be written to get it."""
    _write_urls(tmp_path, ["https://x.test/a meta=hashed"])
    with pytest.raises(FuxError, match=r"urls:1: unknown attribute 'meta'"):
        read_urls(tmp_path, URLS_FILE)


def test_a_duplicate_with_conflicting_attributes_names_both_lines(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a keep=false", "# note", "https://x.test/a fetch=cdp"])
    with pytest.raises(FuxError, match=r"urls:1 and .*urls:3"):
        read_urls(tmp_path, URLS_FILE)


def test_a_duplicate_that_agrees_is_a_merge_artefact_not_an_error(tmp_path):
    _write_urls(tmp_path, ["https://x.test/a keep=true", "https://x.test/a"])
    (entry,) = read_urls(tmp_path, URLS_FILE)
    assert entry.attrs["keep"] == "true"  # absent means the default; they agree


def test_file_order_does_not_change_the_parsed_set(tmp_path):
    lines = ["https://x.test/c fetch=cdp", "https://x.test/a", "https://x.test/b keep=false"]
    _write_urls(tmp_path, lines)
    forward = read_urls(tmp_path, URLS_FILE)
    _write_urls(tmp_path, list(reversed(lines)))
    assert [(e.value, e.attrs) for e in forward] == [
        (e.value, e.attrs) for e in read_urls(tmp_path, URLS_FILE)
    ]


def test_a_line_attribute_beats_the_source_wide_setting(tmp_path):
    """Decision 10, on `fetch` — ⚠ `meta` was this test's worked example until
    W-194 deleted it, and `fetch` is now the only attribute with all three
    layers. A line that declares one wins for its own URL and no other."""
    _init(tmp_path, urls=["https://x.test/a fetch=cdp", "https://x.test/b"])
    _write_fetcher(tmp_path, CDP_FETCHER, name="cdp.py")
    run(tmp_path, refresh_urls=True)
    index = store.read_index(tmp_path)
    assert index["url:https://x.test/a"]["title"] == "Rendered"   # the line's fetcher
    assert index["url:https://x.test/b"]["title"] == "Page b"     # the source-wide one

CDP_FETCHER = """
def fetch(url):
    return "# Rendered" + chr(10) * 2 + "browser fetcher body" + chr(10)
"""


def test_fetch_routes_per_line_and_only_loads_what_it_needs(tmp_path):
    """`fetch=` picks a file in the fetcher directory; nothing else is imported."""
    _init(tmp_path, urls=["https://x.test/a", "https://x.test/b fetch=cdp"])
    _write_fetcher(tmp_path, CDP_FETCHER, name="cdp.py")
    (tmp_path / "http.py").write_text(  # named by no line: must never be imported
        "raise AssertionError('a fetcher no line names must never be imported')",
        encoding="utf-8",
    )
    run(tmp_path, refresh_urls=True)
    index = store.read_index(tmp_path)
    assert index["url:https://x.test/a"]["title"] == "Page a"
    assert index["url:https://x.test/b"]["title"] == "Rendered"


def test_a_missing_fetcher_names_setup_when_nothing_is_beside_it(tmp_path):
    """Nothing in the directory, so `fux setup` IS the remedy."""
    _write_toml(
        tmp_path,
        '[sources]\n[sources.url]\nmax_parallel = 4\n',
    )
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "a.md").write_text("# Doc A\n\nrepo body\n", encoding="utf-8")
    _write_urls(tmp_path, ["https://x.test/a fetch=cdp"])
    with pytest.raises(FuxError, match=r"fetcher not found: \.fux/fetchers/cdp\.py.*fux setup"):
        run(tmp_path, refresh_urls=True)


def test_a_missing_fetcher_names_ITS_SIBLINGS_when_there_are_any(tmp_path):
    """🔴 **The message was wrong for the case W-178 created** (2026-09-15).

    `fetch=` names any module in the fetchers directory now, so the common
    failure is a **typo** — `glasbox` beside a real `glassbox.py`. The old
    message said *"run `fux setup` to write the shipped fetchers"* and nothing
    else: correct for an empty directory, and actively misleading here, because
    `fux setup` writes two files and neither is the one the line names.

    ⚠ **And the stakes are why it matters.** `load_fetcher` raises rather than
    skipping the line, so a one-character typo exits 1 and indexes **zero**
    documents — see `work/regression/2026-09-15-consumer-fetchers/ANALYSIS.md`.
    The message is the whole interface at that moment.
    """
    _write_toml(
        tmp_path,
        '[sources]\n[sources.url]\nmax_parallel = 4\n',
    )
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "a.md").write_text("# Doc A\n\nrepo body\n", encoding="utf-8")
    _write_urls(tmp_path, ["https://x.test/a fetch=glasbox"])
    fetchers = tmp_path / ".fux" / "fetchers"
    fetchers.mkdir(parents=True, exist_ok=True)
    for stem in ("http", "glassbox"):
        (fetchers / f"{stem}.py").write_text("def fetch(url):\n    return ''\n", encoding="utf-8")

    with pytest.raises(FuxError) as exc:
        run(tmp_path, refresh_urls=True)
    message = str(exc.value)
    assert "glassbox" in message, "the file that IS there must be named"
    assert "fux setup" not in message, "setup does not write the module being asked for"
    assert "fux doctor" in message, "the check that would have caught it first"


# -- W-47's defect, and what survives it after W-194 ------------------------


def test_a_url_ingest_produces_an_index_the_build_accepts(tmp_path):
    """⚠ **The measured defect this guards is GONE** (W-194, 2026-09-20).

    It was: `meta = "hashed"` wrote a bare 16-hex `title_h`, which is a quoted
    16-hex token outside `terms`, which the scan counts toward a df and the
    accelerator does not — so `fux build` refused the index. **27.2 ms became
    4 248.8 ms at RFC scale, the whole M2 result forfeited by following the
    documentation.** `title_h` no longer exists, so the default cannot produce
    that index.

    **Kept because ingest-then-build on a url corpus is still the path nobody
    else exercises end to end**, and the stray-quoted-hash tripwire it used to
    trip is still armed — `tests/derive/test_differential.py` exercises that
    directly now.
    """
    from fux.derive import build

    _init(tmp_path, urls=["https://x.test/a", "https://x.test/b"])
    run(tmp_path, refresh_urls=True)
    report = build(tmp_path)  # must not raise
    assert report.docs == 3


def test_a_url_record_carries_no_bare_16_hex_token(tmp_path):
    """The scan finds df by looking for `"<16 hex>"` in the raw record bytes,
    so any quoted 16-hex value outside `terms` makes the two paths disagree.
    `title_h` was the field that did it; the invariant outlives the field."""
    import json
    import re

    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    for path in store.iter_shard_paths(tmp_path):
        for line in path.read_bytes().split(chr(10).encode()):
            record = line.decode("utf-8") if line else ""
            if '"src":"url"' not in record:
                continue
            quoted = set(re.findall(r'"([0-9a-f]{16})"', record))
            assert quoted <= set(json.loads(record)["terms"])


def test_a_url_record_shows_its_real_title(tmp_path):
    """⚠ **REWRITTEN.** This asserted the opposite — *"enough to identify a
    document across two answers, never enough to read"* — and checked that a
    verb showed `term_hash("Page a")`. W-194 deleted the opaque title."""
    from fux.query import scan

    _init(tmp_path, urls=["https://x.test/a"])
    run(tmp_path, refresh_urls=True)
    (result,) = [r for r in scan.ask(tmp_path, "rendered", top=5) if r.id.startswith("url:")]
    assert result.title == "Page a"


# -- W-63 defect 2: a carried record's edges are re-checked, never trusted ---

#: Page `a` points at the other URL and at a repo file; every other page is
#: inert. Two edge kinds on one carried record, which is what makes the
#: assertions below distinguish "dropped the stale one" from "dropped them all".
LINKING_FETCHER = '''\
def fetch(url):
    if url.endswith("/a"):
        return "# Page a\\n\\nsee [b](https://x.test/b) and `docs/keep.md`\\n"
    return "# Page\\n\\nplain body\\n"
'''


def test_a_carried_url_record_drops_its_edge_to_a_delisted_document(tmp_path):
    """W-63 defect 2.

    `graph/model.edges_from_records` lifts `edges` with no validation, on the
    promise that `ingest/edges.py` already dropped the dangling ones. That
    promise holds only for records **re-resolved this run** — and a `url:`
    record is carried forward on every offline run, edges included. So a
    document removed from the corpus survived as an edge target in the derived
    graph plane: an edge into a node no verb can explain.
    """
    _init(
        tmp_path,
        urls=["https://x.test/a", "https://x.test/b"],
        files={"docs/keep.md": "# Keep\n\nbody\n"},
        fetcher=LINKING_FETCHER,
    )
    run(tmp_path, refresh_urls=True)
    edges = store.read_index(tmp_path)["url:https://x.test/a"]["edges"]
    assert {e["dst"] for e in edges} == {"url:https://x.test/b", "file:docs/keep.md"}

    _write_urls(tmp_path, ["https://x.test/a"])  # b de-listed
    run(tmp_path)  # offline: a is carried, but its edges are not trusted

    index = store.read_index(tmp_path)
    assert "url:https://x.test/b" not in index
    carried_edges = index["url:https://x.test/a"]["edges"]
    assert {e["dst"] for e in carried_edges} == {"file:docs/keep.md"}


def test_no_surviving_record_points_at_an_id_this_run_does_not_hold(tmp_path):
    """The invariant, stated over the whole record set rather than one record.

    This is the assertion that would catch defect 2 wherever it came from, so
    it is written against the committed index and not against the code path
    that fixes it. `tag:` targets are exempt: a tag node is minted by the edge
    itself and is never a document, so it cannot dangle.
    """
    _init(
        tmp_path,
        urls=["https://x.test/a", "https://x.test/b"],
        files={
            "docs/keep.md": "---\ntags: [ops]\n---\n# Keep\n\nsee `docs/gone.md`\n",
            "docs/gone.md": "# Gone\n\nbody\n",
        },
        fetcher=LINKING_FETCHER,
    )
    run(tmp_path, refresh_urls=True)

    (tmp_path / "docs" / "gone.md").unlink()
    _write_urls(tmp_path, ["https://x.test/a"])
    run(tmp_path)

    index = store.read_index(tmp_path)
    assert "url:https://x.test/b" not in index and "file:docs/gone.md" not in index

    dangling = [
        (record["id"], edge["dst"])
        for record in index.values()
        for edge in record.get("edges", ())
        if not edge["dst"].startswith("tag:") and edge["dst"] not in index
    ]
    assert dangling == []
    # The tag edge survived, which is what makes the exemption a real one and
    # not just an untested clause.
    assert {"kind": "tag", "dst": "tag:ops", "grade": 10} in index["file:docs/keep.md"]["edges"]


# --- The skip reason must say which of two very different things happened ----
#
# Measured 2026-08-27 against `https://httpbin.org/uuid` in the fux-lab daemon
# environment: fux reported `no decoder for application/json` while `json`
# was built in, claimed `.json`, ran, and correctly dropped a bare UUID —
# leaving nothing to index. The message sent a reader looking for a decoder
# that was already there. `decode.reason()` has always drawn this distinction
# and its docstring says conflating the two "would make the queue useless";
# the FILE path used it and the URL path did not.

def test_a_decoder_that_ran_and_found_nothing_is_not_reported_as_missing():
    """⚠ **The second argument is the DECLARED STEM since the pipe ruling.**

    It was the `Content-Type`, and the distinction this case is about survives
    the change unaltered — it is simply keyed on what the line said instead of
    on what the server said.
    """
    from fux.ingest.urlsrc import _decode_fetched

    uuid_only = b'{\n  "uuid": "23f0c01c-4067-49f9-99cd-b19564aa930e"\n}\n'
    markdown, why = _decode_fetched(uuid_only, "json", "https://httpbin.org/uuid")

    assert markdown is None
    assert "no decoder" not in why, (
        "json is built in and ran — saying there is no decoder is false"
    )
    assert why == "json: nothing readable in the fetched bytes"


def test_a_stem_nothing_provides_still_says_no_decoder():
    """The other half. Narrowing the message must not remove the true case.

    🔴 **The true case MOVED with the ruling, and that is the whole shape of
    it.** It used to be *a content type no decoder claims* (`image/webp`), which
    a server could produce at any time; it is now *a `decoder=` naming no
    module*, which only a committed line can say. The unreadable format is
    caught one step earlier now — `fux add` refuses to write a line for it.
    """
    from fux.ingest.urlsrc import _decode_fetched

    markdown, why = _decode_fetched(b"RIFF....WEBP", "webp", "https://x.test/y.webp")
    assert markdown is None
    assert "no decoder module named 'webp'" in why
    assert "Fix the `decoder=` on this URL's line" in why


def test_json_with_prose_in_it_decodes_rather_than_skipping():
    """The control: the skip above is about the CONTENT, not the stem."""
    from fux.ingest.urlsrc import _decode_fetched

    markdown, why = _decode_fetched(
        b'{"note": "the paging rotation"}', "json", "https://x.test/y"
    )
    assert why == ""
    assert markdown and "paging rotation" in markdown


def test_a_consumer_decoder_reaches_url_content_too(tmp_path):
    """SR-DECODE's premise stopped at the network boundary until 2026-08-27.

    `decode_mod.decode(raw, rel)` was called with **no `root`**, so
    `registry(None)` returned built-ins only and a decoder the consumer wrote
    into `.fux/decoders/` never applied to a fetched document — at exactly the
    boundary where a strange content type is most likely to arrive.

    ⚠ **The line now NAMES the consumer module** rather than arriving at it
    through an extension the registry happened to resolve, which is
    `decoder_named`'s job; `root` is still what makes it reachable at all.
    """
    from fux.ingest.urlsrc import _decode_fetched

    decoders = tmp_path / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    (decoders / "vndthing.py").write_text(
        "EXTENSIONS = ('.vndthing',)\n"
        "def decode(raw, rel_path):\n"
        "    return 'consumer decoder ran: ' + raw.decode()\n",
        encoding="utf-8",
    )

    markdown, why = _decode_fetched(
        b"payload", "vndthing", "https://x.test/doc.vndthing", tmp_path
    )
    assert why == "", why
    assert markdown == "consumer decoder ran: payload"


def test_a_consumer_decoder_is_unreachable_without_the_root():
    """The control for the case above, and it is why `root` is threaded."""
    from fux.ingest.urlsrc import _decode_fetched

    markdown, why = _decode_fetched(b"payload", "vndthing", "https://x.test/doc", None)
    assert markdown is None and "no decoder module named 'vndthing'" in why


# --- URLs reach the enrichment queue too (Arpit, 2026-08-28) ---------------
#
# The file path routed an unreadable document into `.fux/enrich/queue.tsv` with
# its reason; the URL path routed it nowhere, so a URL that needed a model could
# never be queued for one. SR-FETCHER decision 11 named the asymmetry; this is
# it closed.

def test_a_fetch_failure_is_not_queued_for_a_model():
    """⚠ **The care that earns the `UNFETCHED` kind.** A 404 or a timeout is not
    something enrichment discharges, and `queue.tsv` is COMMITTED — queueing one
    would put a permanent work item in front of the whole team that no amount of
    model time closes.
    """
    from fux.ingest.gitdir import UNFETCHED, UNREADABLE, Skipped

    dead = Skipped(rel_path="https://x.test/gone", reason="fetch failed: 404", kind=UNFETCHED)
    unreadable = Skipped(rel_path="https://x.test/scan", reason="pdf: no text layer")

    assert dead.kind == UNFETCHED
    assert unreadable.kind == UNREADABLE, "the default stays the loud bucket"
    queued = [s for s in (dead, unreadable) if s.kind != UNFETCHED]
    assert [s.rel_path for s in queued] == ["https://x.test/scan"]


def test_the_kind_is_set_at_the_skip_site_not_read_back_from_the_reason():
    """Branching on prose is what W-82 ruling 12 refused, and the classification
    would be one string edit away from silently wrong."""
    import inspect

    from fux.ingest import urlsrc

    source = inspect.getsource(urlsrc.fetch_all)
    assert "kind=UNFETCHED" in source
    assert 'reason.startswith("fetch failed' not in source
