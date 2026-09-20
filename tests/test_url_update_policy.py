"""`update = auto|never` — whether `fux update` goes out for a URL at all.

W-113, from Arpit's ruling R-1 (2026-09-05). A URL line could already say
`fetch=`, `keep=`, `ttl=`, `enrich=` and `archived=` and **could not
say whether it should be re-fetched**.

🔴 **The boundary these tests exist to hold.** `ttl=` is **ask-time** — it
bounds how long `fux answer` may cite a document without re-checking it.
`update=` is **update-time** — whether fux ever goes and looks again. They are
different clocks, and `update=` is deliberately not a clock at all.

🔴 **And the saving is not the ETag saving.** `update=never` buys bandwidth by
giving up freshness. SR-CDP-FETCHER decision 12's response-stage interception
saves the decode, never the transfer; only request-stage interception would
deliver *"check cheaply and stay fresh"*, and it is neither costed nor built.
"""

from __future__ import annotations

import pytest

from fux.config import UrlSource
from fux.errors import FuxError
from fux.ingest import sourcelist, urlsrc


def _source(**overrides):
    base = dict(
        fetcher=".fux/fetchers/http.py",
        urls_file=".fux/sources/urls",
        keep=True,
        ttl="24h",
        config={},
        max_parallel=4,
    )
    base.update(overrides)
    return UrlSource(**base)


def _resolve(text, **source_overrides):
    entries = sourcelist.parse(text, sourcelist.URLS, origin="list")
    return urlsrc.resolve_urls(entries, _source(**source_overrides))


# -- the three layers ------------------------------------------------------


def test_silence_resolves_to_auto_so_no_existing_repo_moves():
    """🔴 The URL list is COMMITTED. A default that is not the status quo would
    change what every existing clone does the moment it upgrades."""
    (entry,) = _resolve("https://x.test/a")
    assert entry.update == "auto"


def test_the_source_wide_layer_applies_to_a_silent_line():
    (entry,) = _resolve("https://x.test/a", update="never")
    assert entry.update == "never"


def test_a_line_that_declared_it_beats_the_source_wide_value():
    """Both directions — a source-wide pin must be exemptable per line, or
    pinning a wiki would mean pinning every page in it forever."""
    (pinned,) = _resolve("https://x.test/a update=never")
    assert pinned.update == "never"
    (exempt,) = _resolve("https://x.test/a update=auto", update="never")
    assert exempt.update == "auto"


def test_an_unknown_value_is_refused_by_the_grammar_naming_the_line():
    with pytest.raises(FuxError, match=r"list:1: update='sometimes' is not one of auto, never"):
        sourcelist.parse("https://x.test/a update=sometimes", sourcelist.URLS, origin="list")


def test_an_unknown_source_wide_value_is_refused_by_the_loader(tmp_path):
    from fux.config import load

    (tmp_path / "fux.toml").write_text(
        '[sources.url]\nmax_parallel = 4\nupdate = "weekly"\n', encoding="utf-8"
    )
    with pytest.raises(FuxError, match=r'update must be "auto" or "never"'):
        load(tmp_path)


def test_the_source_wide_default_is_auto(tmp_path):
    from fux.config import load

    (tmp_path / "fux.toml").write_text("[sources.url]\nmax_parallel = 4\n", encoding="utf-8")
    assert load(tmp_path).url.update == "auto"


# -- no socket, and no consumer code executed ------------------------------


def test_a_pinned_url_never_reaches_the_fetcher(tmp_path, monkeypatch):
    """🔴 **The assertion that makes this feature worth having.**

    Filtering inside the per-URL loop would still be correct about the network
    and wrong about everything else: `fetch_all` groups by `fetcher_path` and
    calls `load_fetcher`, which **imports consumer Python and runs whatever is
    at its module level** — a fetcher is free to open a session there. A pinned
    URL must not cause that import, so the skip lives above the grouping.
    """
    from fux.ingest import run as run_mod

    exploded = []

    def _never(*args, **kwargs):  # pragma: no cover - the point is it is not called
        exploded.append(args)
        raise AssertionError("a pinned URL resolved a fetcher")

    monkeypatch.setattr(urlsrc, "load_fetcher", _never)
    monkeypatch.setattr(run_mod.urlsrc, "load_fetcher", _never)

    entries = _resolve("https://x.test/a update=never\nhttps://x.test/b update=never")
    fetched, skipped = urlsrc.fetch_all(
        tmp_path, [e for e in entries if e.update != "never"], {}, max_parallel=1
    )
    assert not exploded and not fetched and not skipped


def test_a_pinned_url_is_a_policy_skip_not_an_unfetched_one():
    """`POLICY` means *the declaration did its job*. `UNFETCHED` would say the
    bytes failed to arrive, which puts the URL in front of somebody as a problem
    and, through `enrich/queue.tsv`, in front of the whole team."""
    from fux.ingest.gitdir import POLICY, UNFETCHED

    assert POLICY != UNFETCHED


# -- the lossy pair is disclosed, never refused ----------------------------


def test_never_plus_keep_false_is_legal():
    """It is coherent for a document that truly never changes, and surprising
    to have chosen by accident — which is a warning's shape, not a refusal's."""
    (entry,) = _resolve("https://x.test/a update=never keep=false")
    assert entry.update == "never" and entry.keep is False


def test_never_plus_keep_true_is_the_coherent_pair():
    """More offline, with the grain of L4: the bytes are in `.fux/acquired/`,
    so a fetch that fails or is forbidden verifies against them and reports
    `as-ingested` rather than `unverified`.

    ⚠ **This docstring said "and no socket opens" and that was wrong**
    (corrected 2026-09-14, W-174). `update=` is the UPDATE-time clock;
    SR-URL-FRESHNESS decision 15 says in as many words that it *"still does not
    keep `answer` offline"*. The knob that closes the socket at ask time is
    `[sources.url] fetch_at_answer` (decision 16).
    """
    (entry,) = _resolve("https://x.test/a update=never")
    assert entry.update == "never" and entry.keep is True


def test_doctor_counts_pinned_lines_and_names_the_lossy_ones(tmp_path):
    from fux import doctor

    (tmp_path / ".git").mkdir()
    (tmp_path / "fux.toml").write_text(
        '[sources]\nurls_file = ".fux/sources/urls"\n[sources.url]\nmax_parallel = 4\n', encoding="utf-8"
    )
    urls = tmp_path / ".fux" / "sources" / "urls"
    urls.parent.mkdir(parents=True)
    urls.write_text(
        "https://x.test/pinned update=never\n"
        "https://x.test/lossy update=never keep=false\n"
        "https://x.test/live\n",
        encoding="utf-8",
    )
    parts = doctor._pinned_note(tmp_path)
    joined = " ".join(parts)
    assert "2 pinned" in joined
    assert "1 of them keep=false" in joined and "https://x.test/lossy" in joined
    assert "https://x.test/pinned" not in joined  # pinned-and-kept is not a finding


def test_doctor_says_nothing_when_no_line_is_pinned(tmp_path):
    """A row that fires on every repo is a row people stop reading."""
    from fux import doctor

    (tmp_path / ".git").mkdir()
    (tmp_path / "fux.toml").write_text(
        '[sources]\nurls_file = ".fux/sources/urls"\n[sources.url]\nmax_parallel = 4\n', encoding="utf-8"
    )
    urls = tmp_path / ".fux" / "sources" / "urls"
    urls.parent.mkdir(parents=True)
    urls.write_text("https://x.test/live\n", encoding="utf-8")
    assert doctor._pinned_note(tmp_path) == []


# -- `fux add --no-update` -------------------------------------------------


def test_no_update_records_the_word_never_not_a_boolean():
    """`update=false` would be a fourth spelling of a two-word attribute, and
    the grammar would refuse it — but only at read time, in someone else's
    clone."""
    from fux.sources import _overrides

    class Args:
        no_update = True

    assert _overrides(Args(), sourcelist.URLS) == {"update": "never"}


def test_no_update_is_refused_on_the_dirs_list():
    """The attribute set is closed, and a flag naming an attribute a list does
    not have is someone believing something false about the line they wrote."""
    from fux.sources import _overrides

    class Args:
        no_update = True

    with pytest.raises(FuxError, match=r"--no_update sets `update`, which `dirs` does not have"):
        _overrides(Args(), sourcelist.DIRS)


# -- the real ingest path --------------------------------------------------


FAKE = 'def fetch(url):\n    return "# Page\\n\\nbody words here\\n"\n'
EXPLODING = (
    'raise RuntimeError("a pinned URL imported its fetcher")\n'
    'def fetch(url):\n    return "# Page\\n\\nbody\\n"\n'
)


def _repo(tmp_path, urls, fetcher=FAKE):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndirs_file = ".fux/sources/dirs"\n'
        '[sources.url]\nfetcher = "mw.py"\nmax_parallel = 4\n',
        encoding="utf-8",
    )
    (tmp_path / "mw.py").write_text(fetcher, encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "urls").write_text("\n".join(urls) + "\n", encoding="utf-8")
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    # SR-PII decision 17: a hand-built repo needs this or every verb refuses.
    (fux / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# Doc A\n\nrepo body\n", encoding="utf-8")
    return tmp_path


def test_ingest_skips_a_pinned_url_without_importing_the_fetcher(tmp_path):
    """🔴 The end-to-end version of the no-socket assertion, through `run()`.

    The fetcher file raises at **module level**. If the pinned line reached
    `fetch_all`'s grouping, `load_fetcher` would execute it and the ingest would
    die — which is the whole class of harm a pinned line exists to avoid.
    """
    from fux.ingest.run import run

    _repo(tmp_path, ["https://x.test/pinned update=never"], fetcher=EXPLODING)
    report = run(tmp_path, refresh_urls=True)
    pinned = [s for s in report.skipped if s.rel_path == "https://x.test/pinned"]
    assert len(pinned) == 1
    assert "update=never" in pinned[0].reason
    assert pinned[0].kind == "policy"


def test_a_mixed_list_fetches_the_live_line_and_pins_the_other(tmp_path):
    from fux import store
    from fux.ingest.run import run

    _repo(tmp_path, ["https://x.test/live", "https://x.test/pinned update=never"])
    run(tmp_path, refresh_urls=True)
    index = store.read_index(tmp_path)
    assert "url:https://x.test/live" in index
    # The pinned line was never fetched, so it has no record to carry forward
    # -- pinning freezes a document, it does not create one from nothing.
    assert "url:https://x.test/pinned" not in index


def test_pinning_a_url_AFTER_it_was_indexed_keeps_its_record(tmp_path):
    """🔴 Pinning freezes a document. It must never DROP one.

    The carry-forward is keyed on the whole resolved list, not on what this run
    fetched — so a URL that stops being fetched keeps the record it already has.
    A narrower keying would turn `update=never` into a delayed deletion.
    """
    from fux import store
    from fux.ingest.run import run

    root = _repo(tmp_path, ["https://x.test/doc"])
    run(root, refresh_urls=True)
    assert "url:https://x.test/doc" in store.read_index(root)

    (root / ".fux" / "sources" / "urls").write_text(
        "https://x.test/doc update=never\n", encoding="utf-8"
    )
    (root / "mw.py").write_text(EXPLODING, encoding="utf-8")
    run(root, refresh_urls=True)
    assert "url:https://x.test/doc" in store.read_index(root)


def test_a_corpus_that_declares_nothing_is_byte_identical(tmp_path):
    """The committed-file guarantee: silence resolves to today's behaviour, so
    adding this attribute moved no existing repo."""
    from fux import store
    from fux.ingest.run import run

    a = _repo(tmp_path / "a", ["https://x.test/doc"])
    b = _repo(tmp_path / "b", ["https://x.test/doc update=auto"])
    run(a, refresh_urls=True)
    run(b, refresh_urls=True)
    assert store.read_index(a) == store.read_index(b)


# -- W-140 row 3: the add's one fetch ---------------------------------------


def test_the_add_that_writes_a_pinned_line_still_fetches_it_once(tmp_path):
    """SR-URL-LIST decision 14, which the code contradicted for six days.

    `fux add <URL> --no-update` wrote the line, fetched nothing and exited 1
    saying *the fetch failed* — because the pin filter ran above the fetch and
    did not know an add was in progress. `--help` and the CHANGELOG both
    promised the one fetch; a pin freezes a document and cannot freeze one
    that was never fetched.
    """
    from fux import store
    from fux.ingest.run import run

    _repo(tmp_path, ["https://x.test/pinned update=never"])
    report = run(tmp_path, refresh_urls=True, first_fetch={"https://x.test/pinned"})

    assert "url:https://x.test/pinned" in store.read_index(tmp_path)
    assert not [s for s in report.skipped if s.rel_path == "https://x.test/pinned"]


def test_the_exemption_is_that_url_and_no_other(tmp_path):
    """One add, one fetch. A second pinned line in the same list stays frozen."""
    from fux import store
    from fux.ingest.run import run

    _repo(
        tmp_path,
        ["https://x.test/added update=never", "https://x.test/other update=never"],
    )
    run(tmp_path, refresh_urls=True, first_fetch={"https://x.test/added"})

    index = store.read_index(tmp_path)
    assert "url:https://x.test/added" in index
    assert "url:https://x.test/other" not in index


def test_a_later_run_pins_the_line_the_add_fetched(tmp_path):
    """The flag governs every run after — including `--all` and `--full`."""
    from fux.ingest.run import run

    _repo(tmp_path, ["https://x.test/pinned update=never"])
    run(tmp_path, refresh_urls=True, first_fetch={"https://x.test/pinned"})

    report = run(tmp_path, refresh_urls=True, full=True)
    pinned = [s for s in report.skipped if s.rel_path == "https://x.test/pinned"]
    assert len(pinned) == 1 and pinned[0].kind == "policy"


def test_cmd_add_passes_the_url_it_just_wrote_and_nothing_else():
    """The set has exactly one populator. Read from the source, because a second
    caller passing a wider set would re-open the hole quietly."""
    import inspect

    from fux import sources

    body = inspect.getsource(sources)
    assert body.count("first_fetch=") == 3, (
        "first_fetch appears in exactly three places — the `_ingest` signature, "
        "its forward, and `cmd_add`'s single call. A fourth needs this test "
        "read, not this number raised: a wider set re-opens the hole quietly"
    )
    assert "first_fetch=only_urls" in body
