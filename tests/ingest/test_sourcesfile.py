"""`.fux/sources.yaml`, the schema (W-294) — what each position may hold.

`yamlsubset.py` reads text; `sourcesfile.py` decides what the text means. This
file pins the schema half of W-294 §Format: the two sections, the flag lists,
per-section attribute legality, the typing that is the schema's and never
YAML's, duplicates as errors, and the `!` refusal that names `.fux/.fuxignore`.
"""

from __future__ import annotations

import pytest

from fux.acquire import sourcesfile
from fux.errors import FuxError

ORIGIN = ".fux/sources.yaml"
URL = "urls:\n  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n"


def _parse(text):
    return sourcesfile.parse(text, origin=ORIGIN)


def _refused(text, line, says):
    with pytest.raises(FuxError) as exc:
        _parse(text)
    message = str(exc.value)
    assert message.startswith(f"{ORIGIN}:{line}: "), message
    assert says in message, message
    return message


# -- the shape ---------------------------------------------------------------


def test_an_empty_file_lists_nothing():
    assert _parse("") == sourcesfile.Sources()


def test_a_path_in_any_list_is_indexed_and_each_list_sets_its_flag():
    found = _parse(
        "paths:\n  include:\n    - docs\n  archived:\n    - archive\n    - docs\n  enrich:\n    - handbook\n"
    )
    assert {e.value: (e.attrs["archived"], e.attrs["enrich"]) for e in found.paths} == {
        "archive": ("true", "false"),
        "docs": ("true", "false"),
        "handbook": ("false", "true"),
    }


def test_the_loader_sorts_so_file_order_cannot_reach_a_byte():
    """L4 applied to config: the same set in two orders parses identically."""
    a = _parse("paths:\n  include:\n    - work\n    - docs\n")
    b = _parse("paths:\n  include:\n    - docs\n    - work\n")
    assert [e.value for e in a.paths] == [e.value for e in b.paths] == ["docs", "work"]


def test_a_url_entry_keeps_what_it_declared():
    (entry,) = _parse(URL + "    ttl: 7d\n").urls
    assert entry.value == "https://x.test/a"
    assert entry.declared == {"fetch", "decoder", "ttl"}
    assert entry.attrs["ttl"] == "7d"


@pytest.mark.parametrize(
    ("text", "line", "says"),
    [
        ("- docs\n", 1, "must be a map whose keys are `paths` and/or `urls`"),
        ("files:\n  - x\n", 1, "unknown key `files`"),
        ("paths:\n  ignored:\n    - x\n", 2, "unknown key `ignored` under `paths`"),
        ("paths:\n", 1, "`paths` is empty"),
        ("paths:\n  include:\n", 2, "`include` is empty"),
        ("urls:\n", 1, "`urls` is empty"),
        ("paths:\n  - docs\n", 1, "`paths` must be a block map"),
        ("urls:\n  - fetch: http\n    decoder: prose\n", 2, "a `urls` entry with no `url:` key"),
    ],
    ids=["top-list", "unknown-top", "unknown-list", "empty-paths", "empty-list", "empty-urls",
         "paths-not-map", "no-url-key"],
)
def test_the_shape_is_closed(text, line, says):
    _refused(text, line, says)


# -- `!` has one meaning in .fux/, and it is not here --------------------------


def test_a_bang_path_is_refused_and_names_fuxignore_with_the_anchored_pattern():
    message = _refused("paths:\n  include:\n    - docs\n    - '!work/golden'\n", 4, "starts with `!`")
    assert ".fux/.fuxignore" in message
    assert "`/work/golden`" in message, "the refusal spells the pattern to write, anchored"


# -- per-section attribute legality --------------------------------------------


def test_a_url_attribute_is_not_a_path_list():
    _refused("paths:\n  fetch:\n    - docs\n", 2, "unknown key `fetch` under `paths`")


def test_an_unknown_url_key_is_refused():
    _refused(URL + "    colour: red\n", 5, "unknown key `colour` in a `urls` entry")


def test_a_url_under_paths_is_sent_to_urls():
    _refused("paths:\n  include:\n    - https://x.test/a\n", 3, "belongs under `urls:`")


@pytest.mark.parametrize("missing", ["fetch", "decoder"])
def test_fetch_and_decoder_are_required_on_every_url(missing):
    lines = [l for l in URL.splitlines() if not l.strip().startswith(f"{missing}:")]
    _refused("\n".join(lines) + "\n", 2, f"does not state `{missing}:`")


def test_a_non_http_url_is_refused():
    _refused("urls:\n  - url: ftp://x.test/a\n    fetch: http\n    decoder: prose\n", 2, "not an http(s) URL")


@pytest.mark.parametrize("path", ["/etc", "../outside"])
def test_a_path_must_stay_inside_the_repo(path):
    _refused(f"paths:\n  include:\n    - {path}\n", 3, path)


# -- typing is the schema's, never YAML's guess --------------------------------


@pytest.mark.parametrize("trap", ["no", "on", "null", "~", "1.10", "010"])
def test_a_typing_trap_is_a_path_where_a_path_is_expected(trap):
    (entry,) = _parse(f"paths:\n  include:\n    - {trap}\n").paths
    assert entry.value == trap


@pytest.mark.parametrize(
    ("key", "value"),
    [("keep", "no"), ("keep", "yes"), ("enrich", "on"), ("archived", "1"),
     ("update", "sometimes"), ("ttl", "1.10"), ("ttl", "~")],
)
def test_a_typed_attribute_accepts_only_its_own_spellings(key, value):
    _refused(URL + f"    {key}: {value}\n", 5, f"{key}: `{value}`")


@pytest.mark.parametrize(
    ("key", "value"),
    [("keep", "true"), ("keep", "false"), ("enrich", "true"), ("archived", "false"),
     ("update", "auto"), ("update", "never"), ("ttl", "0"), ("ttl", "15m")],
)
def test_a_typed_attribute_reads_its_legal_values(key, value):
    (entry,) = _parse(URL + f"    {key}: {value}\n").urls
    assert entry.attrs[key] == value


# -- duplicates are errors, not silent dedupes ---------------------------------


def test_a_path_twice_in_one_list_names_its_first_line():
    _refused("paths:\n  include:\n    - docs\n    - docs\n", 4, "listed twice in `include` (first on line 3)")


def test_a_url_twice_names_its_first_line():
    _refused(URL + URL.removeprefix("urls:\n"), 5, "listed twice (first on line 2)")


def test_a_path_in_two_flag_lists_is_not_a_duplicate():
    """Two lists, two flags — the spec's way to say both."""
    (entry,) = _parse("paths:\n  archived:\n    - old\n  enrich:\n    - old\n").paths
    assert entry.attrs == {"archived": "true", "enrich": "true"}


# -- the old lists are refused while they exist --------------------------------


@pytest.mark.parametrize("legacy", [sourcesfile.LEGACY_DIRS, sourcesfile.LEGACY_URLS])
def test_a_leftover_pre_w294_list_stops_the_read(tmp_path, legacy):
    (tmp_path / sourcesfile.FILE).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / sourcesfile.FILE).write_text("paths:\n  include:\n    - docs\n", encoding="utf-8")
    (tmp_path / legacy).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / legacy).write_text("docs\n", encoding="utf-8")
    with pytest.raises(FuxError, match="fux setup"):
        sourcesfile.read(tmp_path, sourcesfile.FILE)
