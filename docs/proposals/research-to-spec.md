---
type: Proposal
title: Research-to-Spec — evidence-backed product specs from the corpus
description: Draft PRDs/specs where every claim cites a file:line in the versioned corpus; spec review becomes evidence review.
status: proposed
timestamp: 2026-07-21T00:00:00Z
tags: [product-development, citations, corpus]
---

# Research-to-Spec

## Signal

PRDs and specs are full of uncited claims ("users want X", "competitor does Y") that
nobody can verify six months later. Fux v1 already has the pieces: web/CDP ingestion
of competitor docs and standards, provenance frontmatter on every cached file, and
extractive answers with `file:line` citations.

## Sketch

`fux ingest` competitor docs, standards, user-feedback exports → corpus in git →
while drafting a spec, `fux answer "what do competitors charge for X?"` returns cited
evidence → the spec carries citation blocks pointing into the corpus at a specific
git commit. Spec review = checking the evidence trail. A `fux cite <question>`
helper could emit a ready-to-paste citation block.

## Why parked

v1 must ship and be dogfooded first; this is a workflow *on top of* v1 primitives,
not new engine work. Graduates when: v1 is stable in Anton and a real spec gets
written this way once by hand.

# Citations

[1] [Knowledge as Code pattern](https://knowledge-as-code.com/) — plain-text canonical knowledge with verification (accessed 2026-07-21).
[2] [Lore — git commits as structured knowledge for AI agents (arXiv:2603.15566)](https://arxiv.org/pdf/2603.15566) — git as the knowledge protocol substrate (accessed 2026-07-21).
