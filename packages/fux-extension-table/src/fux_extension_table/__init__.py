"""`fux_extension_table` — the fux-extension-table package (W-289, SR-PLUGINS).

The `table` decoder extension — `fux_extension_table.table`, the one emitter every table
format becomes Markdown through (SR-TABULAR). Moved here unchanged from
`src/fux/decode/ext/table.py` in W-289 phase 2.

**Never declared directly**: it arrives as a dependency of the decoder packages
that call it, and `.fux/plugins.toml` pins it as one more row. Its `VERSION` is
still `constants.toml [extensions.table] version` and still rides in the reuse
key of every decoder whose `USES` names `table` (SR-DECODE decision 24).
"""
