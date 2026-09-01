---
type: ADR
name: ADR-URL-LIST
title: "ADR-URL-LIST (0018) — the committed URL list"
description: "One URL per line in a committed file, deduped and sorted by the loader, so config order can never change committed bytes and thousands of entries diff and merge line by line."
status: accepted
date: 2026-08-19
feature: "`.fux/sources/urls` — the file format itself, and the one grammar both committed source lists are parsed by"
owns: [src/fux/ingest/sourcelist.py]
laws: [L2, L3, L4]
timestamp: 2026-08-19T00:00:00Z
---

# ADR-URL-LIST — the committed URL list

## §1 — For humans

The list of URLs Fux indexes is **a file, not a config array**: one URL per
line, `#` comments, blank lines ignored, committed to your repo.

That is the whole decision, and it is not cosmetic. A TOML array of 5 000
entries is **one diff hunk and one merge conflict** — two people adding a URL in
the same week collide, and a reviewer cannot see what changed. One entry per
line is what makes the list reviewable at the size it actually reaches.

The second half is that **the loader sorts and dedupes**. File order is
presentation only. You can group entries by team, by system, by whatever helps a
human read it, and it cannot change a single committed byte — which is what
keeps [ADR-INGEST](0007_ingest.md)'s byte-reproducibility true when two people
maintain the same list in different orders.

The third part is **per-URL attributes**: a line may carry `key=value` pairs
after the URL, `.gitattributes`-style. **There are two, and the set is closed.**

| attribute | values | default | decides |
|---|---|---|---|
| **`fetch`** | `http` · `cdp` | `http` | who retrieves the document |
| **`meta`** | `plain` · `hashed` | `hashed` | whether the index may hold readable display text |

```console
$ cat .fux/sources/urls
https://example.com/handbook/oncall                        # both defaults
https://example.com/docs/api             meta=plain
https://wiki.corp/display/ENG/runbook    fetch=cdp
https://app.corp/reports/q3              fetch=cdp meta=plain
```

**A line with no attributes means every default applies**, so every list valid
today stays valid.

This record exists separately from [ADR-URL-INGEST](0008_url-ingest.md) because
the two answer different questions: that record owns **what fetches a URL**,
this one owns **what the file says**. `fetch=` is the seam between them — this
record fixes the *grammar* and the closed set of attributes; the fetcher records
define what `fetch=` selects. **The writer is [ADR-CLI](0002_cli-surface.md)'s**
— this record decides what a line *means*, that one decides what the command
does.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    F[".fux/sources/urls<br/>committed, human-ordered"] --> P["read_urls<br/>strip comments · validate scheme"]
    P --> S["dedupe + sort<br/>file order discarded"]
    S --> R["stable URL set<br/>same bytes every run"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  .fux/sources/urls        read_urls              dedupe + sort        stable set
  +------------------+   +----------------+   +-----------------+   +-------------+
  | committed        |-->| strip comments |-->| file order is   |-->| same bytes  |
  | human-ordered    |   | validate http  |   | DISCARDED here  |   | every run   |
  +------------------+   +----------------+   +-----------------+   +-------------+
                                 |
                                 v  non-http(s) line
                          error: <file>:<lineno>
```

</details>

### Examples

Captured from the filed fixture,
[`2026-08-19-w54/evidence/fixture.sh`](../../work/regression/2026-08-19-w54/evidence/fixture.sh):

```console
$ cat .fux/sources/urls
# one URL per line. `#` is a comment at line start or after whitespace --
# NOT inside a URL.
https://example.invalid/handbook#oncall    fetch=http meta=hashed
https://example.invalid/handbook#deploys   fetch=http meta=hashed
https://example.invalid/handbook/oncall
https://example.invalid/public/api          fetch=http meta=plain
https://example.invalid/gone
```

**The two `#`-bearing lines are two documents**, which is decision 3's narrow
comment rule doing the only job it exists for. The bare line takes every
default; the `meta=plain` line loosens the L5 floor for one public page.

A URL that fails to fetch is a **skip**, not a deletion — the list is the
statement of intent, and only removing a line removes a document:

```console
$ fux update
ingested 7 docs (5 changed), 1 skipped, 5 shards written
  skip https://example.invalid/gone: fetch failed: 404 not found
```

---

## §2 — For agents

### Context

Three properties had to hold at once, and each rules out an obvious shape.

**It has to merge.** The design point is a corporate corpus, so the list reaches
thousands of entries maintained by people who do not coordinate. Any format
where one logical addition touches a shared line produces conflicts proportional
to team size.

**It has to be reviewable.** A URL entering the index is a decision about what
an agent will treat as authoritative. It belongs in a diff a human reads, not in
a value nested three levels into a config file.

**It must not affect committed bytes.** Two people can hold the same set in
different orders; the index must not know. This is L3 — same sources,
byte-identical index — applied to *config* rather than content.

### Decision

**1. The URL list is a file, not a TOML array.** Default `.fux/sources/urls`,
declared **committed** by [ADR-DOTFUX](0003_fux-directory.md). The path is
configurable ([ADR-CONFIG](0014_config.md)); the format is not.

**2. One URL per line.** Blank lines are ignored. This is the property that
makes the file merge line-by-line at any size, and it is the same reasoning that
shards the index.

**3. `#` starts a comment at the start of a line or after whitespace**, and the
rest of the line is discarded. **`#` anywhere else is part of the entry** — a
URL fragment is not a comment. Under decision 7 this is forced rather than
chosen: `https://x/a#frag meta=plain` cannot be parsed at all if `#` means a
comment everywhere.

**4. The loader dedupes and sorts.** File order is presentation only. A
duplicate line is not an error — it is a merge artefact, and failing the run for
one would make the file hostile to the collaboration it was designed for.

**5. A non-`http(s)` line is a loud error naming `file:lineno`**, never a silent
skip. A typo'd scheme that quietly fetches nothing is worse than a stopped run,
because the corpus is then wrong in a way nothing surfaces.

**6. The list is intent, not state.** A line present means *this document
belongs in the index*. A fetch that fails keeps the prior record and reports a
skip; only removing the line removes the document
([ADR-URL-INGEST](0008_url-ingest.md) decision 3). **The file never records
fetch outcomes.**

**7. A line may carry attributes after the URL**, separated by whitespace:
`<url> key=value [key=value ...]`. **One parser, shared with
`.fux/sources/dirs`** ([ADR-DIR-LIST](0022_dir-list.md) decision 2) — two
parsers for one grammar is how `#`-handling, sorting and the unknown-key error
end up disagreeing. Adding a third list is a `ListSpec`, not a parser.

**8. `key=value` is the only form.** No bare flags, no `-key` unset, no `!key`
revert — `.gitattributes` needs four states because its entries are *patterns*
that overlap; ours are exact entries that do not. One form, one meaning, nothing
to resolve. Values carry no whitespace and no quoting; a value that needs either
is a new decision, not a parser feature.

**9. An unknown key is a loud error naming `file:lineno`.** Same rule
[ADR-RECORD](0010_index-record.md) applies to `_format`: a reader that does not
know a key must refuse rather than guess. Silently ignoring one is how a typo'd
`mata=plain` ships a private document to a public index.

**10. A line attribute beats the source-wide setting, for that URL only.** The
default stays the strict one — L5 is a safety property, so opting out is
per-document and visible in a diff, never a blanket flip. **Two lines carrying
the same URL with *different* attributes are a loud error naming both line
numbers**, not a last-wins merge: exact URLs cannot legitimately disagree, and
quietly picking one would make a merge artefact into a policy change.

**11. The attribute set is closed, and it is two.** **Adding one is a change to
this record**, not a config addition — which is what makes decision 9's
unknown-key error safe to be strict about: the error is never wrong, because
there is nothing legitimate it can reject.

**12. A fux-written line carries every attribute, explicitly.** `fux add` emits
the complete set — `fetch=… meta=…` — even where the value equals the default.
**A generated file holds no implicit state**: the line says what it means, and
changing a policy is a one-word diff rather than the appearance or disappearance
of a key. This is the property [ADR-RECORD](0010_index-record.md) already gives
`meta` inside a record, now given to the source list that produced it.

⚠ **Narrowed 2026-09-01: an attribute whose default is the EMPTY STRING is
omitted at that default.** `types` gained `decoder=` ([ADR-TYPES](0031_types-list.md)
decision 11), whose empty default means *no binding declared* — and writing a
bare `decoder=` on every prose line states no policy, cannot be diffed into one,
and is four dead characters where this decision promised a meaningful word.
**The rule this decision actually protects is that a stated policy is visible,
not that a key is always present**, and an attribute with nothing to state has
no policy to make visible.

**Nothing existing is affected, and that is checkable, not asserted:** `fetch`,
`meta`, `keep`, `ttl`, `archived` and `enrich` all have non-empty defaults, so
all six are still written at their default. The carve-out reaches exactly the
attributes a future record gives an empty default to — and giving one an empty
default is now a decision with a visible consequence rather than a free choice.

**13. The reader is lenient; the writer is strict.** A missing attribute takes
its default **when read**, so a hand-made list, an older file, or a merge that
dropped a key still loads. But a line missing any attribute **was not written by
fux**, and that is worth reporting: a completeness check turns *"the list is not
edited manually"* from a policy into an observation anyone can make. The check
belongs to `fux doctor`; the rule is here because it is a property of the
format.

### The attribute set

**Complete. Anything not in this table is an error at `file:lineno`**
(decision 9). A fux-written line always states both (decision 12), so the
*default* column is what a **missing** attribute means to the reader — which, in
a correctly generated file, never happens.

| attribute | values | default when absent | defined by | changes committed bytes? |
|---|---|---|---|---|
| **`fetch`** | `http` · `cdp` | `http` | [ADR-HTTP-FETCHER](0021_http-fetcher.md) · [ADR-CDP-FETCHER](0020_cdp-fetcher.md) | **no** — it selects *who* retrieves the document, not what the record says. A record does not carry which fetcher produced it |
| **`meta`** | `plain` · `hashed` | `hashed` (L5) | [ADR-CONFIG](0014_config.md) · [ADR-RECORD](0010_index-record.md) | **yes** — `plain` writes `title` + `phrases`, `hashed` writes `title_h` instead. The value is recorded per record, so a record read years later still says which rule wrote it |

**`fetch` is a routing decision.** A name resolves to
`<fetchers dir>/<name>.py`, the directory being the parent of
`[sources.url] fetcher` ([ADR-CONFIG](0014_config.md) decision 5) — so
relocating a repo's fetchers is a one-key change and never a per-line edit.
Exactly one runs ([ADR-FETCHER](0019_fetcher.md) decision 4), and nothing
escalates from one to another ([ADR-HTTP-FETCHER](0021_http-fetcher.md)
decision 3) — so the value on the line is the whole story, every run.

**Three layers, one order, for both attributes.** The built-in default, then the
source-wide `[sources.url]` setting, then the line. A line beats both, for its
own URL only.

**`meta` is a privacy decision, and it only ever loosens per URL.** The
source-wide setting is the floor; a line may opt one document *out* of hashing
because that document is public. **There is deliberately no way to make one URL
stricter than the source** — a source that needs hashing needs it for
everything, and per-line strictness would invite the mistake of leaving one line
off.

### Considered for the set, and deliberately excluded

**Fetcher tunables** — `wait=`, `settle=`, `port=`, `timeout=`. **Rejected on
principle, permanently.** Those are one fetcher's vocabulary, and
`[sources.url.config]` exists precisely to carry it without fux learning it
([ADR-FETCHER](0019_fetcher.md) decision 8). A `settle=500` in this grammar is
fux knowing what Chrome is — the adapter cap breached through the back door
rather than the front.

**Content overrides** — `title=`, `summary=`. **Rejected:** the document owns
its content. Everything in a record is taken from the fetched bytes
([ADR-EXTRACTED](0016_extracted-mode.md)), and a title supplied by the list
would be the one field in the index that no document said.

**Three the grammar could hold and this record does not decide** — named so
nobody re-argues them from scratch, and so nobody adds one quietly:

| candidate | what it would do | why not here |
|---|---|---|
| `snapshot` | commit a machine-made copy of the content, per URL | the refer/snapshot policy is per *source* today and belongs to [ADR-REFER](0030_refer-plane.md); a per-URL form is an L2 decision, not a grammar one |
| `tag` | give a URL document the frontmatter tags a repo file has | URL documents have no frontmatter, so their `tag` edges are always empty — a real gap. But it invents corpus structure in a config file, which needs its own record |
| `max_age` | per-URL freshness bound at answer time | freshness is the refer plane's, and its threshold is a pre-registered prediction. Deciding it here would fix a number no one has measured |

Each would be a new row in the table above **and a change to this record**,
which is the point of decision 11.

### The `dirs` attribute set

The same grammar carries `.fux/sources/dirs`, whose set is also **closed** and
is `archived` and `enrich`, both `true|false`, both defaulting to `false`, both
**declared and never derived**.

| attribute | changes committed bytes? | defining record |
|---|---|---|
| `archived` | no — it routes ranking | [ADR-DIR-LIST](0022_dir-list.md) |
| **`enrich`** | **yes, indirectly** — a scope's documents gain a `ctx` field | [ADR-ENRICH](0040_enrich.md) |

`enrich` is the one attribute whose effect on the index is *indirect*: the
attribute itself writes nothing, but it decides which documents `fux enrich`
plans for, and a document with pinned enrichment indexes extra `ctx` terms.
Worth stating, because decision 12 writes `docs archived=false enrich=false`
and a reader should know which half of that can move a byte.

### Consequences

- **The file is tool-managed, and the writer edits one line rather than
  regenerating the file.** The obvious alternative loses something real:

  | decision | what tool-management changes about it | how `fux add` answers |
  |---|---|---|
  | 3, comments | they stop being how a human annotates and become what a writer must **preserve** | a grouping comment and a line's own trailing comment both survive an edit; a regenerating writer would eat both |
  | 4, duplicates | "a merge artefact" becomes "a writer must not emit one" | an add to a URL already listed is an **update in place**, never a second line |
  | 4, ordering | the loader's canonical sort could be done once by the writer | a new line lands at its sorted position — a courtesy to the reader, since the loader still sorts and correctness does not depend on it |

  **It still is not a lockfile.** A lockfile is generated whole from a manifest;
  this file *is* the manifest, and `fux add` is a careful editor of it. Which is
  why a hand-written line stays legal (decision 13) and `fux add` marks it
  rather than rewriting it.
- **`fux add <URL>` fetches, and the fetch does not gate the write.** A managing
  command that validated a URL by requesting it would make the committed list a
  function of network weather — so the line is recorded first and stays recorded
  even when the fetch fails; the failure is reported and exits 1. **The *list* is
  not a function of whether the network was up. The *index* is, and always was.**
- **The writer commits LF only on disk, regardless of host OS.** `.gitattributes`
  already normalises CRLF to LF at `git add` time for every tracked file, so
  committed bytes were never at risk — the explicit `newline="\n"` is
  defence-in-depth that does not depend on `.gitattributes` staying present or
  correctly matching the path, and it means the working-tree file is right
  immediately rather than only after the next `git add`.
- **Two records describe one subsystem**, deliberately: this one for the format,
  [ADR-URL-INGEST](0008_url-ingest.md) for the fetch contract. The split earns
  itself whenever the grammar moves and the fetcher contract does not.
- ⚠ **Decision 3's narrow comment rule fixed a real disappearance, and it was
  fixed by decision 7 rather than around it.** A rule that stripped from the
  first `#` anywhere on the line loaded `https://x/page#section` as
  `https://x/page`; two lines differing only by fragment then collapsed under
  decision 4, and a document vanished with no error — the failure decision 5
  exists to prevent, reached by a different route. Making the line
  whitespace-delimited made the narrow comment rule the only parseable one.
- **An attribute that changes committed bytes needs a home in the record.**
  `meta=plain` has one. A future attribute that changes bytes without one would
  be an `_format` question.
- **A duplicate is invisible.** Accepted under decision 4, at the cost that a
  reviewer cannot see from the diff that a line was already present.

### Alternatives considered

- **A TOML array in `fux.toml`** — the original shape, **retired with an
  erroring key** ([ADR-CONFIG](0014_config.md) decision 10). One diff hunk, one
  merge conflict, and it buries a corpus decision inside config.
- **Erroring on duplicates.** Rejected: duplicates are what merges produce, and
  a list that fails the build after a clean merge trains people to stop
  maintaining it.
- **Preserving file order.** Rejected: it makes committed bytes a function of
  how someone chose to group their list, which is L3 lost for a cosmetic gain.
- **Sections** (`[http]` / `[cdp]`) — rejected: they reintroduce order
  significance, which decision 4 spent effort removing, and moving a URL between
  mechanisms becomes a two-line diff instead of a one-word one.
- **A file per mechanism** (`urls`, `urls.cdp`) — rejected: it multiplies files
  the moment a second attribute exists, and one already does. It also makes
  "which file is this URL in?" a question, where decision 7 makes it a column.
- **The four `.gitattributes` states** (set / unset / valued / revert) —
  rejected under decision 8. Those exist to resolve overlapping *patterns*;
  exact URLs never overlap, so three of the four would only ever be spelling
  variants of the fourth.
- **Last-wins on a duplicate URL with conflicting attributes** — rejected under
  decision 10. It is what `.gitattributes` does, and it is right *there* because
  later lines are deliberate overrides. Here a duplicate is a merge artefact,
  and silently letting one decide a privacy policy is the worst available
  outcome.

### Reference (required)

- The grammar, in its single implementation —
  [`src/fux/ingest/sourcelist.py`](../../src/fux/ingest/sourcelist.py): the
  comment rule, the attribute parse, the dedupe-and-sort and the two error
  classes; `urls` and `dirs` differ only in a closed attribute set and one entry
  validator.
- The loader that consumes it — `read_urls` in
  [`urlsrc.py`](../../src/fux/ingest/urlsrc.py), whose docstring states the
  sort-and-dedupe guarantee.
- A real list, every attribute exercised, and the fetch behaviour it drives —
  [`work/regression/2026-08-19-w54/`](../../work/regression/2026-08-19-w54/report.md),
  with its committed fixture at
  [`evidence/fixture.sh`](../../work/regression/2026-08-19-w54/evidence/fixture.sh).
- The fetch contract this record is split from —
  [ADR-URL-INGEST](0008_url-ingest.md).
- Prior art for per-entry attributes on a line-oriented committed file — git's
  `gitattributes` format: https://git-scm.com/docs/gitattributes
- Prior art for explicit per-entry fetch mechanism rather than automatic
  fallback — `scrapy-playwright`, where browser rendering is a per-request
  opt-in with no automatic escalation:
  https://github.com/scrapy-plugins/scrapy-playwright

### Veto condition

**Reopen this decision if** an attribute is wanted that cannot be written as a
whitespace-free `key=value` — a value needing quoting or spaces breaks decision
8 and the grammar has to grow rather than bend. **Or** if a committed list is
ever found where two lines carry the same URL and conflicting attributes and
someone wants that to *work* rather than to error: that is decision 10 being
wrong about who writes duplicates.

**How to check it:**

```bash
# 1. does any committed list want a value the grammar cannot hold?
grep -nE '[a-z]+="|[a-z]+=[^ ]* [^ ]*=' .fux/sources/urls 2>/dev/null
# expect: no output — a quoted or spaced value means decision 8 is under strain

# 2. does any URL appear twice with different attributes?
awk '!/^ *#/ && NF {print $1}' .fux/sources/urls 2>/dev/null | sort | uniq -d
# expect: no output; a hit must be an error, per decision 10

# 3. is there still exactly ONE parser for the two lists?
grep -rln "def parse(" src/fux/ingest/sourcelist.py src/fux/ingest/urlsrc.py
# expect: only sourcelist.py — a second parser is the drift this record forbids
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-CLI](0002_cli-surface.md) ·
[ADR-DOTFUX](0003_fux-directory.md) · [ADR-INGEST](0007_ingest.md) ·
[ADR-URL-INGEST](0008_url-ingest.md) · [ADR-RECORD](0010_index-record.md) ·
[ADR-CONFIG](0014_config.md) · [ADR-EXTRACTED](0016_extracted-mode.md) ·
[ADR-FETCHER](0019_fetcher.md) · [ADR-CDP-FETCHER](0020_cdp-fetcher.md) ·
[ADR-HTTP-FETCHER](0021_http-fetcher.md) · [ADR-DIR-LIST](0022_dir-list.md) ·
[ADR-REFER](0030_refer-plane.md) · [ADR-ENRICH](0040_enrich.md)

**Code**

- [`src/fux/ingest/sourcelist.py`](../../src/fux/ingest/sourcelist.py)
- [`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py)

**Measured evidence**

- [`work/regression/2026-08-19-w54/evidence/fixture.sh`](../../work/regression/2026-08-19-w54/evidence/fixture.sh)
- [`work/regression/2026-08-19-w54/report.md`](../../work/regression/2026-08-19-w54/report.md)

**Papers and specifications**

- `gitattributes(5)` — prior art for per-entry attributes on a line-oriented
  committed file
  <https://git-scm.com/docs/gitattributes>
- `scrapy-playwright` — prior art for a per-request browser opt-in with no
  automatic escalation
  <https://github.com/scrapy-plugins/scrapy-playwright>
