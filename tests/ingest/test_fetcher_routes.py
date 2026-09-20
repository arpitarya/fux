"""Fetcher routing — the grammar, the order, and the collisions it refuses.

W-199 D3 (Arpit, 2026-09-20). [SR-FETCHER](../../records/0117_fetcher.md)
decision 16.

🔴 **The property most worth holding is a NEGATIVE one**: resolving a route must
never import a fetcher. `fux doctor` is offline by contract and
`fux ingest --check` promises it opens no socket — a fetcher is free to open a
session at module level, so an import on this path is L4 lost exactly where
nobody would look. It is read with `ast`, and
`test_resolving_never_imports_a_fetcher` is the gate.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import routes


def _table(mapping):
    return routes.validate(mapping, where="t")


# --- the four pattern shapes -------------------------------------------------

@pytest.mark.parametrize("pattern,host,hit", [
    ("example.com", "example.com", True),
    ("example.com", "a.example.com", False),
    ("*.example.com", "a.example.com", True),
    ("*.example.com", "a.b.example.com", True),
    # ⚠ **The first thing a consumer gets wrong**, which is why it is stated in
    # the template docstring, the skill and the error text as well as here.
    ("*.example.com", "example.com", False),
    ("example.com:8443", "example.com:8443", True),
    ("example.com:8443", "example.com", False),
    (r"re:^.*\.sharepoint\.com$", "contoso.sharepoint.com", True),
    (r"re:^.*\.sharepoint\.com$", "sharepoint.com", False),
    (r"re:^.*\.sharepoint\.com$", "x.sharepoint.com.evil.test", False),
])
def test_a_pattern_matches_exactly_what_it_should(pattern, host, hit):
    assert (routes.resolve(host, _table({pattern: "cdp"}), where="t") == "cdp") is hit


def test_a_regex_is_anchored_at_LOAD_not_at_match():
    """🔴 An unanchored regex is a silent widening.

    `re:sharepoint` would match `sharepoint.com.evil.test` if the matcher used
    `search`, and every caller would have to remember `fullmatch`. Anchoring
    once, where the pattern is compiled, is the only place it cannot be
    forgotten.
    """
    table = _table({"re:sharepoint": "cdp"})
    assert routes.resolve("sharepoint", table, where="t") == "cdp"
    assert routes.resolve("evil-sharepoint-lookalike.test", table, where="t") is None


@pytest.mark.parametrize("bad", ["", "HTTP://x", "example.com/path", "*example.com", "re:("])
def test_a_pattern_that_is_neither_shape_is_a_named_error(bad):
    with pytest.raises(FuxError):
        _table({bad: "cdp"})


def test_a_route_value_must_be_a_module_stem():
    for value in ("cdp.py", ".fux/fetchers/cdp.py", "", 7):
        with pytest.raises(FuxError, match="module stem|module name"):
            _table({"example.com": value})


# --- the specificity order, and where it stops -------------------------------

def test_the_literal_order_is_host_port_then_host_then_wildcard():
    table = _table({
        "a.example.com:8443": "one",
        "a.example.com": "two",
        "*.example.com": "three",
    })
    assert routes.resolve("a.example.com:8443", table, where="t") == "one"
    assert routes.resolve("a.example.com", table, where="t") == "two"
    assert routes.resolve("b.example.com", table, where="t") == "three"


def test_a_regex_never_competes_on_specificity_it_COLLIDES():
    """🔴 The refusal that keeps a wrong index from being built quietly.

    Between a regex and a literal there is no ordering that is not arbitrary,
    and the failure a guessed order produces is a **plausible index retrieved by
    the wrong fetcher** — nothing downstream detects it. So it is refused, and
    the error names both patterns.
    """
    table = _table({"example.com": "http", r"re:^example\.com$": "cdp"})
    with pytest.raises(FuxError, match="matches 2 routes"):
        routes.resolve("example.com", table, where="t")


def test_two_regexes_matching_one_host_are_refused_too():
    table = _table({"re:.*[.]example[.]com": "http", r"re:^a\..*$": "cdp"})
    with pytest.raises(FuxError, match="matches 2 routes"):
        routes.resolve("a.example.com", table, where="t")


def test_nothing_matching_is_None_and_never_a_default():
    """🔴 There is no default layer (W-199 D2). `None` means *fux cannot
    retrieve this URL*, and the caller refuses rather than falling back."""
    assert routes.resolve("nowhere.test", _table({"example.com": "http"}), where="t") is None
    assert routes.resolve("anything.test", _table({}), where="t") is None


# --- host normalisation ------------------------------------------------------

@pytest.mark.parametrize("url,host", [
    ("https://Example.COM/a", "example.com"),
    ("https://user:pw@example.com/a", "example.com"),
    ("https://example.com:8443/a?b#c", "example.com:8443"),
    ("http://example.com", "example.com"),
])
def test_the_host_is_normalised_before_matching(url, host):
    assert routes.normalise_host(url) == host


def test_a_url_with_no_port_never_matches_a_host_port_pattern():
    """⚠ The scheme's default port is deliberately NOT invented.

    Inventing `:443` would make a `:443` route match every plain `https://` URL
    that never said so — a route firing on lines nobody wrote it for.
    """
    assert routes.resolve(
        routes.normalise_host("https://example.com/a"),
        _table({"example.com:443": "cdp"}), where="t",
    ) is None


# --- the claim reader, and the import it must never do -----------------------

def _fetcher(tmp_path, name, body):
    d = tmp_path / ".fux" / "fetchers"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")
    return d


def test_a_routes_claim_is_read_from_source(tmp_path):
    d = _fetcher(tmp_path, "cdp.py", 'ROUTES = {"*.wiki.test": "cdp"}\ndef fetch(url): ...\n')
    assert routes.claims(d) == {"*.wiki.test": ("cdp", "cdp.py")}


def test_no_routes_means_no_claims(tmp_path):
    d = _fetcher(tmp_path, "http.py", "def fetch(url): ...\n")
    assert routes.claims(d) == {}


def test_resolving_never_imports_a_fetcher(tmp_path, monkeypatch):
    """🔴 The gate. Same shape as `test_doctor_fetcher_bindings`'s.

    The module body below would raise on import. If `claims` ever reads a
    fetcher by importing it, this fails — which is the only way to notice,
    because an imported fetcher that happens not to raise looks identical.
    """
    d = _fetcher(
        tmp_path, "boom.py",
        'raise AssertionError("a fetcher was IMPORTED to resolve a route")\n'
        'ROUTES = {"boom.test": "boom"}\n',
    )
    import importlib

    def _never(*args, **kwargs):  # pragma: no cover - the point is it is not called
        raise AssertionError("import_module reached on the resolve path")

    monkeypatch.setattr(importlib, "import_module", _never)
    assert routes.claims(d) == {"boom.test": ("boom", "boom.py")}


@pytest.mark.parametrize("body", [
    "ROUTES = []\n",
    'ROUTES = {"a.test": 7}\n',
    'ROUTES = {1: "cdp"}\n',
    'ROUTES = dict(a="cdp")\n',
])
def test_a_malformed_claim_is_a_HARD_ERROR_naming_the_file(tmp_path, body):
    """⚠ Not a skip. A claim fux silently could not read is a routing rule its
    author believes is in force — the same defect an ignored config key is."""
    d = _fetcher(tmp_path, "bad.py", body)
    with pytest.raises(FuxError, match="bad.py"):
        routes.claims(d)


def test_two_fetchers_claiming_one_pattern_is_refused(tmp_path):
    d = _fetcher(tmp_path, "a.py", 'ROUTES = {"x.test": "a"}\n')
    (d / "b.py").write_text('ROUTES = {"x.test": "b"}\n', encoding="utf-8")
    with pytest.raises(FuxError, match="two fetchers claim"):
        routes.claims(d)


def test_the_same_claim_twice_is_not_a_collision(tmp_path):
    """Two files agreeing is not ambiguity — only disagreement is."""
    d = _fetcher(tmp_path, "a.py", 'ROUTES = {"x.test": "cdp"}\n')
    (d / "b.py").write_text('ROUTES = {"x.test": "cdp"}\n', encoding="utf-8")
    assert routes.claims(d)["x.test"][0] == "cdp"


def test_a_missing_fetchers_directory_is_empty_not_an_error(tmp_path):
    assert routes.claims(tmp_path / "nope") == {}


# --- one resolver, and the answer path reaches it ----------------------------

def test_the_answer_path_resolves_through_resolve_urls_and_nothing_else(monkeypatch, tmp_path):
    """🔴 W-199 DoD 3: `urlsrc.resolve_urls` is the ONLY resolver.

    Verifying with a *different* fetcher than a document was ingested with
    compares a rendered page against a shell and reports a **false staleness on
    every query**, with nothing visibly wrong. A second resolution path in the
    answer plane is how the two come apart, so this asserts the answer plane
    goes through the one function rather than re-deriving a path.
    """
    from fux.ingest import urlsrc
    from fux.query import refer_answer

    seen = []
    real = urlsrc.resolve_urls

    def _spy(entries, source):
        seen.append(source)
        return real(entries, source)

    monkeypatch.setattr(urlsrc, "resolve_urls", _spy)

    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\nmax_parallel = 4\n', encoding="utf-8"
    )
    fetchers = tmp_path / ".fux" / "fetchers"
    fetchers.mkdir(parents=True)
    (fetchers / "http.py").write_text('def fetch(url):\n    return "# T\\n\\nbody\\n"\n', encoding="utf-8")
    src = tmp_path / ".fux" / "sources"
    src.mkdir(parents=True, exist_ok=True)
    (src / "urls").write_text("https://x.test/a fetch=http\n", encoding="utf-8")

    fetch, close, _ = refer_answer._load_fetchers(
        tmp_path, [("url:https://x.test/a", "https://x.test/a", "sha")]
    )
    try:
        assert seen, "the answer path did not reach urlsrc.resolve_urls"
    finally:
        close()


def test_fetcher_for_joins_the_declared_directory_and_nothing_else():
    """⚠ The directory is FIXED since 2026-09-20 (W-199 D2).

    It used to be the parent of `[sources.url] fetcher`, so a consumer could
    relocate every fetcher with one key. That key is deleted and the directory
    is SR-DOTFUX's declared `.fux/fetchers/` — which is where it always pointed
    in practice, and the loss is stated in `config.FETCHERS_DIR`'s docstring
    rather than left to be discovered.
    """
    from fux.config import FETCHERS_DIR
    from fux.ingest.urlsrc import fetcher_for

    assert fetcher_for("cdp") == f"{FETCHERS_DIR}/cdp.py"
