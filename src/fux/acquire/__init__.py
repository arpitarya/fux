"""Acquiring a document from its source — the source lists, the directory
walk, URL fetching, refusals, freshness and PII redaction. Core layer
(W-282): the writer ingests through it and the reader re-reads through it
at answer time (refer), and it imports neither.
"""
