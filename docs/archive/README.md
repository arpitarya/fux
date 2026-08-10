# `docs/archive/` — completed doc artifacts

Handoffs, prompts and proposals live here **once they are fully implemented
and their ADR is written** (CLAUDE.md's archive law). Each carries
`status: implemented` and a link to the ADR that closed it, and is named by
the release version it shipped — `vX.Y.Z-name.md`, not its in-flight index.

Active directories (`handoff/`, `proposals/`) hold *live* work only, so
"what's in flight" is answerable by listing them.

| artifact | shipped | closed by |
|---|---|---|
| [`v0.31.0-fux-dir-layout-handoff.md`](v0.31.0-fux-dir-layout-handoff.md) · [prompt](v0.31.0-fux-dir-layout-prompt.md) | 2026-08-11 | [ADR-0011](../adr/0011-fux-dir-layout.md) — the `.fux/` layout + URL-source relocation |

## Not here: the v0.26 doc set

Two different archives share the word, and the distinction matters:

- **`docs/archive/`** (this directory) — completed *doc artifacts* of the
  current v0.30 build.
- **[`archive/v0.26-docs/`](../../archive/v0.26-docs/)** (repo root, **not**
  under `docs/`) — the frozen v0.19–0.26 documentation set. Frozen means never
  edited; its ADRs are always cited as **"archived ADR-NNNN"** with the path.
- **[`archive/v0.26/`](../../archive/v0.26/)** (repo root) — the previous
  *engine*: runnable, reference-only, never modified, never imported.
- **[`archive/v0.26-implemented/`](../../archive/v0.26-implemented/)** — that
  build's implemented artifacts, including `PLAN-v0.26.md`.

That the v0.26 doc set sits at the repo root rather than under `docs/` is the
reset discrepancy DOC-REGISTRY records; resolving it is Arpit's call, not an
agent's. CLAUDE.md's Layout section still describes the intended placement.
