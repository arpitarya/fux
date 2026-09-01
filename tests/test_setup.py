"""`fux setup` — the second scaffolding moment (ADR-DOTFUX decision 6).

Two rules carry the whole design and both are cheap to break silently:
**`ensure_layout` never writes a fetcher**, so a plain `fux ingest` cannot put
code into a repo that only wanted an index; and **everything setup writes is
write-if-missing**, so an edited fetcher survives every later run.
"""

from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

from fux import setup as setup_mod
from fux.store import fuxdir

TEMPLATES = Path(__file__).resolve().parents[1] / "src" / "fux" / "templates"


def _load(path: Path, name: str):
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


# -- what ships ------------------------------------------------------------


def test_both_fetchers_ship_as_package_data_never_as_modules():
    for template in setup_mod.FETCHERS.values():
        path = TEMPLATES / template
        assert path.is_file(), f"{template} is missing from the wheel's package data"
        assert path.suffix == ".txt"
    assert not (TEMPLATES / "__init__.py").exists()  # not a package; nothing here imports


def test_the_engine_never_imports_a_fetcher():
    """ADR-FETCHER decision 1 — a fetcher fux imports is a fetcher fux owns."""
    offenders = []
    for path in (Path(__file__).resolve().parents[1] / "src" / "fux").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) and "templates" in stripped:
                offenders.append(f"{path.name}: {stripped}")
    assert not offenders, offenders


def test_template_bytes_reads_out_of_the_installed_package():
    assert setup_mod.template_bytes("http.py.txt").startswith(b'"""Consumer-owned URL fetcher')


def test_both_fetchers_satisfy_the_contract():
    for name, template in setup_mod.FETCHERS.items():
        module = _load(TEMPLATES / template, f"fetcher_{name.replace('.', '_')}")
        assert callable(module.fetch), f"{name} defines no fetch(url)"
        assert callable(module.configure)


def test_neither_shipped_fetcher_converts_anything():
    """W-86 P8 replaced this test's subject rather than its assertion.

    It used to assert the two fetchers produced **identical markdown**, because
    `fetch=` is routing and not a property of the document — if the two passes
    diverged, which fetcher retrieved a page would change the committed index.
    That property now holds **by construction**: neither file converts at all,
    both return bytes, and one decoder runs afterwards.

    Asserting absence rather than agreement matters. A test that two copies
    agree passes right up until someone edits one.
    """
    for name in ("http.py.txt", "cdp.py.txt"):
        source = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "_MdParser" not in source, name
        assert "html_to_markdown" not in source, name
        assert "-> tuple[bytes, str]" in source, name

def test_the_http_fetcher_rejects_an_unknown_config_key():
    module = _load(TEMPLATES / "http.py.txt", "http_fetcher_cfg")
    module.configure({"timeout_s": 5, "user_agent": "x"})
    assert module.TIMEOUT_S == 5.0
    with pytest.raises(module.FetcherError, match="unknown key"):
        module.configure({"timout_s": 5})


# -- what setup does -------------------------------------------------------


def test_setup_writes_both_fetchers_and_both_source_lists(tmp_path):
    report = setup_mod.run(tmp_path)
    assert (tmp_path / ".fux" / "fetchers" / "http.py").is_file()
    assert (tmp_path / ".fux" / "fetchers" / "cdp.py").is_file()
    assert (tmp_path / ".fux" / "sources" / "dirs").is_file()
    assert (tmp_path / ".fux" / "sources" / "urls").is_file()
    assert ".fux/fetchers/http.py" in report.written
    assert report.kept == []


def test_the_default_fetcher_path_resolves_to_a_file_after_setup(tmp_path):
    """W-51: `DEFAULT_FETCHER` named a file that did not exist."""
    from fux.config import DEFAULT_FETCHER

    setup_mod.run(tmp_path)
    assert (tmp_path / DEFAULT_FETCHER).is_file()


def test_setup_never_overwrites_an_edited_fetcher(tmp_path):
    setup_mod.run(tmp_path)
    edited = tmp_path / ".fux" / "fetchers" / "http.py"
    edited.write_text("# mine now\n", encoding="utf-8")
    report = setup_mod.run(tmp_path)
    assert edited.read_text(encoding="utf-8") == "# mine now\n"
    assert ".fux/fetchers/http.py" in report.kept
    assert report.written == []


def test_setup_never_overwrites_an_edited_source_list(tmp_path):
    setup_mod.run(tmp_path)
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.write_text("handbook\n", encoding="utf-8")
    setup_mod.run(tmp_path)
    assert listing.read_text(encoding="utf-8") == "handbook\n"


def test_setup_seeds_the_dirs_list_from_what_the_repo_actually_has(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("# r\n", encoding="utf-8")
    setup_mod.run(tmp_path)
    lines = (tmp_path / ".fux" / "sources" / "dirs").read_text(encoding="utf-8").splitlines()
    assert [line for line in lines if line and not line.startswith("#")] == ["README.md", "docs"]


def test_setup_seeds_nothing_it_cannot_see(tmp_path):
    setup_mod.run(tmp_path)
    lines = (tmp_path / ".fux" / "sources" / "dirs").read_text(encoding="utf-8").splitlines()
    assert [line for line in lines if line and not line.startswith("#")] == []


def test_setup_writes_a_types_file_ingest_can_actually_read(tmp_path):
    """The setup -> ingest path, which shipped broken.

    `_TYPES_HEADER` is comments end to end, and `read_types` raises on a file
    with no active pattern — so `fux setup` followed by `fux ingest` failed on
    every fresh repo with "lists no file types". Nothing asserted the two verbs
    composed, which is exactly why it got out.
    """
    from fux.ingest.gitdir import DEFAULT_TYPES, read_types

    setup_mod.run(tmp_path)
    types = read_types(tmp_path)  # must not raise
    assert set(types.allow) == set(DEFAULT_TYPES)
    assert types.deny == ()


def test_the_written_types_file_spells_the_default_out_as_live_lines(tmp_path):
    """ADR-TYPES decision 10 — visible without reading fux's source.

    Since decision 11 the written line also states its **binding**, so what is
    visible is the whole map: the pattern, and the module that reads it.
    """
    from fux.decode import builtin_bindings
    from fux.ingest.gitdir import DEFAULT_TYPES

    setup_mod.run(tmp_path)
    text = (tmp_path / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    active = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    assert active, "a header alone is not a types file"

    bindings = builtin_bindings()
    expected = [
        f"{glob} decoder={bindings[glob[1:].lower()]}"
        if glob[1:].lower() in bindings
        else glob
        for glob in DEFAULT_TYPES
    ]
    assert sorted(active) == sorted(expected)


def test_a_freshly_set_up_repo_indexes_its_own_readme(tmp_path):
    """End to end: the two verbs compose, and the default actually matches."""
    from fux.ingest.gitdir import read_types, walk_sources

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("# note\n", encoding="utf-8")
    setup_mod.run(tmp_path)
    walked, _ = walk_sources(tmp_path, ["docs"], types=read_types(tmp_path))
    assert [w.rel_path for w in walked] == ["docs/note.md"]


def test_setup_never_overwrites_an_edited_types_file(tmp_path):
    setup_mod.run(tmp_path)
    listing = tmp_path / ".fux" / "sources" / "types"
    listing.write_text("*.md\n", encoding="utf-8")
    setup_mod.run(tmp_path)
    assert listing.read_text(encoding="utf-8") == "*.md\n"


def test_setup_bootstraps_a_bare_directory(tmp_path, monkeypatch, capsys):
    """The one verb that may run before a root exists — it *creates* the marker."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("fux.setup.find_root", lambda: None)
    assert setup_mod.cmd_setup(object()) == 0
    assert (tmp_path / "fux.toml").is_file()
    assert "wrote fux.toml" in capsys.readouterr().out


def test_setup_never_overwrites_an_edited_config(tmp_path):
    (tmp_path / "fux.toml").write_text('[sources]\ndirs_file = "mine"\n', encoding="utf-8")
    report = setup_mod.run(tmp_path)
    assert (tmp_path / "fux.toml").read_text(encoding="utf-8").endswith('dirs_file = "mine"\n')
    assert "fux.toml" in report.kept


def test_the_generated_config_loads(tmp_path):
    from fux.config import load

    setup_mod.run(tmp_path)
    config = load(tmp_path)
    assert config.dirs_file == ".fux/sources/dirs"
    assert config.shards == 256
    # ⚠ CHANGED BY W-85. This asserted `config.url is None` — `[sources.url]`
    # shipped commented out, which is what made the concurrency bound invisible.
    # The table is live now and the OPT-IN MOVED TO THE URL LIST: `[sources.url]`
    # says *how* to fetch, `.fux/sources/urls` says *whether*, and it is empty.
    assert config.url is not None
    # ...and the list it points at is header comments only. Not one address, so
    # nothing can be fetched: the opt-in is a URL existing, not a table existing.
    from fux.ingest import sourcelist

    listed = sourcelist.parse(
        (tmp_path / config.url.urls_file).read_text(encoding="utf-8"),
        sourcelist.URLS,
        origin=config.url.urls_file,
    )
    assert listed == []


# -- W-85: the concurrency knob is PRESENT, LIVE and REQUIRED ---------------


def test_the_written_config_names_max_parallel_uncommented(tmp_path):
    """Arpit, 2026-08-26: *"I wanted a property exposed. Where is that property?
    It should be present by default."* — then, on being shown a commented line:
    *"never commented. If it is commented, throw an error."*

    W-83 wrote `#max_parallel = 4` inside a commented table, so a consumer
    opening `fux.toml` saw a comment about a number rather than a number.
    """
    from fux.ingest.urlsrc import DEFAULT_MAX_PARALLEL

    setup_mod.run(tmp_path)
    written = (tmp_path / "fux.toml").read_text(encoding="utf-8")
    assert f"\nmax_parallel = {DEFAULT_MAX_PARALLEL}\n" in written, "must be live, not commented"
    assert f"#max_parallel" not in written
    assert "\n[sources.url]\n" in written
    assert "min(this, what your fetcher declares)" in written


def test_the_configs_stated_default_is_the_one_the_engine_applies(tmp_path):
    """The gate, not the trust. A number typed into the template drifts from the
    constant beside it — which is the defect W-83 fixed one file over. `_CONFIG`
    interpolates `DEFAULT_MAX_PARALLEL`; this fails if anyone flattens it."""
    from fux.config import load
    from fux.ingest.urlsrc import DEFAULT_MAX_PARALLEL

    setup_mod.run(tmp_path)
    assert "{default}" not in (tmp_path / "fux.toml").read_text(encoding="utf-8")
    assert load(tmp_path).url.max_parallel == DEFAULT_MAX_PARALLEL


def test_commenting_max_parallel_out_makes_the_config_refuse_to_load(tmp_path):
    """The half of the ruling a template alone cannot deliver.

    `fux setup` is write-if-missing, so it never reaches a `fux.toml` that
    already exists — this repo's own included. **The loader error is the
    migration path**: it puts the key in front of the person on their next
    command, with the value to type.
    """
    from fux.config import load
    from fux.errors import FuxError

    setup_mod.run(tmp_path)
    path = tmp_path / "fux.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\nmax_parallel = ", "\n#max_parallel = "),
        encoding="utf-8",
    )
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    message = str(exc.value)
    assert "max_parallel must be present" in message
    assert "max_parallel = " in message, "an error that does not say what to type is half a migration"


def test_a_repo_with_no_url_source_at_all_is_not_forced_to_declare_one(tmp_path):
    """The line W-85 draws. A docs-only repo fetches nothing, so there is
    nothing to bound, and demanding a bound there would make the key noise —
    which is how a safety value stops being read."""
    from fux.config import load

    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    assert load(tmp_path).url is None


# -- the rule that keeps ingest out of the code business -------------------


def test_ensure_layout_writes_no_fetcher_and_no_source_list(tmp_path):
    """The whole reason `fux setup` exists as a separate verb."""
    fuxdir.ensure_layout(tmp_path)
    assert not (tmp_path / ".fux" / "fetchers").exists()
    assert not (tmp_path / ".fux" / "sources").exists()
    assert sorted(p.name for p in (tmp_path / ".fux").iterdir()) == [".gitignore", "README.md"]


def test_a_plain_ingest_puts_no_code_in_the_repo(tmp_path):
    from fux.ingest.run import run as ingest

    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")

    ingest(tmp_path)
    assert not (tmp_path / ".fux" / "fetchers").exists()
