"""W-287 through the shipped CLI — a table answers by row and by column.

The unit suite proves the scoring (`tests/refer/test_table_columns.py`) and the
decoders (`tests/decode/test_tables.py`). This proves what a user sees: `fux
answer` on a Markdown table, as a record with the asked cell first, in text and
in `--json` — and that turning the mechanism on writes nothing to the index (L3).
"""

from __future__ import annotations

from l12_fixtures import config_file, write_dirs
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from l12_fixtures import tune_text, write_config, write_tune

TICKETS = (
    "# Tickets\n\nWho owns what.\n\n"
    "| Ticket | Owner | Status | Notes |\n|---|---|---|---|\n"
    "| INC1 | Alice | closed | reopened once, still open questions |\n"
    "| INC2 | Bob | open | none |\n"
    "| INC3 | Carol | closed | see INC2 |\n"
    "| INC4 | Dan | closed | open source dependency |\n"
)


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def _repo(root: Path, column_weight: float) -> None:
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    write_dirs(root, "docs\n")
    (config_file(root, "pii")).write_text("", encoding="utf-8")
    write_tune(root, tune_text(ranking={"table_column_weight": column_weight}))
    write_config(root)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "tickets.md").write_text(TICKETS, encoding="utf-8", newline="\n")  # LF on Windows too


def _index_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted((root / ".fux" / "index").rglob("*")):
        if path.is_file():
            h.update(path.relative_to(root).as_posix().encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def test_answer_returns_the_row_as_a_record_with_the_asked_cell_first(tmp_path):
    _repo(tmp_path, 1.0)
    _run(tmp_path, "ingest")

    payload = json.loads(_run(tmp_path, "answer", "owner of INC2", "--json").stdout)
    top = payload["answer"]["passages"][0]
    assert dict(top["cells"])["Ticket"] == "INC2"
    assert top["columns_matched"] == ["Owner"]
    assert (top["table"], top["row"]) == ("Tickets", 2)
    assert top["loc"] == "docs/tickets.md:L8-L8"
    assert "| INC2 | Bob |" in top["text"], "the Markdown band stays available as `text`"

    human = _run(tmp_path, "answer", "owner of INC2").stdout
    lines = human.splitlines()
    first = lines.index("Owner: Bob  <- asked")
    assert lines[first + 1 : first + 4] == ["Ticket: INC2", "Status: open", "Notes: none"]
    assert "docs/tickets.md:L8-L8" in human


def test_a_passage_that_is_not_a_row_gains_no_key(tmp_path):
    _repo(tmp_path, 1.0)
    (tmp_path / "docs" / "notes.md").write_text(
        "# Rollback\n\nTo roll back, drain the queue first.\n", encoding="utf-8"
    )
    _run(tmp_path, "ingest")
    payload = json.loads(_run(tmp_path, "answer", "roll back drain", "--json").stdout)
    top = payload["answer"]["passages"][0]
    assert top["loc"].startswith("docs/notes.md")
    assert not {"cells", "table", "row", "columns_matched"} & set(top)


def test_the_mechanism_writes_nothing_to_the_index(tmp_path):
    """L3 and SR-TUNE decision 1: `cells` exist only on fetched bytes. Ingesting
    the same table with the key off and on commits identical index bytes."""
    off, on = tmp_path / "off", tmp_path / "on"
    for root, weight in ((off, 0.0), (on, 1.0)):
        root.mkdir()
        _repo(root, weight)
        _run(root, "ingest")
    assert _index_digest(off) == _index_digest(on)
