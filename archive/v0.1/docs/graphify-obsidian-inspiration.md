# Inspiration scan — what to borrow from Graphify & Obsidian (and what to leave)

A concrete idea list mined from reading the Graphify source and Obsidian's model,
filtered through Fux's non-negotiable constitution (`$0`, stdlib-only,
deterministic, no maintenance-path LLM). Each idea is tagged **BORROW** (fits the
constitution), **ADAPT** (borrow the shape, drop the LLM/dep), or **LEAVE** (would
break Fux — keep it in graphify's lane).

## From Graphify

### BORROW — clean fits
1. **Versioned per-file extraction cache** (`graphify/cache.py`). AST cache keyed by
   file content **and** extractor version (`cache/ast/v{version}/`), swept on
   upgrade. Fux re-extracts everything each `build`; this is the single highest-ROI
   borrow. → *graph-scale handoff*. Pure stdlib (hashlib/json). **$0-safe.**
2. **`affected.py` incremental recompute.** BFS over dependency relations from the
   changed files to recompute only the touched subgraph + its blast radius. Maps
   perfectly onto Fux's existing `impact`. → *graph-scale handoff*.
3. **SCIP/LSIF ingestion** (`scip_ingest.py`). Consume a precomputed index from a
   real language server instead of re-parsing. Massive accuracy + scale win for big
   repos, and it's *deterministic* (reads a file). Ship behind an opt-in extra like
   `[ast]`; the index generation is the user's toolchain, not Fux's dep. → *scale*.
4. **Global cross-repo graph + manifest** (`global_graph.py`, `~/.graphify/`). A
   home-dir index of all your repos' graphs → org-scale "how does service A relate
   to service B." Deterministic merge of per-repo `graph.json`. → *org handoff*.
5. **Corrupt-file-backup discipline.** On a parse error of a user manifest, graphify
   renames to `.corrupt.<ts>` and continues rather than wiping. Good defensive
   pattern for Fux's `constitution.lock` / caches.
6. **Query log** (`~/.cache/graphify-queries.log`, JSONL, opt-out). Fux could log
   `recall`/`query`/`why` calls to measure what knowledge is actually retrieved —
   feeds `stats` and tells you which rules earn their keep. **$0.** (Privacy: local,
   opt-out, no payloads — copy graphify's stance.)

### ADAPT — borrow the shape, keep it deterministic
7. **Extra export targets** (`export.py`: SVG, GraphML, Neo4j/FalkorDB Cypher). Fux
   emits only HTML/JSON. Adding **GraphML** (Gephi/yEd) and **Cypher** is pure
   serialization of the existing `graph.json` — deterministic, no dep. Cheap parity
   win for row 9. Skip the *push* (network) unless behind an extra.
8. **DB introspection** (`pg_introspect.py`). Reconstruct schema DDL → nodes. Adapt
   as a Fux `ingest` source that drafts `regulatory`/`convention` rules from
   constraints (a NOT NULL / CHECK is literally an invariant-with-why). Behind a
   `[db]` extra; the connection is opt-in, never on `check`.
9. **Connector ingestion pattern** (`google_workspace`, `wiki`, `mcp_ingest`,
   `manifest_ingest`). Fux's schema already has `source_type: jira|confluence|github`
   — graphify shows the *shape* of a connector (fetch → normalize → extraction
   dict). Adapt into Fux's draft-review queue so nothing auto-activates. → *org*.
10. **`--mode deep` extraction dial.** Graphify trades thoroughness for cost. Fux's
    deterministic analog: a `--depth` on graph build that toggles the expensive
    `_xref` pass, so big repos can skip the noisy INFERRED edges. → *scale*.

### LEAVE — would break the constitution
11. **LLM semantic extraction** (the core of graphify's doc/PDF/image path). Needs a
    model on the extraction path. **Do not** put this in Fux's engine — it's exactly
    what the `$0` guard test forbids. If Fux ever wants richer extraction, it rides
    the *host session's* tokens via a skill (the `ingest` pattern), never engine code.
12. **Video/audio transcription** (Whisper, yt-dlp) — third-party deps + models.
    Graphify's lane.
13. **NetworkX / tree-sitter as hard deps.** Fux hand-rolls these for a reason.
    tree-sitter is already correctly fenced behind the optional `[ast]` extra — keep
    that discipline; never make it required.

## From Obsidian

Obsidian's model = **plain markdown files + `[[wikilinks]]` + a local graph view +
backlinks + tags + properties (YAML frontmatter)**. Fux already stores rules as
markdown-with-frontmatter, so the fit is natural.

### BORROW
14. **Obsidian vault export** (graphify already does this — `export.py:to_obsidian`).
    Emit `.fux/rules/` + generated views as an Obsidian-openable vault: one note per
    rule, `[[wikilinks]]` for `related`/`edges`/`governs`, YAML properties already
    present, community tags, and a non-clobbering manifest so it can write **into**
    an existing vault. This gives Fux a zero-cost, offline, *navigable* knowledge
    browser for free — and lets your rules live in your existing second brain.
    Deterministic, stdlib. **Highest-value Obsidian borrow.** → own small handoff or
    fold into *multi-assistant*.
15. **Backlinks as a first-class view.** Obsidian's killer feature is "what links
    here." Fux has `refs` (rules→file) and `related`; surfacing **rule backlinks**
    (which rules reference this rule) in `why`/`serve` is a small, deterministic add.
16. **Bidirectional `[[wikilink]]` authoring in rule bodies.** Let a rule's prose
    write `[[other-rule]]` and have `build` resolve it into a `related` edge
    (mirrors your own memory system's `[[name]]` convention). Turns freeform authoring
    into graph edges deterministically — no LLM.
17. **Local graph "neighbourhood" view.** Obsidian shows the local graph around the
    open note. Fux's viewer is whole-graph; a per-rule *ego-graph* (1–2 hops) is both
    a UX win and a **scale mitigation** (never render 23k nodes at once). → *scale*.

### LEAVE / N-A
18. **Obsidian plugins ecosystem, canvas, sync** — not Fux's job; the vault export
    (14) lets users bring their own Obsidian for all that.

## Priority shortlist (if you do five things)

1. **Per-file cache + `affected` incremental** (1,2) — kills the 23k-node pain. *scale*
2. **Obsidian vault export** (14) — huge navigability ROI, trivial + $0. *own/multi-assistant*
3. **SCIP ingest** (3) — accuracy + scale for large/polyglot repos. *scale*
4. **Global cross-repo graph** (4) — the org story. *org*
5. **GraphML + Cypher export** (7) — cheap row-9 parity so graphify's export edge disappears. *parity*

Each of these is deterministic and stdlib-or-opt-in-extra — none touches the `$0`
guarantee. The LLM-shaped ideas (11–13) are deliberately excluded; that boundary is
what keeps Fux *Fux*.
