"""`src/fux/plugins.py` — SR-PLUGINS (W-289): declared, pinned, refused loudly.

Each test names the decision it holds. The packages it verifies against are the
fifteen first-party ones, installed editable from `packages/` by
`uv sync --extra dev` — real distributions with real metadata, so P4 is checked
against `importlib.metadata` rather than a mock of it.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

from fux import __version__, plugins
from fux import setup as setup_mod
from fux.constants import fixed, table
from fux.errors import FuxError
from l12_fixtures import listed_paths, write_dirs, write_urls

HTTP = "fux-fetcher-http"


@pytest.fixture(autouse=True)
def _fresh_cache():
    plugins.reset()
    yield
    plugins.reset()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    setup_mod.run(tmp_path, agents=False)
    plugins.reset()
    return tmp_path


def _declare(root: Path, text: str) -> None:
    plugins.path(root).parent.mkdir(parents=True, exist_ok=True)
    plugins.path(root).write_text(text, encoding="utf-8")
    plugins.reset()


def _row(name: str, version: str = __version__, digest: str | None = None, extra: str = "") -> str:
    if digest is None:
        digest = plugins.installed_digest(plugins.package_named(name).module) or ""
    return f'[[package]]\nname = "{name}"\nversion = "{version}"\ndigest = "{digest}"\n{extra}\n'


# -- the first-party table -----------------------------------------------------


def test_the_first_party_table_is_the_fifteen_packages_of_the_item():
    names = set(plugins.first_party())
    assert len(names) == 15
    assert {HTTP, "fux-fetcher-cdp", "fux-extension-table", "fux-decoder-pdf"} <= names


def test_every_first_party_package_is_a_directory_under_packages():
    root = Path(__file__).resolve().parents[1]
    for name, pkg in plugins.first_party().items():
        assert (root / "packages" / name / "src" / pkg.module / "__init__.py").is_file(), name


def test_no_two_first_party_packages_claim_one_suffix():
    seen: dict[str, str] = {}
    for name, pkg in plugins.first_party().items():
        for suffix in pkg.suffixes:
            assert suffix not in seen, f"{suffix}: {seen.get(suffix)} and {name}"
            seen[suffix] = name


def test_the_table_carries_every_built_in_decoder_module_exactly_once():
    """The P12 register column and phase 2's move both read `modules`."""
    from fux.decode import BUILTIN_MODULES

    modules = [m for pkg in plugins.first_party().values() for m in pkg.modules]
    assert sorted(modules) == sorted(BUILTIN_MODULES)


def test_the_import_name_follows_the_naming_rule():
    """P7: `fux-<kind>-<subject>` -> `fux_<kind>_<subject>`, and nothing else."""
    assert plugins.first_party()[HTTP].module == "fux_fetcher_http"
    assert plugins.package_named("fux-decoder-my-format").module == "fux_decoder_my_format"
    for bad in ("fux-thing-x", "decoder-x", "fux-decoder-", "fux-decoder-X"):
        with pytest.raises(FuxError, match="not a plugin package name"):
            plugins.split_name(bad)


def test_the_html_sheet_and_office_decoders_depend_on_the_table_extension():
    fp = plugins.first_party()
    for name in ("fux-decoder-html", "fux-decoder-sheet", "fux-decoder-office"):
        assert fp[name].depends == ("fux-extension-table",)
    assert plugins.closure(["fux-decoder-html"]) == ["fux-decoder-html", "fux-extension-table"]


# -- P2: the file -----------------------------------------------------------------


def test_a_missing_file_is_none_and_declares_nothing(tmp_path):
    assert plugins.read(tmp_path) is None
    assert plugins.declared(tmp_path) == {}
    assert not plugins.is_suffix_declared(tmp_path, ".pdf")


def test_the_file_parses_to_rows_sorted_by_name(tmp_path):
    _declare(tmp_path, _row("fux-decoder-pdf") + _row("fux-decoder-json"))
    assert list(plugins.declared(tmp_path)) == ["fux-decoder-json", "fux-decoder-pdf"]


@pytest.mark.parametrize(
    "text, match",
    [
        ("nonsense = 1\n", "unknown top-level"),
        ('[[package]]\nversion = "1"\n', "has no `name`"),
        ('[[package]]\nname = "fux-decoder-pdf"\n', "no `version`"),
        ('[[package]]\nname = "fux-decoder-pdf"\nversion = "1"\ndigest = "md5:x"\n', "digest"),
        ('[[package]]\nname = "fux-decoder-pdf"\nversion = "1"\ncolour = "red"\n', "unknown key"),
        (
            '[[package]]\nname = "fux-decoder-pdf"\nversion = "1"\n'
            '[[package]]\nname = "fux-decoder-pdf"\nversion = "1"\n',
            "declared twice",
        ),
        ('[[package]]\nname = "fux-decoder-pdf"\nversion = "1"\nsuffixes = [".x"]\n', "first-party"),
        ('[[package]]\nname = "fux-decoder-acme"\nversion = "1"\n', "must state the `suffixes`"),
        ('[[package]]\nname = "fux-fetcher-acme"\nversion = "1"\nsuffixes = [".x"]\n', "only a decoder"),
        ('[[package]]\nname = "acme-decoder"\nversion = "1"\n', "not a plugin package name"),
        ("[[package\n", "not valid TOML"),
    ],
)
def test_a_malformed_declaration_is_refused_by_name(tmp_path, text, match):
    _declare(tmp_path, text)
    with pytest.raises(FuxError, match=match):
        plugins.read(tmp_path)


def test_two_declared_packages_may_not_claim_one_suffix(tmp_path):
    _declare(
        tmp_path,
        _row("fux-decoder-pdf")
        + '[[package]]\nname = "fux-decoder-acme"\nversion = "1"\nsuffixes = [".pdf"]\n',
    )
    with pytest.raises(FuxError, match=r"\.pdf is claimed by both"):
        plugins.read(tmp_path)


def test_the_file_is_read_once_per_process(tmp_path, monkeypatch):
    """P2: parsed once per process while it is unchanged — a 10 000-document
    walk asks for it per file — and re-read when it changes (W-289 phase 2:
    the cache is keyed on the file's stat, as `decode.registry()`'s is, so a
    long-lived `fux mcp` sees an edited declaration)."""
    _declare(tmp_path, _row("fux-decoder-pdf"))
    calls = []
    real = plugins._parse  # one parse yields both the package and the index rows
    monkeypatch.setattr(plugins, "_parse", lambda *a: calls.append(a) or real(*a))
    for _ in range(3):
        assert list(plugins.declared(tmp_path)) == ["fux-decoder-pdf"]
    assert len(calls) == 1
    plugins.path(tmp_path).write_text("", encoding="utf-8")
    assert plugins.declared(tmp_path) == {}
    assert len(calls) == 2


def test_render_round_trips_through_parse(tmp_path):
    rows = [plugins.pin("fux-decoder-pdf"), plugins.pin(HTTP)]
    text = plugins.render(rows)
    parsed = plugins.parse(text, "x")
    assert [d for d in parsed.values()] == sorted(rows, key=lambda d: d.name)


def test_render_is_byte_identical_whatever_the_row_order():
    """L4: the declaration's bytes never depend on the order rows were found in."""
    a, b = plugins.pin("fux-decoder-pdf"), plugins.pin(HTTP)
    assert plugins.render([a, b]) == plugins.render([b, a])


# -- P3: declared, never detected -------------------------------------------------


def test_an_installed_package_nobody_declared_is_never_consulted(tmp_path):
    """P3. `fux-fetcher-http` IS installed in this environment."""
    assert plugins.installed_version(HTTP) == __version__
    assert plugins.for_fetch(tmp_path, "http") is None
    assert plugins.resolve(tmp_path, "fetcher", "http").how is None


def test_a_declared_package_answers_for_its_suffixes_and_fetch_name(tmp_path):
    _declare(tmp_path, _row("fux-decoder-config") + _row(HTTP))
    assert plugins.for_suffix(tmp_path, ".YML").name == "fux-decoder-config"
    assert plugins.is_suffix_declared(tmp_path, ".toml")
    assert not plugins.is_suffix_declared(tmp_path, ".pdf")
    assert plugins.for_fetch(tmp_path, "http").name == HTTP
    assert plugins.for_decoder_module(tmp_path, "yaml").name == "fux-decoder-config"


def test_a_third_party_decoder_claims_what_it_states(tmp_path):
    _declare(tmp_path, '[[package]]\nname = "fux-decoder-acme"\nversion = "1.0"\nsuffixes = [".ACME"]\n')
    decl = plugins.for_suffix(tmp_path, ".acme")
    assert decl is not None and not decl.package.first_party
    assert decl.package.module == "fux_decoder_acme"


# -- P4: pinned, refused when missing or drifted ---------------------------------


def test_a_correctly_pinned_package_passes(tmp_path):
    _declare(tmp_path, _row("fux-decoder-pdf"))
    assert plugins.problems(tmp_path) == []
    plugins.verify(plugins.declared(tmp_path)["fux-decoder-pdf"])


def test_a_declared_package_that_is_not_installed_names_the_install_line(tmp_path):
    _declare(tmp_path, '[[package]]\nname = "fux-decoder-acme"\nversion = "2.0"\ndigest = ""\nsuffixes = [".acme"]\n')
    with pytest.raises(FuxError) as exc:
        plugins.verify(plugins.declared(tmp_path)["fux-decoder-acme"])
    message = str(exc.value)
    assert "fux-decoder-acme" in message and "not installed" in message
    assert "pip install fux-decoder-acme==2.0" in message


def test_a_first_party_pin_off_fuxs_version_is_refused(tmp_path):
    _declare(tmp_path, _row("fux-decoder-pdf", version="0.0.1"))
    (problem,) = plugins.problems(tmp_path)
    assert "0.0.1" in problem and __version__ in problem
    assert f"pip install fux-decoder-pdf=={__version__}" in problem
    assert "fux setup --pin" in problem


def test_a_drifted_digest_names_both_digests_and_the_lever(tmp_path):
    wrong = fixed("plugins", "digest_prefix") + "0" * 64
    _declare(tmp_path, _row(HTTP, digest=wrong))
    with pytest.raises(FuxError) as exc:
        plugins.verify(plugins.declared(tmp_path)[HTTP])
    message = str(exc.value)
    assert "drifted" in message and wrong in message
    assert plugins.installed_digest("fux_fetcher_http") in message
    assert f"pip install {HTTP}=={__version__}" in message


def test_an_unpinned_row_is_refused_until_it_is_pinned(tmp_path):
    _declare(tmp_path, _row("fux-decoder-pdf", digest=""))
    (problem,) = plugins.problems(tmp_path)
    assert "without a digest" in problem and "fux setup --pin" in problem


def test_require_refuses_with_every_problem_named(tmp_path):
    _declare(tmp_path, _row(HTTP, digest="") + _row("fux-decoder-pdf", version="0.0.1"))
    with pytest.raises(FuxError, match=r"SR-PLUGINS P4") as exc:
        plugins.require(tmp_path)
    assert HTTP in str(exc.value) and "fux-decoder-pdf" in str(exc.value)


def test_a_declared_dependency_must_be_declared_too(tmp_path):
    _declare(tmp_path, _row("fux-decoder-html"))
    (problem,) = plugins.problems(tmp_path)
    assert "needs fux-extension-table" in problem


def test_a_fetcher_without_the_html_decoder_is_refused(tmp_path):
    """P10: every fetcher returns HTML, so a fetcher alone indexes nothing."""
    _declare(tmp_path, _row(HTTP))
    (problem,) = plugins.problems(tmp_path)
    assert "fux-decoder-html" in problem and "P10" in problem
    _declare(tmp_path, _row(HTTP) + _row("fux-decoder-html") + _row("fux-extension-table"))
    assert plugins.problems(tmp_path) == []


def test_the_digest_is_the_same_spelled_from_record_lines():
    """The digest is RECORD's line format over the import package's files —
    stable across pip, uv, an editable checkout and a wheel."""
    import base64
    import hashlib

    spec_dir = Path(sys.modules["fux"].__file__).resolve().parents[2] / "packages"
    init = spec_dir / "fux-fetcher-http" / "src" / "fux_fetcher_http" / "__init__.py"
    raw = init.read_bytes().replace(b"\r\n", b"\n")
    line = "fux_fetcher_http/__init__.py,sha256=" + base64.urlsafe_b64encode(
        hashlib.sha256(raw).digest()
    ).rstrip(b"=").decode("ascii")
    want = "sha256:" + hashlib.sha256(line.encode("utf-8")).hexdigest()
    assert plugins.installed_digest("fux_fetcher_http") == want


def test_locating_a_package_to_hash_it_never_imports_it():
    """L5: `fux doctor` hashes a declared fetcher without running its code."""
    sys.modules.pop("fux_fetcher_cdp", None)
    assert plugins.installed_digest("fux_fetcher_cdp")
    assert "fux_fetcher_cdp" not in sys.modules


# -- P7 / P8: loading by fixed name, and precedence --------------------------------


def test_load_verifies_first_and_refuses_a_drifted_package(tmp_path):
    _declare(tmp_path, _row(HTTP, digest=fixed("plugins", "digest_prefix") + "1" * 64))
    with pytest.raises(FuxError, match="drifted"):
        plugins.load(plugins.declared(tmp_path)[HTTP])


def test_load_returns_a_fresh_module_each_call_and_registers_none(tmp_path):
    """A fetcher's `configure()` writes module globals; sharing one module
    across calls would carry one run's settings into the next."""
    _declare(tmp_path, _row(HTTP))
    decl = plugins.declared(tmp_path)[HTTP]
    sys.modules.pop("fux_fetcher_http", None)
    one, two = plugins.load(decl), plugins.load(decl)
    assert one is not two
    assert callable(one.fetch)
    assert "fux_fetcher_http" not in sys.modules


def test_a_consumer_file_beats_the_declared_package(tmp_path):
    """P8."""
    _declare(tmp_path, _row(HTTP))
    assert plugins.resolve(tmp_path, "fetcher", "http").how == "package"
    override = tmp_path / fixed("files", "fetchers_dir") / "http.py"
    override.parent.mkdir(parents=True, exist_ok=True)
    override.write_text("def fetch(url):\n    return b'', 'text/html'\n", encoding="utf-8")
    resolved = plugins.resolve(tmp_path, "fetcher", "http")
    assert resolved.how == "override" and resolved.path == override


def test_a_decoder_override_resolves_by_module_name(tmp_path):
    _declare(tmp_path, _row("fux-decoder-config"))
    assert plugins.resolve(tmp_path, "decoder", "yaml").how == "package"
    (tmp_path / ".fux" / "decoders").mkdir(parents=True)
    (tmp_path / ".fux" / "decoders" / "yaml.py").write_text("", encoding="utf-8")
    assert plugins.resolve(tmp_path, "decoder", "yaml").how == "override"
    assert plugins.resolve(tmp_path, "decoder", "pdf").how is None


def test_fetcher_names_are_the_files_and_the_declared_packages(tmp_path):
    _declare(tmp_path, _row(HTTP))
    (tmp_path / ".fux" / "fetchers").mkdir(parents=True)
    (tmp_path / ".fux" / "fetchers" / "glassbox.py").write_text("", encoding="utf-8")
    assert plugins.fetcher_names(tmp_path) == ["glassbox", "http"]


# -- P5 / P6: the scan --------------------------------------------------------------


def test_the_scan_counts_suffixes_in_the_configured_sources(repo):
    (repo / "docs" / "spec.PDF").write_bytes(b"%PDF")
    (repo / "docs" / "data.json").write_text("{}", encoding="utf-8")
    (repo / "elsewhere").mkdir()
    (repo / "elsewhere" / "x.pdf").write_bytes(b"%PDF")
    counts = plugins.scan(repo)
    assert counts[".pdf"] == 1 and counts[".json"] == 1 and counts[".md"] == 1


def test_the_scan_prunes_an_excluded_directory_and_never_enters_it(repo, monkeypatch):
    """W-244 / L11: an excluded directory is pruned, not listed and filtered."""
    (repo / "docs" / "sealed").mkdir()
    (repo / "docs" / "sealed" / "key.pdf").write_bytes(b"%PDF")
    # W-294: exclusion lives in `.fux/.fuxignore` only; the helper moves the
    # retired grammar's `!` line there, anchored, as `fux setup` would.
    write_dirs(repo, "".join(f"{p}\n" for p in listed_paths(repo)) + "!docs/sealed\n")
    entered: list[str] = []
    import os

    real = os.walk

    def spy(top, *a, **k):
        for dirpath, dirnames, filenames in real(top, *a, **k):
            entered.append(Path(dirpath).name)
            yield dirpath, dirnames, filenames

    monkeypatch.setattr(os, "walk", spy)
    assert plugins.scan(repo)[".pdf"] == 0
    assert "sealed" not in entered


def test_the_scan_honours_hand_written_ignores_only(repo):
    (repo / "docs" / "skip.pdf").write_bytes(b"%PDF")
    ignore = repo / ".fux" / ".fuxignore"
    ignore.write_text(ignore.read_text(encoding="utf-8") + "docs/skip.pdf\n", encoding="utf-8")
    assert plugins.scan(repo)[".pdf"] == 0


def test_undeclared_names_the_package_and_the_count():
    counts = Counter({".pdf": 3, ".json": 2, ".md": 9, ".py": 4})
    found = {}
    assert plugins.undeclared(counts, found) == {
        ".json": (2, "fux-decoder-json"),
        ".pdf": (3, "fux-decoder-pdf"),
    }
    found = plugins.parse(_row("fux-decoder-pdf"), "x")
    assert plugins.undeclared(counts, found) == {".json": (2, "fux-decoder-json")}


def test_propose_reads_suffixes_url_lines_and_closes_over_dependencies(repo):
    (repo / "docs" / "sheet.csv").write_text("a,b\n", encoding="utf-8")
    write_urls(repo, "https://x.test/a.pdf fetch=cdp decoder=pdf\n")
    assert plugins.propose(repo) == [
        "fux-decoder-html",  # every fetcher emits HTML (P10)
        "fux-decoder-pdf",  # decoder= on the URL line
        "fux-decoder-sheet",  # .csv in the sources
        "fux-extension-table",  # the closure of html and sheet
        "fux-fetcher-cdp",  # fetch= on the URL line
    ]


def test_a_fetch_name_with_a_consumer_file_needs_no_package(repo):
    write_urls(repo, "https://x.test/a fetch=http decoder=prose\n")
    (repo / ".fux" / "fetchers").mkdir(parents=True, exist_ok=True)
    (repo / ".fux" / "fetchers" / "http.py").write_text("", encoding="utf-8")
    assert HTTP not in plugins.propose(repo)


def test_the_install_line_is_one_line_and_sorted():
    line = plugins.install_line([("fux-decoder-pdf", "1"), ("fux-decoder-json", "1")])
    assert line == f"{fixed('plugins', 'install')} fux-decoder-json==1 fux-decoder-pdf==1"


def test_pin_pins_a_first_party_package_at_fuxs_version():
    decl = plugins.pin(HTTP)
    assert decl.version == __version__
    assert decl.digest == plugins.installed_digest("fux_fetcher_http")


def test_the_constants_table_keys_are_the_ones_parse_accepts():
    assert set(fixed("plugins", "keys")) == {"name", "version", "digest", "suffixes"}
    assert set(table("plugins.packages")) == set(plugins.first_party())
