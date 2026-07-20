"""Minimal MCP stdio server — JSON-RPC handshake, tools/list, tools/call ($0)."""
from __future__ import annotations

import io
import json

from fux import mcpserver
from conftest import write_rule

RULE = """---
id: day-pnl
domain: portfolio
type: rule
status: active
created: 2026-06-01
updated: 2026-06-01
---
**Rule:** Today's P&L uses current INR value. **Why:** relative to yesterday.
"""


def test_initialize_advertises_protocol_and_tools():
    init = mcpserver._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init["result"]["protocolVersion"] == mcpserver.PROTOCOL
    tools = mcpserver._handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in tools["result"]["tools"]}
    assert {"fux_recall", "fux_why", "fux_refs", "fux_savings", "fux_stats"} <= names


def test_notification_initialized_has_no_reply():
    assert mcpserver._handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_tools_call_recall_returns_text(project):
    write_rule(project, "day-pnl", RULE)
    msg = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
           "params": {"name": "fux_recall", "arguments": {"query": "day pnl"}}}
    out = mcpserver._handle(msg)
    text = out["result"]["content"][0]["text"]
    assert "day-pnl" in text and not out["result"].get("isError")


def test_unknown_tool_is_reported_as_tool_error(project):
    msg = {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
           "params": {"name": "nope", "arguments": {}}}
    out = mcpserver._handle(msg)
    assert out["result"]["isError"] and "error" in out["result"]["content"][0]["text"]


def test_serve_loop_over_stdio(project):
    write_rule(project, "day-pnl", RULE)
    inp = io.StringIO("\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "fux_coverage", "arguments": {}}}),
    ]) + "\n")
    out = io.StringIO()
    mcpserver.serve(stdin=inp, stdout=out)
    replies = [json.loads(l) for l in out.getvalue().splitlines() if l.strip()]
    assert len(replies) == 2 and replies[0]["result"]["serverInfo"]["name"] == "fux"
