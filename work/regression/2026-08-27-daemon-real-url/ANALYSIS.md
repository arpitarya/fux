---
type: Analysis
title: Two defects the real network found, and what is left of W-82 ruling 3's hold
description: Both defects are error messages that send a reader somewhere there is nothing to find. The hold narrows to proxy and SSO, which need a corporate network rather than the public internet.
timestamp: 2026-08-27T16:53:50Z
---

# Analysis — the daemon against real external URLs

## 1 · A skip claimed there was no decoder, while the decoder ran

**Observed:** `https://httpbin.org/uuid` was skipped as
`no decoder for application/json`.

**The truth:** `jsondoc` is **built in**, claims `.json`, ran, and correctly
dropped a bare UUID — because dropping UUIDs, hashes and timestamps is what that
decoder is *for*. Nothing readable was left, so `decode()` returned `None`, and
the caller wrote a message that states a falsehood.

- ⚠ **The message sends the reader to write a decoder that already exists.**
- **`decode.reason()` has always drawn this distinction**, and its own docstring
  says conflating the two *"would make the queue useless."* The **file** path
  uses it; the **URL** path did not.
- **The file path also routes the document somewhere useful** — the enrichment
  queue, `.fux/enrich/queue.tsv`, with `jsondoc: nothing readable in .json`.
  Verified live: a UUID-only `.json` file landed there correctly.
- ⚠ **The URL path reaches that queue not at all** (`grep -c queue urlsrc.py`
  → `0`), so **a URL that needs a model can never be queued for one**. That is a
  scope question — `queue.tsv` is committed, so putting `url:` ids in it changes
  committed bytes — and it is **named, not decided**.

**Fixed:** `_decode_fetched` returns `(markdown, why)` and the reason comes from
`decode.reason()`. Three tests in `tests/ingest/test_urlsrc.py`.
**Repro:** `_decode_fetched(b'{"uuid": "..."}', "application/json", url)`.

## 2 · Consumer decoders stopped at the network boundary

Found while fixing §1. `decode_mod.decode(raw, rel)` was called **without
`root`**, so `registry(None)` returned **built-ins only** and a decoder the
consumer wrote into `.fux/decoders/` never applied to a fetched document.

⚠ **ADR-DECODE's premise is *"a consumer may bring a dependency fux may not"***
— and it silently did not hold at the one boundary where an unusual content type
is most likely to arrive. The file path has always passed `root`.

**Fixed and gated** by `test_a_consumer_decoder_reaches_url_content_too`, which
writes a decoder for an invented extension and asserts it runs on URL bytes.

## 3 · Two configuration foot-guns, in the file `fux setup` writes

Both hit while standing the environment up, both first-run experiences.

1. **Appending `[sources.url]` is a duplicate-table error.** The obvious way to
   add `sweep_minutes` — append the table and the key — gives
   `Cannot declare ('sources', 'url') twice`.
2. **Adding the key at the top of the existing table is a duplicate-KEY error.**
   `max_parallel` is defined **25 lines below** the table header, past a long
   comment block, so `[sources.url]\nmax_parallel = 3` at the top collides with
   it: `Cannot overwrite a value (at line 37)`.

⚠ **Neither is a bug in the loader** — both messages are accurate and TOML is
behaving correctly. It is a **shape** problem: the table is long enough that its
own keys are not visible from where a person edits.
**Unresolved, and stated as unresolved:** whether the specimen should carry a
commented `sweep_minutes` beside `max_parallel` is an
[ADR-CONFIG](../../../docs/adr/0014_config.md) question, and `fux setup` is
write-if-missing so it would never reach an existing repo — the same freeze
ADR-DOTFUX decision 6 already names.

## 4 · What is left of W-82 ruling 3's hold

Hands item 1 asked for *"a detached process, a real clock and a real network."*

| clause | status |
|---|---|
| a detached process | ✅ pid reaped on `stop`, `ps` confirms, lock free |
| a real clock | ✅ a page changed externally; picked up unassisted one interval later |
| TLS · DNS · CDN | ✅ three hosts, two CDNs, ~500 KB |
| a real `404` | ✅ recorded skip, prior record kept |
| a real `429` | ✅ **first exercise ever**; `doctor` reports the cumulative count |
| **a proxy** | ❌ needs a corporate network |
| **SSO** | ❌ same |

**The recommendation is that ruling 3 may now land, and it is still Arpit's
call.** The reason to hold it was that the daemon had never been shown to work;
that reason is gone. The reason it might still hold is that narrow-by-default's
blast radius is *URLs that stop being swept*, and proxy/SSO are exactly where a
sweep silently stops in a corporation. **This session does not take the call.**

## 5 · Unresolved

- **The reasonless `"failed"`.** Nothing failed a sweep here, so this run adds
  no evidence — but §1 sharpens the shape of the problem: a sweep can report
  **`"ok"`** while silently skipping URLs, and the skips reach nothing durable.
  A misconfigured or rate-limited repo looks healthy on every surface except a
  foreground `fux update` nobody runs.
- **Whether a URL belongs in `.fux/enrich/queue.tsv`.** §1, named not decided.
- **Windows.** Untested.
