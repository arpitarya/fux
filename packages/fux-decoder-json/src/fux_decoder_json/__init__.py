"""`fux_decoder_json` — the fux-decoder-json package (W-289, SR-PLUGINS).

One fux decoder module per format it reads: `fux_decoder_json.json`, `fux_decoder_json.jsonl`. Each is the
decoder protocol of SR-DECODE — `EXTENSIONS`, `VERSION`, `USES` and
`decode(raw, rel_path)` — moved here unchanged from `src/fux/decode/` in
W-289 phase 2.

**fux loads a module from here only when `.fux/config/plugins.toml` declares this
package**, after verifying its version and digest (SR-PLUGINS P3, P4), by its
fixed import name (P7). A same-named file in `.fux/decoders/` overrides it
(P8). This file runs nothing: importing the package imports no decoder.
"""
