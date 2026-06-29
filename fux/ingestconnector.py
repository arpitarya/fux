"""Connector ingestion guardrail — Jira/Confluence/GitHub via MCP/API (handoff §7).

The **agent** pulls structured, server-side-filtered data through the existing MCP
connectors / APIs (the fallback ladder — MCP → REST+PAT → export/`git clone` →
CDP-JSON → DOM — lives in the ingest skill); **fux never builds a client or calls an
API.** This module is only the deterministic, `$0` fence: a connector pull is bounded
by construction — an explicit query is **mandatory** (refuse the firehose), the item
count is capped, and every drafted item is **low-trust** (a ticket/wiki/PR is candidate
signal, not a spec), so it lands in the review queue as a candidate, never auto-active.
"""
from __future__ import annotations

from dataclasses import dataclass

CONNECTORS = ("github", "jira", "confluence")
DEFAULT_MAX = 50
TRUST = "candidate"                       # low by construction — review-queue candidate
# The abuse surface is an unbounded "everything" pull — refuse it (handoff §7 bounds).
_UNBOUNDED = {"", "*", "all", "everything", "any", "%", ".*", "*.*"}


class ConnectorError(ValueError):
    """A connector request that breaks the bounds (unknown connector / unbounded query)."""


@dataclass
class Plan:
    connector: str
    query: str
    since: str | None
    max_items: int
    trust: str = TRUST

    def describe(self) -> str:
        win = f", since {self.since}" if self.since else ""
        return (f"connector {self.connector}: query {self.query!r}{win}, ≤{self.max_items} "
                f"items, trust={self.trust} (low — review-queue candidates, never auto-active)")


def _is_unbounded(query: str) -> bool:
    """True for an empty / wildcard-only filter — the firehose we refuse."""
    q = " ".join(query.lower().split())
    return q in _UNBOUNDED or (bool(q) and all(tok in _UNBOUNDED for tok in q.split()))


def plan(connector: str, query: str | None, since: str | None = None,
         max_items: int = DEFAULT_MAX) -> Plan:
    """Validate + normalize a connector request. Raises ConnectorError if unbounded."""
    if connector not in CONNECTORS:
        raise ConnectorError(f"unknown connector {connector!r}; choose from {CONNECTORS}")
    if query is None or _is_unbounded(query):
        raise ConnectorError(
            f"refusing an unbounded {connector} pull — an explicit server-side filter is "
            "MANDATORY (Jira JQL / GitHub query / Confluence space-or-page; never "
            "'everything'). Tokens you never fetch cost nothing (handoff §7).")
    if max_items < 1:
        raise ConnectorError("--max must be ≥ 1")
    return Plan(connector=connector, query=query.strip(), since=since, max_items=max_items)
