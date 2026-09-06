---
name: fux-decoder
description: Write a new Fux decoder, or edit an existing one, in .fux/decoders/. Use ONLY when explicitly asked — for example "add a decoder for .srt", "fux can't read our Confluence exports", "change how fux reads spreadsheets", "make the PDF decoder use pypdf". Writes Python into a committed directory that changes which documents are indexed and how they rank.
---

# Writing a Fux decoder

A **decoder** turns one file format into Markdown so Fux can index it. Sixteen
ship with Fux and live in `.fux/decoders/` in this repository — **those copies
are what run**, not the ones inside the installed package.

> ⚠ **This skill writes committed code that changes what is indexed and how it
> ranks.** Only act when a human asked for it by name. Never add or edit a
> decoder as a side effect of another task.

---

## 1 · Decide which of three jobs this is

| the ask | what to do |
|---|---|
| Fux ignores a format entirely | **New decoder.** A new file in `.fux/decoders/` |
| Fux reads a format badly | **Edit the existing one.** It is already in `.fux/decoders/` — open it |
| A format needs a library Fux does not ship (`pypdf`, `olefile`, OCR) | **Edit or replace**, and add the dependency to the repo's own environment |

**Check what exists before writing anything:**

```bash
ls .fux/decoders/
grep -l "EXTENSIONS" .fux/decoders/*.py | xargs grep -H "^EXTENSIONS"
```

If a decoder already claims the extension, **edit it**. Two files claiming one
extension is a defect — the loader resolves by module name, and the loser is
silently ignored.

---

## 2 · The contract

Two names in one file. That is the whole interface.

```python
EXTENSIONS = (".srt", ".vtt")                          # lowercase, with the dot

def decode(raw: bytes, rel_path: str) -> str | None:   # bytes in, Markdown out
    ...
```

| rule | why it exists |
|---|---|
| **Return Markdown, not plain text** | `extract.py` re-derives headings from `#` and puts them in their own weighted field. Flat text drops every heading into the body and disables *heading match outranks body match* for that format |
| **Return `None` for "a model must read this"** | A scanned PDF, a deck of images. This is a signal, not an error — it is what feeds enrichment |
| **Never raise for malformed input** | One corrupt file among ten thousand must not end the ingest. Catch, return `None` |
| **Be deterministic** | Sort every iteration. No `set` order, no dict-insertion reliance, **no clock**. Two teammates with identical files must produce an identical index |
| **Never open a socket** | Ingest is offline. Nothing can enforce this inside your file, so it is on you |
| **Never write anything durable** | The Markdown feeds statistics and is discarded. The index holds statistics, never content |

**Optional, for a library that refuses a buffer** (`pypdf`, `olefile`):

```python
WANTS_PATH = True

def decode(path, rel_path: str) -> str | None:   # a real file, removed after
    ...
```

Prefer bytes. It is testable from memory, cannot read anything it was not
handed, and works for content that never had a path.

**Files starting with `_` are helpers, not decoders** — the loader skips them.
Put shared code there.

---

## 3 · Write it

```python
# .fux/decoders/srtdoc.py
"""SubRip and WebVTT subtitles -> Markdown.

Meeting recordings are transcripts, and a transcript is prose nobody can
currently find. Timings and cue numbers are dropped: they are not words.
"""
from __future__ import annotations

import re

EXTENSIONS = (".srt", ".vtt")

_TIMING = re.compile(r"^\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->")


def decode(raw: bytes, rel_path: str) -> str | None:
    lines = []
    for line in raw.decode("utf-8-sig", errors="replace").splitlines():
        text = line.strip()
        if not text or text.isdigit() or text == "WEBVTT" or _TIMING.match(text):
            continue
        lines.append(text)
    body = " ".join(lines)
    if not body:
        return None
    return f"# {rel_path.rsplit('/', 1)[-1]}\n\n{body}"
```

**Then make the type indexable.** A decoder alone is not enough — the walker
still filters on `.fux/sources/types`:

```
*.srt
*.vtt
```

Absent that file, the built-in default (`*.md`, `*.markdown`, `*.txt`, `*.rst`,
`*.adoc`, `*.org`) applies and your new format is never walked.

---

## 4 · Verify before you claim it works

**Decode a real file and READ the output.** This is not optional ceremony. Four
defects in the shipped decoders produced *plausible* output rather than an
error — one made an entire format decode to nothing, silently. A test asserting
"decoding succeeded" passes on all of them.

```bash
python -c "
from fux.decode import decode
import pathlib
p = pathlib.Path('sample.srt')
print(decode(p.read_bytes(), p.name, pathlib.Path('.')))
"
```

Check, in order:

1. **Is the text all there?** Compare against opening the file yourself.
2. **Are headings `#` lines?** If everything is body text, ranking loses its
   strongest signal for that format.
3. **Is anything duplicated?** A nested walk that emits a container *and* its
   children doubles those terms' frequency.
4. **Are words intact?** Joining fragments with a space splits words that were
   only split by formatting.
5. **Run it twice** and diff. Different output means non-determinism.
6. **Feed it garbage** — `b"\x00\xff not this format"` — and confirm it returns
   `None` rather than raising.

Then ingest and search for something only that file contains:

```bash
fux ingest && fux ask "a phrase from the new file"
```

---

## 5 · How this plane is built — read before editing a shipped decoder

Every decoder is `bytes -> Markdown | None`, dispatched by lowercase extension.
Fux looks in `.fux/decoders/` first; if no file of that module name is there,
it falls back to the copy inside the installed package. **Deleting a decoder
restores the built-in** rather than dropping the format.

Three shared helpers do the parts that are dangerous to rewrite:

| helper | gives you | why not do it yourself |
|---|---|---|
| `fux.decode._zip` | `SafeZip`, `numeric_key` | Decompression-bomb caps, and **sorted** member lists. `namelist()` is archive order — writer-dependent — and `slide10` sorts before `slide2` |
| `fux.decode._xml` | `parse`, `local`, `text_of` | Refuses any DOCTYPE, which closes billion-laughs and XXE in one rule |
| `fux.decode._ooxml` | `paragraph_text`, `heading_level`, `table_markdown` | Run assembly. A run boundary is a formatting event, **not** a word boundary |

⚠ **Imports must be absolute** — `from fux.decode._zip import SafeZip`, never
`from . import _zip`. A file loaded by path has no parent package, so a
relative import raises and the decoder is dead on arrival.

**Pick the closest shipped decoder and read it first:**

| your format looks like | read |
|---|---|
| a zip of XML (Office, OpenDocument) | `docxdoc.py`, then `_ooxml.py` |
| markup or tags | `htmldoc.py` |
| nested key/value (JSON, TOML, config) | `jsondoc.py` — especially `_prose`, which drops UUIDs, hashes, timestamps and bare numbers |
| line-oriented text | `yamldoc.py`, `csvdoc.py` |
| a binary container | `pdfdoc.py` — and read its stated limits before copying its approach |
| headers plus a body | `maildoc.py` |

---

## 6 · Judgement, not mechanics

The mechanics are easy. These four decisions are where decoders go wrong, and
each already cost a defect in the shipped set:

- **What becomes a heading?** Whatever names the thing under it — a key, a
  sheet name, a slide title, a subject line. This is the highest-value choice
  you make.
- **What is not a word?** UUIDs, hashes, base64, timestamps, bare numbers. They
  inflate the corpus and distort rarity for the terms real documents rely on.
  `.json` was once 11 % of a repo's tokens for exactly this reason.
- **What is generated rather than written?** Notebook outputs change every run;
  indexing them makes the index depend on who last hit Run.
- **What is metadata, not content?** Font tables, routing headers, style
  definitions. Emitting them puts "Times New Roman" in your search results.

---

## 7 · Pointers

| you want | go to |
|---|---|
| the decision of record | `docs/adr/0042_decode.md` — §1 for the shape, §2 for the protocol and every per-format judgement |
| the sixteen shipped decoders | `.fux/decoders/` in this repo |
| the loader, the override rule, the registry | `fux.decode.__init__` — read its module docstring |
| where decoding joins ingest | `fux.ingest.parse.parse_document` |
| which files are walked at all | `.fux/sources/types`, and `docs/adr/0031_types-list.md` |
| what `.fux/` may contain | `docs/adr/0003_fux-directory.md` |
| worked tests to copy | `tests/decode/test_formats.py` — fixtures are built in the test, never committed as binaries, so the input is readable beside the assertion |

**When you finish:** say which files you changed, which formats are affected,
and whether existing documents will re-rank. A decoder change is a ranking
change, and the person who asked deserves to know that before they commit it.
