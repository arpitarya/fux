---
type: OpenItem
id: W-201
title: "W-201 — frontmatter scalars are not indexed: a `doc_id:` is unreachable by the string a person types"
description: "Found 2026-09-18 measuring identifier headroom on the golden ladder. `parse.py` splits meta from body and only body reaches the postings, so an identifier that exists only as a frontmatter `doc_id:` cannot be retrieved at any rung — three of the seed's 33 identifiers, and every frontmatter-only value (`find ADR`, `find Deshmukh`). Arpit rules which keys are indexed and into which field."
status: open
lane: arpit
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
ball: arpit
---

# W-200 — a `doc_id:` you can read is not one you can search

**Model: Opus for the ruling's spec; Sonnet to build once ruled** — it is a
small ingest change with a pre-registration in front of it.

## The finding

[The identifier-headroom run](../regression/2026-09-18-identifier-headroom/report.md):
three of the seed's 33 identifiers live **only** in YAML frontmatter
(`doc_id: QCL-IT-ADR-08`, `QCL-CS-MTX-02`, `QCL-OPS-DOCK-03`), and the first is
**absent from the top 50 at every rung**, whole or split. `find ADR` and
`find Deshmukh` show the same for any frontmatter-only value.

**Mechanism:** [`src/fux/ingest/parse.py`](../../src/fux/ingest/parse.py)
returns `ParsedDoc(meta, body)`; the postings come from `body`. The title is
taken from meta; nothing else in meta is indexed. Deliberate or not, it is
unrecorded — neither [SR-INGEST](../../records/0106_ingest.md) nor
[SR-DECODE](../../records/0139_decode.md) says which frontmatter keys reach the
index.

## 🔴 What Arpit decides

1. **Which keys.** `doc_id` is the obvious one — it is the string a person types
   to ask for that document. `owner`, `contributors`, `author` are names, and
   [SR-PII](../../records/0148_pii.md) applies before they enter a posting list.
   `tags`, `status`, `supersedes` are already read as edges/flags.
2. **Into which field.** `title` (weight 2.0) makes an identifier as strong as
   the title; `ctx` (1.0) makes it a body-strength term; a new field is a format
   change and this item does not propose one.
3. **Whether the rule is a closed list in `formats.toml` or an open one** — a
   consumer's frontmatter keys are theirs, and a closed list is the
   auditable shape.

## Definition of done, once ruled

- A pre-registration frozen first: the three frontmatter-only identifiers are
  the headroom, and **3 is below the floor on this seed** — so the endpoint is
  *the three become reachable* (a data-shaped check) plus a no-harm arm on the
  33 id-queries and a sample of non-id questions.
- The chosen keys reach the chosen field; a test asserts a frontmatter-only
  identifier is retrievable and a non-listed key is not.
- SR-INGEST gains a decision naming the keys; `formats.toml` carries the list
  if closed.

## Out of scope

The unstemmed identifier field (W-168 step 2) — a different defect, with
3–4 of 33 headroom on this corpus for a different reason.
