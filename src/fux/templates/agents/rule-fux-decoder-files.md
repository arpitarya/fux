---
paths:
  - ".fux/decoders/**"
---

# Editing a Fux decoder

The files in `.fux/decoders/` are the decoders that run. They are committed and
change which documents are indexed and how they rank.

- **Only when a human asked for this decoder change.** Never as a side effect.
- **Contract:** `EXTENSIONS` (lowercase, with the dot) and
  `decode(raw: bytes, rel_path: str) -> str | None`.
- **Return Markdown**, so headings land in their weighted field; return `None`
  when a model must read the file; **never raise** on malformed input.
- **Deterministic and offline:** no clock, no unordered iteration, no socket,
  nothing written to disk.
- One extension, one decoder - check `EXTENSIONS` in the others first.
- A decoder change moves no source bytes: run `fux ingest --full` to see it.

Full procedure: the `fux-decoder` skill.
