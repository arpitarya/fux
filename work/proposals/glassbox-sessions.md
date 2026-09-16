---
type: Proposal
title: Glassbox sessions — event streams as a fux corpus
description: How a consumer connects fux to a session-replay tool, and why the answer is a materialised-aggregate plane rather than a third fetcher — plus the one line in src/ that blocks fetch=glassbox today.
status: proposed
timestamp: 2026-09-15T00:00:00Z
---

# Glassbox sessions — event streams as a fux corpus

**The ask, Arpit, 2026-09-14:**

> *"I want fux to pull Glassbox sessions and give me the numbers around it. For
> example. Let's say an API call failed. I want to know what was on the screen,
> when the API failed, and later on in same or another session, did the same API
> call succeed, something along those lines."*

[Glassbox](https://www.glassbox.com/platform/) is digital-experience analytics —
session replay plus network and DOM capture for web and mobile. The question it
raises for fux is bigger than one vendor: **it is the first ask for a corpus that
is not written knowledge.**

⚠ **This proposal deliberately does not decide that question.** It states what
already works, names the one line that blocks the obvious path, and puts the two
forks that must be ruled before anything is built. **Nothing here is built.**

---

## 1. The connection point already exists, and it is not in the package

[SR-LAW-4](../../records/0006_LAW-4-offline-by-default.md) put network code in
the **consumer's repo**, not in fux: `fux setup` writes `http.py` and `cdp.py`
into `.fux/fetchers/`, and from that moment they are the consumer's own files.
[SR-URL-INGEST](../../records/0107_url-ingest.md) then fixed routing as *declared,
never detected* — `fetch=` on a line names a fetcher, and

> *"a name resolves to `<fetchers dir>/<name>.py` — the directory being the
> parent of `[sources.url] fetcher`"*
> — [`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py) module docstring

So the shape of the answer to *"how do folks connect to Glassbox"* is already
settled by records that exist: **you write `.fux/fetchers/glassbox.py`, and you
put `fetch=glassbox` on the line.** The contract is fixed and small —
`configure(config)`, optional `connect()`, required
`fetch(url) -> tuple[bytes, str]`, optional `validate(url) -> str | None`,
optional `close()`.

Three things that already exist make it fit better than it has any right to:

| what | why it matters here |
|---|---|
| `[sources.url.config.<name>]` in [`fux.toml`](../../fux.toml) | the per-fetcher slice, handed to `configure()` **verbatim** — tenant host, page size, and the env var naming the API token, with fux reading no key inside |
| [SR-ACQUIRED](../../records/0145_acquired-plane.md) | `keep=true` retains the bytes a fetch returned, in a **gitignored, re-acquirable** plane — the only place session bytes could legally sit |
| [SR-REFUSAL](../../records/0146_refusals.md) | the consumer-owned refusal predicate, which **fails closed** — an expired Glassbox token returning a login page is refused, not indexed as a document |

---

## 2. 🔴 One line in `src/` blocks it today

The `fetch=` attribute's **value set is closed**, not open:

```python
# src/fux/ingest/sourcelist.py:263
Attribute("fetch", ("http", "cdp"), "http"),
```

A line saying `fetch=glassbox` is rejected by the grammar before `urlsrc.py`
ever gets to resolve the name to a file. ⚠ **The module docstring and the
resolution logic already support an open set; the validator does not.** The two
have drifted, and this proposal is what found it.

**This is the W-83 class** — a record describing behaviour the code does not
have: *a third fetcher of any kind is currently impossible*, and neither
[SR-URL-LIST](../../records/0116_url-list.md) nor
[SR-CDP-FETCHER](../../records/0118_cdp-fetcher.md) says it should be.

✅ **Ruled, and SHIPPED the same day** (W-178, 2026-09-15) — it went further
than this proposal asked: Arpit ruled the **symmetry**, so a consumer drops a
file into `.fux/fetchers/` or `.fux/decoders/` and maps it with a flag or the
formats file. `fetch=` is a typed attribute now, validated by name shape, and
`fetch=glassbox` resolving to `.fux/fetchers/glassbox.py` is a **shipped
behaviour** rather than a request this proposal has to make
([SR-URL-LIST](../../records/0116_url-list.md) decision 15,
[the capture](../regression/2026-09-15-consumer-fetchers/report.md) — whose
fixture is literally named `glassbox`). ⚠ **That item was independent of this
proposal and committed to nothing in it**, which is still true: the mechanism
exists, and whether Glassbox sessions belong in the URL list at all is §6's
question and remains open.

**The other blocker is already gone.** The per-fetcher config slice
(`[sources.url.config.cdp]` / `.http]`) landed, so a third fetcher no longer has
to smuggle its settings through a shared table.

---

## 3. Why a plain fetch still does not answer the question

Granting the fetcher: pointing it at Glassbox gets you **session JSON in the
index**, and that answers nothing Arpit asked. Three gaps, and they are the
actual design:

1. **A session is an event stream, not a document.** Fux ranks documents and
   cites line ranges ([SR-PROVENANCE](../../records/0142_provenance.md)). Raw
   event JSON ranks badly — the discriminating terms are timestamps and ids —
   and a citation into it is a line a human cannot read.
2. **"Did the same call succeed later, in another session"** is a **temporal
   join across documents**. `fux ask` retrieves and `fux graph` relates; neither
   joins on a timestamp window. Nothing in the verb surface does.
3. **"Give me the numbers"** is **aggregation**. Fux counts nothing, by design,
   and adding counting to a retrieval engine is how a retrieval engine stops
   being one.

⚠ **The temptation to resist** is making `ask` do (2) and (3). That is a second
engine wearing the first one's CLI.

---

## 4. Sketch — fetch → materialise → index

Three consumer-owned artefacts, no verb added:

**(a) `.fux/fetchers/glassbox.py`** — one closed session per URL. `validate()`
is free and exact: a **closed session is immutable**, so its id is its own
ETag and `fux update` never re-fetches it.
[SR-URL-FRESHNESS](../../records/0147_url-freshness.md)'s `as-ingested` verdict
is the honest one here, and a long `ttl` is correct rather than lazy. ⚠ **Open
sessions must not be ingested at all** — a document that changes under a
citation is the thing the freshness plane exists to prevent.

**(b) A decoder rendering the stream as a *session transcript*** — chronological,
one line per event, each line carrying `timestamp · route/screen · call ·
status`. This is the whole trick behind *"what was on the screen when it
failed"*: it turns a temporal lookup into a **line-range citation**, which fux
already does exactly and verifiably.

**(c) A materialiser writing *incident dossiers*** — one document per
`(endpoint × failure signature)`, with the counts **already computed**: how many
sessions saw it, how many later succeeded, the gap distribution, the screens
present at failure versus at success, and the session ids as links.

> **The dossier is the load-bearing idea.** Fux cannot aggregate — so you
> aggregate **deterministically at ingest** and let fux *cite the number*.
> `fux answer --receipt` then pins it and `fux verify` reproduces it. The
> arithmetic becomes auditable rather than inferred, which is the whole reason
> to route this through fux instead of a notebook.

**Where (c) lives is itself unresolved.** A materialiser is not a fetcher and not
a decoder; it is a *producer of documents fux then indexes as ordinary files*.
That may be the right answer — **it needs no fux concept at all**, just a script
in the consumer's repo writing markdown into a directory `fux add`s. The
alternative, a new plane, should have to argue for itself against that.

---

## 5. ⚠ The fork that must be ruled first — the committed index

**`.fux/index/` is committed.** `runtime/` and `acquired/` are the only ignored
planes ([SR-DOTFUX](../../records/0102_fux-directory.md), enforced by
`fux doctor`'s check-ignore assertion). Session replay from a regulated
consumer-facing app therefore means **customer content entering a committed
index** — and [SR-LAW-2](../../records/0004_LAW-2-content-never-durable.md)'s
accepted cost, restated by **B-190**, is that *"a hashed key is not anonymity"*:
term statistics still come from the document, and `terms` is not salted.

🔴 **`pii.toml` does not close this.** Its `validate` set is a closed list of
checksum validators over **regex-shaped** values
([SR-PII](../../records/0148_pii.md)); a DOM snapshot is unstructured free text
with names, balances and addresses in arbitrary positions. Redaction reduces the
leak here; it does not bound it. And a missing `pii.toml` is already a hard stop
for every command — the machinery is *present*, which makes it easy to assume it
is *sufficient*. It is not.

**The fork:**

| | option | what it costs |
|---|---|---|
| **(a)** | **Index dossiers only.** Endpoint names, counts, screen *identifiers*. Transcripts stay in `acquired/` — gitignored, re-acquirable, never committed | you cannot `fux answer` into a transcript line, so §4(b)'s citation trick is weakened to a dossier-level claim |
| **(b)** | **A second, gitignored index** for transcripts, rebuilt per analyst | two indexes, two freshness stories, and the committed plane stops being the whole truth about the corpus |
| **(c)** | **Index both, committed**, and lean on `meta=hashed` + `pii.toml` | 🔴 rejected here: B-190 and B-191 already say this does not hold, and *"the law reduces the leak; it does not close the channel"* |

**This proposal recommends (a)**, and notes that (a) can be taken **now**,
before any code — it is a privacy ruling, not a build-order question.

---

## 6. The second fork — one human-written line per URL

`.fux/sources/urls` is *committed, human-ordered*, one line per URL, and
[SR-URL-LIST](../../records/0116_url-list.md) treats that as a feature: a human
decides what enters the corpus. **Thousands of auto-generated session lines
break that premise outright**, and quietly.

Two honest ways out, neither free:

- **A generator script owns the file**, and the file says so in its header.
  Cheap, but it retires "human-ordered" for this consumer and nothing checks it.
- **The session plane is not a URL list at all** — the materialiser (§4c) fetches
  sessions itself and emits dossiers as *files*, and only the dossiers are
  `fux add`ed. The URL list stays human-scale because sessions never enter it.

⚠ **The second is probably right, and it dissolves §2's blocker entirely** — if
sessions never appear in `.fux/sources/urls`, no third fetcher is needed and
`fetch=` stays `http|cdp`. That is the strongest argument in this document and
it argues *against* its own §1. It should be litigated before anyone writes
`glassbox.py`.

---

## 7. The honest alternative — MCP, and why it is not the same thing

`fux mcp` already serves the index, and **B-182** (`mcp-adapters.md`) parks the
argument that MCP is the adapter endgame. A **Glassbox MCP server** — the
vendor's or a thin one — would answer Arpit's question *today*, live, with no
ingest, no materialiser, and no privacy ruling.

| | Glassbox over MCP | Glassbox through fux |
|---|---|---|
| joins and counts | live, arbitrary | only what was materialised |
| answer | **uncited, unreproducible** — the model did the arithmetic | cited, receipted, `fux verify`-able |
| corpus | none; nothing persists | a durable record of what was true |
| cost to fux | zero | §5 and §6 must both be ruled |

**Neither dominates.** MCP is the right two-week probe *because* it is cheap: it
reveals which questions actually get asked, and the dossier schema in §4(c) is
worthless if it is guessed. Fux is the right durable answer for the handful of
questions that turn out to be asked repeatedly and need to survive an audit.

---

## 8. What this would be the first of

⚠ **The reason to take this seriously is not Glassbox.** It is the first request
for fux to index a corpus that is *generated*, *high-volume*, *privacy-bearing*
and *not written by a human* — and RUM, Sentry replays, Datadog and FullStory are
all the same shape. The positioning ruling of 2026-09-12 was
*"a search index for your written knowledge"*
([`positioning-documents-not-code.md`](positioning-documents-not-code.md), B-176).

🔴 **A session transcript is not written knowledge.** An *incident dossier*
arguably is — it is a written finding about a system, of exactly the kind fux
was positioned for. **That distinction is the whole proposal**, and if it does
not hold, the answer to this ask is §7's MCP path and fux stays out of it.

---

## 9. Graduation trigger

**A second event-stream source is asked for.** One request is a use case; two is
a shape, and only a shape justifies a plane. Until then the materialiser is a
script in one consumer's repo and fux needs to know nothing about it.

⚠ **Two things do not wait for the trigger**, because neither is this feature:

1. **§2's closed `fetch=` tuple** is a defect in its own right — the docstring
   and the validator disagree, and *no* third fetcher is possible today.
   ✅ **Ruled, filed and SHIPPED on 2026-09-15** (W-178) — `fetch=` is typed,
   the docstring and the validator agree, and a third fetcher is possible.
   [SR-URL-LIST](../../records/0116_url-list.md) decision 15.
2. **§5's privacy fork** can be ruled at any time and is worth ruling once, for
   every future generated corpus, rather than per vendor.

## 10. Open questions

- Does Glassbox expose a session-export API on Arpit's tenant, and under what
  retention window? ⚠ **Retention makes ingest a ratchet** — a session that ages
  out cannot be re-acquired, so `keep=true` is not an optimisation here, it is
  the only copy.
- What is the failure *signature* that groups sessions into one dossier —
  endpoint + status? + error body? + screen? A wrong grouping makes every number
  in §4(c) wrong in a way no citation will reveal.
- Does an incident dossier belong in the consumer's repo at all, or beside the
  code it indicts?

---

## Reference

- [SR-LAW-4](../../records/0006_LAW-4-offline-by-default.md) — offline by default; why network code lives in the consumer's repo
- [SR-LAW-2](../../records/0004_LAW-2-content-never-durable.md) · [SR-LAW-5](../../records/0007_LAW-5-hashed-meta.md) — content never durable; hashed meta, and what it does not close
- [SR-URL-INGEST](../../records/0107_url-ingest.md) · [SR-URL-LIST](../../records/0116_url-list.md) · [SR-CDP-FETCHER](../../records/0118_cdp-fetcher.md) — the fetcher contract, the line grammar, the second fetcher as worked example
- [SR-ACQUIRED](../../records/0145_acquired-plane.md) · [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) · [SR-REFUSAL](../../records/0146_refusals.md) — retained bytes, freshness verdicts, the fail-closed refusal predicate
- [SR-PII](../../records/0148_pii.md) · [SR-DOTFUX](../../records/0102_fux-directory.md) — redaction's closed validator set; which planes are committed
- [SR-PROVENANCE](../../records/0142_provenance.md) — `--receipt`, `--audit`, `fux verify`
- [`mcp-adapters.md`](mcp-adapters.md) (B-182) · [`positioning-documents-not-code.md`](positioning-documents-not-code.md) (B-176)
- [Glassbox platform](https://www.glassbox.com/platform/) · [Glassbox integrations](https://www.glassbox.com/platform/integrations/)
