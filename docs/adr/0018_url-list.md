---
type: ADR
name: ADR-URL-LIST
title: "ADR-URL-LIST (0018) — the committed URL list"
description: "One URL per line in a committed file, deduped and sorted by the loader, so config order can never change committed bytes and 5000 entries diff and merge line by line."
status: accepted
timestamp: 2026-08-19T00:00:00Z
---

# ADR-URL-LIST — the committed URL list

- **Name:** `ADR-URL-LIST` — cite this everywhere; never cite the number
- **Status:** accepted
- **Date:** 2026-08-19
- **Feature:** `.fux/sources/urls` — the file format itself, as distinct from what fetches its entries
- **Owns:** `src/fux/ingest/sourcelist.py` (the grammar, shared with `.fux/sources/dirs` per [ADR-DIR-LIST](0023_dir-list.md) decision 2) and `src/fux/sources.py` (`fux url`, the writer). Both added 2026-08-19 when decisions 7–13 were built: the record decides the format and owns what enforces it. The *fetch* half stays with [ADR-FETCHER](0019_fetcher.md), which owns `ingest/urlsrc.py`
- **Laws:** L2, L3, L4 — see [ADR-LAWS](0001_laws.md); never restated here
- **Split from:** [ADR-URL-INGEST](0008_url-ingest.md) decisions 5 and 6, which shipped in 0.31.x and are restated nowhere

---

## §1 — For humans

The list of URLs Fux indexes is **a file, not a config array**: one URL per
line, `#` comments, blank lines ignored, committed to your repo.

That is the whole decision, and it is not cosmetic. A TOML array of 5 000
entries is **one diff hunk and one merge conflict** — two people adding a URL
in the same week collide, and a reviewer cannot see what changed. One entry per
line is what makes the list reviewable at the size it actually reaches.

The second half is that **the loader sorts and dedupes**. File order is
presentation only. You can group entries by team, by system, by whatever helps
a human read it, and it cannot change a single committed byte — which is what
keeps [ADR-INGEST](0007_ingest.md)'s byte-reproducibility true when two people
maintain the same list in different orders.

The third part is **per-URL attributes**, decided here and built later: a line
may carry `key=value` pairs after the URL, `.gitattributes`-style. **There are
two, and the set is closed.**

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

**A line with no attributes means every default applies** — which is why this
can be decided before it is built: every list valid today stays valid forever.
The full set, what each does to a record, and the candidates deliberately left
out are in §2.

This record exists separately from [ADR-URL-INGEST](0008_url-ingest.md) because
the two answer different questions: that record owns **what fetches a URL**,
this one owns **what the file says**. `fetch=` is the seam between them — this
record fixes the *grammar* and the closed set of attributes; the fetcher records
define what `fetch=` selects.

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
# NOT inside a URL, which is the whole of W-49.
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
$ fux ingest --refresh-urls
ingested 7 docs (5 changed), 1 skipped, 5 shards written
  skip https://example.invalid/gone: fetch failed: 404 not found
```


---

## §2 — For agents

### Context

Three properties had to hold at once, and each rules out an obvious shape.

**It has to merge.** The design point is a corporate corpus, so the list
reaches thousands of entries maintained by people who do not coordinate. Any
format where one logical addition touches a shared line produces conflicts
proportional to team size.

**It has to be reviewable.** A URL entering the index is a decision about what
an agent will treat as authoritative. It belongs in a diff a human reads, not
in a value nested three levels into a config file.

**It must not affect committed bytes.** Two people can hold the same set in
different orders; the index must not know. This is a direct consequence of
L3 — same sources, byte-identical index — applied to *config* rather than
content.

### Decision

**1. The URL list is a file, not a TOML array.** Default
`.fux/sources/urls`, declared **committed** by
[ADR-DOTFUX](0003_fux-directory.md). The path is configurable
([ADR-CONFIG](0014_config.md)); the format is not.

**2. One URL per line.** Blank lines are ignored. This is the property that
makes the file merge line-by-line at any size, and it is the reason the file
exists rather than an array — the same reasoning that shards the index.

**3. `#` starts a comment at the start of a line or after whitespace**, and
the rest of the line is discarded. Groups, owners, and *why this URL is here*
are the reason a human can maintain the file at all. **`#` anywhere else is
part of the entry** — a URL fragment is not a comment. Under decision 7 this
is forced rather than chosen: `https://x/a#frag meta=plain` cannot be parsed
at all if `#` means a comment everywhere. Built 2026-08-19 in
[`sourcelist.strip_comment`](../../src/fux/ingest/sourcelist.py).

**4. The loader dedupes and sorts.** File order is presentation only. A
duplicate line is not an error — it is a merge artefact, and failing the run
for one would make the file hostile to the collaboration it was designed for.

**5. A non-`http(s)` line is a loud error naming `file:lineno`**, never a
silent skip. The house pattern from `store/reader.py`: a typo'd scheme that
quietly fetches nothing is worse than a stopped run, because the corpus is
then wrong in a way nothing surfaces.

**6. The list is intent, not state.** A line present means *this document
belongs in the index*. A fetch that fails keeps the prior record and reports a
skip; only removing the line removes the document
([ADR-URL-INGEST](0008_url-ingest.md) decision 4). The file never records
fetch outcomes.

**7. A line may carry attributes after the URL**, separated by whitespace:
`<url> key=value [key=value ...]`. A line with no attributes means every
default applies, so **every list that is valid today stays valid forever**.
Built 2026-08-19 in
[`sourcelist.py`](../../src/fux/ingest/sourcelist.py) — **one parser, shared
with `.fux/sources/dirs`** ([ADR-DIR-LIST](0023_dir-list.md) decision 2). Two
parsers for one grammar is how `#`-handling, sorting and the unknown-key error
end up disagreeing.

**8. `key=value` is the only form.** No bare flags, no `-key` unset, no `!key`
revert — `.gitattributes` needs four states because its entries are *patterns*
that overlap; ours are exact URLs that do not. One form, one meaning, nothing
to resolve. Values carry no whitespace and no quoting; a value that needs
either is a new decision, not a parser feature.

**9. An unknown key is a loud error naming `file:lineno`.** Same rule
[ADR-RECORD](0010_index-record.md) applies to `_format`: a reader that does not
know a key must refuse rather than guess. Silently ignoring one is how a
typo'd `mata=plain` ships a private document to a public index — the failure
being wrong quietly, which decision 5 already refuses in the other direction.

**10. A line attribute beats the source-wide setting.** `meta=plain` on a line
overrides `[sources.url] meta` ([ADR-CONFIG](0014_config.md)) **for that URL
only**. The default stays the strict one — L5 is a safety property, so opting
out is per-document and visible in a diff, never a blanket flip. Two lines
carrying the same URL with **different** attributes are a loud error naming
both line numbers, not a last-wins merge: exact URLs cannot legitimately
disagree, and quietly picking one would make a merge artefact into a policy
change.

**11. The attribute set is closed, and it is two.** `fetch` and `meta`, defined
below. **Adding one is a change to this record**, not a config addition — which
is what makes decision 9's unknown-key error safe to be strict about: the error
is never wrong, because there is nothing legitimate it can reject.

**12. A fux-written line carries every attribute, explicitly.** `fux url`
emits the complete set — `fetch=… meta=…` — even where the value equals the
default. **A generated file holds no implicit
state**: the line says what it means, and changing a policy is a one-word diff
rather than the appearance or disappearance of a key. This is the property
[ADR-RECORD](0010_index-record.md) already gives `meta` inside a record ("*a
record read years later still says what rule it was written under*"), now given
to the source list that produced it.

**13. The reader is lenient; the writer is strict.** A missing attribute takes
its default **when read**, so a hand-made list, an older file, or a merge that
dropped a key still loads. But a line missing any attribute **was not written by
fux**, and that is worth reporting: a completeness check turns *"the list is not
edited manually"* from a policy into an observation anyone can make. The check
belongs to `fux doctor` ([ADR-DOTFUX](0003_fux-directory.md)); the rule is here
because it is a property of the format.

### The attribute set

**Complete. Anything not in this table is an error at
`file:lineno`** (decision 9).

**A fux-written line always states both** (decision 12). The *default* column
is therefore what a **missing** attribute means to the reader — which, in a
correctly generated file, never happens.

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

**Three layers, one order, for both attributes.** The built-in default in the
table above, then the source-wide `[sources.url]` setting, then the line.
`[sources.url] fetcher`'s stem is the source-wide value of `fetch`;
`[sources.url] meta` is the source-wide value of `meta`. A line beats both,
for its own URL only — which is decision 10 stated as a resolution order
rather than as one attribute's special case.

**`meta` is a privacy decision, and it only ever loosens per URL.** The
source-wide setting is the floor; a line may opt one document *out* of hashing
because that document is public. There is deliberately no way to make one URL
stricter than the source — a source that needs hashing needs it for everything,
and per-line strictness would invite the mistake of leaving one line off.

**Two attributes on one line are independent**, in any order, and a line may
carry either, both, or neither:

| line | fetcher | display fields |
|---|---|---|
| `https://a/x` | `http` | hashed |
| `https://a/x  meta=plain` | `http` | plain |
| `https://a/x  fetch=cdp` | `cdp` | hashed |
| `https://a/x  fetch=cdp meta=plain` | `cdp` | plain |

### Considered for the set, and deliberately excluded

**Fetcher tunables** — `wait=`, `settle=`, `port=`, `timeout=`. **Rejected on
principle, permanently.** Those are one fetcher's vocabulary, and
`[sources.url.config]` exists precisely to carry it without fux learning it
([ADR-FETCHER](0019_fetcher.md) decision 8). A `settle=500` in this grammar is
fux knowing what Chrome is, which is the adapter cap breached through the back
door rather than the front.

**Content overrides** — `title=`, `summary=`. **Rejected:** the document owns
its content. Everything in a record is taken from the fetched bytes
([ADR-EXTRACTED](0016_extracted-mode.md)), and a title supplied by the list
would be the one field in the index that no document said.

**Three that the grammar could hold and this record does not decide** — named
so nobody re-argues them from scratch, and so nobody adds one quietly:

| candidate | what it would do | why not here |
|---|---|---|
| `snapshot` | commit a machine-made copy of the content, per URL | the `refer`/`snapshot` policy is per *source* today and belongs to the M4 refer plane ([W-24](../../archive/open/W-24-m4-refer-plane.md)); a per-URL form is an L2 decision, not a grammar one |
| `tag` | give a URL document the frontmatter tags a repo file has | URL documents have no frontmatter, so their `tag` edges are always empty — a real gap. But it invents corpus structure in a config file, which needs its own record |
| `max_age` | per-URL freshness bound at answer time | freshness is the refer plane's, and its threshold is prediction **R4**. Deciding it here would fix a number no one has measured |

Each would be a new row in the table above **and a change to this record**,
which is the point of decision 11.

### Consequences

- **The file is tool-managed, and the writer edits one line rather than
  regenerating the file** (built 2026-08-19). That is the amendment this
  record's earlier consequence promised, and it fell the way it did because the
  obvious alternative loses something real:

  | decision | what tool-management changes about it | how `fux url` answers |
  |---|---|---|
  | 3, comments | they stop being how a human annotates and become what a writer must **preserve** | a grouping comment and a line's own trailing comment both survive an edit; a regenerating writer would eat both |
  | 4, duplicates | "a merge artefact" becomes "a writer must not emit one" | an add to a URL already listed is an **update in place**, never a second line |
  | 4, ordering | the loader's canonical sort could be done once by the writer | a new line lands at its sorted position — a courtesy to the reader, since the loader still sorts and correctness does not depend on it |

  **It still is not a lockfile.** A lockfile is generated whole from a
  manifest; this file *is* the manifest, and `fux url` is a careful editor of
  it. Which is why a hand-written line stays legal (decision 13) and
  `fux url` marks it rather than rewriting it.

- **`fux url` never fetches.** `--cdp` and `--plain` decide what is *recorded*;
  `fux ingest --refresh-urls` stays the only networked path in the engine
  (L4, [ADR-CLI](0002_cli-surface.md) decision 1). A managing command that
  validated a URL by requesting it would make the committed list a function of
  whether the network was up when someone typed the command.

- **Two files describe one subsystem**, deliberately: this record for the
  format, [ADR-URL-INGEST](0008_url-ingest.md) for the fetch contract. The
  split earned itself immediately — the 2026-08-19 rewrite changed this grammar
  and nothing about the fetcher contract.
- **The fragment truncation is fixed, and it was fixed by decision 7, not
  around it.** The old rule stripped from the first `#` anywhere on the line,
  so `https://x/page#section` loaded as `https://x/page`, two lines differing
  only by fragment collapsed into one under decision 4, and a document
  disappeared with no error — the failure decision 5 exists to prevent,
  reached by a different route. Making the line whitespace-delimited made the
  narrow comment rule the only parseable one. **Both landed together,
  2026-08-19.**
- **The grammar is built, and it has exactly one implementation.**
  [`sourcelist.py`](../../src/fux/ingest/sourcelist.py) holds the comment rule,
  the attribute parse, the dedupe-and-sort and the two error classes; `urls`
  and `dirs` differ only in a closed attribute set and one entry validator.
  Adding a third list is a `ListSpec`, not a parser.
- **An attribute that changes committed bytes needs a home in the record.**
  `meta=plain` does — it decides `title`/`phrases` versus `title_h`. Today
  `meta` is already a record property, so per-URL `meta` needs no schema
  change. A future attribute that changes bytes without one would be an
  `_format` question, same class as the `enriched` shape.
- **A duplicate is invisible.** Accepted under decision 4, at the cost that a
  reviewer cannot see from the diff that a line was already present.

### Alternatives considered

- **A TOML array in `fux.toml`** (`urls = [...]`) — the original shape,
  **retired with an erroring key** ([ADR-CONFIG](0014_config.md) decision 7).
  One diff hunk, one merge conflict, and it buries a corpus decision inside
  config.
- **Erroring on duplicates.** Rejected: duplicates are what merges produce, and
  a list that fails the build after a clean merge trains people to stop
  maintaining it.
- **Preserving file order.** Rejected: it makes committed bytes a function of
  how someone chose to group their list, which is L3 lost for a cosmetic gain.
- **Sections** (`[http]` / `[cdp]`) — rejected: they reintroduce order
  significance, which decision 4 spent effort removing, and moving a URL
  between mechanisms becomes a two-line diff instead of a one-word one.
- **A file per mechanism** (`urls`, `urls.cdp`) — rejected: no parser change,
  but it multiplies files the moment a second attribute exists, and one already
  does (`meta`). It also makes "which file is this URL in?" a question, where
  decision 7 makes it a column.
- **The four `.gitattributes` states** (set / unset / valued / revert) —
  rejected under decision 8. Those exist to resolve overlapping *patterns*;
  exact URLs never overlap, so three of the four states would only ever be
  spelling variants of the fourth.
- **Last-wins on a duplicate URL with conflicting attributes** — rejected under
  decision 10. It is what `.gitattributes` does, and it is right there because
  later lines are deliberate overrides. Here a duplicate is a merge artefact
  (decision 4 says so), and silently letting a merge artefact decide a privacy
  policy is the worst available outcome.

### Reference (required)

- The loader and its rules — [`read_urls`](../../src/fux/ingest/urlsrc.py),
  whose docstring states the sort-and-dedupe guarantee.
- A real list, every attribute exercised, and the fetch behaviour it drives —
  [`work/regression/2026-08-19-w54/`](../../work/regression/2026-08-19-w54/report.md),
  with its committed fixture at
  [`evidence/fixture.sh`](../../work/regression/2026-08-19-w54/evidence/fixture.sh).
  It is the run that closed the fragment defect, and the first that ever
  exercised the URL path end to end.
- The fetch contract this record is split from —
  [ADR-URL-INGEST](0008_url-ingest.md) decisions 4, 5 and 6.
- Prior art for per-entry attributes on a line-oriented committed file —
  git's `gitattributes` format (`pattern attr1 attr2…`, set / unset / valued):
  https://git-scm.com/docs/gitattributes
- Prior art for explicit per-entry fetch mechanism rather than automatic
  fallback — `scrapy-playwright`, where browser rendering is a per-request
  opt-in and there is no automatic escalation:
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
