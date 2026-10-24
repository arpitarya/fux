"""`fux add` / `fux remove` / `fux ingest` — the managing commands (W-63, W-177).

Successor to `test_url_command.py`, which tested `fux url` before that verb
was retired. **Every property that file pinned is still pinned here** — a
written line states every attribute (SR-SOURCES decision 12), the command
opens no socket of its own, it edits one line rather than regenerating the
file, and the file is LF-only with exactly one trailing newline. What is new
is that all of it now holds for three lists instead of one, plus the two
decisions the verbs added: dispatch-on-entry, and remove-by-coverage.

**W-294:** paths and URLs are the two halves of ONE file, `.fux/sources.yaml`
(a strict YAML subset). `fux add` edits it by a textual insert — one item into
the right `paths:` list, or one entry block under `urls:` — and never re-renders
it, so comments and hand order survive; `!` left the file for `.fuxignore`.

Nothing here runs a full ingest unless the test is about ingest: `--no-ingest`
keeps these unit tests about the *list*, which is what they are for.
"""

from __future__ import annotations

from l12_fixtures import config_file, write_dirs, write_urls
import json

from types import SimpleNamespace

import pytest

from fux import sources
from fux.errors import FuxError
from fux.acquire import sourcelist, sourcesfile, typesfile
from l12_fixtures import listed_paths, listed_urls, sources_path, write_config


def _args(entry=None, **flags):
    base = {
        "cdp": False, "http": False, "plain": False, "hashed": False,
        "archived": False, "types": False, "dry_run": False, "decoder": None,
        "no_ingest": True, "no_fetch": True, "no_accelerator": True,
    }
    #: 🔴 **A URL entry gets `--decoder prose`, and `no_fetch=True` is why.**
    #: Since the pipe ruling a URL line states its decoder, and `fux add`
    #: OBSERVES it on the one fetch it performs — which `--no-fetch` forbids, so
    #: the flag makes `--decoder` mandatory. Nearly every case here is about
    #: something else and stays offline, so the pin is supplied for them.
    #: `test_no_fetch_without_a_decoder_is_refused` is the case that is not.
    #:
    #: ⚠ **Keyed on the ENTRY's shape, never put in `base`.** `--decoder` on a
    #: `dirs` entry is a refusal by design (the attribute set is closed), and on
    #: a `--types` entry it would override the decoder `fux add` resolves from
    #: the live registry — which is what half the types cases here assert.
    if (
        "decoder" not in flags
        and not flags.get("types")
        and str(entry or "").lower().startswith(("http://", "https://"))
    ):
        base["decoder"] = "prose"
    return SimpleNamespace(entry=entry, **(base | flags))


@pytest.fixture
def repo(tmp_path):
    # 🔴 **A routes table, because `fux add <url>` now RESOLVES a fetcher and
    # refuses when nothing matches** (W-199 D1, 2026-09-20). Before that it
    # wrote `fetch=http` from the engine default; there is no default any more,
    # so a fixture repo that means to accept a URL has to say which fetcher
    # reaches it — which is the behaviour under test in several cases below.
    (tmp_path / "fux.toml").write_text(
        '[sources]\n[sources.url]\n'
        '[sources.url.routes]\n"x.test" = "http"\n"*.x.test" = "http"\n'
        '"wiki.test" = "http"\n"example.com" = "http"\n',
        encoding="utf-8",
    )
    fetchers = tmp_path / ".fux" / "fetchers"
    fetchers.mkdir(parents=True)
    (fetchers / "http.py").write_text(
        'def fetch(url):\n    return "# T\\n\\nbody\\n"\n', encoding="utf-8"
    )
    (fetchers / "cdp.py").write_text(
        'def fetch(url):\n    return "# T\\n\\nbody\\n"\n', encoding="utf-8"
    )
    sources_path(tmp_path).write_text("# my list\npaths:\n  include:\n    - docs\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/config/pii.toml refuses; empty redacts nothing.
    (config_file(tmp_path, "pii")).write_text("", encoding="utf-8")
    write_config(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("# B\n\nbody\n", encoding="utf-8")
    return tmp_path


def _text(repo):
    """`.fux/sources.yaml`, as bytes a human would read."""
    return sources_path(repo).read_text(encoding="utf-8")


def _parsed(repo):
    return sourcesfile.parse(_text(repo), origin=str(sources_path(repo)))


def _url(repo, url):
    """The attributes `url`'s entry states, or None when it is not listed."""
    entry = next((e for e in _parsed(repo).urls if e.value == url), None)
    return None if entry is None else {k: entry.attrs[k] for k in entry.declared}


def _paths(repo):
    """`{path: sorted lists it sits in}` — the flags ARE the lists (W-294)."""
    out = {}
    for e in _parsed(repo).paths:
        lists = [f for f in sourcesfile.PATH_LISTS if f != sourcesfile.INCLUDE and e.attrs.get(f) == "true"]
        out[e.value] = lists or [sourcesfile.INCLUDE]
    return out


#: Every attribute a fux-written URL entry states at the built-ins, in order.
_FULL = {"fetch": "http", "decoder": "prose", "keep": "true", "ttl": "24h",
         "enrich": "false", "archived": "false", "update": "auto"}


def _types(repo):
    return (config_file(repo, "formats")).read_text(encoding="utf-8")


def _add(repo, monkeypatch, args):
    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    return sources.cmd_add(args)


def _remove(repo, monkeypatch, args):
    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    return sources.cmd_remove(args)


def _ingest_args(entry=None, **flags):
    """`fux ingest`'s namespace — the absorbed surface, all of it (W-177).

    Separate from `_args` because the two verbs no longer share a shape:
    `ingest` carries `--check`, `--json`, `--refetch-all`, `--failed`,
    `--no-fetch`, `--full` and the two runner flags, and `add`/`remove` carry
    none of them. `no_fetch` defaults **False** here — the bare verb goes to
    the network now, and a fixture that quietly opted out would test the wrong
    default.
    """
    base = {
        "check": False, "json": False, "list_skipped": False,
        "refetch_all": False, "failed": False, "no_fetch": False,
        "full": False, "no_accelerator": True, "stop": False,
        "spawn_runner": False, "runner": False, "progress": None,
    }
    return SimpleNamespace(entry=entry, **(base | flags))


def _ingest(repo, monkeypatch, args):
    """What `fux ingest` does once W-177 folded `fux update` into it.

    ⚠ **This drives `cmd_ingest`, not a `sources` entry point.** The verb lives
    in `fux.ingest` now and `sources` keeps only the planning half, so a test
    that called `sources.cmd_update` would have gone on passing against a
    function no CLI path reaches.
    """
    from fux import ingest as ingest_mod

    monkeypatch.setattr("fux.sources.find_root", lambda: repo)
    monkeypatch.setattr("fux.ingest.find_root", lambda: repo)
    return ingest_mod.cmd_ingest(args)


# -- dispatch: the entry decides which list ---------------------------------


@pytest.mark.parametrize(
    "entry, flags, expected",
    [
        ("https://x.test/a", {}, sourcelist.URLS),
        ("http://x.test/a", {}, sourcelist.URLS),
        ("docs", {}, sourcelist.PATHS),
        ("docs/one.md", {}, sourcelist.PATHS),
        ("*.pdf", {"types": True}, sourcelist.TYPES),
        # `--types` wins over the shape, because it is the explicit statement.
        ("weird", {"types": True}, sourcelist.TYPES),
    ],
)
def test_dispatch_picks_the_list_from_the_entry(entry, flags, expected):
    assert sources.dispatch(entry, SimpleNamespace(**({"types": False} | flags))) is expected


def test_a_glob_is_not_sniffed_into_the_type_list():
    """`docs/*` is a reasonable path entry, so `*` may not mean `--types`.

    Guessing between the two lists on a glob character would be wrong exactly
    when it mattered, and silently — the entry would land in a file the user
    never looked at.
    """
    assert sources.dispatch("docs/*", SimpleNamespace(types=False)) is sourcelist.PATHS


def test_a_trailing_slash_is_the_same_directory(repo, monkeypatch, capsys):
    """`docs/` and `docs` are one entry, and the list must not hold both.

    The parser dedupes on the exact string, so it cannot see this duplicate.
    Found by running the verb: `fux add docs/` against a list already holding
    `docs` wrote a second line for the same directory.
    """
    _add(repo, monkeypatch, _args("docs/"))
    # Since W-294 a path's flags are the lists it sits in, so `docs` in
    # `include` already says everything `docs/` would: nothing to write.
    assert _paths(repo) == {"docs": ["include"]}
    assert _text(repo).count("- docs") == 1
    assert "unchanged" in capsys.readouterr().out


# -- decision 12: a written line states everything --------------------------


def test_a_written_entry_carries_every_attribute_even_at_its_default(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    assert _url(repo, "https://x.test/a") == _FULL
    assert "  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n    keep: true\n" in _text(repo)


def test_a_path_lands_in_the_list_its_flags_name(repo, monkeypatch):
    """W-294: a path has no attribute line — `include` unless a flag names
    `archived` or `enrich`, and the list IS the flag."""
    (repo / "handbook").mkdir()
    (repo / "old").mkdir()
    _add(repo, monkeypatch, _args("handbook"))
    _add(repo, monkeypatch, _args("old", archived=True))
    assert _paths(repo) == {"docs": ["include"], "handbook": ["include"], "old": ["archived"]}
    assert "  include:\n    - docs\n    - handbook\n  archived:\n    - old\n" in _text(repo)


def test_moving_a_path_to_another_list_is_an_update_not_a_second_entry(repo, monkeypatch, capsys):
    _add(repo, monkeypatch, _args("docs", archived=True))
    assert _paths(repo) == {"docs": ["archived"]}
    assert "include:" not in _text(repo), "an emptied list is deleted, never left `[]`"
    assert "updated" in capsys.readouterr().out


def test_a_types_entry_a_decoder_reads_becomes_a_binding(repo, monkeypatch):
    """⚠ **This test asserted `*.pdf` carried NO binding until 2026-09-01**, and a
    `*.pdf decoder=pdf` LINE until 2026-09-11 (SR-TYPES decisions 11 and 12). The
    binding fux would otherwise derive is written down, and since decision 12 it is
    a `[decoders]` line — the extension is the key."""
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    assert '\npdf = "pdf"\n' in _types(repo)


def test_a_prose_type_is_an_include_glob_because_no_decoder_reads_it(repo, monkeypatch):
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    _add(repo, monkeypatch, _args("*.tex", types=True))
    text = _types(repo)
    assert '\n  "*.md",\n' in text and '\n  "*.tex",\n' in text
    assert "tex =" not in text


def test_adding_a_type_edits_one_line_and_keeps_a_comment(repo, monkeypatch):
    """The writer's contract, unchanged by the move to TOML: one line changes and a
    human's comment inside the array survives."""
    (config_file(repo, "formats")).write_text(
        '# mine\ninclude = [\n  "*.md",  # our docs\n  "*.txt",\n]\n', encoding="utf-8"
    )
    _add(repo, monkeypatch, _args("*.rst", types=True))
    assert _types(repo) == '# mine\ninclude = [\n  "*.md",  # our docs\n  "*.rst",\n  "*.txt",\n]\n'


def test_the_writer_refuses_a_layout_it_did_not_write(repo, monkeypatch):
    """Reformatting an inline array would eat the comments around it, so fux says so
    and writes nothing (SR-TYPES decision 12, reader lenient / writer strict)."""
    from fux.errors import FuxError

    original = 'include = ["*.md", "*.txt"]\n'
    (config_file(repo, "formats")).write_text(original, encoding="utf-8")
    with pytest.raises(FuxError, match="will not edit it"):
        _add(repo, monkeypatch, _args("*.rst", types=True))
    assert _types(repo) == original


def test_a_bare_glob_moves_into_decoders_when_it_gains_a_binding(repo, monkeypatch, capsys):
    (config_file(repo, "formats")).write_text('include = [\n  "*.md",\n  "*.pdf",\n]\n', encoding="utf-8")
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    text = _types(repo)
    assert '"*.pdf"' not in text and '\npdf = "pdf"\n' in text
    assert "updated" in capsys.readouterr().out


def test_removing_a_type_deletes_its_line_and_never_excludes(repo, monkeypatch, capsys):
    from fux.errors import FuxError

    _add(repo, monkeypatch, _args("*.pdf", types=True))
    assert _remove(repo, monkeypatch, _args("*.pdf", types=True)) == 0
    assert "pdf =" not in _types(repo)
    with pytest.raises(FuxError, match="fuxignore"):
        _remove(repo, monkeypatch, _args("*.nothere", types=True))
    assert "!" not in "".join(ln for ln in _types(repo).splitlines() if not ln.startswith("#"))


def test_a_leftover_line_grammar_types_file_stops_the_verb(repo, monkeypatch):
    from fux.errors import FuxError

    # The fixture now writes `.fux/config/formats.toml` (W-225 stage 4a: the file is
    # required), so the pre-migration state — the old file ALONE — is made here.
    (config_file(repo, "formats")).unlink()
    (repo / ".fux" / "sources").mkdir(parents=True, exist_ok=True)
    (repo / ".fux" / "sources" / "types").write_text("*.md\n", encoding="utf-8")
    with pytest.raises(FuxError, match="fux setup"):
        _add(repo, monkeypatch, _args("*.pdf", types=True))
    assert not (config_file(repo, "formats")).exists()


def test_flags_decide_what_is_recorded(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a", cdp=True, plain=True))
    assert _url(repo, "https://x.test/a")["fetch"] == "cdp"


def test_an_unflagged_attribute_keeps_what_the_entry_already_said(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a", cdp=True, plain=True))
    _add(repo, monkeypatch, _args("https://x.test/a", hashed=True))
    assert _url(repo, "https://x.test/a")["fetch"] == "cdp"
    assert _text(repo).count("url: https://x.test/a") == 1


def test_two_flags_for_one_attribute_is_an_error(repo, monkeypatch):
    with pytest.raises(FuxError, match="pick one"):
        _add(repo, monkeypatch, _args("https://x.test/a", cdp=True, http=True))


def test_a_flag_the_list_does_not_have_is_an_error_not_a_no_op(repo, monkeypatch):
    """`fux add docs --cdp` is someone believing something false about the line.

    The closed attribute set (SR-SOURCES decision 11) is only worth having
    if it is enforced on the way in as well as on the way out.
    """
    with pytest.raises(FuxError, match="which `paths` does not have"):
        _add(repo, monkeypatch, _args("docs", cdp=True))


def test_archived_is_now_legal_on_a_url_too(repo, monkeypatch):
    """W-126, 2026-09-11. This assertion used to run the other way.

    `fux add <URL> --archived` was *the* example of a flag `urls` does not
    have, in the test above. It has it now, and a retired page behind a URL can
    finally be declared retired — the asymmetry was never a decision, just the
    order the two lists were built in.
    """
    _add(repo, monkeypatch, _args("https://x.test/a", archived=True))
    assert _url(repo, "https://x.test/a") == _FULL | {"archived": "true"}


def test_a_non_http_url_is_refused_before_anything_is_written(repo, monkeypatch):
    before = _text(repo)
    with pytest.raises(FuxError, match="not an http"):
        # It dispatches to `dirs` by shape, so force the list to prove the
        # validator runs per-list rather than only on things that look like URLs.
        _add(repo, monkeypatch, _args("ftp://x.test/a"))
    assert _text(repo) == before


def test_adding_a_path_that_is_not_on_disk_writes_nothing(repo, monkeypatch):
    """A line that breaks the next ingest is worse than a refused command."""
    before = _text(repo)
    with pytest.raises(FuxError, match="does not exist"):
        _add(repo, monkeypatch, _args("nope"))
    assert _text(repo) == before


def test_adding_something_already_excluded_is_an_error(repo, monkeypatch):
    """There is no un-exclude, so `add` may not pretend to be one.

    ⚠ **The exclusion is a `.fuxignore` pattern since W-165 fix 1**, and this
    test is the reason that move needed a second guard. `add` checked only the
    `!` lines in `dirs`; pointing `remove` at the other file would have turned
    `add` into the un-exclude this refuses, and the command would have reported
    success while `.fuxignore` went on beating the line it wrote.
    """
    _remove(repo, monkeypatch, _args("docs/a.md"))
    with pytest.raises(FuxError, match="no un-exclude"):
        _add(repo, monkeypatch, _args("docs/a.md"))


def test_adding_something_a_hand_written_ignore_covers_is_an_error(repo, monkeypatch):
    """The same refusal for a pattern nothing in `dirs` knows about.

    A person's own `.fuxignore` line is the common case, and it reaches `add`
    through exactly the path a `fux remove`-written one does.
    """
    ignore = repo / ".fux" / ".fuxignore"
    ignore.write_text("/docs/a.md\n", encoding="utf-8")
    with pytest.raises(FuxError, match="no un-exclude"):
        _add(repo, monkeypatch, _args("docs/a.md"))


# -- one insert, never the file (W-294 step 4) -------------------------------


_HAND = (
    "# team sources\n"
    "paths:\n"
    "  include:\n"
    "    - work      # the shared memory\n"
    "    - docs\n"
    "\n"
    "# team A\n"
    "urls:\n"
    "  - url: https://x.test/a   # the runbook\n"
    "    fetch: http\n"
    "    decoder: prose\n"
    "\n"
    "  # team B\n"
    "  - url: https://x.test/z\n"
    "    fetch: http\n"
    "    decoder: prose\n"
)


def _hand(repo):
    (repo / "work").mkdir()
    (repo / "handbook").mkdir()
    sources_path(repo).write_text(_HAND, encoding="utf-8")


def test_a_grouping_comment_survives_an_edit(repo, monkeypatch):
    _hand(repo)
    _add(repo, monkeypatch, _args("https://x.test/a", plain=True))
    _add(repo, monkeypatch, _args("https://x.test/m"))
    _add(repo, monkeypatch, _args("handbook"))
    text = _text(repo)
    for comment in ("# team sources", "# the shared memory", "# team A", "# team B"):
        assert comment in text, comment


def test_a_trailing_comment_survives_an_edit(repo, monkeypatch):
    _hand(repo)
    _add(repo, monkeypatch, _args("https://x.test/a", cdp=True))
    assert "  - url: https://x.test/a   # the runbook\n    fetch: cdp\n" in _text(repo)


def test_an_insert_never_reorders_what_a_human_wrote(repo, monkeypatch):
    """The file is NOT re-rendered: `work` stays above `docs` exactly as the
    human left it, and only the inserted line is new. File order is for
    humans; the loader sorts (L4), so it cannot move a committed index byte."""
    _hand(repo)
    before = _text(repo).splitlines()
    _add(repo, monkeypatch, _args("handbook"))
    after = _text(repo).splitlines()
    added = [line for line in after if line not in before]
    assert added == ["    - handbook"]
    assert [line for line in after if line != "    - handbook"] == before
    assert after.index("    - work      # the shared memory") < after.index("    - docs")


def test_a_url_entry_lands_as_one_block_and_touches_no_other_line(repo, monkeypatch):
    _hand(repo)
    before = _text(repo).splitlines()
    _add(repo, monkeypatch, _args("https://x.test/m"))
    after = _text(repo).splitlines()
    block = ["  - url: https://x.test/m", *[f"    {k}: {v}" for k, v in _FULL.items()]]
    at = after.index(block[0])
    assert after[at : at + len(block)] == block
    assert after[:at] + after[at + len(block):] == before
    assert listed_urls(repo) == ["https://x.test/a", "https://x.test/m", "https://x.test/z"]


def test_entries_added_to_a_sorted_list_keep_it_sorted(repo, monkeypatch):
    for url in ("https://x.test/c", "https://x.test/a", "https://x.test/b"):
        _add(repo, monkeypatch, _args(url))
    order = [line.split("url: ")[1] for line in _text(repo).splitlines() if "url: " in line]
    assert order == sorted(order)


def test_the_file_always_ends_in_exactly_one_newline(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    text = _text(repo)
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_the_file_is_written_lf_only_regardless_of_host_os(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    assert b"\r\n" not in sources_path(repo).read_bytes()
    (repo / "handbook").mkdir()
    _add(repo, monkeypatch, _args("handbook"))
    assert b"\r\n" not in sources_path(repo).read_bytes()


def test_a_fragment_bearing_url_round_trips_through_the_command(repo, monkeypatch):
    """`#` with no space before it is TEXT in the subset — `page#section` is a
    URL with a fragment, never a URL and a comment."""
    _add(repo, monkeypatch, _args("https://x.test/page#section"))
    assert _url(repo, "https://x.test/page#section")["fetch"] == "http"


def test_two_urls_differing_only_by_fragment_get_two_entries(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/page#a"))
    _add(repo, monkeypatch, _args("https://x.test/page#b"))
    assert listed_urls(repo) == ["https://x.test/page#a", "https://x.test/page#b"]


# -- remove-by-coverage (W-63 decision 4) -----------------------------------


def test_an_entry_with_its_own_line_is_removed_by_deleting_it(repo, monkeypatch, capsys):
    (repo / "handbook").mkdir()
    _add(repo, monkeypatch, _args("handbook"))
    _remove(repo, monkeypatch, _args("handbook"))
    assert "handbook" not in _text(repo)
    assert _paths(repo) == {"docs": ["include"]}
    assert "removed" in capsys.readouterr().out


def test_removing_the_last_path_of_a_list_deletes_the_list_key(repo, monkeypatch):
    """An empty list is refused by the reader, so the writer never leaves one."""
    (repo / "old").mkdir()
    _add(repo, monkeypatch, _args("old", archived=True))
    _remove(repo, monkeypatch, _args("old"))
    assert "archived:" not in _text(repo)
    assert _paths(repo) == {"docs": ["include"]}


def test_a_covered_entry_is_removed_by_writing_an_exclusion(repo, monkeypatch, capsys):
    """W-165 fix 1 — the exclusion lands in `.fuxignore`, and the manifest is
    untouched. Since W-294 `.fuxignore` is the ONLY place exclusion is spelled:
    `!` is refused in `.fux/sources.yaml`, read or written.
    """
    before = _text(repo)
    _remove(repo, monkeypatch, _args("docs/a.md"))
    ignore = (repo / ".fux" / ".fuxignore").read_text(encoding="utf-8")
    # Anchored with a leading `/`: a bare `docs/a.md` would be anchored by its
    # own slash, but the rule has to hold for a top-level entry too, where a
    # bare name means "at any depth" and would drop `archive/docs` as well.
    assert "/docs/a.md" in ignore
    assert _text(repo) == before  # nothing written next door; the ancestor stays listed
    out = capsys.readouterr().out
    assert "excluded" in out and "still listed" in out


def test_a_removed_directory_is_written_with_a_trailing_slash(repo, monkeypatch):
    """`build/` is a directory rule, so a *file* of that name later is untouched."""
    (repo / "docs" / "generated").mkdir()
    (repo / "docs" / "generated" / "x.md").write_text("# x\n", encoding="utf-8")
    _remove(repo, monkeypatch, _args("docs/generated"))
    assert "/docs/generated/" in (repo / ".fux" / ".fuxignore").read_text(encoding="utf-8")


def test_removing_something_neither_listed_nor_covered_names_both_checks(repo, monkeypatch):
    with pytest.raises(FuxError, match="no line of its own, and no listed entry covers it"):
        _remove(repo, monkeypatch, _args("elsewhere/x.md"))


def test_removing_a_url_always_deletes_the_line(repo, monkeypatch, capsys):
    """A URL has no ancestor, so there is only ever one branch to take."""
    _add(repo, monkeypatch, _args("https://x.test/a"))
    _remove(repo, monkeypatch, _args("https://x.test/a"))
    assert _url(repo, "https://x.test/a") is None
    assert "urls:" not in _text(repo), "the last entry takes the `urls:` key with it"
    assert "removed" in capsys.readouterr().out


def test_removing_a_url_that_is_not_listed_fails_loudly(repo, monkeypatch):
    with pytest.raises(FuxError, match="A URL has no ancestor to subtract from"):
        _remove(repo, monkeypatch, _args("https://x.test/missing"))


def test_removing_a_url_deletes_its_line_and_nothing_else(repo, monkeypatch):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    _add(repo, monkeypatch, _args("https://x.test/b"))
    _remove(repo, monkeypatch, _args("https://x.test/a"))
    text = _text(repo)
    assert _url(repo, "https://x.test/a") is None
    assert _url(repo, "https://x.test/b") == _FULL
    assert "# my list" in text
    assert _paths(repo) == {"docs": ["include"]}


def test_removing_a_hand_written_url_takes_its_whole_block_and_nothing_else(repo, monkeypatch):
    _hand(repo)
    _remove(repo, monkeypatch, _args("https://x.test/a"))
    text = _text(repo)
    assert "x.test/a" not in text and "# the runbook" not in text
    assert "# team B" in text and listed_urls(repo) == ["https://x.test/z"]


def test_removing_an_already_excluded_entry_says_so(repo, monkeypatch):
    """Removing something already removed is an error, not a quiet second line.

    The contract the `!`-line form kept, preserved across W-165 fix 1's change of
    write target — a caller's exit code depends on it, and a no-op line would be
    a `duplicate_warnings` conflict fux created itself.
    """
    _remove(repo, monkeypatch, _args("docs/a.md"))
    with pytest.raises(FuxError, match="already excluded"):
        _remove(repo, monkeypatch, _args("docs/a.md"))


def test_a_bang_entry_in_the_manifest_stops_the_verb_and_names_fuxignore(repo, monkeypatch):
    """W-294 step 2: `!` left the source list. A hand-written `!` entry is a loud
    `file:lineno` error naming `.fux/.fuxignore` — never read as an exclusion,
    never migrated as a side effect of a verb asked to do something else."""
    original = "paths:\n  include:\n    - docs\n    - '!docs/a.md'\n"
    sources_path(repo).write_text(original, encoding="utf-8")
    with pytest.raises(FuxError, match=r"sources\.yaml:4: .*\.fux/\.fuxignore"):
        _remove(repo, monkeypatch, _args("docs/a.md"))
    assert _text(repo) == original  # left exactly as it was
    assert not (repo / ".fux" / ".fuxignore").is_file()


# -- --dry-run writes no bytes ----------------------------------------------


def test_dry_run_add_writes_no_bytes(repo, monkeypatch, capsys):
    before = sources_path(repo).read_bytes()
    _add(repo, monkeypatch, _args("https://x.test/a", dry_run=True))
    assert sources_path(repo).read_bytes() == before
    out = capsys.readouterr().out
    assert "would add" in out and "fetch=http decoder=prose" in out


def test_dry_run_remove_writes_no_bytes_and_names_the_branch(repo, monkeypatch, capsys):
    before = sources_path(repo).read_bytes()
    _remove(repo, monkeypatch, _args("docs/a.md", dry_run=True))
    assert sources_path(repo).read_bytes() == before
    assert not (repo / ".fux" / ".fuxignore").is_file()
    assert "would exclude" in capsys.readouterr().out


# -- ingest re-reads and never writes a line --------------------------------


def test_ingest_refuses_an_entry_nobody_listed(repo, monkeypatch):
    with pytest.raises(FuxError, match="never creates a line"):
        _ingest(repo, monkeypatch, _ingest_args("docs/nothing.md"))
    assert "docs/nothing.md" not in _text(repo)


def test_ingest_no_fetch_still_refuses_an_entry_nobody_listed(repo, monkeypatch):
    """🔴 **The order inside `plan_url_refresh` is what this holds.**

    `--no-fetch` returns early, so locating the entry has to happen BEFORE it —
    otherwise `fux ingest --no-fetch typo` re-ingests the whole corpus and
    reports success, which is the silent-wrong-thing `_locate` exists to stop.
    """
    with pytest.raises(FuxError, match="never creates a line"):
        _ingest(repo, monkeypatch, _ingest_args("docs/nothing.md", no_fetch=True))


def test_ingest_with_no_url_source_still_runs_the_dirs_half(repo, monkeypatch, capsys):
    """**Not an error**, unlike the `--refresh-urls` this absorbed."""
    _ingest(repo, monkeypatch, _ingest_args(None))
    assert "ingested" in capsys.readouterr().out


def test_ingest_check_is_read_only_and_reports_drift(repo, monkeypatch, capsys):
    _ingest(repo, monkeypatch, _ingest_args(None))
    capsys.readouterr()

    before = {p: p.read_bytes() for p in (repo / ".fux" / "index").glob("*.jsonl")}
    (repo / "docs" / "a.md").write_text("# A\n\nchanged body\n", encoding="utf-8")

    assert _ingest(repo, monkeypatch, _ingest_args(None, check=True)) == 0
    out = capsys.readouterr().out
    assert "stale" in out and "docs/a.md" in out
    assert {p: p.read_bytes() for p in (repo / ".fux" / "index").glob("*.jsonl")} == before


def test_ingest_check_exits_zero_when_nothing_drifted(repo, monkeypatch, capsys):
    """Drift is a fact, not a failure — a script checking status must not see one."""
    _ingest(repo, monkeypatch, _ingest_args(None))
    capsys.readouterr()
    assert _ingest(repo, monkeypatch, _ingest_args(None, check=True)) == 0
    assert "nothing has drifted" in capsys.readouterr().out


def test_check_beats_list_skipped_when_both_are_given(repo, monkeypatch, capsys):
    """SR-INGEST decision 21 — the precedence is RULED, not argparse's order.

    Both flags print and exit. `--check` wins because it is the whole-corpus
    freshness question, the one with a `--json` form, and the one a pipeline
    gates on; `--list-skipped` reports on a walk this invocation will not do.
    """
    _ingest(repo, monkeypatch, _ingest_args(None))
    capsys.readouterr()
    assert _ingest(repo, monkeypatch, _ingest_args(None, check=True, list_skipped=True)) == 0
    out = capsys.readouterr().out
    assert "drifted" in out or "stale" in out, "the drift report is what must come back"
    assert "ingested" not in out, "neither flag may run an ingest"


# -- the type allowlist is extended, never replaced --------------------------


def test_adding_the_first_type_seeds_the_built_in_allowlist(repo, monkeypatch):
    """Otherwise `fux add '*.pdf' --types` un-indexes every markdown document.

    The file REPLACES the built-in default rather than extending it
    (SR-TYPES), so a one-entry file is a corpus-wide invisible filter — the
    exact defect W-55 was opened about. Found by running the verb.
    """
    from fux.acquire.gitdir import DEFAULT_TYPES, read_types

    # The fixture writes `.fux/config/formats.toml` (required since W-225 stage 4a);
    # the seed is `add`'s answer to a repo that has none, so remove it.
    (config_file(repo, "formats")).unlink()
    _add(repo, monkeypatch, _args("*.tex", types=True))
    allow = set(read_types(repo).allow)
    assert set(DEFAULT_TYPES) <= allow, "the seed IS the default, map included"
    assert "*.tex" in allow


def test_adding_a_second_type_does_not_re_seed(repo, monkeypatch):
    (config_file(repo, "formats")).unlink()  # the seeding path, as above
    _add(repo, monkeypatch, _args("*.pdf", types=True))
    _add(repo, monkeypatch, _args("*.tex", types=True))
    # Counted on the parsed list, not the text: the seeded file's own comment
    # spells `"*.md"` as an example since W-225 stage 4a made setup's seed the
    # file every repo starts with.
    assert typesfile.read(repo).include.count("*.md") == 1


# -- L5: these verbs open no socket of their own ----------------------------


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
    assert _url(repo, "https://x.test/a") == _FULL
    assert "fetching" not in capsys.readouterr().err


def _url_repo(repo):
    """`repo`, with a URL source configured and one URL listed.

    Enough for the fence tests below to be about the FLAG rather than about a
    repo that had nothing to fetch either way — a fixture with no
    `[sources.url]` passes them vacuously.
    """
    (repo / "fux.toml").write_text("[sources]\n[sources.url]\n", encoding="utf-8")
    write_config(repo)  # every other key from the template (SR-LAW-12)
    write_urls(repo, "https://x.test/a fetch=http decoder=prose keep=true ttl=24h "
        "enrich=false archived=false update=auto\n")
    # 🔴 **A REAL fetcher, and it is what makes the fence test load-bearing.**
    # With no `.fux/fetchers/http.py` a networked run dies on *fetcher not
    # found* before it ever reaches a socket — so the offline assertion would
    # pass for a reason that has nothing to do with the flag. This one opens
    # one, which is the thing `--no-fetch` has to stop.
    fetchers = repo / ".fux" / "fetchers"
    fetchers.mkdir(parents=True, exist_ok=True)
    # ⚠ **It leaves a FILE behind, and that is not belt-and-braces.** Ingest
    # catches a fetcher exception and turns it into `! <url> — …; prior record
    # kept` (decision 21a), so a bare `AssertionError` raised in here is
    # *swallowed* and the run still exits 0. The marker is the only evidence
    # that survives the guarantee.
    (fetchers / "http.py").write_text(
        "import pathlib\nimport socket\n\n\ndef fetch(url, **kw):\n"
        "    pathlib.Path(__file__).with_name(\"FETCHED\").write_text(url)\n"
        "    socket.create_connection((\"127.0.0.1\", 9), timeout=0.01)\n"
        "    return \"unreachable\"\n",
        encoding="utf-8",
    )
    return repo


def _fetch_marker(repo):
    return repo / ".fux" / "fetchers" / "FETCHED"


def _no_sockets(monkeypatch):
    """Every `socket.socket()` becomes a test failure, not a connection.

    🔴 **Asserting on stderr is not enough for this one.** The announcement is
    the thing a bug would leave in place while the fetch happened anyway, or
    remove while it still happened — so the fence has to be the syscall, which
    is what L5 is actually about.
    """
    import socket

    def refuse(*a, **kw):
        raise AssertionError("L5: this path opened a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def test_a_hook_path_ingest_opens_no_socket(repo, monkeypatch, capsys):
    """🔴 **W-177 DoD 4 — the fence, moved onto the flag the git hooks write.**

    `fux ingest` was offline *by construction* until W-177 made the bare verb
    networked (SR-CLI decision 16). The fence did not disappear; it moved to
    `--no-fetch`, which is the invocation `fux hooks` writes into `post-merge`
    and the one an air-gapped clone runs by hand. **Split by caller, not by flag
    default** — so this is the assertion that keeps the caller's half honest.
    """
    _no_sockets(monkeypatch)
    _ingest(_url_repo(repo), monkeypatch, _ingest_args(None, no_fetch=True))
    assert not _fetch_marker(repo).exists(), "the consumer fetcher was called"
    err = capsys.readouterr().err
    assert "fetching" not in err, "an offline run may not announce a fetch"


def test_the_hook_script_is_the_invocation_that_test_pins():
    """The two halves of decision 16d, held together.

    A fence test on `--no-fetch` proves nothing if the hook stopped writing the
    flag, and the hook is a string in another module — so the string is checked
    here rather than trusted.
    """
    from fux.maintain.hooks import HOOKS

    assert "fux ingest --no-fetch" in HOOKS["post-merge"]
    assert "fux ingest --spawn-runner" in HOOKS["post-commit"]
    for name, script in HOOKS.items():
        for line in script.splitlines():
            bare = line.strip()
            assert bare != "fux ingest", f"{name} runs the NETWORKED bare verb"


def test_check_opens_no_socket_either(repo, monkeypatch):
    """`--check` is documented read-only AND offline (SR-INGEST decision 21b).

    It is the form a pipeline runs on every commit, so *offline* has to be the
    syscall rather than the docstring.
    """
    _no_sockets(monkeypatch)
    assert _ingest(_url_repo(repo), monkeypatch, _ingest_args(None, check=True)) == 0
    assert not _fetch_marker(repo).exists(), "`--check` called the consumer fetcher"


# -- bare `fux add` lists all three -----------------------------------------


def test_bare_add_lists_every_list(repo, monkeypatch, capsys):
    _add(repo, monkeypatch, _args("https://x.test/a"))
    capsys.readouterr()
    _add(repo, monkeypatch, _args(None))
    out = capsys.readouterr().out
    assert ".fux/sources.yaml `paths:`" in out and ".fux/sources.yaml `urls:`" in out
    assert ".fux/config/formats.toml" in out
    assert "docs  (paths: include)" in out
    assert "https://x.test/a fetch=http decoder=prose" in out
    # A type prints as a type, not as a path (a W-294 regression, found here).
    assert "*.md  (paths: include)" not in out


def test_listing_marks_an_entry_fux_did_not_write(repo, monkeypatch, capsys):
    write_urls(repo, "https://x.test/a fetch=http decoder=prose\n")
    _add(repo, monkeypatch, _args(None))
    out = capsys.readouterr().out
    assert "* https://x.test/a" in out
    assert "do not state every attribute" in out


def test_listing_an_empty_list_says_so(repo, monkeypatch, capsys):
    write_urls(repo, "")
    write_dirs(repo, "")
    _add(repo, monkeypatch, _args(None))
    assert "(empty)" in capsys.readouterr().out


# -- W-140 row 5: the CLI overrode the consumer's own [sources.url] ----------


def test_a_cli_written_line_states_the_repo_policy_not_the_engine_default(tmp_path):
    """🔴 `fux add` wrote the ENGINE's defaults onto every line.

    Every generated line states every attribute (SR-SOURCES decision 12), and
    the values came from `spec.defaults()` — so a team with
    `[sources.url] ttl = "7d"` got `ttl=24h` written onto each line, and the
    middle layer of a three-layer resolution was dead for every line the CLI
    produced. That layer exists so a whole intranet is configured in one place.
    """
    from fux.acquire import sourcelist
    from fux.sources import _source_defaults, add

    (tmp_path / "fux.toml").write_text(
        "[sources]\n\n[sources.url]\n"
        'ttl = "7d"\n'
        "keep = false\n"
        'update = "never"\n'
        "max_parallel = 1\n",
        encoding="utf-8",
    )
    write_config(tmp_path)  # every other key from the template (SR-LAW-12)
    listing = write_urls(tmp_path, "")

    defaults = _source_defaults(tmp_path, sourcelist.URLS)
    _, line, _ = add(listing, "https://wiki.test/p", {"fetch": "cdp"}, sourcelist.URLS, defaults)

    assert "ttl=7d" in line
    assert "keep=false" in line and "update=never" in line

    # ⚠ **`fetch` LEFT the source-wide layer on 2026-09-20** (W-199 D2). This
    # case used to prove that `[sources.url] fetcher = ".fux/fetchers/cdp.py"`
    # reached a CLI-written line; that key is deleted, and `fux add` resolves a
    # stem per URL instead. The three attributes above still carry the layer
    # W-140 row 5 was about, and `fetch` arrives as a resolved override.
    assert "fetch=cdp decoder=prose" in line
    assert "fetch" not in defaults, (
        "`fetch` must not come back as a source-wide default - there is no default "
        "fetcher, and a silent one is what W-199 D2 deleted"
    )


def test_an_explicit_flag_still_beats_the_repo_policy(tmp_path):
    """Precedence is unchanged: built-in, then [sources.url], then the line."""
    from fux.acquire import sourcelist
    from fux.sources import _source_defaults, add

    (tmp_path / "fux.toml").write_text(
        '[sources]\n\n[sources.url]\nttl = "7d"\nmax_parallel = 1\n', encoding="utf-8"
    )
    listing = write_urls(tmp_path, "")

    defaults = _source_defaults(tmp_path, sourcelist.URLS)
    _, line, _ = add(listing, "https://wiki.test/p", {"fetch": "http", "decoder": "prose", "ttl": "30s"}, sourcelist.URLS, defaults)
    assert "ttl=30s" in line, "the flag beats the repo policy, which beats the built-in"


def test_a_repo_with_no_sources_url_is_untouched(tmp_path):
    """No `[sources.url]`, no `fux.toml`, an unreadable one — engine defaults."""
    from fux.acquire import sourcelist
    from fux.sources import _source_defaults

    assert _source_defaults(tmp_path, sourcelist.URLS) == {}
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    assert _source_defaults(tmp_path, sourcelist.URLS) == {}
    assert _source_defaults(tmp_path, sourcelist.PATHS) == {}


# -- W-140 row 14: the verb built to be read had nothing to read -------------


def _check_repo(tmp_path):
    from fux.ingest.run import run

    write_dirs(tmp_path, "docs\n")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (config_file(tmp_path, "pii")).write_text("", encoding="utf-8")
    write_config(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    (docs / "b.md").write_text("# B\n\nother\n", encoding="utf-8")
    run(tmp_path, refresh_urls=False, full=False)
    return tmp_path


def test_check_reports_drift_as_json(tmp_path, capsys, monkeypatch):
    """`--check` exits 0 whether or not anything drifted — deliberately, since
    drift is a fact and not a failure. With no `--json`, the only way to act on
    the answer was to parse a table meant for a person.
    """
    from fux.sources import _check

    _check_repo(tmp_path)
    (tmp_path / "docs" / "a.md").write_text("# A\n\nEDITED\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _check(tmp_path, None, as_json=True) == 0
    payload = json.loads(capsys.readouterr().out)

    assert [d["loc"] for d in payload["drifted"]] == ["docs/a.md"]
    drifted = payload["drifted"][0]
    assert drifted["state"] == "stale"
    assert drifted["indexed_sha"] != drifted["disk_sha"]
    assert payload["fresh"] == 1


def test_a_deleted_document_is_gone_not_stale(tmp_path, capsys, monkeypatch):
    from fux.sources import _check

    _check_repo(tmp_path)
    (tmp_path / "docs" / "b.md").unlink()
    monkeypatch.chdir(tmp_path)

    _check(tmp_path, None, as_json=True)
    payload = json.loads(capsys.readouterr().out)
    assert payload["drifted"] == [
        {"id": "file:docs/b.md", "loc": "docs/b.md", "state": "gone"}
    ]


def test_a_clean_tree_reports_an_empty_list_not_an_error(tmp_path, capsys, monkeypatch):
    from fux.sources import _check

    _check_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert _check(tmp_path, None, as_json=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["drifted"] == [] and payload["fresh"] == 2


def test_the_json_view_is_built_beside_the_text_never_parsed_out_of_it():
    """Two formats, one traversal. A JSON view derived from a human table is a
    second format that can disagree with the first."""
    import inspect

    from fux import sources

    body = inspect.getsource(sources._check)
    # W-233 added the families drift as a third pair, text and JSON together.
    assert body.count("stale.append") == body.count("findings.append") == 3
