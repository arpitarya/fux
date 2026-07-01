"""Connector ingestion guardrail — Jira/Confluence/GitHub (batch-ingest-handoff §7).

The engine never fetches; it only bounds the request: an explicit server-side filter
is mandatory (refuse the firehose), the count is capped, and items are low-trust.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from fux import cliquery, ingestconnector
from fux.errors import FuxError


def test_plan_accepts_a_bounded_query():
    pl = ingestconnector.plan("github", "repo:me/app is:pr label:adr", max_items=30)
    assert pl.connector == "github" and pl.max_items == 30
    assert pl.trust == "candidate"               # low by construction
    assert "candidate" in pl.describe() and "≤30" in pl.describe()


@pytest.mark.parametrize("q", ["", "   ", "*", "all", "everything", "*.*", ".*"])
def test_plan_refuses_an_unbounded_query(q):
    with pytest.raises(ingestconnector.ConnectorError):
        ingestconnector.plan("jira", q)


def test_plan_requires_a_query():
    with pytest.raises(ingestconnector.ConnectorError):
        ingestconnector.plan("confluence", None)


def test_plan_rejects_unknown_connector_and_bad_max():
    with pytest.raises(ingestconnector.ConnectorError):
        ingestconnector.plan("slack", "x")
    with pytest.raises(ingestconnector.ConnectorError):
        ingestconnector.plan("github", "x", max_items=0)


def test_since_cursor_is_carried():
    pl = ingestconnector.plan("jira", "project = ACME AND type = Story", since="2026-06-01")
    assert pl.since == "2026-06-01" and "since 2026-06-01" in pl.describe()


def _args(**kw):
    base = dict(targets=[], queue=False, recheck=False, connector=None, query=None,
                since=None, max=20)
    base.update(kw)
    return SimpleNamespace(**base)


def test_cli_connector_branch(capsys):
    assert cliquery.cmd_ingest(_args(connector="github", query="repo:me/app is:pr")) == 0
    assert "connector github" in capsys.readouterr().out
    # An unbounded connector query is a usage error → FuxError (terse `error:`
    # on stderr, exit 1 at the CLI boundary), not a stdout print + return 1.
    with pytest.raises(FuxError, match="refusing an unbounded"):
        cliquery.cmd_ingest(_args(connector="jira", query="*"))
