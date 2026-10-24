"""W-285 — the Language Server's protocol contract (SR-LSP).

Driven through `serve()` with injected byte streams, as `test_mcp.py` drives
the MCP server: the protocol is the thing worth testing. Three assertions exist
because getting them wrong hangs or kills a client rather than merely being
wrong:

- **a notification is never answered**, and a request is always answered —
  an unknown method gets `MethodNotFound`, never silence;
- **the exit code is the spec's**: `0` only after `shutdown`;
- **columns are UTF-16 code units**, so a link after an emoji is where the
  editor thinks it is.
"""

from __future__ import annotations

import io
import json

import pytest

from fux.lsp import Server, links, read_message, rel_of, serve, target_id, uri_of, write_message
from fux.output_config import OUTPUT_NAME, specimen
from fux.store import TF_FIELDS, term_hash, write_index
from l12_fixtures import write_config

BODY = TF_FIELDS.index("body")


def _rec(doc_id, title, word, *, edges=(), superseded=False, archived=False, phrases=(), mtime=None):
    tf = [0] * len(TF_FIELDS)
    tf[BODY] = 5
    flen = [0] * len(TF_FIELDS)
    flen[BODY] = 40
    record = {
        "id": doc_id, "src": "git", "loc": doc_id.removeprefix("file:"), "mode": "extracted",
        "title": title, "phrases": list(phrases), "terms": {term_hash(word): tf},
        "flen": flen, "sha": "a" * 40, "edges": list(edges),
    }
    if mtime is not None:
        record["mtime"] = mtime
    if superseded:
        record["superseded"] = True
    if archived:
        record["archived"] = True
    return record


@pytest.fixture
def repo(tmp_path):
    (tmp_path / ".fux" / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / OUTPUT_NAME).write_text(specimen(), encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "old.md").write_text("# Old\n\n## Rollback procedure\n\nrollback here\n", encoding="utf-8")
    (docs / "new.md").write_text("# New\n\nReplaces [the old one](old.md).\n", encoding="utf-8")
    (docs / "gone.md").write_text("# Gone\n", encoding="utf-8")
    (docs / "hub.md").write_text(
        "# Hub\n\n\N{GRINNING FACE} [old](old.md) and [gone](./gone.md#top)\n\n[ref]: new.md\n",
        encoding="utf-8",
    )
    write_index(tmp_path, [
        _rec("file:docs/old.md", "Old policy", "rollback", superseded=True, mtime=1788330315,
             phrases=["Rollback procedure"]),
        _rec("file:docs/new.md", "New policy", "decision",
             edges=[{"kind": "supersedes", "dst": "file:docs/old.md", "grade": 10}]),
        _rec("file:docs/gone.md", "Gone", "history", archived=True),
        _rec("file:docs/hub.md", "Hub", "index", edges=[
            {"kind": "ref", "dst": "file:docs/old.md", "grade": 10},
            {"kind": "ref", "dst": "file:docs/gone.md", "grade": 10},
            {"kind": "ref", "dst": "file:docs/new.md", "grade": 10},
        ]),
    ])
    write_config(tmp_path)
    return tmp_path


def _frame(*messages) -> io.BytesIO:
    out = io.BytesIO()
    for m in messages:
        write_message(out, m)
    out.seek(0)
    return out


def _session(repo, *messages) -> tuple[int, list[dict]]:
    stdout = io.BytesIO()
    code = serve(stdin=_frame(*messages), stdout=stdout, root=repo, enabled=True)
    stdout.seek(0)
    replies = []
    while (message := read_message(stdout)) is not None:
        replies.append(message)
    return code, replies


def _server(repo) -> Server:
    server = Server(repo, top=5)
    server.handle({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})
    return server


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
SHUTDOWN = {"jsonrpc": "2.0", "id": 9, "method": "shutdown"}
EXIT = {"jsonrpc": "2.0", "method": "exit"}


def test_framing_round_trips_non_ascii():
    stream = _frame({"jsonrpc": "2.0", "id": 1, "result": "caf\N{LATIN SMALL LETTER E WITH ACUTE}"})
    raw = stream.getvalue()
    header, _, body = raw.partition(b"\r\n\r\n")
    assert header == f"Content-Length: {len(body)}".encode()
    assert read_message(io.BytesIO(raw))["result"] == "caf\N{LATIN SMALL LETTER E WITH ACUTE}"


def test_initialize_announces_the_four_features(repo):
    code, replies = _session(repo, INIT, SHUTDOWN, EXIT)
    caps = replies[0]["result"]["capabilities"]
    assert caps["hoverProvider"] and caps["referencesProvider"] and caps["workspaceSymbolProvider"]
    assert caps["textDocumentSync"]["change"] == 1
    assert caps["positionEncoding"] == "utf-16"
    assert replies[0]["result"]["serverInfo"]["name"] == "fux"
    assert code == 0


def test_exit_without_shutdown_is_code_one(repo):
    code, _ = _session(repo, INIT, EXIT)
    assert code == 1


def test_a_request_before_initialize_is_refused(repo):
    _, replies = _session(repo, {"jsonrpc": "2.0", "id": 3, "method": "workspace/symbol", "params": {"query": "x"}})
    assert replies[0]["error"]["code"] == -32002


def test_an_unknown_request_is_answered_and_a_notification_is_not(repo):
    _, replies = _session(
        repo, INIT,
        {"jsonrpc": "2.0", "method": "initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 4, "method": "textDocument/completion", "params": {}},
    )
    assert [r.get("id") for r in replies] == [1, 4]
    assert replies[1]["error"]["code"] == -32601


def test_workspace_symbol_is_a_ranked_search_at_the_matching_heading(repo):
    result = _server(repo).symbols({"query": "rollback"})
    assert [s["containerName"] for s in result] == ["docs/old.md"]
    assert result[0]["name"] == "Old policy"
    assert result[0]["location"]["range"]["start"]["line"] == 2
    assert result[0]["location"]["uri"] == uri_of(repo, "docs/old.md")


def test_an_empty_symbol_query_returns_nothing(repo):
    assert _server(repo).symbols({"query": "  "}) == []


def test_diagnostics_warn_on_superseded_and_archived_links_in_utf16_columns(repo):
    server = _server(repo)
    uri = uri_of(repo, "docs/hub.md")
    text = (repo / "docs" / "hub.md").read_text(encoding="utf-8")
    server.handle({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                   "params": {"textDocument": {"uri": uri, "text": text}}})
    published = server.outbox[-1]["params"]
    assert published["uri"] == uri
    by_message = {d["message"]: d for d in published["diagnostics"]}
    superseded = by_message["links to a superseded document: docs/old.md — superseded by docs/new.md"]
    # The emoji is ONE code point and TWO UTF-16 units, so the link starts at 3.
    assert superseded["range"]["start"] == {"line": 2, "character": 3}
    assert "links to an archived document: docs/gone.md" in by_message
    assert all(d["severity"] == 2 for d in published["diagnostics"])


def test_diagnostics_follow_the_unsaved_buffer(repo):
    server = _server(repo)
    uri = uri_of(repo, "docs/hub.md")
    server.handle({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                   "params": {"textDocument": {"uri": uri, "text": "[old](old.md)\n"}}})
    assert len(server.outbox[-1]["params"]["diagnostics"]) == 1
    server.handle({"jsonrpc": "2.0", "method": "textDocument/didChange",
                   "params": {"textDocument": {"uri": uri}, "contentChanges": [{"text": "nothing\n"}]}})
    assert server.outbox[-1]["params"]["diagnostics"] == []
    server.handle({"jsonrpc": "2.0", "method": "textDocument/didClose", "params": {"textDocument": {"uri": uri}}})
    assert server.outbox[-1]["params"]["diagnostics"] == []
    assert uri not in server.documents


def test_a_superseded_document_says_so_about_itself(repo):
    server = _server(repo)
    assert server.diagnostics(uri_of(repo, "docs/old.md"))[0]["severity"] == 3


def test_hover_on_a_link_describes_its_target(repo):
    server = _server(repo)
    reply = server.hover({"textDocument": {"uri": uri_of(repo, "docs/new.md")},
                          "position": {"line": 2, "character": 14}})
    value = reply["contents"]["value"]
    assert "**Old policy**" in value
    assert "superseded by `docs/new.md`" in value
    assert "committed 2026-" in value
    assert "2 linking here" in value


def test_hover_off_a_link_is_null(repo):
    server = _server(repo)
    assert server.hover({"textDocument": {"uri": uri_of(repo, "docs/new.md")},
                         "position": {"line": 0, "character": 1}}) is None


def test_references_are_backlinks_at_the_linking_line(repo):
    server = _server(repo)
    refs = server.references({"textDocument": {"uri": uri_of(repo, "docs/old.md")},
                              "position": {"line": 0, "character": 0}})
    spots = sorted((r["uri"], r["range"]["start"]["line"]) for r in refs)
    assert spots == [(uri_of(repo, "docs/hub.md"), 2), (uri_of(repo, "docs/new.md"), 2)]


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        ("docs/a.md", "b.md", "file:docs/b.md"),
        ("docs/a.md", "../README.md#x", "file:README.md"),
        ("docs/a.md", "/records/x.md", "file:records/x.md"),
        ("docs/a.md", "#only-an-anchor", None),
        ("docs/a.md", "../../outside.md", None),
        ("docs/a.md", "mailto:x@y.z", None),
        ("docs/a.md", "https://example.com/p", "url:https://example.com/p"),
        ("docs/a.md", "my%20file.md", "file:docs/my file.md"),
    ],
)
def test_target_id(source, target, expected):
    assert target_id(source, target) == expected


def test_links_finds_inline_and_reference_definitions():
    found = [(line, t) for line, _s, _e, t in links('[a](x.md "t") and [b](<y.md>)\n[c]: w.md\n')]
    assert found == [(0, "x.md"), (0, "y.md"), (1, "w.md")]


def test_rel_of_refuses_a_uri_outside_the_repo(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere") / "x.md"
    assert rel_of(repo, outside.as_uri()) is None
    assert rel_of(repo, "untitled:Untitled-1") is None
    assert rel_of(repo, uri_of(repo, "docs/old.md")) == "docs/old.md"


def test_a_malformed_body_is_a_parse_error_and_the_server_continues(repo):
    stdin = io.BytesIO(b"Content-Length: 3\r\n\r\n{x}" + _frame(INIT, SHUTDOWN, EXIT).getvalue())
    stdout = io.BytesIO()
    assert serve(stdin=stdin, stdout=stdout, root=repo, enabled=True) == 0
    stdout.seek(0)
    first = read_message(stdout)
    assert first["error"]["code"] == -32700
    assert json.dumps(read_message(stdout)["result"]["serverInfo"])
