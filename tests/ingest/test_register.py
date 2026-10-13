"""The committed register — `.fux/index/REGISTER` (W-199 D4; shape v2, W-279).

🔴 **The one property that makes a derived file safe to commit is byte-identity
across runs**, and it is the property a reviewer cannot see. Everything else
here is shape; `test_two_ingests_write_the_register_once` is the rule.

The shape is [SR-INGEST](../../records/0106_ingest.md) decision 22's: a format
line carrying `rules=`, a column header, `loc ⇥ sha ⇥ decoder`, and a `k=v`
tail present only when it holds a value. The reader parses by the header.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.ingest import register
from fux.ingest.extract import RULES_VERSION
from l12_fixtures import write_config


def _repo(tmp_path: Path, *, dirs: str = "docs\n") -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text(dirs, encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    write_config((fux).parent)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A\n\nthe rota hands over Monday\n", encoding="utf-8")
    (docs / "b.md").write_text("# B\n\nthe dock closes at six\n", encoding="utf-8")
    return tmp_path


def _ingest(root: Path) -> None:
    from fux.ingest.run import run

    run(root, refresh_urls=False, full=False)


# --- the rule ---------------------------------------------------------------

def test_two_ingests_write_the_register_once(tmp_path):
    """🔴 L4, and the whole argument for committing this file.

    The first run indexes every document and the second reuses every one — from
    identical sources. If any run-shaped value reached the file, these bytes
    would differ and the register would be a file that changes for no reason
    anybody can explain from the corpus.

    ⚠ **This is exactly why the ruling's `outcome` column is not here.**
    `indexed` then `reused` is what that column would have said on these two
    runs. See `ingest/register.py`'s docstring.
    """
    root = _repo(tmp_path)
    _ingest(root)
    first = register.path_for(root).read_bytes()
    _ingest(root)
    assert register.path_for(root).read_bytes() == first


def test_it_is_written_only_when_the_bytes_change(tmp_path):
    root = _repo(tmp_path)
    _ingest(root)
    path = register.path_for(root)
    before = path.stat().st_mtime_ns
    _ingest(root)
    assert path.stat().st_mtime_ns == before


# --- the shape --------------------------------------------------------------

def test_the_file_opens_with_the_format_line_then_the_column_header(tmp_path):
    """Both `#` lines are part of the bytes. `rules=` on the format line is
    `extract.RULES_VERSION`, so a bare `prose` row is dated once for the whole
    file instead of digesting 1 364 rows and churning them on every upgrade."""
    root = _repo(tmp_path)
    _ingest(root)
    lines = register.path_for(root).read_text(encoding="utf-8").splitlines()
    assert lines[0] == f"# fux.register.v2\trules={RULES_VERSION}"
    assert lines[0] == register.format_line(RULES_VERSION)
    assert lines[1] == register.HEADER == "# loc\tsha\tdecoder\t[k=v ...]"
    assert lines[2:] == [
        f"docs/a.md\t{register.read(root).rows['docs/a.md'].sha}\tprose",
        f"docs/b.md\t{register.read(root).rows['docs/b.md'].sha}\tprose",
    ]


def test_it_is_sorted_by_loc_whatever_order_the_records_arrive_in():
    rows = [
        register.Row(loc="z.md", sha="s3", decoder="md@sha:1"),
        register.Row(loc="a.md", sha="s1", decoder="md@sha:1"),
        register.Row(loc="m.md", sha="s2", decoder="md@sha:1"),
    ]
    body = register.render(rows, rules=RULES_VERSION).splitlines()[2:]
    assert [line.split("\t")[0] for line in body] == ["a.md", "m.md", "z.md"]
    assert register.render(rows, rules=RULES_VERSION) == register.render(list(reversed(rows)), rules=RULES_VERSION)


def test_a_tail_is_absent_when_it_holds_nothing():
    """No sentinel: the v1 file wrote `-` on 2 363 of 2 363 rows for a field
    that was never a field. A row with nothing to say ends at its decoder."""
    row = register.Row(loc="docs/a.md", sha="s", decoder="prose")
    assert row.rendered() == "docs/a.md\ts\tprose"
    assert "\t-" not in register.render([row], rules=RULES_VERSION)


def test_the_tail_keys_come_in_record_order():
    row = register.Row(
        loc="https://x.test/a", sha="s", decoder="html@sha:abc",
        attrs=(("archived", "true"), ("fetch", "cdp")),
    )
    assert row.rendered() == "https://x.test/a\ts\thtml@sha:abc\tarchived=true\tfetch=cdp"


# --- what it holds, and what it must never hold -----------------------------

def test_it_names_every_indexed_document_and_nothing_else(tmp_path):
    root = _repo(tmp_path)
    _ingest(root)
    reg = register.read(root)
    assert reg.state == "v2" and reg.rules == RULES_VERSION
    assert set(reg.rows) == {"docs/a.md", "docs/b.md"}
    assert all(r.sha and r.decoder == "prose" and r.attrs == () for r in reg.rows.values())


def test_archived_true_appears_on_exactly_the_documents_under_an_archived_entry(tmp_path):
    root = _repo(tmp_path, dirs="docs\nold archived=true\n")
    old = root / "old"
    old.mkdir()
    (old / "retired.md").write_text("# Retired\n\nthe cold store is gone\n", encoding="utf-8")
    _ingest(root)
    rows = register.read(root).rows
    assert rows["old/retired.md"].attrs == (("archived", "true"),)
    assert rows["docs/a.md"].attrs == () and rows["docs/b.md"].attrs == ()


def test_a_url_row_carries_its_fetcher_and_a_file_row_carries_none():
    rows = register.rows_from(
        [
            {"id": "url:https://x.test/a", "loc": "https://x.test/a", "sha": "s1", "src": "url"},
            {"id": "file:docs/a.md", "loc": "docs/a.md", "sha": "s2"},
        ],
        {"url:https://x.test/a": ("html@sha:abc", "cdp"), "file:docs/a.md": ("md@sha:1", None)},
    )
    by_loc = {r.loc: r for r in rows}
    assert by_loc["https://x.test/a"].attr("fetch") == "cdp"
    assert by_loc["https://x.test/a"].rendered().endswith("\tfetch=cdp")
    assert by_loc["docs/a.md"].attr("fetch") is None
    assert by_loc["docs/a.md"].rendered() == "docs/a.md\ts2\tmd@sha:1"


def test_a_url_rows_decoder_and_fetcher_come_from_the_committed_list(tmp_path):
    """L4 through a different door: a networked run knows what fetched each URL
    this run and an offline run knows nothing. If the row read the run, the
    file would change with the KIND of run that wrote it. It reads the list."""
    root = _repo(tmp_path)
    (root / "fux.toml").write_text("[sources]\n[sources.url]\nmax_parallel = 4\n", encoding="utf-8")
    fetchers = root / ".fux" / "fetchers"
    fetchers.mkdir(parents=True, exist_ok=True)
    (fetchers / "cdp.py").write_text("def fetch(url): ...\n", encoding="utf-8")
    (root / ".fux" / "sources" / "urls").write_text("https://x.test/a fetch=cdp decoder=prose\n", encoding="utf-8")
    write_config(root)
    assert register.url_provenance(root) == {"url:https://x.test/a": ("prose", "cdp")}
    rows = register.rows_for(
        root,
        [{"id": "url:https://x.test/a", "loc": "https://x.test/a", "sha": "s1", "src": "url"}],
        {},
    )
    assert rows[0].rendered() == "https://x.test/a\ts1\tprose\tfetch=cdp"


def test_it_carries_no_clock_and_no_run_id(tmp_path):
    """L4, asserted on the bytes rather than on the writer's intentions."""
    root = _repo(tmp_path)
    _ingest(root)
    text = register.path_for(root).read_text(encoding="utf-8")
    for forbidden in ("run_seq", "T00:", "timestamp", "mtime", "indexed", "reused"):
        assert forbidden not in text


def test_it_never_grows_a_query_field():
    """🔴 [L9](../../records/0011_LAW-9-use-record.md) is the reason this file may
    be committed at all: it records what the CORPUS is, never who went looking.

    The moment a column or a tail key names a question, a query or a reader, a
    committed path is carrying a use record — the one thing L9 forbids. The
    column list AND the closed key set are asserted here so that adding one is
    a deliberate act with a failing test in front of it.
    """
    assert [f for f in register.Row.__dataclass_fields__] == ["loc", "sha", "decoder", "attrs"]
    assert register.KEYS == ("archived", "fetch")


def test_the_writer_refuses_a_key_the_record_does_not_state():
    """The key set is closed on the WRITE side, like the sources lists'. The
    reader keeps unknown keys so an older engine survives a newer file; the
    writer is this engine, and a key decision 22 does not state is a bug."""
    row = register.Row(loc="a.md", sha="s", decoder="prose", attrs=(("asked", "why"),))
    with pytest.raises(FuxError, match="asked"):
        register.render([row], rules=RULES_VERSION)
    spaced = register.Row(loc="a.md", sha="s", decoder="prose", attrs=(("fetch", "two words"),))
    with pytest.raises(FuxError, match="whitespace"):
        register.render([spaced], rules=RULES_VERSION)


# --- the reader parses by the header, never by count --------------------------

def test_a_v1_file_reads_as_old_format_not_as_missing(tmp_path):
    root = _repo(tmp_path)
    (root / ".fux" / "index").mkdir(parents=True, exist_ok=True)
    register.path_for(root).write_text(
        f"{register.HEADER_V1}\ndocs/a.md\tfile\tabc\tprose\t-\n", encoding="utf-8"
    )
    reg = register.read(root)
    assert reg.state == "old" and reg.rows == {} and reg.rules is None


def test_an_unknown_tail_key_is_kept(tmp_path):
    """So an older engine survives a newer file — and `fux doctor` can still
    compare the columns it does know."""
    root = _repo(tmp_path)
    (root / ".fux" / "index").mkdir(parents=True, exist_ok=True)
    register.path_for(root).write_text(
        f"{register.format_line(RULES_VERSION)}\n{register.HEADER}\n"
        "docs/a.md\tabc\tprose\tsections=4\tarchived=true\n",
        encoding="utf-8",
    )
    row = register.read(root).rows["docs/a.md"]
    assert row.attrs == (("sections", "4"), ("archived", "true"))
    assert row.attr("sections") == "4"


def test_a_missing_file_reads_as_missing(tmp_path):
    assert register.read(tmp_path).state == "missing"


def test_a_truncated_row_describes_nothing(tmp_path):
    root = _repo(tmp_path)
    (root / ".fux" / "index").mkdir(parents=True, exist_ok=True)
    register.path_for(root).write_text(
        f"{register.format_line(RULES_VERSION)}\n{register.HEADER}\nnot\tenough\n", encoding="utf-8"
    )
    reg = register.read(root)
    assert reg.state == "v2" and reg.rows == {}


def test_the_format_line_is_read_by_key_not_by_position():
    reg = register.parse(f"# fux.register.v2\tcomment=x\trules=7\n{register.HEADER}\n")
    assert reg.rules == 7 and reg.state == "v2"


# --- it must never be able to fail a run ------------------------------------

def test_a_write_that_cannot_happen_is_swallowed(tmp_path, monkeypatch):
    """A register that can fail an ingest is worse than one that is a run
    behind — `fux doctor`'s `register` row reports the second, and nothing can
    report the first."""
    root = _repo(tmp_path)
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: (_ for _ in ()).throw(OSError("full")))
    register.write(root, [register.Row(loc="a", sha="s", decoder="d")], rules=RULES_VERSION)


# --- `fux register [--json]` — the same rows, from the index -------------------

def test_fux_register_prints_the_files_bytes_on_a_current_index(tmp_path):
    """The verb derives the rows from the index, the decoder digest table and
    the URL list — the same inputs `fux ingest` wrote the file from — so on a
    current index `fux register | diff - .fux/index/REGISTER` is empty."""
    root = _repo(tmp_path, dirs="docs\nold archived=true\n")
    (root / "old").mkdir()
    (root / "old" / "r.md").write_text("# R\n\nretired\n", encoding="utf-8")
    _ingest(root)
    rows, rules = register.from_index(root)
    assert register.render(rows, rules=rules) == register.path_for(root).read_text(encoding="utf-8")


def test_json_round_trips_the_same_rows(tmp_path):
    root = _repo(tmp_path, dirs="docs\nold archived=true\n")
    (root / "old").mkdir()
    (root / "old" / "r.md").write_text("# R\n\nretired\n", encoding="utf-8")
    _ingest(root)
    rows, rules = register.from_index(root)
    objects = [json.loads(json.dumps(register.as_json(r, rules=rules))) for r in rows]
    assert all(o["rules"] == rules for o in objects)
    assert all(o["decoder"] == {"name": "prose", "digest": None} for o in objects)
    rebuilt = [
        register.Row(
            loc=o["loc"], sha=o["sha"],
            decoder=o["decoder"]["name"] + (f"@sha:{o['decoder']['digest']}" if o["decoder"]["digest"] else ""),
            attrs=tuple((k, "true" if v is True else v) for k, v in o.items() if k in register.KEYS),
        )
        for o in objects
    ]
    assert sorted(rebuilt, key=lambda r: r.loc) == sorted(rows, key=lambda r: r.loc)
    assert {o["loc"]: o.get("archived") for o in objects} == {
        "docs/a.md": None, "docs/b.md": None, "old/r.md": True,
    }


def test_json_names_a_consumer_decoder_by_name_and_digest():
    row = register.Row(loc="x.csv", sha="s", decoder="csv@sha:2c37b28e4a9f6292")
    assert register.as_json(row, rules=5)["decoder"] == {"name": "csv", "digest": "2c37b28e4a9f6292"}


def test_the_verb_is_the_same_rows_via_the_cli(tmp_path, monkeypatch, capsys):
    from fux.cli import main

    root = _repo(tmp_path)
    _ingest(root)
    monkeypatch.chdir(root)
    assert main(["register", "--no-output-config"]) == 0
    assert capsys.readouterr().out == register.path_for(root).read_text(encoding="utf-8")
    assert main(["register", "--json", "--no-output-config"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [json.loads(line)["loc"] for line in lines] == ["docs/a.md", "docs/b.md"]
