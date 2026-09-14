---
type: Handoff
name: W-169
description: "`fux inspect` — a read-only verb reporting the shape of the index: boilerplate words (the TLDR case), unfindable documents, length and fields, duplicates and templates, analyzer coverage, graph orphans and hubs. Words come from a local, gitignored hash → word dictionary; nothing new is committed; descriptive by default with three provisional checks. Promoted from proposals/fux-inspect.md."
item: W-169
filed: 2026-09-14
ball: agent
---

# W-169 — `fux inspect`

**Model: Opus for the lens definitions and the three checks; Sonnet for the report
plumbing.**

**Promoted 2026-09-14 by Arpit** from [`proposals/fux-inspect.md`](../proposals/fux-inspect.md),
which stays the spec: its §2 six lenses, §3 verdict discipline, §4 finding → lever table,
§5 placement and §5b tests are the definition of done and are not repeated here.

## Definition of done — the short form

1. `fux inspect` (Python first) writes a Markdown report and `--json` under
   `.fux/runtime/inspect/`; `git status` stays clean on a clean clone (tested).
2. The hash → word dictionary is built locally by re-tokenising sources with the live
   analyzer; the committed index stays hashes ([SR-POSTINGS](../../records/0112_postings.md) d2).
3. Six lenses, each proven on a **planted corpus** in `tests_e2e/` (a plant per lens;
   each lens names its plant and nothing else).
4. Determinism: byte-identical report twice.
5. Three checks — findable share, boilerplate share, near-duplicate share — with
   floors measured on the golden ladder and marked provisional; a floor that flags a
   healthy rung drops to descriptive.
6. Every finding prints its lever (`[index]` stopwords · `.fuxignore` / `archived=` /
   `supersedes` · `fux enrich` / `fux correct` · decoder) and applies none.
7. A new **SR-INSPECT** from the template, ownership row + `test_sr_ownership.py`;
   SR-CLI (the verb); a `fux-inspect` guide skill (decision-15 shape, all vendors);
   GLOSSARY entries *findability*, *boilerplate term*, *template family*.

## Out of scope

Changing ranking, stopwords or the analyzer — `inspect` reads; the levers are other
items. Node parity — Python first, Node when the dictionary build has a home there.

## Records this will touch

SR-INSPECT (new) · SR-CLI · SR-POSTINGS (the local dictionary note) · SR-DOCTOR (the
boundary) · SR-AGENT-POLICY (the skill).
