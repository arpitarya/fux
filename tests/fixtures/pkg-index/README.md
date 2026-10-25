# The fixture index package (W-299, SR-PKG-INDEX)

`docs/` is the documentation of a pretend library, `acme-docs`. The tests in
`tests/test_pkg_index.py` ingest it in a temporary directory, lay the result out
as an index segment (`index/*.jsonl`, `identifiers.toml`, `fux-index.json`), and
install that one segment twice — as the PyPI import package `acme_docs_index/`
and as the npm package `node_modules/acme-docs-index/` — so both runtimes pin,
verify, refuse and inflate identical segment bytes.

The shards are built at test time rather than committed, so a `_format` or
analyzer bump never leaves a stale fixture behind (SR-PKG-INDEX decision 6 would
refuse it as foreign).
