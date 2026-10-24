---
name: fux-decoder
description: Write a new Fux decoder, or edit an existing one, in .fux/decoders/. Use ONLY when explicitly asked — for example "add a decoder for .srt", "fux can't read our Confluence exports", "change how fux reads spreadsheets", "make the PDF decoder use pypdf". Writes Python into a committed directory that changes which documents are indexed and how they rank.
---

# Writing a Fux decoder

A **decoder** turns one file format into Markdown so Fux can index it. Seventeen
are first-party, shipped in `fux-decoder-*` packages (`fux-decoder-pdf`,
`fux-decoder-office`, …). **One runs only when `.fux/config/plugins.toml` declares its
package**, installed at the pinned version and digest. A file you put in
`.fux/decoders/<module>.py` overrides the package's module of that name.

> ⚠ **This skill writes committed code that changes what is indexed and how it
> ranks.** Only act when a human asked for it by name. Never add or edit a
> decoder as a side effect of another task.

---

## 1 · Decide which of three jobs this is

| the ask | what to do |
|---|---|
| Fux ignores a format a first-party package reads (`fux ingest` prints `N .pdf file(s) not read`) | **Not a decoder job.** Declare the package: `fux setup` adds it to `.fux/config/plugins.toml` and prints the install line |
| Fux ignores a format entirely | **New decoder.** A new file in `.fux/decoders/` |
| Fux reads a format badly | **Override the shipped one.** Copy the package's module into `.fux/decoders/<module>.py` and edit the copy — it now runs instead of the package's |
| A format needs a library Fux does not ship (`pypdf`, `olefile`, OCR) | **Override or replace**, and add the dependency to the repo's own environment |

**Check what exists before writing anything:**

```bash
cat .fux/config/plugins.toml          # the declared packages
ls .fux/decoders/              # your overrides, if any
fux doctor | grep -i plugins   # what is declared, installed, and not covered
python -c "import fux_decoder_pdf.pdf as m; print(m.__file__)"   # a shipped module, to copy
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

**Your headings ARE your chunking. There is nothing to declare.**

`text/chunk.py` derives what a citable passage is from the heading depth you
emit, with one rule: *a short section folds forward only into a section nested
inside it.* So:

| you emit | you get |
|---|---|
| a run of siblings — `## Slide 1`, `## Slide 2`, … | one passage each, never merged, however short |
| a heading with nested subheadings | one passage per section, stubs folded into the enclosing one |
| a Markdown table | one passage per row, header repeated |
| one heading | the whole file, one passage |

⚠ **If your format's unit is a slide, message, page or record, emit them as
SIBLINGS at one level under a `# <filename>` title.** That is the whole
mechanism — a short unit beside a long one is safe because they are siblings,
not because anything was declared. See `records/0151_chunking.md`.

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
still filters on `.fux/config/formats.toml`. Bind each extension to your module under
`[decoders]`; a bound extension is a document, and fux checks the binding
against the module it names:

```toml
[decoders]
srt = "srtdoc"
vtt = "srtdoc"
```

A binding to a first-party module (`pdf = "pdf"`) reads nothing until its
package is declared in `.fux/config/plugins.toml` — or until a file of that module
name sits in `.fux/decoders/`.

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
it runs the module from the **declared** package; if no package carrying it is
declared, the format is not read (and `fux ingest` counts its files on stderr).
**Deleting an override restores the package's module** rather than dropping
the format — as long as the package is declared.

An older `fux setup` (before 4.2) seeded a copy of every decoder into
`.fux/decoders/`, each starting with `# fux-template: <sha256>`. `fux doctor`'s
`seeded copies removable` row names every copy that is still **unedited** — delete
those, so the package runs and engine fixes reach you. A copy that imports
`fux.decode.json` or `fux.decode.ext.table` stops ingest with an error naming
where the import moved: delete it if unedited, or fix the import if it is yours.

Shared **decoder extensions** do the parts that are dangerous to rewrite. Five
are in fux itself, under `fux.decode.ext`; `table` ships in the
`fux-extension-table` package, which every table-reading decoder package
depends on:

| decoder extension | gives you | why not do it yourself |
|---|---|---|
| `fux.decode.ext.zip` | `SafeZip`, `numeric_key` | Decompression-bomb caps, and **sorted** member lists. `namelist()` is archive order — writer-dependent — and `slide10` sorts before `slide2` |
| `fux.decode.ext.xml` | `parse`, `local`, `text_of` | Refuses any DOCTYPE, which closes billion-laughs and XXE in one rule |
| `fux.decode.ext.ooxml` | `paragraph_text`, `heading_level` | Run assembly. A run boundary is a formatting event, **not** a word boundary |
| `fux_extension_table.table` | `Grid`, `Cell`, `Table`, `emit` | The one table emitter: values, spans, the header, the row budget, `\|` escaping — and exactly the Markdown the chunker reads back as rows |
| `fux.decode.ext.limits` | `limit`, `max_table_rows` | The repository's committed caps (`.fux/config/formats.toml [limits]`), read without a third `decode()` parameter |
| `fux.decode.ext.markdown` | `headings`, `strip_headings` | The one heading grammar, fence-aware |

**Name the ones you call in `USES`**, beside `EXTENSIONS` — for example
`USES = ("table", "limits")`, counting any your imports reach through another
extension (`ooxml` uses `xml`, which uses `limits`). Each one's `VERSION` then
joins your decoder's reuse key, so an engine fix to the table emitter
re-extracts your documents on the next `fux ingest` instead of waiting for
`--full`. An unknown name stops the load and names your file. Your decoder's
**suffixes** are still `EXTENSIONS` — *decoder extension* is a different word
(`docs/GLOSSARY.md`).

⚠ **Imports must be absolute** — `from fux.decode.ext.zip import SafeZip`,
`from fux_extension_table import table`, never `from . import zip`. A file loaded by path has no parent package, so a
relative import raises and the decoder is dead on arrival. The pre-4.2 names
(`fux.decode._zip`, `_xml`, `_ooxml`, `_markdown`, `_limits`) still import, as
aliases of the same modules — but declare nothing to the reuse key, so prefer
the `ext` names.

**Pick the closest shipped decoder and read it first:**

| your format looks like | read |
|---|---|
| a zip of XML (Office, OpenDocument) | `fux_decoder_office/docx.py`, then `fux/decode/ext/ooxml.py` |
| markup or tags | `fux_decoder_html/html.py` |
| nested key/value (JSON, TOML, config) | `fux_decoder_json/json.py` — especially `_prose`, which drops UUIDs, hashes, timestamps and bare numbers |
| line-oriented text | `fux_decoder_config/yaml.py`, `fux_decoder_sheet/csv.py` |
| a binary container | `fux_decoder_pdf/pdf.py` — and read its stated limits before copying its approach |
| headers plus a body | `fux_decoder_mail/mail.py` |

(In this repository they are under `packages/fux-decoder-*/src/`; installed,
`python -c "import fux_decoder_html.html as m; print(m.__file__)"` finds one.)

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
| the decision of record | `records/0139_decode.md` — §1 for the shape, §2 for the protocol and every per-format judgement |
| the seventeen shipped decoders | the `fux-decoder-*` packages; which one reads what is `fux.plugins.first_party()` |
| which packages this repo declares | `.fux/config/plugins.toml`, and `records/0165_plugins.md` |
| the loader, the override rule, the registry | `fux.decode.__init__` — read its module docstring |
| where decoding joins ingest | `fux.ingest.parse.parse_document` |
| which files are walked at all | `.fux/config/formats.toml`, and `records/0128_types-list.md` |
| what `.fux/` may contain | `records/0102_fux-directory.md` |
| worked tests to copy | `tests/decode/test_formats.py` — fixtures are built in the test, never committed as binaries, so the input is readable beside the assertion |

**When you finish:** say which files you changed, which formats are affected,
and whether existing documents will re-rank. A decoder change is a ranking
change, and the person who asked deserves to know that before they commit it.
