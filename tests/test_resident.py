"""W-249 — `fux mcp` and `fux serve` hold the loaded index across calls.

[SR-MCP](../records/0136_mcp.md) decision 13. The held index is keyed on the
digest of `.fux/runtime/stamp.json` plus every shard's size and mtime, re-read
before every call. Two promises, and each has a test that can see it break:

- **a changed index is answered without a restart** — after an ingest that
  rebuilds the plane (the stamp moves), after `--no-accelerator` (the stamp
  does NOT move: the case a stamp-only key would serve stale), and with no
  `.fux/runtime/` at all (the key's stamp half is `None`);
- **an unchanged index is not re-read** — a second call, and a stamp rewritten
  with identical bytes, read no shard from disk.

The disk reads are counted by a spy on `store.reader._raw_record_lines`, the one
function every shard read goes through — never by timing.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from fux import mcp
from fux.derive import format as derive_fmt
from fux.output_config import load as load_output
from fux.serve import HOST, make_server
from fux.store import reader as reader_mod
from fux.store import read_index
from fux.store.resident import Holder, state_key
from l12_fixtures import write_config

DOCS = {
    "ranking.md": "# Ranking\n\nSaturation and length normalisation price a long "
    "document against a short one.\n\nSee [the walk](walk.md).\n",
    "walk.md": "# The walk\n\nA personalised page-rank over committed edges.\n",
}
NEW = ("okapi.md", "# Okapi\n\nThe zebrafish protocol is decided here, and nowhere else.\n")


def _ingest(root: Path, *extra: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "fux.cli", "ingest", *extra],
        cwd=root, capture_output=True, text=True, check=True,
    )


@pytest.fixture
def corpus(tmp_path) -> Path:
    """A real repository, ingested once — `.fux/pii.toml` included, or every
    verb refuses (`work/MACHINE.md` §Two test invocations)."""
    root = tmp_path / "repo"
    (root / ".fux" / "sources").mkdir(parents=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    (root / "docs").mkdir()
    for name, body in DOCS.items():
        (root / "docs" / name).write_text(body, encoding="utf-8")
    _ingest(root)
    return root


@pytest.fixture
def disk_reads(monkeypatch) -> list[str]:
    """Every shard read from disk, by file name, in order."""
    seen: list[str] = []
    real = reader_mod._raw_record_lines

    def spy(path):
        seen.append(path.name)
        return real(path)

    monkeypatch.setattr(reader_mod, "_raw_record_lines", spy)
    return seen


def _add_new_doc(root: Path) -> None:
    (root / "docs" / NEW[0]).write_text(NEW[1], encoding="utf-8")


def _edit_held_doc(root: Path) -> None:
    """Change a document whose shard is already held — a new document could
    land in a shard nothing held yet and hide a stale key."""
    with (root / "docs" / "walk.md").open("a", encoding="utf-8") as fh:
        fh.write("\nThe zebrafish protocol is decided here.\n")


def _search(root: Path, holder: Holder, query: str) -> dict:
    cfg = load_output(root, enabled=True)
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "fux_search", "arguments": {"query": query}}}
    response = mcp._handle(
        root, message, top=int(cfg.resolve_mcp("top")),
        max_headings=int(cfg.resolve_mcp("max_headings")), holder=holder,
    )
    return response["result"]["structuredContent"]


def _paths(payload: dict) -> list[str]:
    return [row["path"] for row in payload["results"]]


# --- an unchanged index is not re-read ---------------------------------------


def test_a_second_call_reads_no_shard_from_disk(corpus, disk_reads):
    holder = Holder(corpus)
    first = _search(corpus, holder, "saturation length")
    assert disk_reads, "the first call must read the shards"
    read_once = len(disk_reads)
    second = _search(corpus, holder, "saturation length")
    assert len(disk_reads) == read_once
    assert holder.loads == 1
    assert first == second


def test_a_stamp_rewritten_with_identical_bytes_does_not_reload(corpus, disk_reads):
    """`fux build` over unchanged shards writes the same stamp: nothing to load."""
    holder = Holder(corpus)
    _search(corpus, holder, "saturation length")
    read_once, loads = len(disk_reads), holder.loads
    stamp = derive_fmt.runtime_dir(corpus) / derive_fmt.STAMP_NAME
    stamp.write_bytes(stamp.read_bytes())
    _search(corpus, holder, "saturation length")
    assert (len(disk_reads), holder.loads) == (read_once, loads)


def test_a_different_stamp_reloads(corpus, disk_reads):
    holder = Holder(corpus)
    _search(corpus, holder, "saturation length")
    read_once = len(disk_reads)
    stamp = derive_fmt.runtime_dir(corpus) / derive_fmt.STAMP_NAME
    stamp.write_bytes(stamp.read_bytes().replace(b"{", b"{ ", 1))
    _search(corpus, holder, "saturation length")
    assert holder.loads == 2
    assert len(disk_reads) > read_once


# --- a changed index is answered without a restart ---------------------------


@pytest.mark.parametrize("extra", [(), ("--no-accelerator",)], ids=["ingest", "ingest-no-accelerator"])
def test_a_reingest_is_answered_by_the_next_call(corpus, extra):
    """ingest → call → re-ingest → call, one holder. `--no-accelerator` leaves
    the stamp where it was — the case a stamp-only key would serve stale."""
    holder = Holder(corpus)
    # A hit first: `fux_search` reads the records for its `sha`, so the holder
    # now holds every shard — the state a stale key would go on serving.
    assert _paths(_search(corpus, holder, "saturation length"))
    assert _paths(_search(corpus, holder, "zebrafish protocol")) == []
    assert holder.state.records is not None
    stamp_before = state_key(corpus)[0]
    _edit_held_doc(corpus)
    _ingest(corpus, *extra)
    assert (state_key(corpus)[0] == stamp_before) == bool(extra)
    assert _paths(_search(corpus, holder, "zebrafish protocol")) == ["docs/walk.md"]
    assert holder.loads == 2


def test_no_runtime_is_a_key_and_still_held(corpus, disk_reads):
    """A clone that never ran `fux build`: the stamp half is `None`, the scan
    answers, and the shards are still read once."""
    shutil.rmtree(derive_fmt.runtime_dir(corpus))
    assert state_key(corpus)[0] is None
    holder = Holder(corpus)
    first = _search(corpus, holder, "saturation length")
    assert first["ranked_by"] == "scan"
    read_once = len(disk_reads)
    assert _search(corpus, holder, "saturation length") == first
    assert len(disk_reads) == read_once
    _add_new_doc(corpus)
    _ingest(corpus, "--no-accelerator")
    assert _paths(_search(corpus, holder, "zebrafish protocol")) == ["docs/okapi.md"]


def test_the_mcp_server_answers_a_reingest_without_a_restart(corpus):
    """The whole `serve()` loop, one connection: the holder it makes is the one
    every tool call goes through."""
    asked = {"jsonrpc": "2.0", "method": "tools/call",
             "params": {"name": "fux_search", "arguments": {"query": "zebrafish protocol"}}}

    def stdin():
        yield json.dumps({**asked, "id": 1}) + "\n"
        _add_new_doc(corpus)
        _ingest(corpus)
        yield json.dumps({**asked, "id": 2}) + "\n"

    stdout = io.StringIO()
    mcp.serve(stdin=stdin(), stdout=stdout, root=corpus, enabled=True)
    first, second = (json.loads(line)["result"]["structuredContent"] for line in stdout.getvalue().splitlines())
    assert _paths(first) == []
    assert _paths(second) == ["docs/okapi.md"]


# --- the boundaries -----------------------------------------------------------


def test_outside_a_call_nothing_is_held(corpus, disk_reads):
    """A CLI verb, a test, a background job: `read_index` reads disk every time."""
    holder = Holder(corpus)
    _search(corpus, holder, "saturation length")
    before = len(disk_reads)
    read_index(corpus)
    assert len(disk_reads) > before


def test_a_held_record_map_cannot_be_reshaped_by_a_caller(corpus):
    holder = Holder(corpus)
    with holder.call():
        first = read_index(corpus)
        first.clear()
        assert read_index(corpus), "a caller emptying its dict emptied the held one"


def test_an_index_moving_during_a_call_is_not_kept(corpus, disk_reads):
    """A call that read from disk re-keys when it ends; the index moved, so the
    state it filled is dropped rather than served to the next call."""
    holder = Holder(corpus)
    with holder.call():
        read_index(corpus)
        _add_new_doc(corpus)
        _ingest(corpus)
    assert holder.state is None


# --- serve -----------------------------------------------------------------------


@pytest.fixture
def server(corpus, monkeypatch):
    monkeypatch.chdir(corpus)
    srv = make_server(port=0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{HOST}:{srv.server_address[1]}", srv
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def _get(base: str, path: str) -> dict:
    with urllib.request.urlopen(base + path, timeout=30) as response:
        return json.loads(response.read())


def test_serve_answers_a_reingest_without_a_restart(corpus, server, disk_reads):
    base, srv = server
    ask = "/ask?q=" + urllib.parse.quote("zebrafish protocol")
    assert [r["loc"] for r in _get(base, ask)["results"]] == []
    read_once = len(disk_reads)
    assert [r["loc"] for r in _get(base, ask)["results"]] == []
    assert len(disk_reads) == read_once, "the second /ask re-read the shards"
    _add_new_doc(corpus)
    _ingest(corpus)
    assert [r["loc"] for r in _get(base, ask)["results"]] == ["docs/okapi.md"]
    assert srv.state.resident.loads == 2


# --- the Node twin ---------------------------------------------------------------

NODE_ENTRY = Path(__file__).resolve().parents[1] / "node" / "fux.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_node_mcp_server_answers_a_reingest_without_a_restart(corpus):
    """`node fux.mjs mcp`, one connection: call, re-ingest under it, call."""
    proc = subprocess.Popen(
        ["node", str(NODE_ENTRY), "mcp"], cwd=corpus, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
    )

    def ask(n: int, query: str) -> list[str]:
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call", "params": {
            "name": "fux_search", "arguments": {"query": query}}}) + "\n")
        proc.stdin.flush()
        return _paths(json.loads(proc.stdout.readline())["result"]["structuredContent"])

    try:
        assert ask(1, "saturation length")
        assert ask(2, "zebrafish protocol") == []
        _edit_held_doc(corpus)
        _ingest(corpus, "--no-accelerator")
        assert ask(3, "zebrafish protocol") == ["docs/walk.md"]
    finally:
        proc.stdin.close()
        proc.wait(timeout=30)
