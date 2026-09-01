"""`.fux/sources/types` binds an extension to the decoder that reads it, and
fux checks the binding instead of trusting it — ADR-TYPES decision 11 and
ADR-DECODE decision 13, ruled by Arpit 2026-09-01.

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
from fux.ingest import sourcelist


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    return tmp_path


def _types(root: Path, *lines: str) -> None:
    (root / ".fux" / "sources" / "types").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _decoder(root: Path, name: str, extensions: str, marker: str = "x") -> None:
    """A consumer decoder claiming `extensions`, returning a recognisable body."""
    (root / ".fux" / "decoders").mkdir(parents=True, exist_ok=True)
    (root / ".fux" / "decoders" / f"{name}.py").write_text(
        f"EXTENSIONS = ({extensions})\n"
        f"def decode(raw, rel_path):\n"
        f"    return '# {marker}'\n",
        encoding="utf-8",
    )


# -- the grammar -------------------------------------------------------------


def _parse(text: str):
    return sourcelist.parse(text, sourcelist.TYPES, origin="types")


def test_a_binding_parses_and_resolves_onto_the_entry():
    (entry,) = _parse("*.csv decoder=csvdoc")
    assert entry.value == "*.csv"
    assert entry.attrs["decoder"] == "csvdoc"
    assert entry.declared == {"decoder"}


def test_a_line_with_no_binding_resolves_to_the_empty_default():
    """Which means *derive it from the module's own EXTENSIONS* — the behaviour
    every types line had before this attribute existed."""
    (entry,) = _parse("*.md")
    assert entry.attrs["decoder"] == ""
    assert entry.declared == frozenset()


@pytest.mark.parametrize(
    "name",
    ["csvdoc.py", ".fux/decoders/csvdoc.py", "_helper", "CsvDoc", "csv-doc", "csv doc"],
)
def test_a_name_that_is_not_a_module_stem_is_refused(name: str):
    """A path, a suffix, a leading underscore or a capital cannot name a module
    the registry would load — `_`-prefixed files are skipped as shared helpers,
    and the loader keys on the file stem exactly."""
    with pytest.raises(FuxError) as caught:
        _parse(f"*.csv decoder={name}")
    assert "decoder" in str(caught.value)


def test_an_empty_binding_is_legal_so_a_generated_line_round_trips():
    """`render_line` states every attribute; an empty default is omitted, and
    the omitted form has to parse back to the same entry."""
    rendered = sourcelist.render_line("*.md", {}, sourcelist.TYPES)
    assert rendered == "*.md"
    (entry,) = _parse("*.md decoder=")
    assert entry.attrs["decoder"] == ""


def test_a_rendered_binding_states_the_module():
    assert sourcelist.render_line("*.csv", {"decoder": "csvdoc"}, sourcelist.TYPES) == (
        "*.csv decoder=csvdoc"
    )


def test_an_exclusion_may_not_carry_a_binding():
    """`!*.min.csv` removes a pattern; there is nothing left to bind."""
    with pytest.raises(FuxError, match="exclusion carries no attributes"):
        _parse("!*.min.csv decoder=csvdoc")


# -- resolution --------------------------------------------------------------


def test_a_binding_on_a_path_pattern_is_refused(repo: Path):
    """`docs/api/*.json decoder=jsondoc` cannot mean what it looks like.

    Dispatch sees a suffix and nothing about which glob admitted the file, so
    the binding would silently apply to every `.json` in the corpus rather than
    the ones under `docs/api`.
    """
    _types(repo, "docs/api/*.json decoder=jsondoc")
    with pytest.raises(FuxError, match="per extension"):
        registry(repo)


def test_a_binding_to_a_module_that_does_not_exist_is_a_hard_error(repo: Path):
    _types(repo, "*.csv decoder=nosuchdoc")
    with pytest.raises(FuxError, match="no decoder module named"):
        registry(repo)


def test_redirecting_a_claimed_extension_to_a_non_claimer_is_a_hard_error(repo: Path):
    """**The verify half of "the file binds, the module verifies".**

    `jsondoc` is real and `.csv` is real; the pairing is not, and `csvdoc`
    already claims `.csv`. Falling back to `csvdoc` here would be the dangerous
    outcome — the repo would index happily while its committed config described
    something that never ran.
    """
    _types(repo, "*.csv decoder=jsondoc")
    with pytest.raises(FuxError) as caught:
        registry(repo)
    message = str(caught.value)
    assert "does not claim .csv" in message
    assert "while csvdoc" in message, "the error names the decoder that DOES claim it"
    assert "EXTENSIONS" in message


def test_a_new_extension_may_be_bound_to_an_existing_decoder(repo: Path):
    """**Extending is not redirecting**, and only the second is refused.

    Nothing claims `.geojson`, so there is no competing answer for the line to
    be stale against — without it the extension has no decoder at all. A
    `.geojson` is JSON; making a consumer copy `jsondoc.py` and edit one tuple
    to say so would make the map a worse answer than the code it replaced.
    """
    _types(repo, "*.md", "*.geojson decoder=jsondoc")
    assert registry(repo)[".geojson"].name == "jsondoc"


def test_an_extended_extension_actually_decodes(repo: Path):
    """The binding reaches dispatch, not just the registry."""
    _types(repo, "*.geojson decoder=jsondoc")
    out = decode(b'{"label": "north depot"}', "sites.geojson", repo)
    assert out is not None and "north depot" in out


def test_extending_survives_the_decoder_that_would_otherwise_be_asked(repo: Path):
    """An extension nothing claims decodes to `None` without a binding — that is
    the queue entry the binding removes."""
    _types(repo, "*.geojson")
    assert decode(b'{"label": "north depot"}', "sites.geojson", repo) is None
    assert "no decoder for .geojson" in reason("sites.geojson", repo)


def test_a_consumer_decoder_may_be_extended_too(repo: Path):
    """The rule is about who claims the extension, never about where the module
    came from."""
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, "*.tab decoder=mycsv")
    assert registry(repo)[".tab"].name == "mycsv"


def test_a_binding_beats_load_order_when_two_decoders_claim_one_extension(repo: Path):
    """The failure the binding exists to remove.

    With a consumer `mycsv.py` and the built-in `csvdoc` both claiming `.csv`,
    dispatch resolves by precedence — and *nothing in the repo says which won*.
    Naming one in the types file makes the winner a committed fact.
    """
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, "*.csv")
    assert registry(repo)[".csv"].name == "mycsv"  # consumer wins by precedence

    _types(repo, "*.csv decoder=csvdoc")
    assert registry(repo)[".csv"].name == "csvdoc"  # …until the file says otherwise


def test_a_binding_may_name_a_consumer_module(repo: Path):
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, "*.csv decoder=mycsv")
    assert registry(repo)[".csv"].origin.endswith("mycsv.py")


def test_no_types_file_leaves_dispatch_exactly_as_it_was(repo: Path):
    """The built-in default declares nothing, so every extension still resolves
    through the module tuples. An absent file is not an empty map."""
    assert registry(repo)[".csv"].name == "csvdoc"
    assert registry(repo)[".pdf"].name == "pdfdoc"


def test_an_edit_is_picked_up_within_one_process(repo: Path):
    """The bindings read is cached — `registry()` runs once per document — and
    the cache is keyed on the file's stat so an edit is never served stale."""
    _decoder(repo, "mycsv", '".csv",', marker="consumer")
    _types(repo, "*.csv decoder=csvdoc")
    assert registry(repo)[".csv"].name == "csvdoc"
    _types(repo, "*.csv decoder=mycsv")
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
    _types(repo, *(f"*{ext} decoder={name}" for ext, name in builtin_bindings().items()))
    resolved = registry(repo)
    for ext, name in builtin_bindings().items():
        assert resolved[ext].name == name
