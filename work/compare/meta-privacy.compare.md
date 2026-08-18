---
type: Compare Doc
title: Meta Privacy
description: The committed index leaks summaries of access-controlled documents — plain vs hashed-default vs hashed-only meta.
status: accepted
timestamp: 2026-08-09T00:00:00Z
---

# Index meta privacy — Comparison

> **Verdict: Hashed by default for every non-git source; plain requires
> explicit per-source config** (`meta = hashed | plain` on the ledger
> entry). Enforced at write time in M3, not by documentation.
> **Status:** ✅ accepted — council 2026-08-09 (devils-advocate's strongest
> attack) · **Confidence:** high · **Reopen when:** an enterprise partner
> requires plaintext meta *and* proves repo-ACL ⊇ source-ACL, or hashed
> mode's degraded `explain` labels measurably block adoption.

## Context

A KL top-128 term list plus YAKE phrases is a decent *summary* of a
confidential Confluence page — sitting in every clone, in git history,
forever, readable by repo-cloners who lack Confluence access. Repo ACL
would silently become the union of all source ACLs. Term *hashes* mitigate
(postings/dictionary already store blake2b64 only) but common-word hashes
are dictionary-attackable, and `M/` titles/phrases were plaintext in v1.

## Options

- **A — Hashed by default, plain opt-in** *(verdict)*: external sources
  commit only hashes (query-able — queries hash their terms too — but not
  human-readable); git-dir sources default plain (cloners already have the
  content); `explain`/graph labels degrade to doc titles-from-fetch for
  hashed sources.
- **B — Plain everywhere**: best UX; unacceptable cross-ACL leak (git
  history makes it permanent).
- **C — Hashed everywhere**: max safety; needlessly lobotomizes labels for
  repo docs whose content every cloner can read anyway.

## Matrix

| criterion (weight) | A default-hashed | B plain | C all-hashed |
|---|---|---|---|
| cross-ACL leak (H) | **contained** | permanent | contained |
| ranking quality (H) | unchanged (hashes rank fine) | unchanged | unchanged |
| explain/graph labels (M) | degraded for external only | full | degraded everywhere |
| dictionary-attack residue (M) | hashes only; phrases absent | n/a | hashes only |
| enterprise review story (H) | **defensible** | fails | defensible, overkill |

## Consequences

`M/` stores per-source either plaintext or hash-only records; fetch-time
titles backfill display for hashed sources (cached in ARC, never
committed). Security section in the eventual ADR-0019 cites this doc.
Residual risk stated honestly: hashed terms remain vulnerable to
dictionary attack for common vocabulary — the leak is reduced to term-set
membership, not eliminated; sources needing zero index presence use
`mode = skip` (don't index), which M3 must also support.

## References

Paper §3.1, §9 · council transcript (WORKLOG 2026-08-09) · blake2b (stdlib)
· the `mode/meta` policy fields in PLAN M2–M3.

## Reopen-trigger

See verdict block.
