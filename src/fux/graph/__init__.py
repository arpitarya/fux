"""The document graph — latent in the corpus, materialized as rows (proposal §4).

Not a second source of truth: every edge is *extracted from artifacts that
already exist* — the links an author wrote, the citation sections they kept,
the crawl parentage the fetcher recorded, the tags in their frontmatter. Delete
`fux.db` and the graph rebuilds identically, because nothing here is invented.

This is the sanctioned return of the archived graph work, with the two
properties that made the old one unworkable removed: it is a *document* graph,
not a code graph, and it costs **zero model calls**.

Edges carry a grade, which is how reliability scoring stays honest:

- ``EXTRACTED`` (weight 1.0) — deterministic, re-derivable, what this module emits.
- ``INFERRED`` (weight 0.6) — semantic edges a host session may write back later.
  The schema supports them; nothing here generates them.
"""

from __future__ import annotations

from .extract import EXTRACTED, INFERRED, Edge, edges_from_scans, scan_document

__all__ = ["EXTRACTED", "INFERRED", "Edge", "edges_from_scans", "scan_document"]
