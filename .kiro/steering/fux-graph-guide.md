---
inclusion: auto
name: fux-graph-guide
description: Relationships between documents in the Fux index with fux explain, fux graph and fux path - outbound links, tags, supersession, neighbourhoods and routes. Use when asked what links to a doc, how two docs are related, or to orient in an area.
---

# Relationships with fux explain / graph / path

- **`explain` is outbound only**; there is no verb for inbound links.
- **`path` is directed** - try both orders. An empty `paths` is a finding, but
  **confirm both ends exist with `explain` first**: `path` does not check.
- **Branch on `grade`**: 10 is unambiguous, 8 is a basename match that can hit
  the wrong file.
- Seed and expanded `score`s in `graph` are different quantities.
- **Graph output carries no `archived` flag** - check a node before citing it.
- All three need `fux build` first.

Full procedure: the `fux-graph` skill.
