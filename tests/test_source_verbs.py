"""`fux add` / `fux remove` / `fux update` — the managing commands (W-63).

Successor to `test_url_command.py`, which tested `fux url` before that verb
was retired. **Every property that file pinned is still pinned here** — a
written line states every attribute (ADR-URL-LIST decision 12), the command
opens no socket of its own, it edits one line rather than regenerating the
file, and the file is LF-only with exactly one trailing newline. What is new
is that all of it now holds for three lists instead of one, plus the two
decisions the verbs added: dispatch-on-entry, and remove-by-coverage.

Nothing here runs a full ingest unless the test is about ingest: `--no-ingest`
keeps these unit tests about the *list*, which is what they are for.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fux import sources
from fux.errors import FuxError
from fux.ingest import sourcelist


def _args(entry=None, **flags):
    base = {
        "cdp": False, "http": False, "plain": False, "hashed": False,
        "archived": False, "types": False, "dry_run": False,
        "no_ingest": True, "no_fetch": True, "no_accelerator": True,
    }
    return SimpleNamespace(entry=entry, **(base | flags))


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "urls").write_text("# my list\n", encoding="utf-8")
    (tmp_path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("# B\n\nbody\n", encoding="utf-8")
    return tmp_path


def _urls(repo):
    return (repo / ".fux" / "sources" / "urls").read_text(encoding="utf-8")


def _dirs(repo):
    return (repo / ".fux" / "sources" / "dirs").read_text(encoding="utf-8")


def _add(repo, monkeypatch, args):
    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    return sources.cmd_add(args)


def _remove(repo, monkeypatch, args):
    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    return sources.cmd_remove(args)


def _update(repo, monkeypatch, args):
    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    return sources.cmd_update(args)


# -- dispatch: the entry decides which list ---------------------------------


@pytest.mark.parametrize(
    "entry, flags, expected",
    [
        ("https://x.test/a", {}, sourcelist.URLS),
        ("http://x.test/a", {}, sourcelist.URLS),
        ("docs", {}, sourcelist.DIRS),
        ("docs/one.md", {}, sourcelist.DIRS),
        ("*.pdf", {"types": True}, sourcelist.TYPES),
        # `--types` wins over the shape, because it is the explicit statement.
        ("weird", {"types": True}, sourcelist.TYPES),
    ],
)
def test_dispatch_picks_the_list_from_the_entry(entry, flags, expected):
    assert sources.dispatch(entry, SimpleNamespace(**({"types": False} | flags))) is expected


def test_a_glob_is_not_sniffed_into_the_type_list():
    """`docs/*` is a reasonable `dirs` entry, so `*` may not mean `--types`.

    Guessing between the two lists on a glob character would be wrong exactly
    when it mattered, and silently — the entry would land in a file the user
    never looked at.
    """
    assert sources.dispatch("docs/*", SimpleNamespace(types=False)) is sourcelist.DIRS


def test_a_trailing_slash_is_the_same_directory(repo, monkeypatch, capsys):
    """`docs/` and `docs` are one entry, and the list must not hold both.

    The parser dedupes on the exact string, so it cannot see this duplicate.
    Found by running the verb: `fux add docs/` against a list already holding
    `docs` wrote a second line for the same directory.
    """
    _add(repo, monkeypatch, _args("docs/"))
    # A fux-written line states EVERY attribute explicitly (ADR-URL-LIST
    # decision 12), so this grows when the closed attribute set grows.
    # `enrich=false` arrived with W-76 Phase 8.
    assert [line for line in _dirs(repo).splitlines() if line.strip()] == [
        "docs archived=false enrich=false"
    ]
    assert "updated" in capsys.readouterr().out


# -- decision 12: a written line states everything --------------------------


def test_a_written_line_carries_every_attribute_even_at_its_default(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    assert "https://x.test/a fetch=http meta=hashed" in _urls(repo)


def test_a_dirs_line_carries_its_attribute_too(repo, monkeypatch):
    (repo / "handbook").mkdir()
    _add(repo, monkeypatch, _args("handbook"))
    assert "handbook archived=false" in _dirs(repo)


def test_a_types_line_carries_the_decoder_that_reads_it(repo, monkeypatch):
    """⚠ **This test asserted the opposite until 2026-09-01**, when `types`
    gained its first attribute (ADR-TYPES decision 11). It read
    *"carries none because the set is empty"*; the set is no longer empty, and
    a written line now states the binding fux would otherwise have derived.
    """
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    types = (repo / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    assert "\n*.pdf decoder=pdfdoc\n" in types


def test_a_prose_type_carries_no_binding_because_no_decoder_reads_it(repo, monkeypatch):
    """The empty default is written as absence, not as a bare `decoder=`.

    `*.md` reaches the index as text with no decoder in its path, so there is
    nothing to bind and nothing to state — and four dead characters on every
    prose line would be the cost of pretending otherwise.
    """
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    types = (repo / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    assert "\n*.md\n" in types
    assert not [line for line in types.split("\n") if line.rstrip().endswith("decoder=")]


def test_flags_decide_what_is_recorded(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a", cdp=True, plain=True))
    assert "https://x.test/a fetch=cdp meta=plain" in _urls(repo)


def test_an_unflagged_attribute_keeps_what_the_line_already_said(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a", cdp=True, plain=True))
    _add(repo, monkeypatch, _args("https://x.test/a", hashed=True))
    assert "https://x.test/a fetch=cdp meta=hashed" in _urls(repo)


def test_two_flags_for_one_attribute_is_an_error(repo, monkeypatch):
    with pytest.raises(FuxError, match="pick one"):
        _add(repo, monkeypatch, _args("https://x.test/a", cdp=True, http=True))


def test_a_flag_the_list_does_not_have_is_an_error_not_a_no_op(repo, monkeypatch):
    """`fux add docs --cdp` is someone believing something false about the line.

    The closed attribute set (ADR-URL-LIST decision 11) is only worth having
    if it is enforced on the way in as well as on the way out.
    """
    with pytest.raises(FuxError, match="which `dirs` does not have"):
        _add(repo, monkeypatch, _args("docs", cdp=True))
    with pytest.raises(FuxError, match="which `urls` does not have"):
        _add(repo, monkeypatch, _args("https://x.test/a", archived=True))


def test_a_non_http_url_is_refused_before_anything_is_written(repo, monkeypatch):
    before = _urls(repo)
    with pytest.raises(FuxError, match="not an http"):
        # It dispatches to `dirs` by shape, so force the list to prove the
        # validator runs per-list rather than only on things that look like URLs.
        _add(repo, monkeypatch, _args("ftp://x.test/a"))
    assert _urls(repo) == before


def test_adding_a_path_that_is_not_on_disk_writes_nothing(repo, monkeypatch):
    """A line that breaks the next ingest is worse than a refused command."""
    before = _dirs(repo)
    with pytest.raises(FuxError, match="does not exist"):
        _add(repo, monkeypatch, _args("nope"))
    assert _dirs(repo) == before


def test_adding_something_already_excluded_is_an_error(repo, monkeypatch):
    """There is no un-exclude, so `add` may not pretend to be one."""
    _remove(repo, monkeypatch, _args("docs/a.md"))
    with pytest.raises(FuxError, match="no un-exclude"):
        _add(repo, monkeypatch, _args("docs/a.md"))


# -- one line, never the file ----------------------------------------------


def test_a_grouping_comment_survives_an_edit(repo, monkeypatch):
    path = repo / ".fux" / "sources" / "urls"
    path.write_text("# team A\nhttps://x.test/a fetch=http meta=hashed\n\n# team B\n", encoding="utf-8")
    _add(repo, monkeypatch, _args("https://x.test/a", plain=True))
    text = _urls(repo)
    assert "# team A" in text and "# team B" in text


def test_a_trailing_comment_survives_an_edit(repo, monkeypatch):
    path = repo / ".fux" / "sources" / "urls"
    path.write_text("https://x.test/a fetch=http meta=hashed  # the runbook\n", encoding="utf-8")
    _add(repo, monkeypatch, _args("https://x.test/a", cdp=True))
    assert "# the runbook" in _urls(repo)


def test_lines_land_in_sorted_order(repo, monkeypatch):
    for url in ("https://x.test/c", "https://x.test/a", "https://x.test/b"):
        _add(repo, monkeypatch, _args(url))
    entries = [line.split()[0] for line in _urls(repo).splitlines() if line and not line.startswith("#")]
    assert entries == sorted(entries)


def test_the_file_always_ends_in_exactly_one_newline(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    text = _urls(repo)
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_the_file_is_written_lf_only_regardless_of_host_os(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    assert b"\r\n" not in (repo / ".fux" / "sources" / "urls").read_bytes()
    _add(repo, monkeypatch, _args("docs/a.md"))
    assert b"\r\n" not in (repo / ".fux" / "sources" / "dirs").read_bytes()


def test_a_fragment_bearing_url_round_trips_through_the_command(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/page#section"))
    assert "https://x.test/page#section fetch=http meta=hashed" in _urls(repo)


def test_two_urls_differing_only_by_fragment_get_two_lines(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/page#a"))
    _add(repo, monkeypatch, _args("https://x.test/page#b"))
    listed = [line for line in _urls(repo).splitlines() if line.startswith("https://")]
    assert len(listed) == 2


# -- remove-by-coverage (W-63 decision 4) -----------------------------------


def test_an_entry_with_its_own_line_is_removed_by_deleting_it(repo, monkeypatch, capsys):
    (repo / "handbook").mkdir()
    _add(repo, monkeypatch, _args("handbook"))
    _remove(repo, monkeypatch, _args("handbook"))
    assert "handbook" not in _dirs(repo)
    assert "removed" in capsys.readouterr().out


def test_a_covered_entry_is_removed_by_writing_an_exclusion(repo, monkeypatch, capsys):
    _remove(repo, monkeypatch, _args("docs/a.md"))
    assert "!docs/a.md" in _dirs(repo)
    assert "docs" in _dirs(repo)  # the ancestor stays listed
    out = capsys.readouterr().out
    assert "excluded" in out and "still listed" in out


def test_removing_something_neither_listed_nor_covered_names_both_checks(repo, monkeypatch):
    with pytest.raises(FuxError, match="no line of its own, and no listed entry covers it"):
        _remove(repo, monkeypatch, _args("elsewhere/x.md"))


def test_removing_a_url_always_deletes_the_line(repo, monkeypatch, capsys):
    """`urls` has no exclusions, so there is only ever one branch to take."""
    _add(repo, monkeypatch, _args("https://x.test/a"))
    _remove(repo, monkeypatch, _args("https://x.test/a"))
    assert "https://x.test/a" not in _urls(repo)
    assert "removed" in capsys.readouterr().out


def test_removing_a_url_that_is_not_listed_fails_loudly(repo, monkeypatch):
    with pytest.raises(FuxError, match="no exclusions"):
        _remove(repo, monkeypatch, _args("https://x.test/missing"))


def test_removing_a_url_deletes_its_line_and_nothing_else(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    _add(repo, monkeypatch, _args("https://x.test/b"))
    _remove(repo, monkeypatch, _args("https://x.test/a"))
    text = _urls(repo)
    assert "https://x.test/a" not in text
    assert "https://x.test/b fetch=http meta=hashed" in text
    assert "# my list" in text


def test_removing_an_already_excluded_entry_says_so(repo, monkeypatch):
    _remove(repo, monkeypatch, _args("docs/a.md"))
    with pytest.raises(FuxError, match="already excluded"):
        _remove(repo, monkeypatch, _args("docs/a.md"))


# -- --dry-run writes no bytes ----------------------------------------------


def test_dry_run_add_writes_no_bytes(repo, monkeypatch, capsys):
    before = (repo / ".fux" / "sources" / "urls").read_bytes()
    _add(repo, monkeypatch, _args("https://x.test/a", dry_run=True))
    assert (repo / ".fux" / "sources" / "urls").read_bytes() == before
    out = capsys.readouterr().out
    assert "would add" in out and "fetch=http meta=hashed" in out


def test_dry_run_remove_writes_no_bytes_and_names_the_branch(repo, monkeypatch, capsys):
    before = (repo / ".fux" / "sources" / "dirs").read_bytes()
    _remove(repo, monkeypatch, _args("docs/a.md", dry_run=True))
    assert (repo / ".fux" / "sources" / "dirs").read_bytes() == before
    assert "would exclude" in capsys.readouterr().out


# -- update never writes a line ---------------------------------------------


def test_update_refuses_an_entry_nobody_listed(repo, monkeypatch):
    with pytest.raises(FuxError, match="never creates a line"):
        _update(repo, monkeypatch, _args("docs/nothing.md", check=False))
    assert "docs/nothing.md" not in _dirs(repo)


def test_update_with_no_url_source_still_runs_the_dirs_half(repo, monkeypatch, capsys):
    """**Not an error**, unlike the `--refresh-urls` this verb replaces."""
    _update(repo, monkeypatch, _args(None, check=False, no_ingest=False))
    assert "ingested" in capsys.readouterr().out


def test_update_check_is_read_only_and_reports_drift(repo, monkeypatch, capsys):
    _update(repo, monkeypatch, _args(None, check=False, no_ingest=False))
    capsys.readouterr()

    before = {p: p.read_bytes() for p in (repo / ".fux" / "index").glob("*.jsonl")}
    (repo / "docs" / "a.md").write_text("# A\n\nchanged body\n", encoding="utf-8")

    assert _update(repo, monkeypatch, _args(None, check=True)) == 0
    out = capsys.readouterr().out
    assert "stale" in out and "docs/a.md" in out
    assert {p: p.read_bytes() for p in (repo / ".fux" / "index").glob("*.jsonl")} == before


def test_update_check_exits_zero_when_nothing_drifted(repo, monkeypatch, capsys):
    """Drift is a fact, not a failure — a script checking status must not see one."""
    _update(repo, monkeypatch, _args(None, check=False, no_ingest=False))
    capsys.readouterr()
    assert _update(repo, monkeypatch, _args(None, check=True)) == 0
    assert "nothing has drifted" in capsys.readouterr().out


# -- the type allowlist is extended, never replaced --------------------------


def test_adding_the_first_type_seeds_the_built_in_allowlist(repo, monkeypatch):
    """Otherwise `fux add '*.pdf' --types` un-indexes every markdown document.

    The file REPLACES the built-in default rather than extending it
    (ADR-TYPES), so a one-line file is a corpus-wide invisible filter — the
    exact defect W-55 was opened about. Found by running the verb.
    """
    from fux.decode import builtin_bindings
    from fux.ingest.gitdir import DEFAULT_TYPES

    _add(repo, monkeypatch, _args("*.pdf", types=True))
    types = (repo / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    bindings = builtin_bindings()
    for pattern in DEFAULT_TYPES:
        # A seeded line states its binding when a decoder reads the format and
        # nothing when one does not, so the seed IS the map rather than a list
        # the map is derived from somewhere else.
        binding = bindings.get(pattern[1:].lower(), "")
        line = f"{pattern} decoder={binding}" if binding else pattern
        assert f"\n{line}\n" in types or types.endswith(f"\n{line}\n")
    assert "*.pdf" in types


def test_adding_a_second_type_does_not_re_seed(repo, monkeypatch):
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    _add(repo, monkeypatch, _args("*.csv", types=True))
    types = (repo / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    assert types.count("*.md") == 1


# -- L4: these verbs open no socket of their own ----------------------------


def test_the_module_imports_no_network_library():
    """The fetch `add` performs is `ingest.run`'s, behind the consumer-fetcher
    contract. Nothing here reaches the network directly, and the import fence
    is what keeps that true rather than merely intended."""
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(sources.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    assert not (imported & {"socket", "ssl", "http", "urllib", "requests", "httpx"})


def test_add_with_no_fetch_opens_nothing(repo, monkeypatch, capsys):
    _add(repo, monkeypatch, _args("https://x.test/a", no_fetch=True))
    assert "https://x.test/a" in _urls(repo)
    assert "fetching" not in capsys.readouterr().err


# -- bare `fux add` lists all three -----------------------------------------


def test_bare_add_lists_every_list(repo, monkeypatch, capsys):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    capsys.readouterr()
    _add(repo, monkeypatch, _args(None))
    out = capsys.readouterr().out
    assert "sources/dirs" in out and "sources/urls" in out and "sources/types" in out
    assert "https://x.test/a fetch=http meta=hashed" in out


def test_listing_marks_a_line_fux_did_not_write(repo, monkeypatch, capsys):
    (repo / ".fux" / "sources" / "urls").write_text("https://x.test/a\n", encoding="utf-8")
    _add(repo, monkeypatch, _args(None))
    out = capsys.readouterr().out
    assert "* https://x.test/a" in out
    assert "do not state every attribute" in out


def test_listing_an_empty_list_says_so(repo, monkeypatch, capsys):
    (repo / ".fux" / "sources" / "urls").write_text("", encoding="utf-8")
    _add(repo, monkeypatch, _args(None))
    assert "(empty)" in capsys.readouterr().out
