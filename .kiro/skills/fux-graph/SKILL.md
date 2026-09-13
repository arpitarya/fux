---
name: fux-graph
description: Explore how documents in a Fux index relate with `fux explain`, `fux graph` and `fux path` — outbound links, tags, supersession, communities, query neighbourhoods and the most reliable route between two documents. Use when asked "what does this doc link to", "what links to this SR", "how are X and Y related", "what superseded this" or "orient me in this area", and when ask/find cannot answer a question about relationships.
---

# Relationships in a Fux index — `explain`, `graph`, `path`

`ask` ranks documents by the **words** they share with a question. These three
verbs answer what words cannot: **which document points at which** — a link, a
declared supersession, a shared tag, a quoted file path. **None of them ranks
by relevance**, and none of them changes what `ask` returns.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · Pick the verb

| the ask | what to do |
|---|---|
| "what does this doc link to / depend on?" | `fux explain <doc> --json` — its **outbound** edges and community |
| "what links TO this doc?" | the inbound recipe in §5 — ⚠ `explain` is outbound only |
| "orient me in this area" / "neighbourhood of X" | `fux graph "<query>" --json` — best matches plus what surrounds them |
| "how are X and Y related?" | `fux path X Y --json`, **then** `fux path Y X --json` — routes are directed |
| "what does the corpus say about X?" | `fux ask` — relevance is not this skill (`fux-search`) |
| "the answer, with line ranges" | `fux answer` — only it fetches and cites spans (`fux-answer`) |

**Start from `ask`, then walk:** find the right document, then `explain` or
`path` on the `loc` it returned.

## 2 · What an edge is — extracted at ingest, never guessed

**Every edge is something the document itself wrote.** No model runs; nothing is
inferred from titles, dates or numbering.

| `kind` | comes from | `grade` |
|---|---|---|
| `ref` | an inline Markdown link in the body, resolved to an indexed document | 10 |
| `supersedes` | frontmatter `supersedes:` — a path or a list of paths | 10 |
| `tag` | frontmatter `tags:` — a list or a comma-separated string | 10 |
| `code` | a backtick span that is **exactly** the repo-root path of an indexed file | 10 |
| `code` | a backtick span whose **basename** matches exactly one indexed file | 8 |

- **`ref` resolves relative to the linking document**; a leading `/` means the
  repo root. `#anchors` are stripped; a directory link tries `index.md`, then `README.md`.
- **`supersedes:` paths are repo-root relative.** Tags are lowercased into `tag:<name>` nodes.
- **An `http(s)` link is an edge only if that exact URL is itself indexed.**
- **A target not in the index is dropped** — a broken link is not a relationship.
- **Decoded formats (PDF, DOCX, …) have no frontmatter**, so no `tag`/`supersedes` edges.

**`grade` is the reliability ordering — branch on it, not on `kind`.** `10` is an
unambiguous resolution. `8` means *matched by basename alone* and ⚠ can point at
a same-named file elsewhere (an archived copy is the classic case) — **check it
before building a claim on it.** `6` is reserved for model-derived edges;
extraction never emits it.

## 3 · `explain` — one document's outbound edges

```json
{"doc": "file:docs/decisions/storage.md",
 "edges": [{"kind": "ref", "dst": "file:docs/runbook-rollback.md", "grade": 10},
           {"kind": "tag", "dst": "tag:storage", "grade": 10}],
 "community": "c0"}
```

| result | meaning | exit |
|---|---|---|
| `edges` non-empty | what this document points at, sorted by kind then target | 0 |
| `"edges": []` and `"community": null` | **indexed, but has no relationships** — a fact | 0 |
| `error: … is not in the index` | wrong identifier (§6), or never indexed | 1 |

**Communities** group densely inter-linked documents (label propagation over the
edges, both directions), named `c0`, `c1`, … with `c0` the largest.

- ⚠ **A label is not an identifier.** It is recomputed on every build and can
  change when unrelated documents are added. Never store or cite one.
- **One community can hold most of a well-linked corpus.** "Same community" is
  weak evidence; a direct edge or a short path is strong. No verb lists members.

## 4 · `graph` — the neighbourhood around a query

```json
{"nodes": [
  {"path": "docs/runbook-rollback.md", "id": "file:docs/runbook-rollback.md", "role": "seed", "score": 21.99},
  {"path": "docs/decisions/storage.md", "id": "file:docs/decisions/storage.md", "role": "expanded", "score": 0.0359},
  {"path": "tag:ops", "id": "tag:ops", "role": "expanded", "score": 0.0107}]}
```

1. **Seeds** — the query is ranked as `ask` ranks it; up to 5 become
   `role: "seed"`. `--scan` (default) and `--fast` (use the accelerator when
   fresh) give **identical** seeds — `--fast` is only faster.
2. **Expansion** — a short personalised random walk from the seeds over edges in
   both directions, weighted by grade; up to 10 other nodes become `"expanded"`.

- ⚠ **`score` means different things per `role`**: the ranker's score for a seed,
  walk mass (well under 1) for an expanded node. **Order within a role only.**
- **Expanded nodes can be `tag:` nodes** — labels, not files.
- **Hubs surface often** — indexes, READMEs, changelogs and logs link to
  everything. Discount an expanded hub unless the question is about it.
- `"nodes": []` (text: `No confident matches.`) means the query ranked nothing —
  re-phrase in the corpus's words (`fux-usage`).
- Sizes are `[graph] seed_depth` / `expand_limit` in `.fux/tune.toml`; `--no-tune`
  ignores that file (`fux-config`).

## 5 · `path` — how two documents connect

```json
{"from": "file:docs/decisions/storage.md", "to": "file:docs/rota-oncall.md",
 "paths": [{"hops": [
    {"kind": "ref", "src": "file:docs/decisions/storage.md", "dst": "file:docs/runbook-rollback.md", "grade": 10},
    {"kind": "ref", "src": "file:docs/runbook-rollback.md", "dst": "file:docs/rota-oncall.md", "grade": 10}],
   "reliability": 0.5}]}
```

**"Most reliable route first" is a formula:** the product of `grade / 10` over the
hops, halved for each hop beyond the first (`[graph] hop_decay`, default 0.5).
**A direct grade-10 link is `1.0`**, two grade-10 hops `0.5`, a direct grade-8
`code` edge `0.8`. Sorted descending; **at most 10 routes**.

- **Directed.** A route A→B means A pointed at B. `path B A` is a different question.
- **Simple** — no document repeats. **Tags are dead ends**: a route may end at
  `tag:x` but never passes through one, so sharing a tag is not a connection.
- **`--hops N` bounds the search; default 2** (`[cli.path] hops` in
  `.fux/output.toml`). Widen one step at a time; **3–4 is a sensible ceiling** —
  enumeration grows steeply and a large `--hops` can run for minutes.

**No path** is `"paths": []` with exit `0` (text: `No route from … within 2 hop(s).`).
**Empty is an answer** — report it; do not widen `--hops` until something appears.

**`path` refuses an end that is not in the index**, naming which one
(`… is not in the index (FROM)`, exit `1`). So an empty `paths` means the two
documents are real and unconnected — a finding, not a typo. `fux explain`
refuses an unknown `tag:` the same way.

**Inbound edges ("what links to this SR?") have no verb.** Read the derived
plane `fux build` writes, one `[src, kind, dst, grade]` per edge:

```bash
python -c '
import json, sys
p = json.load(open(".fux/runtime/graph.json", encoding="utf-8"))
assert p["schema"] == "fux.graph.v1", p["schema"]
for src, kind, dst, grade in p["edges"]:
    if dst == sys.argv[1]:
        print(kind, src, grade)
' file:docs/decisions/storage.md
```

Pass a full id — `tag:ops` lists what carries a tag. **If the assertion fails,
the recipe is out of date; say so rather than guess.** Over MCP, `fux_related`
returns inbound edges directly (`fux-mcp`).

## 6 · Which identifiers are accepted

| you pass | looked up as | works? |
|---|---|---|
| `docs/a.md` — the `loc` that `find` / `ask` printed | `file:docs/a.md` | ✅ |
| `file:docs/a.md` or `url:https://wiki.example/p` — the `id` from `ask --json` | as given | ✅ |
| `tag:ops` | as given | ✅ `explain` shows a community, no edges |
| `https://wiki.example/p` — a bare URL | `file:https://…` | ❌ prefix `url:` |
| `./docs/a.md`, an absolute path, `docs\a.md` | not normalised | ❌ |

**Copy identifiers exactly as fux printed them.**

## 7 · Preconditions, and what the output does not tell you

- **All three need the derived plane.** Without it they exit `1` with *"the graph
  lane needs the derived plane …"*. `fux build` writes only
  the gitignored `.fux/runtime/` — run it and **say that you did**.
- **The plane is not checked for currency.** After pulling commits or
  `fux ingest --no-accelerator`, run `fux build` before trusting edges.
- **Offline.** All three read the index; nothing is fetched. Parse stdout — stderr
  notes (e.g. *no fresh accelerator*) are advice, not results.
- ⚠ **No graph output carries `archived`.** Live and retired documents appear
  **unmarked**. Check a node against the `archived=true` lines in
  `.fux/sources/dirs` (URLs: `.fux/sources/urls`) or find it in `fux ask --json`,
  whose results carry `"archived": true` — then follow the `fux-archived-results` policy.
- **Supersession can exist without an edge**: an enrichment's `superseded_by:`
  marks a document superseded with no `supersedes` edge. Over MCP, `superseded`
  reports it.

## Don't

- **Don't read `explain` as "everything related"** — it is outbound only.
- **Don't trust an empty `path`** until `explain` has confirmed both ends exist.
- **Don't compare a seed's `score` with an expanded node's.**
- **Don't cite a community label**, or treat "same community" as a relationship.
- **Don't widen `--hops` to force a route** — no route is a finding.
- **Don't assume a graph node is live** — archived status is not in this output.
- **Don't build on a grade-8 edge unchecked** — basename matches can hit the wrong file.

Related skills: fux-usage, fux-search, fux-answer, fux-sources, fux-index, fux-maintain, fux-config, fux-mcp, fux-archived-results.
