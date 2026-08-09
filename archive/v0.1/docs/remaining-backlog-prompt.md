# Fux — Remaining Backlog: One-Shot Driver Prompt

Paste into Claude Code in the `fux` repo. Full spec + per-item detail: `docs/remaining-backlog-handoff.md`.

```
Work the pending Fux backlog per docs/remaining-backlog-handoff.md. Each item is its OWN PR — do NOT
bundle them into one commit. Go in priority order; STOP after each PR for my review before starting the
next.

FIRST — verify, don't assume. Check the repo for what's already shipped before building anything:
- git log; presence of selfbuild.py, decisioncapture.py; whether `ingest` already supports multi-source +
  --follow-links + json/yaml/swagger; whether `--self` exists on query/explain/path.
- Report a one-line status for each of the 6 items (DONE / PARTIAL / PENDING) and which you'll build.

HARD CONSTRAINTS (every PR): $0/stdlib/deterministic maintenance path; agent fetches/parses/debates, fux
governs; engine imports no network/LLM/parser/OCR library (guard test); money NEVER flows through fux
(ADR 0001 — fux/docs/decisions/0001-fux-elgar-relationship.md); files ≤100 lines; docs in the same change;
each PR goes through the wall (branch → PR → fux gate + ai-review green → merge).

THEN build the PENDING ones, each as its own PR, in this order (use the linked detailed handoff as the
spec for each — read it before implementing):

1. SELF-BUILD + --self  (spec: docs/scrape-howto-cli-handoff.md §C)
   selfbuild.py: AST-extract fux's own fux/*.py + .fux/rules + docs → bundled data/self/ ($0, in the wheel);
   add --self scope to query/explain/path/recall + the `how` corpus; works in any repo with no project
   .fux/. Test: bundle regenerates byte-identically from source.

2. DECISION CAPTURE  (spec: docs/decision-capture-handoff.md)
   decisioncapture.py: on /fux debate or council conclusion, write a tamper-evident ADR (debate_hash +
   content_seal) routed by content — world/code→fux, app→anton, money→ELGAR (fux keeps only
   elgar://decision/<id>, never the body; confirm mandatory for money). check.py verifies the seal + the
   money-firewall guard.

3. BATCH + LINKED-DOCS (PR3)  (spec: docs/batch-ingest-handoff.md)  — VERIFY first; ingestqueue/ingestreduce
   may already cover part. Finish: multi-source + globs → draft review queue; --follow-links (depth-1,
   same-origin, capped, allow-list, list-and-confirm); json/yaml/swagger (Swagger → per-endpoint rules +
   --recheck contract drift).

4. CONNECTOR INGESTION (PR4)  (spec: docs/batch-ingest-handoff.md §7)
   Jira/Confluence/GitHub via MCP/API, server-side filtered (JQL/query/since-cursor), low-trust queue items,
   mandatory explicit query (refuse "everything"). Fallback ladder: MCP → REST+PAT → export/git clone →
   CDP-via-session(JSON not DOM) → DOM scrape (last resort). GitHub first.

5. ENFORCEMENT PII-CONTENT GATE PROBE  (spec: docs/constitution-enforcement-handoff.md)
   Port dante's PII regexes into a STDLIB probe (no pip dep on dante) and add it to the `gate` job, so a
   stray PAN/Aadhaar in a non-plan .py/.md is caught in CI, not just locally.

For each PR: plan → show me → implement → `python -m pytest -q` + paste output → guard test green → docs
updated. Then stop for review before the next. (Item 6, the BRANCH_PROTECTION_TOKEN secret, is mine to do —
just remind me.)
```
