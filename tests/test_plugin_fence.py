"""L5's import fence, extended to the plugin packages (SR-PLUGINS P10, W-289).

A fetcher package carries network code — `fux-fetcher-cdp` a WebSocket client —
so it ships as its own distribution, and **fux executes one only when a URL line
names it, on a fenced path.** Three things hold that:

1. **No module under `src/fux/` imports a plugin package by name.** The one way
   in is `plugins.load`, with a computed name, after `plugins.verify` (P4/P7).
2. **The offline paths never call `plugins.load`**: `fux ingest --no-fetch` —
   what the git hooks run — and `fux doctor`, in a repository that DECLARES both
   fetchers and lists URL lines for them.
3. **A declared package that has drifted is refused before a byte is fetched**
   (P4 / P13's half that phase 1 can hold): the fetch never runs.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from fux import __version__, plugins
from fux import setup as setup_mod
from fux.acquire import urlsrc
from fux.cli import main
from fux.errors import FuxError
from l12_fixtures import write_urls

SRC = Path(__file__).resolve().parents[1] / "src" / "fux"
PREFIXES = ("fux_decoder_", "fux_fetcher_", "fux_extension_")


def test_no_engine_module_imports_a_plugin_package_by_name():
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for name in names:
                assert not name.startswith(PREFIXES), f"{path}: imports {name} by name"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    """A repository declaring both shipped fetchers, with a URL line for each."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    setup_mod.run(tmp_path, agents=False)
    config = tmp_path / "fux.toml"
    text = config.read_text(encoding="utf-8")
    if "[sources.url]\n" not in text:
        text = text.replace("[sources.url.config]", "[sources.url]\n\n[sources.url.config]", 1)
    config.write_text(text, encoding="utf-8")
    write_urls(tmp_path, "https://x.test/a fetch=http decoder=html\nhttps://x.test/b fetch=cdp decoder=html\n")
    plugins.reset()
    rows = [plugins.pin(n) for n in ("fux-fetcher-http", "fux-fetcher-cdp", "fux-decoder-html", "fux-extension-table")]
    plugins.path(tmp_path).write_text(plugins.render(rows), encoding="utf-8")
    plugins.reset()
    monkeypatch.chdir(tmp_path)
    yield tmp_path
    plugins.reset()


def _forbid_load(monkeypatch) -> list[str]:
    calls: list[str] = []

    def refuse(decl):
        calls.append(decl.name)
        raise AssertionError(f"an offline path executed {decl.name}")

    monkeypatch.setattr(plugins, "load", refuse)
    return calls


def test_ingest_no_fetch_never_executes_a_fetcher_package(repo, monkeypatch):
    calls = _forbid_load(monkeypatch)
    assert main(["ingest", "--no-fetch"]) == 0
    assert calls == []


def test_doctor_never_executes_a_fetcher_package(repo, monkeypatch):
    from fux import doctor

    calls = _forbid_load(monkeypatch)
    checks = doctor.run(repo)
    assert calls == []
    by_name = {c.name: c for c in checks}
    assert by_name["plugins installed"].ok, by_name["plugins installed"].detail
    assert by_name["fetcher bindings"].ok, by_name["fetcher bindings"].detail


def test_a_url_line_reaches_its_declared_package_through_load(repo, monkeypatch):
    """The fenced path DOES reach it — through `plugins.load`, and only there."""
    seen: list[str] = []
    real = plugins.load

    def spy(decl):
        seen.append(decl.name)
        return real(decl)

    monkeypatch.setattr(plugins, "load", spy)
    module = urlsrc.load_fetcher(repo, urlsrc.fetcher_for("http"))
    assert callable(module.fetch)
    assert seen == ["fux-fetcher-http"]


def test_a_drifted_fetcher_package_is_refused_before_any_fetch(repo):
    """P4 / P13: a declared package at a different version is a hard error."""
    text = plugins.path(repo).read_text(encoding="utf-8")
    cdp = f'name = "fux-fetcher-cdp"\nversion = "{__version__}"'
    assert cdp in text
    plugins.path(repo).write_text(
        text.replace(cdp, 'name = "fux-fetcher-cdp"\nversion = "0.0.1"'), encoding="utf-8"
    )
    plugins.reset()
    with pytest.raises(FuxError, match=r"0\.0\.1.*pip install"):
        urlsrc.load_fetcher(repo, urlsrc.fetcher_for("cdp"))


def test_an_installed_but_undeclared_fetcher_package_is_never_loaded(repo):
    """P3 / P13: `fux-fetcher-http` is installed here; undeclare it and the
    line that names it fails with the package named, rather than running it."""
    rows = [d for n, d in plugins.declared(repo).items() if n != "fux-fetcher-http"]
    plugins.path(repo).write_text(plugins.render(rows), encoding="utf-8")
    plugins.reset()
    with pytest.raises(FuxError, match="fux-fetcher-http"):
        urlsrc.load_fetcher(repo, urlsrc.fetcher_for("http"))


def test_a_consumer_file_overrides_the_declared_package(repo):
    """P8: the file in `.fux/fetchers/` wins, and the package is not loaded."""
    fetchers = repo / ".fux" / "fetchers"
    fetchers.mkdir(parents=True, exist_ok=True)
    (fetchers / "http.py").write_text(
        "OVERRIDE = True\ndef fetch(url):\n    return b'<p>x</p>', 'text/html'\n", encoding="utf-8"
    )
    module = urlsrc.load_fetcher(repo, urlsrc.fetcher_for("http"))
    assert getattr(module, "OVERRIDE", False) is True
