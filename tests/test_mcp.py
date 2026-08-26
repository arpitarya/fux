"""W-76 Phase 5 — the MCP server's protocol contract.

Driven through `serve()` with injected streams rather than a subprocess: the
protocol is the thing worth testing, and a pipe adds only flakiness. Two of
these assertions exist because getting them wrong is fatal to a host rather
than merely wrong:

- **a notification must not be answered.** `notifications/initialized` arrives
  on every connection and carries no `id`; replying to it is a protocol error
  some hosts treat as fatal.
- **a tool failure is reported inside the result**, with `isError`, not as a
  JSON-RPC error. The agent should see a tool that answered "no" — something
  it can act on — rather than a transport fault, which it usually cannot.
"""

from __future__ import annotations

import io
import json

import pytest

from fux.derive import build
from fux.mcp import PROTOCOL_VERSION, TOOLS, serve
from fux.store import TF_FIELDS, term_hash, write_index

BODY = TF_FIELDS.index("body")


def _rec(doc_id, title, word, *, edges=(), superseded=False, phrases=()) -> dict:
    tf = [0] * len(TF_FIELDS)
    tf[BODY] = 5
    flen = [0] * len(TF_FIELDS)
    flen[BODY] = 40
    record = {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": list(phrases),
        "terms": {term_hash(word): tf},
        "flen": flen,
        "sha": "a" * 40,
        "edges": list(edges),
    }
    if superseded:
        record["superseded"] = True
    return record


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "retry.md").write_text(
        "# Retry\n\nline three\nline four\nline five\n", encoding="utf-8"
    )
    write_index(
        tmp_path,
        [
            # `superseded` is stamped by `ingest.run`, which `write_index`
            # does not go through -- so a hand-built record carries the flag
            # explicitly. The edge below is what a real ingest would derive it
            # FROM; both are present here so the fixture matches what the
            # pipeline actually produces.
            _rec(
                "file:docs/retry.md",
                "Retry policy",
                "rollback",
                superseded=True,
                # W-84: the headings a real ingest would have extracted. One
                # matches the query the tests use, one does not, so the
                # filtering is visible rather than assumed.
                phrases=["Backoff", "Rollback procedure"],
            ),
            _rec(
                "file:docs/new.md",
                "New decision",
                "rollback",
                edges=[{"kind": "supersedes", "dst": "file:docs/retry.md", "grade": 10}],
                phrases=["Scope"],
            ),
        ],
    )
    build(tmp_path)
    return tmp_path


def _exchange(repo, *messages) -> list[dict]:
    stdin = io.StringIO("\n".join(json.dumps(m) for m in messages) + "\n")
    stdout = io.StringIO()
    serve(stdin=stdin, stdout=stdout, root=repo)
    return [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]


def _call(repo, name, arguments):
    (response,) = _exchange(
        repo, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": arguments}}
    )
    return response["result"]


def test_initialize_announces_the_protocol_and_the_tools_capability(repo):
    (response,) = _exchange(repo, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    result = response["result"]
    assert result["protocolVersion"] == PROTOCOL_VERSION
    assert "tools" in result["capabilities"]
    assert result["serverInfo"]["name"] == "fux"


def test_a_notification_is_never_answered(repo):
    """No `id` means no reply. Answering is a protocol error, not a nicety."""
    responses = _exchange(
        repo,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 7, "method": "tools/list"},
    )
    assert len(responses) == 1, "the notification drew a reply"
    assert responses[0]["id"] == 7


def test_tools_list_matches_the_declared_surface(repo):
    (response,) = _exchange(repo, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = [t["name"] for t in response["result"]["tools"]]
    assert names == [t["name"] for t in TOOLS]
    assert "fux_answer" not in names, (
        "`answer` is deliberately not exposed: the agent IS the answerer"
    )


def test_every_tool_declares_a_usable_schema():
    for tool in TOOLS:
        assert tool["description"].strip(), f"{tool['name']} has no description"
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        for required in schema.get("required", []):
            assert required in schema["properties"], (
                f"{tool['name']} requires {required!r} but does not declare it"
            )


def test_search_returns_the_sha_the_ranking_used(repo):
    payload = _call(repo, "fux_search", {"query": "rollback", "k": 5})["structuredContent"]
    assert payload["results"], "no results"
    for row in payload["results"]:
        assert row["sha"], "an agent cannot verify a result with no sha"
        assert "path" in row and "score" in row


def test_search_surfaces_the_supersession_flag(repo):
    payload = _call(repo, "fux_search", {"query": "rollback", "k": 5})["structuredContent"]
    flags = {r["path"]: r["superseded"] for r in payload["results"]}
    assert flags.get("docs/retry.md") is True
    assert flags.get("docs/new.md") is False


def test_search_carries_the_matching_headings(repo):
    """W-84 — section-level, and only the sections the query asked about.

    `fux_search` stays document-level (no fetch, no chunking, no line
    arithmetic); this narrows *where in the document* to look, which is the
    decision an agent makes before it spends a `fux_passage` call.
    """
    payload = _call(repo, "fux_search", {"query": "rollback", "k": 5})["structuredContent"]
    headings = {r["path"]: r["headings"] for r in payload["results"]}
    assert headings["docs/retry.md"] == ["Rollback procedure"], "`Backoff` does not match"
    assert headings["docs/new.md"] == [], "present and empty — an absent key is a trap"


def test_search_does_not_claim_line_ranges_it_never_returns(repo):
    """The tool description said *"line-range citations"* until 2026-08-26 and
    `_search` has never returned one. An agent reads this string and acts on
    it, so a false claim here is worse than a false one in a doc."""
    (search,) = [t for t in TOOLS if t["name"] == "fux_search"]
    assert "line-range" not in search["description"]
    payload = _call(repo, "fux_search", {"query": "rollback", "k": 5})["structuredContent"]
    for row in payload["results"]:
        assert ":L" not in row["path"], "a search hit is a document, not a span"


def test_passage_returns_exactly_the_requested_lines(repo):
    payload = _call(
        repo, "fux_passage", {"path": "docs/retry.md", "line_start": 3, "line_end": 4}
    )["structuredContent"]
    assert payload["text"] == "line three\nline four"
    assert payload["line_start"] == 3 and payload["line_end"] == 4
    assert len(payload["sha"]) == 40


def test_passage_clamps_a_range_past_the_end(repo):
    payload = _call(
        repo, "fux_passage", {"path": "docs/retry.md", "line_start": 1, "line_end": 9999}
    )["structuredContent"]
    assert payload["line_end"] == 5, "a range past the end must clamp, not raise"


@pytest.mark.parametrize(
    "escape", ["../../../etc/passwd", "docs/../../outside.md", "/etc/passwd"]
)
def test_passage_refuses_to_escape_the_repository(repo, escape):
    """`resolve()` collapses `..` BEFORE the check, so a traversal cannot slip
    through by being spelled differently."""
    result = _call(repo, "fux_passage", {"path": escape})
    assert result["isError"] is True
    assert "outside" in result["content"][0]["text"] or "not a file" in result["content"][0]["text"]


def test_related_reports_both_directions(repo):
    payload = _call(repo, "fux_related", {"path": "docs/retry.md"})["structuredContent"]
    assert payload["superseded"] is True
    assert payload["inbound"] == [{"path": "docs/new.md", "kind": "supersedes"}]


def test_a_tool_failure_is_a_result_not_a_transport_error(repo):
    result = _call(repo, "fux_related", {"path": "docs/nope.md"})
    assert result["isError"] is True
    assert "content" in result, "a tool failure must still return content the agent can read"


def test_an_unknown_tool_is_a_jsonrpc_error(repo):
    """This one IS a protocol fault: the agent called something that does not exist."""
    (response,) = _exchange(
        repo,
        {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "nope", "arguments": {}}},
    )
    assert response["error"]["code"] == -32602


def test_malformed_json_does_not_kill_the_server(repo):
    stdin = io.StringIO('not json\n{"jsonrpc":"2.0","id":4,"method":"tools/list"}\n')
    stdout = io.StringIO()
    serve(stdin=stdin, stdout=stdout, root=repo)
    responses = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    assert responses[0]["error"]["code"] == -32700
    assert responses[1]["id"] == 4, "the server must keep serving after a parse error"
