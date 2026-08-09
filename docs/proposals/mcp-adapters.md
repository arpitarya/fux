---
type: Proposal
title: MCP as the adapter endgame
description: Replace per-app source adapters with the enterprise's own MCP servers — Fux stays the scorer/ledger; auth and connectivity become the org's existing infrastructure.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# MCP as the adapter endgame

**The idea.** v0.30 caps adapters at git + generic HTTP + Confluence
(council ruling). The long-game answer to "every SaaS needs an adapter" is
to not own adapters at all: enterprises increasingly expose Confluence,
SharePoint, Jira, and internal systems to agents through **MCP servers
they already run and authenticate**. Fux's fetch layer speaks one protocol
(MCP tool calls for read-by-locator), and every source the org has wired
becomes reachable — with the org's own auth, audit, and rate limits.

**Why it fits the laws.** Fux stays stdlib and $0 — MCP is JSON-RPC the
org's infrastructure serves; Fux adds a thin client, not per-app SDKs.
The devils-advocate's auth attack (every consumer needs a Confluence
token) dissolves: tokens live in the MCP server. Determinism is untouched
— fetched bytes are fetched bytes, sha-verified against the ledger.

**Sketch.** Ledger locator gains a `via: mcp:<server>/<tool>` form; the
fetch layer resolves it through a configured MCP endpoint; conformance =
"returns bytes + a version identifier". One blessed reference server
config (Confluence-via-MCP) proves the path; the built-in Confluence REST
adapter becomes the fallback for orgs without MCP.

**Graduation trigger.** First enterprise design partner with an MCP
gateway, or the moment a fourth adapter request appears (the cap holding
is the signal the endgame is needed).

**References.** Council visionary seat + DA cross-examination (WORKLOG
2026-08-09) · PLAN M5 cap · paper §2 (adjacent tools).
