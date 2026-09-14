"""`fux setup` — the second scaffolding moment (SR-DOTFUX decision 6).

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
from fux.ingest.urlsrc import DEFAULT_MAX_PARALLEL
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
    """SR-FETCHER decision 1 — a fetcher fux imports is a fetcher fux owns."""
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


def test_the_written_types_file_spells_the_default_out_as_live_lines(tmp_path):
    """SR-TYPES decision 10 — visible without reading fux's source.

    Since decision 11 the file also states each **binding**, so what is visible
    is the whole map; since decision 12 the map is `[decoders]` and the prose is
    `include`, and a bound extension is not written twice.
    """
    from fux.decode import builtin_bindings
    from fux.ingest import typesfile
    from fux.ingest.gitdir import DEFAULT_TYPES

    setup_mod.run(tmp_path)
    text = (tmp_path / ".fux" / "formats.toml").read_text(encoding="utf-8")
    listed = typesfile.parse(text, origin="formats.toml")
    bindings = {ext.lstrip("."): name for ext, name in builtin_bindings().items()}
    assert listed.decoders == bindings
    assert set(listed.include) == {g for g in DEFAULT_TYPES if typesfile.pattern_extension(g) not in bindings}
    assert '\n  "*.md",\n' in text, "one glob per line - the layout the editor keeps"
    assert '\nhtml = "html"\n' in text


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
    listing = tmp_path / ".fux" / "formats.toml"
    listing.write_text('include = ["*.md"]\n', encoding="utf-8")
    setup_mod.run(tmp_path)
    assert listing.read_text(encoding="utf-8") == 'include = ["*.md"]\n'


# -- SR-TYPES decision 12: the old file is converted, never silently dropped --


def _legacy(root, text):
    (root / ".fux" / "sources").mkdir(parents=True, exist_ok=True)
    (root / ".fux" / "sources" / "types").write_text(text, encoding="utf-8")


def test_setup_converts_a_leftover_line_grammar_types_file(tmp_path, capsys):
    from fux.ingest import typesfile

    _legacy(tmp_path, "# mine\n*.md\ndocs/*.txt\n*.csv decoder=csv\n*.geojson decoder=json\n")
    report = setup_mod.run(tmp_path)
    assert report.converted_types and ".fux/formats.toml" in report.written
    listed = typesfile.parse((tmp_path / ".fux" / "formats.toml").read_text(encoding="utf-8"), origin="t")
    assert listed.include == ("*.md", "docs/*.txt")
    assert listed.decoders == {"csv": "csv", "geojson": "json"}
    assert (tmp_path / ".fux" / "sources" / "types").is_file(), "the old file is the human's to delete"


def test_the_converted_file_states_what_the_old_one_admitted(tmp_path):
    """The whole point: a conversion that changed the allowlist would be the silent
    index change the refusal exists to prevent."""
    from fux.ingest.gitdir import TypeFilter, read_types
    from fux.ingest import sourcelist

    legacy = "*.md\n*.rst\n*.CSV\n*.csv decoder=csv\n*.pdf decoder=pdf\ndocs/**/*.txt\n"
    _legacy(tmp_path, legacy)
    before = TypeFilter(
        allow=tuple(e.value for e in sourcelist.parse(legacy, sourcelist.TYPES, origin="x"))
    )
    setup_mod.run(tmp_path)
    (tmp_path / ".fux" / "sources" / "types").unlink()
    after = read_types(tmp_path)
    for name in ("a.md", "a.rst", "a.csv", "a.CSV", "a.pdf", "docs/x/y.txt", "a.txt", "a.json"):
        assert before.accepts(name) == after.accepts(name), name


def test_an_upper_case_bound_pattern_is_refused_rather_than_converted_wrongly(tmp_path):
    """`*.CSV decoder=csv` admitted `a.CSV`; a `csv` binding admits `a.csv`. Either
    silent conversion changes the allowlist, so setup stops and says so."""
    import pytest

    from fux.errors import FuxError

    _legacy(tmp_path, "*.CSV decoder=csv\n")
    with pytest.raises(FuxError, match="lowercase extension"):
        setup_mod.run(tmp_path)


def test_bang_lines_move_to_fuxignore_above_the_first_hand_pattern(tmp_path):
    """`.fuxignore` is last-match-wins and already outranked the types list, so a
    re-include written there must keep beating the moved line."""
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / ".fuxignore").write_text("# header\n!keep.min.md\n", encoding="utf-8")
    _legacy(tmp_path, "*.md\n!*.min.md\n")
    report = setup_mod.run(tmp_path)
    assert report.moved_exclusions == ["*.min.md"]
    lines = (tmp_path / ".fux" / ".fuxignore").read_text(encoding="utf-8").splitlines()
    assert lines.index("*.min.md") < lines.index("!keep.min.md")
    from fux.ingest import fuxignore

    ignores = fuxignore.read(tmp_path)
    assert ignores.decide("docs/a.min.md").ignored
    assert not ignores.decide("docs/keep.min.md").ignored


def test_setup_leaves_both_files_alone_when_the_new_one_exists(tmp_path):
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "formats.toml").write_text('include = ["*.md"]\n', encoding="utf-8")
    _legacy(tmp_path, "*.rst\n")
    report = setup_mod.run(tmp_path)
    assert not report.converted_types
    assert (tmp_path / ".fux" / "formats.toml").read_text(encoding="utf-8") == 'include = ["*.md"]\n'


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
    # ⚠ **This used to pin the sentence "min(this, what your fetcher declares)".**
    # That prose left with W-122 (2026-09-12): a comment explaining a key can
    # drift from SR-CONFIG while both look correct, which SR-LAW-0 decision 4
    # forbids. What the template owes a consumer now is the POINTER — a repo
    # whose `fux.toml` says nothing and links nowhere is the worse outcome, so
    # this asserts the link rather than dropping the check.
    assert "records/0113_config.md" in written, "the template must name SR-CONFIG"
    assert "may not be commented out" in written


def test_the_configs_stated_default_is_the_one_the_engine_applies(tmp_path):
    """The gate, not the trust. A number typed into the template drifts from the
    constant beside it — which is the defect W-83 fixed one file over.
    `config_text()` substitutes `DEFAULT_MAX_PARALLEL` into
    `templates/fux.toml.txt`; this fails if anyone flattens it."""
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
    # `node/` and `fux` are engine-owned and vendored here on purpose
    # (SR-NODE-SEARCH R2); a fetcher or a source list would still be `setup`'s
    # alone, which is the invariant this test exists for.
    assert sorted(p.name for p in (tmp_path / ".fux").iterdir()) == [
        ".gitignore", "README.md", "fux", "node",
    ]


def test_a_plain_ingest_puts_no_code_in_the_repo(tmp_path):
    from fux.ingest.run import run as ingest

    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")

    ingest(tmp_path)
    assert not (tmp_path / ".fux" / "fetchers").exists()


def test_setup_writes_the_pii_starter_and_never_rewrites_it(tmp_path):
    """SR-PII decision 17: the starter's header said setup wrote it; now it does."""
    from fux.ingest import pii

    setup_mod.run(tmp_path, agents=False)
    path = pii.rules_path(tmp_path)
    assert path.read_bytes() == setup_mod.template_bytes(setup_mod.PII_TEMPLATE)
    assert pii.load(tmp_path), "the starter ships its safe rules enabled"

    path.write_text("# redact nothing, on purpose\n", encoding="utf-8")
    setup_mod.run(tmp_path, agents=False)
    assert path.read_text(encoding="utf-8") == "# redact nothing, on purpose\n"


# -- W-140 row 18: three statements fux shipped that were not true -----------


def test_a_re_run_of_setup_does_not_re_print_the_agents_snippet(tmp_path, capsys):
    """It printed the whole template on EVERY run after the first.

    The note is for a repo whose `AGENTS.md` fux did not write — *nothing here
    tells them the index exists*. After one `fux setup`, the file that gets
    kept is fux's own, which says exactly that, and the announcement fired on
    it anyway.
    """
    from fux import setup as setup_mod

    setup_mod.run(tmp_path)
    capsys.readouterr()

    report = setup_mod.run(tmp_path)
    assert (tmp_path / "AGENTS.md").is_file()
    assert not report.skipped_agents_md, "fux's own AGENTS.md is not a hand-written one"


def test_a_hand_written_agents_md_still_gets_the_snippet(tmp_path):
    """The case the announcement exists for, unchanged."""
    from fux import setup as setup_mod

    (tmp_path / "AGENTS.md").write_text("# our own house rules\n", encoding="utf-8")
    report = setup_mod.run(tmp_path)
    assert report.skipped_agents_md


def test_the_urls_header_is_derived_from_the_spec(tmp_path):
    """It said *"Two attributes, and the set is closed"* while there were seven.

    `keep`, `ttl`, `enrich`, `archived` and `update` all landed after the header
    was written, and every repo set up in between committed the sentence.
    """
    from fux.ingest.sourcelist import URLS
    from fux.setup import _urls_header

    header = _urls_header()
    assert f"# {len(URLS.attributes)} attributes" in header
    for attr in URLS.attributes:
        assert f"{attr.name}=" in header, f"{attr.name} is in the spec and not in the header"


def test_the_urls_header_does_not_promise_a_full_sweep(tmp_path):
    """`fux update` stopped re-fetching every line when narrow-by-default landed."""
    from fux.setup import _urls_header

    assert "re-fetches every line" not in _urls_header()


def test_the_starter_pii_file_points_at_a_probe_the_consumer_has(tmp_path):
    """`tools/pii-probe/` is in the fux repository, not in the wheel.

    Pointing a consumer at a path they do not have is worse than pointing at
    nothing: they conclude their install is broken.
    """
    from fux.setup import template_bytes

    starter = template_bytes("pii.toml.txt").decode("utf-8")
    assert "python3 tools/pii-probe/probe.py" not in starter
    assert "fux-pii" in starter, "name the skill that actually carries the script"


def test_the_scaffolded_config_is_a_template_file_not_a_string(tmp_path):
    """Arpit, 2026-09-14: *"create a template for fux.toml file like others."*

    The starter lives at `templates/fux.toml.txt` and is READ, like
    `pii.toml.txt` and the two fetchers. This fails if anyone inlines it back
    into `setup.py` — where a stray quote in a config comment becomes a syntax
    error in the engine.
    """
    from importlib import resources

    shipped = (resources.files("fux") / "templates" / "fux.toml.txt").read_text(encoding="utf-8")
    assert "[sources.url]" in shipped
    assert "{default}" in shipped, "the template holds the placeholder; setup substitutes it"
    assert "{url_config}" in shipped, "the fetcher tables are DERIVED, never typed here"
    expected = shipped.replace("{default}", str(DEFAULT_MAX_PARALLEL))
    expected = expected.replace("{url_config}", setup_mod.url_config_tables())
    assert setup_mod.config_text() == expected


def test_a_brace_in_the_template_cannot_break_setup(tmp_path, monkeypatch):
    """Why `str.replace` and not `str.format`.

    The template is an editable file now, so a `{` added to a comment must be
    written through verbatim rather than raising `KeyError` out of `fux setup`.
    """
    doctored = '# see {docs} for detail\n[sources]\n[sources.url]\nmax_parallel = {default}\n'
    monkeypatch.setattr(setup_mod, "template_bytes", lambda name: doctored.encode("utf-8"))
    out = setup_mod.config_text()
    assert "{docs}" in out
    assert f"max_parallel = {DEFAULT_MAX_PARALLEL}" in out


def test_the_two_valued_url_keys_are_written_live_with_their_defaults(tmp_path):
    """Arpit's ruling, 2026-09-14. A closed, small value domain is written out;
    a tuning number defers to the engine (SR-DOTFUX).

    The written line is the complete menu — a reader learns the key *and* its
    alternatives without leaving the file.
    """
    from fux.config import load

    setup_mod.run(tmp_path)
    written = (tmp_path / "fux.toml").read_text(encoding="utf-8")
    assert 'update          = "auto"' in written
    assert "fetch_at_answer = true" in written
    assert "keep            = true" in written
    assert "enrich          = false" in written
    # Written live and still the engine's own defaults — not a second opinion.
    config = load(tmp_path)
    assert config.url.update == "auto"
    assert config.url.fetch_at_answer is True
    # The deferring keys stay OUT: their defaults are numbers that may move.
    # Assigned lines only — the header names them in prose, saying why.
    assigned = {
        line.split("=")[0].strip()
        for line in written.splitlines()
        if "=" in line and not line.lstrip().startswith(("#", "["))
    }
    assert "acquired_max_bytes" not in assigned
    assert "sweep_minutes" not in assigned
    assert "ttl" not in assigned


def test_the_fetcher_config_tables_are_derived_from_the_fetchers(tmp_path):
    """Derived, never transcribed — the `_urls_header()` lesson (W-140 row 18).

    The values in `[sources.url.config.<stem>]` must be the fetcher's own
    defaults, read out of the shipped file, so editing a fetcher's default
    cannot leave the scaffolded config saying something else.
    """
    tables = setup_mod.url_config_tables()
    assert "[sources.url.config.http]" in tables
    assert "[sources.url.config.cdp]" in tables
    for template, key, needle in (
        ("cdp.py.txt", "cdp_port", "CDP_PORT"),
        ("http.py.txt", "timeout_s", "TIMEOUT_S"),
    ):
        derived = setup_mod.fetcher_defaults(template)
        source = setup_mod.template_bytes(template).decode("utf-8")
        assert f"{needle} = {derived[key]!r}" in source or f"{needle} = {derived[key]}" in source


def test_the_fetchers_are_parsed_not_executed(tmp_path, monkeypatch):
    """`cdp.py` carries network code and must never run inside the package
    (SR-CDP-FETCHER decision 8) — least of all from `fux setup`."""
    import subprocess

    def explode(*a, **k):  # pragma: no cover - the point is that it is not called
        raise AssertionError("fux setup executed a fetcher")

    monkeypatch.setattr(subprocess, "Popen", explode)
    monkeypatch.setattr(subprocess, "run", explode)
    assert setup_mod.fetcher_defaults("cdp.py.txt")["cdp_port"] == 9222


def test_no_fetcher_receives_another_fetchers_keys(tmp_path):
    """End to end: the scaffolded file must LOAD and hand http.py only keys
    http.py knows. Writing `cdp_port` flat is what made this impossible, and is
    why the block shipped commented out."""
    from fux.config import load

    setup_mod.run(tmp_path)
    url = load(tmp_path).url
    http_keys = set(url.config_for(".fux/fetchers/http.py"))
    cdp_keys = set(url.config_for(".fux/fetchers/cdp.py"))
    assert "cdp_port" not in http_keys
    assert "timeout_s" not in cdp_keys
    assert "cdp_port" in cdp_keys
