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
from fux.output_config import OUTPUT_NAME, specimen
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
    # `serve()` now loads `.fux/output.toml` at start (it must be in effect
    # and cover [mcp] `top`, per output_config's no-fallback rule) — this
    # fixture never goes through `fux setup`, so it writes a live specimen
    # itself, exactly what `fux setup` would have produced.
    (tmp_path / ".fux").mkdir()
    (tmp_path / OUTPUT_NAME).write_text(specimen(), encoding="utf-8")
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


# --------------------------------------------------------------------------
# W-91 fork E — the tool descriptions are the only docs with a MACHINE audience
# and were the only docs with no test. W-84's finding, closed here.


def _tool(name: str) -> dict:
    from fux.mcp import TOOLS

    return next(t for t in TOOLS if t["name"] == name)


def test_the_advertised_default_is_the_engine_s_default():
    """⚠ **This shipped WRONG for about an hour on 2026-08-27.**

    `k` advertised a hand-written `default: 5`; `[mcp] top` then made the
    engine use whatever the repo configured, and the schema kept saying 5.
    Nothing failed — an MCP tool schema is a machine-facing declaration that
    no gate read, which is exactly W-84's class in the one surface whose
    reader is ALWAYS a machine.
    """
    from fux.output_config import BUILT_IN

    k = _tool("fux_search")["inputSchema"]["properties"]["k"]
    assert k["default"] == BUILT_IN["top"]
    assert str(BUILT_IN["top"]) in k["description"]


def test_the_advertised_default_says_a_repo_can_change_it():
    """Advertising a number that a config silently overrides is worse than
    advertising none — the agent believes the number."""
    from fux.output_config import OUTPUT_NAME

    k = _tool("fux_search")["inputSchema"]["properties"]["k"]
    assert OUTPUT_NAME in k["description"]
    assert "[mcp]" in k["description"]


def test_every_band_the_description_names_actually_exists():
    """The description tells an agent how to branch on `confidence.band`.

    A band renamed in `confidence.py` would leave this prose instructing an
    agent to look for a value that can never appear.
    """
    from fux.query.confidence import BANDS

    text = _tool("fux_search")["description"]
    named = {b for b in BANDS if f"'{b}'" in text or f"`{b}`" in text}
    assert named, "the description branches on bands but names none"
    for band in named:
        assert band in BANDS


def test_the_description_names_the_fields_it_tells_an_agent_to_read():
    """`answerable`, `band` and `missing` are instructions to read specific
    keys. If a key is renamed, this prose sends the agent to a field that is
    not there — silently, because prose does not fail."""
    from fux.query.confidence import Confidence

    text = _tool("fux_search")["description"]
    shape = Confidence(0.0, 0.0, 0, "unverified", ()).as_dict()
    for field in ("answerable", "band", "missing"):
        assert field in text, f"the description no longer mentions {field}"
        assert field in shape, f"the description names {field}, which the block lacks"


def test_the_confidence_block_the_description_promises_is_unconditional_here():
    """⚠ ADR-CONFIDENCE decision 11 gates the block behind `--band` on the CLI
    and leaves it ALWAYS ON over MCP. The description says *read the confidence
    block* with no caveat, and that is only honest while MCP stays ungated."""
    from fux.output_config import MCP_KEYS

    assert "band" not in MCP_KEYS, (
        "[mcp] band would let a config remove the block this description "
        "unconditionally promises"
    )


def test_every_tool_has_a_handler_and_every_handler_a_tool():
    """A tool advertised with no handler is a guaranteed runtime error an agent
    discovers by calling it; a handler with no tool is unreachable code."""
    from fux import mcp as mcp_mod
    from fux.mcp import TOOLS

    advertised = {t["name"] for t in TOOLS}
    handlers = {
        f"fux_{n}" for n in ("search", "passage", "related") if hasattr(mcp_mod, f"_{n}")
    }
    assert advertised == handlers, f"advertised={sorted(advertised)} handlers={sorted(handlers)}"


def test_the_surface_stays_three_tools():
    """ADR-MCP capped it deliberately — `answer` is absent because the agent is
    the answerer. A fourth tool is a decision, not a convenience, so it should
    cost a failing test and a record edit."""
    from fux.mcp import TOOLS

    assert len(TOOLS) == 3, [t["name"] for t in TOOLS]


def test_every_tool_declares_a_description_and_a_schema():
    from fux.mcp import TOOLS

    for tool in TOOLS:
        assert tool.get("description", "").strip(), f"{tool['name']} has no description"
        assert tool.get("inputSchema", {}).get("required"), f"{tool['name']} declares no required input"
