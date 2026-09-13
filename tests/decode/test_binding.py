"""`.fux/formats.toml` binds an extension to the decoder that reads it, and fux
checks the binding instead of trusting it — SR-TYPES decisions 11 and 12 and
SR-DECODE decision 13, ruled by Arpit 2026-09-01 and 2026-09-11.

**What the binding is for.** Before it, "which decoder reads `.csv`" was a
property of the code installed on a machine: a built-in's `EXTENSIONS` tuple,
possibly replaced by a consumer module of the same name. Two people with
different `.fux/decoders/` contents could commit different indexes from the
same sources and nothing in the repo said so. The binding makes the answer a
committed line, and `_bind` makes a disagreement between the line and the
module a **hard error** rather than a silent fallback — because the wrong
answer does not fail visibly, it produces a plausible index with different
postings.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux.decode import builtin_bindings, decode, reason, registry
from fux.errors import FuxError
from fux.ingest import typesfile


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir(parents=True)
    return tmp_path


def _types(root: Path, include=(), **decoders: str) -> None:
    """Write `.fux/formats.toml` in the canonical layout fux itself writes."""
    (root / ".fux" / "formats.toml").write_text(
        typesfile.render(list(include), decoders), encoding="utf-8"
    )


def _decoder(root: Path, name: str, extensions: str, marker: str = "x") -> None:
    """A consumer decoder claiming `extensions`, returning a recognisable body."""
    (root / ".fux" / "decoders").mkdir(parents=True, exist_ok=True)
    (root / ".fux" / "decoders" / f"{name}.py").write_text(
        f"EXTENSIONS = ({extensions})\n"
        f"def decode(raw, rel_path):\n"
        f"    return '# {marker}'\n",
        encoding="utf-8",
    )


# -- the file ----------------------------------------------------------------


def _parse(text: str) -> typesfile.TypesList:
    return typesfile.parse(text, origin=".fux/formats.toml")


def test_a_binding_parses_onto_its_extension():
    listed = _parse('[decoders]\ncsv = "csv"\n')
    assert listed.decoders == {"csv": "csv"}
    assert listed.allow == ("*.csv",), "a bound extension IS a document"


def test_an_include_glob_carries_no_binding():
    """Which means *derive the decoder from the module's own EXTENSIONS* — the
    behaviour every types entry had before bindings existed."""
    listed = _parse('include = ["*.md"]\n')
    assert listed.include == ("*.md",) and listed.decoders == {}


@pytest.mark.parametrize(
    "name",
    ["csv.py", ".fux/decoders/csv.py", "_helper", "CsvDoc", "csv-doc", "csv doc"],
)
def test_a_name_that_is_not_a_module_stem_is_refused(name: str):
    """A path, a suffix, a leading underscore or a capital cannot name a module
    the registry would load — `_`-prefixed files are skipped as shared helpers,
    and the loader keys on the file stem exactly."""
    with pytest.raises(FuxError) as caught:
        _parse(f'[decoders]\ncsv = "{name}"\n')
    assert "decoder" in str(caught.value)


def test_an_empty_binding_is_refused_because_it_binds_nothing():
    """The line grammar had to accept `decoder=` so a generated line could round
    trip. TOML has no such line: a format no decoder reads is an `include` glob."""
    with pytest.raises(FuxError, match="binds nothing"):
        _parse('[decoders]\nmd = ""\n')


def test_a_path_scoped_binding_cannot_be_written():
    """**SR-TYPES decision 12: the shape is the rule.** The line grammar had to
    refuse `docs/api/*.json decoder=json` at resolution, because dispatch sees a
    suffix and nothing about the glob. A `[decoders]` key is an extension, so the
    nearest thing anybody can write is an extension that is not one."""
    with pytest.raises(FuxError, match="not an extension"):
        _parse('[decoders]\n"docs/api/*.json" = "json"\n')


def test_two_bindings_for_one_extension_are_refused_by_toml_itself():
    with pytest.raises(FuxError, match="not valid TOML"):
        _parse('[decoders]\ncsv = "csv"\ncsv = "json"\n')


def test_an_extension_stated_in_both_keys_is_refused():
    """A bound extension is already a document; `*.csv` in `include` as well is
    two lines that must agree and are one edit away from disagreeing."""
    with pytest.raises(FuxError, match="already a document"):
        _parse('include = ["*.csv"]\n[decoders]\ncsv = "csv"\n')


@pytest.mark.parametrize(
    "text, match",
    [
        ('exclude = ["*.min.md"]\n', "fuxignore"),
        ('include = ["!*.min.md"]\n', "does not subtract"),
        ('[decoders]\n".csv" = "csv"\n', "without its dot"),
        ('[decoders]\nCSV = "csv"\n', "lowercase"),
        ('[decoders]\ntar.gz = "zip"\n', "must be quoted"),
        ('include = ["docs/"]\n', "trailing slash"),
        ('include = "*.md"\n', "array"),
    ],
)
def test_every_shape_the_file_cannot_mean_is_a_loud_error(text: str, match: str):
    with pytest.raises(FuxError, match=match):
        _parse(text)


def test_an_upper_case_glob_beside_its_binding_is_not_a_repeat():
    """`glob_match` is case-sensitive: `*.CSV` admits files the `csv` binding does not."""
    assert _parse('include = ["*.CSV"]\n[decoders]\ncsv = "csv"\n').allow == ("*.CSV", "*.csv")


def test_a_quoted_compound_extension_is_legal():
    assert _parse('[decoders]\n"tar.gz" = "zip"\n').decoders == {"tar.gz": "zip"}


def test_an_error_names_the_key_and_the_line_when_it_can():
    """SR-TYPES decision 12's stated cost: a parsed TOML value has no position,
    so the key is always named and the line only when a scan finds exactly one."""
    with pytest.raises(FuxError) as caught:
        _parse('include = [\n  "*.md",\n]\n\n[decoders]\ngeojson = "Json"\n')
    assert ".fux/formats.toml:6 (decoders.geojson)" in str(caught.value)


# -- resolution --------------------------------------------------------------


def test_a_binding_to_a_module_that_does_not_exist_is_a_hard_error(repo: Path):
    _types(repo, csv="nosuchdoc")
    with pytest.raises(FuxError, match="no decoder module named"):
        registry(repo)


def test_redirecting_a_claimed_extension_to_a_non_claimer_is_a_hard_error(repo: Path):
    """**The verify half of "the file binds, the module verifies".**

    `json` is real and `.csv` is real; the pairing is not, and `csv`
    already claims `.csv`. Falling back to `csv` here would be the dangerous
    outcome — the repo would index happily while its committed config described
    something that never ran.
    """
    _types(repo, csv="json")
    with pytest.raises(FuxError) as caught:
        registry(repo)
    message = str(caught.value)
    assert "does not claim .csv" in message
    assert "while csv" in message, "the error names the decoder that DOES claim it"
    assert "EXTENSIONS" in message


def test_a_new_extension_may_be_bound_to_an_existing_decoder(repo: Path):
    """**Extending is not redirecting**, and only the second is refused.

    Nothing claims `.geojson`, so there is no competing answer for the line to
    be stale against — without it the extension has no decoder at all. A
    `.geojson` is JSON; making a consumer copy `json.py` and edit one tuple
    to say so would make the map a worse answer than the code it replaced.
    """
    _types(repo, ["*.md"], geojson="json")
    assert registry(repo)[".geojson"].name == "json"


def test_an_extended_extension_actually_decodes(repo: Path):
    """The binding reaches dispatch, not just the registry."""
    _types(repo, geojson="json")
    out = decode(b'{"label": "north depot"}', "sites.geojson", repo)
    assert out is not None and "north depot" in out


def test_extending_survives_the_decoder_that_would_otherwise_be_asked(repo: Path):
    """An extension nothing claims decodes to `None` without a binding — that is
    the queue entry the binding removes."""
    _types(repo, ["*.geojson"])
    assert decode(b'{"label": "north depot"}', "sites.geojson", repo) is None
    assert "no decoder for .geojson" in reason("sites.geojson", repo)


def test_a_consumer_decoder_may_be_extended_too(repo: Path):
    """The rule is about who claims the extension, never about where the module
    came from."""
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, tab="mycsv")
    assert registry(repo)[".tab"].name == "mycsv"


def test_a_binding_beats_load_order_when_two_decoders_claim_one_extension(repo: Path):
    """The failure the binding exists to remove.

    With a consumer `mycsv.py` and the built-in `csv` both claiming `.csv`,
    dispatch resolves by precedence — and *nothing in the repo says which won*.
    Naming one in the types file makes the winner a committed fact.
    """
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, ["*.csv"])
    assert registry(repo)[".csv"].name == "mycsv"  # consumer wins by precedence

    _types(repo, csv="csv")
    assert registry(repo)[".csv"].name == "csv"  # …until the file says otherwise


def test_a_binding_may_name_a_consumer_module(repo: Path):
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, csv="mycsv")
    assert registry(repo)[".csv"].origin.endswith("mycsv.py")


def test_no_types_file_leaves_dispatch_exactly_as_it_was(repo: Path):
    """The built-in default declares nothing, so every extension still resolves
    through the module tuples. An absent file is not an empty map."""
    assert registry(repo)[".csv"].name == "csv"
    assert registry(repo)[".pdf"].name == "pdf"


def test_an_edit_is_picked_up_within_one_process(repo: Path):
    """The bindings read is cached — `registry()` runs once per document — and
    the cache is keyed on the file's stat so an edit is never served stale."""
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, csv="csv")
    assert registry(repo)[".csv"].name == "csv"
    _types(repo, csv="mycsv")
    assert registry(repo)[".csv"].name == "mycsv"


# -- the map fux writes ------------------------------------------------------


def test_every_builtin_extension_has_exactly_one_builtin_binding():
    """`builtin_bindings()` is what a generated types file states, so a shared
    extension between two built-ins would make that file's map ambiguous."""
    from fux.decode import BUILTIN_MODULES, builtin_extensions

    bindings = builtin_bindings()
    assert set(bindings) == set(builtin_extensions())
    assert set(bindings.values()) <= set(BUILTIN_MODULES)


def test_the_written_map_verifies_against_the_modules_it_names(repo: Path):
    """Every binding fux writes must survive the check fux applies. If these two
    ever disagree, `fux setup` produces a repo that cannot ingest."""
    _types(repo, **{ext.lstrip("."): name for ext, name in builtin_bindings().items()})
    resolved = registry(repo)
    for ext, name in builtin_bindings().items():
        assert resolved[ext].name == name


# -- the old file -------------------------------------------------------------


def test_a_leftover_line_grammar_file_stops_dispatch_loudly(repo: Path):
    """SR-TYPES decision 12. `fux ask` decodes fetched documents without walking,
    so a binding it silently stopped seeing would re-read them with a different
    decoder than the index was built with."""
    (repo / ".fux" / "sources").mkdir()
    (repo / ".fux" / "sources" / "types").write_text("*.geojson decoder=json\n", encoding="utf-8")
    with pytest.raises(FuxError, match="moved to .fux/formats.toml"):
        registry(repo)


def test_the_old_file_beside_the_new_one_is_refused_too(repo: Path):
    _types(repo, geojson="json")
    (repo / ".fux" / "sources").mkdir()
    (repo / ".fux" / "sources" / "types").write_text("*.md\n", encoding="utf-8")
    with pytest.raises(FuxError, match="still exists beside"):
        registry(repo)
