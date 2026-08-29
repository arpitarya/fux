---
type: ADR
name: ADR-DECODE
title: "ADR-DECODE (0042) — the decoder plane: bytes become Markdown in one place, and a consumer may bring a dependency fux may not"
description: "Decoding gets one home, one protocol, and a consumer seam where third-party libraries are legal — declared, so a machine that cannot satisfy the declaration fails instead of committing a smaller index."
status: accepted
date: 2026-08-26
feature: the decoder plane — the protocol, the registry, the consumer seam and the enrichment queue
owns: [src/fux/decode, src/fux/templates/agents/DECODER-SKILL.md]
laws: [L1, L2, L3, L4]
timestamp: 2026-08-26T00:00:00Z
---

# ADR-DECODE — bytes become Markdown in one place

## §1 — For humans

Fux indexed six plain-text extensions and nothing else. The corpus it is pitched
at is mostly PDFs, decks, spreadsheets, wiki HTML and mail.

⚠ **The awkward part: it already owned an HTML decoder.** It sat inside
`.fux/fetchers/http.py`, and a second copy sat inside `cdp.py` with a comment
saying *"Kept identical to…"*. `http.py`'s docstring stated the consequence as a
rule it had no way to enforce:

> Both fetchers must produce the same markdown from the same bytes, or which
> fetcher retrieved a document would change the committed index.

**That is L3 demoted to a code comment** — and neither copy was reachable from
the git-dir walker, so **a `.html` file sitting on disk was never decoded at
all.**

**A decoder is `bytes -> Markdown`, not `bytes -> text`,** and that is forced
rather than chosen: `extract.py` re-derives headings from `#` and gives them
their own weighted field. **Flat text would silently disable *heading match
outranks body match* for every non-Markdown document.**

```mermaid
flowchart TD
    W["the walker reads bytes"] --> C{"does a decoder claim<br/>this extension?"}
    C -->|no| P["parse: utf-8 + NFC + frontmatter"]
    P --> X["extract.py"]
    C -->|yes| O{"is there a copy in<br/>.fux/decoders/ ?"}
    O -->|"yes: the normal case,<br/>setup writes all of them"| CD["the CONSUMER COPY runs<br/>consumer dependencies allowed"]
    O -->|"no: the copy was deleted"| BD["the packaged built-in runs<br/>stdlib only, L1"]
    CD --> R{"Markdown, or None?"}
    BD --> R
    R -->|Markdown| N["NFC applied<br/>frontmatter NOT re-read"]
    N --> X
    R -->|None| Q["skipped, and written to the queue:<br/>a model must read it"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  the walker reads bytes
        |
  does a decoder claim this extension?
        |                     |
        no                   yes
        |                     |
  parse:                is there a copy in .fux/decoders/ ?
  utf-8 + NFC +               |                    |
  frontmatter          yes: the normal      no: the copy
        |              case, setup          was deleted
        |              writes them all           |
        |                     |                  |
        |            the CONSUMER COPY    the packaged built-in
        |            runs (consumer       runs (stdlib only, L1)
        |            dependencies OK)           |
        |                     |                  |
        |                     +--------+---------+
        |                              |
        |                     Markdown, or None?
        |                      |               |
        |                 Markdown            None
        |                      |               |
        |                NFC applied      skipped, and queued:
        |                frontmatter      a model must read it
        |                NOT re-read
        +----------+-----------+
                   |
              extract.py
```

</details>

**Why a consumer may bring a dependency fux may not.** Legacy Office formats,
OCR and a stronger PDF need libraries the runtime is not allowed to have. **The
answer is not to amend L1** — it is
[ADR-ENRICH](0040_enrich.md) decision 1's table gaining a third row:

| fux refuses to own | the consumer owns it as |
|---|---|
| network I/O | `.fux/fetchers/http.py` |
| model calls | their own agent, invoked by them |
| **third-party parsing libraries** | **`.fux/decoders/<name>.py`** |

---

## §2 — For agents

### Context

- The walker skipped anything containing a NUL byte or failing a UTF-8 decode.
  **A `.docx` is a zip and a `.pdf` is compressed streams: both fail both tests,
  and both are documents.** *Binary* stopped being a sufficient reason to skip
  the moment decoders existed.
- `parse(content: bytes)` took no path, so it could not dispatch on type.
- Two fetchers carried two copies of one converter.

### Decision

**1. A decoder is `bytes -> Markdown | None`, keyed by lowercase extension.**
`None` means *nothing readable came out* — an image, a scanned PDF — and is a
**return value rather than an exception**, because it is a fact about the
document, not a failure of the run. It is the signal the queue in decision 13 is
built on.

**2. Markdown is the intermediate, because `extract.py` reads `#`.** A decoder
returning flat text would drop every heading into the body field. **The heading
syntax is the interface between the two planes.**

**This is the contract, not a default a later session may quietly revisit.** The
alternative on the table was a structured `headings: list[str]` field, with
decoders returning structure directly instead of encoding it. **Markdown won
because a decoded document then takes the exact path an already-prose file
takes**: one pipeline, the best-tested one, no branch, and nothing to migrate
across every built-in decoder plus every consumer copy.

⚠ **The accepted cost, and it is one-directional.** A decoder that *knows* a
line is body text has no way to say so when that line begins with `#`. A PDF
line `# 3 of 7 — see appendix`, a CSV cell `#1 priority`, an RTF paragraph
starting with a hash — **each is promoted to a heading and weighted above
body.** The structure was known at decode time and is **deliberately thrown away
and re-derived**; that round-trip is the smell being accepted, not overlooked.
**No reopen-trigger is attached** — one was offered and declined, so a future
session proposing the structured field is reopening a ratified decision, not
filling a gap.

**3. Frontmatter is NOT re-parsed on decoded output.** Frontmatter is something
a human typed at the top of a source file; **decoded Markdown is generated, and
generated Markdown can legitimately begin with `---`** (an HTML `<hr>` produces
exactly that), which the frontmatter parser would eat as a delimiter.
Already-prose documents keep the old path untouched, so no existing corpus
moves.

**4. Bytes by default; a path only on request.** `WANTS_PATH = True` makes fux
spill a temporary file with the original suffix and hand over its path. **Bytes
is the default because it is testable from memory, cannot read anything it was
not handed, and works unchanged for URL-sourced content, which has no path** —
the opt-in exists because some libraries will not accept a buffer, and without
it every such decoder would spill its own temp file, differently.

**5. A consumer decoder overrides a built-in BY MODULE NAME, not by extension.**
`.fux/decoders/htmldoc.py` replaces the built-in `htmldoc` wholesale — not
merged, not fallen back to. **Matching on extension would let two files both
claim `.html` and resolve by load order**, which is the same class of defect as
a filesystem-ordered registry.

**6. The built-in module list is an explicit sorted tuple, never a directory
scan.** A directory listing is filesystem order; **a plane whose dispatch
depends on filesystem order has a committed index that depends on it too**
(L3).

**7. A missing consumer dependency is a HARD ERROR naming the module.**
*Unavailable* has to mean **the ingest stops**, not that the index quietly
shrinks. ⚠ **Detection would break L3 outright:** a decoder that ran whenever
its library happened to import makes two developers with identical sources
commit different root hashes. **Declared-and-committed plus a loud failure is
what preserves *same sources → same index*.**

**8. A decoder that raises is a skipped document, never a failed run.**
`DecodeFailed` is deliberately **not** a `FuxError`, because `FuxError` renders
at the CLI boundary as *the command failed* — **and one corrupt file among ten
thousand is not that.**

**9. The default type allowlist is prose plus every extension a BUILT-IN decoder
claims.** ⚠ **This decision once read the opposite** — that widening it needed a
pre-registered measurement — and **that was wrong on its own terms.** The
pre-registration rule governs **frozen thresholds**; the allowlist's *contents*
were never one (its own verdict block calls them *a defaults judgment rather
than a measurement*), so a ruling could move it, and one did. See
[ADR-TYPES](0031_types-list.md) decision 1 for what stays out and why, **and for
the reason the default may never be derived from the live registry.**

**10. `fux setup` writes every built-in decoder into `.fux/decoders/`, and the
copy is what runs.** The argument: **a consumer invited to override decoders
should be able to read them in their own repo**, which an eject-on-demand
alternative only half delivers.

- **There is no `.py.txt` template.** A fetcher needs one because it carries
  network code that must not be importable inside an offline package
  ([ADR-CDP-FETCHER](0020_cdp-fetcher.md) decision 9). **A decoder is
  stdlib-only and offline — it is already a legitimate module**, so the module
  *is* the template and the copy is byte-identical. **Two files that agree by
  habit is the duplication this record exists to remove**, and nineteen of
  them would be worse.
- ⚠ **Imports inside `decode/` are absolute.** A path-loaded file has no parent
  package, so a relative import raises *attempted relative import with no known
  parent package* and **every copy carrying a helper import would be dead on
  arrival.** Absolute imports are what make one set of bytes work in both
  places.
- **A deleted copy restores the built-in.** `rm .fux/decoders/pdfdoc.py` must
  not silently stop indexing PDFs — **that is indistinguishable from a corpus
  containing none.**
- ⚠ **The accepted cost, declined knowingly:** after setup,
  `src/fux/decode/` does not execute in that repo, so **engine upgrades do not
  reach a consumer's decoders.** Four real defects — ODF decoding to nothing,
  lexical slide order, doubled table cells, runs joined with a space — would
  each have needed every consumer to refresh their copy. The alternative on the
  table was *copies inert until edited*, resolved by a hash stamp; it was
  declined in favour of the simpler rule.

**10a. `jsonldoc`, `svgdoc` and `imagedoc` joined the built-in set on
2026-08-29** (sixteen → nineteen). `.jsonl` is `.json`'s line-delimited
sibling, walked the same way. `svgdoc` and `imagedoc` are the two format
families this record's §1 named as "no decoder" the day it was written —
SVG (markup, geometry dropped, only `<title>`/`<desc>`/`<text>` kept) and
raster images (PNG/JPEG/GIF, pixels dropped, only embedded text metadata
kept, hand-rolled per **L1** since Pillow is not stdlib). **The consequence
belongs to ADR-TYPES, not here**: decision 1 unions every built-in's
extensions into `DEFAULT_TYPES` automatically, so shipping these three
built-in reverses the SVG half of [ADR-TYPES](0031_types-list.md) decision 5
— see that record for the reversal and why it does not repeat verdict G's
measured failure.

**11. The plane ships its own skill, `fux-decoder`.** The answer to *how do I
write a decoder* had lived only in a module docstring and in §2 — **the
agent-facing half of a record, which is not where a consumer looks.**

- Rendered to `.claude/skills/fux-decoder/` and `.kiro/skills/fux-decoder/`.
  **Never to an ambient surface**: it writes committed Python that changes what
  is indexed ([ADR-AGENT-POLICY](0035_agent-policy.md) decision 9a).
- **Exempt from the verbatim policy block** — a build procedure, not a rendering
  of the archived-results policy, pinned by a test.
- **It carries the reasoning, not just the recipe**: the contract with a *why*
  per rule, the four judgement calls where decoders actually go wrong, the
  shared-helper table, and a pointer table naming which shipped decoder to read
  for which shape of format.
- ⚠ **Its verification section is the load-bearing part.** It tells the agent to
  decode a real file and **read the output**, because **all four defects found
  during the build produced plausible text rather than an error, and a test
  asserting *decoding succeeded* passes on every one of them.**

**12. The enrichment queue — what fux could not read, written down.** Before
this, **nothing in fux could *say* a document needs a model.**
[ADR-ENRICH](0040_enrich.md) decision 4 derives scope from a declaration; a
decoder returning `None` is **discovered**, and had nowhere to go.

| file | git | why |
|---|---|---|
| `.fux/enrich/queue.tsv` | **committed** | a backlog is a *team* fact; a teammate cloning the repo sees what needs a model without re-running ingest |
| `.fux/runtime/enrich-progress.tsv` | **gitignored** | which entries *this machine* handled is local; committing it would make two people's progress conflict on every pull |

- **Sorted by doc id, no wall clock, deduplicated.** It is a committed byte, so
  **L3 applies**: an ingest over an unchanged corpus leaves `git status` clean.
- **Paths, shas and a reason. Never content (L2).** **A queue that quoted the
  first line of an unreadable file would be the one place the architecture
  leaks.**
- **The reason distinguishes two facts**, and conflating them would make the
  queue useless: *no decoder for `.heic`* means someone could write one;
  *nothing readable in this `.pdf`* means only a model will help.
- ⚠ **`queue.tsv` is checked against the enrichment pruner's glob**, which
  deletes orphans in that directory. A file at the mercy of that glob would
  vanish; a test pins that it is invisible to it.
- ⚠ **Nothing consumes the queue yet.** `fux enrich` still derives its worklist
  from declared scope. **The queue records the need; wiring it to the verb is a
  separate decision** — and *discovered* and *declared* are different origins,
  so merging them amends an accepted record.

### Consequences

- **The converter duplication is structurally impossible now**, and the
  requirement a docstring asked for is retired rather than enforced.
- **A local `.html` on disk is decodable** for the first time.
- ⚠ **A consumer decoder can break L4 and no gate reaches it.** An import fence
  cannot see code loaded by path. This is the same asymmetry
  [ADR-ENRICH](0040_enrich.md) decision 3 owns about `model:` being a claim fux
  records and cannot confirm: **a documented obligation, checked by review of a
  committed diff. No test should be claimed to cover it.**
- ⚠ **An overridden decoder makes the index a function of consumer-edited
  code.** Already true of fetchers, accepted there, **named here so it is not
  discovered later.**
- **The walker's skip reasons change**, because `_skip_reason` consults the
  registry before judging bytes.

### Alternatives considered

- **A path-only protocol.** Rejected under decision 4: no answer for URL
  content, hands consumer code the run of the filesystem, and its contract moves
  the day the fetch contract returns bytes.
- **A structured `headings` field instead of Markdown.** Rejected under decision
  2, with its cost stated. **Reopening it is reopening a ratified decision.**
- **Amending L1 to permit optional dependencies.** Rejected as unnecessary —
  see §1's table. **L1 constrains the runtime fux ships; consumer code is not
  that.** A later session proposing this amendment is crossing this fence.
- **Detecting decoders by whether their library imports.** Rejected under
  decision 7: **an L3 violation wearing convenience as a disguise.**
- **Decoders for in-document structure (tables, code fences).** Rejected as a
  category — by the time a decoder finishes, a table *is* Markdown, and
  weighting it is `extract.py`'s job. **Consumer code owning ranking policy is a
  worse defect than a missing field.** See
  [`proposals/structure-aware-extraction.md`](../../work/proposals/structure-aware-extraction.md).

### Reference (required)

- [`src/fux/decode/__init__.py`](../../src/fux/decode/__init__.py) — the
  protocol, the registry and the override precedence, as code; the skill —
  [`src/fux/templates/agents/DECODER-SKILL.md`](../../src/fux/templates/agents/DECODER-SKILL.md).
- [`tests/decode/test_decode.py`](../../tests/decode/test_decode.py) — in
  particular `test_both_fetchers_now_share_one_conversion`, which asserts the
  copies are **gone** rather than that they currently agree, and
  `test_decoding_is_byte_identical_across_processes`, which varies
  `PYTHONHASHSEED`.
- [ADR-ENRICH](0040_enrich.md) decision 1 — the table this record extends, and
  the precedent that a consumer boundary is a design choice rather than a
  dependency budget; [ADR-TYPES](0031_types-list.md) — what the widened default
  admits and what it still refuses.
- The seam it changed in ingest — [ADR-INGEST](0007_ingest.md) decision 11; the
  fetchers that stopped converting —
  [ADR-HTTP-FETCHER](0021_http-fetcher.md) and
  [ADR-CDP-FETCHER](0020_cdp-fetcher.md).

### Veto condition

**Reopen if any of these becomes true:**

1. **A consumer decoder is found to have made an index non-reproducible** — two
   machines, same sources, same declared decoders, different root hash. That
   would mean declaration is not sufficient and decision 7 is wrong.
2. **A built-in decoder needs a non-stdlib import** to be correct rather than
   merely convenient. **That would mean the built-in/consumer split is drawn in
   the wrong place, not that L1 should move.**
3. **The default type allowlist is ever derived from the LIVE registry** rather
   than from the built-ins — a consumer dropping a decoder into `.fux/decoders/`
   must never silently start indexing a new file type
   ([ADR-TYPES](0031_types-list.md) decision 1a).
4. **A decoder returns flat text and a heading lands in the body field**, which
   is decision 2 failing rather than being traded.

**How to check them:**

```bash
# 1, 4 — the protocol's own properties
uv run pytest -q tests/decode/

# 2 — the built-ins are stdlib only
grep -rnE '^(import|from) ' src/fux/decode/ | grep -vE 'fux\.|^\S+:(import|from) (json|re|zipfile|xml|html|email|csv|struct|base64|io|pathlib|typing|dataclasses|unicodedata|__future__)'
# expect: no output

# 3 — the default unions BUILT-IN extensions only
grep -n 'builtin_extensions' src/fux/ingest/gitdir.py
# expect: one call, inside the default-types helper
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-INGEST](0007_ingest.md) ·
[ADR-EXTRACTED](0016_extracted-mode.md) ·
[ADR-CDP-FETCHER](0020_cdp-fetcher.md) ·
[ADR-HTTP-FETCHER](0021_http-fetcher.md) · [ADR-TYPES](0031_types-list.md) ·
[ADR-AGENT-POLICY](0035_agent-policy.md) · [ADR-ENRICH](0040_enrich.md)

**Code**

- [`.fux/fetchers/http.py`](../../.fux/fetchers/http.py)
- [`src/fux/decode/__init__.py`](../../src/fux/decode/__init__.py)
- [`src/fux/ingest/gitdir.py`](../../src/fux/ingest/gitdir.py)
- [`src/fux/templates/agents/DECODER-SKILL.md`](../../src/fux/templates/agents/DECODER-SKILL.md)
- [`tests/decode/test_decode.py`](../../tests/decode/test_decode.py)

**Project docs**

- [`work/proposals/structure-aware-extraction.md`](../../work/proposals/structure-aware-extraction.md)
